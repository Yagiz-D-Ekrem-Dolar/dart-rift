"""Gözemli seçimi — üç parametre için üç bağımsız kısıt araması.

Sınavlar **kurgulanmış** Jakobyenlerle çalışır: cevabı bildiğimiz
durumlarda seçicinin doğru alt kümeyi bulduğu, grup kısıtına uyduğu ve
gözlenmeyeni seçmediği kilitlenir.
"""
from __future__ import annotations

import numpy as np
import pytest

from dartrift.inference import gozlemli_secimi as GS
from dartrift.inference.design import DART_UZAYI_S4
from dartrift.inference.tanimlanabilirlik import FISHER_ESIGI
from dartrift.observables.aday_gozlemliler import Aday


def _aday(ad, grup, gozlenen=True):
    return Aday(ad, f"{ad} aciklama", gozlenen, f"{ad} kaynagi", "-", grup)


# ----------------------------------------------------------- kosegen kovaryans
def test_kosegen_kovaryans_ve_denetimi():
    K = GS.kosegen_kovaryans([0.1, 0.2])
    assert np.allclose(K, np.diag([0.01, 0.04]))
    for kotu in ([], [0.0, 1.0], [-1.0], [np.nan]):
        with pytest.raises(ValueError, match="sigma"):
            GS.kosegen_kovaryans(kotu)


# ----------------------------------------------------------- alt kume degeri
def test_alt_kume_degeri_tam_rankta_uc_yon_veriyor():
    """Birim Jakobyen + küçük gürültü → üç yön de öğrenilir."""
    J = np.eye(3) * 10.0
    kov = GS.kosegen_kovaryans([1.0, 1.0, 1.0])
    d = GS.alt_kume_degeri(J, kov, [0, 1, 2])
    assert d["ogrenilen"] == 3 and d["ust_sinir"] == 3
    assert d["en_kucuk_ozdeger"] == pytest.approx(100.0)
    # sd_oran = sqrt(ONSEL_VARYANS^-1 / (lam + ONSEL_VARYANS^-1))
    #         = sqrt(12 / (100 + 12)) = 0,327
    assert all(s == pytest.approx(0.3273, abs=1e-3) for s in d["sd_oran"])
    with pytest.raises(ValueError, match="bos alt kume"):
        GS.alt_kume_degeri(J, kov, [])


def test_alt_kume_degeri_iki_satirda_ucuncu_ozdeger_SIFIR():
    """`k = 2` ile üçüncü yön tam sıfır — aritmetiğin kendisi."""
    J = np.array([[10.0, 0.0, 0.0], [0.0, 10.0, 0.0]])
    d = GS.alt_kume_degeri(J, GS.kosegen_kovaryans([1.0, 1.0]), [0, 1])
    assert d["ust_sinir"] == 2
    assert min(d["ozdegerler"]) == pytest.approx(0.0, abs=1e-9)
    assert max(d["sd_oran"]) == pytest.approx(1.0, abs=1e-6)   # onselden farksiz


# ----------------------------------------------------------- grup kisiti
def test_ayni_gruptan_IKI_aday_secilemez():
    """`e_hiz` ile `v_p50` aynı ölçümün özeti — birlikte seçilmemeli."""
    adaylar = [_aday("beta", "periyot"), _aday("e_hiz", "hiz_dagilimi"),
               _aday("v_p50", "hiz_dagilimi")]
    # e_hiz ve v_p50 ucuncu yone cok guclu; beta zayif. Acgozlu bir secici
    # ikisini birlikte alirdi -- grup kisiti engellemeli.
    J = np.array([[5.0, 0.0, 0.0], [0.0, 0.0, 30.0], [0.0, 0.0, 29.0]])
    kov = GS.kosegen_kovaryans([1.0, 1.0, 1.0])
    r = GS.grup_kisitli_secim(adaylar, J, kov, k=2)
    assert r["genel"] == "SECILDI"
    assert set(r["gruplar"]) == {"periyot", "hiz_dagilimi"}
    assert len(set(r["gruplar"])) == 2


