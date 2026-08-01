"""Oz-yercekimi altinda moloz yigini oturtma (P3-FR-05, P3-VR-01).

NEDEN GEREKLI: `rubble_generator` parcaciklari bir KAFESE koyar; bu, kendi
yercekimi altindaki denge durumu DEGILDIR. Kafes birakildiginda yigin bir
miktar buzusur ve bu buzusme kinetik enerjiye donusur. Sondurulmezse carpma
senaryosu, mermiden GELMEYEN bir hareketle baslar ve momentum aktarim
katsayisi beta kirlenir — yani P3-FR-05 kozmetik bir adim degil, olcumun
on kosuludur.

KABUL (P3-VR-01): oturma sonrasi kinetik enerji, hedef yogunlugun "isil
gurultusu" altina inmeli. Burada isil gurultu esigi, yigini bir arada tutan
yercekimsel baglanma enerjisinin kucuk bir kesri olarak tanimlanir:

    E_bag = (3/5) G M^2 / R        (duzgun kure)
    esik  = ke_frac * E_bag        (varsayilan ke_frac = 1e-3)

Bu tanim OLCEKTEN BAGIMSIZDIR: hem 160 m'lik Dimorphos'ta hem test
olceginde ayni anlami tasir.

SONUMLEME: hiz her adimda bir carpanla kucultulur (kuvvet olarak degil).
Deterministiktir, zaman adimindan bagimsizdir ve sondurulen enerji ayri bir
kalem olarak izlenebilir.

OLCULEN GERCEK — NICIN KE ZATEN SIFIRA YAKIN (ADR-0024):
Bu modul P3-VR-01'i saglar, ama sagladigi icin degil, baslangic durumu ZATEN
denge oldugu icin. Olculdu (N=8842, R=80 m):
  * t=0'da maks |a_SPH| = 0.0 TAM olarak; P = 0, S = 0, rho = rho0/alpha0.
    Sureklilik modunda dengesiz TEK kuvvet yercekimidir.
  * Yercekimsel serbest dusme suresi t_ff = 1566 s, DART cozunurlugunde
    CFL adimi 1.22e-4 s -> bir t_ff = 1.28e7 adim. Yercekimsel oturmayi
    ACIK integrasyonla cozmek bu fazda hesaplanabilir DEGILDIR.
  * Dimorphos'ta merkez litostatik basinci 3.05 Pa; kohezyon test degeri
    1e4 Pa. Oran 3.0e-4 — yani yigin yercekimiyle DEGIL dayanimla tutulur ve
    oturacak bir sey yoktur. (Sartname Ek A'daki Y0 taramasi 0.1-1e3 Pa'ya
    iniyor; Y0 < ~3 Pa'da bu tersine doner ve o kosular ayrica isaretlenir.)
Dolayisiyla bu modul, oturtmak yerine baslangic durumunun DENGE OLDUGUNU
SINAR ve sapmayi olcer. Bunu "settling KE'yi dusurdu" diye sunmak yanlis
olurdu; olculen sey KE'nin zaten esigin 9 mertebe altinda oldugudur.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

__all__ = ["SettleResult", "binding_energy", "settle_pile"]

G_GRAV = 6.6743e-11


@dataclass
class SettleResult:
    """Oturma sonucu: durum + enerji izi + kabul karari."""

    x: np.ndarray
    v: np.ndarray
    rho: np.ndarray
    alpha: np.ndarray
    n_steps: int
    t_end: float
    ke_series: list[tuple[int, float]] = field(default_factory=list)
    ke_initial: float = 0.0
    ke_final: float = 0.0
    ke_threshold: float = 0.0
    binding_energy: float = 0.0
    damped_energy: float = 0.0
    converged: bool = False
    diagnostics: dict = field(default_factory=dict)


def binding_energy(total_mass: float, radius: float) -> float:
    """Duzgun kurenin yercekimsel baglanma enerjisi: (3/5) G M^2 / R."""
    if radius <= 0.0:
        raise ValueError(f"yaricap pozitif olmali, {radius} geldi")
    return 0.6 * G_GRAV * total_mass * total_mass / radius


def settle_pile(
    pile,
    material,
    device: str = "cuda:0",
    damping: float = 0.02,
    max_steps: int = 2000,
    ke_frac: float = 1.0e-3,
    report_every: int = 50,
    cfl: float = 0.25,
    gravity_rebuild_every: int = 1,
    gravity_drift_tol: float = 0.25,
    h_over_spacing: float = 2.0,
):
    """Yigini oz-yercekimi altinda oturt; KE esigin altina inince dur.

    `pile`    : `rubble_generator.build_rubble_pile` ciktisi
    `material`: `MaterialParams` — yercekimi ACIK olmali
    `damping` : adim basina hiz kucultme orani (v <- (1-damping) v)

    Erken durma KE esigine gore yapilir; `max_steps` yalnizca ust sinirdir.
    Yakinsamadan bitilirse `converged=False` doner ve cagiran taraf gorur —
    sessizce "oldu" denmez.
    """
    # Dogrulama warp'tan ONCE: boylece argüman hatalari GPU'suz ortamda da
    # yakalanir ve testleri kosmak icin cihaz gerekmez.
    if not material.gravity.enabled:
        raise ValueError("settling oz-yercekimi ister: material.gravity.enabled=False")
    if not (0.0 <= damping < 1.0):
        raise ValueError(f"damping [0,1) araliginda olmali, {damping} geldi")

    import warp as wp

    from ..cpu_reference.sph_ref import RefParams
    from ..warp_core import integrator as I
    from ..warp_core.solver_solid import WarpSolid3D

    x0 = np.ascontiguousarray(pile.x, dtype=np.float64)
    n = len(x0)
    m = np.ascontiguousarray(pile.m, dtype=np.float64)
    h = h_over_spacing * pile.spacing

    # esik: yigini bir arada tutan enerjinin kucuk bir kesri
    m_tot = float(np.sum(m))
    r_eff = float((3.0 * pile.mesh_volume / (4.0 * np.pi)) ** (1.0 / 3.0))
    e_bind = binding_energy(m_tot, r_eff)
    ke_thr = ke_frac * e_bind

    solver = WarpSolid3D(
        x0, np.zeros_like(x0), m, np.zeros(n), h, material, RefParams(cfl=cfl),
        # alpha0 VE Y0 birlikte gecirilir: yigin ureticisi ikisini de parcacik
        # basina uretiyor (P3-FR-03/04). Yalnizca alpha0'i gecirmek, bloklari
        # gozeneksiz ama matris kadar zayif yapardi — yarim baglanmis bir
        # heterojenlik, hic olmamasindan daha yaniltici olurdu.
        alpha0=np.ascontiguousarray(pile.alpha0, dtype=np.float64),
        Y0=np.ascontiguousarray(pile.Y0, dtype=np.float64),
        device=device, check_every=10**9,
        gravity_rebuild_every=gravity_rebuild_every,
        gravity_drift_tol=gravity_drift_tol,
    )
    factor = wp.float64(1.0 - damping)

    def _ke() -> float:
        # `budgets()` 11 diziyi GPU'dan cekiyor; burada yalnizca m ve v gerekli.
        # Sicak dongude tam durum kopyasi almak bos maliyettir.
        vv = solver.v.numpy().astype(np.float64)
        mm = solver.m.numpy()
        return 0.5 * float(np.sum(mm * np.sum(vv * vv, axis=1)))

    solver._eval()
    solver._evaluated = True
    ke0 = _ke()
    # Denge TANISI: t=0'da SPH ivmesi ve yercekimi ivmesi ayri ayri. Kurulum
    # denge degilse bu iki sayi hemen gosterir; "settling hallederdi" diye
    # gecistirilmez.
    a0 = np.linalg.norm(solver.state_numpy()["a"], axis=1)
    g0 = np.linalg.norm(solver.g.numpy().astype(np.float64), axis=1)
    a_sph0 = float(np.max(np.abs(a0 - g0)))
    g_max0 = float(g0.max())
    series: list[tuple[int, float]] = [(0, ke0)]
    t = 0.0
    step = 0
    converged = False
    for step in range(1, max_steps + 1):
        dt = solver.compute_dt()
        solver.step(dt)
        wp.launch(I.damp_velocity_3d, dim=n,
                  inputs=[solver.v, solver.active, factor], device=device)
        t += dt
        if step % report_every == 0 or step == max_steps:
            ke = _ke()
            series.append((step, ke))
            if ke < ke_thr:
                converged = True
                break

    st = solver.state_numpy()
    ke_fin = _ke()
    bud = solver.budgets()
    # Serbest dusme suresi yalnizca YOGUNLUGA baglidir (boyuttan bagimsiz):
    # t_ff = sqrt(3 pi / (32 G rho)). Bir t_ff'nin kac adim ettigi, acik
    # integrasyonun yercekimsel oturmayi cozup cozemeyecegini soyler.
    rho_bulk = m_tot / (4.0 / 3.0 * np.pi * r_eff**3)
    t_ff = float(np.sqrt(3.0 * np.pi / (32.0 * G_GRAV * rho_bulk)))
    dt_ort = max(t / max(step, 1), 1.0e-300)
    return SettleResult(
        x=st["x"], v=st["v"], rho=st["rho"], alpha=st["alpha"],
        n_steps=step, t_end=t, ke_series=series,
        ke_initial=ke0, ke_final=ke_fin, ke_threshold=ke_thr,
        binding_energy=e_bind,
        damped_energy=max(ke0 - ke_fin, 0.0),
        converged=converged,
        diagnostics={
            "n_particles": n,
            "total_mass": m_tot,
            "effective_radius": r_eff,
            "smoothing_length": h,
            "damping": damping,
            "ke_over_binding_initial": ke0 / e_bind if e_bind else float("nan"),
            "ke_over_binding_final": ke_fin / e_bind if e_bind else float("nan"),
            "gravity_rebuild_every": int(gravity_rebuild_every),
            "rho_min": float(st["rho"].min()),
            "rho_max": float(st["rho"].max()),
            "alpha_min": float(st["alpha"].min()),
            "alpha_max": float(st["alpha"].max()),
            # denge tanisi (yukaridaki modul basligi)
            "a_sph_max_t0": a_sph0,
            "a_gravity_max_t0": g_max0,
            "free_fall_time": t_ff,
            "steps_per_free_fall": t_ff / dt_ort,
            "simulated_fraction_of_free_fall": t / t_ff,
            # ADR-0024 denetim kaydi (K=1 ise None)
            "tree_drift_max_over_h": bud.get("gravity_tree_drift_max_over_h"),
            "tree_drift_exceeded": bud.get("gravity_tree_drift_exceeded"),
        },
    )
