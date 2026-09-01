"""Momentum defteri — `β`'nın bileşimi provenance ile ayrılıyor mu.

`β = 3,2` demek tek başına hiçbir şey kanıtlamaz. Bu depoda ölçüldü ki
`β = 1,4112`'nin **tamamı mermi geri tepmesiydi**; hedef katkısı tam
`0`. Fizik düzelince `β` `1,379 -> 1,081`'e **düştü** çünkü sahte
katkı kayboldu.

Defter kapanmıyorsa `β` **raporlanmaz** — kapanmayan bir defterin
türevi de kapanmaz.
"""
from __future__ import annotations

import numpy as np
import pytest

from dartrift.observables.momentum_defteri import (
    ARTIK_ESIGI,
    defter_satiri,
    momentum_defteri,
)

E = np.array([0.0, 0.0, 1.0])
KW = dict(R=1.0, v_esc=0.1, ehat=E)


def test_HICBIR_SEY_kacmazsa_beta_tam_BIR() -> None:
    """Mermi gömülü kalırsa `β = 1` — momentum artışı yok."""
    x = np.array([[0.0, 0.0, 0.5]])
    d = momentum_defteri(x, np.array([[0.0, 0.0, 10.0]]), np.array([1.0]),
                         mermi_kesri=np.array([1.0]), p_imp=10.0, **KW)
    assert d["beta_toplam"] == pytest.approx(1.0)
    assert d["kapandi"] and d["artik_bagil"] == pytest.approx(0.0)


def test_HEDEF_ejektasi_beta_hedefi_YUKSELTIYOR() -> None:
    """`-ê` yönünde kaçan **hedef** maddesi gerçek `β` katkısıdır.

    Geometri: mermi `+ê` ile geliyor, ejekta `-ê`'ye uçuyor. Kaçan
    parçacık `-z`'de ve `-z`'ye gidiyor -> `v_r > 0` (dışa doğru).
    """
    x = np.array([[0.0, 0.0, -2.0], [0.0, 0.0, 0.5]])
    v = np.array([[0.0, 0.0, -5.0], [0.0, 0.0, 15.0]])
    m = np.array([1.0, 1.0])
    d = momentum_defteri(x, v, m, mermi_kesri=np.array([0.0, 1.0]),
                         p_imp=10.0, **KW)
    assert d["n_kacan_hedef"] == 1
    assert d["beta_hedef"] == pytest.approx(1.5)     # 1 - (-5)/10
    assert d["beta_mermi"] == pytest.approx(0.0)
    assert d["kapandi"]


def test_MERMI_geri_tepmesi_AYRI_sayiliyor() -> None:
    """Bu deponun `β = 1,4112`'si tamamen buydu — ve `β` sayılmamalı."""
    x = np.array([[0.0, 0.0, -2.0], [0.0, 0.0, 0.5]])
    v = np.array([[0.0, 0.0, -4.0], [0.0, 0.0, 14.0]])
    d = momentum_defteri(x, v, np.array([1.0, 1.0]),
                         mermi_kesri=np.array([1.0, 0.0]), p_imp=10.0, **KW)
    assert d["n_kacan_mermi"] == 1 and d["n_kacan_hedef"] == 0
    assert d["beta_mermi"] == pytest.approx(0.4)
    assert d["beta_hedef"] == pytest.approx(1.0)     # hedef hic kacmadi
    assert d["beta_toplam"] == pytest.approx(1.4)


def test_defter_KAPANMAZSA_isaretliyor() -> None:
    """Momentum korunmuyorsa `β` raporlanmamalı."""
    x = np.array([[0.0, 0.0, 0.5]])
    d = momentum_defteri(x, np.array([[0.0, 0.0, 1.0]]), np.array([1.0]),
                         mermi_kesri=np.array([1.0]), p_imp=10.0, **KW)
    assert not d["kapandi"]
    assert d["artik_bagil"] == pytest.approx(0.9)
    assert "RAPORLANMAZ" in defter_satiri(d)


def test_kacis_olcutu_IKI_kosul_birden() -> None:
    """`r > R` **ve** `v_r > v_esc`; biri yetmez."""
    # (a) hizli ve DISA dogru ama YARICAP ICINDE -> kacmis sayilmaz
    d = momentum_defteri(np.array([[0.0, 0.0, -0.5]]),
                         np.array([[0.0, 0.0, -50.0]]), np.array([1.0]),
                         mermi_kesri=np.zeros(1), p_imp=10.0, **KW)
    assert d["n_kacan_hedef"] == 0
    # (b) YARICAP DISINDA ama ICERI dogru -> kacmis sayilmaz
    d = momentum_defteri(np.array([[0.0, 0.0, -2.0]]),
                         np.array([[0.0, 0.0, 50.0]]), np.array([1.0]),
                         mermi_kesri=np.zeros(1), p_imp=10.0, **KW)
    assert d["n_kacan_hedef"] == 0
    # (c) ikisi birden -> kacti
    d = momentum_defteri(np.array([[0.0, 0.0, -2.0]]),
                         np.array([[0.0, 0.0, -50.0]]), np.array([1.0]),
                         mermi_kesri=np.zeros(1), p_imp=10.0, **KW)
    assert d["n_kacan_hedef"] == 1


def test_KESIR_ile_kutle_TAM_bolunuyor() -> None:
    """Ara değerli `mermi_kesri` kütleyi bölmeli, yuvarlamamalı."""
    x = np.array([[0.0, 0.0, -2.0]])
    d = momentum_defteri(x, np.array([[0.0, 0.0, -10.0]]), np.array([10.0]),
                         mermi_kesri=np.array([0.3]), p_imp=100.0, **KW)
    assert d["kutle_kacan_mermi"] == pytest.approx(3.0)
    assert d["kutle_kacan_hedef"] == pytest.approx(7.0)


def test_esik_makul() -> None:
    assert 0.0 < ARTIK_ESIGI <= 1.0e-2


def test_bozuk_girdi_REDDEDILIYOR() -> None:
    x = np.zeros((2, 3))
    with pytest.raises(ValueError, match="ayni uzunlukta"):
        momentum_defteri(x, x, np.ones(2), mermi_kesri=np.ones(1),
                         p_imp=1.0, **KW)
    with pytest.raises(ValueError, match=r"\[0,1\]"):
        momentum_defteri(x, x, np.ones(2), mermi_kesri=np.array([0.0, 1.5]),
                         p_imp=1.0, **KW)
    with pytest.raises(ValueError, match="p_imp pozitif"):
        momentum_defteri(x, x, np.ones(2), mermi_kesri=np.zeros(2),
                         p_imp=0.0, **KW)
