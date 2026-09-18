"""PROTOKOL-W2 §3 duman kabulü — kural ve 'β yazdırılmaz' sözleşmesi."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import w2_duman_kontrol as D  # noqa: E402


def test_KURAL_esikleri_kilitli():
    assert D.ARTIK_ESIGI_DUMAN == 1.0e-4 and D.DONMUS_EN_AZ == 1


@pytest.mark.parametrize("donmus,artik,kabul", [
    (5, 1e-6, True), (1, 1e-4, True), (0, 1e-9, False),
    (3, 2e-4, False), (3, float("nan"), False)])
def test_KARAR(donmus, artik, kabul):
    assert D.karar(donmus=donmus, artik=artik)["kabul"] is kabul


def test_CLI_BETA_YAZDIRMIYOR(tmp_path, capsys):
    d = tmp_path / "W2D.durumlar"
    d.mkdir()
    ft = {"beta_hedef": 9.8765, "dondurulmus": 4}
    gc = {"gecerli": True, "kontroller": {"momentum_defteri": True},
          "degerler": {"momentum_artik_bagil": 3.0e-7}}
    np.savez(d / "nokta_0000_a.npz", fizik_tani=json.dumps(ft),
             gecerlilik=json.dumps(gc), t=5.0)
    assert D.main(["--npz", str(d / "*.npz")]) == 0
    cikti = capsys.readouterr().out
    assert "W2 GONDERILEBILIR" in cikti
    assert "9.87" not in cikti and "beta_hedef" not in cikti
