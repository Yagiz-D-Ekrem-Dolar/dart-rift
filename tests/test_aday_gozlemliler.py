"""Aday gözlemliler — üç parametre denemesinin ölçüm tarafı.

Sınavlar fiziğin **değişmezlerini** kilitler: kaçış eşiği, ağırlıklı
yüzdelikler, dağılım eğiminin işareti, ve en önemlisi **çevrimdışı hesabın
koşunun kendi sayılarını yeniden üretmesi**.
"""
from __future__ import annotations

import numpy as np
import pytest

from dartrift.observables import aday_gozlemliler as AG
from dartrift.observables.ejekta_ayrismasi import ejekta_bilesenleri

EHAT = np.array([0.0, 0.0, -1.0])      # mermi -z'ye gidiyor -> ejekta +z


def _bulut(n=400, hiz=1.0, yarim_aci=40.0, tohum=11, egim=None):
    """**Temiz koni**: kutup açısı `[0, yarim_aci]` içinde, katı açıda düzgün.

    `cos θ ~ U[cos(yarim_aci), 1]` → koni içinde düzgün dağılım. Böylece
    `yarim_aci` küçüldükçe hem medyan açı hem açısal yayılım **tekdüze**
    küçülür; önceki (Gauss'u ezerek kurulan) fikstürde kuyruk yüzünden
    tekdüze değildi ve sınav haklı olarak düştü.

    `egim` verilirse hız dağılımı `v ~ U^(-1/egim)` ile güç yasası olur.
    """
    rng = np.random.default_rng(tohum)
    kos_max = np.cos(np.radians(float(yarim_aci)))
    kos = kos_max + (1.0 - kos_max) * rng.random(n)
    sin = np.sqrt(np.clip(1.0 - kos ** 2, 0.0, None))
    faz = 2.0 * np.pi * rng.random(n)
    yon = np.column_stack([sin * np.cos(faz), sin * np.sin(faz), kos])
    if egim is None:
        h = np.full(n, hiz)
    else:
        h = hiz * rng.random(n) ** (-1.0 / float(egim))
    return yon * h[:, None], np.full(n, 1.0e4)


# ------------------------------------------------------------ kutuk
def test_kutuk_kilitli_ve_gozlenen_bayraklari_durust():
    adlar = [a.ad for a in AG.ADAYLAR]
    assert adlar[:2] == ["beta", "M_kacan"]          # sira kilitli
    assert len(adlar) == len(set(adlar))             # ad tekrari yok
    d = {a.ad: a for a in AG.ADAYLAR}
    # Gozlemsel karsiligi OLANLAR
    assert d["beta"].gozlenen and d["M_kacan"].gozlenen
    assert d["e_hiz"].gozlenen                        # kutle-hiz dagilimi
    # A95'e takilanlar gozlenen SAYILMAZ
    for ad in ("kos_ort", "aci_p50", "aci_yayilim"):
        assert not d[ad].gozlenen, ad
        assert "A95" in d[ad].kaynak, ad
    # v_ort gozlenen DEGIL ve nicini yazili
    assert not d["v_ort"].gozlenen and "v*kos" in d["v_ort"].kaynak
    # e_hiz'in sayisi henuz kilitlenmedi -- bu ACIKCA yazili
    assert "sayisi henuz yok" in d["e_hiz"].kaynak
    for a in AG.ADAYLAR:
        assert a.aciklama and a.birim


def test_aday_kunyesi_bos_alani_ve_tutarsizligi_reddediyor():
    with pytest.raises(ValueError, match="zorunlu"):
        AG.Aday("", "x", True, "k", "-", "g")
    with pytest.raises(ValueError, match="zorunlu"):
        AG.Aday("x", "x", True, "", "-", "g")
    with pytest.raises(ValueError, match="zorunlu"):
        AG.Aday("x", "x", True, "k", "-", "")
    # gozlenen ama grubu 'gozlenemez' -> tutarsiz
    with pytest.raises(ValueError, match="gozlenemez"):
        AG.Aday("x", "x", True, "k", "-", "gozlenemez")
    # gozlenen DEGILSE 'gozlenemez' grubu serbest
    assert AG.Aday("x", "x", False, "k", "-", "gozlenemez").ad == "x"


