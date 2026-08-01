"""DART mermisi ve carpma geometrisi (P3-FR-06, P3-FR-07, P3-VR-02).

NOKTA PARCACIK YASAKTIR (P3-FR-06). Nedeni fiziksel: momentum aktarim
katsayisi beta, sokun hedefe HANGI ALANDAN girdigine duyarlidir. Tum kutleyi
tek parcaciga yiginca ilk temas basinci cozunurluge baglanir ve beta olcumu
sayisal bir yapaya donusur. Bu yuzden mermi de hedefle ayni SPH kurallariyla,
sonlu boyutlu ve cozunurlukle yakinsayan bicimde ayriklastirilir.

DART GERCEK DEGERLERI (NASA DART sonuclari, Daly ve digerleri 2022/2023):
  kutle      m = 579.4 kg  (carpma anindaki uzay araci kutlesi)
  hiz        v = 6144.9 m/s
  momentum   p = m v = 3.5601e6 kg m/s
Bu ucu birbiriyle TUTARLI olmali; `DART_NOMINAL` sabitleri ve testleri bunu
korur.

CARPMA GEOMETRISI (P3-FR-07): carpma noktasi ve gelis yonu, hedef sekli
uzerinde tanimlanir. Gelis yonu YUZEY NORMALINE gore verilir; boylece
"dik carpma" (0 derece) sekil ne olursa olsun ayni anlami tasir.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from .rubble_generator import lattice_points, particle_volume
from .shape_mesh import TriMesh

__all__ = [
    "DART_MASS",
    "DART_SPEED",
    "DART_MOMENTUM",
    "Impactor",
    "ImpactGeometry",
    "build_impactor",
    "impact_geometry",
    "place_impactor",
    "resolution_series",
    "sphere_mesh_for_impactor",
]

# --- DART anma degerleri (P3-FR-06) ---
DART_MASS = 579.4      # kg
DART_SPEED = 6144.9    # m/s
DART_MOMENTUM = DART_MASS * DART_SPEED  # kg m/s


@dataclass(frozen=True)
class Impactor:
    """Ayriklastirilmis mermi: konum, kutle, hiz ve tani sayilari."""

    x: np.ndarray            # (M,3) [m]
    m: np.ndarray            # (M,) [kg]
    v: np.ndarray            # (M,3) [m/s]
    radius: float            # kure yaricapi [m]
    spacing: float           # parcacik araligi [m]
    density: float           # malzeme yogunlugu [kg/m^3]
    diagnostics: dict = field(default_factory=dict)

    @property
    def n(self) -> int:
        return len(self.m)

    @property
    def total_mass(self) -> float:
        return float(np.sum(self.m))

    @property
    def momentum(self) -> np.ndarray:
        return np.sum(self.m[:, None] * self.v, axis=0)

    @property
    def kinetic_energy(self) -> float:
        return 0.5 * float(np.sum(self.m * np.sum(self.v * self.v, axis=1)))


@dataclass(frozen=True)
class ImpactGeometry:
    """Carpma noktasi, yuzey normali ve gelis yonu."""

    point: np.ndarray        # (3,) yuzeydeki carpma noktasi [m]
    normal: np.ndarray       # (3,) DISA dogru birim yuzey normali
    direction: np.ndarray    # (3,) merminin gittigi birim yon (iceri bakar)
    angle_deg: float         # normalden sapma [derece]; 0 = dik carpma
    diagnostics: dict = field(default_factory=dict)


def sphere_mesh_for_impactor(radius: float, subdiv: int = 3) -> TriMesh:
    """Mermi kabugu icin ikosahedron kuresi (yalniz kolaylik sarmalayicisi)."""
    from .shape_mesh import icosphere

    return icosphere(subdiv, radius)


def build_impactor(
    n_target: int,
    *,
    mass: float = DART_MASS,
    speed: float = DART_SPEED,
    density: float = 2700.0,
    direction: np.ndarray | None = None,
    center: np.ndarray | None = None,
    packing: str = "fcc",
) -> Impactor:
    """Merminin sonlu boyutlu ayriklastirmasini uret (P3-FR-06).

    `n_target` YAKLASIK parcacik sayisidir: aralik ondan turetilir, sonra
    kureye giren parcaciklar sayilir; gercek sayi biraz farkli cikar ve
    `diagnostics["n_requested"]` ile birlikte raporlanir.

    KUTLE TAM KORUNUR: parcacik kutleleri, toplam `mass`'i verecek bicimde
    olceklenir. Ayriklastirma kaba oldugunda hacim hatasi kutleye degil
    YOGUNLUGA yansir; sapma `density_error` olarak raporlanir — sessizce
    yutulmaz.
    """
    if n_target < 8:
        raise ValueError(f"n_target >= 8 olmali (nokta parcacik yasak), {n_target} geldi")
    if mass <= 0.0 or speed <= 0.0 or density <= 0.0:
        raise ValueError("kutle, hiz ve yogunluk pozitif olmali")

    volume = mass / density
    radius = (3.0 * volume / (4.0 * math.pi)) ** (1.0 / 3.0)
    # V_p = spacing^3 / sqrt(2) (fcc) -> spacing = (V/n * sqrt(2))^(1/3)
    vol_per = volume / float(n_target)
    spacing = (vol_per / particle_volume(1.0, packing)) ** (1.0 / 3.0)

    # Kure icin ANALITIK ic test kullanilir, mesh degil: ikosfer bir icyazili
    # cokyuzludur, hacmi gercek kureden kucuktur ve ayriklastirmaya sistematik
    # bir egilim sokardi.
    lo = np.full(3, -radius - spacing)
    hi = np.full(3, radius + spacing)
    cand = lattice_points(lo, hi, spacing, packing=packing)
    inside = np.sum(cand * cand, axis=1) <= radius * radius
    x = np.ascontiguousarray(cand[inside])
    if len(x) < 8:
        raise ValueError(
            f"mermi ayriklastirmasi cok kaba: {len(x)} parcacik. n_target artir."
        )

    m = np.full(len(x), mass / len(x), dtype=np.float64)
    d = _unit(np.array([0.0, 0.0, -1.0]) if direction is None else direction)
    v = np.tile(speed * d, (len(x), 1))
    if center is not None:
        x = x + np.asarray(center, dtype=np.float64).reshape(1, 3)

    v_disc = len(x) * particle_volume(spacing, packing)
    return Impactor(
        x=x, m=m, v=v, radius=radius, spacing=spacing, density=density,
        diagnostics={
            "n_requested": int(n_target),
            "n_actual": int(len(x)),
            "packing": packing,
            "sphere_volume": volume,
            "discrete_volume": v_disc,
            "volume_error": abs(v_disc - volume) / volume,
            "effective_density": mass / v_disc,
            "density_error": abs(mass / v_disc - density) / density,
            "particles_across_diameter": 2.0 * radius / spacing,
            "momentum_nominal": mass * speed,
        },
    )


def _unit(v: np.ndarray) -> np.ndarray:
    v = np.asarray(v, dtype=np.float64).reshape(3)
    nrm = float(np.linalg.norm(v))
    if nrm == 0.0:
        raise ValueError("sifir uzunluklu yon vektoru")
    return v / nrm


def impact_geometry(
    mesh: TriMesh,
    aim: np.ndarray,
    angle_deg: float = 0.0,
    azimuth_deg: float = 0.0,
) -> ImpactGeometry:
    """Carpma noktasini ve gelis yonunu hedef sekli uzerinde kur (P3-FR-07).

    `aim` merkezden disariya bir yondur; yuzeyle kesistigi yer carpma
    noktasidir. `angle_deg` YUZEY NORMALINDEN sapmadir (0 = dik carpma,
    90 = teget). `azimuth_deg` egik carpmalarda tegetsel yonu secer.

    Egiklik normale gore tanimlandigi icin duzensiz sekillerde de anlami
    sabittir — "z eksenine gore" tanimlamak sekil degisince sessizce baska
    bir carpma acisina kayardi.
    """
    if not (0.0 <= angle_deg < 90.0):
        raise ValueError(f"carpma acisi [0,90) olmali, {angle_deg} geldi")

    d = _unit(aim)
    point, normal, t_hit = _ray_surface(mesh, d)

    # normalin disa baktigindan emin ol
    if float(np.dot(normal, d)) < 0.0:
        normal = -normal

    # tegetsel taban (normale dik iki birim vektor) — azimut icin
    tmp = np.array([1.0, 0.0, 0.0])
    if abs(float(np.dot(tmp, normal))) > 0.9:
        tmp = np.array([0.0, 1.0, 0.0])
    e1 = _unit(np.cross(normal, tmp))
    e2 = np.cross(normal, e1)

    th = math.radians(angle_deg)
    az = math.radians(azimuth_deg)
    tang = math.cos(az) * e1 + math.sin(az) * e2
    # iceri bakan yon: -normal etrafinda th kadar egik
    direction = _unit(-math.cos(th) * normal + math.sin(th) * tang)

    return ImpactGeometry(
        point=point, normal=normal, direction=direction, angle_deg=float(angle_deg),
        diagnostics={
            "hit_distance": float(t_hit),
            "azimuth_deg": float(azimuth_deg),
            "cos_incidence": float(-np.dot(direction, normal)),
            "aim_direction": d,
        },
    )


def _ray_surface(mesh: TriMesh, d: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
    """Merkezden `d` yonunde isin at; EN UZAK kesisimi dondur (dis yuzey).

    Icbukey sekillerde isin birden cok ucgeni deler; carpma noktasi disaridan
    gorunen yuzeydir, yani en buyuk t. En yakini almak, merminin cismin
    icindeki bir catlaga carpmasi anlamina gelirdi.
    """
    o = mesh.centroid
    v0 = mesh.v[mesh.f[:, 0]]
    v1 = mesh.v[mesh.f[:, 1]]
    v2 = mesh.v[mesh.f[:, 2]]
    e1, e2 = v1 - v0, v2 - v0
    pv = np.cross(d[None, :], e2)
    det = np.einsum("ij,ij->i", e1, pv)
    ok = np.abs(det) > 1.0e-300
    inv = np.zeros_like(det)
    inv[ok] = 1.0 / det[ok]
    tv = o[None, :] - v0
    u = np.einsum("ij,ij->i", tv, pv) * inv
    qv = np.cross(tv, e1)
    w = np.einsum("j,ij->i", d, qv) * inv
    t = np.einsum("ij,ij->i", e2, qv) * inv
    hit = ok & (u >= 0.0) & (w >= 0.0) & (u + w <= 1.0) & (t > 0.0)
    if not np.any(hit):
        raise ValueError("isin hicbir ucgeni delmedi — mesh kapali mi?")
    idx = int(np.argmax(np.where(hit, t, -np.inf)))
    face = mesh.f[idx]
    nrm = np.cross(mesh.v[face[1]] - mesh.v[face[0]],
                   mesh.v[face[2]] - mesh.v[face[0]])
    return o + t[idx] * d, _unit(nrm), float(t[idx])


def place_impactor(
    imp: Impactor,
    geom: ImpactGeometry,
    standoff: float | None = None,
) -> Impactor:
    """Mermiyi carpma noktasinin hemen disina, gelis yonunde konumlandir.

    `standoff` verilmezse merminin yaricapi + bir aralik kullanilir: mermi
    hedefe DEGMEDEN baslar, boylece t=0'da yapay ortusme kuvveti olusmaz.
    """
    off = (imp.radius + imp.spacing) if standoff is None else float(standoff)
    if off <= 0.0:
        raise ValueError(f"standoff pozitif olmali, {off} geldi")
    x0 = imp.x - np.mean(imp.x, axis=0)[None, :]
    center = geom.point - off * geom.direction
    speed = float(np.linalg.norm(imp.v[0]))
    return Impactor(
        x=x0 + center[None, :],
        m=imp.m.copy(),
        v=np.tile(speed * geom.direction, (imp.n, 1)),
        radius=imp.radius, spacing=imp.spacing, density=imp.density,
        diagnostics={**imp.diagnostics, "standoff": off,
                     "impact_point": geom.point, "angle_deg": geom.angle_deg},
    )


def resolution_series(
    n_list: list[int], **kw
) -> list[Impactor]:
    """P3-VR-02: en az uc cozunurlukte mermi uret (yakinsama kaniti icin)."""
    if len(n_list) < 3:
        raise ValueError("P3-VR-02 en az 3 cozunurluk ister")
    return [build_impactor(n, **kw) for n in n_list]
