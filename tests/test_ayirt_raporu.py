"""Ayırt edilebilirlik raporu — **sonuçlardan önce** sınanır.

NEDEN VAR. Bu betik projenin asıl sorusunu yanıtlıyor: gözlenebilir
`θ` hakkında bilgi taşıyor mu? Yargı eşikleri (`F_ESIGI` vb.) koşudan
önce kilitlendi. Sınavlar, betiğin **bilinen** girdilerde doğru yargıyı
verdiğini gösteriyor — yani sonuç geldiğinde onu ayarlamaya yer yok.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest

_yol = Path(__file__).resolve().parents[1] / "scripts" / "ayirt_raporu.py"
_spec = importlib.util.spec_from_file_location("ayirt_raporu", _yol)
ar = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ar)


def _k(theta, deger, *, n_kacan=5, artik=1e-14, benzersiz=3):
    return {
        "theta": np.asarray(theta, dtype=float),
        "delta_beta": float(deger),
        "M_ejekta": float(deger),
        "v_ort": float(deger),
        "n_kacan": n_kacan,
        "artik_bagil": artik,
        "n_benzersiz_alpha0": benzersiz,
    }


# --- sira korelasyonu ---------------------------------------------------

def test_spearman_tam_monoton():
    a = [1, 2, 3, 4, 5]
    assert ar.spearman(a, [10, 20, 30, 40, 50]) == pytest.approx(1.0)
    assert ar.spearman(a, [50, 40, 30, 20, 10]) == pytest.approx(-1.0)


def test_spearman_dogrusal_olmayani_da_yakalar():
    a = [1, 2, 3, 4, 5]
    assert ar.spearman(a, [1, 4, 9, 16, 25]) == pytest.approx(1.0)


def test_spearman_beraberlikte_cokmez():
    assert np.isnan(ar.spearman([1, 1, 1, 1], [1, 2, 3, 4]))


def test_permutasyon_p_gurultude_buyuk_sinyalde_kucuk():
    rng = np.random.default_rng(0)
    x = np.arange(20, dtype=float)
    assert ar.permutasyon_p(x, x, n=2000) < 0.01
    assert ar.permutasyon_p(x, rng.permutation(x), n=2000) > 0.05


# --- varyans orani ------------------------------------------------------

def test_F_buyuk_theta_bilgi_tasiyorsa():
    """`θ`'lar çok farklı, tekrarlar birbirine çok yakın → `F` büyük."""
    tablo = {}
    for i in range(6):
        th = (1.0 + 0.1 * i, 1e4, 0.1 * i)
        tablo[th] = [_k(th, 10.0 * i), _k(th, 10.0 * i + 0.01)]
    v = ar.varyans_orani(tablo, "delta_beta")
    assert v["n_theta"] == 6 and v["n_tekrarli"] == 6
    assert v["F"] > ar.F_ESIGI


def test_F_kucuk_gurultu_baskinsa():
    """Değer `θ`'ya bağlı değil, yalnız gerçeklemeye → `F` küçük."""
    rng = np.random.default_rng(3)
    tablo = {}
    for i in range(8):
        th = (1.0 + 0.1 * i, 1e4, 0.1 * i)
        tablo[th] = [_k(th, rng.normal()), _k(th, rng.normal())]
    v = ar.varyans_orani(tablo, "delta_beta")
    assert v["F"] < ar.F_ESIGI


def test_tekrar_yoksa_F_hesaplanmaz():
    tablo = {(1.0, 1e4, 0.1): [_k((1.0, 1e4, 0.1), 1.0)],
             (1.2, 1e4, 0.2): [_k((1.2, 1e4, 0.2), 2.0)]}
    v = ar.varyans_orani(tablo, "delta_beta")
    assert np.isnan(v["F"]), "tekrar olmadan gurultu tabani YOK"


# --- on kosullar --------------------------------------------------------

def test_kacan_orani_esigi_uygulaniyor():
    tablo = {}
    for i in range(10):
        th = (1.0 + 0.1 * i, 1e4, 0.1 * i)
        # 7/10 noktada kacan var -> %70 < %80
        tablo[th] = [_k(th, 1.0, n_kacan=1 if i < 7 else 0)]
    ok = ar.on_kosullar(tablo)
    assert ok["kacan_orani"] == pytest.approx(0.7)
    assert ok["kacan_gecti"] is False


def test_A46_nobetcisi_iki_benzersiz_alpha0_dusuruyor():
    """`alpha0` yalnız iki değer taşıyorsa sahne `M0`'a düşmüş demektir."""
    th = (1.05, 1e4, 0.1)
    tablo = {th: [_k(th, 1.0, benzersiz=2)]}
    assert ar.on_kosullar(tablo)["M1_gecti"] is False
    tablo = {th: [_k(th, 1.0, benzersiz=3)]}
    assert ar.on_kosullar(tablo)["M1_gecti"] is True


def test_defter_acikken_dusuyor():
    th = (1.05, 1e4, 0.1)
    tablo = {th: [_k(th, 1.0, artik=1e-6)]}
    assert ar.on_kosullar(tablo)["defter_gecti"] is False


# --- eslestirme ---------------------------------------------------------

def test_ayni_theta_iki_tohumda_eslesiyor():
    th = (1.05, 1e4, 0.1)
    kollar = [[_k(th, 1.0)], [_k(th, 1.1)]]
    tablo = ar.esle(kollar)
    assert len(tablo) == 1
    assert len(next(iter(tablo.values()))) == 2


def test_farkli_theta_eslesmiyor():
    kollar = [[_k((1.05, 1e4, 0.1), 1.0)], [_k((1.30, 1e4, 0.4), 1.1)]]
    assert len(ar.esle(kollar)) == 2


# --- esikler kilitli ----------------------------------------------------

def test_esikler_protokolle_ayni():
    """Eşikler `docs/truba/PROTOKOL-G-AYIRT.md` ile birebir olmalı."""
    m = (Path(__file__).resolve().parents[1] / "docs" / "truba"
         / "PROTOKOL-G-AYIRT.md").read_text(encoding="utf-8")
    assert ar.F_ESIGI == 4.0 and "`F > 4`" in m
    assert ar.RHO_ESIGI == 0.5 and "0,5" in m
    assert ar.P_ESIGI == 0.05 and "0,05" in m
    assert ar.KACAN_ORANI_ESIGI == 0.80 and "%80" in m
