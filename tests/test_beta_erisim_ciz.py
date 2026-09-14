"""β erişilebilirlik figürü — JSON okuma ve çizim."""
from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path

import pytest

_KOK = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("bec", _KOK / "scripts" / "beta_erisim_ciz.py")
bec = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bec)


def _dart(tmin, bmax, beta=3.12, s=0.34, karar="ONSEL DISI (YUKARI)"):
    return {"kapsama": {"tahmin_min": math.log10(tmin - 1), "beta_max_model": bmax,
                        "karar": karar}, "gozlem": {"beta": beta, "sigma_beta": s}}


def test_satirlar_havuz_ve_varyant(tmp_path):
    (tmp_path / "S_DART_kesif_k72.json").write_text(json.dumps(_dart(1.246, 1.853)), "utf-8")
    (tmp_path / "S_U.json").write_text(json.dumps({"satirlar": {
        "U0:kaba": {"beta_eksi_1_sim": 0.95, "beta_eksi_1_gozlem": 2.12, "sigma_beta": 0.34,
                    "karar": "ALTINDA"},
        "U9:kaba": {"karar": "OKUNMAZ"}}}), "utf-8")
    s = bec.satirlar(tmp_path)
    assert [r["tur"] for r in s] == ["havuz", "varyant"]
    assert s[0]["b_min"] == pytest.approx(1.246) and s[0]["b_max"] == 1.853
    assert s[1]["b_sim"] == pytest.approx(1.95) and s[1]["gozlem"] == pytest.approx(3.12)


def test_ciz_png_yaziyor(tmp_path):
    (tmp_path / "S_DART_Qo.json").write_text(json.dumps(_dart(1.3, 1.9)), "utf-8")
    out = tmp_path / "sekil" / "b.png"
    bec.ciz(bec.satirlar(tmp_path), out)
    assert out.exists() and out.stat().st_size > 1000


def test_json_yoksa_bos():
    assert bec.satirlar(Path("/yok/boyle/bir/dizin")) == []
