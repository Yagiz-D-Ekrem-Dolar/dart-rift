"""Ara an kare planı sınavları (A116 üçüncü örneğini bağlarken yazıldı)."""
from __future__ import annotations

import numpy as np
import pytest

from dartrift.anlik_plan import (
    A95_PLANI,
    VIDEO_PLANI,
    AnlikPlanlayici,
    Bolum,
    kare_zamanlari,
    sabit_altornek,
)

# --- Bolum ---------------------------------------------------------------

def test_bolum_ters_aralik_reddedilir():
    with pytest.raises(ValueError, match="t1 > t0"):
        Bolum(10.0, 1.0, 5)


def test_bolum_sifir_kare_reddedilir():
    with pytest.raises(ValueError, match="n >= 1"):
        Bolum(0.0, 1.0, 0)


def test_log_bolumde_t0_sifir_reddedilir():
    # log 0 tanimsiz; sessizce -inf uretmektense hata vermeli.
    with pytest.raises(ValueError, match="log 0 tanimsiz"):
        Bolum(0.0, 1.0, 5, log=True)


def test_bolum_t0_dahil_degil_t1_dahil():
    b = Bolum(0.0, 1.0, 4)
    t = b.zamanlar()
    assert t.size == 4
    assert t[0] > 0.0
    assert np.isclose(t[-1], 1.0)


def test_log_bolum_geometrik():
    b = Bolum(1.0, 1000.0, 3, log=True)
    t = b.zamanlar()
    # geomspace(1, 1000, 4) = [1, 10, 100, 1000]; t0 atilinca [10, 100, 1000]
    assert np.allclose(t, [10.0, 100.0, 1000.0])


# --- kare_zamanlari ------------------------------------------------------

def test_bitisik_olmayan_bolumler_reddedilir():
    with pytest.raises(ValueError, match="bitisik degil"):
        kare_zamanlari([Bolum(0.0, 1.0, 2), Bolum(5.0, 10.0, 2)])


def test_bos_bolum_listesi_reddedilir():
    with pytest.raises(ValueError, match="en az bir bolum"):
        kare_zamanlari([])


def test_t_sifir_eklenir_ve_kesin_artan():
    t = kare_zamanlari([Bolum(0.0, 1.0, 3)])
    assert t[0] == 0.0
    assert t.size == 4
    assert np.all(np.diff(t) > 0.0)


def test_t_sifir_kapatilabilir():
    t = kare_zamanlari([Bolum(0.0, 1.0, 3)], t_sifir=False)
    assert t[0] > 0.0
    assert t.size == 3


def test_VIDEO_PLANI_181_kare_ve_600s_bitiyor():
    t = kare_zamanlari(VIDEO_PLANI)
    assert t.size == 181          # 0 + 60 + 60 + 60
    assert t[0] == 0.0
    assert np.isclose(t[-1], 600.0)
    assert np.all(np.diff(t) > 0.0)


def test_VIDEO_PLANI_erken_ani_COZUYOR_esit_aralikli_COZMUYOR():
    # Modulun varlik sebebi: esit aralikli plan carpmayi tek karede gecer.
    t = kare_zamanlari(VIDEO_PLANI)
    erken = int(np.count_nonzero(t <= 1.0))
    esit = np.linspace(0.0, 600.0, 181)
    erken_esit = int(np.count_nonzero(esit <= 1.0))
    assert erken == 61            # 0 dahil, ilk bolumun 60 karesi
    assert erken_esit == 1        # yalniz t=0
    assert erken > 20 * erken_esit


def test_A95_PLANI_koni_penceresini_siklastiriyor():
    t = kare_zamanlari(A95_PLANI)
    pencere = int(np.count_nonzero((t > 100.0) & (t <= 250.0)))
    disari = int(t.size - pencere)
    assert pencere == 30
    # 150 s'lik pencerede 30 kare, kalan 450 s'de 21 kare (0 dahil).
    assert pencere / 150.0 > disari / 450.0


