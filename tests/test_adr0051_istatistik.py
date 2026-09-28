"""ADR-0051 — kalibrasyon (SBC/PIT), GP varyans kalibrasyonu, tanımlanabilirlik,
kaynaklı model eksikliği, Daly 2023 sabitleri."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pytest

from dartrift.inference import gp_vekil as G
from dartrift.inference import kalibrasyon as K
from dartrift.inference import tanimlanabilirlik as T
from dartrift.inference import tarih_esleme as H
from dartrift.inference.design import ParamSpace
from dartrift.inference.posterior import grid_posterior
from dartrift.observables import dart_gozlemleri as D

UZAY = ParamSpace(names=("a", "b"), lo=(0.0, 0.0), hi=(1.0, 1.0), log=(False, False))


@dataclass
class _Vekil:
    """`predict` + `sigma` sunan en küçük vekil (doğrusal birleşim)."""

    w: tuple
    kayma: float = 0.0
    sigma: float = 0.0

    def predict(self, x):
        x = np.atleast_2d(x)
        return x @ np.asarray(self.w, float) + self.kayma


# ------------------------------------------------------------ kalibrasyon
def test_cdf_duzgun_ve_dogrusal_yogunlukta_TAM():
    n = 11
    assert K._cdf_parcali_dogrusal(np.ones(n), 0.37) == pytest.approx(0.37, abs=1e-12)
    f = np.linspace(0.0, 1.0, n)                      # f(u) = u -> F = u^2
    for u in (0.0, 0.15, 0.5, 0.93, 1.0):
        assert K._cdf_parcali_dogrusal(f, u) == pytest.approx(u * u, abs=1e-12)


def test_pit_merkez_ve_aralik_disi():
    post = grid_posterior(UZAY, [_Vekil((1.0, 0.0)), _Vekil((0.0, 1.0))],
                          [0.5, 0.5], 0.05, n_grid=61)
    assert K.pit_degeri(post, 0, 0.5) == pytest.approx(0.5, abs=1e-9)
    assert K.pit_degeri(post, 0, -0.2) == 0.0 and K.pit_degeri(post, 1, 1.3) == 1.0


def test_kapsama_ve_ks_duzgun_dizide():
    pit = (np.arange(1000) + 0.5) / 1000
    kap = {k["nominal"]: k["deneysel"] for k in K.kapsama_egrisi(pit)}
    assert kap[0.68] == pytest.approx(0.68, abs=2e-3)
    D_, p = K.ks_duzgunluk(pit)
    assert D_ < 1e-3 and p > 0.99
    assert K.pit_tanisi(pit)["tani"] == "KALIBRE"


@pytest.mark.parametrize("pit_uret,tani", [
    (lambda r: np.where(r.random(400) < 0.5, r.random(400) * 0.1, 0.9 + r.random(400) * 0.1),
     "ASIRI GUVENLI"),
    (lambda r: 0.4 + 0.2 * r.random(400), "ASIRI TEMKINLI"),
    (lambda r: r.random(400) ** 2, "YANLI")])
def test_bicim_tanilari(pit_uret, tani):
    assert tani in K.pit_tanisi(pit_uret(np.random.default_rng(3)))["tani"]


def _sbc(sig_gercek, sig_cikarim, kayma=0.0, n=200):
    vek = [_Vekil((1.0, 0.5)), _Vekil((0.5, -1.0))]
    cik = [_Vekil((1.0, 0.5), kayma), _Vekil((0.5, -1.0), kayma)]

    def uret(x, rng):
        return np.array([v.predict(x)[0] for v in vek]) + sig_gercek * rng.standard_normal(2)

    def cikarim(y):
        return grid_posterior(UZAY, cik, y, sig_cikarim, n_grid=61)

    return K.sbc_calistir(UZAY, uret, cikarim, n, tohum=20260919)


def test_SBC_dogru_model_KALIBRE():
    s = _sbc(0.05, 0.05)
    assert s.genel == "KALIBRE", s.tanilar
    assert s.pit.shape == (200, 2) and s.gercekler.shape == (200, 2)


def test_SBC_dar_gurultu_ASIRI_GUVENLI_genis_ASIRI_TEMKINLI():
    assert "ASIRI GUVENLI" in _sbc(0.05, 0.015).genel
    assert "ASIRI TEMKINLI" in _sbc(0.05, 0.2).genel


def test_SBC_kayik_vekil_YANLI():
    assert "YANLI" in _sbc(0.05, 0.05, kayma=0.06).genel


def test_SBC_belirlenimci_ve_az_tekrar_REDDEDILIR():
    a, b = _sbc(0.05, 0.05, n=20), _sbc(0.05, 0.05, n=20)
    assert np.array_equal(a.pit, b.pit)
    with pytest.raises(ValueError):
        K.sbc_calistir(UZAY, None, None, 5, tohum=1)


# ------------------------------------------------ GP varyans kalibrasyonu
def _gp_sabit(space, x, y, logp):
    """Hiperparametreleri SABIT bir GP (gp_uydur'un son adimi)."""
    U = space.to_unit(x)
    ort, olc = float(y.mean()), float(y.std())
    ys = (y - ort) / olc
    s2, ell, n2 = np.exp(logp[0]), np.exp(logp[1:-1]), np.exp(logp[-1])
    Kk = G._cekirdek(U, U, s2, ell) + (n2 + 1e-10) * np.eye(len(U))
    L = np.linalg.cholesky(Kk)
    alfa = np.linalg.solve(L.T, np.linalg.solve(L, ys))
    return G.GpVekil(space=space, U=U, y_ort=ort, y_olcek=olc, logp=np.asarray(logp),
                     alfa=alfa, L=L, nlml=0.0)


def _veri(n=30, tohum=4):
    r = np.random.default_rng(tohum)
    x = r.random((n, 2))
    y = np.sin(6.0 * x[:, 0]) + 0.5 * x[:, 1] + 0.05 * r.standard_normal(n)
    return x, y


def test_varyans_carpani_varsayilan_BIT_AYNI_ve_olcek_yalniz_varyansi_carpar():
    x, y = _veri()
    v = G.gp_uydur(UZAY, x, y)
    assert v.varyans_carpani == 1.0
    Uy = np.random.default_rng(5).random((7, 2))
    m0, s0 = v.predict_u(Uy)
    from dataclasses import replace
    m1, s1 = replace(v, varyans_carpani=2.5).predict_u(Uy)
    assert np.array_equal(m0, m1)
    np.testing.assert_allclose(s1, 2.5 * s0, rtol=1e-14)


def test_CV_olcegi_KABA_KUVVET_birak_bir_disari_ile_ayni():
    x, y = _veri()
    logp = np.array([0.0, np.log(0.4), np.log(0.8), np.log(1e-2)])
    v = _gp_sabit(UZAY, x, y, logp)
    _, bil = G.gp_varyans_kalibre(v, y, np.arange(len(y)), yalniz_buyut=False)
    # kaba kuvvet: noktayi cikar, AYNI hiperparametrelerle (ve ayni y olcegiyle) ongor
    ys = (y - v.y_ort) / v.y_olcek
    U = UZAY.to_unit(x)
    s2, ell, n2 = np.exp(logp[0]), np.exp(logp[1:-1]), np.exp(logp[-1])
    z2 = []
    for i in range(len(y)):
        m = np.arange(len(y)) != i
        Kk = G._cekirdek(U[m], U[m], s2, ell) + (n2 + 1e-10) * np.eye(m.sum())
        ks = G._cekirdek(U[i:i + 1], U[m], s2, ell)[0]
        mu = ks @ np.linalg.solve(Kk, ys[m])
        var = s2 + n2 + 1e-10 - ks @ np.linalg.solve(Kk, ks)
        z2.append((ys[i] - mu) ** 2 / var)
    assert bil["k_cv"] == pytest.approx(float(np.mean(z2)), rel=1e-8)


def test_yanlis_belirlenmis_GP_ASIRI_GUVENLI_olcek_BUYUTUR_ve_kucultmez():
    x, y = _veri()
    # cok uzun uzunluk olcegi + kucuk varyans: sin(6x)'i gormez, emin konusur
    v = _gp_sabit(UZAY, x, y, np.array([np.log(0.05), np.log(3.0), np.log(3.0), np.log(1e-3)]))
    v2, bil = G.gp_varyans_kalibre(v, y, np.arange(len(y)))
    assert bil["k_cv"] > 3.0 and v2.varyans_carpani == pytest.approx(bil["k_cv"])
    # iyi uydurulmus GP'de k < 1 olsa bile varsayilan KUCULTMEZ
    w = G.gp_uydur(UZAY, x, y)
    w2, bil2 = G.gp_varyans_kalibre(w, y, np.arange(len(y)))
    assert w2.varyans_carpani == max(1.0, bil2["k_cv"])


# ------------------------------------------------------ tanımlanabilirlik
def _post(vekiller, veri, sig=0.03, n=61):
    return grid_posterior(UZAY, vekiller, veri, sig, n_grid=n)


def test_TEK_gozlem_toplami_ogrenir_eksenleri_OGRENMEZ():
    post = _post([_Vekil((1.0, 1.0))], [1.0])
    oz = T.tanimlanabilirlik_ozeti(post)
    for s in oz["eksenler"]:
        assert s["daralma_sinifi"] == "ONSEL BASKIN" and s["profil"] == "TANIMLANAMAZ"
        assert s["genel"] == "TANIMLANAMAZ"
    yon = np.abs(np.asarray(oz["yonler"]["en_iyi_yon"]))
    np.testing.assert_allclose(yon, [2 ** -0.5, 2 ** -0.5], atol=0.02)
    assert oz["yonler"]["en_iyi_sd_oran"] < 0.3


def test_IKI_gozlem_iki_ekseni_de_OGRENIR():
    post = _post([_Vekil((1.0, 1.0)), _Vekil((1.0, -1.0))], [1.0, 0.2])
    for s in T.tanimlanabilirlik_ozeti(post)["eksenler"]:
        assert s["genel"] == "TANIMLANABILIR", s


def test_profil_TEK_YONLU_ust_sinir():
    # gozlem yalniz 'a'nin KUCUK oldugunu soyluyor: a ~ 0 kenarinda
    post = _post([_Vekil((1.0, 0.0))], [-0.2], sig=0.1)
    assert T.profil_tanisi(post, 0)["sinif"] == "TEK YONLU"


def test_fisher_ust_sinir_ve_yon_sayisi():
    f1 = T.fisher_yonleri([[1.0, 1.0, 0.0]], [[0.01 ** 2]])
    assert f1["ust_sinir"] == 1 and f1["ogrenilen_yon_sayisi"] == 1
    np.testing.assert_allclose(np.abs(f1["yonler"][0]), [2 ** -0.5, 2 ** -0.5, 0.0], atol=1e-9)
    f3 = T.fisher_yonleri(np.eye(3), np.eye(3) * 0.01 ** 2)
    assert f3["ogrenilen_yon_sayisi"] == 3
    zayif = T.fisher_yonleri([[0.01, 0.0]], [[1.0]])       # duyarsiz gozlem
    assert zayif["ogrenilen_yon_sayisi"] == 0


def test_yerel_jakobyen_ic_ve_sinir():
    def f(u):
        return np.array([2.0 * u[0] + u[1] ** 2, u[0] * u[1]])

    J = T.yerel_jakobyen(f, [0.3, 0.6], adim=1e-4)
    np.testing.assert_allclose(J, [[2.0, 1.2], [0.6, 0.3]], atol=1e-6)
    J0 = T.yerel_jakobyen(f, [0.0, 1.0], adim=1e-4)          # tek yonlu fark
    np.testing.assert_allclose(J0, [[2.0, 2.0], [1.0, 0.0]], atol=1e-3)


# ------------------------------------------------ kaynaklı model eksikliği
def test_kaynakli_eksiklik_OLCULMEMIS_terimde_HATA():
    with pytest.raises(ValueError, match="OLCULMEDI"):
        H.model_eksikligi_kaynakli(2.0, ["cozunurluk_yakin"])
    with pytest.raises(ValueError):
        H.model_eksikligi_kaynakli(2.0, [])
    r = H.model_eksikligi_kaynakli(2.0, ["cozunurluk_uzak", "carpma_yeri"])
    assert r["sigma"] == pytest.approx(2.0 * np.hypot(0.004, 0.10))
    for ad, (_s, kaynak) in H.MODEL_EKSIKLIGI_KAYNAKLI.items():
        assert kaynak, ad                                   # her terimin kaynagi var


def test_kod_kiyasi_W2_sayilariyla():
    k = H.kod_kiyasi_olc([3.2953, 3.6669, 3.9920], [3.63, 4.18, 4.66])
    assert k == pytest.approx(0.158, abs=2e-3)


def test_cok_ciktili_uygunsuzluk_en_buyuk_ve_ikinci():
    m = np.array([[3.0, 1.6e7], [2.0, 4.0e7]])
    ii = H.uygunsuzluk_cok(m, [3.1, 1.6e7], [0.3, 0.5e7])
    np.testing.assert_allclose(ii, [1 / 3, 4.8])
    np.testing.assert_allclose(H.uygunsuzluk_cok(m, [3.1, 1.6e7], [0.3, 0.5e7], ikinci=True),
                               [0.0, 11 / 3])


# ----------------------------------------------------- Daly 2023 sabitleri
def test_daly2023_tablo1_tam_metin():
    assert D.CARPMA_HIZI.deger == 6144.9 and D.UZAY_ARACI_KUTLESI.deger == 579.4
    assert D.CARPMA_KACIKLIGI.deger == 25.0 and D.CARPMA_ACISI_DALY.deger == 17.0
    for g in (D.CARPMA_HIZI, D.UZAY_ARACI_KUTLESI, D.CARPMA_KACIKLIGI, D.CARPMA_ACISI_DALY):
        assert g.teyit == "tam_metin" and g in D.GOZLEMLER
    assert D.CARPMA_ACISI.deger == D.CARPMA_ACISI_DALY.deger     # arama ozeti teyit edildi
