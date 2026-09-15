"""Çözünürlük terimi — kısmi Mt havuzu SESSİZ geçmiyor (2026-09-15 öz denetim).

14 Eylül iptalinde Mt'nin 8–35 görevleri koşmadı. `σ_çöz` eksik θ/tohumdan
hesaplanıp D/HT'ye tam havuz gibi girecekti. Kural değişmedi; eksik yazılıyor.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

_KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_KOK / "scripts"))
_spec = importlib.util.spec_from_file_location("ch", _KOK / "scripts" / "cozunurluk_hatasi.py")
ch = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ch)


def _veri(cikar=(), tek_tohum=()):
    v = {}
    for k in range(ch.N_TETA):
        for m in ch.MERDIVENLER:
            n = 0 if (k, m) in cikar else (1 if (k, m) in tek_tohum else 2)
            v[(k, m)] = {g: [0.5 + 0.1 * k + (0.2 if m == "orta" else 0.0)] * n
                         for g in ch.GOZLEMLER_C}
    return v


def test_tam_havuz_TAM():
    out = ch.hata_modeli(_veri(), "orta")
    assert out["tam"] is True and out["eksik"] == []


def test_ince_theta_ve_tek_tohum_EKSIK_yaziliyor_hesap_AYNI():
    tam = ch.hata_modeli(_veri(), "orta")
    out = ch.hata_modeli(_veri(cikar={(5, "ince")}, tek_tohum={(2, "orta")}), "orta")
    assert out["tam"] is False
    assert out["eksik"] == ["t2:orta:1/2", "t5:ince:0/2"]
    # kilitli hesap: eksik theta dusulur, kalanlardan sigma (degerler sabit kayma 0,2)
    assert out["gozlem"]["beta_eksi_1"]["n_theta"] == 5
    assert out["gozlem"]["beta_eksi_1"]["sigma_coz"] == tam["gozlem"]["beta_eksi_1"]["sigma_coz"]


def test_Mt_iptali_senaryosu_ince_hic_yok_OKUNMAZ_ve_EKSIK():
    cikar = {(k, "ince") for k in range(ch.N_TETA)}
    out = ch.hata_modeli(_veri(cikar=cikar), "kaba")
    assert out["tam"] is False and len(out["eksik"]) == 6
    assert all(d["karar"] == "OKUNMAZ" for d in out["gozlem"].values())


def test_oku_tum_durumlar(tmp_path):
    assert ch.oku(None, ["beta_eksi_1"]) == {"sigma": {}, "tam": None,
                                             "not": "COZUNURLUK TERIMI YOK"}
    assert ch.oku(tmp_path / "yok.json", ["beta_eksi_1"])["not"] == "COZUNURLUK TERIMI YOK"

    def yaz(ad, d):
        p = tmp_path / ad
        p.write_text(json.dumps(d), encoding="utf-8")
        return p

    eksik = yaz("e.json", {"gozlem": {"beta_eksi_1": {"sigma_coz": 0.05},
                                      "V_krater": {"sigma_coz": float("nan")}},
                           "tam": False, "eksik": ["t5:ince:0/2"]})
    r = ch.oku(eksik, ["beta_eksi_1", "V_krater"])
    assert r["sigma"] == {"beta_eksi_1": 0.05} and r["tam"] is False
    assert "EKSIK HAVUZ (1 eksik: t5:ince:0/2)" in r["not"]
    nan = yaz("n.json", {"gozlem": {"beta_eksi_1": {"sigma_coz": float("nan")}},
                         "tam": False, "eksik": ["x"]})
    assert ch.oku(nan, ["beta_eksi_1"])["not"].startswith("COZUNURLUK TERIMI YOK")
    eski = yaz("o.json", {"gozlem": {"beta_eksi_1": {"sigma_coz": 0.05}}})
    r = ch.oku(eski, ["beta_eksi_1"])
    assert r["tam"] is None and "eski JSON" in r["not"]
    tam = yaz("t.json", {"gozlem": {"beta_eksi_1": {"sigma_coz": 0.05}}, "tam": True})
    assert ch.oku(tam, ["beta_eksi_1"])["not"] == "cozunurluk: t.json"


def test_D_ve_HT_ORTAK_okuyucuyu_kullaniyor():
    for ad in ("dart_gozlem_posterior.py", "hera_tahmin.py"):
        m = (_KOK / "scripts" / ad).read_text(encoding="utf-8")
        assert "ch.oku(a.cozunurluk" in m, ad
        assert '["gozlem"][GOZLEM]' not in m and 'read_text(encoding="utf-8"))["gozlem"]' not in m
