"""FAZ 3 sahne kurulumu dogrulama senaryolari (G3 kaniti).

Her fonksiyon TEK bir kriteri olcer ve sayilarini dondurur; gecti/kaldi
karari kapi kosucusuna aittir. Boylece esikler tek yerde durur ve senaryo
kendi sinavini kendisi gecemez.
"""

from __future__ import annotations

import numpy as np

from ..observables.crater_shape import crater_profile
from ..observables.ejecta_catalog import catalog_ejecta
from ..observables.momentum_transfer import beta_sensitivity, escape_speed
from ..observables.period_interface import DIMORPHOS_SYSTEM, beta_from_period_change
from ..setup.impactor import (
    DART_MASS,
    DART_MOMENTUM,
    build_impactor,
    impact_geometry,
    place_impactor,
)
from ..setup.rubble_generator import build_rubble_pile, coordination_number
from ..setup.shape_mesh import ellipsoid, icosphere

__all__ = [
    "run_shape_pipeline",
    "run_rubble_quality",
    "run_impactor_convergence",
    "run_observable_selftest",
    "run_scene_determinism",
]


def run_scene_determinism() -> dict:
    """FAZ 3 teslimi: config'den kurulan sahne yeniden uretilebilir mi?

    Uc sey ayri ayri sinanir:
      1. Ayni tohum -> ayni karma (yeniden uretilebilirlik).
      2. Farkli tohum -> farkli karma (tohum GERCEKTEN baglanmis mi; aksi
         halde 1. madde bos bir dogru olurdu).
      3. Fiziksel butunluk: kutle/momentum korunumu, mermi hedefe degmiyor,
         mermi malzemesi hedefinkinden ayri.
    """
    from ..setup.scene import build_scene

    kw = dict(radius=82.0, spacing=8.0, n_impactor=400, model_class="M1",
              f_boulder=0.25, q=3.0, r_min=16.0, r_max=48.0)
    a = build_scene(root_seed=11, **kw)
    b = build_scene(root_seed=11, **kw)
    c = build_scene(root_seed=12, **kw)
    d = a.diagnostics
    imp_dist = float(np.linalg.norm(a.x[a.is_impactor], axis=1).min())
    tgt = ~a.is_impactor
    return {
        "digest": a.digest,
        "reproducible": bool(a.digest == b.digest),
        "seed_sensitive": bool(a.digest != c.digest),
        "n_total": int(a.n),
        "n_target": int(a.n_target),
        "n_impactor": int(d["n_impactor"]),
        "impactor_mass_rel_err": abs(
            float(np.sum(a.m[a.is_impactor])) - DART_MASS) / DART_MASS,
        "impactor_momentum_rel_err": abs(
            float(np.linalg.norm(a.impactor_momentum)) - DART_MOMENTUM) / DART_MOMENTUM,
        "mass_ratio": d["mass_ratio_target_over_impactor"],
        "impactor_min_distance": imp_dist,
        "target_radius": a.target_radius,
        "impactor_outside_target": bool(imp_dist > a.target_radius),
        "target_at_rest": bool(np.all(a.v[tgt] == 0.0)),
        "impactor_nonporous": bool(np.all(a.alpha0[a.is_impactor] == 1.0)),
        "target_porous": bool(np.any(a.alpha0[tgt] > 1.0)),
        "material_heterogeneous": bool(len(np.unique(a.alpha0[tgt])) > 1
                                       and len(np.unique(a.Y0[tgt])) > 1),
        "particles_across_impactor": d["particles_across_impactor"],
        "bulk_density_measured": d["bulk_density_measured"],
    }


