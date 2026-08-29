"""Kademeli inceltme — arayüz basamağı merdivene yayılıyor mu (A25).

Tek basamaklı inceltmede `λ = 20` şu arayüzü üretiyor: ince parçacık
`46,6 kg`, hemen dışındaki `372 834 kg` — **oran `8 000`** — ve
şoklanan `73` tonun tamamının momentumu tek bir kaba parçacığı şok
hızına çıkarmaya `107` kat yetmiyor.

Burada kilitlenen: merdivenin **sırası** (yanlış sıra sessizce daha
kötü bir sahne üretirdi) ve mermi `h`'sinin **en ince** seviyeye
bağlanması.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from arayuz_orani import kademe_onerisi, oranlar  # noqa: E402

from dartrift.setup.refine import refine_scene_kademeli  # noqa: E402


class _Sahte:
    """Kafes kurulumunu koşmadan **doğrulama** yollarını sınamak için."""

    spacing = 7.0
    impact_point = np.array([0.0, 0.0, 82.0])
    target_radius = 82.0
    impact_direction = np.array([0.0, 0.0, -1.0])
    surface_normal = np.array([0.0, 0.0, 1.0])
    x = np.zeros((1, 3))
    m = np.ones(1)
    alpha0 = np.ones(1)
    Y0 = np.ones(1)
    is_boulder = np.zeros(1, bool)
    is_impactor = np.zeros(1, bool)


def test_TEK_kademe_reddediliyor() -> None:
    with pytest.raises(ValueError, match="en az iki kademe"):
        refine_scene_kademeli(_Sahte(), None, [(3.0, 20.0)])


def test_YARICAP_sirasi_zorunlu() -> None:
    """Dıştan içe **azalmalı**; ters sıra sessizce geçmemeli."""
    with pytest.raises(ValueError, match="DISTAN ICE azalmali"):
        refine_scene_kademeli(_Sahte(), None, [(3.0, 2.0), (12.0, 20.0)])


def test_LAM_sirasi_zorunlu() -> None:
    """İç bölge **daha ince** olmalı — `lam` dıştan içe artmalı."""
    with pytest.raises(ValueError, match="DISTAN ICE artmali"):
        refine_scene_kademeli(_Sahte(), None, [(12.0, 20.0), (3.0, 2.0)])


def test_esit_lam_de_reddediliyor() -> None:
    with pytest.raises(ValueError, match="DISTAN ICE artmali"):
        refine_scene_kademeli(_Sahte(), None, [(12.0, 5.0), (3.0, 5.0)])


# --------------------------------------------- merdivenin ARITMETIGI

def _kutleler(spacing: float, lamlar) -> np.ndarray:
    """Verilen `lam` merdiveninin parçacık kütleleri (`m ~ s³`)."""
    rho = 2700.0 / 1.7564
    return np.array([0.707 * (spacing / lam) ** 3 * rho for lam in lamlar])


def test_TEK_BASAMAK_olculen_orani_yeniden_uretiyor() -> None:
    """`λ = 20` ve kaba `λ = 1`: `8 000`."""
    o = oranlar(_kutleler(7.0, [20.0, 1.0]))
    assert o["en_dik"] == pytest.approx(8000.0, rel=1e-6)
    assert o["yargi"] == "TEHLIKELI"


def test_MERDIVEN_basamagi_OLAGAN_a_indiriyor() -> None:
    """`20 -> 10 -> 5 -> 2,5 -> 1,25 -> 1`: her basamak `8×`."""
    o = oranlar(_kutleler(7.0, [20.0, 10.0, 5.0, 2.5, 1.25, 1.0]))
    assert o["en_dik"] <= 8.0 + 1e-9
    assert o["yargi"] == "OLAGAN"
    assert len(o["oranlar"]) == 5


def test_kademe_onerisi_MERDIVEN_uzunlugunu_veriyor() -> None:
    """`8 000` -> `4` ara seviye; merdiven `20,10,5,2.5,1.25` = `4` ara."""
    assert kademe_onerisi(8000.0) == 4
    ara = [10.0, 5.0, 2.5, 1.25]
    assert len(ara) == kademe_onerisi(8000.0)


def test_EKSIK_merdiven_hala_tehlikeli() -> None:
    """Üç seviyeli yol bir ara seviye ekliyor — gerekenin dörtte biri."""
    o = oranlar(_kutleler(7.0, [20.0, 8.0, 1.0]))
    assert o["yargi"] == "TEHLIKELI"
    assert o["en_dik"] > 100.0
