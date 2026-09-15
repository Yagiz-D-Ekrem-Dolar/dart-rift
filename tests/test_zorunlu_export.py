"""İş betiklerinin zorunlu değişkenleri — unutulan export SESSİZ varsayılana düşmüyor (2026-09-15).

Yeni TRUBA MCP'si `--export` geçemiyor; değerler `sirali_gonderici.gorev_betigi`
ile betiğe yazılıyor. Unutulan bir değer eskiden:
- `is_N_genel`: `T_END` → 24 ms, `SAHA` → matris (plato/Q5 işi yanlış koşar);
- `is_Pgen_rapor`: `BEKLENEN_DESEN` / `BEKLENEN_KOSU_EN_AZ` → A84 denetimleri atlanır.
Artık betik durur ve `gorev_betigi` eksik export'lu betik üretmez.
"""
from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
from pathlib import Path

import pytest

_KOK = Path(__file__).resolve().parents[1]
TRUBA = _KOK / "truba"
_spec = importlib.util.spec_from_file_location("sg", _KOK / "scripts" / "sirali_gonderici.py")
sg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sg)


def _bash():
    for a in (os.environ.get("DARTRIFT_BASH"),
              os.path.join(os.environ.get("ProgramFiles", ""), "Git", "bin", "bash.exe"),
              shutil.which("bash")):
        if a and os.path.isfile(a) and not any(s in a.lower() for s in ("system32", "windowsapps")):
            return a
    return None


BASH = _bash()
NGEN = (TRUBA / "is_N_genel.slurm").read_text(encoding="utf-8")
PGEN = (TRUBA / "is_Pgen_rapor.slurm").read_text(encoding="utf-8")
VMOD = (TRUBA / "is_V_model.slurm").read_text(encoding="utf-8")


def _kos(tmp_path, parca, env):
    p = tmp_path / "parca.sh"
    p.write_text(parca + "\necho TAMAM\n", encoding="utf-8", newline="\n")
    return subprocess.run([BASH, p.as_posix()], capture_output=True, text=True,
                          env={"PATH": "/usr/bin:/bin", **env})


def test_isaret_satirlari_okunuyor():
    assert sg.zorunlu_export(NGEN) == ["LAD", "TASARIMLAR", "ONEKLER", "NDILIM", "T_END", "SAHA"]
    assert sg.zorunlu_export(PGEN) == ["D", "O", "SN", "BEKLENEN_DESEN", "BEKLENEN_KOSU_EN_AZ"]
    assert sg.zorunlu_export(VMOD) == ["V4_EK", "V4_U"]
    assert sg.zorunlu_export((TRUBA / "is_U_model.slurm").read_text(encoding="utf-8")) == []


def test_N_genel_sessiz_varsayilan_YOK_ve_liste_isaretle_AYNI():
    komut = [s for s in NGEN.splitlines() if not s.lstrip().startswith("#")]
    assert not any(":-0.024" in s or ":-matris" in s for s in komut)
    dongu = next(s for s in komut if s.startswith("for v in "))
    assert dongu.removeprefix("for v in ").removesuffix("; do").split() == sg.zorunlu_export(NGEN)


@pytest.mark.skipif(BASH is None, reason="POSIX bash yok")
def test_N_genel_eksik_T_END_DURUR_tam_env_GECER(tmp_path):
    bas = NGEN.index("for v in LAD")
    son = NGEN.index("exit 2; fi", NGEN.index("bilinmeyen SAHA")) + len("exit 2; fi")
    parca = NGEN[bas:son]
    tam = {"LAD": "orta", "TASARIMLAR": "1 2", "ONEKLER": "a b", "NDILIM": "12",
           "T_END": "0.1", "SAHA": "blok"}
    r = _kos(tmp_path, parca, tam)
    assert r.returncode == 0 and "TAMAM" in r.stdout, r.stdout + r.stderr
    eksik = {k: v for k, v in tam.items() if k != "T_END"}
    r = _kos(tmp_path, parca, eksik)
    assert r.returncode == 2 and "HATA: T_END verilmedi" in r.stdout
    r = _kos(tmp_path, parca, {**tam, "SAHA": "yanlis"})
    assert r.returncode == 2 and "bilinmeyen SAHA" in r.stdout


@pytest.mark.skipif(BASH is None, reason="POSIX bash yok")
def test_Pgen_beklentiler_verilmezse_DURUR(tmp_path):
    bas = PGEN.index('D="${D//+/,}"')
    son = PGEN.index("fi", PGEN.index("exit 5", PGEN.index('if [ "$N_NPZ" -lt'))) + 2
    parca = PGEN[bas:son]
    temel = {"D": "A_*.durumlar+B_*.durumlar", "KOK": tmp_path.as_posix()}
    r = _kos(tmp_path, parca, temel)
    assert r.returncode == 4 and "BEKLENEN_DESEN verilmedi" in r.stdout, r.stdout
    r = _kos(tmp_path, parca, {**temel, "BEKLENEN_DESEN": "2"})
    assert r.returncode == 5 and "BEKLENEN_KOSU_EN_AZ verilmedi" in r.stdout, r.stdout
    r = _kos(tmp_path, parca, {**temel, "BEKLENEN_DESEN": "2", "BEKLENEN_KOSU_EN_AZ": "1"})
    assert r.returncode == 5 and "0 npz < 1" in r.stdout
    r = _kos(tmp_path, parca, {**temel, "BEKLENEN_DESEN": "2", "BEKLENEN_KOSU_EN_AZ": "0"})
    assert r.returncode == 0 and "TAMAM" in r.stdout


def test_gorev_betigi_eksik_zorunlu_export_ile_URETMEZ():
    with pytest.raises(ValueError, match="zorunlu export eksik: V4_U"):
        sg.gorev_betigi(VMOD, 3, {"V4_EK": "--mu-f 0.2"})
    b = sg.gorev_betigi(VMOD, 3, {"V4_EK": "", "V4_U": "U0"})        # bos V4_EK gecerli
    assert "export V4_EK=''" in b and "export V4_U=U0" in b
    with pytest.raises(ValueError, match="T_END, SAHA"):
        sg.gorev_betigi(NGEN, 0, {"LAD": "kaba", "TASARIMLAR": "1", "ONEKLER": "a",
                                  "NDILIM": "1"})
