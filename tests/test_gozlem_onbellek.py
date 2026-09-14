"""Gözlenebilir önbelleği — bit-aynı değerler, geçersizleşme, kapatma."""
from __future__ import annotations

import importlib.util
import json
import math
import os
import sys
from pathlib import Path

import numpy as np

_KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_KOK / "scripts"))
_spec = importlib.util.spec_from_file_location("gob", _KOK / "scripts" / "gozlem_onbellek.py")
gob = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gob)


class _Sayac:
    def __init__(self):
        self.n = 0

    def __call__(self, d):
        self.n += 1
        x = float(d["x"])
        return {"a": x / 3.0, "b": float("nan"), "c": 1e-300 * x}


def _npz(yol, x=7.0):
    np.savez(yol, x=x)
    return yol


def test_ikinci_cagri_onbellekten_ve_BIT_AYNI(tmp_path):
    f = _npz(tmp_path / "nokta_0000.npz")
    h = _Sayac()
    a = gob.gozlem(f, h, kod="k1")
    b = gob.gozlem(f, h, kod="k1")
    assert h.n == 1
    assert a["a"] == b["a"] and a["c"] == b["c"]
    assert math.isnan(b["b"])
    assert (tmp_path / "nokta_0000.gozlem.json").exists()


def test_kod_ozeti_degisince_yeniden_hesap(tmp_path):
    f = _npz(tmp_path / "nokta_0000.npz")
    h = _Sayac()
    gob.gozlem(f, h, kod="k1")
    gob.gozlem(f, h, kod="k2")
    assert h.n == 2


def test_npz_degisince_yeniden_hesap(tmp_path):
    f = _npz(tmp_path / "nokta_0000.npz", 7.0)
    h = _Sayac()
    a = gob.gozlem(f, h, kod="k1")
    st = f.stat()
    _npz(f, 9.0)
    os.utime(f, ns=(st.st_atime_ns, st.st_mtime_ns + 10**9))
    b = gob.gozlem(f, h, kod="k1")
    assert h.n == 2 and b["a"] != a["a"]


def test_bozuk_onbellek_dosyasi_yok_sayiliyor(tmp_path):
    f = _npz(tmp_path / "nokta_0000.npz")
    (tmp_path / "nokta_0000.gozlem.json").write_text("{bozuk", encoding="utf-8")
    h = _Sayac()
    assert gob.gozlem(f, h, kod="k1")["a"] == 7.0 / 3.0
    assert h.n == 1
    assert json.loads((tmp_path / "nokta_0000.gozlem.json").read_text())["anahtar"]["kod"] == "k1"


def test_ortam_degiskeni_ile_kapatma(tmp_path, monkeypatch):
    f = _npz(tmp_path / "nokta_0000.npz")
    monkeypatch.setenv("DARTRIFT_GOZLEM_ONBELLEK", "0")
    h = _Sayac()
    gob.gozlem(f, h, kod="k1")
    gob.gozlem(f, h, kod="k1")
    assert h.n == 2 and not (tmp_path / "nokta_0000.gozlem.json").exists()


def test_kod_ozeti_kaynaklara_bagli(tmp_path):
    a = tmp_path / "a.py"
    a.write_text("x = 1\n")
    o1 = gob.kod_ozeti((a,))
    a.write_text("x = 2\n")
    assert gob.kod_ozeti((a,)) != o1
    assert all(p.exists() for p in gob.KAYNAKLAR)


def test_isit_havuz_boyunca_dolduruyor_ve_hatayi_SAYIYOR(tmp_path):
    for dz in ("A_matris_sahne1.durumlar", "B_matris_sahne2.durumlar"):
        (tmp_path / dz).mkdir()
        _npz(tmp_path / dz / "nokta_0000.npz")
    (tmp_path / "B_matris_sahne2.durumlar" / "nokta_0001.npz").write_bytes(b"bozuk npz")
    h = _Sayac()
    out = gob.isit(tmp_path, "A_matris_sahne*.durumlar+B_matris_sahne*.durumlar", h)
    assert out["n"] == 3 and out["n_hata"] == 1 and h.n == 2
    assert "nokta_0001.npz" in out["hatalar"][0]
    assert (tmp_path / "A_matris_sahne1.durumlar" / "nokta_0000.gozlem.json").exists()


def test_havuz_globu_onbellek_dosyalarini_TOPLAMIYOR(tmp_path):
    f = _npz(tmp_path / "nokta_0000.npz")
    gob.gozlem(f, _Sayac(), kod="k1")
    assert [p.name for p in tmp_path.glob("nokta_*.npz")] == ["nokta_0000.npz"]
