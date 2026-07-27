"""P2-FR-06: her modul config ile kapatilabilir; etki beklenen yonde."""

import pytest

from dartrift.validation.ablation import run_ablation_matrix


class TestAblationMatrix:
    @pytest.fixture(scope="class")
    def matrix(self):
        return run_ablation_matrix(n=350)

    def test_all_expected_directions(self, matrix):
        assert matrix["all_expected"], matrix["checks"]

    def test_strength_off_means_zero_deviatoric(self, matrix):
        assert matrix["cases"]["base"]["vm_max"] == 0.0

    def test_strength_on_produces_plastic_work(self, matrix):
        assert matrix["cases"]["strength"]["plastic_cum"] > 0.0

    def test_porosity_crushes(self, matrix):
        c = matrix["cases"]["porosity"]
        assert c["alpha_min"] < 1.4 and c["alpha_min"] >= 1.0

    def test_gravity_contributes_potential(self, matrix):
        assert matrix["cases"]["gravity"]["e_pot"] < 0.0
