"""PROTOKOL-A104 raporu — sentetik durumlarla yargı dalları."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest

_SC = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(_SC))
_spec = importlib.util.spec_from_file_location(
    "a104_keskin_cekirdek_raporu", _SC / "a104_keskin_cekirdek_raporu.py")
RAP = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(RAP)


def _yaz(kok: Path, ad: str, beta: float, gecerli=True, t_son=300.0):
    d = kok / f"{ad}.durumlar"
    d.mkdir(parents=True, exist_ok=True)
    ft = {"impuls_egrisi": [[0.1, 0.0, 1.5, 0.0], [t_son, 0.0, beta, 0.0]]}
    np.savez(d / "nokta_0000_x.npz", fizik_tani=json.dumps(ft),
             gecerlilik=json.dumps({"gecerli": gecerli}))


def _hepsi(kok: Path, bk=3.6864, bo=3.9784, b15=3.83, bo15=4.01):
    for (ad, _), b in zip(RAP.KOLLAR.values(), (bk, bo, b15, bo15), strict=True):
        _yaz(kok, ad, b)


def test_h_YE_BAGLI_ve_YAKINSAMA_BASLIYOR(tmp_path):
    _hepsi(tmp_path)   # k15 dogrusal aradegere yakin; egim 0,584 -> 0,253
    y = RAP.yargila(RAP.oku(tmp_path))
    assert y["bulunan"] == 4
    assert y["H1_beta_dogrusal"] == pytest.approx(3.6864 + 0.5 * 0.292)
    assert y["H1"] == "SONUC ONCELIKLE h'YE BAGLI"
    assert y["H2"] == "YAKINSAMA BASLIYOR"
    assert y["genel"] == y["H1"]


def test_N_YE_BAGLI_ve_YAKINSAMA_YOK(tmp_path):
    _hepsi(tmp_path, b15=3.70, bo15=4.10)   # egim 0,584 -> 0,976
    y = RAP.yargila(RAP.oku(tmp_path))
    assert y["H1"] == "SONUC ONCELIKLE PARCACIK SAYISINA BAGLI"
    assert y["H2"] == "YAKINSAMA YOK"


def test_KARISIK_ve_YAVAS(tmp_path):
    _hepsi(tmp_path, b15=3.76, bo15=4.035)  # egim 0,584 -> 0,454
    y = RAP.yargila(RAP.oku(tmp_path))
    assert y["H1"] == "KARISIK"
    assert y["H2"] == "YAVAS YAKINSAMA"


def test_EKSIK_ve_KISA_kol(tmp_path):
    _hepsi(tmp_path)
    for p in (tmp_path / "A104_o15.durumlar").iterdir():
        p.unlink()
    y = RAP.yargila(RAP.oku(tmp_path))
    assert y["bulunan"] == 3 and y["H2"] == "OKUNMAZ" and y["H1"] != "OKUNMAZ"
    _yaz(tmp_path, "A104_k15", 3.8, t_son=100.0)
    y = RAP.yargila(RAP.oku(tmp_path))
    assert y["eksik"]["k15"] == "300 s'ye ulasmamis" and y["H1"] == "OKUNMAZ"


def test_CLI_json_uzerine_yazmaz(tmp_path):
    _hepsi(tmp_path / "k")
    out = tmp_path / "S.json"
    assert RAP.main(["--kok", str(tmp_path / "k"), "--json", str(out)]) == 0
    assert json.loads(out.read_text(encoding="utf-8"))["bulunan"] == 4
    with pytest.raises(SystemExit):
        RAP.main(["--kok", str(tmp_path / "k"), "--json", str(out)])
