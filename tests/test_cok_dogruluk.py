"""Çok doğruluklu vekil (Kennedy–O'Hagan AR(1)) — klasik Forrester sınaması.

Forrester, Sóbester & Keane (2007) iki doğruluklu sınama fonksiyonu:

    f_H(x) = (6x − 2)² sin(12x − 4)
    f_L(x) = 0,5 f_H(x) + 10 (x − 0,5) − 5

Yani `f_H = 2 f_L − 20 (x − 0,5) + 10`: `ρ = 2` ve fark doğrusal. 11 ucuz +
4 pahalı noktayla eşevrensel kriging, yalnız 4 pahalı noktalı GP'den çok
daha iyi olmalı (literatürdeki standart gösterim).
"""
from __future__ import annotations

import numpy as np
import pytest

from dartrift.inference.cok_dogruluk import (
    RHO_IZGARASI,
    cok_dogruluk_uydur,
)
from dartrift.inference.design import ParamSpace
from dartrift.inference.gp_vekil import gp_uydur

UZAY = ParamSpace(names=("x",), lo=(0.0,), hi=(1.0,), log=(False,))


def f_h(x):
    return (6 * x - 2) ** 2 * np.sin(12 * x - 4)


def f_l(x):
    return 0.5 * f_h(x) + 10 * (x - 0.5) - 5


X_L = np.linspace(0.0, 1.0, 11)[:, None]
X_H = np.array([0.0, 0.4, 0.6, 1.0])[:, None]
IZGARA = tuple(np.round(np.linspace(0.0, 3.0, 121), 6))


def _hata(tahmin):
    xs = np.linspace(0.0, 1.0, 201)[:, None]
    return float(np.sqrt(np.mean((tahmin(xs) - f_h(xs[:, 0])) ** 2)))


def test_FORRESTER_cok_dogruluk_tek_katmandan_COK_iyi():
    v = cok_dogruluk_uydur(UZAY, X_L, f_l(X_L[:, 0]), X_H, f_h(X_H[:, 0]),
                           rho_izgara=IZGARA)
    tek = gp_uydur(UZAY, X_H, f_h(X_H[:, 0]))
    e_cok = _hata(v.predict)
    e_tek = _hata(tek.predict)
    assert e_cok < 0.25 * e_tek, (e_cok, e_tek)


def test_FORRESTER_rho_dogru_bulunuyor():
    v = cok_dogruluk_uydur(UZAY, X_L, f_l(X_L[:, 0]), X_H, f_h(X_H[:, 0]),
                           rho_izgara=IZGARA)
    assert v.rho == pytest.approx(2.0, abs=0.15)
    assert not any("kenarda" in u for u in v.uyarilar)


def test_VARYANS_pozitif_ve_orta_noktalarda_kucuk():
    v = cok_dogruluk_uydur(UZAY, X_L, f_l(X_L[:, 0]), X_H, f_h(X_H[:, 0]),
                           rho_izgara=IZGARA)
    xs = np.linspace(0.0, 1.0, 101)[:, None]
    _, var = v.predict_u(UZAY.to_unit(xs), yeni_gerceklem=False)
    assert np.all(var >= 0.0)
    _, var_h = v.predict_u(UZAY.to_unit(X_H), yeni_gerceklem=False)
    assert float(var_h.max()) < float(var.max())


def test_DETERMINIST_ayni_veri_bit_ayni():
    a = cok_dogruluk_uydur(UZAY, X_L, f_l(X_L[:, 0]), X_H, f_h(X_H[:, 0]),
                           rho_izgara=IZGARA)
    b = cok_dogruluk_uydur(UZAY, X_L, f_l(X_L[:, 0]), X_H, f_h(X_H[:, 0]),
                           rho_izgara=IZGARA)
    xs = np.linspace(0.0, 1.0, 17)[:, None]
    assert a.rho == b.rho
    assert np.array_equal(a.predict(xs), b.predict(xs))


def test_KENAR_rho_UYARILIYOR():
    """Gerçek `ρ = 2` iken varsayılan ızgara (0–2) kenarda kalır → uyarı."""
    v = cok_dogruluk_uydur(UZAY, X_L, f_l(X_L[:, 0]), X_H, f_h(X_H[:, 0]))
    assert v.rho == max(RHO_IZGARASI)
    assert any("kenarda" in u for u in v.uyarilar)


def test_IC_ICE_olmayan_tasarim_UYARILIYOR():
    xh = np.array([0.05, 0.45, 0.65, 0.95])[:, None]
    v = cok_dogruluk_uydur(UZAY, X_L, f_l(X_L[:, 0]), xh, f_h(xh[:, 0]),
                           rho_izgara=IZGARA)
    assert any("ic_ice_degil" in u for u in v.uyarilar)


@pytest.mark.parametrize("kw,mesaj", [
    ({"x_orta": X_H[:2], "y_orta": f_h(X_H[:2, 0])}, "en az 3"),
    ({"x_kaba": X_L[:4], "y_kaba": f_l(X_L[:4, 0])}, "COK olmali"),
    ({"rho_izgara": (1.0, 2.0)}, "rho_izgara"),
])
def test_GECERSIZ_girdi_REDDEDILIYOR(kw, mesaj):
    tam = dict(x_kaba=X_L, y_kaba=f_l(X_L[:, 0]), x_orta=X_H,
               y_orta=f_h(X_H[:, 0]), rho_izgara=IZGARA)
    tam.update(kw)
    with pytest.raises(ValueError, match=mesaj):
        cok_dogruluk_uydur(UZAY, tam["x_kaba"], tam["y_kaba"], tam["x_orta"],
                           tam["y_orta"], rho_izgara=tam["rho_izgara"])


def test_UC_BOYUTLU_uzayda_calisiyor():
    """Bizim θ uzayı 3 boyutlu: kaba = orta + düzgün sapma; ρ ≈ 1 bulunmalı."""
    uzay = ParamSpace(names=("a", "y", "f"), lo=(1.0, 1.0, 0.0),
                      hi=(1.3, 500.0, 0.5), log=(False, True, False))
    rng = np.random.default_rng(4)
    xk = np.column_stack([rng.uniform(1.0, 1.3, 30),
                          10 ** rng.uniform(0.0, np.log10(500.0), 30),
                          rng.uniform(0.0, 0.5, 30)])

    def orta(x):
        return 1.0 + 2.0 / (1.0 + np.log10(x[:, 1])) - 0.5 * x[:, 2]

    def kaba(x):
        return orta(x) + 0.1 + 0.05 * (x[:, 0] - 1.15)

    xo = xk[:8]
    v = cok_dogruluk_uydur(uzay, xk, kaba(xk), xo, orta(xo))
    assert 0.7 < v.rho < 1.3
    xt = xk[10:20]
    assert np.max(np.abs(v.predict(xt) - orta(xt))) < 0.2
