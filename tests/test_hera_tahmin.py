"""Protokol HT — Hera ön kaydı: öngörü dağılımı, koşul etiketi, değiştirilemezlik."""
from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path

import numpy as np
import pytest

from dartrift.inference.design import DART_UZAYI_S3, lhs_design

_KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_KOK / "scripts"))
_spec = importlib.util.spec_from_file_location("ht", _KOK / "scripts" / "hera_tahmin.py")
ht = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ht)


def _havuz(tohum=5):
    rng = np.random.default_rng(tohum)
    th = np.vstack([lhs_design(DART_UZAYI_S3, 24, root_seed=s) for s in (20260906, 20260914)])
    X = np.vstack([th, th])
    U = DART_UZAYI_S3.to_unit(X)
    beta_log = -0.3 + 0.6 * (1 - U[:, 1]) + rng.normal(0, 0.01, len(X))
    R = 2.0 + 1.5 * (1 - U[:, 1]) + rng.normal(0, 0.02, len(X))          # R_krater, kimlik
    V = np.log10(20 + 40 * (1 - U[:, 1])) + rng.normal(0, 0.01, len(X))   # V_krater, log10
    grup = np.concatenate([np.arange(48), np.arange(48)])
    return X, np.column_stack([beta_log, R, V]), grup


def _gozlem(bm1, s_log=0.02):
    return {"beta": 1 + bm1, "beta_eksi_1": bm1, "sigma_beta": 0.1,
            "y_log": math.log10(bm1), "sigma_log": s_log}


def test_POSTERIOR_ongorusu_gercek_Y0_krateri_kapsiyor_ve_onselden_dar():
    X, Y, g = _havuz()
    u_gercek = 0.3
    y_obs = -0.3 + 0.6 * (1 - u_gercek)
    w, kosul, _ = ht.agirliklar(X, Y[:, 0], g, _gozlem(10 ** y_obs), n_grid=16)
    assert kosul.startswith("POSTERIOR")
    t = ht.ongoru(X, Y[:, 1:], g, w, ["R_krater", "V_krater"], n_grid=16, n_ornek=4000)
    R_gercek = 2.0 + 1.5 * (1 - u_gercek)
    V_gercek = 20 + 40 * (1 - u_gercek)
    assert t["R_krater"]["kantiller"]["q05"] <= R_gercek <= t["R_krater"]["kantiller"]["q95"]
    assert t["V_krater"]["kantiller"]["q05"] <= V_gercek <= t["V_krater"]["kantiller"]["q95"]
    w0 = np.full(len(w), 1.0 / len(w))
    t0 = ht.ongoru(X, Y[:, 1:], g, w0, ["R_krater"], n_grid=16, n_ornek=4000)
    gen = t["R_krater"]["kantiller"]["q84"] - t["R_krater"]["kantiller"]["q16"]
    gen0 = t0["R_krater"]["kantiller"]["q84"] - t0["R_krater"]["kantiller"]["q16"]
    assert gen < 0.6 * gen0


def test_gozlem_onsel_disinda_ise_KOSULSUZ_etiketi_ve_duz_agirlik():
    X, Y, g = _havuz()
    w, kosul, d = ht.agirliklar(X, Y[:, 0], g, _gozlem(5.0), n_grid=12)
    assert kosul.startswith("KOSULSUZ") and "ONSEL DISI" in kosul
    assert np.allclose(w, 1.0 / len(w))


def test_log_donusum_geri_donuyor():
    assert ht.geri_donustur("V_krater", 2.0) == pytest.approx(100.0)
    assert ht.geri_donustur("R_krater", 2.5) == pytest.approx(2.5)


def test_kayit_SHA256_dogrulaniyor_ve_UZERINE_YAZILMAZ(tmp_path):
    k = ht.kayit_olustur({"R_krater": {"kantiller": {"q50": 2.5}}}, {"etiket": "x"})
    assert ht.dogrula(k)
    bozuk = {**k, "tahmin": {"R_krater": {"kantiller": {"q50": 2.6}}}}
    assert not ht.dogrula(bozuk)
    yol = ht.kaydet(k, tmp_path / "ONKAYIT_HERA_x.json")
    with pytest.raises(FileExistsError, match="UZERINE YAZILMAZ"):
        ht.kaydet(k, yol)


def test_ongoru_deterministik():
    X, Y, g = _havuz()
    w = np.full(12 ** 3, 1.0 / 12 ** 3)
    a = ht.ongoru(X, Y[:, 1:], g, w, ["R_krater", "V_krater"], n_grid=12, n_ornek=2000)
    b = ht.ongoru(X, Y[:, 1:], g, w, ["R_krater", "V_krater"], n_grid=12, n_ornek=2000)
    assert a == b


def test_protokol_belgesi_ve_uyari():
    m = (_KOK / "docs" / "truba" / "PROTOKOL-HT-HERA-TAHMIN.md").read_text(encoding="utf-8")
    # (Ilk yazimda burada anlamsiz bir kosullu ifade vardi: hicbir sey sinamiyordu.)
    assert "son krater değil" in m
    for p in ("`KOSULSUZ`", "SHA-256", "üzerine yazılmaz", "`q05`–`q95`"):
        assert p in m, p
    assert "SON krater degildir" in ht.UYARI
