"""U/V kapsamı — düşen görev genel yargıyı ve V kararını SESSİZCE bozmuyor (2026-09-15).

Rapor yalnız bulduğu dizinleri okuyordu: U6 (ρ 1500) düşse "HİÇBİR VARYANT
ULAŞMIYOR" onsuz verilir, V de ona göre gönderilirdi. Kural değişmedi;
eksik yazılıyor, V kararı eksik U ile gönderim önermiyor.
"""
from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

_KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_KOK / "scripts"))


def _yukle(ad):
    spec = importlib.util.spec_from_file_location(ad, _KOK / "scripts" / f"{ad}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


ur = _yukle("u_model_raporu")
vgk = _yukle("v_gonderim_karari")
sg = _yukle("sirali_gonderici")
b3 = _yukle("bitis3_raporu")


def _tam_U():
    v = {}
    for (ad, lad), n in ur.BEKLENEN["U"].items():
        v[(ad, lad)] = [{"bm1": 1.0, "M": 4.157e9, "p_imp": 579.4 * 6144.9, "tohum": t}
                        for t in ("20260906", "99991111")[:n]]
    return v


def test_beklenen_tasarim_is_betikleriyle_AYNI_boyut():
    for onek, betik in (("U", "is_U_model.slurm"), ("V", "is_V_model.slurm")):
        m = (_KOK / "truba" / betik).read_text(encoding="utf-8")
        lo, hi = map(int, re.search(r"^#SBATCH --array=(\d+)-(\d+)", m, flags=re.M).groups())
        assert sum(ur.BEKLENEN[onek].values()) == hi - lo + 1, onek


def test_kapsam_tam_eksik_tohum_ve_nan():
    assert ur.kapsam(_tam_U()) == {"tam": True, "eksik": []}
    v = _tam_U()
    v[("U6", "kaba")] = v[("U6", "kaba")][:1]
    v[("U8", "orta")][1]["bm1"] = float("nan")
    del v[("U3", "kaba")]
    assert ur.kapsam(v) == {"tam": False,
                            "eksik": ["U3:kaba:0/2", "U6:kaba:1/2", "U8:orta:1/2"]}
    assert ur.kapsam({}, "X")["tam"] is None


def test_main_bos_kokte_TAM_DEGIL_ve_hepsi_eksik(tmp_path):
    j = tmp_path / "S_U.json"
    assert ur.main(["--kok", str(tmp_path), "--json", str(j)]) == 0
    out = json.loads(j.read_text(encoding="utf-8"))
    assert out["genel"] == "OKUNMAZ" and out["tam"] is False
    assert len(out["eksik"]) == len(ur.BEKLENEN["U"])


def _satir(varyant, z):
    # u_model_raporu.yargi'nin gercekte urettigi alanlar (ilk surum eksik alanla
    # yazilmisti; bitis3 taslagi KeyError verdi -- sahte veri gercek bicimde olmali)
    return {"varyant": varyant, "merdiven": "kaba", "n": 2, "beta_eksi_1_sim": 1.0,
            "beta_eksi_1_gozlem": 2.1, "sigma_beta": 0.34, "z": z, "karar": "ALTINDA"}


def _s_u(tam):
    s = {"U0:kaba": _satir("U0", 3.4), "U8:kaba": _satir("U8", 2.3)}
    d = {"genel": "HICBIR VARYANT ULASMIYOR (en yakin U8:kaba, z = +2.3)", "satirlar": s,
         "tam": tam}
    if tam is False:
        d["eksik"] = ["U6:kaba:0/2"]
    return d


def test_V_karari_EKSIK_U_ile_GONDERMEZ_tam_U_ile_plan_adimi_uretir():
    k = vgk.karar(_s_u(False))
    assert k["gonder"] is False and k["sebep"].startswith("U EKSIK (1): U6:kaba:0/2")
    k = vgk.karar(_s_u(True))
    assert k["gonder"] and k["plan_adimi"]["export"] == {"V4_EK": k["V4_EK"], "V4_U": "U8"}
    plan = {"adimlar": [k["plan_adimi"]]}
    sg.plani_denetle(plan)
    metin = (_KOK / k["plan_adimi"]["betik"]).read_text(encoding="utf-8")
    b = sg.gorev_betigi(metin, 8, k["plan_adimi"]["export"])
    assert "export V4_U=U8" in b and "export V4_EK='--onsel-disi-izin --mu-f 0.2" in b


def test_V_betigi_V4_U_ZORUNLU_ve_tasarim_yoksa_DURUR():
    m = (_KOK / "truba" / "is_V_model.slurm").read_text(encoding="utf-8")
    assert 'if [ -z "${V4_U:-}" ]; then' in m and "exit 2" in m
    komut_satirlari = [s for s in m.splitlines() if not s.lstrip().startswith("#")]
    assert not any("${V4_U:-U0}" in s for s in komut_satirlari)
    assert 'if [ ! -f "$TAS_U" ]' in m and "exit 3" in m


def test_bitis3_taslagi_EKSIK_U_ve_cozunurluk_notunu_gosteriyor(tmp_path):
    (tmp_path / "S_U.json").write_text(json.dumps(_s_u(False)), encoding="utf-8")
    (tmp_path / "S_DART_Qo.json").write_text(json.dumps({
        "kapsama": {"tahmin_min": -0.3, "beta_max_model": 1.9, "karar": "ONSEL DISI (YUKARI)",
                    "fark_ust_sigma": 5.0},
        "gozlem": {"beta": 3.12, "sigma_beta": 0.34},
        "cozunurluk_notu": "cozunurluk: S_cozunurluk_Mt_orta.json -- EKSIK HAVUZ (6 eksik: x)"}),
        encoding="utf-8")
    metin = b3.taslak(tmp_path)
    assert "- Kapsam: **EKSİK** (U6:kaba:0/2)" in metin
    assert "GÖNDERİLMELİ" not in metin and "U **EKSİK**" in metin
    assert "σ_çöz: cozunurluk: S_cozunurluk_Mt_orta.json -- EKSIK HAVUZ" in metin
    (tmp_path / "S_U.json").write_text(json.dumps(_s_u(True)), encoding="utf-8")
    metin = b3.taslak(tmp_path)
    assert "- Kapsam: TAM" in metin and "**GÖNDERİLMELİ**" in metin
