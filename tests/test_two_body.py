"""P2-VR-05: iki-cisim yorungesi — enerji/yaricap drifti sinirli."""

import pytest

from dartrift.validation.gravity import run_two_body


class TestTwoBody:
    @pytest.fixture(scope="class")
    def long(self):
        return run_two_body(n_orbits=20.0)

    def test_energy_bounded(self, long):
        # leapfrog: enerji salinimi O(dt^2), sekuler buyume yok
        assert long["energy_max_rel_err"] < 5.0e-4, long

    def test_radius_drift_bounded(self, long):
        assert long["radius_drift_rel"] < 1.0e-3, long

    def test_no_secular_energy_growth(self):
        # 20 yorungedeki maksimum hata ~2 yorungedekiyle ayni mertebede olmali
        short = run_two_body(n_orbits=2.0)
        long = run_two_body(n_orbits=20.0)
        assert long["energy_max_rel_err"] < 3.0 * short["energy_max_rel_err"], (short, long)
