"""`coarsen_to_sites` — ADR-0043 §7 madde 2'nin sınavı.

Bu testlerin işi tek şey: **korunum iddiası doğru mu.** ADR-0043 §5
üç şey istiyor (kütle, momentum, enerji) ve dördüncü bir şeyi
(açısal momentum) **iddia etmiyor** — testler tam olarak bu ayrımı
sınıyor.
"""
from __future__ import annotations

import numpy as np
import pytest

from dartrift.setup.coarsen import coarsen_to_sites

RNG = np.random.default_rng(20260808)


def _ornek(n=500, ns=17, sacilimli=True):
    x = RNG.uniform(-5.0, 5.0, size=(n, 3))
    v = (RNG.normal(0.0, 300.0, size=(n, 3)) if sacilimli
         else np.tile([120.0, -40.0, 7.0], (n, 1)))
    m = RNG.uniform(0.5, 4.0, size=n)
    e = RNG.uniform(1.0e3, 5.0e4, size=n)
    siteler = RNG.uniform(-5.0, 5.0, size=(ns, 3))
    return x, v, m, e, siteler


# --------------------------------------------------------------- korunum

def test_kutle_momentum_enerji_makine_hassasiyetinde_korunur():
    r = coarsen_to_sites(*_ornek())["korunum"]
    assert r["kutle_hata"] < 1e-14, r
    assert r["momentum_hata"] < 1e-13, r
    assert r["enerji_hata"] < 1e-13, r


@pytest.mark.parametrize("n,ns", [(50, 3), (500, 17), (2000, 101), (10, 9)])
def test_korunum_her_boyutta_tutar(n, ns):
    r = coarsen_to_sites(*_ornek(n, ns))["korunum"]
    assert r["kutle_hata"] < 1e-14
    assert r["momentum_hata"] < 1e-12
    assert r["enerji_hata"] < 1e-12


def test_kutle_toplami_birebir():
    x, v, m, e, s = _ornek()
    out = coarsen_to_sites(x, v, m, e, s)
    assert out["m"].sum() == pytest.approx(m.sum(), rel=1e-15)


def test_atama_bir_boluntudur():
    """Her ince parçacık **tam bir** siteye gidiyor — korunumun temeli."""
    x, v, m, e, s = _ornek()
    out = coarsen_to_sites(x, v, m, e, s)
    at = out["atama"]
    assert len(at) == len(x)
    assert at.min() >= 0 and at.max() < len(s)
    # Grup kutlelerinin toplami = toplam kutle (hicbir parcacik iki grupta degil)
    assert np.bincount(at, weights=m).sum() == pytest.approx(m.sum(), rel=1e-15)


# ------------------------------------------------- naif ortalamanin kusuru

def test_naif_agirliksiz_ortalama_momentumu_BOZARDI():
    """ADR-0043 §5'in reddettiği yol gerçekten bozuyor mu — ölçülüyor.

    Reddedilen bir alternatifi *"bozar"* diye yazmak, bozduğunu
    **göstermeden**, tam da bu projenin beş kez düştüğü kalıp.
    """
    x, v, m, e, s = _ornek()
    out = coarsen_to_sites(x, v, m, e, s)
    at, ns = out["atama"], len(s)
    dolu = np.bincount(at, minlength=ns) > 0
    # NAIF: agirliksiz hiz ortalamasi, kutleyi yine topla.
    v_naif = np.stack([np.bincount(at, weights=v[:, d], minlength=ns)
                       for d in range(3)], axis=1)[dolu]
    v_naif /= np.bincount(at, minlength=ns)[dolu][:, None]
    P0 = (m[:, None] * v).sum(axis=0)
    P_naif = (out["m"][:, None] * v_naif).sum(axis=0)
    hata = np.linalg.norm(P_naif - P0) / np.linalg.norm(P0)
    assert hata > 1e-3, f"naif yol {hata:.2e} ile bozmali; kurulum zayif"
    # Ve dogru yol AYNI kurulumda bozmuyor:
    assert out["korunum"]["momentum_hata"] < 1e-13


# ------------------------------------------------------------ enerji secimi

def test_kayip_kinetik_ic_enerjiye_gidiyor():
    x, v, m, e, s = _ornek()
    out = coarsen_to_sites(x, v, m, e, s)
    # Ic enerji ARTMALI: sacilim isiya dondu.
    assert (out["m"] * out["e"]).sum() > (m * e).sum()
    assert out["korunum"]["ice_donen_kinetik_oran"] > 0.0


def test_sacilimsiz_akista_ic_enerji_DEGISMEZ():
    """Bütün hızlar aynıysa ortalama hiçbir şey kaybetmez."""
    x, v, m, e, s = _ornek(sacilimli=False)
    out = coarsen_to_sites(x, v, m, e, s)
    assert out["korunum"]["ice_donen_kinetik_oran"] == pytest.approx(0.0,
                                                                    abs=1e-15)
    assert (out["m"] * out["e"]).sum() == pytest.approx((m * e).sum(),
                                                        rel=1e-14)


