"""`boulder_boundary` — ADR-0043 #4'ün yargıcı.

Bu testlerin **asıl** işi dejenere durumu sınamak: ince bölgede hiç
blok yokken ölçüm `%0` değil **`belirsiz`** demeli. İlk sürümüm `%0,000`
yazdı ve geçmiş gibi okundu.
"""
from __future__ import annotations

import numpy as np
import pytest

from dartrift.validation.boulder_boundary import (F_BLOK_SAPMA_ESIGI,
                                                  blok_sapmasi, judge)


def _kol(f_kes, f_kul):
    """`f_kes` / `f_kul` kütle kesirlerini **tam olarak** tutturan kol.

    İlk sürüm `n=1000` parçacığı sayarak kesir kuruyordu ve
    `int(round(0.3297 * 1000)) = 330` yüzünden `%9,9`'u `%10,0`'a
    yuvarlıyordu — eşik kenarı testi bu yüzden düşmüştü. Kütleyi
    doğrudan vermek yuvarlamayı ortadan kaldırır.
    """
    if not 0.0 <= f_kes <= f_kul <= 1.0:
        raise AssertionError(f"fikstür geçersiz: {f_kes} ≤ {f_kul} ≤ 1 olmalı")
    m = np.array([f_kes, f_kul - f_kes, 1.0 - f_kul])
    kb = np.array([True, False, False])
    ub = np.array([True, True, False])
    # Sifir kutle yasak; olcuyu bozmadan minik bir taban eklenir.
    m = np.where(m <= 0.0, 1e-12, m)
    return blok_sapmasi(m / m.sum(), kb, ub)


# ------------------------------------------------------- DEJENERE durum

def test_blok_YOKKEN_belirsiz_der_sifir_DEMEZ():
    """Ölçülemeyen şeye `0` demek `nan` demekten kötüdür."""
    m = np.ones(50)
    yok = np.zeros(50, bool)
    d = blok_sapmasi(m, yok, yok)
    assert d["durum"] == "belirsiz"
    assert d["blok_var"] is False
    assert np.isnan(d["f_blok_sapma"])          # <-- 0.0 DEGIL
    assert "blok yok" in d["neden"]


def test_judge_hepsi_dejenereyse_gecti_DEGIL_belirsiz():
    m, yok = np.ones(20), np.zeros(20, bool)
    d = judge([blok_sapmasi(m, yok, yok) for _ in range(3)])
    assert d["durum"] == "belirsiz"
    assert d["gecti"] is None                   # <-- False DEGIL
    assert d["n_olculen"] == 0
    assert "kayıt bulunamadı" in d["neden"]


def test_judge_dejenere_kollari_ATAR_olculeni_kullanir():
    m, yok = np.ones(1000), np.zeros(1000, bool)
    kollar = [blok_sapmasi(m, yok, yok), _kol(0.30, 0.32)]
    d = judge(kollar)
    assert d["durum"] == "olculdu"
    assert d["n_kol"] == 2 and d["n_olculen"] == 1 and d["n_dejenere"] == 1


# ----------------------------------------------------------- olcum dogru

def test_sapma_dogru_hesaplaniyor():
    d = _kol(0.30, 0.33)
    assert d["f_blok_kesin"] == pytest.approx(0.30, abs=1e-12)
    assert d["f_blok_kullanilan"] == pytest.approx(0.33, abs=1e-12)
    assert d["f_blok_sapma"] == pytest.approx(0.03 / 0.30, rel=1e-9)


def test_kusursuz_atamada_sapma_sifir():
    m = np.ones(100)
    b = np.zeros(100, bool); b[:30] = True
    d = blok_sapmasi(m, b, b)
    assert d["durum"] == "olculdu"               # blok VAR
    assert d["f_blok_sapma"] == 0.0
    assert d["yanlis_oran"] == 0.0


def test_kutle_agirlikli_sayim_DEGIL_parcacik_sayisi():
    """Ağır bir blok parçacığı, çok sayıda hafif matris parçacığından
    daha fazla ağırlık taşımalı."""
    m = np.array([100.0, 1.0, 1.0, 1.0])
    kb = np.array([True, False, False, False])
    d = blok_sapmasi(m, kb, kb)
    assert d["f_blok_kesin"] == pytest.approx(100.0 / 103.0)


@pytest.mark.parametrize("sapma,bekle", [(0.05, True), (0.099, True),
                                         (0.10, False), (0.30, False)])
def test_esik_kenarlari(sapma, bekle):
    d = judge([_kol(0.30, 0.30 * (1.0 + sapma))])
    assert d["gecti"] is bekle
    assert d["esik"] == F_BLOK_SAPMA_ESIGI


def test_yanlis_oran_ve_kutle_orani_ayri():
    """Sayıca az ama ağır parçacıklar yanlışsa ikisi ayrışmalı."""
    m = np.array([1000.0, 1.0, 1.0, 1.0, 1.0])
    kb = np.array([True, False, False, False, False])
    ub = np.array([False, False, False, False, False])
    d = blok_sapmasi(m, kb, ub)
    assert d["yanlis_oran"] == pytest.approx(1 / 5)
    assert d["yanlis_kutle_oran"] == pytest.approx(1000.0 / 1004.0)


@pytest.mark.parametrize("kw,mesaj", [
    (dict(m=np.ones(3)), "uzunluklar uyuşmuyor"),
    (dict(m=np.zeros(0), kesin_blok=np.zeros(0, bool),
          kullanilan_blok=np.zeros(0, bool)), "parçacık yok"),
    (dict(m=np.array([1.0, -1.0]), kesin_blok=np.zeros(2, bool),
          kullanilan_blok=np.zeros(2, bool)), "pozitif"),
])
def test_gecersiz_girdiler(kw, mesaj):
    g = dict(m=np.ones(2), kesin_blok=np.zeros(2, bool),
             kullanilan_blok=np.zeros(2, bool))
    g.update(kw)
    with pytest.raises(ValueError, match=mesaj):
        blok_sapmasi(**g)
