"""TRUBA iş betikleri — A84 türü sessiz hatalara karşı denetimler.

A84: `sbatch --export=ALL,D="a,b,c"` virgülü değişken ayırıcı saydı; dört
rapor hata vermeden tek kampanyayla koştu. Bu sınavlar:

1. Her `truba/*.slurm` sözdizimi olarak geçerli (`bash -n`).
2. Havuz raporu `+` ayırıcıyı virgüle çeviriyor, desen ve koşu sayısını
   denetliyor ve eksikte hata koduyla duruyor.
3. Depodaki hiçbir betik/belge **komut satırında** virgüllü bir `D=`'yi
   `--export` ile geçirmiyor (yorum satırları hariç).
4. Havuz raporunun desen işleme parçası gerçekten `bash` ile koşulunca
   üç deseni üç sayıyor.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

_KOK = Path(__file__).resolve().parents[1]
TRUBA = _KOK / "truba"


def _bash() -> str | None:
    """POSIX bash bul; Windows'ta WSL kısayolunu ATLA.

    PowerShell'den koşunca `shutil.which("bash")` `System32\\bash.exe`'yi (WSL)
    buluyordu: Windows yolunu ters eğik çizgisiz alıp "No such file" ile 127
    döndü ve 32 sınav betiklerde kusur yokken düştü (2026-09-15). Git Bash'ten
    koşunca geçiyordu — sınav ortama bağlıydı.
    """
    adaylar = [os.environ.get("DARTRIFT_BASH"), shutil.which("bash")]
    if os.name == "nt":
        pf = [os.environ.get("ProgramFiles"), os.environ.get("ProgramW6432"),
              os.environ.get("LOCALAPPDATA") and os.path.join(os.environ["LOCALAPPDATA"],
                                                               "Programs")]
        adaylar += [os.path.join(p, "Git", "bin", "bash.exe") for p in pf if p]
    for a in adaylar:
        if not a or not os.path.isfile(a):
            continue
        if os.name == "nt" and any(s in a.lower() for s in ("system32", "windowsapps")):
            continue
        return a
    return None


BASH = _bash()


@pytest.mark.skipif(BASH is None, reason="bash yok")
@pytest.mark.parametrize("betik", sorted(p.name for p in TRUBA.glob("*.slurm")))
def test_slurm_sozdizimi(betik):
    r = subprocess.run([BASH, "-n", str(TRUBA / betik)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def test_Pgen_desen_ve_kosu_denetimleri_var():
    m = (TRUBA / "is_Pgen_rapor.slurm").read_text(encoding="utf-8")
    assert 'D="${D//+/,}"' in m
    assert "BEKLENEN_DESEN" in m and "exit 4" in m
    assert "BEKLENEN_KOSU_EN_AZ" in m and "exit 5" in m
    assert 'kosu_denetle "$K/S_${O}_$V.json" || exit 6' in m


def test_virgullu_export_D_komut_satirinda_YOK():
    kotu = []
    for p in list(TRUBA.glob("*")) + list((_KOK / "docs").rglob("*.md")):
        if not p.is_file():
            continue
        for i, satir in enumerate(p.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            if satir.lstrip().startswith("#") or "`" in satir:
                continue
            if re.search(r'--export=[^\s]*\bD="[^"]*,', satir):
                kotu.append(f"{p.name}:{i}")
    assert not kotu, kotu


@pytest.mark.skipif(BASH is None, reason="bash yok")
def test_desen_isleme_parcasi_UC_deseni_uc_sayiyor(tmp_path):
    m = (TRUBA / "is_Pgen_rapor.slurm").read_text(encoding="utf-8")
    bas = m.index('D="${D//+/,}"')
    son = m.index("fi", m.index("BEKLENEN_DESEN\" ]")) + 2
    parca = m[bas:son]
    betik = tmp_path / "p.sh"
    betik.write_text('D="A_*.durumlar+B_*.durumlar+C_*.durumlar"\n' + parca + "\n",
                     encoding="utf-8", newline="\n")
    r = subprocess.run([BASH, str(betik)], capture_output=True, text=True,
                       env={"BEKLENEN_DESEN": "3", "PATH": "/usr/bin:/bin"})
    assert r.returncode == 0, r.stdout + r.stderr
    assert "desen sayisi: 3" in r.stdout
    r2 = subprocess.run([BASH, str(betik)], capture_output=True, text=True,
                        env={"BEKLENEN_DESEN": "4", "PATH": "/usr/bin:/bin"})
    assert r2.returncode == 4, r2.stdout
