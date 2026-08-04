"""FAZ 4 ölçümlerinin **yargı mantığı** — her dal sınanıyor (GPU gerekmez).

Bu modüllerin sayıları ADR-0041'i besledi. Yargı mantığı koşunun içine gömülü
kaldığı sürece **hiçbir testten geçmiyordu**: GPU'suz makinede koşu atlanıyor,
GPU'da ise yalnızca üretilen tek sonuç görülüyordu.

ADR-0040'ın kuralı burada da geçerli: bir yargının `inconclusive` dalı varsa,
o dalın **düşebildiği** gösterilmelidir.
"""
from __future__ import annotations

import pytest

from dartrift.validation.resolution_scaling import judge as res_judge
from dartrift.validation.shock_interface import judge as shock_judge

# --- E3 (KAYIT-026, is 1450837) GERCEK olculen degerler, 8:1 n=64
KABA = {"r_measured": 0.23874, "energy_injected": 1.0, "total_mass": 1.000000}
IKI = {"r_measured": 0.24337, "energy_injected": 1.0, "total_mass": 1.000134}
INCE = {"r_measured": 0.24404, "energy_injected": 1.0, "total_mass": 1.000000}


def _shock(a=None, b=None, c=None):
    return shock_judge(a or KABA, b or IKI, c or INCE, 2, 0.15, 0.03125, 0.0288)


def test_shock_gercek_olcum_zararsiz() -> None:
    """KAYIT-026'nın sonucu yeniden üretiliyor: taşma %0,000."""
    r = _shock()
    assert r["verdict"] == "interface_harmless"
    assert r["two_zone_within_bracket"] is True
    assert r["excess_rel"] == pytest.approx(0.0, abs=1e-12)
    assert r["arms_distinguishable"] is True
    assert r["energy_injection_matches"] is True
    assert r["mass_effect_negligible"] is True


def test_shock_aralik_disi_BEDELLI() -> None:
    r = _shock(b=dict(IKI, r_measured=0.30))
    assert r["verdict"] == "interface_costs"
    assert r["two_zone_within_bracket"] is False
    assert r["excess_rel"] > 0.2


def test_shock_kollar_ayirt_etmezse_INCONCLUSIVE() -> None:
    """BOŞLUK KONTROLÜ: `a == c` iken `b`'nin "arada" olması boş bir doğrudur."""
    r = _shock(a=dict(KABA, r_measured=0.24404))
    assert r["arms_distinguishable"] is False
    assert r["verdict"] == "inconclusive"


def test_shock_enerji_farkliysa_INCONCLUSIVE() -> None:
    """Farklı enerji = **farklı problem** (ADR-0011'in yakaladığı hata)."""
    r = _shock(b=dict(IKI, energy_injected=1.5))
    assert r["energy_injection_matches"] is False
    assert r["verdict"] == "inconclusive"


def test_shock_kutle_sapmasi_buyukse_INCONCLUSIVE() -> None:
    r = _shock(b=dict(IKI, total_mass=1.5))
    assert r["mass_effect_negligible"] is False
    assert r["verdict"] == "inconclusive"


# --- KAYIT-023 (is 1450829) GERCEK olculen platolar
STD = {"plateau": 0.24008, "settled": True}
KABA_H = {"plateau": 0.25650, "settled": True}
INCE_H = {"plateau": 0.24303, "settled": True}


def test_res_gercek_olcum_h_belirliyor() -> None:
    """KAYIT-023'ün sonucu yeniden üretiliyor."""
    r = res_judge(STD, KABA_H, INCE_H, 0.0625, 0.03125)
    assert r["verdict"] == "h_sets_resolution"
    assert r["gap_coarse_vs_limit"] == pytest.approx(0.0684, abs=5e-4)
    assert r["gap_fine_vs_limit"] == pytest.approx(0.0123, abs=5e-4)
    assert r["plateau_shifts_with_h"] == pytest.approx(0.0525, abs=5e-4)
    assert r["finer_h_is_closer"] is True


def test_res_oturmamis_kol_INCONCLUSIVE() -> None:
    """BOŞLUK KONTROLÜ: oturmamış bir koldan plato okunmaz."""
    for bozuk in ("standard", "coarse", "fine"):
        a = dict(STD, settled=(bozuk != "standard"))
        b = dict(KABA_H, settled=(bozuk != "coarse"))
        c = dict(INCE_H, settled=(bozuk != "fine"))
        r = res_judge(a, b, c, 0.0625, 0.03125)
        assert r["all_settled"] is False, bozuk
        assert r["verdict"] == "inconclusive", bozuk


def test_res_platolar_ayrismazsa_dx_de_katki() -> None:
    """Sabit-`h` platoları `h → 0` limitiyle çakışırsa `h` tek belirleyici değil."""
    r = res_judge(STD, {"plateau": 0.24010, "settled": True},
                  {"plateau": 0.24009, "settled": True}, 0.0625, 0.03125)
    assert r["verdict"] == "dx_also_contributes"
    assert r["plateau_shifts_with_h"] < 0.01
