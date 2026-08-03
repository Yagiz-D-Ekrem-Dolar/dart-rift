"""Tillotson EOS — Warp device fonksiyonlari (P2-FR-03).

CPU referansiyla (cpu_reference/materials.py) birebir ayni formul ve islem
sirasi; test_solid_cross parite ile sinar. Ses hizi ayni merkezli sonlu-fark
formuluyle hesaplanir ve tabanla korunur (negatif/patlayan cs -> dt cokmesi).
"""

from __future__ import annotations

import warp as wp

F = wp.float64


@wp.struct
class TillotsonWp:
    rho0: F
    A: F
    B: F
    a: F
    b: F
    u0: F
    u_iv: F
    u_cv: F
    alpha_t: F
    beta_t: F
    cs_min: F  # onceden hesaplanmis taban [m/s]


def make_tillotson_wp(p) -> TillotsonWp:
    """cpu_reference.materials.TillotsonParams -> Warp struct."""
    t = TillotsonWp()
    t.rho0 = p.rho0
    t.A = p.A
    t.B = p.B
    t.a = p.a
    t.b = p.b
    t.u0 = p.u0
    t.u_iv = p.u_iv
    t.u_cv = p.u_cv
    t.alpha_t = p.alpha_t
    t.beta_t = p.beta_t
    t.cs_min = p.cs_floor_frac * p.cs_ref
    return t


@wp.func
def _till_cold(rho: F, u: F, tp: TillotsonWp) -> F:
    eta = rho / tp.rho0
    mu_t = eta - F(1.0)
    # Carpim SIRASI korunur (bkz. CPU notu): gecerli girdide bit ayni.
    # Tekil noktada (rho == 0) dogru LIMIT: u > 0 ise omega -> inf.
    payda = tp.u0 * eta * eta
    oran = F(0.0)
    if payda != F(0.0):
        oran = u / payda
    elif u > F(0.0):
        oran = F(1.0e300) * F(1.0e300)      # +inf
    omega = oran + F(1.0)
    return (tp.a + tp.b / omega) * rho * u + tp.A * mu_t + tp.B * mu_t * mu_t


@wp.func
def _till_hot(rho: F, u: F, tp: TillotsonWp) -> F:
    eta = rho / tp.rho0
    mu_t = eta - F(1.0)
    # Carpim SIRASI korunur (bkz. CPU notu): gecerli girdide bit ayni.
    # Tekil noktada (rho == 0) dogru LIMIT: u > 0 ise omega -> inf.
    payda = tp.u0 * eta * eta
    oran = F(0.0)
    if payda != F(0.0):
        oran = u / payda
    elif u > F(0.0):
        oran = F(1.0e300) * F(1.0e300)      # +inf
    omega = oran + F(1.0)
    ex = wp.exp(-tp.beta_t * (F(1.0) / eta - F(1.0)))
    ex2 = wp.exp(-tp.alpha_t * (F(1.0) / eta - F(1.0)) * (F(1.0) / eta - F(1.0)))
    return tp.a * rho * u + (tp.b * rho * u / omega + tp.A * mu_t * ex) * ex2


@wp.func
def tillotson_p(rho: F, u_in: F, tp: TillotsonWp) -> F:
    u = wp.max(u_in, F(0.0))
    # K21: rho <= 0 icin genlesmis-sicak kol NaN uretir. `ex` ussu
    # -beta*(1/eta - 1)'dir; eta kucuk NEGATIF iken us buyuk POZITIF olur,
    # exp TASAR (inf) ve `inf * ex2` (ex2 = exp(-cok buyuk) = 0) NaN verir.
    # NaN oradan her komsu toplamina yayilir ve kosuyu SESSIZCE zehirler —
    # GPU'da uyari da yoktur.
    #
    # rho <= 0 ASLA fizik degildir: sureklilikte drho/dt = -rho*div(v) ustel
    # azalir, sifiri ancak dt fazla buyukse gecer. Yani bu her zaman SAYISAL
    # BASARISIZLIKTIR. Burada EOS'u TOPLAM yapiyoruz (sonlu girdi -> sonlu
    # cikti) ama sorunu MASKELEMIYORUZ: cozucu `nonpositive_density_count`
    # sayacini rapor eder ve sifirdan buyukse kosu GECERSIZDIR.
    if rho <= F(0.0):
        return _till_cold(rho, u, tp)
    eta = rho / tp.rho0
    if eta >= F(1.0) or u <= tp.u_iv:
        return _till_cold(rho, u, tp)
    if u >= tp.u_cv:
        return _till_hot(rho, u, tp)
    w = (u - tp.u_iv) / (tp.u_cv - tp.u_iv)
    return (F(1.0) - w) * _till_cold(rho, u, tp) + w * _till_hot(rho, u, tp)


@wp.func
def tillotson_cs(rho: F, u: F, tp: TillotsonWp) -> F:
    """cs^2 = dP/drho|_u + (P/rho^2) dP/du|_rho (merkezli FD, CPU ile ayni)."""
    d_rho = F(1.0e-6) * wp.max(rho, F(1.0e-3) * tp.rho0)
    d_u = F(1.0e-6) * wp.max(wp.abs(u), F(1.0e-6) * tp.u0)
    p0 = tillotson_p(rho, u, tp)
    dp_drho = (tillotson_p(rho + d_rho, u, tp) - tillotson_p(rho - d_rho, u, tp)) / (
        F(2.0) * d_rho
    )
    dp_du = (tillotson_p(rho, u + d_u, tp) - tillotson_p(rho, u - d_u, tp)) / (F(2.0) * d_u)
    cs2 = dp_drho + p0 / (rho * rho) * dp_du
    cs2_min = tp.cs_min * tp.cs_min
    return wp.sqrt(wp.max(cs2, cs2_min))


@wp.kernel
def eos_solid(
    rho: wp.array(dtype=F),
    u: wp.array(dtype=F),
    alpha: wp.array(dtype=F),
    tp: TillotsonWp,
    P: wp.array(dtype=F),
    cs: wp.array(dtype=F),
):
    """P-alpha baglantili Tillotson: P = P_solid(rho*alpha, u) / alpha."""
    i = wp.tid()
    rho_s = rho[i] * alpha[i]
    P[i] = tillotson_p(rho_s, u[i], tp) / alpha[i]
    cs[i] = tillotson_cs(rho_s, u[i], tp)