# ------------------------------------------------------------ kacan maske
def test_kacis_esigi_ve_mermi_ayiklamasi():
    v, m = _bulut(hiz=1.0)
    kac, vv, mm, hiz = AG.kacan_maske(v, m, v_esc=0.5)
    assert kac.sum() == len(m) and np.allclose(hiz, 1.0)
    mk = np.zeros(len(m))
    mk[:50] = 1.0
    kac2, _, mm2, _ = AG.kacan_maske(v, m, v_esc=0.5, mermi_kesri=mk)
    assert kac2.sum() == len(m) - 50
    assert mm2.sum() < mm.sum()


def test_az_kacanda_REDDEDIYOR():
    v, m = _bulut(n=20, hiz=1.0)                     # 20 < EN_AZ_KACAN
    with pytest.raises(ValueError, match="gurultuden okunamaz"):
        AG.kacan_maske(v, m, v_esc=0.5)
    assert AG.EN_AZ_KACAN == 30


def test_kacan_maske_gecersiz_girdiler():
    v, m = _bulut()
    with pytest.raises(ValueError):
        AG.kacan_maske(v[:, :2], m, v_esc=0.5)
    with pytest.raises(ValueError):
        AG.kacan_maske(v, m, v_esc=0.0)
    with pytest.raises(ValueError):
        AG.kacan_maske(v, m, v_esc=0.5, mermi_kesri=np.zeros(7))
    bozuk = v.copy()
    bozuk[0, 0] = np.nan
    with pytest.raises(ValueError, match="sonlu"):
        AG.kacan_maske(bozuk, m, v_esc=0.5)


# ------------------------------------------------------------ yuzdelik
def test_agirlikli_yuzdelik_bilinen_cevabi_veriyor():
    x = np.array([1.0, 2.0, 3.0, 4.0])
    w = np.ones(4)
    # Tanim: kumulatif kutle kesri q'yu gectigi deger. Dort esit agirlikta
    # kum = [0,25 ; 0,50 ; 0,75 ; 1,00] oldugu icin q=0,5 TAM x=2,0'a denk.
    assert AG._agirlikli_yuzdelik(x, w, 0.5) == pytest.approx(2.0)
    # agirligi uca yiginca medyan oraya kayar
    w2 = np.array([1.0, 1.0, 1.0, 97.0])
    # kum = [0,01 ; 0,02 ; 0,03 ; 1,00] -> q=0,5 son aralikta,
    # 3 + (0,5-0,03)/(1,00-0,03) = 3,4845
    assert AG._agirlikli_yuzdelik(x, w2, 0.5) == pytest.approx(3.4845, abs=1e-3)


def test_agirlikli_yuzdelik_denetimleri():
    x, w = np.arange(5.0), np.ones(5)
    for q in (0.0, 1.0, -0.1, 1.5):
        with pytest.raises(ValueError, match="q"):
            AG._agirlikli_yuzdelik(x, w, q)
    with pytest.raises(ValueError):
        AG._agirlikli_yuzdelik(x, np.zeros(5), 0.5)
    with pytest.raises(ValueError):
        AG._agirlikli_yuzdelik(x, -np.ones(5), 0.5)
    with pytest.raises(ValueError):
        AG._agirlikli_yuzdelik(x, np.ones(4), 0.5)


# ------------------------------------------------------------ dagilim egimi
def test_dagilim_egimi_kurulan_guc_yasasini_buluyor():
    """`v ~ U^(−1/e)` ile kurulan buluttan `e` geri okunmalı."""
    for e_gercek in (1.0, 2.0):
        v, m = _bulut(n=4000, hiz=1.0, egim=e_gercek, tohum=5)
        hiz = np.linalg.norm(v, axis=1)
        e = AG._dagilim_egimi(hiz, m, v_esc=1.0, ust_carpan=30.0)
        assert e == pytest.approx(e_gercek, rel=0.25), (e_gercek, e)


def test_dagilim_egimi_dar_aralikta_REDDEDIYOR():
    v, m = _bulut(n=200, hiz=1.0)
    hiz = np.linalg.norm(v, axis=1)
    with pytest.raises(ValueError, match="hiz araligi bos"):
        AG._dagilim_egimi(hiz, m, v_esc=float(hiz.max()))