def run_shape_pipeline() -> dict:
    """P3-FR-01: mesh kapali, kenar-manifold ve hacmi analitik degerle uyusuyor."""
    out: dict = {"cases": {}}
    for name, mesh, v_exact in (
        ("icosphere_r80", icosphere(4, 80.0), 4.0 / 3.0 * np.pi * 80.0**3),
        ("ellipsoid_100_60_40", ellipsoid(100.0, 60.0, 40.0, subdiv=4),
         4.0 / 3.0 * np.pi * 100.0 * 60.0 * 40.0),
    ):
        v = mesh.volume
        out["cases"][name] = {
            "n_vertices": int(len(mesh.v)),
            "n_faces": int(len(mesh.f)),
            "volume": float(v),
            "volume_exact": float(v_exact),
            "volume_rel_err": float(abs(v - v_exact) / v_exact),
            "edge_manifold": bool(mesh.is_edge_manifold()),
            "area": float(mesh.area),
        }
    # yakinsama: bolunme arttikca hacim hatasi kuculmeli (ikosfer icyazili
    # cokyuzludur; hata yakinsamiyorsa hat bozuktur)
    errs = []
    for sub in (2, 3, 4):
        m = icosphere(sub, 80.0)
        errs.append(abs(m.volume - 4.0 / 3.0 * np.pi * 80.0**3) / (4.0 / 3.0 * np.pi * 80.0**3))
    out["volume_error_ladder"] = errs
    out["volume_converges"] = bool(errs[0] > errs[1] > errs[2])
    out["all_manifold"] = all(c["edge_manifold"] for c in out["cases"].values())
    out["max_volume_rel_err"] = max(c["volume_rel_err"] for c in out["cases"].values())
    return out


def run_rubble_quality(spacing: float = 7.0, seed: int = 17) -> dict:
    """P3-FR-02/03/04: yigin yogunlugu, blok kesri ve komsuluk sayisi."""
    mesh = icosphere(4, 80.0)
    plain = build_rubble_pile(mesh, spacing=spacing, bulk_density=1800.0,
                              root_seed=seed, model_class="M0", matrix_alpha0=1.6)
    boul = build_rubble_pile(mesh, spacing=spacing, bulk_density=1800.0,
                             root_seed=seed, model_class="M1", matrix_alpha0=1.6,
                             f_boulder=0.30, q=3.0,
                             r_min=2.0 * spacing, r_max=6.0 * spacing)
    cn = coordination_number(plain.x, spacing)
    f_meas = float(np.sum(boul.m[boul.is_boulder]) / np.sum(boul.m))
    # determinizm: ayni tohum ayni yigin
    rep = build_rubble_pile(mesh, spacing=spacing, bulk_density=1800.0,
                            root_seed=seed, model_class="M1", matrix_alpha0=1.6,
                            f_boulder=0.30, q=3.0,
                            r_min=2.0 * spacing, r_max=6.0 * spacing)
    return {
        "n_particles": int(plain.n),
        "bulk_density": float(plain.bulk_density),
        "bulk_density_target": 1800.0,
        "bulk_density_rel_err": float(abs(plain.bulk_density - 1800.0) / 1800.0),
        "coordination_mean": float(np.mean(cn)),
        "coordination_interior_mean": float(np.mean(cn[cn >= np.median(cn)])),
        "boulder_fraction_target": 0.30,
        "boulder_fraction_measured": f_meas,
        "boulder_fraction_rel_err": abs(f_meas - 0.30) / 0.30,
        "boulder_saturated": bool(boul.diagnostics.get("boulder_saturated", False)),
        "n_boulders": int(0 if boul.boulders is None else len(boul.boulders.radii)),
        "deterministic": bool(np.array_equal(boul.x, rep.x)
                              and np.array_equal(boul.Y0, rep.Y0)),
        "matrix_alpha0": 1.6,
        "alpha0_distinct": bool(len(np.unique(boul.alpha0)) > 1),
        "Y0_distinct": bool(len(np.unique(boul.Y0)) > 1),
    }


