"""D kütle duyarlılığı — eşik kütlesi formülü ve kenar durumlar."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_KOK = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("dkd", _KOK / "scripts" / "d_kutle_duyarliligi.py")
dkd = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dkd)


def _d(beta, sig, bmax, M=4.16e9):
    return {"gozlem": {"beta": beta, "sigma_beta": sig, "hedef_kutlesi": M},
            "kapsama": {"beta_max_model": bmax}}


def test_esikte_band_alt_ucu_model_maksimumuna_esit():
    r = dkd.esik(_d(3.12, 0.34, 1.85), 1800.0)
    beta_M = 3.12 * r["kutle_orani"]
    sig_M = r["sigma_rel"] * beta_M
    assert beta_M - 2 * sig_M == pytest.approx(1.85)
    assert r["karar"] == "BANDA GIRMEK ICIN KUTLE AZALMALI"
    assert r["rho_esik"] == pytest.approx(1800 * r["kutle_orani"])
    assert r["kutle_orani"] < 1


def test_zaten_banddaysa_ve_tanimsiz():
    assert dkd.esik(_d(1.5, 0.1, 1.85), 1800.0)["karar"] == "ZATEN BANDA"
    assert dkd.esik(_d(3.0, 1.6, 1.85), 1800.0)["karar"] == "TANIMSIZ"


def test_kaydedilmis_kesif_jsonlarinda_calisiyor():
    import json

    for ad in ("S_DART_kesif_k72.json", "S_DART_kesif_o72.json"):
        d = json.loads((_KOK / "docs" / "olcumler" / "D_kesif" / ad).read_text(encoding="utf-8"))
        r = dkd.esik(d, 1800.0)
        assert r["karar"] == "BANDA GIRMEK ICIN KUTLE AZALMALI" and 0.5 < r["kutle_orani"] < 1
