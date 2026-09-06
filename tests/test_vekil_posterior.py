"""Vekil model + posterior — bilinen girdilerde doğru mu.

NEDEN VAR. Bu betik zincirin son halkası: `θ → krater → posterior`.
Bir çıkarım aracının en tehlikeli kusuru, **yanlış ama dar** bir
güven aralığı üretmesidir. Sınavlar üç şeyi kilitler: uydurma bilinen
parametreleri geri veriyor mu, posterior gerçeği kapsıyor mu, ve
platoda **tek yanlı** olduğunu söylüyor mu.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest

_yol = Path(__file__).resolve().parents[1] / "scripts" / "vekil_posterior.py"
_spec = importlib.util.spec_from_file_location("vekil_posterior", _yol)
vp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vp)


GERCEK = (0.08, 0.36, 5.9, 0.45)      # d_alt, d_ust, x0, w


def _veri(n=24, gurultu=0.0, tohum=0):
    rng = np.random.default_rng(tohum)
    x = np.linspace(3.1, 7.0, n)
    d = vp.sigmoid_model(x, *GERCEK)
    if gurultu:
        d = d + rng.normal(0.0, gurultu, n)
    return x, d


# --- model ---------------------------------------------------------------

def test_sigmoid_azalan_ve_sinirli():
    x = np.linspace(2.0, 9.0, 200)
    d = vp.sigmoid_model(x, *GERCEK)
    assert np.all(np.diff(d) < 0), "yuksek Y0 -> sig krater olmali"
    assert d[0] == pytest.approx(GERCEK[1], abs=1e-3), "dusuk uc platosu"
    assert d[-1] == pytest.approx(GERCEK[0], abs=1e-3), "yuksek uc platosu"


def test_x0_gecis_noktasi_ortada():
    d = vp.sigmoid_model(np.array([GERCEK[2]]), *GERCEK)[0]
    assert d == pytest.approx((GERCEK[0] + GERCEK[1]) / 2, abs=1e-9)


# --- uydurma -------------------------------------------------------------

def test_gurultusuz_veride_parametreler_geri_geliyor():
    x, d = _veri()
    v = vp.uydur(x, d)
    assert v["R2"] > 0.999
    assert v["x0"] == pytest.approx(GERCEK[2], abs=0.15)
    assert v["d_ust"] == pytest.approx(GERCEK[1], abs=0.01)
    assert v["d_alt"] == pytest.approx(GERCEK[0], abs=0.02)


def test_gurultulu_veride_de_makul():
    x, d = _veri(gurultu=0.01, tohum=3)
    v = vp.uydur(x, d)
    assert v["R2"] > 0.95
    assert v["x0"] == pytest.approx(GERCEK[2], abs=0.4)
    assert 0.0 < v["artik_sigma"] < 0.05


# --- posterior -----------------------------------------------------------

def test_posterior_gercegi_KAPSIYOR():
    """Bilinen `Y₀`'dan üretilen gözlem, `%95` aralıkta olmalı."""
    x, d = _veri(gurultu=0.005, tohum=1)
    v = vp.uydur(x, d)
    x_gercek = 6.3
    d_gozlem = float(vp.sigmoid_model(np.array([x_gercek]), *GERCEK)[0])
    po = vp.posterior(v, d_gozlem, 0.01)
    assert po["q025"] < x_gercek < po["q975"], (
        f"gercek {x_gercek} posteriorun %95 araliginin DISINDA: "
        f"[{po['q025']:.3f}, {po['q975']:.3f}]"
    )


