"""Completed constitutive updates must reach the next CFL and first kick."""
from dataclasses import replace
from unittest.mock import patch

import numpy as np
import pytest

from dartrift.cpu_reference.materials import (
    ALUMINYUM_TILLOTSON,
    MaterialParams,
    PorosityParams,
    StrengthParams,
    tillotson_pressure,
)
from dartrift.cpu_reference.solid_ref import (
    SolidState,
    compute_timestep_solid,
    evaluate_solid,
    step_kdk_solid,
)
from dartrift.cpu_reference.sph_ref import RefParams


def _case(porous=True, strength=False):
    x = np.array(np.meshgrid(*([[-0.3, 0.0, 0.3]] * 3))).reshape(3, -1).T
    n = len(x)
    mask = np.arange(n) % 2 == 0
    alpha = np.full(n, 2.7 if porous else 1.0)
    mat = MaterialParams(
        eos="tillotson", density_method="continuity",
        strength=StrengthParams(enabled=strength, Y0=100., mu_f=0.),
        porosity=PorosityParams(enabled=porous, alpha0=2.7, Pe=1e6, Ps=1e8))
    rho = 2700. / alpha * (1.05 + 0.01 * np.arange(n) / n)
    v = -30. * x
    v[:, 0] += 10. * x[:, 1]
    st = SolidState(x=x, v=v, m=np.full(n, 1.), u=np.full(n, 1e4),
                    h=np.linspace(0.45, 0.6, n), active=np.ones(n, bool),
                    alpha=alpha, rho=rho, mermi_maske=mask,
                    mermi_tillotson=ALUMINYUM_TILLOTSON)
    return st, mat, RefParams(cfl=0.2, akma_kipi="ara")


def _warp(porous=True, strength=False):
    pytest.importorskip("warp")
    from dartrift.warp_core.solver_solid import WarpSolid3D

    st, mat, num = _case(porous, strength)
    return WarpSolid3D(st.x, st.v, st.m, st.u, st.h, mat, num,
                       alpha0=st.alpha, rho_durum=st.rho, device="cpu",
                       mermi_maske=st.mermi_maske,
                       mermi_tillotson=st.mermi_tillotson)


def _pressure(st, mat):
    p = tillotson_pressure(st["rho"] * st["alpha"], st["u"], mat.tillotson)
    mask = np.arange(len(p)) % 2 == 0
    p[mask] = tillotson_pressure((st["rho"] * st["alpha"])[mask],
                                 st["u"][mask], ALUMINYUM_TILLOTSON)
    return p / st["alpha"]


@pytest.mark.warp
def test_cfl_refreshes_zero_time_compaction_pressure_and_force():
    sol = _warp()
    sol.step(0.)
    assert sol.alpha.numpy().max() < 2.7 - 0.01
    dt = sol.compute_dt()
    st = sol.state_numpy()
    np.testing.assert_allclose(st["P"], _pressure(st, sol.mat), rtol=1e-10)
    a, cs = sol.a.numpy().copy(), sol.cs.numpy().copy()
    sol._eval()  # Independent explicit evaluation of the final physical state.
    np.testing.assert_array_equal(sol.a.numpy(), a)
    np.testing.assert_array_equal(sol.cs.numpy(), cs)
    assert sol.compute_dt() == dt


@pytest.mark.warp
@pytest.mark.parametrize("porous,strength", [(True, False), (False, True)])
@pytest.mark.parametrize("use_cfl", [False, True])
def test_dynamic_steps_match_explicit_final_state_evaluation(porous, strength, use_cfl):
    sol, oracle = _warp(porous, strength), _warp(porous, strength)
    for _ in range(4):
        oracle._eval()
        oracle._evaluated = True
        if use_cfl:
            sol.hazirla()
            dt = min(sol.compute_dt(), 1e-7)
            assert sol.compute_dt() == pytest.approx(oracle.compute_dt(), rel=1e-12)
        else:
            dt = 1e-7
        sol.step(dt)
        oracle.step(dt)
        for key in ("x", "v", "rho", "u", "S", "alpha"):
            np.testing.assert_allclose(sol.state_numpy()[key], oracle.state_numpy()[key],
                                       rtol=1e-12, atol=1e-12, err_msg=key)


@pytest.mark.warp
def test_cfl_and_kick_share_one_refresh_and_observation_stays_read_only():
    sol = _warp(strength=True)
    sol.step(1e-7)
    with patch.object(sol, "_eval", wraps=sol._eval) as evaluate:
        before = sol.state_numpy()
        sol.budgets()
        assert evaluate.call_count == 0
        np.testing.assert_array_equal(sol.state_numpy()["S"], before["S"])
        sol.compute_dt()
        assert evaluate.call_count == 1
        sol.compute_dt()
        sol.hazirla()
        assert evaluate.call_count == 1
        sol.step(1e-7)
        assert evaluate.call_count == 3  # Two KDK evaluations, no duplicate refresh.


@pytest.mark.parametrize("porous,strength", [(True, False), (False, True)])
@pytest.mark.parametrize("use_cfl", [False, True])
def test_cpu_dynamic_cache_matches_explicit_evaluation(porous, strength, use_cfl):
    st, mat, num = _case(porous, strength)
    oracle, _, _ = _case(porous, strength)
    evaluate_solid(st, mat, num)
    for _ in range(4):
        evaluate_solid(oracle, mat, num)
        if use_cfl:
            assert compute_timestep_solid(st, mat, num) == pytest.approx(
                compute_timestep_solid(oracle, mat, num), rel=1e-12)
        step_kdk_solid(st, mat, num, 1e-7)
        step_kdk_solid(oracle, mat, num, 1e-7)
        for key in ("x", "v", "rho", "u", "S", "alpha"):
            np.testing.assert_allclose(getattr(st, key), getattr(oracle, key),
                                       rtol=1e-12, atol=1e-12, err_msg=key)


def test_porosity_off_momentum_and_energy_under_timestep_refinement():
    errors = []
    for dt in (1e-7, 5e-8):
        st, mat, num = _case(porous=False)
        mat = replace(mat, strength=StrengthParams(enabled=False))
        evaluate_solid(st, mat, num)
        p0 = np.sum(st.m[:, None] * st.v, axis=0)
        e0 = np.sum(st.m * (st.u + 0.5 * np.sum(st.v**2, axis=1)))
        for _ in range(round(1e-6 / dt)):
            step_kdk_solid(st, mat, num, dt)
        p1 = np.sum(st.m[:, None] * st.v, axis=0)
        e1 = np.sum(st.m * (st.u + 0.5 * np.sum(st.v**2, axis=1)))
        assert np.linalg.norm(p1 - p0) < 1e-11
        errors.append(abs(e1 / e0 - 1))
    assert errors[0] < 1e-4
    assert errors[1] < 0.75 * errors[0]