# ------------------------------------------------------------ aday_hesapla
def test_aday_hesapla_butun_alanlari_veriyor():
    v, m = _bulut(n=600, hiz=1.0, egim=1.5)
    d = AG.aday_hesapla(v, m, ehat=EHAT, v_esc=0.5, beta=3.5)
    for ad in ("M_kacan", "v_ort", "kos_ort", "e_hiz", "v_p50", "v_p90",
               "aci_p50", "aci_yayilim", "bagli_kutle", "n_kacan", "beta"):
        assert ad in d and np.isfinite(d[ad]), ad
    assert 0.0 < d["kos_ort"] <= 1.0
    assert d["v_p90"] > d["v_p50"]
    assert 0.0 <= d["aci_p50"] <= 180.0
    assert d["beta"] == pytest.approx(3.5)


def test_beta_verilmezse_UYDURULMUYOR():
    v, m = _bulut()
    d = AG.aday_hesapla(v, m, ehat=EHAT, v_esc=0.5)
    assert "beta" not in d
    with pytest.raises(ValueError, match="beta sonlu"):
        AG.aday_hesapla(v, m, ehat=EHAT, v_esc=0.5, beta=float("nan"))


def test_bagli_kutle_esigin_ALTINDAKI_kutle():
    v, m = _bulut(n=400, hiz=1.0)
    v2 = np.vstack([v, v * 0.05])                    # ikinci yari cok yavas
    m2 = np.concatenate([m, m])
    d = AG.aday_hesapla(v2, m2, ehat=EHAT, v_esc=0.5)
    assert d["bagli_kutle"] == pytest.approx(m.sum())
    assert d["M_kacan"] == pytest.approx(m.sum())


def test_daha_toplu_koni_daha_kucuk_aci_ve_daha_buyuk_kosinus():
    onceki = None
    for yarim_aci in (60.0, 30.0, 10.0):
        v, m = _bulut(n=3000, yarim_aci=yarim_aci, tohum=7)
        d = AG.aday_hesapla(v, m, ehat=EHAT, v_esc=0.5)
        if onceki is not None:
            assert d["aci_p50"] < onceki["aci_p50"]
            assert d["aci_yayilim"] < onceki["aci_yayilim"]
            assert d["kos_ort"] > onceki["kos_ort"]
        onceki = d
    assert onceki["kos_ort"] > 0.99                  # 10 derecelik koni


def test_ehat_denetimleri():
    v, m = _bulut()
    with pytest.raises(ValueError):
        AG.aday_hesapla(v, m, ehat=np.zeros(3), v_esc=0.5)
    with pytest.raises(ValueError):
        AG.aday_hesapla(v, m, ehat=np.ones(2), v_esc=0.5)


# ------------------------------------------- KOSUYLA TUTARLILIK (en onemli)
def test_cevrimdisi_hesap_kosunun_sayilarini_YENIDEN_URETIYOR():
    """`aday_hesapla` ile `ejekta_bilesenleri` **aynı** üç çarpanı vermeli."""
    v, m = _bulut(n=900, hiz=1.2, egim=1.8, tohum=3)
    kosudan = ejekta_bilesenleri(v, m, ehat=EHAT, v_esc=0.5)
    hesap = AG.aday_hesapla(v, m, ehat=EHAT, v_esc=0.5)
    r = AG.tutarlilik_denetle(hesap, kosudan)
    assert r["denetlendi"] and r["en_buyuk"] < 1e-12


def test_tutarlilik_YANLIS_eksende_HATA_veriyor():
    """Eksen yanlış kurulursa sessiz geçmemeli — bütün adaylar bozulur."""
    v, m = _bulut(n=900, hiz=1.2, tohum=4)
    kosudan = ejekta_bilesenleri(v, m, ehat=EHAT, v_esc=0.5)
    yanlis = AG.aday_hesapla(v, m, ehat=np.array([1.0, 0.0, 0.0]), v_esc=0.5)
    with pytest.raises(ValueError, match="yeniden uretmiyor"):
        AG.tutarlilik_denetle(yanlis, kosudan)


def test_tutarlilik_kosuda_hata_varsa_denetlemiyor():
    r = AG.tutarlilik_denetle({}, {"hata": "kacan parcacik 4 (< 30)"})
    assert r["denetlendi"] is False and "kacan parcacik" in r["neden"]
    with pytest.raises(ValueError, match="iki tarafta da gerekli"):
        AG.tutarlilik_denetle({"M_kacan": 1.0}, {"M_kacan": 1.0, "v_ort": 1.0})


