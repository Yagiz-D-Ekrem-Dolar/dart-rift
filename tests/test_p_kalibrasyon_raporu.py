"""Protokol P — kapalı döngü kalibrasyonu: kovaryanslı posterior ve yargılar."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

from dartrift.inference.design import DART_UZAYI_S3, lhs_design
from dartrift.inference.posterior import grid_posterior, grid_posterior_kovaryans
from dartrift.inference.surrogate import design_matrix, fit_surrogate, loo_artiklari

_KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_KOK / "scripts"))
_spec = importlib.util.spec_from_file_location(
    "p_kalibrasyon_raporu", _KOK / "scripts" / "p_kalibrasyon_raporu.py")
pr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pr)


def _tasarim(n=24, tohum=20260906):
    return lhs_design(DART_UZAYI_S3, n, root_seed=tohum)


def _kayitlar(fonklar: dict, gurultu: float, tohum=1):
    """24 θ × 2 tohum; `fonklar[g](u) + N(0, gurultu)`, geri kalanı `nan`."""
    rng = np.random.default_rng(tohum)
    th = _tasarim()
    U = DART_UZAYI_S3.to_unit(th)
    kayit = []
    for s in ("a", "b"):
        for t, u in zip(th, U, strict=True):
            k = {g: float("nan") for g in pr.DONUSUMLER}
            for g, f in fonklar.items():
                k[g] = float(f(u) + rng.normal(0.0, gurultu))
            k["theta"] = t
            k["tohum"] = s
            kayit.append(k)
    return kayit


def test_loo_artiklari_elle_LOO_ile_ayni():
    rng = np.random.default_rng(3)
    X = _tasarim(20)
    y = rng.normal(size=20) + DART_UZAYI_S3.to_unit(X)[:, 1]
    e = loo_artiklari(DART_UZAYI_S3, X, y)
    for i in (0, 7, 19):
        k = np.arange(20) != i
        v = fit_surrogate(DART_UZAYI_S3, X[k], y[k])
        assert e[i] == pytest.approx(y[i] - v.predict(X[i:i + 1])[0], rel=1e-8, abs=1e-10)


def test_kovaryansli_posterior_KOSEGENDE_bagimsiz_posteriora_esit():
    X = _tasarim(30)
    U = DART_UZAYI_S3.to_unit(X)
    y1, y2 = U[:, 0] + 0.3 * U[:, 1], U[:, 2] ** 2
    v1 = fit_surrogate(DART_UZAYI_S3, X, y1)
    v2 = fit_surrogate(DART_UZAYI_S3, X, y2)
    n = 16
    e = np.linspace(0, 1, n)
    izg = np.meshgrid(e, e, e, indexing="ij")
    A = design_matrix(np.column_stack([a.ravel() for a in izg]))
    tah = np.column_stack([A @ v1.coef, A @ v2.coef])
    d = [0.4, 0.25]
    s1, s2 = 0.05, 0.08
    pk = grid_posterior_kovaryans(DART_UZAYI_S3, tah, d, np.diag([s1**2, s2**2]), n)

    class _V:
        def __init__(self, c):
            self.coef, self.sigma = c, 0.0

        def predict(self, x):
            return design_matrix(DART_UZAYI_S3.to_unit(x)) @ self.coef

    pb = grid_posterior(DART_UZAYI_S3, [_V(v1.coef), _V(v2.coef)], d, [s1, s2], n_grid=n)
    assert np.allclose(pk.p, pb.p, atol=1e-12)


def test_ayni_bilgiyi_IKI_KEZ_saymak_posterioru_yapay_daraltiyor():
    """Tam ilişkili iki kopya: kovaryanslı genişlik ≈ tek gözlem; bağımsız dar."""
    n = 32
    e = np.linspace(0, 1, n)
    izg = np.meshgrid(e, e, e, indexing="ij")
    u1 = izg[1].ravel()
    s = 0.1
    tek = grid_posterior_kovaryans(DART_UZAYI_S3, u1[:, None], [0.5], [[s**2]], n)
    iki = np.column_stack([u1, u1])
    kov_tam = np.array([[s**2, 0.999 * s**2], [0.999 * s**2, s**2]])
    tam = grid_posterior_kovaryans(DART_UZAYI_S3, iki, [0.5, 0.5], kov_tam, n)
    bag = grid_posterior_kovaryans(DART_UZAYI_S3, iki, [0.5, 0.5], np.diag([s**2, s**2]), n)
    assert tam.width_u[1] == pytest.approx(tek.width_u[1], rel=0.02)
    assert bag.width_u[1] < 0.8 * tek.width_u[1]


def test_tekil_kovaryans_ADIYLA_duser():
    with pytest.raises(ValueError, match="pozitif tanımlı"):
        grid_posterior_kovaryans(DART_UZAYI_S3, np.zeros((8**3, 2)), [0, 0],
                                 [[1.0, 1.0], [1.0, 1.0 - 1e-17]], 8)


def test_UC_eksene_bagli_sentetik_veri_UC_EKSEN_COZULUYOR():
    kayit = _kayitlar({"d_merkez": lambda u: u[0],
                       "R_krater": lambda u: u[1] + 0.2 * u[0],
                       "dV_sikisma": lambda u: u[2] - 0.3 * u[1] ** 2}, gurultu=0.03)
    out = pr.rapor(kayit, None, n_grid=24)
    assert out["secilen"] == ["d_merkez", "R_krater", "dV_sikisma"]
    for ad, e in out["eksen"].items():
        assert e["karar"].startswith("COZULUYOR"), (ad, e)
    assert out["gurultu_tepkisi"]["tepkili"]
    assert out["genel"] == "UC EKSEN COZULUYOR"


def test_yalniz_Y0a_bagli_veri_TEK_EKSEN_ve_digerleri_BILGI_YOK():
    kayit = _kayitlar({"d_merkez": lambda u: 0.8 * u[1],
                       "R_krater": lambda u: -0.5 * u[1] + 0.2 * u[1] ** 2}, gurultu=0.03)
    out = pr.rapor(kayit, None, n_grid=24)
    e = out["eksen"]
    assert e["log10_Y0"]["karar"].startswith("COZULUYOR")
    assert e["blok_alpha0"]["karar"] == "BILGI YOK"
    assert e["blok_kesri"]["karar"] == "BILGI YOK"
    assert out["genel"] == "TEK EKSEN COZULUYOR"


def test_N_AYIRT_ETMIYOR_dediyse_gozlenebilir_SECILMEZ():
    kayit = _kayitlar({"d_merkez": lambda u: u[1], "R_krater": lambda u: u[0]}, 0.03)
    s_n = {"gozlem": {"d_merkez": {"karar": "AYIRT EDIYOR"},
                      "R_krater": {"karar": "AYIRT ETMIYOR"}}}
    sec, tani = pr.gozlem_sec(kayit, s_n)
    assert sec == ["d_merkez"]
    assert tani["R_krater"]["neden"] == "N AYIRT ETMIYOR"
    assert tani["V_krater"]["neden"] == "SONLU DEGIL"


def test_gercegi_icermeyen_dar_araliklar_ASIRI_GUVENLI():
    vakalar = [{"gercek_u": [0.5, 0.5, 0.5], "carpan": {1.0: {
        "hdi68": [[0.6, 0.62]] * 3, "hdi95": [[0.58, 0.64]] * 3,
        "genislik": [0.02] * 3, "cakili": [False] * 3}}} for _ in range(10)]
    y = pr.eksen_yargisi(vakalar, 0)
    assert y["kapsama68"] == 0.0 and y["karar"] == "ASIRI GUVENLI"
    tepki = {"tepkili": True}
    assert pr.genel_yargi({"a": y}, tepki) == "KALIBRASYON DUSTU"


def test_tepkisiz_gurultu_yargiyi_GECERSIZ_kilar():
    e = {"a": {"karar": "COZULUYOR"}, "b": {"karar": "BILGI YOK"}}
    assert pr.genel_yargi(e, {"tepkili": False}).endswith("GECERSIZ")


def test_donusum_tabanlari():
    assert pr.donustur("M_ejekta", 0.0) == pytest.approx(-3.0)
    assert pr.donustur("beta_eksi_1", -0.01) == pytest.approx(-4.0)
    assert pr.donustur("d_merkez", -0.2) == -0.2
    assert np.isnan(pr.donustur("V_krater", float("nan")))


def test_esikler_belgede_ayni():
    m = (_KOK / "docs" / "truba" / "PROTOKOL-P-KALIBRASYON.md").read_text(encoding="utf-8")
    assert (pr.KAPSAMA_ALT, pr.KAPSAMA_UST) == (0.50, 0.87)
    assert pr.GENISLIK_ESIGI == pytest.approx(0.34)
    assert (pr.KUCULTME, pr.Q2_ESIGI, pr.SONLU_EN_AZ) == (0.3, 0.5, 0.90)
    for parca in ("`0,50`", "`0,87`", "`0,34`", "`λ = 0,3`", "`q2 > 0,5`",
                  "`%90`", "`1×, 2×, 4×`"):
        assert parca in m, parca