# --- AnlikPlanlayici -----------------------------------------------------

def test_planlayici_artan_olmayan_zamani_reddeder():
    with pytest.raises(ValueError, match="kesin artan"):
        AnlikPlanlayici([0.0, 1.0, 1.0, 2.0])


def test_planlayici_bos_reddeder():
    with pytest.raises(ValueError, match="en az bir kare"):
        AnlikPlanlayici([])


def test_yarim_acik_aralik_ayni_kareyi_iki_kez_vermez():
    p = AnlikPlanlayici([1.0, 2.0, 3.0])
    assert p.gereken(0.0, 1.0) == [0]
    assert p.gereken(1.0, 2.0) == [1]     # 1.0 tekrar DONMEZ
    assert p.gereken(2.0, 3.0) == [2]


def test_buyuk_adim_atlanan_karelerin_HEPSINI_verir():
    # Degisken dt: tek adim bircok kareyi asabilir. Kare kaybi olmamali.
    p = AnlikPlanlayici([0.1, 0.2, 0.5, 1.0, 5.0])
    assert p.gereken(0.0, 1.0) == [0, 1, 2, 3]


def test_kare_dusmeyen_adim_bos_liste():
    p = AnlikPlanlayici([1.0, 2.0])
    assert p.gereken(0.0, 0.5) == []


def test_tam_sureste_her_kare_TAM_BIR_KEZ_yazilir():
    t = kare_zamanlari(VIDEO_PLANI)
    p = AnlikPlanlayici(t)
    sayac = np.zeros(t.size, dtype=int)
    t_onceki = -1.0                      # t=0 karesi de yakalansin
    # Duzensiz adimlarla bastan sona suhup her karenin tam bir kez
    # dondugunu dogrula.
    rng = np.random.default_rng(7)
    t_simdi = 0.0
    while t_simdi < 600.0:
        t_simdi = min(600.0, t_simdi + float(rng.uniform(0.01, 12.0)))
        for i in p.gereken(t_onceki, t_simdi):
            sayac[i] += 1
        t_onceki = t_simdi
    assert np.all(sayac == 1)
    assert p.eksik() == []


def test_eksik_kare_bildirilir():
    p = AnlikPlanlayici([1.0, 2.0, 3.0])
    p.gereken(0.0, 2.0)
    assert p.eksik() == [2]


def test_geriye_giden_zaman_reddedilir():
    p = AnlikPlanlayici([1.0, 2.0])
    with pytest.raises(ValueError, match="t_simdi >= t_onceki"):
        p.gereken(5.0, 1.0)


# --- sabit_altornek ------------------------------------------------------

def test_altornek_ayni_tohumda_AYNI_kume():
    # Videonun en kritik ozelligi: karelerde ayni parcaciklar olmali,
    # yoksa taneler kare kare gorunup kaybolur.
    a = sabit_altornek(1_000_000, 200_000, tohum=20261009)
    b = sabit_altornek(1_000_000, 200_000, tohum=20261009)
    assert np.array_equal(a, b)


def test_altornek_farkli_tohumda_FARKLI_kume():
    a = sabit_altornek(1_000_000, 200_000, tohum=1)
    b = sabit_altornek(1_000_000, 200_000, tohum=2)
    assert not np.array_equal(a, b)


def test_altornek_artan_ve_tekrarsiz():
    a = sabit_altornek(10_000, 500, tohum=3)
    assert a.size == 500
    assert np.all(np.diff(a) > 0)
    assert a.min() >= 0 and a.max() < 10_000


def test_hedef_n_den_buyukse_hepsi_doner():
    a = sabit_altornek(100, 500, tohum=3)
    assert np.array_equal(a, np.arange(100))


def test_altornek_gecersiz_girdi():
    with pytest.raises(ValueError, match="hedef >= 1"):
        sabit_altornek(100, 0, tohum=1)
    with pytest.raises(ValueError, match="n >= 0"):
        sabit_altornek(-1, 10, tohum=1)