# ------------------------------------------------------------ toplama
def test_tum_adaylar_eksigi_SAYIYOR():
    d1 = {"M_kacan": 1.0, "v_ort": 2.0}
    d2 = {"M_kacan": 3.0}                            # v_ort EKSIK
    out = AG.tum_adaylar([d1, d2])
    assert out["M_kacan"].tolist() == [1.0, 3.0]
    assert np.isnan(out["v_ort"][1])
    assert out["eksik_sayisi"].tolist() == [0.0, 1.0]
    with pytest.raises(ValueError):
        AG.tum_adaylar([])


# ------------------------------------------------------------ uretim ekseni
def test_uretim_ehat_birim_ve_acisi_dogru():
    n = np.array([0.0, 0.0, 1.0])
    for aci in (0.0, 17.0, 45.0):
        e = AG.uretim_ehat(aci)
        assert np.linalg.norm(e) == pytest.approx(1.0)
        # mermi ICERI gidiyor: -n ile arasindaki aci = carpma acisi
        assert np.degrees(np.arccos(np.clip(e @ (-n), -1, 1))) == pytest.approx(aci)
    with pytest.raises(ValueError):
        AG.uretim_ehat(17.0, nisan=(0.0, 0.0, 0.0))
    with pytest.raises(ValueError):
        AG.uretim_ehat(17.0, nisan=(1.0, 2.0))


# ------------------------------- kacis hizini kosunun kutlesinden geri cozme
def test_kacis_hizi_kosunun_kutlesinden_geri_cozuluyor():
    """Bilinen bir eşikle kütle hesapla, sonra eşiği **geri oku**."""
    rng = np.random.default_rng(13)
    n = 500
    yon = rng.normal(size=(n, 3))
    yon /= np.linalg.norm(yon, axis=1, keepdims=True)
    hiz = rng.uniform(0.1, 3.0, size=n)
    v = yon * hiz[:, None]
    m = rng.uniform(0.5, 2.0, size=n) * 1e4
    for v_esc in (0.4, 1.0, 2.2):
        M = float(m[hiz > v_esc].sum())
        geri = AG.kacis_hizi_kalibre(v, m, M)
        # geri okunan esik AYNI kutleyi vermeli (esik araliginin ortasi)
        assert float(m[hiz > geri].sum()) == pytest.approx(M)


def test_kacis_hizi_kalibre_mermiyi_ayikliyor():
    rng = np.random.default_rng(14)
    n = 300
    yon = rng.normal(size=(n, 3))
    yon /= np.linalg.norm(yon, axis=1, keepdims=True)
    hiz = rng.uniform(0.1, 3.0, size=n)
    v, m = yon * hiz[:, None], np.full(n, 1.0e4)
    mk = np.zeros(n)
    mk[:60] = 1.0                                    # mermi
    hedef = ~(mk > 0.5)
    M = float(m[hedef][hiz[hedef] > 1.0].sum())
    geri = AG.kacis_hizi_kalibre(v, m, M, mermi_kesri=mk)
    assert float(m[hedef][hiz[hedef] > geri].sum()) == pytest.approx(M)


def test_kacis_hizi_kalibre_tutarsizligi_REDDEDIYOR():
    v, m = _bulut(n=100, hiz=1.0)
    with pytest.raises(ValueError, match="butun hedef kutlesinden"):
        AG.kacis_hizi_kalibre(v, m, 1e12)            # kutle cok buyuk
    with pytest.raises(ValueError, match="M_kacan > 0"):
        AG.kacis_hizi_kalibre(v, m, 0.0)
    # hicbir esigin vermedigi bir kutle (parcacik kutlelerinin arasinda)
    rng = np.random.default_rng(2)
    hiz = rng.uniform(0.5, 2.0, 50)
    yon = rng.normal(size=(50, 3))
    yon /= np.linalg.norm(yon, axis=1, keepdims=True)
    with pytest.raises(ValueError, match="hicbir hiz esigi"):
        AG.kacis_hizi_kalibre(yon * hiz[:, None], np.full(50, 1.0e4), 1.5e4)
