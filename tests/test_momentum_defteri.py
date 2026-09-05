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


# ------------------------------- DELTA BETA ve P_ejekta (yakinsama)

def test_DELTA_BETA_yakinsama_niceligi() -> None:
    """`β` değil `Δβ = β − 1` ölçülmeli.

    `β = 1,030` ile `1,040` arasında `β`'nın bağıl farkı `%0,97`;
    `Δβ`'nın bağıl farkı **`%33`**. `β` üzerinden `%20` eşiği koymak,
    gerçek ejekta katkısı üç katına çıksa bile *"yakınsadı"* der.
    """
    b1, b2 = 1.030, 1.040
    beta_fark = abs(b2 - b1) / b2
    delta_fark = abs((b2 - 1) - (b1 - 1)) / (b2 - 1)
    assert beta_fark < 0.01, beta_fark
    assert delta_fark == pytest.approx(0.25, abs=1e-9), delta_fark
    # ORAN 26,0 -- `beta` uzerinden olcmek farki 26 kat KUCUK gosterir
    assert delta_fark / beta_fark == pytest.approx(26.0, abs=0.1)


def test_defter_DELTA_BETAYI_veriyor() -> None:
    x = np.array([[0.0, 0.0, -2.0]])
    d = momentum_defteri(x, np.array([[0.0, 0.0, -1.0]]), np.array([1.0]),
                         mermi_kesri=np.zeros(1), p_imp=10.0, **KW)
    assert d["delta_beta_hedef"] == pytest.approx(d["beta_hedef"] - 1.0)
    assert d["delta_beta_hedef"] == pytest.approx(0.1)


def test_P_ejekta_VEKTORU_aci_kaymasini_yakaliyor() -> None:
    """`β` sabit kalıp yön dağılımı değişirse bu ancak vektörde görünür."""
    x = np.array([[0.0, 0.0, -2.0]])
    dik = momentum_defteri(x, np.array([[0.0, 0.0, -10.0]]), np.array([1.0]),
                           mermi_kesri=np.zeros(1), p_imp=100.0, **KW)
    egik = momentum_defteri(x, np.array([[10.0, 0.0, -10.0]]), np.array([1.0]),
                            mermi_kesri=np.zeros(1), p_imp=100.0, **KW)
    # eksenel bilesen ve delta_beta AYNI
    assert dik["P_ejekta_eksenel"] == pytest.approx(egik["P_ejekta_eksenel"])
    assert dik["delta_beta_hedef"] == pytest.approx(egik["delta_beta_hedef"])
    # ama buyukluk FARKLI -> aci kaymasi gorunuyor
    assert egik["P_ejekta_buyukluk"] > dik["P_ejekta_buyukluk"] * 1.4


def test_M_ejekta_kesirle_dogru() -> None:
    x = np.array([[0.0, 0.0, -2.0]])
    d = momentum_defteri(x, np.array([[0.0, 0.0, -10.0]]), np.array([10.0]),
                         mermi_kesri=np.array([0.3]), p_imp=100.0, **KW)
    assert d["M_ejekta"] == pytest.approx(7.0)


def test_P_ejekta_EKSENEL_beta_ile_tutarli() -> None:
    """`Δβ = −P_ejekta,∥ / p_mermi` — defterden türetiliyor."""
    x = np.array([[0.0, 0.0, -2.0]])
    d = momentum_defteri(x, np.array([[0.0, 0.0, -7.0]]), np.array([2.0]),
                         mermi_kesri=np.zeros(1), p_imp=50.0, **KW)
    assert d["delta_beta_hedef"] == pytest.approx(
        -d["P_ejekta_eksenel"] / d["p_imp"])


# --------------------------------- ZAMANSAL PLATO KAPISI + ACI

def test_plato_DUZ_sinyali_geciriyor() -> None:
    from dartrift.observables.momentum_defteri import plato_gecti
    t = np.linspace(0.0, 0.2, 25)
    assert plato_gecti(t, np.full(25, 0.033))["gecti"]


def test_plato_HALA_BUYUYEN_sinyali_DUSURUYOR() -> None:
    """Uzamsal yakınsama yeter görünse de ejekta gelişiyorsa ölçüm erken."""
    from dartrift.observables.momentum_defteri import plato_gecti
    t = np.linspace(0.0, 0.2, 25)
    assert not plato_gecti(t, 0.033 + 0.05 * t / 0.2)["gecti"]


