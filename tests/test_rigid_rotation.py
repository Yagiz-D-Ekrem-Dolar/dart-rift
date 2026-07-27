"""P2-VR-01: rijit donme yapay gerilme uretmez; S es-doner (objektiflik)."""

import pytest

from dartrift.validation.solids import run_rigid_rotation


class TestRigidRotation:
    @pytest.fixture(scope="class")
    def with_jaumann(self):
        return run_rigid_rotation(jaumann=True)

    def test_stress_co_rotates(self, with_jaumann):
        # 90 derece donmede S ~= R S0 R^T (ic bolge medyani)
        assert with_jaumann["rel_err_vs_rotated"] < 0.03, with_jaumann

    def test_von_mises_invariant_preserved(self, with_jaumann):
        # rijit donme plastik akis uretmez: vm sabit kalmali (yapay gerilme ~0)
        assert with_jaumann["vm_drift_rel"] < 0.02, with_jaumann

    def test_without_jaumann_fails_badly(self):
        # ablasyon kaniti: donme terimleri kapatilinca hata O(1) olmali.
        # (90 derecede R S0 R^T = -S0 -> beklenen goreli hata ~2)
        r = run_rigid_rotation(jaumann=False)
        assert r["rel_err_vs_rotated"] > 0.5, r
