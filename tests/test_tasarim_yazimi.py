"""U/V iş betiklerinde tasarım dosyası ATOMİK yazılıyor (2026-09-16, gönderimden önce).

Aynı varyantın iki tohumu aynı `U_tasarim_<A>.json` / `V_tasarim_<A>.json`
dosyasına yazıyor. `echo ... > "$TAS"` birisi dosyayı sıfırlarken öbürünün
python'u okursa boş JSON okuyup düşerdi (16 görev aynı anda başlıyor).
Geçici dosya + `mv -f` ile okuyan her zaman tam dosya görür.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

_KOK = Path(__file__).resolve().parents[1]
BETIKLER = ("is_U_model.slurm", "is_V_model.slurm")


def _bash():
    for a in (os.environ.get("DARTRIFT_BASH"),
              os.path.join(os.environ.get("ProgramFiles", ""), "Git", "bin", "bash.exe"),
              shutil.which("bash")):
        if a and os.path.isfile(a) and not any(s in a.lower() for s in ("system32", "windowsapps")):
            return a
    return None


def _yazim_satiri(ad: str) -> str:
    m = (_KOK / "truba" / ad).read_text(encoding="utf-8")
    komut = [s for s in m.splitlines() if not s.lstrip().startswith("#")]
    satirlar = [s for s in komut if s.startswith("echo") and '"$TAS' in s]
    assert len(satirlar) == 1, (ad, satirlar)
    return satirlar[0]


@pytest.mark.parametrize("ad", BETIKLER)
def test_dogrudan_yazim_YOK_gecici_dosya_ve_mv_VAR(ad):
    s = _yazim_satiri(ad)
    assert '> "$TAS"' not in s
    assert '> "$TAS.$SLURM_JOB_ID.tmp" && mv -f "$TAS.$SLURM_JOB_ID.tmp" "$TAS"' in s


@pytest.mark.skipif(_bash() is None, reason="POSIX bash yok")
@pytest.mark.parametrize("ad", BETIKLER)
def test_yazim_gercekten_gecerli_JSON_uretir_gecici_dosya_kalmaz(ad, tmp_path):
    hedef = tmp_path / "tasarim.json"
    kabuk = f'TAS="{hedef.as_posix()}"; TA=1.15; TY=1.0e0; TF=0.275; SLURM_JOB_ID=42\n' \
            + _yazim_satiri(ad) + "\n"
    r = subprocess.run([_bash(), "-c", kabuk], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert json.loads(hedef.read_text(encoding="utf-8")) == {"theta": [[1.15, 1.0, 0.275]]}
    assert sorted(p.name for p in tmp_path.iterdir()) == ["tasarim.json"]
