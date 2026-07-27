"""Sedov-Taylor patlamasi senaryosu (P1-VR-05).

Nokta enerji enjeksiyonu, kendine-benzer sok: r_s(t) = (E t^2 / (alpha rho0))^(1/5).
gamma=1.4 icin enerji integrali sabiti alpha = 0.8511 (Sedov 1959; Book 1994).
Sok yarcapi radyal yogunluk profilinin tepe noktasindan olculur.
"""

from __future__ import annotations

import numpy as np

from ..cpu_reference.sph_ref import RefParams

GAMMA = 1.4
SEDOV_ALPHA = 0.8511  # gamma=1.4, kuresel (Sedov/Book literatur degeri)
E_INJECT = 1.0
RHO0 = 1.0
U_BACKGROUND = 1.0e-6
H_OVER_DX = 1.25

# Kosu suresi, sok yaricapinin domain yari-genisliginin YARISINA ulastigi ana
# sabitlenir (r_s = 0.25, domain [-0.5,0.5]^3). Daha gec zamanlarda cephe
# kubun yuzune yaklasir ve olcum kenar etkileriyle bozulur.
T_END_DEFAULT = 0.0288  # -> r_s ~ 0.2500

# Enerji enjeksiyon olcegi SABIT FIZIKSEL uzunluktur, h'nin katı DEGILDIR.
# Bu ayrim yakinsama testinin gecerliligi icin zorunludur: h'ye bagli bir
# enjeksiyon yaricapi kullanildiginda her cozunurluk FARKLI bir baslangic
# kosulu (dolayisiyla farkli bir fiziksel problem) cozer ve olculen hata
# cozunurlukle KUCULMEZ — ilk kurulumda tam olarak bu gozlendi (ADR-0011).
# Destek yaricapi 2*H_INJECT = 0.08; en kaba kafeste (n=32, h=0.039) bile
# kernel destegi kadar, en incede (n=64) 4h genisliginde kalir.
H_INJECT = 0.04


def shock_radius_exact(t: float) -> float:
    return (E_INJECT * t * t / (SEDOV_ALPHA * RHO0)) ** 0.2


def build_sedov_ic(n_side: int, h_inject: float = H_INJECT) -> dict:
    """[-0.5,0.5]^3 kafesi; merkezde kernel-agirlikli enerji enjeksiyonu.

    Enjeksiyon olcegi `h_inject` SABITTIR (bkz. H_INJECT notu): boylece tum
    cozunurlukler ayni baslangic kosulunu — ayni fiziksel problemi — cozer.
    """
    dx = 1.0 / n_side
    axis = (np.arange(n_side) + 0.5) * dx - 0.5
    xx, yy, zz = np.meshgrid(axis, axis, axis, indexing="ij")
    x = np.column_stack([xx.ravel(), yy.ravel(), zz.ravel()])
    n = x.shape[0]
    m = np.full(n, RHO0 * dx**3)
    u = np.full(n, U_BACKGROUND)
    h = H_OVER_DX * dx
    r = np.sqrt(np.sum(x * x, axis=1))
    # 3B Wendland C2 agirliklariyla enerji dagit
    q = r / h_inject
    t = np.maximum(1.0 - 0.5 * q, 0.0)
    w = np.where(q < 2.0, t**4 * (2.0 * q + 1.0), 0.0)
    wsum = np.sum(m * w)
    if wsum <= 0.0:
        raise ValueError(
            f"enjeksiyon bolgesi bos: h_inject={h_inject} kafes araligi dx={dx} "
            "icin cok kucuk (hicbir parcacik destek icinde degil)"
        )
    u += E_INJECT * w / wsum  # ozgul enerji: E * w_i / sum(m w)
    return {
        "x": x, "v": np.zeros_like(x), "m": m, "u": u, "h": h, "dx": dx,
        "n_injected": int(np.count_nonzero(w > 0.0)),
        "r_inject": 2.0 * h_inject,
    }


def radial_profile(
    x: np.ndarray, val: np.ndarray, n_bins: int = 80, r_max: float = 0.48, min_count: int = 8
):
    """Radyal binlenmis ortalama profil (bos binler NaN)."""
    r = np.sqrt(np.sum(x * x, axis=1))
    edges = np.linspace(0.0, r_max, n_bins + 1)
    idx = np.digitize(r, edges) - 1
    prof = np.full(n_bins, np.nan)
    for b in range(n_bins):
        sel = idx == b
        if np.count_nonzero(sel) >= min_count:
            prof[b] = np.mean(val[sel])
    return 0.5 * (edges[:-1] + edges[1:]), prof


