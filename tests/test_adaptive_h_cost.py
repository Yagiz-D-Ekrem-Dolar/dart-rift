"""A′ komşu arama israfı ölçümünün denetimi.

Bu sayı ADR-0041'in A′ kefesini belirledi; aracın kendisi bozuksa karar
çürür.
"""
from __future__ import annotations

import numpy as np
import pytest

from dartrift.validation.adaptive_h_cost import measure_neighbour_waste

GEO = dict(r_outer=70.0, r_inner=25.0, spacing=8.0, h_over_spacing=1.3)


def test_bosluk_kontrolu_tek_h_israf_TAM_BIR() -> None:
    """`λ = 1`: tek `h` var, israf **tam 1,0** olmalı."""
    r = measure_neighbour_waste(lam=1.0, **GEO)
    assert r["is_identity_case"] is True
    assert r["waste_fine"] == pytest.approx(1.0, abs=1e-12)
    assert r["waste_coarse"] == pytest.approx(1.0, abs=1e-12)
    assert r["waste_overall"] == pytest.approx(1.0, abs=1e-12)


def test_israf_KUP_yasasini_izliyor() -> None:
    """İnce bölgede israf `(h_maks/h_i)³` olmalı — ölçüldü: 7,58 vs 8,00."""
    r = measure_neighbour_waste(lam=2.0, **GEO)
    assert r["h_ratio"] == pytest.approx(2.0)
    assert r["expected_fine"] == pytest.approx(8.0)
    # Olculen beklenene YAKIN ama esit degil (arayuz yakininda karisik
    # komsuluk); %10 icinde olmali.
    assert abs(r["waste_fine"] - r["expected_fine"]) / r["expected_fine"] < 0.10


def test_kaba_bolgede_israf_YOK() -> None:
    """Küresel destek zaten kaba parçacıkların desteği — israf `1,0`."""
    for lam in (1.26, 1.59, 2.0):
        r = measure_neighbour_waste(lam=lam, **GEO)
        assert r["waste_coarse"] == pytest.approx(1.0, abs=1e-12), lam


def test_net_maliyet_orani_16de_BIRI_asiyor() -> None:
    """Asıl bulgu: tasarruf doğrusal, israf küpsel → 16:1'de A′ **kaybettiriyor**.

    Ölçülen NET (israf/tasarruf): 2:1 → 0,694 · 4:1 → 0,650 ·
    8:1 → 0,857 · 16:1 → **1,065**.
    """
    net = {}
    for lam in (1.26, 2.0, 2.52):
        r = measure_neighbour_waste(lam=lam, **GEO)
        net[lam] = r["net_cost_vs_all_fine"]
        assert r["particle_saving"] > 1.0
    assert net[1.26] < 0.8
    assert net[2.52] > 1.0, net           # 16:1'de PAHALI
    assert net[2.52] > net[1.26]          # kotulesme MONOTON
    # Ve hicbiri "degdi" (net < 0.5) esigini gecemiyor.
    for lam in (1.26, 2.0, 2.52):
        assert measure_neighbour_waste(lam=lam, **GEO)["single_grid_worthwhile"] is False


def test_gecersiz_girdi_reddediliyor() -> None:
    with pytest.raises(ValueError, match="lam >= 1"):
        measure_neighbour_waste(lam=0.5, **GEO)
    with pytest.raises(ValueError, match="iç bölge çok küçük"):
        measure_neighbour_waste(lam=2.0, r_outer=30.0, r_inner=25.0,
                                spacing=8.0, h_over_spacing=1.3)


def test_parcacik_tasarrufu_gercek() -> None:
    """KALİBRASYON: A′ **gerçekten** daha az parçacık kullanıyor mu?

    Kullanmıyorsa israf ölçümünün karşılaştırdığı bir şey yok demektir.
    """
    r = measure_neighbour_waste(lam=2.0, **GEO)
    assert r["n_all_fine_equivalent"] > 5.0 * r["n_total"]
    assert r["particle_saving"] == pytest.approx(
        r["n_all_fine_equivalent"] / r["n_total"])
