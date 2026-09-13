"""Protokol M raporu — eşikler ve tasarım koşudan ÖNCE kilitli."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

_KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_KOK / "scripts"))
_spec = importlib.util.spec_from_file_location(
    "m_yakinsama_raporu", _KOK / "scripts" / "m_yakinsama_raporu.py")
mr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mr)


def test_esikler_protokolle_AYNI():
    m = (_KOK / "docs" / "truba" / "PROTOKOL-M-YAKINSAMA.md").read_text(encoding="utf-8")
    for g, tol in mr.TOLERANS.items():
        assert f"| `{g}` | `{tol:.2f}`".replace(".", ",") in m, g
    assert mr.YAKINSIYOR_EN_AZ == 4 and "`≥ 4`" in m
    assert mr.YAKINSAMIYOR_EN_COK == 1 and "`≤ 1`" in m


def test_tasarim_ONSEL_icinde_ve_alti_teta():
    from dartrift.inference.design import DART_UZAYI_S3 as U

    assert len(mr.TETALAR) == 6
    lo, hi = np.asarray(U.lo), np.asarray(U.hi)
    for th in mr.TETALAR:
        assert np.all(np.asarray(th) >= lo) and np.all(np.asarray(th) <= hi)


def test_tasarim_dosyalari(tmp_path):
    yollar = mr.tasarim_yaz(tmp_path)
    assert len(yollar) == 6 and all(p.exists() for p in yollar)


def test_seviye_ozeti_iki_tohum():
    ort, s = mr.seviye_ozeti([1.0, 1.2])
    assert ort == pytest.approx(1.1) and s == pytest.approx(0.1)
    assert np.isnan(mr.seviye_ozeti([1.0])[0])


def test_yakinsayan_teta_YAKINSAMIS():
    x = [5.0 + 0.4 * h ** 2 for h in (4.0, 2.0, 1.0)]    # hata_ince 0,4 / 5,4 = %7,4
    y = mr.teta_yargisi((x[0], 0.001), (x[1], 0.001), (x[2], 0.001), 0.10)
    assert y["karar"] == "YAKINSAMIS" and y["durum"] == "UYGUN"


def test_toleransi_asan_teta_YAKINSAMAMIS():
    x = [5.0 + 0.8 * h ** 2 for h in (4.0, 2.0, 1.0)]    # hata_ince 0,8 / 5,8 = %13,8
    y = mr.teta_yargisi((x[0], 0.001), (x[1], 0.001), (x[2], 0.001), 0.10)
    assert y["karar"] == "YAKINSAMAMIS"


def test_eksik_seviye_OKUNMAZ():
    y = mr.teta_yargisi((1.0, 0.1), (float("nan"), float("nan")), (1.0, 0.1), 0.1)
    assert y["karar"] == "OKUNMAZ"


@pytest.mark.parametrize("n_yak, beklenen", [(6, "YAKINSIYOR"), (4, "YAKINSIYOR"),
                                              (3, "KISMI"), (2, "KISMI"),
                                              (1, "YAKINSAMIYOR"), (0, "YAKINSAMIYOR")])
def test_gozlem_yargisi_SINIRLARI(n_yak, beklenen):
    s = [{"karar": "YAKINSAMIS"}] * n_yak + [{"karar": "YAKINSAMAMIS"}] * (6 - n_yak)
    assert mr.gozlem_yargisi(s)["karar"] == beklenen