def test_platoda_TEK_YANLI_diyor():
    """Plato bölgesinde gözlenebilir bilgi taşımıyor; iki yanlı aralık YASAK."""
    x, d = _veri(gurultu=0.005, tohum=2)
    v = vp.uydur(x, d)
    # plato degeri: dusuk Y0 ucundaki derinlik
    po = vp.posterior(v, GERCEK[1], 0.01)
    assert po["tek_yanli"] is True, "platoda tek yanli olmali"
    assert po["alt_sinira_dayali"] is True, (
        "platoda %68 araliginin ALT ucu onsel sinirina dayanmali"
    )
    # `bilgi_orani` icin MUTLAK esik KOYMUYORUM. Once `> 0,5` yazmistim;
    # olculen `0,395` cikti ve esigi ayarlamak yerine iddiayi
    # DUZELTTIM: platoda gozlenebilir BIR MIKTAR bilgi tasiyor --
    # yuksek `Y0`'i eliyor. Tasimadigi sey IKI YANLI sinir.
    # Anlamli sinav GORELI olan (asagida).
    assert po["q84"] < vp.ONSEL_LOG10_UST, "ust sinir yine de daralmali"


def test_gecis_bolgesinde_IKI_YANLI():
    x, d = _veri(gurultu=0.005, tohum=2)
    v = vp.uydur(x, d)
    d_gecis = (GERCEK[0] + GERCEK[1]) / 2
    po = vp.posterior(v, d_gecis, 0.005)
    assert po["tek_yanli"] is False, "gecis bolgesinde iki yanli olmali"
    assert po["q84"] - po["q16"] < 1.0, "gecis bolgesinde aralik dar olmali"
    assert po["bilgi_orani"] < 0.4, "gecis bolgesinde posterior DARALMALI"


def test_gozlem_sigmasi_buyuyunce_aralik_GENISLIYOR():
    x, d = _veri(gurultu=0.005, tohum=4)
    v = vp.uydur(x, d)
    d_gecis = (GERCEK[0] + GERCEK[1]) / 2
    dar = vp.posterior(v, d_gecis, 0.005)
    genis = vp.posterior(v, d_gecis, 0.05)
    assert (genis["q84"] - genis["q16"]) > (dar["q84"] - dar["q16"]), (
        "daha belirsiz gozlem daha GENIS posterior vermeli"
    )


def test_posterior_onsel_disina_TASMIYOR():
    x, d = _veri(gurultu=0.005, tohum=5)
    v = vp.uydur(x, d)
    po = vp.posterior(v, 0.5, 0.01)      # her degerden buyuk derinlik
    assert vp.ONSEL_LOG10_ALT <= po["MAP"] <= vp.ONSEL_LOG10_UST
    assert vp.ONSEL_LOG10_ALT <= po["q025"]
    assert po["q975"] <= vp.ONSEL_LOG10_UST


# --- birak-bir dogrulama -------------------------------------------------

def test_birak_bir_gurultusuz_veride_neredeyse_kusursuz():
    x, d = _veri(n=14)
    lo = vp.birak_bir_dogrula(x, d)
    assert lo["n"] == 14
    assert lo["RMSE"] < 0.01, f"gurultusuz veride RMSE {lo['RMSE']}"


def test_birak_bir_yanliligi_kucuk():
    x, d = _veri(n=14, gurultu=0.01, tohum=7)
    lo = vp.birak_bir_dogrula(x, d)
    assert abs(lo["yanlilik"]) < 0.02


def test_bilgi_orani_plato_ile_gecisi_ayiriyor():
    """`bilgi_orani`: posteriorun önsele göre darlığı.

    A65: ilk yazdığım "tek yanlı" ölçüsü *sınıra yığılan olasılık
    kütlesi* idi ve platoda **çalışmadı** — orada posterior yığılmıyor,
    yayılıyor. Bu sınav iki rejimi ölçünün ayırdığını kilitler.
    """
    x, d = _veri(gurultu=0.005, tohum=11)
    v = vp.uydur(x, d)
    plato = vp.posterior(v, GERCEK[1], 0.01)
    gecis = vp.posterior(v, (GERCEK[0] + GERCEK[1]) / 2, 0.005)
    assert plato["bilgi_orani"] > 3 * gecis["bilgi_orani"], (
        f"plato {plato['bilgi_orani']:.3f} vs gecis {gecis['bilgi_orani']:.3f}"
    )
