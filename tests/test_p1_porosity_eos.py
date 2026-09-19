"""Porous projectile compaction must use the same EOS as its pressure."""
from dataclasses import replace

import numpy as np
import pytest

from dartrift.cpu_reference.materials import (
    ALUMINYUM_TILLOTSON,
    MaterialParams,
    PorosityParams,
    StrengthParams,
    solve_alpha_implicit,
)
from dartrift.cpu_reference.solid_ref import SolidState, _apply_strength_and_porosity


def case():
    mat = MaterialParams(eos="tillotson", density_method="continuity",
                         strength=StrengthParams(enabled=False),
                         porosity=PorosityParams(enabled=True, alpha0=2.7,
                                                Pe=1e6, Ps=1e8))
    rho = np.array([1050., 1200., 1500.] * 2)
    u = np.array([0., 1e4, 1e5] * 2)
    a0 = np.full(6, 2.7)
    mask = np.array([False] * 3 + [True] * 3)
    reference = solve_alpha_implicit(a0, rho, u, mat, alpha_ref=a0)
    reference[mask] = solve_alpha_implicit(
        a0[mask], rho[mask], u[mask], replace(mat, tillotson=ALUMINYUM_TILLOTSON),
        alpha_ref=a0[mask])
    return mat, rho, u, a0, mask, reference


def test_cpu_compaction_uses_projectile_eos():
    mat, rho, u, a0, mask, reference = case()
    st = SolidState(x=np.arange(18).reshape(6, 3).astype(float),
                    v=np.zeros((6, 3)), m=np.ones(6), u=u, h=1.,
                    active=np.ones(6, bool), rho=rho, alpha=a0.copy(),
                    mermi_maske=mask, mermi_tillotson=ALUMINYUM_TILLOTSON)
    st.alpha_ref = a0.copy()
    _apply_strength_and_porosity(st, mat)
    np.testing.assert_allclose(st.alpha, reference, rtol=0, atol=2e-12)
    assert abs(reference[0] - reference[3]) > 1e-4


@pytest.mark.warp
def test_solver_routes_compaction_and_keeps_inactive_particle():
    pytest.importorskip("warp")
    from dartrift.warp_core.solver_solid import WarpSolid3D

    mat, rho, u, a0, mask, reference = case()
    active = np.ones(6, bool)
    active[-1] = False
    sol = WarpSolid3D(np.arange(18).reshape(6, 3).astype(float) * 100,
                      np.zeros((6, 3)), np.ones(6), u, 1., mat,
                      alpha0=a0, rho_durum=rho, active=active, device="cpu",
                      mermi_maske=mask, mermi_tillotson=ALUMINYUM_TILLOTSON)
    sol.step(0.)  # Isolate the algebraic compaction update from motion.
    reference[-1] = a0[-1]
    np.testing.assert_allclose(sol.state_numpy()["alpha"], reference, rtol=0, atol=2e-12)
