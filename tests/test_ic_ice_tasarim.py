"""İç içe ince tasarım sınavları (ADR-0059 §3.2, havuz okunmadan yazıldı)."""
from __future__ import annotations

import numpy as np
import pytest

from dartrift.inference.design import DART_UZAYI_S4, lhs_design
from dartrift.inference.ic_ice_tasarim import (
    ayrim_raporu,
    ic_ice_mi,
    maximin_alt_kume,
)

#: PROTOKOL-HAVUZ §3'ün kilitli tasarımı.
_N, _K, _TOHUM = 96, 12, 20260906


def _havuz():
    return lhs_design(DART_UZAYI_S4, _N, root_seed=_TOHUM)


# --- determinizm: ADR-0059'un birinci sarti -----------------------------

def test_secim_DETERMINISTIK_ayni_girdi_ayni_cikti():
    u = DART_UZAYI_S4.to_unit(_havuz())
    a = maximin_alt_kume(u, _K)
    b = maximin_alt_kume(u, _K)
    assert np.array_equal(a, b)


def test_secim_TOHUMSUZ_global_rng_degistirse_de_ayni():
    # Betik baska bir yerde rastgelelik kullanirsa secim kaymamali.
    u = DART_UZAYI_S4.to_unit(_havuz())
    a = maximin_alt_kume(u, _K)
    np.random.default_rng(1234).random(1000)
    np.random.seed(99)
    b = maximin_alt_kume(u, _K)
    assert np.array_equal(a, b)


def test_KILITLI_12_nokta_kaydi():
    # Bu sinav seçimi KILITLER: havuz verisi gelince indeksler degisirse
    # (ornegin biri "daha iyi" diye) sinav duser. Kural 6.
    u = DART_UZAYI_S4.to_unit(_havuz())
    idx = maximin_alt_kume(u, _K)
    assert idx.tolist() == [11, 20, 33, 44, 45, 57, 58, 62, 74, 78, 87, 92]


# --- dogruluk ------------------------------------------------------------

def test_dogru_sayida_tekrarsiz_artan_indeks():
    u = DART_UZAYI_S4.to_unit(_havuz())
    idx = maximin_alt_kume(u, _K)
    assert idx.size == _K
    assert np.unique(idx).size == _K
    assert np.all(np.diff(idx) > 0)
    assert idx.min() >= 0 and idx.max() < _N


def test_k_esit_n_ise_hepsi():
    u = np.random.default_rng(0).random((7, 3))
    assert np.array_equal(maximin_alt_kume(u, 7), np.arange(7))


def test_gecersiz_k_reddedilir():
    u = np.random.default_rng(0).random((5, 2))
    with pytest.raises(ValueError, match="1 <= k <= n"):
        maximin_alt_kume(u, 6)
    with pytest.raises(ValueError, match="1 <= k <= n"):
        maximin_alt_kume(u, 0)


def test_tek_boyutlu_girdi_reddedilir():
    with pytest.raises(ValueError, match=r"\(n, d\) olmali"):
        maximin_alt_kume(np.arange(5.0), 2)


def test_ilk_nokta_MERKEZE_en_yakin():
    # Kosede baslamak zinciri kenara yapistirir; belgelenen davranis bu.
    u = np.array([[0.0, 0.0], [1.0, 1.0], [0.5, 0.5], [0.0, 1.0]])
    assert maximin_alt_kume(u, 1).tolist() == [2]


def test_uzak_kumeler_ayri_ayri_ORNEKLENIYOR():
    # Iki ayri yigin; k=2 ikisinden birer nokta almali.
    g = np.random.default_rng(3)
    u = np.vstack([g.random((20, 2)) * 0.1,
                   0.9 + g.random((20, 2)) * 0.1])
    idx = maximin_alt_kume(u, 2)
    assert (idx[0] < 20) != (idx[1] < 20)


# --- maximin GERCEKTEN rastgeleden iyi mi -------------------------------

def test_maximin_rastgeleden_DAHA_IYI_yayiliyor():
    u = DART_UZAYI_S4.to_unit(_havuz())
    r = ayrim_raporu(u, maximin_alt_kume(u, _K))
    assert r["min_ikili"] > r["rastgele_ortalama_min_ikili"]


def test_ayrim_raporu_alanlari():
    u = DART_UZAYI_S4.to_unit(_havuz())
    r = ayrim_raporu(u, maximin_alt_kume(u, _K))
    assert r["k"] == _K and r["n"] == _N
    assert 0.0 < r["min_ikili"] < np.sqrt(3.0)
    assert 0.0 < r["en_uzak_ortulmemis"] < np.sqrt(3.0)


def test_rapor_tek_nokta_reddeder():
    u = np.random.default_rng(0).random((5, 2))
    with pytest.raises(ValueError, match="en az 2 nokta"):
        ayrim_raporu(u, [0])


# --- ic ice kapisi (ADR-0059 kapi 1) ------------------------------------

def test_ic_ice_mi_secilen_alt_kume_icin_DOGRU():
    X = _havuz()
    idx = maximin_alt_kume(DART_UZAYI_S4.to_unit(X), _K)
    assert ic_ice_mi(X[idx], X)


def test_ic_ice_mi_DISARIDAN_nokta_icin_YANLIS():
    X = _havuz()
    disari = lhs_design(DART_UZAYI_S4, _K, root_seed=_TOHUM + 1)
    assert not ic_ice_mi(disari, X)


def test_ic_ice_mi_KUCUK_kaymayi_yakalar():
    # Ince kosu yanlis theta ile gonderilirse indeks listesi yine dogru
    # gorunur; kapi DEGERE bakmali.
    X = _havuz()
    idx = maximin_alt_kume(DART_UZAYI_S4.to_unit(X), _K)
    bozuk = X[idx].copy()
    bozuk[0, 0] += 1e-6
    assert not ic_ice_mi(bozuk, X)


def test_ic_ice_mi_boyut_uyusmazligi():
    with pytest.raises(ValueError, match="boyutlar uyusmuyor"):
        ic_ice_mi(np.zeros((2, 2)), np.zeros((3, 3)))
