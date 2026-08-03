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
from ..observables.period_interface import (
    DIMORPHOS_SYSTEM,
    beta_from_period_change,
    dart_beta_budget,
)
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
    "run_speed_threshold_selftest",
    "run_crater_irregular_selftest",
    "run_scene_determinism",
]


def run_crater_irregular_selftest(seed: int = 31) -> dict:
    """Krater cikarici DUZENSIZ cisimde de dogru mu (P3-FR-08)?

    NEDEN AYRI SENARYO. Mevcut krater sinavlarinin hepsi KURE uzerindeydi:
    bilinen kalot, kuresel buzusme (RT9), az orneklenen kutular. Hepsi
    geciyordu — ama hicbiri cismin KENDI seklini sinamiyordu. Dimorphos kure
    degil: 88 x 87 x 65 m. Kuresel referans varsayimiyla KRATERSIZ bir
    elipsoitte 9,04 m'lik hayali krater olculdu; bilinen 8 m'lik cukur ise
    17,43 m raporlandi.

    Bu senaryo iki seyi birden kanitlar:
      1. carpma oncesi sekil referans alininca kratersiz cisimde derinlik ~0,
      2. bilinen cukur DOGRU olculuyor (kuresel varsayim ise sisiriyor).

    KALAN SAPMA NEDIR. Bilinen 8 m'lik cukur duzeltilmis referansla 8,7-9,0 m
    olculuyor (3 tohumda %8,3 / %8,7 / %13,0). Bu YENI bir kusur degil,
    `surface_particles`in bilinen orneklem yanliligidir: "yuzey", yon
    kutusundaki EN UZAK parcaciktir ve gercek yuzeyin bir miktar icinde kalir;
    krater tabaninda kutu basina ornek sayisi referans bolgesinden az oldugu
    icin yanlilik iki bolgede farkli olur ve derinligi biraz BUYUK gosterir.
    Ayni etki kure testinde de olculmus ve turetilmisti (bilinen 20 m ->
    beklenen 21,1 m, +%5,5). Yani isaret ve mertebe onceden bilinen bir
    ozelliktir; esik buna gore %20 secildi, "genis band" diye degil.
    """
    rng = np.random.default_rng(seed)
    a, b, c_ax = 44.0, 43.5, 32.5          # gercek Dimorphos yari-eksenleri
    n = 60000
    p = rng.normal(size=(n, 3))
    p /= np.linalg.norm(p, axis=1)[:, None]
    x0 = p * (rng.random(n) ** (1.0 / 3.0))[:, None] * np.array([a, b, c_ax])

    ort = dict(center=np.zeros(3), impact_direction=np.array([0.0, 0.0, -1.0]),
               reference_radius=40.0, outer_angle_deg=60.0, n_bins=12)
    bos_kuresel = crater_profile(x0, **ort)
    bos_gercek = crater_profile(x0, **ort, x_reference=x0)

    # Bilinen cukur: koni icinde YEREL YUZEYDEN tam `derinlik` metre kaz.
    # Normalize yaricapta kazimak (r_local > 1 - h/c) elipsoitte koni boyunca
    # DEGISEN bir mutlak derinlik verir — yani "bilinen" deger bilinmez olur.
    # Olculdu: oyle kazinca cikarici 9,06 m raporluyordu ve bu %13 "hata" gibi
    # gorunuyordu; oysa gercek kazi derinligi eksen disinda zaten 8 m'den
    # fazlaydi. Sinavin kendisi belirsizse cikaricinin dogrulugu olculemez.
    derinlik = 8.0
    d = np.linalg.norm(x0, axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        nrm = x0 / np.maximum(d, 1e-300)[:, None]
    # yon boyunca elipsoit yuzey yaricapi
    r_surf = 1.0 / np.sqrt((nrm[:, 0] / a) ** 2 + (nrm[:, 1] / b) ** 2
                           + (nrm[:, 2] / c_ax) ** 2)
    ca = nrm[:, 2]
    kaz = (ca > np.cos(np.radians(25.0))) & (d > r_surf - derinlik)
    xk = x0[~kaz]
    dolu_kuresel = crater_profile(xk, **ort)
    dolu_gercek = crater_profile(xk, **ort, x_reference=x0)

    return {
        "axes_m": [2 * a, 2 * b, 2 * c_ax],
        "phantom_depth_spherical_ref": float(bos_kuresel.depth),
        "phantom_depth_true_ref": float(bos_gercek.depth),
        "known_depth": float(derinlik),
        "measured_depth_spherical_ref": float(dolu_kuresel.depth),
        "measured_depth_true_ref": float(dolu_gercek.depth),
        "depth_rel_err_true_ref": abs(dolu_gercek.depth - derinlik) / derinlik,
        "spherical_flag_reported": bool(
            bos_kuresel.diagnostics["reference_is_spherical"]),
        "true_ref_flag_reported": bool(
            not bos_gercek.diagnostics["reference_is_spherical"]),
        "phantom_removed": bool(abs(bos_gercek.depth) < 1.0e-6),
        "spherical_ref_inflates": bool(dolu_kuresel.depth > 1.5 * derinlik),
    }


def run_speed_threshold_selftest(seed: int = 29) -> dict:
    """HIZ ESIGI ekseni gercekten is goruyor mu (P3-VR-03'un ikinci yarisi).

    NEDEN AYRI BIR SENARYO. `run_observable_selftest` iki boyutlu bir tarama
    raporluyor ve "duyarlilik olculdu" diyordu. Eksen basina olculunce:

        beta_spread_radius_axis = 0,2189
        beta_spread_speed_axis  = 0,0        <-- TAM OLARAK SIFIR

    Sebep fiziksel, sahne bozuk degil: o senaryoda kacis hizi 0,0803 m/s,
    en yavas ejekta 0,2 m/s. Tarama 0,5x-2x arasi, yani en fazla 0,161 m/s —
    hicbir parcaciği eleyemez. Yayilimin TAMAMI yaricap ekseninden geliyordu.
    Yani hiz esigi kod yolu HIC KOSULMAMISTI, ama toplam yayilim pozitif
    oldugu icin kapi kriteri geciyordu. (RT12 ile ayni sinif: dogru sonuc,
    yanlis sebep.)

    Bu senaryo, hizlari kacis hizinin ETRAFINA yayar; boylece esik gercekten
    parcacik eler. Beklenen davranis: esik yukseldikce sayilan ejekta azalir,
    |p_ejekta| duser, beta 1'e YAKLASIR — yani beta esikle MONOTON AZALIR.
    Monotonluk sartsiz degil, olculebilir bir tahmindir; ihlali siniflandirma
    mantiginda hata demektir.
    """
    rng = np.random.default_rng(seed)
    m_target, r_target = 3.86e9, 80.0
    v_esc = escape_speed(m_target, r_target)

    n_t = 4000
    p = rng.normal(size=(n_t, 3))
    p /= np.linalg.norm(p, axis=1)[:, None]
    x_t = p * (r_target * rng.uniform(0.0, 1.0, n_t) ** (1.0 / 3.0))[:, None]
    m_t = np.full(n_t, m_target / n_t)

    # Ejekta hizlari 0,25x - 4x v_kacis araliginda LOG-DUZGUN: tarama noktasi
    # 0,5/1/2 arasi her dilimde parcacik var, yani her esik farkli sayida
    # parcacik eler. Kritik nokta budur.
    n_e = 3000
    th = np.radians(rng.uniform(15.0, 45.0, n_e))
    ph = rng.uniform(0.0, 2 * np.pi, n_e)
    d = np.stack([np.sin(th) * np.cos(ph), np.sin(th) * np.sin(ph), np.cos(th)], -1)
    sp = v_esc * 4.0 ** rng.uniform(-1.0, 1.0, n_e)
    x_e = (rng.uniform(200.0, 600.0, n_e))[:, None] * d
    v_e = sp[:, None] * d
    m_e = np.full(n_e, 1.0e4)

    p_imp = np.array([0.0, 0.0, -DART_MOMENTUM])
    p_ej_all = np.sum(m_e[:, None] * v_e, axis=0)
    v_t = np.tile((p_imp - p_ej_all) / float(np.sum(m_t)), (n_t, 1))

    x = np.vstack([x_e, x_t])
    v = np.vstack([v_e, v_t])
    m = np.concatenate([m_e, m_t])

    faktorler = [0.5, 1.0, 2.0]
    sens = beta_sensitivity(
        x, v, m, impactor_momentum=p_imp,
        control_radii=[120.0, 160.0], speed_factors=faktorler,
        center=np.zeros(3), target_mass=m_target, target_radius=r_target)

    grid = sens["beta_grid"]                      # (yaricap, hiz)
    frac = sens["ejecta_fraction_grid"]
    # Her sabit yaricap icin beta esikle azalmali (fark <= 0, tolerans yok:
    # esik yukselince ejekta kumesi bir ALT KUMEYE gecer, bu kesin bir sart)
    monoton = bool(np.all(np.diff(grid, axis=1) <= 0.0))
    kutle_monoton = bool(np.all(np.diff(frac, axis=1) <= 0.0))
    return {
        "escape_speed": v_esc,
        "speed_factors": [float(f) for f in faktorler],
        "beta_by_speed_factor": [float(b) for b in grid[0]],
        "ejecta_fraction_by_speed_factor": [float(f) for f in frac[0]],
        "beta_spread_speed_axis": sens["beta_spread_speed_axis"],
        "beta_spread_radius_axis": sens["beta_spread_radius_axis"],
        "speed_axis_active": sens["speed_axis_active"],
        "beta_monotone_in_threshold": monoton,
        "mass_monotone_in_threshold": kutle_monoton,
        "n_ejecta_by_speed_factor": [
            int(round(f * float(np.sum(m)) / 1.0e4)) for f in frac[0]],
    }


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
    plain = build_rubble_pile(mesh, spacing=spacing, bulk_density=1800.0, rho0_solid=2700.0,
                              root_seed=seed, model_class="M0")
    boul = build_rubble_pile(mesh, spacing=spacing, bulk_density=1800.0, rho0_solid=2700.0,
                             root_seed=seed, model_class="M1",
                             f_boulder=0.30, q=3.0,
                             r_min=2.0 * spacing, r_max=6.0 * spacing)
    cn = coordination_number(plain.x, spacing)
    f_meas = float(np.sum(boul.m[boul.is_boulder]) / np.sum(boul.m))
    # determinizm: ayni tohum ayni yigin
    rep = build_rubble_pile(mesh, spacing=spacing, bulk_density=1800.0, rho0_solid=2700.0,
                            root_seed=seed, model_class="M1",
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
        "matrix_alpha0_solved": float(plain.diagnostics["matrix_alpha0_solved"]),
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
    d_ax = float(np.sum(v_e @ np.array([0.0, 0.0, -1.0])))
    if d_ax == 0.0:
        raise RuntimeError("ejekta konisinin eksenel bileseni sifir — sahne bozuk")
    m_e = np.full(n_e, abs(p_ax_target / d_ax))

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
    bilanco = dart_beta_budget(DART_MOMENTUM)

    return {
        "beta_true": float(beta_true),
        "beta_median": sens["beta_median"],
        "beta_min": sens["beta_min"],
        "beta_max": sens["beta_max"],
        "beta_recovery_rel_err": abs(sens["base"].beta - beta_true) / beta_true,
        "beta_relative_spread": sens["beta_relative_spread"],
        "sensitivity_reported": bool(sens["beta_spread"] > 0.0),
        # EKSEN BASINA: toplam yayilim tek basina "iki boyut da olculdu"
        # sanisi verir. Hangi eksenin gercekten is gordugu ACIK yazilir.
        "beta_spread_radius_axis": sens["beta_spread_radius_axis"],
        "beta_spread_speed_axis": sens["beta_spread_speed_axis"],
        "radius_axis_active": sens["radius_axis_active"],
        "speed_axis_active": sens["speed_axis_active"],
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
        # Bu sayi FAZ 4+'ta modelin HEDEFLEYECEGI degerdir; tek sayi olarak
        # gecmek, model-hedef farkinin nereden geldigini gorunmez kilardi.
        # Olculen: bu basit arayuz 3,222 veriyor, yayinlanan ~3,6 (%10,5 fark)
        # ve Delta_T'nin +/-1 dk bandi [3,125 ; 3,320] 3,6'yi ICERMIYOR —
        # yani fark olcum hatasi degil, KUTLE VARSAYIMI.
        "beta_budget": bilanco,
        "beta_dart_low": bilanco["beta_low"],
        "beta_dart_high": bilanco["beta_high"],
        "beta_dart_vs_published_rel": bilanco["rel_diff_vs_published"],
        "beta_dart_band_covers_published": bool(
            bilanco["beta_low"] <= bilanco["published_beta"] <= bilanco["beta_high"]),
        "target_mass_for_published_beta": bilanco["target_mass_for_published_beta"],
    }

