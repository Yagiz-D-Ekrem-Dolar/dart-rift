"""Sıralı gönderici — 8 GPU sınırı (bekleyenler dahil), sıra, HATA'da durma, A84."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

_KOK = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("sg", _KOK / "scripts" / "sirali_gonderici.py")
sg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sg)


def _plan():
    return {"adimlar": [
        {"ad": "Mt", "betik": "truba/is_Mt_plato.slurm", "gorevler": list(range(12))},
        {"ad": "U", "betik": "truba/is_U_model.slurm", "gorevler": [0, 1, 2]},
        {"ad": "Pg", "betik": "truba/is_Pgen_rapor.slurm", "gorevler": None,
         "export": {"TASARIMLAR": "a+b"}, "sonra": ["Mt"]},
    ]}


def test_sinir_8_ve_ust_sinir_degismez():
    assert sg.AZAMI_GPU == 8


def test_gpu_ayristirma_ve_bekleyenler_de_sayilir():
    assert sg.gpu_sayisi("gres:gpu:1") == 1
    assert sg.gpu_sayisi("gres/gpu:a100:2") == 2
    assert sg.gpu_sayisi("N/A") == 0
    satir = ["1_0 RUNNING gres:gpu:1", "1_1 PENDING gres:gpu:1",
             "2_[3-5,9] PENDING gres/gpu:1", "3 COMPLETING gres:gpu:4", "4 RUNNING N/A"]
    # COMPLETING GPU'yu hala tutuyor: ortak hesapta guvenli taraf, sayilir
    assert sg.kuyruk_gpu(satir) == 1 + 1 + 4 + 4


def test_bos_yuva_kadar_secer_asla_asmaz():
    s = sg.secim(_plan(), {}, kullanilan_gpu=3)
    assert [(a["ad"], g) for a, g in s["secilen"]] == [("Mt", i) for i in range(5)]
    assert sg.secim(_plan(), {}, kullanilan_gpu=8)["secilen"] == []
    assert sg.secim(_plan(), {}, kullanilan_gpu=11)["secilen"] == []


def test_onceki_adim_BITMEDEN_sonraki_gonderilmez():
    durum = {f"Mt:{i}": {"is": f"9_{i}", "durum": "GONDERILDI"} for i in range(12)}
    s = sg.secim(_plan(), durum, kullanilan_gpu=0)
    assert s["secilen"] == [] and set(s["bekleyen_adim"]) == {"U", "Pg"}
    for i in range(12):
        durum[f"Mt:{i}"]["durum"] = "BITTI"
    s = sg.secim(_plan(), durum, kullanilan_gpu=0)
    assert [(a["ad"], g) for a, g in s["secilen"]] == [("U", 0), ("U", 1), ("U", 2), ("Pg", None)]


def test_bagimli_adimda_HATA_varsa_DURUR():
    durum = {f"Mt:{i}": {"is": f"9_{i}", "durum": "BITTI"} for i in range(12)}
    durum["Mt:4"]["durum"] = "HATA"
    s = sg.secim(_plan(), durum, kullanilan_gpu=0)
    assert set(s["duran_adim"]) == {"U", "Pg"} and s["secilen"] == []


def test_A84_virgullu_export_REDDEDILIR_ve_komut_bicimi():
    p = _plan()
    assert sg.sbatch_komutu(p["adimlar"][2], None) == [
        "sbatch", "--parsable", "--export=ALL,TASARIMLAR=a+b", "truba/is_Pgen_rapor.slurm"]
    assert sg.sbatch_komutu(p["adimlar"][0], 7)[2] == "--array=7"
    p["adimlar"][2]["export"]["TASARIMLAR"] = "a,b"
    with pytest.raises(ValueError, match="A84"):
        sg.secim(p, {}, 0)


def test_sonra_yalniz_onceki_adimlara_bakabilir():
    p = _plan()
    p["adimlar"][0]["sonra"] = ["Pg"]
    with pytest.raises(ValueError, match="ONCEKI"):
        sg.plani_denetle(p)


def test_adim_at_sacct_ile_gunceller_ve_sinirda_gonderir(tmp_path):
    plan = {"adimlar": [{"ad": "U", "betik": "u.slurm", "gorevler": list(range(10))}]}
    yol = tmp_path / "SIRA.json"
    yol.write_text(json.dumps({"U:0": {"is": "50_0", "durum": "GONDERILDI"},
                               "U:1": {"is": "50_1", "durum": "GONDERILDI"}}), "utf-8")
    cagrilar = []
    sayac = iter(range(100, 200))

    def calistir(k):
        cagrilar.append(k)
        if k[0] == "sacct":
            return "50_0|COMPLETED\n50_1|CANCELLED by 5\n"
        if k[0] == "squeue":
            return "77 RUNNING gres:gpu:1\n78 PENDING gres:gpu:1\n"   # baska isler: 2 GPU
        return f"{next(sayac)}\n"

    r = sg.adim_at(plan, yol, kuru=False, calistir=calistir, kullanici="u4")
    d = json.loads(yol.read_text("utf-8"))
    assert d["U:0"]["durum"] == "BITTI" and d["U:1"]["durum"] == "HATA"
    assert len(r["gonderilen"]) == 6                                  # 8 - 2
    assert d["U:2"] == {"is": "100_2", "durum": "GONDERILDI"}
    assert sum(1 for k in cagrilar if k[0] == "sbatch") == 6
    kuru = sg.adim_at(plan, yol, kuru=True, calistir=calistir, kullanici="u4")
    assert all(g.startswith("sbatch") for g in kuru["gonderilen"])
