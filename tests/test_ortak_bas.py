"""ortak_bas.sh — her TRUBA isinin basi: yanlis ortamda ILK SANIYEDE durur (2026-09-16).

Eski kopya yalniz TRUBA'daydi ve hesap degisince kayboldu; artik depoda.
Sinavlar gercek bash'le `source` eder (Git Bash; WSL kisayolu atlanir).
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

_KOK = Path(__file__).resolve().parents[1]
BETIK = _KOK / "truba" / "ortak_bas.sh"


def _bash():
    for a in (os.environ.get("DARTRIFT_BASH"),
              os.path.join(os.environ.get("ProgramFiles", ""), "Git", "bin", "bash.exe"),
              shutil.which("bash")):
        if a and os.path.isfile(a) and not any(s in a.lower() for s in ("system32", "windowsapps")):
            return a
    return None


BASH = _bash()
METIN = BETIK.read_text(encoding="utf-8")


def test_cikis_kodlari_ve_ortam_yolu_yazili():
    for kod in ("exit 91", "exit 92", "exit 93", "exit 94"):
        assert kod in METIN, kod
    assert 'export PATH="$ORTAM_BIN:$PATH"' in METIN
    assert "envs/gpu-2024.0/bin" in METIN and "SABIT_COMMIT" in METIN
    # isin basinda git pull YOK (dizinin gorevleri farkli kodla kosmasin)
    komut = [s for s in METIN.splitlines() if not s.lstrip().startswith("#")]
    assert not any("git pull" in s for s in komut)
    assert "\r" not in METIN


@pytest.mark.skipif(BASH is None, reason="POSIX bash yok")
def test_sozdizimi():
    r = subprocess.run([BASH, "-n", BETIK.as_posix()], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


@pytest.mark.skipif(BASH is None, reason="POSIX bash yok")
def test_KOK_yoksa_ve_GPU_yoksa_DURUR(tmp_path):
    kabuk = f"source '{BETIK.as_posix()}'; echo GECTI"
    r = subprocess.run([BASH, "-c", kabuk], capture_output=True, text=True,
                       env={"PATH": "/usr/bin:/bin"})
    assert r.returncode != 0 and "KOK tanimli degil" in r.stderr and "GECTI" not in r.stdout
    r = subprocess.run([BASH, "-c", kabuk], capture_output=True, text=True,
                       env={"PATH": "/usr/bin:/bin", "KOK": tmp_path.as_posix()})
    assert r.returncode == 91 and "TESISAT SINAVI DUSTU" in r.stdout
