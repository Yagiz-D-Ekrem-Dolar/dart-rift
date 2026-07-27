"""P1-VR-04: Sod sok tupu analitik cozume %3-5 + korunum esikleri."""

import numpy as np
import pytest

from dartrift.particles import warp_available
from dartrift.validation.riemann import (
    SOD_LEFT,
    SOD_RIGHT,
    sample_profile,
    solve_riemann,
)
from dartrift.validation.sod import run_sod_cpu, run_sod_warp

needs_warp = pytest.mark.skipif(not warp_available(), reason="warp yok")

TOL = 0.05  # sartname: %3-5; kapi esigi olarak 5 kullanilir ve raporlanir


class TestExactRiemann:
    """Kesin cozucu — literatur degerleriyle (Toro, Tablo 4.1, Sod problemi)."""

    def test_star_region_matches_literature(self):
        sol = solve_riemann(SOD_LEFT, SOD_RIGHT, 1.4)
        assert sol.p_star == pytest.approx(0.30313, rel=1e-4)
        assert sol.v_star == pytest.approx(0.92745, rel=1e-4)
        assert sol.rho_star_left == pytest.approx(0.42632, rel=1e-4)
        assert sol.rho_star_right == pytest.approx(0.26557, rel=1e-4)

    def test_shock_speed(self):
        sol = solve_riemann(SOD_LEFT, SOD_RIGHT, 1.4)
        # S = v_R + a_R*sqrt((gp/2g) p*/P_R + gm/2g)
        assert sol.shock_speed == pytest.approx(1.75216, rel=1e-4)

    def test_profile_is_piecewise_consistent(self):
        sol = solve_riemann(SOD_LEFT, SOD_RIGHT, 1.4)
        x = np.linspace(-0.5, 0.5, 2001)
        rho, v, p = sample_profile(sol, x, 0.2)
        assert rho[0] == SOD_LEFT.rho and rho[-1] == SOD_RIGHT.rho
        assert np.all(rho > 0) and np.all(p > 0)
        # temas yuzeyinde basinc/hiz surekli, yogunluk sicramali
        i_contact = np.searchsorted(x, sol.v_star * 0.2)
        assert p[i_contact - 2] == pytest.approx(p[i_contact + 2], rel=1e-12)


class TestSodCpu:
    @pytest.fixture(scope="class")
    def result(self):
        return run_sod_cpu(resolution=256)

    def test_post_shock_within_tolerance(self, result):
        assert result["max_rel_err"] < TOL, f"rel_err: {result['rel_err']}"

    def test_mass_conservation_machine_precision(self, result):
        assert result["conservation"]["mass_rel"] < 1.0e-13  # P1-VR-01

    def test_momentum_budget_closes_with_wall_impulse(self, result):
        # Sod IZOLE DEGIL: donmus bantlar duvar; kazanc (P_L-P_R)*t ile kapanmali.
        # (Izole momentum korunumu <1e-6 esigi test_conservation'da sinanir.)
        mb = result["momentum_budget"]
        assert mb["closure_rel_err"] < 0.02, mb

    def test_energy_conservation(self, result):
        # duvarlar is yapmaz (temas bolgesi statik) -> enerji korunmali
        assert result["conservation"]["energy_rel"] < 0.005  # P1-VR-03

    def test_continuity_cross_check_tracks_summation(self, result):
        # P1-FR-02: iki yogunluk yontemi sok boyunca birbirini izlemeli
        assert result["continuity_max_rel_dev"] < 0.10


@needs_warp
class TestSodWarp:
    @pytest.fixture(scope="class")
    def result(self):
        return run_sod_warp(resolution=256, device="cpu")

    def test_post_shock_within_tolerance(self, result):
        assert result["max_rel_err"] < TOL, f"rel_err: {result['rel_err']}"

    def test_conservation_and_budget(self, result):
        assert result["conservation"]["mass_rel"] < 1.0e-13
        assert result["conservation"]["energy_rel"] < 0.005
        assert result["momentum_budget"]["closure_rel_err"] < 0.02

    def test_timestep_log_present(self, result):
        # P1-FR-07: kisit yuzdesi logu uretiliyor
        ts = result["timestep_summary"]
        assert ts["n_steps"] > 0
        total = ts["binding_cfl_viscous_pct"] + ts["binding_acceleration_pct"]
        assert total == pytest.approx(100.0)

    @pytest.mark.gpu
    def test_gpu_matches_cpu_metrics(self):
        from dartrift.particles import warp_devices

        if not any(d.startswith("cuda") for d in warp_devices()):
            pytest.skip("CUDA yok")
        gpu = run_sod_warp(resolution=128, device="cuda:0")
        cpu = run_sod_cpu(resolution=128)
        # ayni fizik, ayni IC: plato metrikleri cok yakin olmali
        for key in ("rho_post", "p_post", "v_post"):
            assert gpu["measured"][key] == pytest.approx(
                cpu["measured"][key], rel=1e-6
            )
