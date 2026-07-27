"""P1-VR-06: >=3 cozunurlukte monotonik/aciklanabilir yakinsama."""

import pytest

from dartrift.validation.sod import run_sod_cpu

RESOLUTIONS = [64, 128, 256]  # DR-RIFT-P1 Ek A


class TestSodConvergence:
    @pytest.fixture(scope="class")
    def ladder(self):
        return {r: run_sod_cpu(resolution=r) for r in RESOLUTIONS}

    def test_l1_error_decreases_monotonically(self, ladder):
        errs = [ladder[r]["l1_rho"] for r in RESOLUTIONS]
        assert errs[0] > errs[1] > errs[2], f"L1(rho) merdiveni monoton degil: {errs}"

    def test_post_shock_error_does_not_grow(self, ladder):
        errs = [ladder[r]["max_rel_err"] for r in RESOLUTIONS]
        assert errs[2] <= errs[0], f"plato hatasi cozunurlukle buyudu: {errs}"

    def test_highest_resolution_within_gate_tolerance(self, ladder):
        assert ladder[256]["max_rel_err"] < 0.05

    def test_all_resolutions_conserve(self, ladder):
        for r in RESOLUTIONS:
            c = ladder[r]["conservation"]
            assert c["mass_rel"] < 1.0e-13, f"res={r}"
            assert c["energy_rel"] < 0.005, f"res={r}"
            assert ladder[r]["momentum_budget"]["closure_rel_err"] < 0.03, f"res={r}"