def measure_shock_radius(x: np.ndarray, rho: np.ndarray, n_bins: int = 80) -> float:
    """Sok yaricapi: radyal yogunluk profilinin tepesi (parabolik incelik).

    SPH'de cephe ~2-3h kalinliktadir; tepe konumu, dis-yamac gradyanina gore
    cozunurlukten daha az etkilenen olcudur (her iki kestirimci de olculdu,
    bkz. ADR-0011).
    """
    centers, prof = radial_profile(x, rho, n_bins=n_bins)
    valid = np.isfinite(prof)
    if not np.any(valid):
        raise ValueError("radyal profil bos: bin basina yeterli parcacik yok")
    pk = int(np.nanargmax(prof))
    if 0 < pk < n_bins - 1 and valid[pk - 1] and valid[pk + 1]:
        y0, y1, y2 = prof[pk - 1], prof[pk], prof[pk + 1]
        denom = y0 - 2.0 * y1 + y2
        if abs(denom) > 1.0e-300:
            shift = 0.5 * (y0 - y2) / denom
            return float(centers[pk] + shift * (centers[1] - centers[0]))
    return float(centers[pk])


def run_sedov_warp(n_side: int, device: str, t_end: float = T_END_DEFAULT,
                   params: RefParams | None = None, max_steps: int = 500_000,
                   h_inject: float = H_INJECT) -> dict:
    """Sedov'u Warp 3B hash-grid cozucusuyle kostur.

    `h_inject` acikca gecirilebilir: modul duzeyindeki H_INJECT'i sonradan
    degistirmek ETKISIZDIR (varsayilan deger fonksiyon tanimlanirken baglanir).
    """
    from ..warp_core.solver import WarpSPH3D

    ic = build_sedov_ic(n_side, h_inject=h_inject)
    params = params or RefParams(gamma=GAMMA)
    solver = WarpSPH3D(
        ic["x"], ic["v"], ic["m"], ic["u"], ic["h"], params, device=device,
    )
    diag = solver.run(t_end, max_steps=max_steps)
    # Kismi kosu SESSIZCE gecerli sayilmaz: t_end'e ulasilmadan olculen yaricap
    # sistematik olarak kucuk cikar ve "cozunurlukle kotulesen hata" gibi
    # gorunur (ADR-0011). Adim butcesi bittiyse acik hata verilir.
    if diag["t_end"] < t_end * (1.0 - 1.0e-9):
        raise RuntimeError(
            f"Sedov t_end'e ULASILAMADI: {diag['t_end']:.6g} < {t_end:.6g} "
            f"({diag['n_steps']} adim, max_steps={max_steps}). Olcum gecersiz."
        )
    s = solver.state_numpy()
    r_meas = measure_shock_radius(s["x"], s["rho"])
    r_exact = shock_radius_exact(t_end)
    from ..cpu_reference.sph_ref import conservation_errors

    cons = conservation_errors(diag)
    r_prof = np.sqrt(np.sum(s["x"] * s["x"], axis=1))
    ke = 0.5 * float(np.sum(s["m"] * np.sum(s["v"] * s["v"], axis=1)))
    return {
        "n_side": n_side,
        "t_end": t_end,
        "shock_radius_measured": r_meas,
        "shock_radius_exact": r_exact,
        "shock_radius_rel_err": abs(r_meas - r_exact) / r_exact,
        # Sedov benzerlik cozumunde kinetik enerji orani gamma=1.4 icin ~0.28;
        # bu, "enerji gercekten soka gitti mi" sorusunun bagimsiz gostergesi.
        "kinetic_fraction": ke / E_INJECT,
        "n_injected": ic["n_injected"],
        "r_inject": ic["r_inject"],
        "conservation": cons,
        "n_steps": diag["n_steps"],
        "timestep_summary": diag["timestep_summary"],
        "profile": {
            "r": r_prof[:: max(1, len(r_prof) // 20000)].tolist(),
            "rho": s["rho"][:: max(1, len(r_prof) // 20000)].tolist(),
        },
    }
