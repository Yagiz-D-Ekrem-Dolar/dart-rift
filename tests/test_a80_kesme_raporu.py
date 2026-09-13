"""A80 doğrulama raporu — kilitli V1/V2 kuralları."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np

_KOK = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("a80r", _KOK / "scripts" / "a80_kesme_raporu.py")
ar = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ar)

SIG = {"d_merkez": 0.1, "R_krater": 0.1, "V_krater": 1.0, "beta_eksi_1": 0.01, "M_ejekta": 100.0}
TOH = ("20260906", "99991111")


def _kol(kay=0.0, eksik=()):
    rng = np.random.default_rng(3)
    out = {}
    for k in range(6):
        for t in TOH:
            if (k, t) in eksik:
                continue
            out[(k, t)] = {g: 1.0 + kay * SIG[g] + 0.3 * SIG[g] * rng.normal() for g in SIG}
    return out


def test_esikler_belgede():
    m = (_KOK / "docs" / "truba" / "PROTOKOL-A80-KESME.md").read_text(encoding="utf-8")
    assert (ar.NOTR_ESIGI, ar.KUCUK_ESIGI, ar.SAPMA_KATI) == (0.90, 0.70, 2.0)
    for p in ("`≥ 0,90`", "`≥ 0,70`", "`< 0,70`", "`|Δ| ≤ 2σ`", "12/12"):
        assert p in m, p


def test_ayni_kollar_NOTR_ve_KARARLI():
    y = ar.yargi(_kol(), _kol(), SIG)
    assert y["V1"] == "KARARLI" and y["V2"] == "NOTR" and y["n_karsilastirma"] == 60


def test_3_sigma_kayma_FIZIGI_DEGISTIRIYOR():
    y = ar.yargi(_kol(), _kol(kay=3.0), SIG)
    assert y["V2"] == "FIZIGI DEGISTIRIYOR"


def test_eksik_kesmeli_nokta_KARARSIZ_ve_adiyla():
    y = ar.yargi(_kol(eksik={(5, "20260906")}), _kol(eksik={(2, "99991111")}), SIG)
    assert y["V1"] == "KARARSIZ" and y["eksik_yeni"] == ["t2_s99991111"]
    assert y["n_karsilastirma"] == 50


def test_az_karsilastirma_OKUNMAZ():
    az = {k: v for k, v in _kol().items() if k[0] < 2}
    assert ar.yargi(az, az, SIG)["V2"] == "OKUNMAZ"


def test_sigma_L2_json_eslemesi():
    s_l2 = {"L2_matris": {"gozlemler": ["d_merkez", "R_krater", "V_krater", "beta_hedef",
                                        "M_ejekta", "P_ejekta"],
                          "sigma": [0.07, 0.08, 0.9, 0.0026, 183.0, 9000.0]}}
    s = ar.sigma_oku(s_l2)
    assert s["beta_eksi_1"] == 0.0026 and s["M_ejekta"] == 183.0
