"""Protokol J raporu — **sonuçlardan önce** sınanır.

Eşikler koşudan önce kilitlendi. Bu sınavlar betiğin bilinen
girdilerde doğru yargıyı verdiğini gösteriyor; sonuç geldiğinde eşiği
ayarlamaya yer kalmıyor.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest

_KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_KOK / "scripts"))
_spec = importlib.util.spec_from_file_location(
    "dt_raporu", _KOK / "scripts" / "dt_raporu.py")
dt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dt)


def _kol(ad="k", kip="son", x0=6.0, s=0.1, gecerli=True, tam=1.0,
         oran=float("nan")):
    return {"ad": ad, "kip": kip, "x0": x0, "sigma_x0": s,
            "gecerli": gecerli, "tamamlanma": tam, "ara_oran_max": oran,
            "akma": {}}


# --- esikler protokolle ayni -------------------------------------------

def test_esikler_protokol_metniyle_AYNI():
    m = (_KOK / "docs" / "truba" / "PROTOKOL-J-ZAMAN-ADIMI.md").read_text(
        encoding="utf-8")
    assert dt.TAMAMLANMA_ESIGI == 0.90 and "`≥ 0,90`" in m
    assert dt.ARA_ORAN_TAVANI == 1.0 + 1.0e-9 and "1 + 1e-9" in m
    assert dt.ARA_KALDIRMA_ORANI == 0.5 and "0,5 |Δ_son|" in m
    assert dt.J_SIGMA == 2.0 and "`kat ≥ 2`" in m
    assert dt.TEKRAR_ESIGI == 1.0e-9 and "`≤ 1e-9`" in m
    assert dt.N_TASARIM == 48


def test_I2_protokol_I_esiklerini_KULLANIYOR():
    import gecis_raporu as gr

    assert gr.DAYANIKLI_SIGMA == 2.0 and gr.DAYANIKSIZ_SIGMA == 4.0
    assert gr.R2_ESIGI == 0.85


def test_I_kaymasi_protokol_I_sonucu():
    assert dt.I_KAYMA == pytest.approx(5.950 - 6.340)


# --- O1-O3 --------------------------------------------------------------

def test_tamamlanma_esik_altinda_OKUNMAZ():
    ok, sebep = dt.okunabilir(_kol(tam=0.89))
    assert not ok and "tamamlanma" in sebep
    assert dt.okunabilir(_kol(tam=0.90))[0]


def test_gecersiz_sigmoid_OKUNMAZ():
    ok, sebep = dt.okunabilir(_kol(gecerli=False))
    assert not ok and "GECERSIZ" in sebep


def test_ara_kolunda_akma_asimi_UYGULAMA_KUSURU():
    ok, sebep = dt.okunabilir(_kol(kip="ara", oran=1.0 + 1e-6))
    assert not ok and "UYGULAMA KUSURU" in sebep
    assert dt.okunabilir(_kol(kip="ara", oran=1.0 + 1e-10))[0]


def test_ara_kolunda_tani_yoksa_OKUNMAZ():
    """Tanı alanı eksikse `ara`'nın doğru çalıştığı bilinemez."""
    assert not dt.okunabilir(_kol(kip="ara", oran=float("nan")))[0]


def test_son_kolunda_akma_asimi_OKUNABILIR():
    """`son` kipinde aşım BEKLENEN kusurdur; ön koşul değil."""
    assert dt.okunabilir(_kol(kip="son", oran=1966.0))[0]


# --- Y1 -----------------------------------------------------------------

def test_Y1_negatif_ve_anlamli_YOL_GOSTERILDI():
    y = dt.y1_yargi(_kol(x0=6.34, s=0.1), _kol(x0=5.90, s=0.1))
    assert y["karar"] == "ZAMAN ADIMI YOLU GOSTERILDI"
    assert y["kat"] == pytest.approx(0.44 / np.sqrt(0.02))


def test_Y1_pozitif_ve_anlamli_TERS_YON():
    y = dt.y1_yargi(_kol(x0=6.0, s=0.1), _kol(x0=6.5, s=0.1))
    assert y["karar"] == "ZAMAN ADIMI ETKILI, TERS YON"


