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


class TestGradientCorrectionIsActuallyApplied:
    """ADR-0009 duzeltmesi GERCEKTEN devrede mi? (ADR-0019)

    `state.grad_correction_used` uzun sure kaydedilip HICBIR YERDE
    denetlenmiyordu. Denetlenmeyince de sessizce devre disi kalabildi: B
    matrisi 3B'ye gomuldugu icin dim<3 senaryolarinda y/z satirlari ozdes
    sifirdi, det(B) her zaman 0 cikiyordu ve duzeltme 1B'de HIC
    uygulanmiyordu (olculdu: 3B kurede %100, 1B cubukta %0).

    Bu testler o bosluğu kapatir: bir modulun ADI, calistigi anlamina gelmez.
    """

    @staticmethod
    def _uygulama_orani(state, mat, num):
        from dartrift.cpu_reference.solid_ref import evaluate_solid

        evaluate_solid(state, mat, num)
        return float(state.grad_correction_used.mean())

    @staticmethod
    def _mat_num():
        from dartrift.cpu_reference.materials import (
            GravityParams,
            MaterialParams,
            PorosityParams,
            StrengthParams,
        )
        from dartrift.cpu_reference.sph_ref import RefParams

        return (
            MaterialParams(
                eos="linear", c0=3000.0, rho0_linear=2700.0,
                strength=StrengthParams(enabled=True, Y0=1e12, mu_f=0.0,
                                        YM=1e13, shear_G=2.27e10),
                porosity=PorosityParams(enabled=False),
                gravity=GravityParams(enabled=False),
            ),
            RefParams(alpha_av=0.0, beta_av=0.0),
        )

    def test_applied_everywhere_in_3d(self):
        import numpy as np

        from dartrift.cpu_reference.solid_ref import SolidState
        from dartrift.validation.solids import H_OVER_DX_3D, _ball_lattice

        x = _ball_lattice(10)
        n, dxl = x.shape[0], 0.1
        st = SolidState(x=x, v=np.zeros_like(x), m=np.full(n, 2700.0 * dxl**3),
                        u=np.zeros(n), h=H_OVER_DX_3D * dxl,
                        active=np.ones(n, bool))
        assert self._uygulama_orani(st, *self._mat_num()) == 1.0

    def test_applied_everywhere_in_1d(self):
        """Regresyon: bu oran eskiden 0.0 idi (bkz. ADR-0019)."""
        import numpy as np

        from dartrift.cpu_reference.solid_ref import SolidState

        dx1 = 1.0 / 120
        x = np.arange(-0.1 + 0.5 * dx1, 1.0 + 0.1, dx1)[:, None]
        n = x.shape[0]
        st = SolidState(x=x, v=np.zeros((n, 1)), m=np.full(n, 2700.0 * dx1),
                        u=np.zeros(n), h=2.0 * dx1, active=np.ones(n, bool))
        assert self._uygulama_orani(st, *self._mat_num()) == 1.0
