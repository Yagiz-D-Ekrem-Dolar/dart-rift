"""PROTOKOL-UA kilitli kuralı — sınavlar."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import ua_uzak_alan_raporu as U  # noqa: E402


def _npz(kok: Path, ad: str, beta: float, gecerli=True, n=100):
    d = kok / f"{ad}.durumlar"
    d.mkdir(parents=True, exist_ok=True)
    ft = {"beta_hedef": beta, "M_ejekta": 1e6, "dondurulmus": 5,
          "beta_iki_yontem": {"koni_tam_acisi_derece": 110.0,
                              "koni_kenar_derece": 150.0}}
    gc = {"gecerli": gecerli}
    np.savez(d / "nokta_0000_a.npz", fizik_tani=json.dumps(ft),
             gecerlilik=json.dumps(gc), m=np.ones(n))


def _kur(kok, b7, b5, b3, **kw):
    _npz(kok, "W2_Y10_g0p2", 1.0 + b7, **kw)
    _npz(kok, "UA_s5p0", 1.0 + b5, **kw)
    _npz(kok, "UA_s3p5", 1.0 + b3, **kw)
    return U.yargi(U.topla(kok))


def test_ESIKLER_kilitli():
    assert U.ESIK_INCE == 0.05 and U.ESIK_KABA == 0.10 and U.ORAN == 1.4
    assert U.KOLLAR[7.0] == "W2_Y10_g0p2"


def test_YAKINSAMIS(tmp_path):
    out = _kur(tmp_path, 2.00, 2.05, 2.08)
    assert out["genel"] == "UZAK ALAN YAKINSAMIS"


def test_YAKINSIYOR_ve_RICHARDSON(tmp_path):
    out = _kur(tmp_path, 2.0, 2.4, 2.6)
    assert out["genel"] == "YAKINSIYOR"
    r = out["richardson"]
    assert r["p"] == pytest.approx(np.log(2.0) / np.log(1.4), rel=1e-9)
    assert r["b_sonsuz"] > 2.6


def test_YAKINSAMA_YOK(tmp_path):
    out = _kur(tmp_path, 2.0, 2.1, 2.6)
    assert out["genel"] == "YAKINSAMA YOK"


def test_EKSIK_ve_GECERSIZ_OKUNMAZ(tmp_path):
    _npz(tmp_path, "W2_Y10_g0p2", 3.0)
    _npz(tmp_path, "UA_s5p0", 3.0)
    out = U.yargi(U.topla(tmp_path))
    assert out["genel"].startswith("OKUNMAZ") and out["eksik"] == ["3.5"]
    out2 = _kur(tmp_path / "b", 2.0, 2.0, 2.0, gecerli=False)
    assert out2["genel"].startswith("OKUNMAZ") and len(out2["gecersiz"]) == 3


def test_CLI(tmp_path, capsys):
    _kur(tmp_path, 2.0, 2.05, 2.08)
    yol = tmp_path / "S_UA.json"
    assert U.main(["--kok", str(tmp_path), "--json", str(yol)]) == 0
    assert json.loads(yol.read_text(encoding="utf-8"))["genel"] == \
        "UZAK ALAN YAKINSAMIS"
    assert "GENEL" in capsys.readouterr().out
