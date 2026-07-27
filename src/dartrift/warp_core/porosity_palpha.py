"""P-alpha porozite crush-curve guncellemesi (P2-FR-04, §5.3).

CPU referansi: cpu_reference/materials.py::porosity_update. Geri genlesme yok:
alpha yalnizca azalabilir ve alpha >= 1. Sikisma isi cift-terimli PdV isinde
muhasebe edilir (ayrica eklenmez — cifte sayim olur; ADR-0008).
"""

from __future__ import annotations

import warp as wp

F = wp.float64


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


@wp.kernel
def porosity_update_k(
    alpha: wp.array(dtype=F),
    P: wp.array(dtype=F),
    active: wp.array(dtype=wp.uint8),
    pp: PorosityWp,
):
    i = wp.tid()
    if active[i] == wp.uint8(0):
        return
    a_curve = wp.max(F(1.0), crush_alpha(P[i], pp))
    alpha[i] = wp.min(alpha[i], a_curve)  # geri genlesme yok, alpha >= 1
