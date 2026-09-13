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


def test_grup_loo_artiklari_elle_BIRAK_BIR_GRUP_ile_ayni():
    rng = np.random.default_rng(5)
    th = _tasarim(15)
    X = np.vstack([th, th])
    grup = np.concatenate([np.arange(15), np.arange(15)])
    y = DART_UZAYI_S3.to_unit(X)[:, 0] ** 2 + rng.normal(0, 0.1, 30)
    e = loo_artiklari(DART_UZAYI_S3, X, y, gruplar=grup)
    for g in (0, 9):
        k = grup != g
        v = fit_surrogate(DART_UZAYI_S3, X[k], y[k])
        for i in np.flatnonzero(~k):
            assert e[i] == pytest.approx(y[i] - v.predict(X[i:i + 1])[0], rel=1e-7, abs=1e-9)


def test_ikiz_tohum_egitimde_kalinca_tek_LOO_artigi_KUCUK_kaliyor():
    """Neden bırak-bir-grup: gerçekleme gürültüsü baskınken tek LOO yarıya iner."""
    rng = np.random.default_rng(8)
    th = _tasarim(24)
    X = np.vstack([th, th])
    grup = np.concatenate([np.arange(24), np.arange(24)])
    y = DART_UZAYI_S3.to_unit(X)[:, 1] + rng.normal(0, 0.1, 48)
    tek = loo_artiklari(DART_UZAYI_S3, X, y)
    grp = loo_artiklari(DART_UZAYI_S3, X, y, gruplar=grup)
    assert np.std(grp) > 1.15 * np.std(tek)


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


def test_DIS_ORNEKLEM_ikinci_tasarimda_ayni_yargiyi_veriyor():
    f = {"d_merkez": lambda u: u[0], "R_krater": lambda u: u[1] + 0.2 * u[0],
         "dV_sikisma": lambda u: u[2] - 0.3 * u[1] ** 2}
    egit = _kayitlar(f, 0.03, tohum=1)
    test = _kayitlar(f, 0.03, tohum=2)
    th2 = lhs_design(DART_UZAYI_S3, 24, root_seed=20260914)
    rng = np.random.default_rng(100)
    for i, k in enumerate(test):
        k["theta"] = th2[i % 24]
        u = DART_UZAYI_S3.to_unit(th2[i % 24][None, :])[0]
        for g, fn in f.items():
            k[g] = float(fn(u) + rng.normal(0, 0.03))
    out = pr.rapor(egit, None, n_grid=24, test_kayitlar=test)
    d = out["dis_ornek"]
    assert d["n_theta"] == 24 and d["n_kosu"] == 48
    assert d["genel"] == "UC EKSEN COZULUYOR", d["eksen"]


def test_DIS_ORNEKLEM_gurultu_modeli_uyusmazligini_YAKALIYOR():
    """Sınama gürültüsü gözlenebilirler arasında TAM ilişkili, eğitimde
    bağımsız: kovaryans modeli yanlış → aralıklar yalan → KALIBRASYON DUSTU.
    (Bu sınav ilk yazımda kazara bulundu: sınav verisinin gürültüsü hatalı
    üretilmişti ve yöntem bunu yakaladı.)"""
    f = {"d_merkez": lambda u: u[0], "R_krater": lambda u: u[1] + 0.2 * u[0],
         "dV_sikisma": lambda u: u[2] - 0.3 * u[1] ** 2}
    egit = _kayitlar(f, 0.03, tohum=1)
    test = _kayitlar(f, 0.0, tohum=2)
    th2 = lhs_design(DART_UZAYI_S3, 24, root_seed=20260914)
    for i, k in enumerate(test):
        k["theta"] = th2[i % 24]
        u = DART_UZAYI_S3.to_unit(th2[i % 24][None, :])[0]
        ortak = np.random.default_rng(100 + i).normal(0, 0.03)
        for g, fn in f.items():
            k[g] = float(fn(u) + ortak)
    out = pr.rapor(egit, None, n_grid=24, test_kayitlar=test)
    assert out["dis_ornek"]["genel"] == "KALIBRASYON DUSTU"


