"""P1-VR-01..03: izole korunum + kesme/Balsara (P1-FR-05)."""

import pytest

from dartrift.particles import warp_available
from dartrift.validation.conservation import (
    run_conservation_cpu,
    run_conservation_warp,
    shear_av_suppression,
)

needs_warp = pytest.mark.skipif(not warp_available(), reason="warp yok")


class TestIsolatedConservation:
    @pytest.fixture(scope="class")
    def result(self):
        return run_conservation_cpu(n=300, t_end=0.3)

    def test_mass(self, result):
        assert result["mass_rel"] < 1.0e-13

    def test_momentum(self, result):
        assert result["momentum_rel"] < 1.0e-6

    def test_energy(self, result):
        assert result["energy_rel"] < 0.005


@needs_warp
class TestIsolatedConservationWarp:
    @pytest.fixture(scope="class")
    def result(self):
        return run_conservation_warp(n=300, device="cpu", t_end=0.3)

    def test_all_thresholds(self, result):
        assert result["mass_rel"] < 1.0e-13
        assert result["momentum_rel"] < 1.0e-6
        assert result["energy_rel"] < 0.005

    def test_continuity_tracks(self, result):
        assert result["continuity_max_rel_dev"] < 0.10


class TestShearBalsara:
    def test_balsara_suppresses_av_in_pure_shear(self):
        # P1-FR-05: kesme akisinda asiri sonum yok
        m = shear_av_suppression()
        assert m["heating_balsara_off"] > 0.0
        assert m["suppression_ratio"] < 0.05, (
            f"Balsara bastirma orani {m['suppression_ratio']:.3f} (>= 0.05: asiri sonum)"
        )
