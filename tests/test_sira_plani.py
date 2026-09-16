"""TRUBA sıra planları (`truba/sira_*.json`) — gönderimden ÖNCE tutarlılık ve bütçe.

Plan yanlışsa sıralı gönderici yanlış görevi, yanlış betikle ya da dizi
aralığı dışında gönderir. Her plan için: betik var, görevler `#SBATCH
--array` aralığında, GPU sayısı `--gres` ile aynı, `export` virgülsüz (A84),
adım başına GPU ≤ 8.
"""
from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

import pytest

_KOK = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("sg", _KOK / "scripts" / "sirali_gonderici.py")
sg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sg)

PLANLAR = sorted((_KOK / "truba").glob("sira_*.json"))


def test_en_az_bir_plan_var():
    assert PLANLAR


@pytest.mark.parametrize("yol", PLANLAR, ids=lambda p: p.name)
def test_plan_betiklerle_TUTARLI(yol):
    plan = json.loads(yol.read_text(encoding="utf-8"))
    sg.plani_denetle(plan)
    for a in plan["adimlar"]:
        betik = _KOK / a["betik"]
        assert betik.is_file(), a["betik"]
        m = betik.read_text(encoding="utf-8")
        gres = re.search(r"^#SBATCH --gres=gpu:(\d+)", m, flags=re.M)
        assert int(a.get("gpu", 1)) == (int(gres.group(1)) if gres else 0), a["ad"]
        dizi = re.search(r"^#SBATCH --array=(\d+)-(\d+)", m, flags=re.M)
        if a.get("gorevler") is None:
            assert dizi is None, f"{a['ad']}: dizi betigi tek is olarak gonderilemez"
        else:
            assert dizi, f"{a['ad']}: betik dizi degil"
            lo, hi = int(dizi.group(1)), int(dizi.group(2))
            assert all(lo <= g <= hi for g in a["gorevler"]), a["ad"]
            assert len(set(a["gorevler"])) == len(a["gorevler"]), a["ad"]
        sg.sure_saat(m)                                      # sure siniri okunabilir


@pytest.mark.parametrize("metin,saat", [
    ("#SBATCH --time=16:00:00", 16.0), ("#SBATCH --time=1-02:30:00", 26.5),
    ("#SBATCH --time=90", 1.5), ("#SBATCH --time=30:00", 0.5),
    ("#SBATCH --time=2-12", 60.0), ("#SBATCH -t 03:15:00", 3.25)])
def test_sure_bicimleri(metin, saat):
    assert sg.sure_saat("#!/bin/bash\n" + metin + "\n") == pytest.approx(saat)


def test_U_planinin_butcesi_ust_sinir():
    plan = json.loads((_KOK / "truba" / "sira_bitis3_U.json").read_text(encoding="utf-8"))
    saat = {a["ad"]: sg.sure_saat((_KOK / a["betik"]).read_text(encoding="utf-8"))
            for a in plan["adimlar"]}
    r = sg.butce(plan, {}, saat, azami=8)
    assert r["gpu_saat_ust"] == pytest.approx(200.0)          # 20 gorev x 10 sa
    assert r["duvar_saat_ust"] == pytest.approx(30.0)         # 8 GPU: kaba 2 tur + orta 1 tur
    # varsayilan sinir 20 (2026-09-16): kaba 16 gorev tek turda -> 10 + 10 sa
    assert sg.butce(plan, {}, saat)["duvar_saat_ust"] == pytest.approx(20.0)
    durum = {f"U_kaba:{i}": {"is": f"9_{i}", "durum": "BITTI"} for i in range(8)}
    r = sg.butce(plan, durum, saat, azami=8)
    assert r["adimlar"]["U_kaba"] == {"kalan": 8, "gpu_saat_ust": 80.0, "duvar_saat_ust": 10.0}
    assert r["duvar_saat_ust"] == pytest.approx(20.0)