def test_tek_site_tum_kutleyi_toplar():
    """`ns = 1`: sonuç tek parçacık, kütle merkezi ve toplam momentum."""
    x, v, m, e, _ = _ornek()
    out = coarsen_to_sites(x, v, m, e, np.zeros((1, 3)))
    assert out["m"].shape == (1,)
    assert out["m"][0] == pytest.approx(m.sum(), rel=1e-15)
    np.testing.assert_allclose(out["v"][0], (m[:, None] * v).sum(0) / m.sum(),
                               rtol=1e-13)
    np.testing.assert_allclose(out["x"][0], (m[:, None] * x).sum(0) / m.sum(),
                               rtol=1e-13)


# --------------------------------------------- IDDIA EDILMEYEN: acisal mom.

def test_acisal_momentum_KORUNMUYOR_ve_bu_raporlaniyor():
    """Kaba tanecikleştirme grup dönüşünü siler. Test bunu **bekliyor**.

    Bir gün korunur hâle gelirse bu test düşer ve o zaman ADR
    güncellenmeli — sessizce iyileşmesini istemiyoruz.
    """
    r = coarsen_to_sites(*_ornek())["korunum"]
    assert r["acisal_momentum_hata"] > 1e-6, (
        "açısal momentum beklenmedik biçimde korunmuş — ADR-0043 §5 gözden "
        "geçirilmeli")


def test_bos_siteler_dusuruluyor():
    x, v, m, e, _ = _ornek(n=20)
    # Yarisi cok uzakta: hicbir parcacik oraya atanmaz.
    s = np.concatenate([RNG.uniform(-5, 5, size=(4, 3)),
                        np.full((6, 3), 1.0e6)])
    out = coarsen_to_sites(x, v, m, e, s)
    assert out["korunum"]["n_bos_site"] == 6
    assert out["korunum"]["n_cikan"] == 4
    assert out["m"].sum() == pytest.approx(m.sum(), rel=1e-15)


# ------------------------------------------------------------- yan alanlar

def test_alpha0_Y0_kutle_agirlikli_ve_araliktan_cikmiyor():
    x, v, m, e, s = _ornek()
    a0 = RNG.uniform(1.1, 2.0, size=len(x))
    y0 = RNG.uniform(1e4, 1e7, size=len(x))
    out = coarsen_to_sites(x, v, m, e, s, alpha0=a0, Y0=y0)
    assert out["alpha0"].min() >= a0.min() - 1e-12
    assert out["alpha0"].max() <= a0.max() + 1e-12
    assert out["Y0"].min() >= y0.min() - 1e-6
    assert out["korunum"]["alpha0_Y0_yaklasim"] is True


def test_is_boulder_kutle_cogunluguyla():
    x = np.array([[0.0, 0, 0], [0.1, 0, 0], [0.2, 0, 0]])
    v, e = np.zeros((3, 3)), np.zeros(3)
    m = np.array([10.0, 1.0, 1.0])
    out = coarsen_to_sites(x, v, m, e, np.zeros((1, 3)),
                           is_boulder=np.array([True, False, False]))
    assert bool(out["is_boulder"][0]) is True          # 10/12 > 0.5
    out2 = coarsen_to_sites(x, v, np.array([1.0, 1.0, 10.0]), e,
                            np.zeros((1, 3)),
                            is_boulder=np.array([True, False, False]))
    assert bool(out2["is_boulder"][0]) is False        # 1/12 < 0.5


# ---------------------------------------------------------------- korumalar

def test_belirlenimci_ayni_girdi_ayni_cikti():
    a = _ornek()
    r1 = coarsen_to_sites(*a)
    r2 = coarsen_to_sites(*a)
    for k in ("x", "v", "m", "e"):
        np.testing.assert_array_equal(r1[k], r2[k])


def test_parcali_en_yakin_site_tek_parcayla_ayni():
    """`parca` bölmesi sonucu **değiştirmemeli** — bellek koruması sessizce
    farklı bir atama üretirse korunum yine tutar ama sonuç yeniden
    üretilemez olur."""
    from dartrift.setup.coarsen import _en_yakin_site
    x, _, _, _, s = _ornek(n=1000)
    np.testing.assert_array_equal(_en_yakin_site(x, s, parca=10 ** 9),
                                  _en_yakin_site(x, s, parca=7))


