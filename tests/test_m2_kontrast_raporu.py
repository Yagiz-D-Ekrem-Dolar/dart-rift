"""Protokol M2 — kontrast kararlılığı kilitli kuralları."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest

_KOK = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("m2r", _KOK / "scripts" / "m2_kontrast_raporu.py")
m2 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m2)


def _veri(ofset, duyarlilik, gurultu=0.002):
    """Mutlak değer çözünürlükle kayar (ofset), kontrast sabit (duyarlilik)."""
    veri = {}
    for m, o in zip(m2.MERDIVENLER, ofset, strict=True):
        for ad in m2.TETALAR:
            d = {}
            for g in m2.GOZLEMLER_M2:
                baz = o + (duyarlilik[m][g] if ad == "Y" else 0.0)
                if g in m2.LOG_ORAN:
                    baz = 30.0 * np.exp(baz)
                d[g] = [baz + gurultu, baz - gurultu]
            veri[(ad, m)] = d
    return veri


def test_mutlak_kayarken_KONTRAST_sabitse_KARARLI_ve_H_Y_DAYANIKLI():
    sabit = {m: {g: -0.24 for g in m2.GOZLEMLER_M2} for m in m2.MERDIVENLER}
    out = m2.rapor(_veri((0.74, 0.64, 0.46), sabit))
    assert out["yargilar"]["Y:beta_eksi_1"]["karar"] == "KARARLI"
    assert out["yargilar"]["Y:V_krater"]["karar"] == "KARARLI"
    assert out["H_Y"] == "DAYANIKLI"
    assert out["yargilar"]["a:beta_eksi_1"]["karar"] == "SINYAL YOK"
    assert out["H_a"] == "DAYANIKSIZ"


def test_kontrast_orta_ince_arasi_yari_yariya_degisirse_KARARSIZ():
    d = {"kaba": {g: -0.10 for g in m2.GOZLEMLER_M2},
         "orta": {g: -0.10 for g in m2.GOZLEMLER_M2},
         "ince": {g: -0.20 for g in m2.GOZLEMLER_M2}}
    out = m2.rapor(_veri((0.7, 0.6, 0.5), d))
    assert out["yargilar"]["Y:beta_eksi_1"]["karar"] == "KARARSIZ"
    assert out["H_Y"] == "DAYANIKSIZ"


def test_isaret_degisimi_KARARSIZ():
    y = m2.kontrast_yargisi({"kaba": (0.05, 0.001), "orta": (-0.05, 0.001),
                             "ince": (-0.05, 0.001)})
    assert y["karar"] == "KARARSIZ" and not y["ayni_isaret"]


def test_log_oran_ve_sigma_yayilimi():
    c, s = m2.kontrast("V_krater", [10.0, 10.0], [20.0, 20.0])
    assert c == pytest.approx(np.log(2.0)) and s == 0.0
    c, s = m2.kontrast("beta_eksi_1", [0.5, 0.7], [0.3, 0.3])
    assert c == pytest.approx(-0.3) and s == pytest.approx(0.1)


def test_eksik_seviye_OKUNMAZ():
    assert m2.kontrast_yargisi({"kaba": (1.0, 0.1), "orta": (1.0, 0.1)})["karar"] == "OKUNMAZ"


def test_esikler_belgede_ve_tasarim_onselde():
    m = (_KOK / "docs" / "truba" / "PROTOKOL-M2-KONTRAST.md").read_text(encoding="utf-8")
    assert (m2.BAGIL_TOLERANS, m2.SIGMA_KATI) == (0.25, 2.0)
    for p in ("`|c_ince − c_orta| ≤ max(0,25 |c_ince|, 2 σ_c)`",
              "`|c_ince| ≤ 2 σ_c`", "en az ikisinde"):
        assert p in m, p
    from dartrift.inference.design import DART_UZAYI_S3 as U

    for th in m2.TETALAR.values():
        assert all(lo <= v <= hi for v, lo, hi in zip(th, U.lo, U.hi, strict=True))
