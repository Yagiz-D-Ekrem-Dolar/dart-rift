"""Basinca bagli dayanim + von Mises return mapping (P2-FR-02, §5.2).

CPU referansi: cpu_reference/materials.py::return_mapping — ayni formuller.
Plastik is ic enerjiye gider: du = f(1-f)(S_t:S_t)/(2 G rho) >= 0.
"""

from __future__ import annotations

import warp as wp

F = wp.float64
M3 = wp.mat33d


@wp.struct
class StrengthWp:
    Y0: F
    mu_f: F
    YM: F
    shear_G: F


def make_strength_wp(p) -> StrengthWp:
    s = StrengthWp()
    s.Y0 = p.Y0
    s.mu_f = p.mu_f
    s.YM = p.YM
    s.shear_G = p.shear_G
    return s


@wp.func
def yield_stress(P: F, sp: StrengthWp) -> F:
    """Lundborg/Collins Y(P); cekmede Y0'a sabit (hasar D=0 bu fazda)."""
    Pp = wp.max(P, F(0.0))
    return sp.Y0 + sp.mu_f * Pp / (F(1.0) + sp.mu_f * Pp / (sp.YM - sp.Y0))


@wp.kernel
def return_mapping_k(
    S: wp.array(dtype=M3),
    P: wp.array(dtype=F),
    rho: wp.array(dtype=F),
    u: wp.array(dtype=F),
    active: wp.array(dtype=wp.uint8),
    sp: StrengthWp,
    plastic_du: wp.array(dtype=F),
):
    i = wp.tid()
    if active[i] == wp.uint8(0):
        plastic_du[i] = F(0.0)
        return
    si = S[i]
    j2 = F(0.5) * wp.ddot(si, si)
    vm = wp.sqrt(F(3.0) * j2)
    y = yield_stress(P[i], sp)
    du = F(0.0)
    if vm > y and vm > F(0.0):
        f = y / vm
        S[i] = f * si
        du = f * (F(1.0) - f) * (F(2.0) * j2) / (F(2.0) * sp.shear_G * rho[i])
        u[i] = u[i] + du
    plastic_du[i] = du
