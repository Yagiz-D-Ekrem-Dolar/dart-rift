"""PROTOKOL-A98K raporu — sentetik sonuçlarla yargı dalları (fizik yok)."""
from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path

import pytest

_YOL = Path(__file__).resolve().parents[1] / "scripts" / "a98k_raporu.py"
_spec = importlib.util.spec_from_file_location("a98k_raporu", _YOL)
RAP = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(RAP)

AV = {"av1": [1.0, 2.0], "av01": [0.1, 0.2], "av0": [0.0, 0.0],
      "av01L": [0.1, 0.2]}


def _yaz(kok: Path, Q: dict, *, av_payi=0.8, nn=(0.9, 0.0), atla=(),
         momentum=0.0, sonlu=True):
    """`Q[kol] = (q_s1, q_s0p5, q_s0p25)` ile 12 kolu yaz."""
    kok.mkdir(parents=True, exist_ok=True)
    for ad, s, kol in RAP.KOLLAR:
        if ad in atla:
            continue
        i = [e for e, _ in RAP.ARALIKLAR].index(ad.split("_")[1][1:])
        r = {"s": s, "av": AV[kol], "sureklilik": "trL" if kol == "av01L" else "sph",
             "sonlu": sonlu, "momentum_bagil_sapma": momentum,
             "P_up_v0.1": Q[kol][i], "av_payi": av_payi,
             "saglik": {"nn_min": nn[0], "kesir_nn_lt_0p5": nn[1]}}
        (kok / f"{ad}.json").write_text(json.dumps(r), encoding="utf-8")


def _Q(av1=(1.0, 1.5, 1.75), av01=(2.0, 2.02, 2.03), av0=(2.1, 2.1, 2.1),
       av01L=(2.0, 2.01, 2.02)):
    return {"av1": av1, "av01": av01, "av0": av0, "av01L": av01L}


def test_ANA_SENARYO_ana_sebep_birinci_mertebe(tmp_path):
    _yaz(tmp_path, _Q())
    y = RAP.yargila(RAP.oku(tmp_path))
    assert y["bulunan"] == y["beklenen"] == 12
    assert y["K1"] == "VARSAYILAN AV'DE COZUNURLUK BAGIMLILIGI VAR"
    assert y["K2"] == "AV KABADA BASKIN"
    assert y["K3"].endswith("BUYUK OLCUDE KALDIRIYOR")
    assert y["K4_p"] == pytest.approx(1.0)
    assert y["K4"].startswith("BIRINCI MERTEBE (")
    assert y["K5"] == "AV 0,1'DE IC ICE GECME YOK"
    assert y["K6"] == "A101 COZUNURLUK FARKINI BUYUTMUYOR"
    assert y["genel"] == y["K3"]


def test_KISMEN_ve_KALDIRMIYOR(tmp_path):
    _yaz(tmp_path / "a", _Q(av01=(1.5, 1.7, 1.9)))    # D_01 = 0,21 ; D_1 = 0,43
    assert RAP.yargila(RAP.oku(tmp_path / "a"))["K3"].endswith("KISMEN KALDIRIYOR")
    _yaz(tmp_path / "b", _Q(av01=(1.0, 1.5, 2.0)))    # D_01 = 0,5 > D_1
    assert RAP.yargila(RAP.oku(tmp_path / "b"))["K3"].endswith("KALDIRMIYOR")


def test_MONOTON_DEGILSE_K1_uretilmedi(tmp_path):
    _yaz(tmp_path, _Q(av1=(1.0, 2.0, 1.5)))
    y = RAP.yargila(RAP.oku(tmp_path))
    assert y["K1"].endswith("URETILMEDI")
    assert math.isnan(y["K4_p"]) and y["K4"] == "OKUNMAZ"


def test_EKSIK_KOL_sayiliyor_ve_ilgili_yargi_OKUNMAZ(tmp_path):
    _yaz(tmp_path, _Q(), atla=("K_s0p25_av01",))
    y = RAP.yargila(RAP.oku(tmp_path))
    assert y["bulunan"] == 11
    assert y["eksik"] == {"K_s0p25_av01": "dosya yok"}
    assert y["K3"] == "OKUNMAZ" and y["K5"] == "OKUNMAZ"
    assert y["K1"] != "OKUNMAZ"


def test_GECERSIZ_kol_eksik_sayilir(tmp_path):
    _yaz(tmp_path / "m", _Q(), momentum=1e-3)
    assert RAP.yargila(RAP.oku(tmp_path / "m"))["bulunan"] == 0
    _yaz(tmp_path / "n", _Q(), sonlu=False)
    assert RAP.yargila(RAP.oku(tmp_path / "n"))["bulunan"] == 0


def test_YANLIS_AV_ya_da_SUREKLILIK_reddedilir(tmp_path):
    _yaz(tmp_path, _Q())
    yol = tmp_path / "K_s1_av01L.json"
    r = json.loads(yol.read_text(encoding="utf-8"))
    r["sureklilik"] = "sph"
    yol.write_text(json.dumps(r), encoding="utf-8")
    y = RAP.yargila(RAP.oku(tmp_path))
    assert "K_s1_av01L" in y["eksik"] and y["K6"] == "OKUNMAZ"


def test_IC_ICE_GECME_ve_A101_BUYUTUYOR(tmp_path):
    _yaz(tmp_path, _Q(av01L=(1.8, 2.0, 2.1)), nn=(0.2, 0.05))
    y = RAP.yargila(RAP.oku(tmp_path))
    assert y["K5"] == "AV 0,1'DE IC ICE GECME VAR"
    assert y["K6"] == "A101 COZUNURLUK FARKINI BUYUTUYOR"


def test_AV_IKINCIL(tmp_path):
    _yaz(tmp_path, _Q(), av_payi=0.3)
    assert RAP.yargila(RAP.oku(tmp_path))["K2"] == "AV KABADA IKINCIL"


def test_CLI_json_uzerine_yazmaz(tmp_path):
    _yaz(tmp_path / "k", _Q())
    out = tmp_path / "S.json"
    assert RAP.main(["--kok", str(tmp_path / "k"), "--json", str(out)]) == 0
    assert json.loads(out.read_text(encoding="utf-8"))["bulunan"] == 12
    with pytest.raises(SystemExit):
        RAP.main(["--kok", str(tmp_path / "k"), "--json", str(out)])