@pytest.mark.parametrize("kw,mesaj", [
    (dict(siteler=np.zeros((0, 3))), "site listesi boş"),
    (dict(m=np.array([1.0, -1.0])), "pozitif"),
])
def test_gecersiz_girdiler(kw, mesaj):
    g = dict(x=np.zeros((2, 3)), v=np.zeros((2, 3)), m=np.ones(2),
             e=np.zeros(2), siteler=np.zeros((1, 3)))
    g.update(kw)
    with pytest.raises(ValueError, match=mesaj):
        coarsen_to_sites(**g)


def test_uzunluk_uyusmazligi_yakalanir():
    with pytest.raises(ValueError, match="uzunluklar uyuşmuyor"):
        coarsen_to_sites(np.zeros((3, 3)), np.zeros((2, 3)), np.ones(3),
                         np.zeros(3), np.zeros((1, 3)))


# -------------------------------------------------- atama mesafesi tanisi

def test_atama_mesafesi_raporlaniyor():
    x, v, m, e, s = _ornek()
    k = coarsen_to_sites(x, v, m, e, s)["korunum"]
    assert k["atama_mesafe_max"] >= k["atama_mesafe_ort"] > 0.0


def test_UZAK_parcacik_korunumu_bozmaz_ama_mesafe_YAKALAR():
    """Korunumun **göremediği** kusur: kütlenin ışınlanması.

    Bir parçacığı çok uzağa koyup en yakın siteye zorluyoruz. Üç
    korunum yasası da **tam** kalıyor — tanı olmasaydı bu bozukluk
    görünmezdi.
    """
    x = np.array([[0.0, 0, 0], [0.1, 0, 0], [1000.0, 0, 0]])
    v = np.array([[1.0, 0, 0], [2.0, 0, 0], [3.0, 0, 0]])
    m, e = np.ones(3), np.zeros(3)
    k = coarsen_to_sites(x, v, m, e, np.zeros((1, 3)))["korunum"]
    assert k["kutle_hata"] < 1e-15
    assert k["momentum_hata"] < 1e-15
    assert k["enerji_hata"] < 1e-15
    assert k["atama_mesafe_max"] == pytest.approx(1000.0)   # <-- YAKALADI


def test_acisal_momentum_olcekli_kayip_L0_SIFIRA_YAKINKEN_anlamli():
    """`|L₀|`'a bölmek `L₀ ≈ 0` iken **anlamsız** — ölçekli sürüm var mı.

    Kurulum: yörünge terimi (`m x_km × v_k`) ile grup **iç dönüşü**
    birbirini tam götürüyor, yani `L₀ = 0`. Kabalaştırma iç dönüşü
    siliyor, geriye yörünge terimi kalıyor: `L₁ = 40 ẑ`.

    Ham oran `40/0` → patlıyor ve hiçbir şey söylemiyor. Gerçek
    sahnede tam bu oldu: `%72 870`. Ölçekli sürüm `0,1` diyor.

    İlk denemem bunu **gösteremiyordu** (uyumlu dönen bir küme
    kurmuştum, `L₀ = 4 ẑ` çıktı ve ham oran `1,0` oldu). Test kendi
    kusurumu yakaladı; fikstür düzeltildi.
    """
    x = np.array([[11.0, 0, 0], [9.0, 0, 0], [10.0, 1.0, 0], [10.0, -1.0, 0]])
    v = np.array([[0, -9.0, 0], [0, 11.0, 0], [10.0, 1.0, 0], [-10.0, 1.0, 0]])
    m, e = np.ones(4), np.zeros(4)
    L0 = (m[:, None] * np.cross(x, v)).sum(axis=0)
    assert np.allclose(L0, 0.0), f"fikstür bozuk: L0 = {L0}"
    k = coarsen_to_sites(x, v, m, e, np.zeros((1, 3)))["korunum"]
    assert k["acisal_momentum_hata"] > 1e10         # ham oran ANLAMSIZ
    assert k["acisal_momentum_kayip_olcekli"] == pytest.approx(0.1, rel=1e-9)
    assert 0.0 <= k["acisal_momentum_kayip_olcekli"] <= 1.0 + 1e-12


# ------------------------------------------- LAGRANGE'ci site uretimi (#5)

def test_lagrange_atama_mesafesi_YAPI_GEREGI_sinirli():
    """Euler'ci sürümün düştüğü yer: `4,35` hücre. Bu sınırlı olmalı.

    Kübik hücreye bölünen bir bulutta her parçacık kendi hücresinin
    merkezine `≤ a√3/2` uzaklıkta. Ölçülüyor.
    """
    from dartrift.setup.coarsen import sites_from_cloud
    x = RNG.uniform(-50.0, 50.0, size=(4000, 3))       # GENIS yayilmis bulut
    v, m, e = RNG.normal(0, 200, (4000, 3)), np.ones(4000), np.zeros(4000)
    s2 = 3.5
    s = sites_from_cloud(x, s2)
    k = coarsen_to_sites(x, v, m, e, s)["korunum"]
    a = s2 / 2.0 ** (1.0 / 6.0)
    assert k["atama_mesafe_max"] <= a * np.sqrt(3.0) / 2.0 + 1e-9
    assert k["atama_mesafe_max"] / s2 < 1.0            # Euler'ci: 4.35
    assert k["kutle_hata"] < 1e-14 and k["momentum_hata"] < 1e-12


