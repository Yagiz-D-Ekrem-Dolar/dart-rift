"""P1-FR-04: Wendland C2 cekirdegi — normalizasyon, tutarlilik, simetri."""

import numpy as np
import pytest

from dartrift.cpu_reference.sph_ref import kernel_dwdq, kernel_w
from dartrift.particles import warp_available

needs_warp = pytest.mark.skipif(not warp_available(), reason="warp yok")

# np.trapezoid NumPy 2.0'da geldi; TRUBA'daki yorumlayici daha eski ve orada
# yalnizca np.trapz var. Yerelde gecip kumede kalan bir test, kapinin
# guvenilirligini bozar (G1 1426017: C1 ve C6 bu yuzden KALDI).
_trapz = getattr(np, "trapezoid", None) or np.trapz


class TestNormalization:
    def test_3d_integral_is_one(self):
        # integral W dV = 1 (kuresel kabuk integrali, yuksek cozunurluk)
        h = 0.7
        r = np.linspace(0.0, 2.0 * h, 200_001)
        w = kernel_w(r / h, h, 3)
        integral = _trapz(4.0 * np.pi * r * r * w, r)
        assert integral == pytest.approx(1.0, rel=1.0e-8)

    def test_1d_integral_is_one(self):
        h = 0.3
        r = np.linspace(-2.0 * h, 2.0 * h, 400_001)
        w = kernel_w(np.abs(r) / h, h, 1)
        assert _trapz(w, r) == pytest.approx(1.0, rel=1.0e-8)

    def test_compact_support(self):
        assert kernel_w(np.array([2.0, 2.5, 10.0]), 1.0, 3).tolist() == [0.0, 0.0, 0.0]
        assert kernel_dwdq(np.array([2.0, 3.0]), 1.0, 1).tolist() == [0.0, 0.0]

    def test_positive_inside_support(self):
        q = np.linspace(0.0, 1.999, 100)
        assert np.all(kernel_w(q, 1.0, 3) > 0.0)
        assert np.all(kernel_w(q, 1.0, 1) > 0.0)

    def test_unknown_dim_raises(self):
        with pytest.raises(ValueError, match="boyut"):
            kernel_w(np.array([1.0]), 1.0, 2)


class TestDerivative:
    @pytest.mark.parametrize("dim", [1, 3])
    def test_dwdq_matches_numerical_derivative(self, dim):
        h = 0.5
        q = np.linspace(0.01, 1.95, 300)
        eps = 1.0e-7
        num = (kernel_w(q + eps, h, dim) - kernel_w(q - eps, h, dim)) / (2.0 * eps)
        ana = kernel_dwdq(q, h, dim)
        assert np.allclose(ana, num, rtol=1.0e-6, atol=1.0e-6)

    @pytest.mark.parametrize("dim", [1, 3])
    def test_dwdq_zero_at_center(self, dim):
        # merkezde duz tepe: dW/dq(0) = 0 (cekirdek C2 duzgunlugu)
        assert kernel_dwdq(np.array([0.0]), 1.0, dim)[0] == 0.0


class TestPartitionOfUnity:
    def test_constant_field_reproduced_interior(self):
        # duzgun kafeste ic bolgede sum (m/rho) W ~= 1 (<%1) — P1 §6.1
        n_side, dx = 12, 1.0 / 12
        ax = (np.arange(n_side) + 0.5) * dx
        xx, yy, zz = np.meshgrid(ax, ax, ax, indexing="ij")
        x = np.column_stack([xx.ravel(), yy.ravel(), zz.ravel()])
        h = 1.3 * dx
        m = np.full(x.shape[0], dx**3)
        d = x[:, None, :] - x[None, :, :]
        q = np.sqrt(np.sum(d * d, axis=2)) / h
        w = kernel_w(q, h, 3)
        rho = w @ m
        # partition of unity: sum_j (m_j/rho_j) W_ij
        pou = w @ (m / rho)
        interior = np.all((x > 2 * h) & (x < 1.0 - 2 * h), axis=1)
        assert np.max(np.abs(pou[interior] - 1.0)) < 0.01

    def test_gradient_antisymmetry_bitwise(self):
        # gradW_ij = -gradW_ji bit-yakin (P1 §6.1); FP'de tam esitlik saglanir
        rng = np.random.default_rng(3)
        xi = rng.uniform(-1, 1, (200, 3))
        xj = rng.uniform(-1, 1, (200, 3))
        h = 0.8

        def grad(a, b):
            d = a - b
            r = np.sqrt(np.sum(d * d, axis=1))
            q = r / h
            return (kernel_dwdq(q, h, 3) / (h * r))[:, None] * d

        gij = grad(xi, xj)
        gji = grad(xj, xi)
        assert np.array_equal(gij, -gji)


@needs_warp
class TestWarpDeviceParity:
    """Device fonksiyonlari NumPy referansiyla birebir ayni matematik olmali."""

    @pytest.mark.parametrize("dim", [1, 3])
    def test_w_and_dwdq_match_cpu(self, dim):
        from dartrift.warp_core.kernel_fn import eval_kernel_on_device

        h = 0.37
        q = np.linspace(0.0, 2.5, 501)
        w_gpu, d_gpu = eval_kernel_on_device(q, h, dim, device="cpu")
        assert np.allclose(w_gpu, kernel_w(q, h, dim), rtol=1e-14, atol=1e-300)
        assert np.allclose(d_gpu, kernel_dwdq(q, h, dim), rtol=1e-14, atol=1e-300)