def test_ESIK_bicimli_veride_GP_polinomun_goremedigi_ekseni_cozuyor():
    """G1'in ölçtüğü biçim: `Y₀`'da plato + dik düşüş. Polinom `log10_Y0`'ı
    çözemiyor; GP çözüyor — ve ikisi de kalibre (aşırı güvenli değil)."""
    f = {"d_merkez": lambda u: 0.35 / (1 + np.exp((u[1] - 0.6) / 0.06)) + 0.2 * u[0],
         "R_krater": lambda u: u[2] + 0.1 * u[0]}
    kayit = _kayitlar(f, 0.02)
    kuad = pr.rapor(kayit, None, n_grid=24)
    gp = pr.rapor(kayit, None, n_grid=24, vekil="gp")
    assert kuad["eksen"]["log10_Y0"]["karar"] == "BILGI YOK"
    assert gp["eksen"]["log10_Y0"]["karar"].startswith("COZULUYOR")
    assert "KALIBRASYON" not in kuad["genel"] and "KALIBRASYON" not in gp["genel"]


def test_P_v3_kfold_artiklari_ELLE_ile_ayni_ve_ikiz_tohum_ayni_katta():
    th = _tasarim(24)
    X = np.vstack([th, th])
    grup = pr._gruplar(X)
    kat = pr.kat_ata(grup)
    assert np.array_equal(kat[:24], kat[24:])          # ikiz tohum ayrilmiyor
    assert sorted(np.bincount(kat).tolist()) == [12, 12, 12, 12]
    rng = np.random.default_rng(2)
    y = DART_UZAYI_S3.to_unit(X)[:, 1] ** 2 + rng.normal(0, 0.05, 48)
    e = pr.kfold_artiklari(X, y, grup)
    t = kat == 1
    v = fit_surrogate(DART_UZAYI_S3, X[~t], y[~t])
    np.testing.assert_allclose(e[t], y[t] - v.predict(X[t]), rtol=1e-10, atol=1e-12)


def test_P_v3_kfold_artigi_LOO_dan_kucuk_degil_ve_rapor_calisiyor():
    kayit = _kayitlar({"d_merkez": lambda u: u[0] + 0.5 * np.sin(6 * u[1]),
                       "R_krater": lambda u: u[1] + 0.2 * u[0] ** 3,
                       "dV_sikisma": lambda u: u[2] - 0.3 * u[1] ** 2}, gurultu=0.03)
    sec = ["d_merkez", "R_krater", "dV_sikisma"]
    X, Y = pr._matrisler(kayit, sec)
    grup = pr._gruplar(X)
    e_loo = loo_artiklari(DART_UZAYI_S3, X, Y[:, 0], gruplar=grup)
    e_kf = pr.kfold_artiklari(X, Y[:, 0], grup)
    assert np.std(e_kf) >= 0.95 * np.std(e_loo)
    out = pr.rapor(kayit, None, n_grid=20, artik="kfold4")
    assert out["artik"] == "kfold4" and "genel" in out


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


def test_yol_secim_kurali_belgede_ve_koda_bagli():
    """§4c'nin kuralı `yol_sec`'te; belge ile kod ayrışamaz."""
    m = (_KOK / "docs" / "truba" / "PROTOKOL-P-KALIBRASYON.md").read_text(encoding="utf-8")
    assert "dış örneklemde daha çok ekseni çözen" in m
    assert "Eşitlikte kuadratik esastır" in m
    ok = {"genel": "TEK EKSEN COZULUYOR",
          "eksen": {"a": {"karar": "COZULUYOR"}, "b": {"karar": "BILGI YOK"}}}
    iki = {"genel": "IKI EKSEN COZULUYOR",
           "eksen": {"a": {"karar": "COZULUYOR"}, "b": {"karar": "COZULUYOR (TEMKINLI)"}}}
    dus = {"genel": "KALIBRASYON DUSTU", "eksen": {"a": {"karar": "ASIRI GUVENLI"}}}
    tepkisiz = {"genel": "IKI EKSEN COZULUYOR -- GURULTU TEPKISIZ, GECERSIZ",
                "eksen": {"a": {"karar": "COZULUYOR"}, "b": {"karar": "COZULUYOR"}}}
    assert pr.yol_sec(ok, iki)["esas"] == "gp"
    assert pr.yol_sec(iki, ok)["esas"] == "kuadratik"
    assert pr.yol_sec(ok, ok)["esas"] == "kuadratik"
    assert pr.yol_sec(dus, ok)["esas"] == "gp"
    assert pr.yol_sec(ok, tepkisiz)["esas"] == "kuadratik"
    assert pr.yol_sec(dus, dus)["genel"] == "KALIBRASYON DUSTU"