def test_plato_UCLAR_AYNI_ama_ARADA_SALINIM_dusuyor() -> None:
    """İki uç nokta tesadüfen aynı olabilir — pencere **boyunca** bakılır."""
    from dartrift.observables.momentum_defteri import plato_gecti
    t = np.linspace(0.0, 0.2, 25)
    salinim = 0.033 + 0.02 * np.sin(8 * np.pi * t / 0.2)
    assert not plato_gecti(t, salinim)["gecti"]


def test_plato_SIFIRA_YAKIN_sinyalde_PATLAMIYOR() -> None:
    """Yalnız bağıl ölçüt `Δβ -> 0`'da paydayı sıfıra götürür.

    `Δβ = 1e-5` gibi neredeyse sıfır bir sinyalde gürültü sonsuz
    bağıl fark üretirdi; mutlak taban bunu engelliyor.
    """
    from dartrift.observables.momentum_defteri import plato_gecti
    t = np.linspace(0.0, 0.2, 25)
    r = plato_gecti(t, 1.0e-5 + 1.0e-7 * np.sin(20 * t))
    assert r["gecti"]
    assert r["tolerans"] == pytest.approx(1.0e-4)   # mutlak taban devrede


def test_plato_bozuk_girdi_REDDEDIYOR() -> None:
    from dartrift.observables.momentum_defteri import plato_gecti
    with pytest.raises(ValueError, match="en az"):
        plato_gecti(np.array([0.0, 1.0]), np.array([1.0, 1.0]))
    with pytest.raises(ValueError, match="pencere"):
        plato_gecti(np.linspace(0, 1, 5), np.ones(5), pencere=1.5)


def test_theta_ejekta_yon_degisimini_olcuyor() -> None:
    """`β` aynı kalıp açı değişirse `θ` yakalar."""
    x = np.array([[0.0, 0.0, -2.0]])
    dik = momentum_defteri(x, np.array([[0.0, 0.0, -10.0]]), np.array([1.0]),
                           mermi_kesri=np.zeros(1), p_imp=100.0, **KW)
    egik = momentum_defteri(x, np.array([[10.0, 0.0, -10.0]]), np.array([1.0]),
                            mermi_kesri=np.zeros(1), p_imp=100.0, **KW)
    assert dik["theta_ejekta_derece"] == pytest.approx(180.0)
    assert egik["theta_ejekta_derece"] == pytest.approx(135.0)
    assert dik["delta_beta_hedef"] == pytest.approx(
        egik["delta_beta_hedef"])          # beta AYNI, aci FARKLI


def test_theta_ejekta_YOKSA_nan() -> None:
    x = np.array([[0.0, 0.0, 0.5]])
    d = momentum_defteri(x, np.zeros((1, 3)), np.array([1.0]),
                         mermi_kesri=np.zeros(1), p_imp=10.0, **KW)
    assert np.isnan(d["theta_ejekta_derece"])


# ------------------------- SEVIYE BILESIMI ve YOGUNLASMA (A36)

def test_ejekta_SEVIYE_bilesimini_ayiriyor() -> None:
    """`33` ince ile `33` kaba parçacık **aynı sayısal kanıt değil**.

    Ölçülen (`L2`): düşük AV kolunda kaçan `33` parçacığın hepsi
    `372,83 kg` — tabandakinin (`5,83 kg`) **`64` katı**.
    """
    x = np.array([[0.0, 0.0, -2.0]] * 4)
    v = np.array([[0.0, 0.0, -10.0]] + [[0.0, 0.0, -1.0]] * 3)
    m = np.array([372.8, 5.83, 5.83, 5.83])
    d = momentum_defteri(x, v, m, mermi_kesri=np.zeros(4),
                         p_imp=1.0e5, **KW)
    sev = d["ejekta_seviyeleri"]
    assert len(sev) == 2
    assert sev[0]["parcacik_kg"] == pytest.approx(5.83)
    assert sev[0]["n"] == 3
    assert sev[1]["parcacik_kg"] == pytest.approx(372.8)
    assert sev[1]["n"] == 1
    assert d["m_ej_medyan"] == pytest.approx(5.83)
    assert d["m_ej_max"] == pytest.approx(372.8)


