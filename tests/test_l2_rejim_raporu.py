"""L2 rejim tekrar sınavı — eşikler koşudan ÖNCE kilitli."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_KOK = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "l2_rejim_raporu", _KOK / "scripts" / "l2_rejim_raporu.py")
lr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lr)


def test_esikler_protokolle_AYNI():
    m = (_KOK / "docs" / "truba" / "PROTOKOL-L2-SAHA.md").read_text(encoding="utf-8")
    assert lr.REPLIKE_ORANI == 5.0 and "`≥ 5`" in m
    assert lr.BELIRSIZ_ORANI == 2.0 and "`2 – 5`" in m
    assert lr.BLOK_SIFIR_MATRIS_ESIGI == 0.05 and "`≥ 0,05`" in m


def test_L_olcumu_REPLIKE():
    """L'nin koşu sonrası sayıları (0,5 / 0,03) REPLİKE vermeli."""
    assert lr.rejim_yargisi([0.53, 0.54, 0.47], [0.02, 0.05, 0.03])["karar"] == "REPLIKE"


@pytest.mark.parametrize("dm, db, beklenen", [
    ([0.50], [0.10], "REPLIKE"),          # oran 5 tam sinir
    ([0.49], [0.10], "BELIRSIZ"),
    ([0.20], [0.10], "BELIRSIZ"),         # oran 2 tam sinir
    ([0.19], [0.10], "REPLIKE DEGIL"),
])
def test_esik_SINIRLARI(dm, db, beklenen):
    assert lr.rejim_yargisi(dm, db)["karar"] == beklenen


def test_blok_kolu_sifir_ya_da_negatif():
    assert lr.rejim_yargisi([0.3], [0.0])["karar"] == "REPLIKE"
    assert lr.rejim_yargisi([0.01], [-0.001])["karar"] == "BELIRSIZ"


def test_MEDYAN_kullaniliyor():
    assert lr.rejim_yargisi([0.5, 0.5, 5.0], [0.1, 0.1, 0.0001])["oran"] == pytest.approx(5.0)
