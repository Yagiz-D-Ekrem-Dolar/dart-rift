"""CPU vektor matematigi referans katmani + deterministik indirgemeler."""

import math

import numpy as np
import pytest

from dartrift.cpu_math import cross3, dot3, fixed_order_sum, kahan_sum, norm3, normalize3


def _triplet(rng, n=64):
    return rng.uniform(-5, 5, n), rng.uniform(-5, 5, n), rng.uniform(-5, 5, n)


class TestVector:
    def test_dot_matches_numpy(self):
        rng = np.random.default_rng(7)
        a, b = _triplet(rng), _triplet(rng)
        expected = np.einsum("ij,ij->i", np.stack(a, 1), np.stack(b, 1))
        assert np.allclose(dot3(a, b), expected, rtol=1e-15)

    def test_dot_known_value(self):
        a = (np.array([1.0]), np.array([2.0]), np.array([3.0]))
        b = (np.array([4.0]), np.array([5.0]), np.array([6.0]))
        assert dot3(a, b)[0] == 32.0

    def test_cross_orthogonality(self):
        rng = np.random.default_rng(8)
        a, b = _triplet(rng), _triplet(rng)
        c = cross3(a, b)
        assert np.allclose(dot3(c, a), 0.0, atol=1e-12)
        assert np.allclose(dot3(c, b), 0.0, atol=1e-12)

    def test_cross_known_value(self):
        ex = (np.array([1.0]), np.array([0.0]), np.array([0.0]))
        ey = (np.array([0.0]), np.array([1.0]), np.array([0.0]))
        cz = cross3(ex, ey)
        assert (cz[0][0], cz[1][0], cz[2][0]) == (0.0, 0.0, 1.0)

    def test_norm(self):
        a = (np.array([3.0]), np.array([4.0]), np.array([0.0]))
        assert norm3(a)[0] == 5.0

    def test_normalize_unit_length(self):
        rng = np.random.default_rng(9)
        a = _triplet(rng)
        u = normalize3(a)
        assert np.allclose(norm3(u), 1.0, rtol=1e-14)

    def test_normalize_zero_vector_raises(self):
        a = (np.zeros(2), np.zeros(2), np.zeros(2))
        with pytest.raises(FloatingPointError, match="normu sifira"):
            normalize3(a)

    def test_normalize_eps_guard(self):
        a = (np.array([1e-300]), np.array([0.0]), np.array([0.0]))
        with pytest.raises(FloatingPointError):
            normalize3(a, eps=1e-100)


class TestDeterministicReductions:
    def test_kahan_beats_naive_on_adversarial(self):
        # Klasik Kahan senaryosu: buyuk akumulatore art arda kucuk katkilar.
        # Naif sirali toplam her +1'i kaybeder; Kahan kompanzasyonla kurtarir.
        arr = np.array([1.0e16] + [1.0] * 1000, dtype=np.float64)
        exact = math.fsum(arr)
        naive = 0.0
        for v in arr:
            naive += float(v)
        assert exact == 1.0e16 + 1000.0
        assert naive != exact  # naif sirali toplam hatali
        assert kahan_sum(arr) == exact  # Kahan bit-tam kurtarir

    def test_kahan_reproducible(self):
        a = np.random.default_rng(3).normal(size=10_000)
        assert kahan_sum(a) == kahan_sum(a)  # bit-esit tekrar

    def test_fixed_order_sum_matches_fsum(self):
        a = np.random.default_rng(4).normal(size=10_000) * 1e8
        assert fixed_order_sum(a) == pytest.approx(math.fsum(a), rel=1e-14)

    def test_fixed_order_sum_deterministic_given_block(self):
        a = np.random.default_rng(5).normal(size=9_999)
        assert fixed_order_sum(a, block=1024) == fixed_order_sum(a, block=1024)

    def test_fixed_order_bad_block_raises(self):
        with pytest.raises(ValueError, match="block"):
            fixed_order_sum(np.ones(4), block=0)

    def test_empty_sums(self):
        assert kahan_sum(np.empty(0)) == 0.0
        assert fixed_order_sum(np.empty(0)) == 0.0