def test_Y1_sinirin_hemen_alti_GOSTERILEMEDI():
    s = 0.1
    esik = dt.J_SIGMA * np.sqrt(2) * s
    y = dt.y1_yargi(_kol(x0=6.0, s=s), _kol(x0=6.0 - 0.999 * esik, s=s))
    assert y["karar"] == "DT YOLU GOSTERILEMEDI"
    y = dt.y1_yargi(_kol(x0=6.0, s=s), _kol(x0=6.0 - 1.001 * esik, s=s))
    assert y["karar"] == "ZAMAN ADIMI YOLU GOSTERILDI"


def test_Y1_aciklanan_pay_c0125_kolundan():
    y = dt.y1_yargi(_kol(x0=6.34), _kol(x0=5.80), _kol(x0=6.145))
    # (6,145 - 6,34) / (5,950 - 6,340) = 0,5
    assert y["aciklanan_pay"] == pytest.approx(0.5)


def test_Y1_okunmayan_kol_OKUNMAZ():
    y = dt.y1_yargi(_kol(tam=0.5), _kol())
    assert y["karar"] == "OKUNMAZ"


# --- Y2 -----------------------------------------------------------------

def test_Y2_ara_duz_ve_kucuk_KALDIRIYOR():
    y1 = dt.y1_yargi(_kol(x0=6.34), _kol(x0=5.80))
    y2 = dt.y2_yargi(_kol(kip="ara", x0=5.0, oran=1.0),
                     _kol(kip="ara", x0=4.95, oran=1.0), y1)
    assert y2["karar"] == "ARA KALDIRIYOR"


def test_Y2_ara_hala_kayiyorsa_KALDIRMIYOR():
    y1 = dt.y1_yargi(_kol(x0=6.34), _kol(x0=5.80))
    y2 = dt.y2_yargi(_kol(kip="ara", x0=5.0, oran=1.0),
                     _kol(kip="ara", x0=4.5, oran=1.0), y1)
    assert y2["karar"] == "ARA KALDIRMIYOR"


def test_Y2_anlamsiz_ama_yari_payindan_buyuk_KALDIRMIYOR():
    """İki koşul BİRLİKTE: `< 2σ` tek başına yetmez."""
    y1 = dt.y1_yargi(_kol(x0=6.34, s=0.1), _kol(x0=5.90, s=0.1))  # d=-0,44
    y2 = dt.y2_yargi(_kol(kip="ara", x0=5.0, s=0.3, oran=1.0),
                     _kol(kip="ara", x0=4.7, s=0.3, oran=1.0), y1)  # |d|=0,3
    assert y2["kat"] < dt.J_SIGMA
    assert y2["karar"] == "ARA KALDIRMIYOR"


def test_Y2_Y1_okunmadiysa_OKUNMAZ():
    y2 = dt.y2_yargi(_kol(kip="ara", oran=1.0), _kol(kip="ara", oran=1.0),
                     {"karar": "OKUNMAZ", "sebep": "x"})
    assert y2["karar"] == "OKUNMAZ"


def test_Y2_Y1_yol_yoksa_NOT_dusuyor():
    y1 = dt.y1_yargi(_kol(x0=6.0), _kol(x0=6.01))
    y2 = dt.y2_yargi(_kol(kip="ara", x0=5.0, oran=1.0),
                     _kol(kip="ara", x0=5.0, oran=1.0), y1)
    assert "zaten gosterilemedi" in y2["not"]


# --- I2 -----------------------------------------------------------------

def test_I2_protokol_I_tablosunu_uyguluyor():
    kaba = _kol(kip="ara", x0=5.0, s=0.1, oran=1.0)
    kaba.update(R2=0.95, x0_veri_icinde=True)
    orta = _kol(kip="ara", x0=5.1, s=0.1, oran=1.0)
    orta.update(R2=0.95, x0_veri_icinde=True)
    assert dt.i2_yargi(kaba, orta)["karar"] == "DAYANIKLI"
    orta["x0"] = 5.5
    assert dt.i2_yargi(kaba, orta)["karar"] == "ZAYIF"
    orta["x0"] = 6.0
    assert dt.i2_yargi(kaba, orta)["karar"] == "DAYANIKSIZ"