def test_TEK_KABA_parcacik_domine_ediyorsa_GORUNUYOR() -> None:
    """`β` yakınsarken momentumu bir-iki kaba parçacık taşıyorsa
    gözlenebilir **kırılgandır** — tanı, kapı değil."""
    x = np.array([[0.0, 0.0, -2.0]] * 4)
    v = np.array([[0.0, 0.0, -10.0]] + [[0.0, 0.0, -1.0]] * 3)
    m = np.array([372.8, 5.83, 5.83, 5.83])
    d = momentum_defteri(x, v, m, mermi_kesri=np.zeros(4),
                         p_imp=1.0e5, **KW)
    assert d["en_agir_1_pay"] > 0.99


def test_ESIT_dagilimda_yogunlasma_DUSUK() -> None:
    x = np.array([[0.0, 0.0, -2.0]] * 10)
    v = np.array([[0.0, 0.0, -5.0]] * 10)
    d = momentum_defteri(x, v, np.full(10, 5.83), mermi_kesri=np.zeros(10),
                         p_imp=1.0e5, **KW)
    assert d["en_agir_1_pay"] == pytest.approx(0.1, abs=1e-9)
    assert len(d["ejekta_seviyeleri"]) == 1


def test_kacan_YOKSA_bilesim_nan() -> None:
    x = np.array([[0.0, 0.0, 0.5]])
    d = momentum_defteri(x, np.zeros((1, 3)), np.array([1.0]),
                         mermi_kesri=np.zeros(1), p_imp=10.0, **KW)
    assert d["ejekta_seviyeleri"] == []
    assert np.isnan(d["en_agir_1_pay"])


# ------------------------- PROTOKOL v2: ust sinir TANI, kapi DEGIL

def test_asiri_sikisma_SONUCU_IPTAL_ETMIYOR() -> None:
    """Üst sınırın türetimi ampirik; sert kapı yapmak savunulamaz.

    `%74,3` bandın üst kenarı `up = v/2`'den geliyor ve bu **aynı
    malzeme/empedanstaki** simetrik düzlemsel çarpma için doğru.
    """
    from dartrift.observables.sok import sok_gecti, sok_yargisi_ayrintili
    a0 = np.array([1.7564])
    taban = 2700.0 / 1.7564
    r = sok_yargisi_ayrintili(np.array([taban * 2.20]), a0)
    assert r["yargi"] == "SOK_ASIRI_ADAY"
    assert r["asiri_suphe"] is True
    assert r["gecti"] is True, "asiri suphe TEK BASINA sonucu iptal etmemeli"
    assert sok_gecti(np.array([taban * 2.20]), a0)


def test_SERT_KAPI_yalnizca_ALT_sinir() -> None:
    from dartrift.observables.sok import sok_gecti
    a0 = np.array([1.7564])
    taban = 2700.0 / 1.7564
    assert not sok_gecti(np.array([taban * 1.0168]), a0)   # lam2=8
    assert sok_gecti(np.array([taban * 1.2200]), a0)       # lam2=20


def test_bilesim_MERMI_parcaciklarini_HARIC_tutuyor() -> None:
    """`R1`'de kaçan `803` parçacığın **hepsi mermi**; hedef kütlesi `0`.

    Onları dahil etmek *"803 parçacık, `0,0` kg, `P = -778 330`"*
    gibi anlamsız bir seviye üretiyordu — kaçan momentum merminin,
    hedefin değil.
    """
    x = np.array([[0.0, 0.0, -2.0]] * 3)
    v = np.array([[0.0, 0.0, -10.0]] * 3)
    m = np.array([5.83, 100.0, 100.0])
    f = np.array([0.0, 1.0, 1.0])          # ikisi TAMAMEN mermi
    d = momentum_defteri(x, v, m, mermi_kesri=f, p_imp=1.0e5, **KW)
    assert len(d["ejekta_seviyeleri"]) == 1
    assert d["ejekta_seviyeleri"][0]["parcacik_kg"] == pytest.approx(5.83)
    assert d["ejekta_seviyeleri"][0]["n"] == 1
    assert d["n_kacan_hedef"] == 1
    assert d["n_kacan_mermi"] == 2


def test_bilesim_hedef_ejektasi_YOKSA_bos() -> None:
    """`R1`'in gerçek durumu: kaçan hedef parçacığı **sıfır**."""
    x = np.array([[0.0, 0.0, -2.0]] * 2)
    v = np.array([[0.0, 0.0, -10.0]] * 2)
    d = momentum_defteri(x, v, np.array([100.0, 100.0]),
                         mermi_kesri=np.ones(2), p_imp=1.0e5, **KW)
    assert d["ejekta_seviyeleri"] == []
    assert np.isnan(d["en_agir_1_pay"])
    assert d["delta_beta_hedef"] == pytest.approx(0.0)
