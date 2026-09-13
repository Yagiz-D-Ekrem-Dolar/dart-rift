"""Protokol N raporu — Protokol G eşikleri ve Bonferroni eksen sayımı."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np

_KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_KOK / "scripts"))
_spec = importlib.util.spec_from_file_location(
    "n_ayirt_raporu", _KOK / "scripts" / "n_ayirt_raporu.py")
nr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(nr)
import ayirt_raporu as ar  # noqa: E402


def _tablo(fonk, gurultu, tohum=0, n=24):
    """İki tohumlu sentetik tablo: gözlem = fonk(θ) + gürültü."""
    rng = np.random.default_rng(tohum)
    th = np.column_stack([rng.uniform(1.0, 1.3, n), 10 ** rng.uniform(3, 7, n),
                          rng.uniform(0.05, 0.5, n)])
    kollar = []
    for _ in range(2):
        kol = []
        for t in th:
            y = fonk(t) + rng.normal(0.0, gurultu)
            kol.append({"theta": t, "d_merkez": y})
        kollar.append(kol)
    return ar.esle(kollar)


def test_esikler_PROTOKOL_G_ile_ayni_ve_metinde():
    m = (_KOK / "docs" / "truba" / "PROTOKOL-N-AYIRT.md").read_text(encoding="utf-8")
    assert (ar.F_ESIGI, ar.RHO_ESIGI, ar.P_ESIGI) == (4.0, 0.5, 0.05)
    assert "`F > 4`" in m and "`|ρ| > 0,5`" in m and "`p < 0,05`" in m
    assert nr.BONFERRONI_SINAV == 21 and "`0,05 / 21`" in m


def test_Y0a_bagli_gozlem_AYIRT_EDIYOR_ve_eksen_GORUNUR():
    tab = _tablo(lambda t: 2.0 - 0.3 * np.log10(t[1]), gurultu=0.01)
    y = nr.gozlem_yargisi(tab, "d_merkez", n_perm=2000)
    assert y["karar"] == "AYIRT EDIYOR"
    assert abs(y["eksen"]["log10_Y0"]["rho"]) > 0.9
    es = nr.eksen_sayimi({"d_merkez": y})
    assert es["gorunen"] == ["log10_Y0"] and es["karar"] == "TEK EKSEN"


def test_gurultuye_gomulu_gozlem_AYIRT_ETMIYOR():
    tab = _tablo(lambda t: 0.01 * np.log10(t[1]), gurultu=1.0)
    assert nr.gozlem_yargisi(tab, "d_merkez", n_perm=2000)["karar"] == "AYIRT ETMIYOR"


def test_sabit_gozlem_DEJENERE():
    tab = _tablo(lambda t: 1.0, gurultu=0.0)
    assert nr.gozlem_yargisi(tab, "d_merkez", n_perm=500)["karar"] == "DEJENERE"


def test_bonferroni_SINIRDA_eksen_sayilmiyor():
    """`p = 0,01` Protokol G'yi geçer ama Bonferroni eksen sayımını geçmez."""
    y = {"karar": "AYIRT EDIYOR", "eksen": {
        "blok_alpha0": {"rho": 0.6, "p": 0.01},
        "log10_Y0": {"rho": -0.9, "p": 1e-4},
        "blok_kesri": {"rho": 0.2, "p": 0.3}}}
    es = nr.eksen_sayimi({"g": y})
    assert es["gorunen"] == ["log10_Y0"]


def test_ayirt_etmeyen_gozlem_eksen_SAYDIRMAZ():
    y = {"karar": "AYIRT ETMIYOR", "eksen": {"log10_Y0": {"rho": -0.9, "p": 1e-5}}}
    assert nr.eksen_sayimi({"g": y})["karar"] == "HICBIRI"
