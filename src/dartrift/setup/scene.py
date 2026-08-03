"""FAZ 3 sahne birlestirici: config -> carpmaya hazir tam durum.

NICIN AYRI BIR MODUL. Parcalar (shape_mesh, rubble_generator, settling,
impactor) tek tek dogru olabilir ama FAZ 3'un teslimi bir PARCA degil, tek bir
YENIDEN URETILEBILIR SAHNEDIR. Birlestirmeyi her cagiran tarafa birakmak,
"hangi sirayla, hangi tohumla, hangi h ile" sorularini her yerde ayri
yanitlatir ve kosular sessizce ayrisir.

SIRA SABITTIR ve degistirilemez:
  1. mesh    — sekil (analitik ya da OBJ)
  2. yigin   — parcacik doldurma + bloklar + malzeme atamasi
  3. settling— denge sinamasi (istege bagli; ADR-0024: oturtma DEGIL)
  4. mermi   — sonlu boyutlu, yuzey normaline gore yerlestirilmis
  5. birlesim— hedef + mermi tek dizi; mermi parcaciklari isaretli

TOHUM: tek `root_seed`, `dartrift.rng`'nin adlandirilmis akislarina dagitilir.
Ayni config + ayni tohum ayni sahneyi verir; `Scene.digest` bunu tek bir
karma ile kanitlar.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

import numpy as np

from .impactor import build_impactor, impact_geometry, place_impactor
from .rubble_generator import build_rubble_pile
from .shape_mesh import TriMesh, ellipsoid, icosphere, load_obj, orient_outward

__all__ = ["Scene", "build_scene", "scene_from_config"]


@dataclass(frozen=True)
class Scene:
    """Carpmaya hazir tam durum: hedef + mermi, tek dizi halinde."""

    x: np.ndarray                 # (N,3) [m]
    v: np.ndarray                 # (N,3) [m/s]
    m: np.ndarray                 # (N,) [kg]
    alpha0: np.ndarray            # (N,) baslangic distansiyonu
    Y0: np.ndarray                # (N,) kohezyon [Pa]
    is_impactor: np.ndarray       # (N,) bool
    is_boulder: np.ndarray        # (N,) bool
    spacing: float
    mesh_volume: float
    target_radius: float
    impact_point: np.ndarray      # (3,)
    impact_direction: np.ndarray  # (3,) birim
    surface_normal: np.ndarray    # (3,) birim, disa
    diagnostics: dict = field(default_factory=dict)

    @property
    def n(self) -> int:
        return len(self.m)

    @property
    def n_target(self) -> int:
        return int(np.count_nonzero(~self.is_impactor))

    @property
    def target_mass(self) -> float:
        return float(np.sum(self.m[~self.is_impactor]))

    @property
    def impactor_momentum(self) -> np.ndarray:
        s = self.is_impactor
        return np.sum(self.m[s, None] * self.v[s], axis=0)

    @property
    def digest(self) -> str:
        """Sahnenin icerik karmasi — determinizm kaniti.

        Yalnizca FIZIKSEL durumu karar: konum, hiz, kutle, malzeme. Tanilar
        (sure, makine adi) disaridadir; aksi halde ayni sahne iki makinede
        farkli karma verirdi ve karma isini yapmazdi.
        """
        h = hashlib.sha256()
        for a in (self.x, self.v, self.m, self.alpha0, self.Y0):
            h.update(np.ascontiguousarray(a, dtype=np.float64).tobytes())
        for a in (self.is_impactor, self.is_boulder):
            h.update(np.ascontiguousarray(a, dtype=np.uint8).tobytes())
        return h.hexdigest()


def _build_mesh(shape: str, *, radius=None, semi_axes=None, subdiv=4,
                obj_path=None, obj_units="m") -> TriMesh:
    if shape == "icosphere":
        if radius is None:
            raise ValueError("icosphere icin radius zorunlu")
        return icosphere(subdiv, float(radius))
    if shape == "ellipsoid":
        if semi_axes is None:
            raise ValueError("ellipsoid icin semi_axes zorunlu")
        a, b, c = (float(t) for t in semi_axes)
        return ellipsoid(a, b, c, subdiv=subdiv)
    if shape == "obj":
        if not obj_path:
            raise ValueError("obj icin obj_path zorunlu")
        # PDS DART sekil modelleri KILOMETRE cinsindendir; birim cagiran
        # taraftan ACIKCA gelir (bkz. shape_mesh.load_obj).
        return orient_outward(load_obj(obj_path, units=obj_units))
    raise ValueError(f"bilinmeyen sekil: {shape!r}")


def build_scene(
    *,
    shape: str = "icosphere",
    radius: float | None = 82.0,
    semi_axes: list[float] | None = None,
    subdiv: int = 4,
    obj_path: str | None = None,
    obj_units: str = "m",
    spacing: float = 7.0,
    bulk_density: float = 1800.0,
    root_seed: int = 0,
    model_class: str = "M0",
    # ADR-0030: None -> hedef yigin yogunlugunu tutturan deger COZULUR.
    # Sabit bir deger vermek, `bulk_density` ile celisirse HATA verir.
    rho0_solid: float = 2700.0,
    matrix_alpha0: float | None = None,
    matrix_Y0: float = 1.0e4,
    boulder_alpha0: float = 1.05,
    boulder_Y0: float = 1.0e7,
    f_boulder: float = 0.0,
    q: float = 3.0,
    r_min: float | None = None,
    r_max: float | None = None,
    n_impactor: int = 800,
    impactor_mass: float = 579.4,
    impactor_speed: float = 6144.9,
    impactor_density: float = 2700.0,
    aim: np.ndarray | list[float] = (0.0, 0.0, 1.0),
    angle_deg: float = 0.0,
    azimuth_deg: float = 0.0,
    standoff: float | None = None,
    settle: dict | None = None,
    material=None,
    device: str = "cuda:0",
) -> Scene:
    """Config parametrelerinden tam sahneyi kur.

    `settle` verilirse (ve `material` ile birlikte) denge sinamasi kosulur ve
    hedefin oturmus konumlari kullanilir. Verilmezse yigin uretildigi gibi
    kalir — ADR-0024'e gore bu bir kayip degildir: baslangic durumu zaten
    dengedir (maks |a_SPH| = 0 tam olarak).
    """
    mesh = _build_mesh(shape, radius=radius, semi_axes=semi_axes,
                       subdiv=subdiv, obj_path=obj_path, obj_units=obj_units)

    pile = build_rubble_pile(
        mesh, spacing=spacing, bulk_density=bulk_density, root_seed=root_seed,
        rho0_solid=rho0_solid,
        model_class=model_class, matrix_alpha0=matrix_alpha0, matrix_Y0=matrix_Y0,
        boulder_alpha0=boulder_alpha0, boulder_Y0=boulder_Y0,
        f_boulder=f_boulder, q=q, r_min=r_min, r_max=r_max,
    )

    x_t = np.ascontiguousarray(pile.x, dtype=np.float64)
    v_t = np.zeros_like(x_t)
    settle_diag: dict = {"ran": False}
    if settle and material is not None:
        from .settling import settle_pile

        res = settle_pile(
            pile, material, device=device,
            damping=float(settle.get("damping", 0.02)),
            max_steps=int(settle.get("max_steps", 400)),
            ke_frac=float(settle.get("ke_frac", 1.0e-3)),
            gravity_rebuild_every=int(settle.get("gravity_rebuild_every", 1)),
            gravity_drift_tol=float(settle.get("gravity_drift_tol", 0.25)),
            h_over_spacing=float(settle.get("h_over_spacing", 2.0)),
        )
        x_t, v_t = res.x, res.v
        settle_diag = {
            "ran": True, "n_steps": res.n_steps, "t_end": res.t_end,
            "ke_final": res.ke_final, "ke_threshold": res.ke_threshold,
            "converged": res.converged, **res.diagnostics,
        }

    # carpma geometrisi ve mermi
    geom = impact_geometry(mesh, np.asarray(aim, dtype=np.float64),
                           angle_deg=angle_deg, azimuth_deg=azimuth_deg)
    imp = place_impactor(
        build_impactor(n_impactor, mass=impactor_mass, speed=impactor_speed,
                       density=impactor_density),
        geom, standoff=standoff)

    n_t, n_i = len(x_t), imp.n
    r_eff = float((3.0 * mesh.volume / (4.0 * np.pi)) ** (1.0 / 3.0))

    # Mermiye hedefin malzemesi DEGIL kendi malzemesi verilir: uzay araci
    # gozeneksizdir (alpha0 = 1) ve moloz matrisiyle ayni kohezyona sahip
    # degildir. Bunu hedefin degerleriyle doldurmak, merminin kendisini
    # gozenekli asteroit malzemesi yapardi.
    x = np.vstack([x_t, imp.x])
    v = np.vstack([v_t, imp.v])
    m = np.concatenate([pile.m, imp.m])
    alpha0 = np.concatenate([pile.alpha0, np.ones(n_i)])
    Y0 = np.concatenate([pile.Y0, np.full(n_i, boulder_Y0)])
    is_imp = np.concatenate([np.zeros(n_t, bool), np.ones(n_i, bool)])
    is_bld = np.concatenate([pile.is_boulder, np.zeros(n_i, bool)])

    return Scene(
        x=x, v=v, m=m, alpha0=alpha0, Y0=Y0,
        is_impactor=is_imp, is_boulder=is_bld,
        spacing=spacing, mesh_volume=float(mesh.volume), target_radius=r_eff,
        impact_point=geom.point, impact_direction=geom.direction,
        surface_normal=geom.normal,
        diagnostics={
            "n_total": int(n_t + n_i),
            "n_target": int(n_t),
            "n_impactor": int(n_i),
            "root_seed": int(root_seed),
            "shape": shape,
            "model_class": model_class,
            "bulk_density_measured": float(pile.bulk_density),
            "target_mass": float(np.sum(pile.m)),
            "impactor_mass": float(imp.total_mass),
            "impactor_momentum": float(np.linalg.norm(imp.momentum)),
            "impactor_kinetic_energy": float(imp.kinetic_energy),
            "mass_ratio_target_over_impactor": float(np.sum(pile.m) / imp.total_mass),
            "impact_angle_deg": float(geom.angle_deg),
            "standoff": float(imp.diagnostics["standoff"]),
            "particles_across_impactor": float(
                imp.diagnostics["particles_across_diameter"]),
            "pile": pile.diagnostics,
            "settling": settle_diag,
        },
    )


def scene_from_config(cfg, material=None, device: str = "cuda:0") -> Scene:
    """`RunConfig.scene` bolumunden sahne kur.

    Tohum `RunConfig.random_seed`'den gelir — sahne icin ayri bir tohum alani
    YOKTUR. Iki tohum olsaydi hangisinin sonucu belirledigi belirsizlesirdi.
    """
    if cfg.scene is None:
        raise ValueError("config'de `scene` bolumu yok")
    t, i, s = cfg.scene.target, cfg.scene.impactor, cfg.scene.settling
    return build_scene(
        shape=t.shape, radius=t.radius, semi_axes=t.semi_axes, subdiv=t.subdiv,
        obj_path=t.obj_path, obj_units=t.obj_units,
        spacing=t.spacing, bulk_density=t.bulk_density,
        root_seed=cfg.random_seed, model_class=t.model_class,
        matrix_alpha0=t.matrix_alpha0, matrix_Y0=t.matrix_Y0,
        boulder_alpha0=t.boulder_alpha0, boulder_Y0=t.boulder_Y0,
        f_boulder=t.f_boulder, q=t.q, r_min=t.r_min, r_max=t.r_max,
        n_impactor=i.n_particles, impactor_mass=i.mass, impactor_speed=i.speed,
        impactor_density=i.density, aim=i.aim, angle_deg=i.angle_deg,
        azimuth_deg=i.azimuth_deg, standoff=i.standoff,
        settle=({"damping": s.damping, "max_steps": s.max_steps,
                 "ke_frac": s.ke_frac,
                 "gravity_rebuild_every": s.gravity_rebuild_every,
                 "gravity_drift_tol": s.gravity_drift_tol}
                if s.enabled else None),
        material=material, device=device,
    )
