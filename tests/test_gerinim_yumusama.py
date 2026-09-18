"""Gerinimle kohezyon kaybı (ADR-0050 ek; L1 Raducan & Jutzi 2022).

L1: *"constant cohesion Y₀ with a strain-based weakening model"* — kohezyon
toplam gerinim `≥ 1`'de kaybolur. Biçim (doğrusal/basamak) makalede yazılı
değil; ikisi de seçenek.
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

ALFA0 = 1.3
RHO0 = 2700.0
Y0 = 1.0e4
G = 2.27e10
TAU = 5.0e4                 # kayma gerilmesi: vm = sqrt(3)*TAU > Y0


def _mat(dayanim=True):
    return MaterialParams(
        eos="tillotson", density_method="continuity",
        strength=StrengthParams(enabled=dayanim, Y0=Y0, mu_f=0.6, YM=1.5e9,
                                shear_G=G),
        porosity=PorosityParams(enabled=True, alpha0=ALFA0, Pe=1e6, Ps=1e8,
                                n_exp=2.0),
        gravity=GravityParams(enabled=False))


def _kafes():
    g = np.arange(-2, 3) * 0.5
    return np.stack(np.meshgrid(g, g, g, indexing="ij"), -1).reshape(-1, 3)


def _cozucu(tau=TAU, mat=None, **kw):
    from dartrift.warp_core.solver_solid import WarpSolid3D

    x = _kafes()
    n = len(x)
    S0 = np.zeros((n, 3, 3))
    S0[:, 0, 1] = S0[:, 1, 0] = tau
    s = WarpSolid3D(x, np.zeros_like(x), np.full(n, RHO0 / ALFA0 * 0.125),
                    np.zeros(n), 0.65, mat or _mat(), R.RefParams(), S0=S0,
                    alpha0=np.full(n, ALFA0), rho_durum=np.full(n, RHO0 / ALFA0),
                    device="cpu", **kw)
    s.hazirla()
    return s


def _deps_bekle(tau=TAU):
    vm = np.sqrt(3.0) * tau
    return (vm - Y0) / (3.0 * G)


def test_VARSAYILAN_kapali_dizi_yok():
    s = _cozucu()
    assert s._gy is None and not hasattr(s, "eps_p")
    assert s.gerinim_tanisi() == {}


def test_AKMA_ALTINDA_gerinim_birikmiyor_Y0_degismiyor():
    s = _cozucu(tau=1.0e3, gerinim_yumusama={"eps_c": 1e-6})
    for _ in range(3):
        s.step(1e-7)
    assert float(s.eps_p.numpy().max()) == 0.0
    np.testing.assert_array_equal(s.Y0.numpy(), Y0)


def test_ESDEGER_PLASTIK_GERINIM_radyal_donus_formulu():
    s = _cozucu(gerinim_yumusama={"eps_c": 1.0})
    s.step(1e-9)
    e = s.eps_p.numpy()
    # ic parcaciklar: S sabit (hiz sifir), P ~ 0 -> Y = Y0
    assert float(np.median(e)) == pytest.approx(_deps_bekle(), rel=1e-3)


def test_DOGRUSAL_kohezyon_kaybi():
    eps_c = 10.0 * _deps_bekle()
    s = _cozucu(gerinim_yumusama={"eps_c": eps_c, "bicim": "dogrusal"})
    s.step(1e-9)
    y = float(np.median(s.Y0.numpy()))
    assert y == pytest.approx(Y0 * (1.0 - 0.1), rel=2e-3)


def test_DOGRUSAL_esikte_kohezyon_SIFIR():
    s = _cozucu(gerinim_yumusama={"eps_c": 0.5 * _deps_bekle()})
    s.step(1e-9)
    assert float(np.median(s.Y0.numpy())) == 0.0
    t = s.gerinim_tanisi()
    assert t["kohezyonsuz_kutle_kesri"] > 0.5


def test_BASAMAK_bicimi():
    alt = _cozucu(gerinim_yumusama={"eps_c": 2.0 * _deps_bekle(),
                                    "bicim": "basamak"})
    alt.step(1e-9)
    assert float(np.median(alt.Y0.numpy())) == Y0          # esik asilmadi
    ust = _cozucu(gerinim_yumusama={"eps_c": 0.5 * _deps_bekle(),
                                    "bicim": "basamak"})
    ust.step(1e-9)
    assert float(np.median(ust.Y0.numpy())) == 0.0


def test_MASKE_disindaki_parcacik_yumusamiyor():
    n = len(_kafes())
    mk = np.zeros(n, bool)
    mk[: n // 2] = True
    s = _cozucu(gerinim_yumusama={"eps_c": 0.5 * _deps_bekle(), "maske": mk})
    s.step(1e-9)
    y = s.Y0.numpy()
    assert np.all(y[~mk] == Y0)
    assert float(np.median(y[mk])) == 0.0


def test_KOHEZYON_GERI_GELMIYOR():
    s = _cozucu(gerinim_yumusama={"eps_c": 5.0 * _deps_bekle()})
    onceki = s.Y0.numpy().copy()
    for _ in range(4):
        s.step(1e-9)
        simdiki = s.Y0.numpy().copy()
        assert np.all(simdiki <= onceki + 1e-12)
        onceki = simdiki


def test_ARA_KIPINDE_de_birikiyor_cift_sayim_yok():
    """"ara" kipinde projeksiyon değerlendirmede de yapılır; ikinci
    değerlendirme idempotent olduğundan tek adımda birikim `son` kipiyle
    aynı mertebede olmalı (iki katı değil)."""
    son = _cozucu(gerinim_yumusama={"eps_c": 1.0})
    son.step(1e-9)
    x = _kafes()
    n = len(x)
    S0 = np.zeros((n, 3, 3))
    S0[:, 0, 1] = S0[:, 1, 0] = TAU
    from dartrift.warp_core.solver_solid import WarpSolid3D as W

    ara = W(x, np.zeros_like(x), np.full(n, RHO0 / ALFA0 * 0.125), np.zeros(n),
            0.65, _mat(), R.RefParams(akma_kipi="ara"), S0=S0,
            alpha0=np.full(n, ALFA0), rho_durum=np.full(n, RHO0 / ALFA0),
            device="cpu", gerinim_yumusama={"eps_c": 1.0})
    ara.hazirla()
    ara.step(1e-9)
    e_son = float(np.median(son.eps_p.numpy()))
    e_ara = float(np.median(ara.eps_p.numpy()))
    assert e_ara == pytest.approx(e_son, rel=1e-3)


@pytest.mark.parametrize("gy,mesaj", [
    ({"eps_c": 0.0}, "eps_c"),
    ({"eps_c": -1.0}, "eps_c"),
    ({"bicim": "ustel"}, "bicim"),
    ({"maske": np.ones(3, bool)}, "maske"),
])
def test_GECERSIZ_ayar_REDDEDILIYOR(gy, mesaj):
    with pytest.raises(ValueError, match=mesaj):
        _cozucu(gerinim_yumusama=gy)


def test_DAYANIMSIZ_malzemede_REDDEDILIYOR():
    with pytest.raises(ValueError, match="dayanim"):
        _cozucu(mat=_mat(dayanim=False), gerinim_yumusama={"eps_c": 1.0})
