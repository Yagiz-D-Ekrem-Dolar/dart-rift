"""Protokol D — gerçek gözlem uygulaması, çözünürlük hatası ve Bitiş 3 taslağı."""
from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np
import pytest

from dartrift.inference.design import DART_UZAYI_S3, lhs_design
from dartrift.observables.period_interface import dart_beta_budget

_KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_KOK / "scripts"))


def _yukle(ad):
    spec = importlib.util.spec_from_file_location(ad, _KOK / "scripts" / f"{ad}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


dg = _yukle("dart_gozlem_posterior")
ch = _yukle("cozunurluk_hatasi")
b3 = _yukle("bitis3_raporu")


def _havuz(fonk, gurultu=0.02, tohum=3):
    rng = np.random.default_rng(tohum)
    th = np.vstack([lhs_design(DART_UZAYI_S3, 24, root_seed=s) for s in (20260906, 20260914)])
    X = np.vstack([th, th])
    U = DART_UZAYI_S3.to_unit(X)
    y = np.array([fonk(u) for u in U]) + rng.normal(0, gurultu, len(X))
    grup = np.concatenate([np.arange(48), np.arange(48)])
    return X, y, grup


def test_gozlenen_beta_depo_arayuzuyle_ve_kutleyle_orantili():
    p = 579.4 * 6144.9
    a = dg.gozlenen_beta(4.3e9, p)
    b = dart_beta_budget(p, target_mass=4.3e9)
    assert a["beta"] == pytest.approx(b["beta"])
    c = dg.gozlenen_beta(2.15e9, p)
    # beta ~ M, ama yorunge hizi TOPLAM kutleye bagli: tam orantili degil
    # (ilk surum tam oranti bekliyordu; %0,2 fark vardi).
    assert c["beta"] == pytest.approx(dart_beta_budget(p, target_mass=2.15e9)["beta"])
    assert c["beta"] == pytest.approx(a["beta"] / 2, rel=5e-3)
    assert a["sigma_sistematik"] == pytest.approx(0.105 * a["beta"])
    assert a["sigma_log"] == pytest.approx(a["sigma_beta"] / (a["beta_eksi_1"] * math.log(10)))


def _gozlem(bm1, s_log=0.05):
    return {"beta": 1 + bm1, "beta_eksi_1": bm1, "sigma_beta": 0.1, "y_log": math.log10(bm1),
            "sigma_log": s_log}


def test_model_gozleme_ulasmiyorsa_ONSEL_DISI_YUKARI_posterior_YOK():
    # model log10(beta-1) in [-0.3, -0.05]  (beta 1.5..1.9); gozlem beta-1 = 2.2
    X, y, g = _havuz(lambda u: -0.3 + 0.25 * (1 - u[1]))
    out = dg.uygula(X, y, g, _gozlem(2.2), n_grid=16)
    assert out["kapsama"]["karar"] == "ONSEL DISI (YUKARI)"
    assert "posterior" not in out
    assert out["kapsama"]["theta_max_dogal"][1] < 3e3       # en buyuk beta dusuk Y0'da
    assert out["kapsama"]["fark_ust_sigma"] > 2


def test_ONSEL_ICINDE_Y0_kisitlaniyor_digerleri_kisitlanmiyor():
    X, y, g = _havuz(lambda u: -0.3 + 0.6 * (1 - u[1]), gurultu=0.01)
    gercek_u = 0.3
    y_obs = -0.3 + 0.6 * (1 - gercek_u)
    out = dg.uygula(X, y, g, _gozlem(10 ** y_obs, s_log=0.02), n_grid=24)
    assert out["kapsama"]["karar"] == "ONSEL ICINDE"
    p = out["posterior"]
    assert p["log10_Y0"]["karar"] == "KISITLANIYOR"
    lo, hi = p["log10_Y0"]["aralik95_u"]
    assert lo <= gercek_u <= hi
    assert p["blok_alpha0"]["karar"] == "KISITLANMIYOR"
    assert p["blok_kesri"]["karar"] == "KISITLANMIYOR"


def test_cozunurluk_terimi_toplam_sigmayi_buyutuyor():
    X, y, g = _havuz(lambda u: -0.3 + 0.6 * (1 - u[1]), gurultu=0.01)
    a = dg.uygula(X, y, g, _gozlem(0.8, 0.02), n_grid=12)
    b = dg.uygula(X, y, g, _gozlem(0.8, 0.02), sigma_coz=0.1, n_grid=12)
    assert b["sigma_toplam_log"] > a["sigma_toplam_log"]
    assert b["sigma_toplam_log"] == pytest.approx(math.hypot(a["sigma_toplam_log"], 0.1))


def test_orta_nokta_araligi_duz_dagilimda_simetrik():
    e = np.linspace(0, 1, 41)
    lo, hi = dg._orta_nokta_aralik(np.ones(41), e, 0.16, 0.84)
    assert lo == pytest.approx(0.16, abs=1e-9) and hi == pytest.approx(0.84, abs=1e-9)


def test_cozunurluk_hatasi_sabit_ve_theta_bagli_kayma():
    veri = {}
    for k in range(6):
        for m, kay in (("kaba", 0.3), ("orta", 0.1), ("ince", 0.0)):
            veri[(k, m)] = {g: [1.0 + k * 0.1 + kay + (0.05 * k if g == "V_krater" else 0),
                                1.0 + k * 0.1 + kay + (0.05 * k if g == "V_krater" else 0)]
                            for g in ch.GOZLEMLER_C}
    for k in range(6):   # V_krater: kaymasi theta'ya bagli olsun (orta'da)
        veri[(k, "orta")]["V_krater"] = [v + (0.2 if k % 2 else -0.2)
                                         for v in veri[(k, "orta")]["V_krater"]]
    out = ch.hata_modeli(veri, "orta")["gozlem"]
    assert out["beta_eksi_1"]["karar"] == "SABIT KAYMA"
    assert out["beta_eksi_1"]["sigma_coz"] == pytest.approx(0.1)
    assert out["V_krater"]["karar"] == "THETA'YA BAGLI KAYMA"


def test_bitis3_Q_kurali_ve_P_v4b_kurali(tmp_path):
    def yaz(ad, d):
        (tmp_path / ad).write_text(json.dumps(d), encoding="utf-8")

    assert b3.esas_sonuc(tmp_path)["Q1"] == "BEKLENIYOR"
    yaz("S_Mt.json", {g: {"yargi": {"karar": "YAKINSIYOR"}} for g in b3.YAKINSAMA_GOZLEMLERI[:4]})
    yaz("S_PQo_yol.json", {"esas": "gp", "genel": "TEK EKSEN COZULUYOR", "cozulen": {"gp": 1}})
    yaz("S_PQob_yol.json", {"esas": "kuadratik", "genel": "IKI EKSEN COZULUYOR",
                            "cozulen": {"kuadratik": 2}})
    e = b3.esas_sonuc(tmp_path)
    assert e["Q1"] == "YAKINSIYOR" and e["esas"]["havuz"].startswith("Q3")
    assert e["esas"]["kaynak"] == "P-v4b" and e["esas"]["genel"] == "IKI EKSEN COZULUYOR"
    yaz("S_PQob_yol.json", {"esas": None, "genel": "KALIBRASYON DUSTU"})
    assert b3.esas_sonuc(tmp_path)["esas"]["kaynak"] == "P-v4"
    yaz("S_Mt.json", {g: {"yargi": {"karar": "YAKINSAMIYOR"}} for g in b3.YAKINSAMA_GOZLEMLERI})
    assert b3.esas_sonuc(tmp_path)["esas"]["havuz"].startswith("ince-72")
    metin = b3.taslak(tmp_path)
    assert "BEKLENIYOR" in metin and "Q1 plato anında yakınsama" in metin
    assert "## 5. Model yeterliliği (Protokol U)" in metin
    assert "## 6. Hera ön kayıtları (Protokol HT)" in metin
    yaz("S_U.json", {"genel": "HICBIR VARYANT ULASMIYOR (en yakin U8:kaba, z = +3.1)",
                     "satirlar": {"U8:kaba": {"beta_eksi_1_sim": 1.1, "beta_eksi_1_gozlem": 2.1,
                                              "z": 3.1, "karar": "ALTINDA"}}})
    yaz("ONKAYIT_HERA_Qo.json", {"tahmin": {"R_krater": {"kantiller": {
        "q16": 2.1, "q50": 2.5, "q84": 2.9}}}, "meta": {"kosul": "KOSULSUZ (x)", "t_end_s": 0.1},
        "sha256": "ab" * 32})
    metin = b3.taslak(tmp_path)
    assert "HICBIR VARYANT ULASMIYOR" in metin and "U8:kaba" in metin
    assert "**GÖNDERİLMELİ**" in metin
    yaz("S_V.json", {"genel": "MODEL GOZLEME ULASABILIYOR: V1:kaba"})
    assert "koşuldu — **MODEL GOZLEME ULASABILIYOR: V1:kaba**" in b3.taslak(tmp_path)
    assert "R_krater q16/q50/q84 = 2.10 / 2.50 / 2.90 m" in metin


def test_protokol_D_esikleri_belgede():
    m = (_KOK / "docs" / "truba" / "PROTOKOL-D-DART-GOZLEM.md").read_text(encoding="utf-8")
    assert (dg.SISTEMATIK_BAGIL, dg.KAPSAMA_SIGMA_KATI, dg.BILGI_ESIGI) == (0.105, 2.0, 0.5)
    for p in ("(0,105 β)²", "`y − 2s > ŷ_max`", "`genişlik68 / 0,68 < 0,5`",
              "std/|ort| < 0,5"):
        assert p in m, p
    assert ch.SABIT_KAYMA_ESIGI == 0.5
