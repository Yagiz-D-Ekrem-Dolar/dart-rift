"""P2-VR-03: elastik dalga hizi sqrt((K + 4G/3)/rho)'ya yakin."""

import pytest

from dartrift.validation.solids import run_elastic_wave


class TestElasticWave:
    @pytest.fixture(scope="class")
    def result(self):
        return run_elastic_wave(resolution=400)

    def test_speed_matches_longitudinal(self, result):
        assert result["rel_err"] < 0.03, result

    def test_speed_is_longitudinal_not_bulk(self, result):
        # dalga hizi c0=sqrt(K/rho)'dan AYIRT edilebilir olmali (G katkisi gercek)
        assert result["distinguishes_bulk"], result
