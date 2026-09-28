"""PROTOKOL-A105 raporu — sentetik durumlarla yargı dalları."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest

_SC = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(_SC))
_spec = importlib.util.spec_from_file_location("a105_cekme_raporu",
                                               _SC / "a105_cekme_raporu.py")
RAP = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(RAP)


def _yaz(kok: Path, ad: str, beta: float, b3: float = 2.95, gecerli=True,
         t_son=300.0):
    d = kok / f"{ad}.durumlar"
    d.mkdir(parents=True, exist_ok=True)
    ft = {"impuls_egrisi": [[0.1, 0.0, 1.5, 0.0], [3.0, 0.0, b3, 0.0],
                            [t_son, 0.0, beta, 0.0]]}
    np.savez(d / "nokta_0000_x.npz", fizik_tani=json.dumps(ft),
             gecerlilik=json.dumps({"gecerli": gecerli}))


def _hepsi(kok: Path, k0=3.6864, o0=3.9784, kT=3.10, oT=3.14):
    for ad, b in zip(RAP.KOLLAR.values(), (k0, o0, kT, oT), strict=True):
        _yaz(kok, ad, b)


def test_COGUNU_TASIYOR_ve_DUYARLI(tmp_path):
    _hepsi(tmp_path)   # g0 = 0,0734; gT = 0,0127 -> oran 0,17
    y = RAP.yargila(RAP.oku(tmp_path))
    assert y["bulunan"] == 4
    assert y["C1_g0"] == pytest.approx((3.9784 - 3.6864) / 3.9784)
    assert y["C1"] == "CEKMESIZ AYRILMA COZUNURLUK FARKININ COGUNU TASIYOR"
    assert y["C3"] == "BETA CEKME DAYANIMINA DUYARLI"
    assert y["genel"] == y["C1"]
    assert y["gec_artis"]["kaba0"] == pytest.approx(3.6864 - 2.95)


def test_KISMEN_ve_TASIMIYOR(tmp_path):
    _hepsi(tmp_path, kT=3.60, oT=3.80)       # gT = 0,0526 -> oran 0,72
    y = RAP.yargila(RAP.oku(tmp_path))
    assert y["C1"] == "CEKMESIZ AYRILMA COZUNURLUK FARKININ BIR KISMINI TASIYOR"
    assert y["C3"] == "BETA CEKME DAYANIMINA DUYARSIZ"
    _hepsi(tmp_path, kT=3.50, oT=3.85)       # gT = 0,0909 -> oran 1,24
    y = RAP.yargila(RAP.oku(tmp_path))
    assert y["C1"] == "CEKMESIZ AYRILMA COZUNURLUK FARKINI TASIMIYOR"
    assert y["C3"] == "BETA CEKME DAYANIMINA DUYARLI"


def test_ters_isaret_de_oran_mutlak(tmp_path):
    _hepsi(tmp_path, kT=3.20, oT=3.16)       # gT < 0, |oran| = 0,17
    y = RAP.yargila(RAP.oku(tmp_path))
    assert y["C1_oran"] < 0
    assert y["C1"] == "CEKMESIZ AYRILMA COZUNURLUK FARKININ COGUNU TASIYOR"


def test_EKSIK_GECERSIZ_KISA(tmp_path):
    _hepsi(tmp_path)
    for p in (tmp_path / "A105_o_T.durumlar").iterdir():
        p.unlink()
    y = RAP.yargila(RAP.oku(tmp_path))
    assert y["bulunan"] == 3 and y["C1"] == "OKUNMAZ"
    assert y["C3"] != "OKUNMAZ"          # C3 yalniz kaba kollari ister
    _yaz(tmp_path, "A105_k_T", 3.1, gecerli=False)
    y = RAP.yargila(RAP.oku(tmp_path))
    assert y["eksik"]["kabaT"] == "gecersiz" and y["C3"] == "OKUNMAZ"
    _yaz(tmp_path, "A105_k_T", 3.1, t_son=100.0)
    y = RAP.yargila(RAP.oku(tmp_path))
    assert y["eksik"]["kabaT"] == "300 s'ye ulasmamis"


def test_CLI_json_uzerine_yazmaz(tmp_path):
    _hepsi(tmp_path / "k")
    out = tmp_path / "S.json"
    assert RAP.main(["--kok", str(tmp_path / "k"), "--json", str(out)]) == 0
    assert json.loads(out.read_text(encoding="utf-8"))["bulunan"] == 4
    with pytest.raises(SystemExit):
        RAP.main(["--kok", str(tmp_path / "k"), "--json", str(out)])