def run_impactor_convergence(n_list: tuple[int, ...] = (200, 800, 3200)) -> dict:
    """P3-FR-06/07, P3-VR-02: nokta parcacik degil, >=3 cozunurlukte yakinsak."""
    mesh = icosphere(4, 80.0)
    geom = impact_geometry(mesh, np.array([0.0, 0.0, 1.0]), angle_deg=0.0)
    rows = []
    for n in n_list:
        imp = place_impactor(build_impactor(n), geom)
        d = imp.diagnostics
        rows.append({
            "n_requested": int(n),
            "n_actual": int(imp.n),
            "mass_rel_err": abs(imp.total_mass - DART_MASS) / DART_MASS,
            "momentum_rel_err": abs(float(np.linalg.norm(imp.momentum)) - DART_MOMENTUM)
            / DART_MOMENTUM,
            "volume_error": float(d["volume_error"]),
            "particles_across_diameter": float(d["particles_across_diameter"]),
            "min_distance_to_center": float(np.linalg.norm(imp.x, axis=1).min()),
        })
    return {
        "resolutions": rows,
        "n_resolutions": len(rows),
        "volume_error_converges": bool(rows[0]["volume_error"] > rows[-1]["volume_error"]),
        "max_mass_rel_err": max(r["mass_rel_err"] for r in rows),
        "max_momentum_rel_err": max(r["momentum_rel_err"] for r in rows),
        "min_particles_across": min(r["particles_across_diameter"] for r in rows),
        "no_point_particle": bool(min(r["n_actual"] for r in rows) >= 8),
        "starts_outside_target": bool(min(r["min_distance_to_center"] for r in rows) > 80.0),
        "impact_angle_deg": float(geom.angle_deg),
        "cos_incidence": float(geom.diagnostics["cos_incidence"]),
    }


