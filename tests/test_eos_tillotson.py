"""P2-FR-03: Tillotson EOS birim/limit testleri + dayanim yasasi."""

import numpy as np
import pytest

from dartrift.cpu_reference.materials import (
    StrengthParams,
    TillotsonParams,
    return_mapping,
    tillotson_pressure,
    tillotson_sound_speed,
)

TP = TillotsonParams()


class TestTillotsonLimits:
    def test_reference_state_zero_pressure(self):
        # (rho0, u=0): mu=0, u=0 -> P = 0
        p = tillotson_pressure(np.array([TP.rho0]), np.array([0.0]), TP)
        assert p[0] == 0.0

    def test_bulk_modulus_at_reference(self):
        # K0 = rho dP/drho |_(rho0,0) = A
        d = 1.0e-4 * TP.rho0
        p1 = tillotson_pressure(np.array([TP.rho0 + d]), np.array([0.0]), TP)
        p0 = tillotson_pressure(np.array([TP.rho0 - d]), np.array([0.0]), TP)
        K0 = TP.rho0 * (p1[0] - p0[0]) / (2 * d)
        assert K0 == pytest.approx(TP.A, rel=1e-3)

    def test_compression_positive_tension_negative(self):
        p_c = tillotson_pressure(np.array([1.2 * TP.rho0]), np.array([0.0]), TP)
        p_t = tillotson_pressure(np.array([0.95 * TP.rho0]), np.array([0.0]), TP)
        assert p_c[0] > 0.0 and p_t[0] < 0.0

    def test_branch_continuity_at_u_iv_and_u_cv(self):
        # ara enterpolasyon kollari u_iv ve u_cv'de surekli birlesmeli
        rho = np.array([0.8 * TP.rho0])
        for u_edge in (TP.u_iv, TP.u_cv):
            lo = tillotson_pressure(rho, np.array([u_edge * (1 - 1e-9)]), TP)
            hi = tillotson_pressure(rho, np.array([u_edge * (1 + 1e-9)]), TP)
            assert lo[0] == pytest.approx(hi[0], rel=1e-6)

    def test_hot_expanded_branch_positive(self):
        # genlesmis + cok sicak: buhar basinci pozitif olmali
        p = tillotson_pressure(np.array([0.5 * TP.rho0]), np.array([10 * TP.u_cv]), TP)
        assert p[0] > 0.0

    def test_reference_sound_speed(self):
        cs = tillotson_sound_speed(np.array([TP.rho0]), np.array([0.0]), TP)
        assert cs[0] == pytest.approx(np.sqrt(TP.A / TP.rho0), rel=0.02)

    def test_cs_floor_prevents_collapse(self):
        # patolojik durumda bile cs >= taban (dt cokmesine karsi, P2 §2.3)
        rho = np.array([0.3 * TP.rho0])
        u = np.array([0.5 * TP.u_iv])
        cs = tillotson_sound_speed(rho, u, TP)
        assert cs[0] >= TP.cs_floor_frac * TP.cs_ref
        assert np.isfinite(cs[0])

    def test_negative_u_clamped(self):
        p = tillotson_pressure(np.array([TP.rho0]), np.array([-1.0]), TP)
        assert np.isfinite(p[0])


class TestStrengthLaw:
    SP = StrengthParams()

    def test_yield_at_zero_pressure_is_cohesion(self):
        assert self.SP.yield_stress(np.array([0.0]))[0] == self.SP.Y0

    def test_yield_monotone_in_pressure(self):
        P = np.linspace(0.0, 5e9, 100)
        Y = self.SP.yield_stress(P)
        assert np.all(np.diff(Y) > 0)

    def test_yield_saturates_at_YM(self):
        Y = self.SP.yield_stress(np.array([1e14]))
        assert Y[0] < self.SP.YM
        assert Y[0] == pytest.approx(self.SP.YM, rel=0.01)

    def test_tension_clamped_to_cohesion(self):
        assert self.SP.yield_stress(np.array([-1e9]))[0] == self.SP.Y0


class TestReturnMapping:
    SP = StrengthParams(Y0=1e6, mu_f=0.0, YM=1e12, shear_G=2e10)  # von Mises

    def test_below_yield_untouched(self):
        S = np.zeros((1, 3, 3))
        S[0, 0, 0], S[0, 1, 1] = 1e5, -1e5  # vm = sqrt(3*J2) ~ 1.7e5 < Y0
        S_new, du = return_mapping(S, np.array([0.0]), np.array([2700.0]), self.SP)
        assert np.array_equal(S_new, S)
        assert du[0] == 0.0

    def test_above_yield_projected_onto_surface(self):
        S = np.zeros((1, 3, 3))
        S[0, 0, 0], S[0, 1, 1] = 2e6, -2e6
        S_new, du = return_mapping(S, np.array([0.0]), np.array([2700.0]), self.SP)
        j2 = 0.5 * np.sum(S_new[0] * S_new[0])
        assert np.sqrt(3 * j2) == pytest.approx(self.SP.Y0, rel=1e-12)

    def test_plastic_work_positive_and_into_u(self):
        S = np.zeros((1, 3, 3))
        S[0, 0, 0], S[0, 1, 1] = 2e6, -2e6
        _, du = return_mapping(S, np.array([0.0]), np.array([2700.0]), self.SP)
        assert du[0] > 0.0  # kirmizi-takim: plastik is POZITIF

    def test_direction_preserved(self):
        # radyal geri cekme: S yonu korunur, buyukluk olceklenir
        S = np.zeros((1, 3, 3))
        S[0, 0, 1] = S[0, 1, 0] = 3e6
        S_new, _ = return_mapping(S, np.array([0.0]), np.array([2700.0]), self.SP)
        ratio = S_new[0, 0, 1] / S[0, 0, 1]
        assert 0 < ratio < 1
        assert S_new[0, 1, 0] == S_new[0, 0, 1]