def test_gozlenmeyen_aday_SECILEMEZ():
    adaylar = [_aday("beta", "periyot"), _aday("M", "kutle"),
               _aday("kos_ort", "koni", gozlenen=False)]
    # kos_ort ucuncu yonu tek basina cozuyor ama GOZLENMIYOR
    J = np.array([[10.0, 0.0, 0.0], [0.0, 10.0, 0.0], [0.0, 0.0, 50.0]])
    kov = GS.kosegen_kovaryans([1.0, 1.0, 1.0])
    r = GS.grup_kisitli_secim(adaylar, J, kov, k=3)
    assert r["genel"] == "YETERLI GOZLENEN GRUP YOK"
    assert r["acik_grup"] == ["kutle", "periyot"]
    assert r["en_iyi"] is None


def test_E_eniyi_en_kucuk_ozdegeri_buyuteni_seciyor():
    """İki aday aynı toplamı veriyor ama biri yönleri **dengeli** kaplıyor."""
    adaylar = [_aday("a", "g1"), _aday("b", "g2"), _aday("c", "g3")]
    # a+b: ozdegerler (100, 100, 0) -> en kucuk 0
    # a+c: ozdegerler (100, 0, 100)? c ucuncu yonde -> a+c de 0 verir
    # a+b+c: ucu de -> en kucuk 100
    J = np.array([[10.0, 0.0, 0.0], [0.0, 10.0, 0.0], [0.0, 0.0, 10.0]])
    kov = GS.kosegen_kovaryans([1.0, 1.0, 1.0])
    r3 = GS.grup_kisitli_secim(adaylar, J, kov, k=3)
    assert r3["en_iyi"]["en_kucuk_ozdeger"] == pytest.approx(100.0)
    r2 = GS.grup_kisitli_secim(adaylar, J, kov, k=2)
    assert r2["en_iyi"]["en_kucuk_ozdeger"] == pytest.approx(0.0, abs=1e-9)


def test_grup_kisitli_secim_denetimleri():
    adaylar = [_aday("a", "g1")]
    J = np.array([[1.0, 0.0, 0.0]])
    kov = GS.kosegen_kovaryans([1.0])
    with pytest.raises(ValueError, match="k >= 1"):
        GS.grup_kisitli_secim(adaylar, J, kov, k=0)
    with pytest.raises(ValueError, match="Jakobyen satiri"):
        GS.grup_kisitli_secim(adaylar * 2, J, kov, k=1)


# ----------------------------------------------------------- rapor
def test_rapor_UC_YON_DA_OGRENILIYOR():
    adaylar = [_aday("beta", "periyot"), _aday("M", "kutle"),
               _aday("e_hiz", "hiz_dagilimi")]
    J = np.eye(3) * 10.0
    kov = GS.kosegen_kovaryans([1.0, 1.0, 1.0])
    r = GS.secim_raporu(adaylar, J, kov, d_parametre=3)
    assert r["genel"] == "UC YON DA OGRENILIYOR"
    assert r["ogrenilen"] == 3
    assert sorted(r["secilen"]) == ["M", "beta", "e_hiz"]
    assert r["en_kucuk_ozdeger"] > FISHER_ESIGI
    assert r["en_zayif_sd_oran"] < 0.5
    assert 1 in r["basamaklar"] and 3 in r["basamaklar"]
    assert "TEK noktada" in r["uyari"]                 # yerellik uyarisi yazili


def test_rapor_ucuncu_gozlemli_ZAYIFSA_yetmiyor_diyor():
    """Üçüncü aday var ama eşiğin altında → dürüstçe "yetmiyor"."""
    adaylar = [_aday("beta", "periyot"), _aday("M", "kutle"),
               _aday("e_hiz", "hiz_dagilimi")]
    J = np.array([[10.0, 0.0, 0.0], [0.0, 10.0, 0.0], [0.0, 0.0, 1.0]])
    kov = GS.kosegen_kovaryans([1.0, 1.0, 1.0])
    r = GS.secim_raporu(adaylar, J, kov, d_parametre=3)
    assert r["ogrenilen"] == 2
    assert "YETMIYOR" in r["genel"]
    assert r["en_kucuk_ozdeger"] == pytest.approx(1.0)
    assert r["en_zayif_sd_oran"] > 0.9                 # ucuncu yon onsel-baskin


