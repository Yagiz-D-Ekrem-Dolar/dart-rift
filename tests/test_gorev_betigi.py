"""Görev başına betik — argümansız `sbatch <dosya>` ile tek görev ve export.

Yeni TRUBA MCP'si `--array`/`--export` geçemiyor. Üretilen betik: tek dizi
indeksi, bütün `#SBATCH` yönergeleri korunmuş, export'lar yönergelerden
SONRA (önce yazılsa sbatch kalan yönergeleri sessizce yok sayar).
"""
from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
from pathlib import Path

import pytest

_KOK = Path(__file__).resolve().parents[1]
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


U = (_KOK / "truba" / "is_U_model.slurm").read_text(encoding="utf-8")
D = (_KOK / "truba" / "is_D_dart.slurm").read_text(encoding="utf-8")


def test_dizi_satiri_TEK_indekse_iner_diger_yonergeler_AYNI():
    b = sg.gorev_betigi(U, 5)
    assert "#SBATCH --array=5" in b.splitlines() and "--array=0-19" not in b
    eski = [s for s in U.splitlines() if s.startswith("#SBATCH") and "--array" not in s]
    yeni = [s for s in b.splitlines() if s.startswith("#SBATCH") and "--array" not in s]
    assert eski == yeni
    assert b.replace("#SBATCH --array=5", "#SBATCH --array=0-19") == U.rstrip("\n") + "\n"


def test_export_SON_yonergeden_sonra_ve_tirnakli():
    b = sg.gorev_betigi(U, 3, {"V4_EK": "--mu-f 0.2 --yigin-yogunlugu 1500", "LAD": "kaba"})
    s = b.splitlines()
    son_yon = max(i for i, x in enumerate(s) if x.startswith("#SBATCH"))
    i_ex = s.index("export V4_EK='--mu-f 0.2 --yigin-yogunlugu 1500'")
    assert i_ex > son_yon and s[i_ex + 1] == "export LAD=kaba"
    assert all(not x.startswith("#SBATCH") for x in s[son_yon + 1:])


def test_dizi_olmayan_betik_ve_hatali_girdiler():
    assert sg.gorev_betigi(D, None) == D.rstrip("\n") + "\n"
    with pytest.raises(ValueError, match="dizi degil"):
        sg.gorev_betigi(D, 0)
    with pytest.raises(ValueError, match="gorevsiz"):
        sg.gorev_betigi(U, None)
    with pytest.raises(ValueError, match="degisken adi"):
        sg.gorev_betigi(U, 0, {"A-B": "x"})
    assert sg.gorev_dosya_adi({"ad": "U_kaba"}, 7) == "sira_U_kaba_7.slurm"
    assert sg.gorev_dosya_adi({"ad": "D"}, None) == "sira_D.slurm"


@pytest.mark.skipif(_bash() is None, reason="POSIX bash yok")
def test_uretilen_betik_bash_ile_gecerli_ve_export_calisiyor(tmp_path):
    b = sg.gorev_betigi(U, 11, {"V4_EK": "a b"})
    p = tmp_path / "g.slurm"
    p.write_text(b, encoding="utf-8", newline="\n")
    r = subprocess.run([_bash(), "-n", p.as_posix()], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    parca = "\n".join(x for x in b.splitlines() if x.startswith("export ")) + '\necho "[$V4_EK]"\n'
    r = subprocess.run([_bash(), "-c", parca], capture_output=True, text=True)
    assert r.stdout.strip() == "[a b]"


def test_CLI_betikler_HAZIRLANDI_sayar_iki_kez_cagrilinca_sinir_ASILMAZ(tmp_path, capsys):
    import json

    plan = {"adimlar": [{"ad": "U", "betik": str(_KOK / "truba" / "is_U_model.slurm"),
                         "gorevler": list(range(20))}]}
    pp, dp, od = tmp_path / "p.json", tmp_path / "SIRA.json", tmp_path / "b"
    pp.write_text(json.dumps(plan), encoding="utf-8")
    arg = ["betikler", "--plan", str(pp), "--durum", str(dp), "--cikti-dizini", str(od)]
    dolu = sg.AZAMI_GPU - 2                               # kuyrukta sinirin 2 eksigi
    assert sg.main([*arg, "--kullanilan-gpu", str(dolu)]) == 0
    assert sorted(p.name for p in od.iterdir()) == ["sira_U_0.slurm", "sira_U_1.slurm"]
    d = json.loads(dp.read_text("utf-8"))
    assert d["U:0"]["durum"] == "HAZIRLANDI" and d["U:1"]["betik"] == "sira_U_1.slurm"
    # gonderilmeden tekrar: kuyruk ayni ama 2 hazir -> yeni betik YOK
    assert sg.main([*arg, "--kullanilan-gpu", str(dolu)]) == 0
    assert len(list(od.iterdir())) == 2
    # U:0 gonderildi (kuyruk +1), U:1 hala hazir -> sinir dolu, yeni YOK
    assert sg.main(["kaydet", "--durum", str(dp), "--anahtar", "U:0", "--is", "900_0"]) == 0
    assert sg.main([*arg, "--kullanilan-gpu", str(dolu + 1)]) == 0
    assert len(list(od.iterdir())) == 2
    assert json.loads(dp.read_text("utf-8"))["U:0"] == {"is": "900_0", "durum": "GONDERILDI"}
    assert "#SBATCH --array=1" in (od / "sira_U_1.slurm").read_text("utf-8")
