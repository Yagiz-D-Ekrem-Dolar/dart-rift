"""Çalışma alanı yolu — yeni hesapta iş betikleri u1 yolunda KALMIYOR (2026-09-15).

İş betikleri `/arf/scratch/egitimg16u1/driftclaude` sabit yazıyor. Kullanıcı
başka hesap verecek; o hesapta `#SBATCH -o` izin hatasıyla işi düşürür, `KOK`
başka kampanyaya bakar. Plan `kok` alanı taşıyorsa `betikler` betiğe uygular.
Ayrıca Windows çalışma kopyasındaki CRLF üretilen betiğe geçmiyor.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

_KOK = Path(__file__).resolve().parents[1]
TRUBA = _KOK / "truba"
_spec = importlib.util.spec_from_file_location("sg", _KOK / "scripts" / "sirali_gonderici.py")
sg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sg)

AKTIF = ("is_U_model.slurm", "is_Mt_plato.slurm", "is_M2t_plato.slurm", "is_N_genel.slurm",
         "is_Pgen_rapor.slurm", "is_D_dart.slurm", "is_HT_hera.slurm", "is_V_model.slurm")
YENI = "/arf/scratch/egitimg16u9/driftclaude"


@pytest.mark.parametrize("ad", AKTIF)
def test_aktif_betiklerde_u1_yolu_TAMAMEN_degisiyor(ad):
    m = (TRUBA / ad).read_text(encoding="utf-8")
    n_eski = len(sg._KOK_KALIBI.findall(m))
    assert n_eski >= 2, ad                                  # en az -o/-e ya da KOK
    y = sg.kok_uygula(m, YENI + "/")                        # sondaki / atilir
    assert "egitimg16u1" not in y
    assert y.count(YENI) == n_eski and len(y.splitlines()) == len(m.splitlines())
    assert f"{YENI}/ciktilar" in y


def test_None_aynen_gecersiz_yol_ve_kalipsiz_betik_REDDEDILIR():
    m = (TRUBA / "is_U_model.slurm").read_text(encoding="utf-8")
    assert sg.kok_uygula(m, None) == m
    for kotu in ("goreli/yol", "/a b/driftclaude", "/arf/../etc", "/x;rm -rf"):
        with pytest.raises(ValueError, match="gecersiz"):
            sg.kok_uygula(m, kotu)
    with pytest.raises(ValueError, match="kalibi yok"):
        sg.kok_uygula("#!/bin/bash\n#SBATCH -J x\necho a\n", YENI)


def test_CRLF_girdi_uretilen_betige_GECMEZ():
    m = (TRUBA / "is_U_model.slurm").read_text(encoding="utf-8").replace("\n", "\r\n")
    b = sg.gorev_betigi(m, 4)
    assert "\r" not in b and "#SBATCH --array=4" in b.splitlines()


def test_CLI_betikler_plandaki_kok_alanini_UYGULAR(tmp_path):
    plan = {"kok": YENI, "adimlar": [{"ad": "U", "betik": str(TRUBA / "is_U_model.slurm"),
                                      "gorevler": [0, 1]}]}
    pp, dp, od = tmp_path / "p.json", tmp_path / "SIRA.json", tmp_path / "b"
    pp.write_text(json.dumps(plan), encoding="utf-8")
    assert sg.main(["betikler", "--plan", str(pp), "--durum", str(dp), "--cikti-dizini",
                    str(od), "--kullanilan-gpu", "0"]) == 0
    b = (od / "sira_U_1.slurm").read_bytes().decode("utf-8")
    assert "egitimg16u1" not in b and f"#SBATCH -o {YENI}/ciktilar/U_%A_%a.out" in b
    assert f"KOK={YENI}" in b and "\r" not in b
