"""P1 §6.2: 1B plate impact — post-sok durum analitik cozume yakin."""

import pytest

from dartrift.particles import warp_available
from dartrift.validation.plate import U_IMPACT, analytic_post_shock, run_plate_cpu

needs_warp = pytest.mark.skipif(not warp_available(), reason="warp yok")


class TestAnalytic:
    def test_closed_form_satisfies_jump_conditions(self):
        # kutle: rho*(Us-u) = rho0*Us ; momentum: P* = rho0*Us*u ; EOS tutarli
        ex = analytic_post_shock()
        us, u = ex["shock_speed_material"], U_IMPACT
        assert ex["rho_star"] * (us - u) == pytest.approx(1.0 * us, rel=1e-12)
        assert ex["p_star"] == pytest.approx(us * u, rel=1e-12)
        # lineer EOS: P* = c0^2 (rho* - rho0)
        assert ex["p_star"] == pytest.approx(ex["rho_star"] - 1.0, rel=1e-12)

    def test_weak_shock_limit(self):
        # u -> 0: Us -> c0 (akustik limit)
        ex = analytic_post_shock(u=1e-9)
        assert ex["shock_speed_material"] == pytest.approx(1.0, rel=1e-6)


class TestPlateCpu:
    @pytest.fixture(scope="class")
    def result(self):
        return run_plate_cpu(resolution=256)

    def test_post_shock_state(self, result):
        assert result["max_rel_err"] < 0.05, f"rel_err: {result['rel_err']}"


@needs_warp
class TestPlateWarp:
    def test_post_shock_state(self):
        from dartrift.validation.plate import run_plate_warp

        result = run_plate_warp(resolution=256, device="cpu")
        assert result["max_rel_err"] < 0.05, f"rel_err: {result['rel_err']}"