def run_observable_selftest(seed: int = 23, beta_true: float = 3.0,
                            mu_true: float = 2.5) -> dict:
    """P3-FR-08, P3-VR-03: cikaricilar bilinen yapay sahnede dogru cevabi verir.

    SAHNE UC OZELLIGI ILE KURULUR, ucu de bilerek:
      * Ejekta momentumu, istenen `beta_true`yi verecek sekilde OLCEKLENIR —
        boylece beta cikaricisinin dogru sayiyi bulup bulmadigi sinanabilir.
      * Hedefe, momentum defterini KAPATAN geri tepme hizi verilir
        (p_bagli + p_ejekta = p_mermi). Aksi halde `momentum_closure` tanisi
        yapay olarak devasa cikar ve hicbir sey sinamaz.
      * Ejekta hizlari US'U BILINEN kesik uslu yasadan cekilir; boylece
        `power_law_exponent` geri kazanimi gercek bir sinavdir. Duzgun
        dagilimla uretip "us olctuk" demek, olculmemis bir seyi olcmus gibi
        gostermek olurdu (R^2 = 0.56 ile yakalanmisti).
    """
    rng = np.random.default_rng(seed)
    # hedef: 80 m kure. Krater cikaricisi yon kutulari kullanir; N cok
    # dusukse kutu basina ornek azalir ve derinlik yanli olcum verir
    # (N=4000'de 16 m'lik bilinen cukur 2.95 m olculdu). N buna gore secildi.
    n_t = 40000
    p = rng.normal(size=(n_t, 3))
    p /= np.linalg.norm(p, axis=1)[:, None]
    x_t = p * (80.0 * rng.uniform(0.0, 1.0, n_t) ** (1.0 / 3.0))[:, None]
    m_t = np.full(n_t, 3.86e9 / n_t)

    # ejekta: +z konisi, hizlar kesik uslu yasadan (us = mu_true)
    n_e = 2000
    th = np.radians(rng.uniform(15.0, 45.0, n_e))
    ph = rng.uniform(0.0, 2 * np.pi, n_e)
    d = np.stack([np.sin(th) * np.cos(ph), np.sin(th) * np.sin(ph), np.cos(th)], -1)
    u = rng.uniform(0.0, 1.0, n_e)
    v_ref = 0.2                                    # m/s, alt kesim
    sp = v_ref * (1.0 - u) ** (-1.0 / mu_true)     # M(>v) ~ v^-mu
    x_e = (rng.uniform(200.0, 600.0, n_e))[:, None] * d
    v_e = sp[:, None] * d

    p_imp = np.array([0.0, 0.0, -DART_MOMENTUM])
    # beta = 1 - (p_ej . e)/|p_imp| -> istenen beta icin gerekli eksenel momentum
    p_ax_target = -(beta_true - 1.0) * DART_MOMENTUM      # negatif: merminin tersi
    d_ax = float(np.sum(rng.uniform(1.0, 1.0, n_e) * (v_e @ np.array([0.0, 0.0, -1.0]))))
    m_per = p_ax_target / d_ax if d_ax != 0.0 else 1.0
    m_e = np.full(n_e, abs(m_per))

    # hedefe geri tepme: p_bagli = p_mermi - p_ejekta  (defter kapansin)
    p_ej = np.sum(m_e[:, None] * v_e, axis=0)
    v_t = np.tile((p_imp - p_ej) / float(np.sum(m_t)), (n_t, 1))

    x = np.vstack([x_e, x_t])
    v = np.vstack([v_e, v_t])
    m = np.concatenate([m_e, m_t])

    m_target, r_target = float(np.sum(m_t)), 80.0
    v_esc = escape_speed(m_target, r_target)
    sens = beta_sensitivity(
        x, v, m, impactor_momentum=p_imp,
        control_radii=[120.0, 160.0, 240.0], speed_factors=[0.5, 1.0, 2.0],
        center=np.zeros(3), target_mass=m_target, target_radius=r_target)

    cat = catalog_ejecta(x, v, m, center=np.zeros(3),
                         surface_normal=np.array([0.0, 0.0, 1.0]),
                         control_radius=120.0, escape_speed=v_esc,
                         target_mass=m_target)

    # krater: bilinen 20 m'lik kalot
    dd = np.linalg.norm(x_t, axis=1)
    ca = x_t[:, 2] / np.maximum(dd, 1e-300)
    keep = ~((ca > np.cos(np.radians(30.0))) & (dd > 64.0))
    cs = crater_profile(x_t[keep], center=np.zeros(3),
                        impact_direction=np.array([0.0, 0.0, -1.0]),
                        reference_radius=80.0, outer_angle_deg=60.0, n_bins=12)

    beta_dart = beta_from_period_change(
        DIMORPHOS_SYSTEM["measured_period_change"], DART_MOMENTUM)

    return {
        "beta_true": float(beta_true),
        "beta_median": sens["beta_median"],
        "beta_min": sens["beta_min"],
        "beta_max": sens["beta_max"],
        "beta_recovery_rel_err": abs(sens["base"].beta - beta_true) / beta_true,
        "beta_relative_spread": sens["beta_relative_spread"],
        "sensitivity_reported": bool(sens["beta_spread"] > 0.0),
        "escape_speed": v_esc,
        "momentum_closure": sens["base"].momentum_closure,
        "ejecta_direction_ok": bool(sens["base"].diagnostics["ejecta_direction_ok"]),
        "ejecta_n": int(cat.n_ejecta),
        "ejecta_mass_fraction": float(cat.mass_fraction),
        "ejecta_cone_angle_deg": float(cat.cone_angle_deg),
        "ejecta_cone_spread_deg": float(cat.cone_angle_spread_deg),
        "ejecta_power_law_exponent": float(cat.power_law_exponent),
        "ejecta_power_law_exponent_true": float(mu_true),
        "ejecta_power_law_rel_err": abs(cat.power_law_exponent - mu_true) / mu_true,
        "ejecta_power_law_r2": float(cat.power_law_r2),
        "crater_depth": float(cs.depth),
        "crater_depth_expected": 16.0,
        "crater_global_change": float(cs.global_radius_change),
        "crater_separates_global": bool(abs(cs.global_radius_change) < 5.0),
        "beta_from_dart_period": float(beta_dart),
    }

