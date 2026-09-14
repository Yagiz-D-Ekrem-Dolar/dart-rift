"""Protokol V (koşullu) — U raporunun önek genellemesi ve iş betiği tutarlılığı."""
from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

import numpy as np

_KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_KOK / "scripts"))
_spec = importlib.util.spec_from_file_location("urv", _KOK / "scripts" / "u_model_raporu.py")
ur = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ur)


def _durum(yol: Path, bm1: float):
    yol.parent.mkdir(parents=True, exist_ok=True)
    np.savez(yol, mermi_kesri=np.array([0.0, 0.0, 1.0]), m=np.array([2e9, 2.16e9, 580.0]),
             p_imp=579.4 * 6144.9, fizik_tani=json.dumps({"beta_hedef": 1.0 + bm1}))


def test_topla_onek_V_yalniz_V_dizinlerini_okuyor(tmp_path):
    _durum(tmp_path / "V_V1_kaba_sahne20260906.durumlar" / "nokta_0000.npz", 1.4)
    _durum(tmp_path / "V_V1_kaba_sahne99991111.durumlar" / "nokta_0000.npz", 1.6)
    _durum(tmp_path / "U_U0_kaba_sahne20260906.durumlar" / "nokta_0000.npz", 0.9)
    v = ur.topla(tmp_path, "V")
    assert list(v) == [("V1", "kaba")] and len(v[("V1", "kaba")]) == 2
    u = ur.topla(tmp_path)
    assert list(u) == [("U0", "kaba")]
    out = ur.yargi(v)
    assert out["satirlar"]["V1:kaba"]["beta_eksi_1_sim"] == 1.5


def test_V_isi_kosullu_ve_varyantlar_belgeyle_ayni():
    m = (_KOK / "truba" / "is_V_model.slurm").read_text(encoding="utf-8")
    assert 'if [ -z "${V4_EK+x}" ]' in m and "exit 2" in m
    ad = re.search(r"^AD=\(([^)]*)\)", m, flags=re.M).group(1).split()
    doc = (_KOK / "docs" / "truba" / "PROTOKOL-V-MODEL2.md").read_text(encoding="utf-8")
    for v in ad:
        assert f"| {v} |" in doc, v
    assert "HİÇBİR VARYANT ULAŞMIYOR" in doc and "gönderilmez" in doc
    assert "--t-end 0.2" in m
