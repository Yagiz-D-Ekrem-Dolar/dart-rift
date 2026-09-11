"""A77 — ilk `dt` temas öncesi alanlarla seçiliyordu.

Ölçüldü (kaba DART sahnesi, `cfl = 0,25`): ilk `dt = 1,82e-5 s`,
ikincisi `9,96e-6 s`; toplam enerjinin `%0,94`'ü o TEK adımda
kayboluyor. `t = 1 ms`'de sapma `−%2,19` (düzeltmeyle `−%1,73`),
`cfl = 0,125`'te `−%0,95`: kalan kayıp `Δt` ile yaklaşık doğrusal.

`WarpSolid3D.hazirla()` ilk değerlendirmeyi `compute_dt()`'den ÖNCE
yapar. Kilitlenen: aynı `dt` ile sonucu bit bit DEĞİŞTİRMİYOR, yalnız
`dt` seçimini etkiliyor.
"""
from __future__ import annotations

import numpy as np
import pytest

from dartrift.cpu_reference import sph_ref as R
from dartrift.cpu_reference.materials import (
    GravityParams,
    MaterialParams,
    PorosityParams,
    StrengthParams,
)
from dartrift.particles import warp_available

pytestmark = pytest.mark.skipif(not warp_available(), reason="warp yok")


def _iki_blok():
    """Hedef kafesi + ona 1 km/s ile yaklaşan küçük blok (destekler örtüşük)."""
    g = np.arange(-2, 3) * 0.5
    X = np.stack(np.meshgrid(g, g, g, indexing="ij"), -1).reshape(-1, 3)
    mermi = np.stack(np.meshgrid(g[1:4], g[1:4], g[1:4], indexing="ij"),
                     -1).reshape(-1, 3) + np.array([0.0, 0.0, 1.6])
    x = np.vstack([X, mermi])
    v = np.zeros_like(x)
    v[len(X):, 2] = -1000.0
    n = len(x)
    m = np.full(n, 2700.0 * 0.125 / 1.3)
    mat = MaterialParams(
        eos="tillotson", density_method="continuity",
        strength=StrengthParams(enabled=True, Y0=1e5, mu_f=0.6, YM=1.5e9,
                                shear_G=2.27e10),
        porosity=PorosityParams(enabled=True, alpha0=1.3, Pe=1e6, Ps=1e8,
                                n_exp=2.0),
        gravity=GravityParams(enabled=False))
    return x, v, m, mat


def _sol(**kw):
    from dartrift.warp_core.solver_solid import WarpSolid3D

    x, v, m, mat = _iki_blok()
    return WarpSolid3D(x, v, m, np.zeros(len(m)), 0.65, mat,
                       R.RefParams(cfl=0.25), alpha0=np.full(len(m), 1.3),
                       device="cpu", **kw)


def test_hazirla_ilk_dt_yi_KUCULTUYOR():
    a = _sol()
    dt_bayat = a.compute_dt()
    b = _sol()
    b.hazirla()
    dt_taze = b.compute_dt()
    assert dt_taze < dt_bayat, (dt_taze, dt_bayat)


def test_hazirla_ayni_dt_ile_sonucu_BIT_BIT_degistirmiyor():
    a = _sol()
    b = _sol()
    b.hazirla()
    for _ in range(3):
        a.step(1.0e-6)
        b.step(1.0e-6)
    sa, sb = a.state_numpy(), b.state_numpy()
    for k in ("x", "v", "u", "rho", "S", "P"):
        assert np.array_equal(sa[k], sb[k]), k


def test_hazirla_IDEMPOTENT():
    s = _sol()
    s.hazirla()
    a1 = s.a.numpy().copy()
    s.hazirla()
    assert np.array_equal(s.a.numpy(), a1)


def test_ileri_model_varsayilani_KAPALI_ve_ozet_ayri():
    import inspect

    from dartrift.inference.forward import _fizik_ozeti, ileri_kosu_merdiven

    p = inspect.signature(ileri_kosu_merdiven).parameters
    assert p["ilk_degerlendirme"].default is False
    t = {"radius": 82.0}
    assert (_fizik_ozeti(t, "m", ("48:5.6",), 7.0, 0.024)
            == _fizik_ozeti(t, "m", ("48:5.6",), 7.0, 0.024,
                            ilk_degerlendirme=False))
    assert (_fizik_ozeti(t, "m", ("48:5.6",), 7.0, 0.024)
            != _fizik_ozeti(t, "m", ("48:5.6",), 7.0, 0.024,
                            ilk_degerlendirme=True))