def test_I2_ara_kusurluysa_OKUNMAZ():
    kaba = _kol(kip="ara", oran=2.0)
    kaba.update(R2=0.95, x0_veri_icinde=True)
    orta = _kol(kip="ara", oran=1.0)
    orta.update(R2=0.95, x0_veri_icinde=True)
    assert dt.i2_yargi(kaba, orta)["karar"] == "OKUNMAZ"


# --- uctan uca: sentetik sigmoidlerden ----------------------------------

def _sigmoid(x, x0, w=0.4, alt=0.2, ust=0.6):
    return alt + (ust - alt) / (1.0 + np.exp((x - x0) / w))


def test_uctan_uca_bilinen_kayma_GERI_KAZANILIYOR():
    """`x₀` `6,3 → 5,8` kayan sentetik veride Y1 yolu bulmalı."""
    rng = np.random.default_rng(5)
    x = np.sort(rng.uniform(3.0, 7.0, 24))
    kollar = {}
    for (kip, cetik, _), x0 in zip(dt.KOLLAR,
                                   (6.3, 6.05, 5.8, 5.0, 5.0, 5.0),
                                   strict=True):
        d = _sigmoid(x, x0) + rng.normal(0, 0.003, len(x))
        o = dt.kol_degerlendir(f"J1_{kip}_{cetik}", kip, x, d, n_nokta=48,
                               akma={"oran_max_max": 1.0} if kip == "ara"
                               else {"oran_max_max": 1966.0})
        kollar[(kip, cetik)] = o
    r = dt.seri_raporu(kollar)
    assert r["Y1"]["karar"] == "ZAMAN ADIMI YOLU GOSTERILDI", r["Y1"]
    assert r["Y1"]["aciklanan_pay"] == pytest.approx(0.25 / 0.39, abs=0.15)
    assert r["Y2"]["karar"] == "ARA KALDIRIYOR", r["Y2"]


def test_uctan_uca_kayma_YOKSA_gosterilemedi():
    rng = np.random.default_rng(7)
    x = np.sort(rng.uniform(3.0, 7.0, 24))
    kollar = {}
    for kip, cetik, _ in dt.KOLLAR:
        d = _sigmoid(x, 6.0) + rng.normal(0, 0.01, len(x))
        kollar[(kip, cetik)] = dt.kol_degerlendir(
            f"J1_{kip}_{cetik}", kip, x, d, n_nokta=48,
            akma={"oran_max_max": 1.0})
    r = dt.seri_raporu(kollar)
    assert r["Y1"]["karar"] == "DT YOLU GOSTERILEMEDI", r["Y1"]


# --- npz akma tanisi okunuyor -------------------------------------------

def test_akma_ozeti_npz_JSON_alanini_okuyor(tmp_path):
    dz = tmp_path / "J1_ara_c0250_sahne1.durumlar"
    dz.mkdir()
    for i, o in enumerate((0.9999999999, 1.0)):
        np.savez(dz / f"nokta_{i:04d}_x.npz", theta=np.zeros(3),
                 akma_tani=json.dumps({"oran_max": o, "oran_p99": 0.5,
                                       "asan_kutle_kesri": 0.0}))
    np.savez(dz / "nokta_0009_eski.npz", theta=np.zeros(3))   # alan yok
    a = dt.akma_ozeti([dz])
    assert a["n_npz"] == 3 and a["n_tanili"] == 2
    assert a["oran_max_max"] == pytest.approx(1.0)


def test_akma_ozeti_tanisiz_kol_tavani_GECEMEZ(tmp_path):
    dz = tmp_path / "J1_ara_c0250_sahne1.durumlar"
    dz.mkdir()
    np.savez(dz / "nokta_0000_x.npz", theta=np.zeros(3))
    a = dt.akma_ozeti([dz])
    kol = _kol(kip="ara", oran=a.get("oran_max_max", float("nan")))
    assert not dt.okunabilir(kol)[0]