def test_rapor_gozlenen_grup_yetmezse_soyluyor():
    adaylar = [_aday("beta", "periyot"), _aday("M", "kutle")]
    J = np.array([[10.0, 0.0, 0.0], [0.0, 10.0, 0.0]])
    r = GS.secim_raporu(adaylar, J, GS.kosegen_kovaryans([1.0, 1.0]),
                        d_parametre=3)
    assert r["genel"] == "YETERLI GOZLENEN GRUP YOK"
    with pytest.raises(ValueError, match="d_parametre"):
        GS.secim_raporu(adaylar, J, GS.kosegen_kovaryans([1.0, 1.0]),
                        d_parametre=0)


# ----------------------------------------------------------- Jakobyen
def test_aday_jakobyeni_bilinen_dogrusal_modeli_geri_veriyor():
    """`y = a·u` kurulursa Jakobyen `a`'yı (birim küpte) vermeli."""
    uzay = DART_UZAYI_S4
    rng = np.random.default_rng(3)
    U = rng.random((60, 3))
    X = uzay.from_unit(U)
    kats = {"y1": np.array([2.0, -3.0, 0.5]), "y2": np.array([0.0, 1.0, 4.0])}
    Y = {ad: U @ k for ad, k in kats.items()}
    J, adlar = GS.aday_jakobyeni(uzay, X, Y, u0=np.full(3, 0.5),
                                 adlar=["y1", "y2"])
    assert adlar == ["y1", "y2"] and J.shape == (2, 3)
    for i, ad in enumerate(adlar):
        assert np.allclose(J[i], kats[ad], atol=2e-2), (ad, J[i])


def test_aday_jakobyeni_log_al_ve_denetimler():
    uzay = DART_UZAYI_S4
    rng = np.random.default_rng(5)
    U = rng.random((40, 3))
    X = uzay.from_unit(U)
    Y = {"m": 10.0 ** (1.0 + 2.0 * U[:, 1])}           # log10(m) = 1 + 2 u1
    J, _ = GS.aday_jakobyeni(uzay, X, Y, u0=np.full(3, 0.5),
                             log_al={"m": True})
    assert J[0, 1] == pytest.approx(2.0, abs=0.05)
    with pytest.raises(ValueError, match="pozitif olmayan"):
        GS.aday_jakobyeni(uzay, X, {"m": -Y["m"]}, u0=np.full(3, 0.5),
                          log_al={"m": True})
    with pytest.raises(ValueError, match="sonlu olmayan"):
        bozuk = Y["m"].copy()
        bozuk[0] = np.nan
        GS.aday_jakobyeni(uzay, X, {"m": bozuk}, u0=np.full(3, 0.5))
    with pytest.raises(ValueError, match="tasarim noktasi"):
        GS.aday_jakobyeni(uzay, X, {"m": Y["m"][:5]}, u0=np.full(3, 0.5))
    with pytest.raises(ValueError, match="birim kupte"):
        GS.aday_jakobyeni(uzay, X, Y, u0=np.array([0.5, 0.5, 1.5]))
    with pytest.raises(ValueError, match="en az bir aday"):
        GS.aday_jakobyeni(uzay, X, {}, u0=np.full(3, 0.5))


# --------------------------------------------- gercek kutukle yapisal sinav
def test_GERCEK_kutukte_uc_acik_grup_var():
    """Koni (A95) kapalı olsa bile üç parametre için sayı **tam tutuyor**."""
    from dartrift.observables.aday_gozlemliler import ADAYLAR
    acik = {a.karsilik_grubu for a in ADAYLAR if a.gozlenen}
    assert acik == {"periyot_degisimi", "ejekta_kutlesi", "ejekta_hiz_dagilimi"}
    assert len(acik) == 3                               # d = 3 icin yeterli SAYI
    # koni grubu VAR ama hicbiri gozlenen degil
    koni = [a for a in ADAYLAR if a.karsilik_grubu == "ejekta_konisi"]
    assert koni and not any(a.gozlenen for a in koni)
    assert all("A95" in a.kaynak for a in koni)
