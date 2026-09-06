"""Geçiş noktası raporu — **sonuçlardan önce** sınanır.

Eşikler (`DAYANIKLI_SIGMA`, `DAYANIKSIZ_SIGMA`, `R2_ESIGI`) koşudan
önce kilitlendi. Bu sınavlar betiğin bilinen girdilerde doğru yargıyı
verdiğini gösteriyor; sonuç geldiğinde eşiği ayarlamaya yer yok.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest

_kok = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "gecis_raporu", _kok / "scripts" / "gecis_raporu.py")
gr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gr)
vp = gr._yukle()


def _egri(x0, n=24, gurultu=0.004, tohum=0, d_alt=0.08, d_ust=0.36, w=0.5):
    rng = np.random.default_rng(tohum)
    x = np.linspace(3.1, 7.0, n)
    d = vp.sigmoid_model(x, d_alt, d_ust, x0, w)
    return x, d + rng.normal(0.0, gurultu, n)


# --- belirsizlik ---------------------------------------------------------

def test_jackknife_sigma_gurultuyle_BUYUYOR():
    x, d1 = _egri(5.9, gurultu=0.002, tohum=1)
    _, d2 = _egri(5.9, gurultu=0.020, tohum=1)
    s1 = gr.x0_belirsizligi(x, d1)["sigma_x0"]
    s2 = gr.x0_belirsizligi(x, d2)["sigma_x0"]
    assert s2 > s1, f"gurultulu veride sigma buyumeli: {s1:.4f} -> {s2:.4f}"


def test_jackknife_sigma_pozitif_ve_makul():
    x, d = _egri(5.9, tohum=2)
    jk = gr.x0_belirsizligi(x, d)
    assert jk["n"] == 24
    assert 0.0 < jk["sigma_x0"] < 1.0


# --- yargi ---------------------------------------------------------------

def _olcek(ad, x0, **kw):
    x, d = _egri(x0, **kw)
    return gr.olcek_raporu(ad, x, d)


def test_ayni_x0_DAYANIKLI():
    kaba = _olcek("kaba", 5.90, tohum=3)
    orta = _olcek("orta", 5.90, tohum=4)
    y = gr.yargi(kaba, orta)
    assert y["karar"] == "DAYANIKLI", (
        f"delta={y.get('delta_x0'):.4f} kat={y.get('kat'):.2f}")


def test_cok_farkli_x0_DAYANIKSIZ():
    kaba = _olcek("kaba", 5.40, tohum=3)
    orta = _olcek("orta", 6.40, tohum=4)
    y = gr.yargi(kaba, orta)
    assert y["karar"] == "DAYANIKSIZ", (
        f"delta={y.get('delta_x0'):.4f} kat={y.get('kat'):.2f}")


def test_esikler_kilitli():
    assert gr.DAYANIKLI_SIGMA == 2.0
    assert gr.DAYANIKSIZ_SIGMA == 4.0
    assert gr.R2_ESIGI == 0.85
    m = (_kok / "docs" / "truba" / "PROTOKOL-I-GECIS.md").read_text(
        encoding="utf-8")
    assert "2 √(σ²ᵏᵃᵇᵃ + σ²ᵒʳᵗᵃ)" in m or "2σ" in m
    assert "4σ" in m
    assert "0,85" in m


def test_yargi_sirasi_DAYANIKLI_ZAYIF_DAYANIKSIZ():
    """Eşikler arasında `ZAYIF` dalı gerçekten var mı."""
    taban = {"ad": "x", "R2": 0.99, "x0_veri_icinde": True, "gecerli": True,
             "sigma_x0": 0.10, "d_alt_sinirda": False, "veri_araligi": [3, 7]}
    for dx, beklenen in ((0.10, "DAYANIKLI"), (0.40, "ZAYIF"),
                         (0.90, "DAYANIKSIZ")):
        a = dict(taban, x0=5.0)
        b = dict(taban, x0=5.0 + dx)
        assert gr.yargi(a, b)["karar"] == beklenen, f"dx={dx}"


# --- on kosullar ---------------------------------------------------------

def test_dusuk_R2_OKUNMAZ():
    taban = {"ad": "x", "x0": 5.0, "sigma_x0": 0.1, "x0_veri_icinde": True,
             "d_alt_sinirda": False, "veri_araligi": [3, 7]}
    kaba = dict(taban, ad="kaba", R2=0.50, gecerli=False)
    orta = dict(taban, ad="orta", R2=0.99, gecerli=True)
    y = gr.yargi(kaba, orta)
    assert y["karar"] == "OKUNMAZ"
    assert "R2" in y["sebep"]


def test_x0_veri_disindaysa_OKUNMAZ():
    taban = {"ad": "x", "x0": 5.0, "sigma_x0": 0.1, "R2": 0.99,
             "d_alt_sinirda": False, "veri_araligi": [3, 7]}
    kaba = dict(taban, ad="kaba", x0_veri_icinde=False, gecerli=False)
    orta = dict(taban, ad="orta", x0_veri_icinde=True, gecerli=True)
    y = gr.yargi(kaba, orta)
    assert y["karar"] == "OKUNMAZ"
    assert "DISINDA" in y["sebep"]


def test_olcek_raporu_gecerlilik_bayragini_kuruyor():
    o = _olcek("kaba", 5.90, tohum=5)
    assert o["R2"] > gr.R2_ESIGI
    assert o["x0_veri_icinde"] is True
    assert o["gecerli"] is True
    assert o["n"] == 24