def test_lagrange_hucre_hacmi_asama2_parcacigiyla_AYNI():
    """`a = s/2^(1/6)` — FCC parçacık hacmi `s³/√2` ile eşleşmeli."""
    from dartrift.setup.coarsen import sites_from_cloud
    s2 = 3.5
    x = np.array([[0.0, 0, 0], [100.0, 0, 0]])
    s = sites_from_cloud(x, s2)
    a = float(np.linalg.norm(s[1] - s[0])) / round(
        float(np.linalg.norm(s[1] - s[0])) / (s2 / 2 ** (1 / 6)))
    assert a ** 3 == pytest.approx(s2 ** 3 / np.sqrt(2.0), rel=1e-12)


def test_lagrange_belirlenimci_ve_dolu_hucreler():
    from dartrift.setup.coarsen import sites_from_cloud
    x = RNG.uniform(-10, 10, size=(500, 3))
    s1, s2 = sites_from_cloud(x, 2.0), sites_from_cloud(x, 2.0)
    np.testing.assert_array_equal(s1, s2)
    # Hicbir site BOS kalmamali: her site en az bir parcacik almali.
    k = coarsen_to_sites(x, np.zeros_like(x), np.ones(len(x)),
                         np.zeros(len(x)), s1)["korunum"]
    assert k["n_bos_site"] == 0
    assert k["n_cikan"] == len(s1)


@pytest.mark.parametrize("kw,mesaj", [
    (dict(x=np.zeros((0, 3))), "bulut boş"),
    (dict(s_hedef=0.0), "pozitif"),
    (dict(paketleme="hcp"), "fcc"),
    (dict(x=np.array([[np.nan, 0.0, 0.0]])), "sonlu olmayan"),
])
def test_lagrange_gecersiz_girdiler(kw, mesaj):
    from dartrift.setup.coarsen import sites_from_cloud
    g = dict(x=np.zeros((3, 3)), s_hedef=1.0)
    g.update(kw)
    with pytest.raises(ValueError, match=mesaj):
        sites_from_cloud(**g)


# ------------------------------------------------ komsu sagligi (SPH sarti)

def test_komsu_sagligi_duzgun_kafeste_bol_komsu():
    """FCC benzeri düzgün bir kafeste `2h = 4s` içinde komşu **çok**."""
    from dartrift.setup.coarsen import komsu_sagligi
    from dartrift.setup.rubble_generator import lattice_points
    s2 = 3.5
    x = lattice_points(np.full(3, -30.0), np.full(3, 30.0), s2, "fcc")
    d = komsu_sagligi(x, h=2.0 * s2)
    assert d["komsu_medyan"] > 100.0, d
    assert d["yalniz_oran"] < 0.35            # yalnizca KENAR parcaciklari


def test_komsu_sagligi_seyrek_bulutta_YALNIZ_parcacik_yakalar():
    """Genişlemiş/seyrek bir kümede uyarı çıkmalı — sessiz kalmamalı."""
    from dartrift.setup.coarsen import komsu_sagligi
    rng = np.random.default_rng(11)
    x = rng.uniform(-500.0, 500.0, size=(200, 3))     # cok seyrek
    d = komsu_sagligi(x, h=7.0)
    assert d["komsu_medyan"] == 0.0
    assert d["cok_yalniz_oran"] == pytest.approx(1.0)


def test_komsu_sagligi_parcali_tek_blokla_ayni():
    from dartrift.setup.coarsen import komsu_sagligi
    x = RNG.uniform(-20, 20, size=(700, 3))
    a = komsu_sagligi(x, h=3.0)
    d = np.linalg.norm(x[:, None, :] - x[None, :, :], axis=2)
    bek = np.count_nonzero(d < 6.0, axis=1) - 1
    assert a["komsu_ort"] == pytest.approx(float(bek.mean()), rel=1e-12)
    assert a["komsu_min"] == int(bek.min())


@pytest.mark.parametrize("kw,mesaj", [
    (dict(x_k=np.zeros((0, 3))), "boş küme"),
    (dict(h=0.0), "pozitif"),
    (dict(x_k=np.zeros((3, 2))), r"\(M,3\)"),
])
def test_komsu_sagligi_gecersiz(kw, mesaj):
    from dartrift.setup.coarsen import komsu_sagligi
    g = dict(x_k=np.zeros((3, 3)), h=1.0)
    g.update(kw)
    with pytest.raises(ValueError, match=mesaj):
        komsu_sagligi(**g)
