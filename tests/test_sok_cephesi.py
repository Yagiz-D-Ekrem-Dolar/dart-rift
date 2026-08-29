"""Şok cephesi izleyicisi — konum, kalınlık, hız.

A24'te cephe iki anlık görüntüde de `3,41 m` çıktı ve *"duruyor"*
sonucuna varıldı. İki noktadan çıkarım yapmak bu deponun tekrarlayan
hatası; araç onu ölçülebilir kıldığı için **aracın kendisi**
kilitlenmeli.

Özellikle: çarpma noktası bir kez `ehat`'ın **ters** ucundan alındı
ve cephe `160 m` çıktı (cismin antipodu). O yüzden nokta dışarıdan
veriliyor ve işaret hatası testle yakalanıyor.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from sok_cephesi import cephe, hiz  # noqa: E402
from sok_sinavi import RHO_MATRIS  # noqa: E402


def _kabuk(yaricaplar, sik):
    """Verilen yarıçaplarda, verilen sıkışmalarla parçacıklar."""
    n = len(yaricaplar)
    xr = np.zeros((n, 3))
    xr[:, 0] = yaricaplar
    return dict(rho=RHO_MATRIS * (1.0 + np.asarray(sik, float)),
                alpha0=np.full(n, 1.7564), x_referans=xr,
                carpma_noktasi=np.zeros(3), m=np.ones(n))


def test_cephe_EN_UZAK_soklanmis_parcacik() -> None:
    r = cephe(**_kabuk([1.0, 2.0, 5.0], [0.20, 0.10, 0.001]))
    assert r["cephe_m"] == pytest.approx(2.0)     # 5,0 esigin ALTINDA
    assert r["ic_kenar_m"] == pytest.approx(1.0)
    assert r["kalinlik_m"] == pytest.approx(1.0)
    assert r["n"] == 2


def test_soklanmis_YOKSA_nan_veriyor_sifir_DEGIL() -> None:
    """`0` demek *"cephe merkezde"* olurdu; yokluk `nan` ile ayrılmalı."""
    r = cephe(**_kabuk([1.0, 2.0], [0.0, 0.0]))
    assert r["n"] == 0
    assert np.isnan(r["cephe_m"]) and np.isnan(r["kalinlik_m"])
    assert r["kutle_kg"] == 0.0


def test_kutle_yalnizca_SOKLANANI_topluyor() -> None:
    k = _kabuk([1.0, 2.0, 5.0], [0.20, 0.10, 0.001])
    k["m"] = np.array([3.0, 4.0, 100.0])
    assert cephe(**k)["kutle_kg"] == pytest.approx(7.0)


def test_ISARET_hatasi_yakalaniyor() -> None:
    """Çarpma noktası ters uçtan verilirse cephe **çok** büyük çıkar.

    Bir kez öyle ölçüldü (`160 m`, cismin antipodu); test o hatanın
    sessizce geçmediğini gösteriyor.
    """
    k = _kabuk([1.0, 2.0], [0.20, 0.10])
    dogru = cephe(**k)["cephe_m"]
    k["carpma_noktasi"] = np.array([-160.0, 0.0, 0.0])
    ters = cephe(**k)["cephe_m"]
    assert ters > 50 * dogru


def test_esik_AYRIM_yapabiliyor() -> None:
    """`%1` eşiği: `λ₂ = 8` tek parçacık, `λ₂ = 20` binlerce verdi."""
    zayif = cephe(**_kabuk([1.0, 2.0], [0.005, 0.004]))
    guclu = cephe(**_kabuk([1.0, 2.0], [0.22, 0.10]))
    assert zayif["n"] == 0 and guclu["n"] == 2


def test_hiz_DURAN_cepheyi_sifir_veriyor() -> None:
    """Ölçülen: `3,41 -> 3,41 m`, `3,767e-3 s`'de. Sönüm değil, durma."""
    assert hiz(3.41, 3.41, 3.767e-3) == pytest.approx(0.0)
    assert hiz(0.0, 3.41, 1.0e-3) == pytest.approx(3410.0)


def test_hiz_bozuk_dt_REDDEDIYOR() -> None:
    with pytest.raises(ValueError, match="dt pozitif"):
        hiz(1.0, 2.0, 0.0)


def test_bozuk_konum_REDDEDILIYOR() -> None:
    k = _kabuk([1.0], [0.2])
    k["x_referans"] = np.zeros((1, 2))
    with pytest.raises(ValueError, match=r"\(N,3\)"):
        cephe(**k)
