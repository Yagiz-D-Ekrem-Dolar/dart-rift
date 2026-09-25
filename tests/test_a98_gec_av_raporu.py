"""PROTOKOL-A98 kilitli kuralları — sınavlar (koşudan önce)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import a98_gec_av_raporu as A  # noqa: E402


def _npz(kok: Path, ad: str, beta_300: float, *, t_son=300.0, gecerli=True,
         E_av=None, W_pl=None):
    ts = np.geomspace(1e-4, t_son, 50)
    if t_son > 300.0:
        ts = np.unique(np.append(ts, 300.0))
    egri = [[float(t), 1.0, float(beta_300), 1e6] for t in ts]
    ft = {"beta_hedef": float(beta_300), "impuls_egrisi": egri,
          "gec_evre": {"t_gecis": 0.2}}
    if E_av is not None:
        ft["av_tanisi"] = {"E_av_gec_evre": E_av, "plastik_is_gec_evre": W_pl}
    d = kok / f"{ad}.durumlar"
    d.mkdir(parents=True, exist_ok=True)
    np.savez(d / "nokta_0000_a.npz", fizik_tani=json.dumps(ft),
             gecerlilik=json.dumps({"gecerli": gecerli}), m=np.ones(10))


def _hepsi(kok, *, w2=3.686, uy=3.978, k1=3.686, k01=4.3, o01=4.35, k0=4.33,
           p64=3.70, E=9.0, W=1.0, **kw):
    _npz(kok, "W2_Y10_g0p2", w2, t_son=600.0)
    _npz(kok, "UY_orta", uy)
    _npz(kok, "A98_k_av1", k1, E_av=E, W_pl=W)
    _npz(kok, "A98_k_av01", k01, E_av=0.5, W_pl=2.0)
    _npz(kok, "A98_o_av01", o01, E_av=0.4, W_pl=2.0, **kw)
    _npz(kok, "A98_k_av0", k0, E_av=0.0, W_pl=2.0)
    if p64 is not None:
        _npz(kok, "A98_k_p6400", p64, E_av=9.0, W_pl=1.0)
    return A.yargi(A.topla(kok))


def test_esikler_ve_kollar_kilitli():
    assert (A.R0_ESIK, A.M1_ESIK, A.M2_ESIK, A.M3_ESIK, A.M4_ESIK,
            A.M5_ESIK) == (0.01, 0.5, 0.05, 0.05, 0.02, 0.05)
    assert A.T_KIYAS == 300.0
    assert A.KOLLAR == {"W2": "W2_Y10_g0p2", "UYorta": "UY_orta",
                        "k_av1": "A98_k_av1", "k_av01": "A98_k_av01",
                        "o_av01": "A98_o_av01", "k_av0": "A98_k_av0",
                        "k_p6400": "A98_k_p6400"}


def test_ANA_SEBEP(tmp_path):
    o = _hepsi(tmp_path)
    assert o["R0"] == "GECTI"
    assert o["M1"] == "AV GEC EVREDE BASKIN" and o["M1_pay"] == pytest.approx(0.9)
    assert o["M2"] == "BETA GEC EVRE AV'SINE DUYARLI"
    assert o["M3"] == "AV COZUNURLUK FARKININ ANA SEBEBI"
    assert o["M4"] == "AV 0,1'DE IHMAL EDILEBILIR"
    assert o["genel"] == o["M3"]


def test_KISMI_ve_SEBEP_DEGIL(tmp_path):
    # D1 = (2.978-2.686)/2.978 = 0.098; D01 = (3.6-3.3)/3.6 = 0.083 -> KISMI
    o = _hepsi(tmp_path / "a", k01=4.3, o01=4.6)
    assert o["M3"] == "AV KISMI SEBEP"
    o = _hepsi(tmp_path / "b", k01=4.0, o01=4.6)
    assert o["M3"] == "AV SEBEP DEGIL"


def test_M3_iki_kosul_BIRLIKTE(tmp_path):
    # D01 <= 0.05 ama D1/2'den buyuk -> ana sebep DEGIL, KISMI
    o = _hepsi(tmp_path, uy=3.80, k01=4.30, o01=4.43)
    assert o["M3_delta_av01"] <= 0.05
    assert o["M3_delta_av01"] > 0.5 * o["M3_delta_av1"]
    assert o["M3"] == "AV KISMI SEBEP"


def test_R0_DUSERSE_hepsi_OKUNMAZ(tmp_path):
    o = _hepsi(tmp_path, k1=3.70)
    assert o["R0"] == "DUSTU" and o["genel"].startswith("OKUNMAZ")
    assert "M3" not in o


def test_GECERSIZ_kol_yalniz_kendi_olcutunu_dusurur(tmp_path):
    _hepsi(tmp_path)
    _npz(tmp_path, "A98_k_av0", 4.33, gecerli=False)
    o = A.yargi(A.topla(tmp_path))
    assert o["M4"] == "OKUNMAZ"
    assert o["M3"] == "AV COZUNURLUK FARKININ ANA SEBEBI"


def test_300s_ULASMAYAN_kol_OKUNMAZ(tmp_path):
    _hepsi(tmp_path)
    _npz(tmp_path, "A98_o_av01", 4.35, t_son=150.0)
    o = A.yargi(A.topla(tmp_path))
    assert "o_av01" in o["kullanilmaz"]
    assert o["M3"] == "OKUNMAZ"


def test_M1_tani_yoksa_OKUNMAZ(tmp_path):
    _hepsi(tmp_path)
    _npz(tmp_path, "A98_k_av1", 3.686)          # av_tanisi yok
    o = A.yargi(A.topla(tmp_path))
    assert o["M1"] == "OKUNMAZ"
    assert o["R0"] == "GECTI"


def test_EKSIK_R0_kolu(tmp_path):
    _npz(tmp_path, "A98_k_av01", 4.3)
    o = A.yargi(A.topla(tmp_path))
    assert o["genel"].startswith("OKUNMAZ")


def test_M5_mermi_cozunurlugu_AYRI_yargi(tmp_path):
    o = _hepsi(tmp_path / "a", p64=3.70)
    assert o["M5"] == "MERMI COZUNURLUGU GEC BETA'YA YANSIMIYOR"
    o = _hepsi(tmp_path / "b", p64=4.20)
    assert o["M5"] == "MERMI COZUNURLUGU GEC BETA'YA YANSIYOR"
    assert o["genel"] == o["M3"]           # genel yargi M5'ten etkilenmez
    o = _hepsi(tmp_path / "c", p64=None)
    assert o["M5"] == "OKUNMAZ"
    assert o["M3"] == "AV COZUNURLUK FARKININ ANA SEBEBI"
