"""P1-VR-05: Sedov patlamasi — sok yaricapi benzerlik cozumune ~%5 (GPU)."""

import numpy as np
import pytest

from dartrift.particles import warp_available, warp_devices
from dartrift.validation.sedov import (
    build_sedov_ic,
    measure_shock_radius,
    shock_radius_exact,
)

needs_warp = pytest.mark.skipif(not warp_available(), reason="warp yok")


class TestSedovSetup:
    def test_energy_injection_totals_E(self):
        ic = build_sedov_ic(24)
        from dartrift.validation.sedov import E_INJECT, U_BACKGROUND

        e_tot = float(np.sum(ic["m"] * ic["u"]))
        e_bg = float(np.sum(ic["m"] * U_BACKGROUND))
        assert e_tot - e_bg == pytest.approx(E_INJECT, rel=1e-12)

    def test_similarity_solution_scaling(self):
        # r ~ t^(2/5)
        assert shock_radius_exact(0.08) / shock_radius_exact(0.02) == pytest.approx(
            4.0**0.4, rel=1e-12
        )

    def test_radius_measurement_on_synthetic_profile(self):
        # olcum yontemi: bilinen tepe konumunu geri bulmali
        rng = np.random.default_rng(5)
        x = rng.uniform(-0.5, 0.5, (40000, 3))
        r = np.sqrt(np.sum(x * x, axis=1))
        r0 = 0.31
        rho = 1.0 + 3.0 * np.exp(-((r - r0) / 0.03) ** 2)
        assert measure_shock_radius(x, rho) == pytest.approx(r0, abs=0.01)


@needs_warp
@pytest.mark.gpu
class TestSedovGpu:
    @pytest.fixture(scope="class")
    def result(self):
        if not any(d.startswith("cuda") for d in warp_devices()):
            pytest.skip("CUDA yok")
        from dartrift.validation.sedov import run_sedov_warp

        return run_sedov_warp(n_side=48, device="cuda:0")

    def test_shock_radius_within_5pct(self, result):
        assert result["shock_radius_rel_err"] < 0.05, (
            f"r_olculen={result['shock_radius_measured']:.4f} "
            f"r_analitik={result['shock_radius_exact']:.4f}"
        )

    def test_conservation(self, result):
        c = result["conservation"]
        assert c["mass_rel"] < 1.0e-13
        assert c["momentum_rel"] < 1.0e-6
        assert c["energy_rel"] < 0.005

    def test_timestep_log(self, result):
        ts = result["timestep_summary"]
        assert ts["n_steps"] > 50
        assert 0.0 <= ts["binding_cfl_viscous_pct"] <= 100.0
