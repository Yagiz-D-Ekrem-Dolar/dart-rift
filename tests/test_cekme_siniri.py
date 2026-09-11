"""Granüler matris çekme sınırı `T_m` — `P_eff = max(P, −T_m)` (uzman S1)."""
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

ALFA0 = 1.3


def _gergin(**kw):
    """Durgun kafes, yoğunluğu dinlenme değerinin %1 ALTINDA -> P < 0."""
    from dartrift.warp_core.solver_solid import WarpSolid3D

    g = np.arange(-2, 3) * 0.5
    x = np.stack(np.meshgrid(g, g, g, indexing="ij"), -1).reshape(-1, 3)
    n = len(x)
    rho0 = 2700.0 / ALFA0
    mat = MaterialParams(
        eos="tillotson", density_method="continuity",
        strength=StrengthParams(enabled=True, Y0=1e4, mu_f=0.6, YM=1.5e9,
                                shear_G=2.27e10),
        porosity=PorosityParams(enabled=True, alpha0=ALFA0, Pe=1e6, Ps=1e8,
                                n_exp=2.0),
        gravity=GravityParams(enabled=False))
    maske = np.zeros(n, bool)
    maske[: n // 2] = True
    s = WarpSolid3D(x, np.zeros_like(x), np.full(n, rho0 * 0.125), np.zeros(n),
                    0.65, mat, R.RefParams(), alpha0=np.full(n, ALFA0),
                    rho_durum=np.full(n, 0.99 * rho0), device="cpu",
                    cekme_kirp_maske=maske, **kw)
    s.hazirla()
    return s, maske


def _serbest():
    from dartrift.warp_core.solver_solid import WarpSolid3D

    s, maske = _gergin()
    x = s.x.numpy()
    n = len(x)
    rho0 = 2700.0 / ALFA0
    t = WarpSolid3D(x, np.zeros_like(x), np.full(n, rho0 * 0.125), np.zeros(n),
                    0.65, s.mat, R.RefParams(), alpha0=np.full(n, ALFA0),
                    rho_durum=np.full(n, 0.99 * rho0), device="cpu")
    t.hazirla()
    return t


def test_kurulum_gercekten_CEKMEDE():
    assert np.all(_serbest().P.numpy() < -1e6)


def test_T_m_uygulaniyor_maskesiz_parcacik_DOKUNULMUYOR():
    T = 1.0e6
    s, maske = _gergin(cekme_siniri=T)
    P = s.P.numpy()
    assert np.all(P[maske] >= -T) and np.any(np.isclose(P[maske], -T))
    np.testing.assert_array_equal(P[~maske], _serbest().P.numpy()[~maske])


def test_T_sifir_eski_kirpma_ile_BIT_AYNI():
    a, _ = _gergin()
    b, _ = _gergin(cekme_siniri=0.0)
    assert a.P.numpy().tobytes() == b.P.numpy().tobytes()


def test_parcacik_basina_T_dizisi():
    s0, maske = _gergin()
    n = len(maske)
    T = np.linspace(1e5, 2e6, n)
    s, _ = _gergin(cekme_siniri=T)
    P = s.P.numpy()
    assert np.all(P[maske] >= -T[maske] - 1e-6)


def test_negatif_T_REDDEDILIYOR():
    with pytest.raises(ValueError, match="cekme_siniri"):
        _gergin(cekme_siniri=-1.0)


def test_maskesiz_T_REDDEDILIYOR():
    from dartrift.warp_core.solver_solid import WarpSolid3D

    s = _serbest()
    x = s.x.numpy()
    with pytest.raises(ValueError, match="cekme_kirp_maske"):
        WarpSolid3D(x, np.zeros_like(x), np.ones(len(x)), np.zeros(len(x)),
                    0.65, s.mat, R.RefParams(), device="cpu", cekme_siniri=1e5)


def test_ileri_model_varsayilani_YOK_ve_ozet_ayri():
    import inspect

    from dartrift.inference.forward import _fizik_ozeti, ileri_kosu_merdiven

    assert inspect.signature(ileri_kosu_merdiven).parameters[
        "matris_cekme_siniri"].default is None
    t = {"radius": 82.0}
    a = _fizik_ozeti(t, "m", ("48:5.6",), 7.0, 0.024)
    b = _fizik_ozeti(t, "m", ("48:5.6",), 7.0, 0.024, matris_cekme_siniri=1e3)
    assert a != b
