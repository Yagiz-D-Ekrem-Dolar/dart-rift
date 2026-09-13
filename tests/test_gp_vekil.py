"""GP vekili ve θ'ya bağlı varyanslı ızgara posterior."""
from __future__ import annotations

import numpy as np
import pytest

from dartrift.inference.design import DART_UZAYI_S3, lhs_design
from dartrift.inference.gp_vekil import _cekirdek, gp_grup_loo, gp_uydur
from dartrift.inference.posterior import grid_posterior_hetero, grid_posterior_kovaryans


def _veri(n=16, tohum=4):
    rng = np.random.default_rng(tohum)
    th = lhs_design(DART_UZAYI_S3, n, root_seed=20260906)
    X = np.vstack([th, th])
    U = DART_UZAYI_S3.to_unit(X)
    y = np.tanh((U[:, 1] - 0.5) / 0.15) + 0.3 * U[:, 0] + rng.normal(0, 0.05, 2 * n)
    grup = np.concatenate([np.arange(n), np.arange(n)])
    return X, y, grup


def test_gp_uydurma_DETERMINISTIK():
    X, y, _ = _veri()
    a = gp_uydur(DART_UZAYI_S3, X, y)
    b = gp_uydur(DART_UZAYI_S3, X, y)
    assert np.array_equal(a.logp, b.logp)


def test_gp_esik_bicimini_ogreniyor_ve_gurultuyu_ayiriyor():
    X, y, _ = _veri(24)
    v = gp_uydur(DART_UZAYI_S3, X, y)
    assert np.sqrt(v.n2) * v.y_olcek == pytest.approx(0.05, rel=0.6)
    # Y0 ekseni (keskin tanh) alpha ekseninden (dogrusal, zayif) KISA olcekli
    assert v.ell[1] < v.ell[0]


def test_gp_grup_loo_ayni_hiperparametrelerle_ELLE_yeniden_uydurmaya_esit():
    X, y, grup = _veri()
    v = gp_uydur(DART_UZAYI_S3, X, y)
    e, s2 = gp_grup_loo(v, y, grup)
    ys = (y - v.y_ort) / v.y_olcek
    for g in (0, 11):
        k, t = grup != g, grup == g
        K = _cekirdek(v.U[k], v.U[k], v.s2, v.ell) + (v.n2 + 1e-10) * np.eye(k.sum())
        Ks = _cekirdek(v.U[t], v.U[k], v.s2, v.ell)
        mu = Ks @ np.linalg.solve(K, ys[k])
        cov = (_cekirdek(v.U[t], v.U[t], v.s2, v.ell) + (v.n2 + 1e-10) * np.eye(t.sum())
               - Ks @ np.linalg.solve(K, Ks.T))
        assert np.allclose(e[t], v.y_olcek * (ys[t] - mu), rtol=1e-6, atol=1e-8)
        assert np.allclose(s2[t], v.y_olcek ** 2 * np.diag(cov), rtol=1e-6)


def test_hetero_SABIT_varyansta_kovaryansli_posteriora_esit():
    n = 12
    rng = np.random.default_rng(1)
    mu = rng.normal(size=(n ** 3, 2))
    D = np.array([0.3, 0.7])
    R = np.array([[1.0, 0.4], [0.4, 1.0]])
    S = np.sqrt(D)[:, None] * R * np.sqrt(D)[None, :]
    a = grid_posterior_hetero(DART_UZAYI_S3, mu, np.tile(D, (n ** 3, 1)), [0.1, -0.2], R, n)
    b = grid_posterior_kovaryans(DART_UZAYI_S3, mu, [0.1, -0.2], S, n)
    assert np.allclose(a.p, b.p, atol=1e-12)


def test_hetero_LOG_DET_terimi_belirsiz_bolgeyi_odullendirmiyor():
    """Ortalama her yerde veriye eşit; varyans `u₁ ≥ 0,5`'te 100×. Log-det
    olmadan posterior düz olurdu; doğrusu düşük varyanslı yarıyı yeğlemek."""
    n = 20
    e = np.linspace(0, 1, n)
    izg = np.meshgrid(e, e, e, indexing="ij")
    var = np.where(izg[1].ravel() < 0.5, 1.0, 100.0)[:, None]
    p = grid_posterior_hetero(DART_UZAYI_S3, np.zeros((n ** 3, 1)), var, [0.0], [[1.0]], n)
    m = p.marginal(1)
    assert m[e < 0.5].sum() > 0.85


def test_hetero_sifir_varyans_ADIYLA_duser():
    with pytest.raises(ValueError, match="varyans pozitif"):
        grid_posterior_hetero(DART_UZAYI_S3, np.zeros((8 ** 3, 1)),
                              np.zeros((8 ** 3, 1)), [0.0], [[1.0]], 8)
