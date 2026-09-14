"""Gözlenebilir tanısı (A86) — istisna metni kaydediliyor, türler sayılıyor."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np

_KOK = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("gt", _KOK / "scripts" / "gozlem_tanisi.py")
gt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gt)


def _sahte_krater(d):
    if float(d["t"]) > 0.05:
        raise ValueError("eksen isininda yuzey bulunamadi (pencere: 79.5..91.0 m)")
    return SimpleNamespace(derinlik_merkez=3.7, hacim=51.8, yaricap=2.8)


def _npz(yol: Path, t: float, gecerli: bool = True):
    yol.parent.mkdir(parents=True, exist_ok=True)
    np.savez(yol, t=t, gecerlilik=json.dumps({"gecerli": gecerli}))


def test_tani_TAMAM_ve_istisna_metni(tmp_path):
    _npz(tmp_path / "a.npz", 0.024)
    _npz(tmp_path / "b.npz", 0.1, gecerli=False)
    a = gt.tani(np.load(tmp_path / "a.npz"), _sahte_krater)
    b = gt.tani(np.load(tmp_path / "b.npz"), _sahte_krater)
    assert a["krater"] == "TAMAM" and a["V_krater"] == 51.8 and a["gecerli"] is True
    assert b["krater"].startswith("ValueError: eksen isininda yuzey bulunamadi")
    assert b["gecerli"] is False


def test_eksik_alan_KeyError_yakalaniyor(tmp_path):
    np.savez(tmp_path / "c.npz", t=0.024)
    r = gt.tani(np.load(tmp_path / "c.npz"))       # gercek operator: 'x' yok -> KeyError
    assert r["krater"].startswith("KeyError")


def test_tara_havuz_desen_ve_hata_turleri(tmp_path):
    for dz, t in (("X_matris_sahne1.durumlar", 0.024), ("X_matris_sahne2.durumlar", 0.1),
                  ("Y_matris_sahne1.durumlar", 0.2)):
        _npz(tmp_path / dz / "nokta_0000.npz", t)
    out = gt.tara(tmp_path, "X_matris_sahne*.durumlar+Y_matris_sahne*.durumlar", _sahte_krater)
    assert out["n"] == 3 and out["n_krater_hata"] == 2
    assert out["hata_turleri"] == {"TAMAM": 1, "ValueError: eksen isininda yuzey bulunamadi": 2}
    assert {r["dizin"] for r in out["hatalilar"]} == {"X_matris_sahne2.durumlar",
                                                     "Y_matris_sahne1.durumlar"}
