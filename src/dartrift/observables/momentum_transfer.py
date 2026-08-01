"""Momentum aktarim katsayisi beta (P3-FR-08, P3-VR-03).

TANIM. Merminin getirdigi momentum p_m; hedefin kazandigi momentum p_h.
Ejekta geri tepmesi olmasaydi p_h = p_m olurdu (beta = 1). Kacan ejekta ters
yonde momentum tasidigi icin:

    beta = 1 + |p_ejekta| / |p_mermi|          (mermi yonune izdusum)

Iki yoldan da hesaplanir:
    beta_ejekta = 1 - (p_ejekta . e) / |p_mermi|
    beta_bagli  =     (p_bagli  . e) / |p_mermi|
DIKKAT: bu ikisi BAGIMSIZ olcumler DEGILDIR. Momentum tam korunuyorsa
p_bagli + p_ejekta = p_mermi olur ve iki ifade cebirsel olarak ozdestir.
Dolayisiyla farklari yeni bir fizik dogrulamaz; farkları MOMENTUM DEFTERININ
KAPANMA HATASIDIR ve tam olarak o ad altinda raporlanir. (Bunu "bagimsiz
capraz kontrol" diye sunmak, hicbir sey sinamayan bir kontrolu sinama gibi
gostermek olurdu.)

KONTROL YUZEYI DUYARLILIGI (P3-VR-03). "Kacan" tanimi bir esige baglidir:
hangi parcacik ejektadir? Tek bir esik secip beta'yi tek sayi olarak vermek,
kesin olmayan bir seyi kesin gostermektir. Bu yuzden beta, kontrol yuzeyi
yaricapi ve hiz esigi taramasi uzerinde raporlanir ve duyarliligi ciktinin
parcasidir.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

__all__ = ["BetaResult", "escape_speed", "momentum_transfer", "beta_sensitivity"]


@dataclass(frozen=True)
class BetaResult:
    """beta ve onu ureten butun ara buyukluklerle birlikte."""

    beta: float
    p_impactor: float                 # |p_mermi| [kg m/s]
    p_ejecta_axial: float             # ejekta momentumunun mermi eksenindeki bileseni
    p_ejecta_vec: np.ndarray          # (3,) ejekta momentum vektoru
    ejecta_mass: float                # kacan kutle [kg]
    ejecta_fraction: float            # kacan kutle / hedef kutlesi
    n_ejecta: int
    beta_from_bound: float            # ayni beta, bagli kutlenin momentumundan
    momentum_closure: float           # |p_bagli + p_ejekta - p_mermi| / |p_mermi|
    criteria: dict = field(default_factory=dict)
    diagnostics: dict = field(default_factory=dict)


def escape_speed(mass: float, radius: float, G: float = 6.6743e-11) -> float:
    """sqrt(2 G M / R) — kacis hizi."""
    if mass <= 0.0 or radius <= 0.0:
        raise ValueError("kutle ve yaricap pozitif olmali")
    return float(np.sqrt(2.0 * G * mass / radius))


def momentum_transfer(
    x: np.ndarray,
    v: np.ndarray,
    m: np.ndarray,
    *,
    impactor_momentum: np.ndarray,
    center: np.ndarray | None = None,
    target_mass: float | None = None,
    target_radius: float | None = None,
    control_radius: float | None = None,
    speed_threshold: float | None = None,
    G: float = 6.6743e-11,
) -> BetaResult:
    """beta'yi kacan ejektanin momentumundan hesapla.

    Bir parcacik EJEKTA sayilir eger:
      (a) kontrol yuzeyinin disindaysa (|x - merkez| > control_radius), VE
      (b) radyal hizi kacis hizini asiyorsa (v_r > speed_threshold).

    (b) sart: kontrol yuzeyini gecmek tek basina kacmak degildir — yavas
    ejekta geri duser ve momentumu hedefe geri verir. Yalnizca (a) kullanmak
    beta'yi sistematik olarak BUYUK gosterirdi.
    """
    x = np.ascontiguousarray(x, dtype=np.float64)
    v = np.ascontiguousarray(v, dtype=np.float64)
    m = np.ascontiguousarray(m, dtype=np.float64)
    if not (len(x) == len(v) == len(m)):
        raise ValueError(f"x/v/m uzunluklari esit olmali: {len(x)}/{len(v)}/{len(m)}")
    if len(m) == 0:
        raise ValueError("bos durum")

    p_imp = np.asarray(impactor_momentum, dtype=np.float64).reshape(3)
    p_imp_mag = float(np.linalg.norm(p_imp))
    if p_imp_mag <= 0.0:
        raise ValueError("mermi momentumu sifir olamaz")
    ehat = p_imp / p_imp_mag

    m_tot = float(np.sum(m))
    c = (np.sum(m[:, None] * x, axis=0) / m_tot) if center is None else \
        np.asarray(center, dtype=np.float64).reshape(3)

    r = x - c[None, :]
    dist = np.linalg.norm(r, axis=1)
    m_target = m_tot if target_mass is None else float(target_mass)
    r_target = float(np.median(dist)) if target_radius is None else float(target_radius)
    r_ctrl = 2.0 * r_target if control_radius is None else float(control_radius)
    v_esc = escape_speed(m_target, r_target, G)
    v_thr = v_esc if speed_threshold is None else float(speed_threshold)

    with np.errstate(invalid="ignore", divide="ignore"):
        rhat = np.where(dist[:, None] > 0.0, r / np.maximum(dist, 1e-300)[:, None], 0.0)
    v_rad = np.einsum("ij,ij->i", v, rhat)

    is_ejecta = (dist > r_ctrl) & (v_rad > v_thr)
    p_ej = np.sum(m[is_ejecta, None] * v[is_ejecta], axis=0)
    p_ej_ax = float(np.dot(p_ej, ehat))

    # beta = 1 - (p_ejekta . e) / |p_mermi|
    # Ejekta mermiye TERS yonde firlar, yani p_ej_ax < 0 beklenir; bu beta'yi
    # 1'in USTUNE cikarir. Ters isaret fiziksel olarak anlamsizdir ve mutlak
    # deger alinarak GIZLENMEZ — `ejecta_direction_ok` tanisi olarak raporlanir.
    beta = 1.0 - p_ej_ax / p_imp_mag

    p_bound = np.sum(m[~is_ejecta, None] * v[~is_ejecta], axis=0)
    beta_b = float(np.dot(p_bound, ehat)) / p_imp_mag
    # Momentum defteri kapaniyor mu: p_bagli + p_ejekta =? p_mermi
    closure = float(np.linalg.norm(p_bound + p_ej - p_imp)) / p_imp_mag

    m_ej = float(np.sum(m[is_ejecta]))
    return BetaResult(
        beta=float(beta),
        p_impactor=p_imp_mag,
        p_ejecta_axial=p_ej_ax,
        p_ejecta_vec=p_ej,
        ejecta_mass=m_ej,
        ejecta_fraction=m_ej / m_tot,
        n_ejecta=int(np.count_nonzero(is_ejecta)),
        beta_from_bound=beta_b,
        momentum_closure=closure,
        criteria={
            "control_radius": r_ctrl,
            "speed_threshold": v_thr,
            "escape_speed": v_esc,
            "target_radius": r_target,
            "target_mass": m_target,
            "center": c,
        },
        diagnostics={
            "n_total": int(len(m)),
            "total_mass": m_tot,
            "max_distance": float(dist.max()),
            "max_radial_speed": float(v_rad.max()),
            "ejecta_direction_ok": bool(p_ej_ax < 0.0),
            "p_ejecta_transverse": float(
                np.linalg.norm(p_ej - p_ej_ax * ehat)),
        },
    )


def beta_sensitivity(
    x: np.ndarray,
    v: np.ndarray,
    m: np.ndarray,
    *,
    impactor_momentum: np.ndarray,
    control_radii: np.ndarray | list[float],
    speed_factors: np.ndarray | list[float] = (0.5, 1.0, 2.0),
    **kw,
) -> dict:
    """beta'nin kontrol yuzeyi ve hiz esigine duyarliligi (P3-VR-03).

    Donen sozlukte `beta_grid` (len(r) x len(f)) ve tarama uzerindeki
    yayilim yer alir. Yayilim, beta'nin RAPORLANAN belirsizliginin alt
    siniridir: tanim secimi bile bu kadar oynatiyorsa, daha dar bir hata
    cubugu iddia edilemez.
    """
    rr = np.asarray(control_radii, dtype=np.float64).ravel()
    ff = np.asarray(speed_factors, dtype=np.float64).ravel()
    if rr.size < 2:
        raise ValueError("duyarlilik icin en az 2 kontrol yaricapi gerekir")
    if np.any(rr <= 0.0) or np.any(ff <= 0.0):
        raise ValueError("yaricap ve carpanlar pozitif olmali")
    # `control_radius`/`speed_threshold` tarama degiskenleridir; kw ile de
    # gelirlerse asagidaki cagrida ayni argüman iki kez verilir ve TypeError
    # olur. Sessiz ezmek yerine ACIK reddediliyor: tarama yapan bir fonksiyona
    # sabit bir tarama degeri vermek, cagiranin niyetinin belirsiz oldugunu
    # gosterir.
    cakisan = {"control_radius", "speed_threshold"} & set(kw)
    if cakisan:
        raise ValueError(
            f"{sorted(cakisan)} tarama degiskenidir, kw ile verilemez; "
            "control_radii / speed_factors kullanin")

    base = momentum_transfer(x, v, m, impactor_momentum=impactor_momentum, **kw)
    v_esc = base.criteria["escape_speed"]
    grid = np.empty((rr.size, ff.size), dtype=np.float64)
    frac = np.empty_like(grid)
    for i, rc in enumerate(rr):
        for j, f in enumerate(ff):
            b = momentum_transfer(
                x, v, m, impactor_momentum=impactor_momentum,
                control_radius=float(rc), speed_threshold=float(f * v_esc), **kw)
            grid[i, j] = b.beta
            frac[i, j] = b.ejecta_fraction
    return {
        "control_radii": rr,
        "speed_factors": ff,
        "escape_speed": v_esc,
        "beta_grid": grid,
        "ejecta_fraction_grid": frac,
        "beta_min": float(grid.min()),
        "beta_max": float(grid.max()),
        "beta_median": float(np.median(grid)),
        "beta_spread": float(grid.max() - grid.min()),
        "beta_relative_spread": float(
            (grid.max() - grid.min()) / max(abs(np.median(grid)), 1e-300)),
        "base": base,
    }
