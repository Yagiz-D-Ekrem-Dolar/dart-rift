"""P2 §6: soguk collapse — enerji muhasebesi (KE+IE+PE) kapaniyor."""

import pytest

from dartrift.validation.gravity import run_cold_collapse


class TestColdCollapse:
    @pytest.fixture(scope="class")
    def result(self):
        return run_cold_collapse(n=500)

    def test_collapse_actually_happens(self, result):
        assert result["collapse_happened"], result

    def test_energy_ledger_closes(self, result):
        # P2-VR-06: yercekimi dahil enerji <%1 (potansiyel olcegine gore)
        assert result["energy_rel_err_vs_pot"] < 0.01, result

    def test_momentum_conserved(self, result):
        assert result["momentum_rel"] < 1.0e-6, result
