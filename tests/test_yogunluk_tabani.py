"""A83 — süreklilik yoğunluğu tabanı."""
from __future__ import annotations

import inspect
from pathlib import Path

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

ALFA0 = 2.2
RHO0 = 2700.0


def _cozucu(rho, **kw):
    from dartrift.warp_core.solver_solid import WarpSolid3D

    g = np.arange(-2, 3) * 0.5
    x = np.stack(np.meshgrid(g, g, g, indexing="ij"), -1).reshape(-1, 3)
    n = len(x)
    mat = MaterialParams(
        eos="tillotson", density_method="continuity",
        strength=StrengthParams(enabled=True, Y0=1e4, mu_f=0.6, YM=1.5e9, shear_G=2.27e10),
        porosity=PorosityParams(enabled=True, alpha0=ALFA0, Pe=1e6, Ps=1e8, n_exp=2.0),
        gravity=GravityParams(enabled=False))
    v = np.zeros_like(x)
    v[12] = (230.0, 0.0, 0.0)                                  # A83'teki ayrilan parcacik
    s = WarpSolid3D(x, v, np.full(n, RHO0 / ALFA0 * 0.125), np.zeros(n), 0.65, mat,
                    R.RefParams(akma_kipi="ara"), alpha0=np.full(n, ALFA0), rho_durum=rho,
                    device="cpu", cekme_kirp_maske=np.ones(n, bool),
                    dayanim_kesme={"eta_kes": 0.5}, **kw)
    s.hazirla()
    return s


def _rho(n=125, kucuk=1e-9):
    r = np.full(n, RHO0 / ALFA0)
    r[12] = kucuk
    return r


def test_varsayilan_None_BIT_AYNI():
    a, b = _cozucu(_rho(kucuk=5.0)), _cozucu(_rho(kucuk=5.0), yogunluk_tabani=None)
    for _ in range(2):
        a.step(a.compute_dt())
        b.step(b.compute_dt())
    assert a.rho.numpy().tobytes() == b.rho.numpy().tobytes()
    assert a.taban_tanisi() == {}


def test_taban_bir_adimda_uygulaniyor_ve_sayiliyor():
    s = _cozucu(_rho(), yogunluk_tabani=0.01)
    s.step(1e-7)
    alt = 0.01 * RHO0 / s.alpha.numpy()[12]
    assert s.rho.numpy()[12] >= alt * (1 - 1e-12)
    t = s.taban_tanisi()
    assert t["n_tabanda"] >= 1 and 0 < t["tabanda_kutle_kesri"] < 0.02
    diger = np.arange(125) != 12
    assert np.all(s.rho.numpy()[diger] > 100.0)


def test_sifira_inen_yogunlukta_dt_COKUSU_kalkiyor():
    """Ölçülen mekanizma (A83): `divv ∝ 1/ρ_i` → yapay viskozite `dt → 0`."""
    eski = _cozucu(_rho(kucuk=1e-9))
    yeni = _cozucu(_rho(kucuk=1e-9), yogunluk_tabani=0.01)
    yeni.step(1e-9)                          # taban bir adimda devreye girer
    yeni._eval()
    assert yeni.compute_dt() > 1e3 * eski.compute_dt()


def test_gecersiz_eta_ADIYLA_duser():
    with pytest.raises(ValueError, match="yogunluk_tabani"):
        _cozucu(_rho(), yogunluk_tabani=1.5)


def test_fizik_ozeti_ve_surucu_bayragi():
    from dartrift.inference import forward

    arg = ({}, None, ("3:0.35",), 7.0, 0.024)
    assert forward._fizik_ozeti(*arg) == forward._fizik_ozeti(*arg, yogunluk_tabani=False)
    assert forward._fizik_ozeti(*arg, dayanim_kesme=True) != forward._fizik_ozeti(
        *arg, dayanim_kesme=True, yogunluk_tabani=True)
    assert forward.YOGUNLUK_TABANI_ETA == 0.01
    assert "yogunluk_tabani=(YOGUNLUK_TABANI_ETA if yogunluk_tabani" in inspect.getsource(
        forward.ileri_kosu_merdiven)
    surucu = (Path(__file__).resolve().parents[1] / "scripts"
              / "faz5_ensemble_merdiven.py").read_text(encoding="utf-8")
    assert "yogunluk_tabani=a.yogunluk_tabani" in surucu
