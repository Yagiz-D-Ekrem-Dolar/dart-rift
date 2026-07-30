"""P-alpha porozite crush-curve guncellemesi (P2-FR-04, §5.3).

CPU referansi: cpu_reference/materials.py::solve_alpha_implicit. Geri genlesme
yok: alpha yalnizca azalabilir ve alpha >= 1. Sikisma isi cift-terimli PdV
isinde muhasebe edilir (ayrica eklenmez — cifte sayim olur; ADR-0008).

ORTUK COZUM (ADR-0023): alpha, bir onceki adimin P'sinden ACIK olarak
okunamaz. Tillotson gibi sert bir EOS'ta crush egrisi cok dar bir basinc
araliginda asilir ve acik guncelleme ASIRI ATAR — olcumde alpha, sikistirma
hizindan bagimsiz olarak tek adimda 1.5'ten 1.0'a cokuyordu. Bunun yerine

    alpha = crush_alpha( P_kati(alpha*rho, u) / alpha )

denklemi [1, alpha_eski] araliginda bisection ile cozulur. Kalinti bu
aralikta monotondur, dolayisiyla bisection kararlidir ve sabit adim sayisiyla
DETERMINISTIKTIR (ADR-0002).
"""

from __future__ import annotations

import warp as wp

from .eos_tillotson import TillotsonWp, tillotson_p

F = wp.float64

# Bisection adim sayisi: [1, 2.5] araliginda 2^-40 ~ 1e-12 hassasiyet.
# SABIT sayida adim: kosudan kosuya ayni is, ayni sonuc (ADR-0002).
BISECTION_STEPS = 40


@wp.struct
class PorosityWp:
    alpha0: F
    Pe: F
    Ps: F
    n_exp: F


def make_porosity_wp(p) -> PorosityWp:
    s = PorosityWp()
    s.alpha0 = p.alpha0
    s.Pe = p.Pe
    s.Ps = p.Ps
    s.n_exp = p.n_exp
    return s


@wp.func
def crush_alpha(P: F, pp: PorosityWp) -> F:
    if P <= pp.Pe:
        return pp.alpha0
    if P >= pp.Ps:
        return F(1.0)
    t = (pp.Ps - P) / (pp.Ps - pp.Pe)
    return F(1.0) + (pp.alpha0 - F(1.0)) * wp.pow(t, pp.n_exp)


@wp.func
def _residual(a: F, alpha_old: F, rho: F, u: F, pp: PorosityWp, tp: TillotsonWp) -> F:
    """a - hedef(a).  hedef = clamp(crush_alpha(P_kati(a*rho,u)/a), 1, alpha_old)"""
    p = tillotson_p(a * rho, u, tp) / a
    target = wp.min(alpha_old, wp.max(F(1.0), crush_alpha(p, pp)))
    return a - target


@wp.kernel
def porosity_update_k(
    alpha: wp.array(dtype=F),
    rho: wp.array(dtype=F),
    u: wp.array(dtype=F),
    active: wp.array(dtype=wp.uint8),
    pp: PorosityWp,
    tp: TillotsonWp,
):
    i = wp.tid()
    if active[i] == wp.uint8(0):
        return
    a_old = alpha[i]
    if a_old <= F(1.0):
        return                                   # zaten tam sikismis
    lo = F(1.0)
    hi = a_old
    for _ in range(BISECTION_STEPS):
        mid = F(0.5) * (lo + hi)
        if _residual(mid, a_old, rho[i], u[i], pp, tp) < F(0.0):
            lo = mid
        else:
            hi = mid
    alpha[i] = wp.min(a_old, F(0.5) * (lo + hi))  # geri genlesme yok
