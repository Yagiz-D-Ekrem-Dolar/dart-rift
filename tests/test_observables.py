"""Gozlenebilir cikarici testleri (P3-FR-08, P3-VR-03).

Tasarim: her cikarici, cevabi ANALITIK OLARAK BILINEN yapay bir duruma
uygulanir. Boylece test, kodun kendi ciktisini degil bagimsiz bir dogruyu
sinar.
"""

import numpy as np
import pytest

from dartrift.observables.crater_shape import crater_profile, surface_particles
from dartrift.observables.ejecta_catalog import catalog_ejecta, cumulative_mass_velocity
from dartrift.observables.momentum_transfer import (
    beta_sensitivity,
    kacis_bekleyenler,
    escape_speed,
    momentum_transfer,
)
from dartrift.observables.period_interface import (
    DIMORPHOS_SYSTEM,
    beta_from_period_change,
    period_change,
)
from dartrift.setup.impactor import DART_MOMENTUM

# =========================== beta ===========================

def _iki_parcali_durum(m_ej, v_ej, m_hedef, v_hedef, r_ej=100.0):
    """Analitik durum: 1 ejekta parcacigi + 1 hedef parcacigi."""
    x = np.array([[0.0, 0.0, r_ej], [0.0, 0.0, 0.0]])
    v = np.array([[0.0, 0.0, v_ej], [0.0, 0.0, v_hedef]])
    m = np.array([m_ej, m_hedef])
    return x, v, m


def test_ejekta_yoksa_beta_bir():
    """Hicbir sey kacmazsa beta = 1 (tanim geregi)."""
    x, v, m = _iki_parcali_durum(1.0, 0.0, 1000.0, 0.1)
    r = momentum_transfer(x, v, m, impactor_momentum=np.array([0.0, 0.0, -100.0]),
                          center=np.zeros(3), target_mass=1000.0, target_radius=10.0,
                          control_radius=1000.0)
    assert r.n_ejecta == 0
    assert r.beta == pytest.approx(1.0, abs=1e-14)


def test_beta_bilinen_degeri_verir():
    """p_mermi = 100 (-z); ejekta 50 (+z) tasiyorsa beta = 1.5."""
    x, v, m = _iki_parcali_durum(m_ej=1.0, v_ej=50.0, m_hedef=1000.0, v_hedef=0.0)
    r = momentum_transfer(x, v, m, impactor_momentum=np.array([0.0, 0.0, -100.0]),
                          center=np.zeros(3), target_mass=1000.0, target_radius=10.0,
                          control_radius=50.0, speed_threshold=1.0)
    assert r.n_ejecta == 1
    assert r.beta == pytest.approx(1.5, rel=1e-13)
    assert r.diagnostics["ejecta_direction_ok"] is True


def test_ters_yon_gizlenmez():
    """Ejekta mermiyle AYNI yone giderse beta < 1 cikar ve tani bunu soyler.

    Mutlak deger alip 'beta > 1' gostermek fiziksel olarak yanlis bir
    sonucu dogru gibi sunmak olurdu."""
    x, v, m = _iki_parcali_durum(m_ej=1.0, v_ej=-50.0, m_hedef=1000.0, v_hedef=0.0)
    r = momentum_transfer(x, v, m, impactor_momentum=np.array([0.0, 0.0, -100.0]),
                          center=np.zeros(3), target_mass=1000.0, target_radius=10.0,
                          control_radius=50.0, speed_threshold=1.0)
    assert r.n_ejecta == 0 or r.beta < 1.0 or not r.diagnostics["ejecta_direction_ok"]


def test_yavas_ejekta_sayilmaz():
    """Kontrol yuzeyini gecmek yetmez; kacis hizini asmayan geri duser."""
    x, v, m = _iki_parcali_durum(m_ej=1.0, v_ej=0.001, m_hedef=1000.0, v_hedef=0.0)
    r = momentum_transfer(x, v, m, impactor_momentum=np.array([0.0, 0.0, -100.0]),
                          center=np.zeros(3), target_mass=1000.0, target_radius=10.0,
                          control_radius=50.0, speed_threshold=1.0)
    assert r.n_ejecta == 0, "yavas parcacik ejekta sayildi"


def test_momentum_defteri_kapanmasi_rapor_edilir():
    """beta_ejekta ve beta_bagli cebirsel olarak ayni; farklari KAPANMA
    hatasidir ve o adla raporlanir."""
    x, v, m = _iki_parcali_durum(m_ej=1.0, v_ej=50.0, m_hedef=1000.0, v_hedef=-0.05)
    r = momentum_transfer(x, v, m, impactor_momentum=np.array([0.0, 0.0, -100.0]),
                          center=np.zeros(3), target_mass=1000.0, target_radius=10.0,
                          control_radius=50.0, speed_threshold=1.0)
    # p_bagli = 1000*(-0.05) = -50 ; p_ej = +50 ; toplam = 0 ; p_mermi = -100
    assert r.momentum_closure == pytest.approx(1.0, rel=1e-12)
    assert r.beta_from_bound == pytest.approx(0.5, rel=1e-12)


def test_kacis_hizi_formulu():
    m, rr = 4.3e9, 82.0
    assert escape_speed(m, rr) == pytest.approx(np.sqrt(2 * 6.6743e-11 * m / rr), rel=1e-14)
    assert 0.05 < escape_speed(m, rr) < 0.15


def test_kacis_hizi_gecersiz_girdi():
    for a, b in ((0.0, 1.0), (1.0, 0.0), (-1.0, 1.0)):
        with pytest.raises(ValueError, match="pozitif"):
            escape_speed(a, b)


def test_bos_durum_reddedilir():
    with pytest.raises(ValueError, match="bos durum"):
        momentum_transfer(np.empty((0, 3)), np.empty((0, 3)), np.empty(0),
                          impactor_momentum=np.array([0.0, 0.0, -1.0]))


def test_uyumsuz_uzunluk_reddedilir():
    with pytest.raises(ValueError, match="uzunluk"):
        momentum_transfer(np.zeros((3, 3)), np.zeros((2, 3)), np.zeros(3),
                          impactor_momentum=np.array([0.0, 0.0, -1.0]))


def test_sifir_mermi_momentumu_reddedilir():
    with pytest.raises(ValueError, match="sifir olamaz"):
        momentum_transfer(np.zeros((2, 3)), np.zeros((2, 3)), np.ones(2),
                          impactor_momentum=np.zeros(3))


# ------------------------ duyarlilik (P3-VR-03) ------------------------

def _koni_durumu(n=400, seed=3):
    """Yapay ejekta konisi + duran hedef."""
    rng = np.random.default_rng(seed)
    th = np.radians(rng.uniform(10.0, 50.0, n))
    ph = rng.uniform(0.0, 2 * np.pi, n)
    sp = rng.uniform(0.05, 5.0, n)
    d = np.stack([np.sin(th) * np.cos(ph), np.sin(th) * np.sin(ph), np.cos(th)], -1)
    r = rng.uniform(120.0, 400.0, n)
    x_ej, v_ej = r[:, None] * d, sp[:, None] * d
    m_ej = np.full(n, 1.0e3)
    x_t = rng.normal(scale=30.0, size=(200, 3))
    v_t = np.zeros((200, 3))
    m_t = np.full(200, 1.0e6)
    return (np.vstack([x_ej, x_t]), np.vstack([v_ej, v_t]), np.concatenate([m_ej, m_t]))


def test_hedef_yaricapi_kestirimi_yanli_degil():
    """Varsayilan yaricap kestirimi duzgun dolu kurede DOGRU R vermeli.

    Bulunan kusur: `median(dist)` dogrudan yaricap sayiliyordu. Duzgun dolu
    kurede medyan uzaklik R/2^(1/3) = 0,794 R'dir; yani yaricap %21 KUCUK,
    kacis hizi %12 BUYUK, kontrol yuzeyi 2,00 R yerine 1,59 R cikiyordu.
    Ucu de ejekta olcutunu sikilastirir ve beta'yi sessizce kaydirir.
    """
    from dartrift.observables.momentum_transfer import estimate_target_radius

    rng = np.random.default_rng(0)
    n, R = 200000, 100.0
    d = rng.normal(size=(n, 3)); d /= np.linalg.norm(d, axis=1)[:, None]
    x = d * (R * rng.random(n) ** (1.0 / 3.0))[:, None]
    dist = np.linalg.norm(x, axis=1)

    kestirim = estimate_target_radius(dist)
    assert abs(kestirim - R) / R < 0.01, f"kestirim {kestirim:.3f}, gercek {R}"
    # ESKI kural ne kadar yaniltiyordu: bu, duzeltmenin gerekcesinin olcusu
    eski = float(np.median(dist))
    assert abs(eski - R) / R > 0.15, "eski kuralin yanliligi kayboldu mu?"


def test_kestirilen_yaricap_taniyla_bildirilir():
    """Yaricap KESTIRILDIYSE beta'yi okuyan bunu gormeli."""
    x, v, m = _koni_durumu(100)
    p = np.array([0.0, 0.0, -1.0e6])
    verilen = momentum_transfer(x, v, m, impactor_momentum=p, center=np.zeros(3),
                                target_mass=2.0e8, target_radius=80.0)
    kestirilen = momentum_transfer(x, v, m, impactor_momentum=p, center=np.zeros(3),
                                   target_mass=2.0e8)
    assert verilen.diagnostics["target_radius_estimated"] is False
    assert kestirilen.diagnostics["target_radius_estimated"] is True


def test_duyarlilik_izgarasi_ve_yayilim():
    x, v, m = _koni_durumu()
    s = beta_sensitivity(x, v, m, impactor_momentum=np.array([0.0, 0.0, -3.5601e6]),
                         control_radii=[110.0, 150.0, 250.0],
                         speed_factors=[0.5, 1.0, 2.0],
                         center=np.zeros(3), target_mass=2.0e8, target_radius=80.0)
    assert s["beta_grid"].shape == (3, 3)
    assert s["beta_spread"] >= 0.0
    assert s["beta_min"] <= s["beta_median"] <= s["beta_max"]
    # tanim secimi beta'yi gercekten oynatmali; oynatmiyorsa tarama anlamsizdir
    assert s["beta_spread"] > 0.0, "duyarlilik taramasi hicbir sey degistirmedi"


def test_duyarlilik_eksen_basina_ayrisiyor():
    """Toplam yayilim YETMEZ: hangi eksenin is gordugu ayri ayri bilinmeli.

    Bulunan kusur: `run_observable_selftest` iki boyutlu tarama raporluyordu,
    ama olculen hiz ekseni yayilimi TAM SIFIRDI (butun yayilim yaricap
    ekseninden). Kriter yine de geciyordu — hiz esigi kod yolu hic kosulmadan.
    Burada iki eksen de TEK TEK dogrulanir.
    """
    x, v, m = _koni_durumu()
    s = beta_sensitivity(x, v, m, impactor_momentum=np.array([0.0, 0.0, -3.5601e6]),
                         control_radii=[110.0, 150.0, 250.0],
                         speed_factors=[0.5, 1.0, 2.0],
                         center=np.zeros(3), target_mass=2.0e8, target_radius=80.0)
    assert s["beta_spread_radius_axis"] >= 0.0
    assert s["beta_spread_speed_axis"] >= 0.0
    # eksen yayilimlari toplam yayilimi asamaz
    assert max(s["beta_spread_radius_axis"], s["beta_spread_speed_axis"]) \
        <= s["beta_spread"] + 1e-12
    assert s["radius_axis_active"] == (s["beta_spread_radius_axis"] > 0.0)
    assert s["speed_axis_active"] == (s["beta_spread_speed_axis"] > 0.0)


def test_olu_eksen_toplam_yayilimda_gizlenmez():
    """Hiz esigi hicbir seyi elemiyorsa bu ACIKCA gorunmeli.

    Butun ejekta kacis hizinin cok ustundeyse esik taramasi anlamsizdir;
    toplam yayilim yine pozitif cikar (yaricap ekseninden). Eksen bazli
    rapor bunu yakalar.
    """
    rng = np.random.default_rng(5)
    n = 400
    d = rng.normal(size=(n, 3)); d /= np.linalg.norm(d, axis=1)[:, None]
    # hizlar 50-100 m/s: kacis hizi (~0.4 m/s) yaninda devasa -> esik olu
    x = (rng.uniform(150.0, 600.0, n))[:, None] * d
    v = (rng.uniform(50.0, 100.0, n))[:, None] * d
    m = np.full(n, 1.0e3)
    x = np.vstack([x, rng.normal(scale=20.0, size=(200, 3))])
    v = np.vstack([v, np.zeros((200, 3))])
    m = np.concatenate([m, np.full(200, 1.0e6)])
    s = beta_sensitivity(x, v, m, impactor_momentum=np.array([0.0, 0.0, -3.5601e6]),
                         control_radii=[160.0, 300.0], speed_factors=[0.5, 1.0, 2.0],
                         center=np.zeros(3), target_mass=2.0e8, target_radius=80.0)
    assert s["beta_spread_speed_axis"] == 0.0, "esik gercekten eliyorsa senaryo yanlis"
    assert s["speed_axis_active"] is False
    assert s["beta_spread"] > 0.0          # toplam yayilim yine pozitif...
    assert s["radius_axis_active"] is True  # ...ama hepsi yaricaptan


def test_hiz_esigi_beta_yi_monoton_dusurur():
    """Esik yukseldikce sayilan ejekta ALT KUMEYE dusmeli -> beta azalmali."""
    from dartrift.validation.scene_checks import run_speed_threshold_selftest

    r = run_speed_threshold_selftest()
    assert r["speed_axis_active"] is True
    assert r["beta_monotone_in_threshold"] is True
    assert r["mass_monotone_in_threshold"] is True
    b = r["beta_by_speed_factor"]
    assert b[0] > b[-1], f"esik beta'yi oynatmadi: {b}"


def test_duyarlilik_en_az_iki_yaricap_ister():
    x, v, m = _koni_durumu(50)
    with pytest.raises(ValueError, match="en az 2"):
        beta_sensitivity(x, v, m, impactor_momentum=np.array([0.0, 0.0, -1.0e6]),
                         control_radii=[100.0])


def test_duyarlilik_negatif_parametre_reddeder():
    x, v, m = _koni_durumu(50)
    with pytest.raises(ValueError, match="pozitif"):
        beta_sensitivity(x, v, m, impactor_momentum=np.array([0.0, 0.0, -1.0e6]),
                         control_radii=[100.0, -5.0])


def test_duyarlilik_sabit_tarama_degerini_reddeder():
    """Tarama degiskenini kw ile sabitlemek TypeError ile patlardi; acik hata."""
    x, v, m = _koni_durumu(50)
    for bad in ({"control_radius": 100.0}, {"speed_threshold": 1.0}):
        with pytest.raises(ValueError, match="tarama degiskenidir"):
            beta_sensitivity(x, v, m, impactor_momentum=np.array([0.0, 0.0, -1.0e6]),
                             control_radii=[100.0, 200.0], **bad)


# =========================== ejekta katalogu ===========================

def test_kumulatif_dagilim_monoton_azalir():
    sp = np.array([1.0, 2.0, 3.0, 4.0])
    ms = np.array([1.0, 1.0, 1.0, 1.0])
    v, mc = cumulative_mass_velocity(sp, ms)
    assert np.all(np.diff(mc) <= 0.0)
    assert mc[0] == pytest.approx(4.0)
    assert mc[-1] == pytest.approx(1.0)


def test_kumulatif_dagilim_sekil_kontrolu():
    with pytest.raises(ValueError, match="sekilleri esit"):
        cumulative_mass_velocity(np.zeros(3), np.zeros(2))


def test_uslu_yasa_usu_geri_kazanilir():
    """M(>v) = C v^-2 uretilen veriden us 2.0 cikmali."""
    # M(>v) ~ v^-mu ise hizlar N(>v) ~ v^-mu dagilimindan gelir (esit kutle)
    rng = np.random.default_rng(11)
    mu = 2.0
    u = rng.uniform(0.0, 1.0, 20000)
    sp = (1.0 - u) ** (-1.0 / mu)          # v >= 1, kuyruk us -mu
    x = np.zeros((len(sp), 3))
    x[:, 2] = 500.0
    v = np.zeros((len(sp), 3))
    v[:, 2] = sp
    m = np.ones(len(sp))
    cat = catalog_ejecta(x, v, m, center=np.zeros(3),
                         surface_normal=np.array([0.0, 0.0, 1.0]),
                         control_radius=100.0, escape_speed=0.5)
    assert cat.power_law_exponent == pytest.approx(mu, rel=0.15), cat.power_law_exponent
    assert cat.power_law_r2 > 0.95, cat.power_law_r2


def test_firlatma_acisi_normale_gore():
    """Normalden 30 derece firlayan parcaciklar 30 derece olcmeli."""
    a = np.radians(30.0)
    d = np.array([np.sin(a), 0.0, np.cos(a)])
    x = np.tile(np.array([0.0, 0.0, 200.0]), (5, 1))
    v = np.tile(10.0 * d, (5, 1))
    cat = catalog_ejecta(x, v, np.ones(5), center=np.zeros(3),
                         surface_normal=np.array([0.0, 0.0, 1.0]),
                         control_radius=100.0, escape_speed=1.0)
    assert cat.cone_angle_deg == pytest.approx(30.0, abs=1e-9)
    assert cat.cone_angle_spread_deg == pytest.approx(0.0, abs=1e-9)


def test_kacan_kutle_esikle_ayrilir():
    x = np.tile(np.array([0.0, 0.0, 200.0]), (4, 1))
    v = np.zeros((4, 3))
    v[:, 2] = [0.01, 0.05, 0.2, 1.0]
    cat = catalog_ejecta(x, v, np.ones(4), center=np.zeros(3),
                         surface_normal=np.array([0.0, 0.0, 1.0]),
                         control_radius=100.0, escape_speed=0.1, target_mass=100.0)
    assert cat.n_ejecta == 4
    assert cat.escaping_mass == pytest.approx(2.0)     # 0.2 ve 1.0
    assert cat.escaping_fraction == pytest.approx(0.02)


def test_bos_katalog_sessizce_sifir_donmez():
    """Ejekta yoksa NaN + gerekce doner; 0.0 'olcum' gibi gosterilmez."""
    x = np.zeros((3, 3))
    v = np.zeros((3, 3))
    cat = catalog_ejecta(x, v, np.ones(3), center=np.zeros(3),
                         surface_normal=np.array([0.0, 0.0, 1.0]),
                         control_radius=100.0, escape_speed=0.1)
    assert cat.n_ejecta == 0
    assert np.isnan(cat.speed_max) and np.isnan(cat.power_law_exponent)
    assert "reason" in cat.diagnostics


def test_katalog_gecersiz_girdi():
    x = np.zeros((2, 3))
    v = np.zeros((2, 3))
    m = np.ones(2)
    with pytest.raises(ValueError, match="kontrol yaricapi"):
        catalog_ejecta(x, v, m, center=np.zeros(3),
                       surface_normal=np.array([0.0, 0.0, 1.0]),
                       control_radius=0.0, escape_speed=0.1)
    with pytest.raises(ValueError, match="sifir uzunlukta"):
        catalog_ejecta(x, v, m, center=np.zeros(3), surface_normal=np.zeros(3),
                       control_radius=10.0, escape_speed=0.1)


# =========================== krater sekli ===========================

def _kure_parcaciklari(r=100.0, n=8000, seed=5):
    rng = np.random.default_rng(seed)
    p = rng.normal(size=(n, 3))
    p /= np.linalg.norm(p, axis=1)[:, None]
    rad = r * rng.uniform(0.0, 1.0, n) ** (1.0 / 3.0)
    return p * rad[:, None]


def test_yuzey_parcaciklari_kabuktan_secilir():
    x = _kure_parcaciklari()
    si = surface_particles(x, np.zeros(3))
    d = np.linalg.norm(x[si], axis=1)
    assert d.mean() > 85.0, d.mean()      # ic parcaciklar yuzey sayilmamis
    assert len(si) < len(x)


def _elipsoit_parcaciklari(a=44.0, b=43.5, c=32.5, n=60000, seed=1):
    """Gercek Dimorphos oranlari: 88 x 87 x 65 m."""
    rng = np.random.default_rng(seed)
    p = rng.normal(size=(n, 3))
    p /= np.linalg.norm(p, axis=1)[:, None]
    return p * (rng.random(n) ** (1.0 / 3.0))[:, None] * np.array([a, b, c])


def test_kuresel_referans_duzensiz_cisimde_hayali_krater_uretir():
    """OLCULEN KUSUR — kaydi burada durur, gizlenmez.

    Referansi tek bir sayi (carpma disi medyan yaricap) almak cismi KURE
    kabul eder. Dimorphos kure degil (88x87x65 m). Kratersiz bir elipsoitte
    olculen hayali krater:
        kisa (z) eksende carpma : 9,04 m derinlik, 66,76 m cap
        uzun (x) eksende carpma : 1,46 m derinlik
    Bu test o rakami KILITLER: kuresel varsayimin bedeli budur ve
    `reference_is_spherical` tanisiyla bildirilmek zorundadir.
    """
    x0 = _elipsoit_parcaciklari()
    cs = crater_profile(x0, center=np.zeros(3),
                        impact_direction=np.array([0.0, 0.0, -1.0]),
                        reference_radius=40.0, outer_angle_deg=60.0, n_bins=12)
    assert cs.diagnostics["reference_is_spherical"] is True
    assert cs.depth > 5.0, (
        f"hayali krater kayboldu mu ({cs.depth:.3f} m)? Oyleyse bu testin "
        "gerekcesi degismistir — yeniden olcun")


def test_carpma_oncesi_referans_hayali_krateri_sifirlar():
    """Duzeltme: referans, cismin KENDI carpma oncesi sekli.

    Ayni kratersiz elipsoit, `x_reference` verilince 0,000 m raporlamali.
    """
    x0 = _elipsoit_parcaciklari()
    for yon in ([0.0, 0.0, -1.0], [-1.0, 0.0, 0.0]):
        cs = crater_profile(x0, center=np.zeros(3),
                            impact_direction=np.array(yon),
                            reference_radius=40.0, outer_angle_deg=60.0,
                            n_bins=12, x_reference=x0)
        assert cs.diagnostics["reference_is_spherical"] is False
        assert abs(cs.depth) < 1.0e-9, f"{yon}: derinlik {cs.depth:.3e}"
        assert cs.diameter == 0.0


def test_duzensiz_cisimde_bilinen_krater_dogru_olculur():
    """Elipsoide BILINEN ~8 m'lik cukur; kuresel referans 2 kat sisiriyordu.

    Olculdu (3 tohum): kuresel varsayimla 17,3-17,6 m (gercek 8), carpma
    oncesi referansla 8,66 / 8,69 / 9,04 m. Yani duzeltme yalnizca hayali
    krateri silmiyor, GERCEK krateri de dogru olcuyor.

    KALAN ~%8-13 fazlalik yeni bir kusur DEGIL: `surface_particles` "yuzey"i
    yon kutusundaki en uzak parcacik olarak alir ve bu gercek yuzeyin biraz
    icinde kalir; krater tabaninda kutu basina ornek referans bolgesinden az
    oldugu icin yanlilik derinligi biraz BUYUK gosterir. Ayni etki kure
    testinde de turetilmisti (20 m -> 21,1 m, +%5,5). Isaret ve mertebe
    onceden bilindigi icin esik %20.
    """
    a, b, c = 44.0, 43.5, 32.5
    x0 = _elipsoit_parcaciklari(a, b, c)
    d = np.linalg.norm(x0, axis=1)
    nrm = x0 / np.maximum(d, 1e-300)[:, None]
    # Koni icinde YEREL YUZEYDEN tam 8 m kaz. Normalize yaricapta kazimak
    # elipsoitte koni boyunca DEGISEN mutlak derinlik verirdi — o zaman
    # "bilinen derinlik" bilinmez olur ve test kendi belirsizligini
    # cikaricinin hatasi sanardi (olculdu: oyle kazinca 9,06 m, sozde %13).
    r_surf = 1.0 / np.sqrt((nrm[:, 0] / a) ** 2 + (nrm[:, 1] / b) ** 2
                           + (nrm[:, 2] / c) ** 2)
    kaz = (nrm[:, 2] > np.cos(np.radians(25.0))) & (d > r_surf - 8.0)
    xk = x0[~kaz]
    ort = dict(center=np.zeros(3), impact_direction=np.array([0.0, 0.0, -1.0]),
               reference_radius=40.0, outer_angle_deg=60.0, n_bins=12)
    kuresel = crater_profile(xk, **ort)
    gercek = crater_profile(xk, **ort, x_reference=x0)
    assert kuresel.depth > 15.0, kuresel.depth          # sisirilmis hali
    assert gercek.depth == pytest.approx(8.0, rel=0.20), gercek.depth
    assert gercek.depth < 0.6 * kuresel.depth


def test_krater_derinligi_bilinen_cukurda():
    """Kureden 20 m'lik bir kalot cikarilir; olculen derinlik ~21 m olmali.

    NICIN TAM 20 DEGIL: "yuzey", yon kutusundaki EN UZAK parcaciktir ve bu
    gercek yuzeyin bir miktar icinde kalir. Yanlilik kutudaki ornek sayisina
    baglidir ve krater icinde (parcaciklar silindigi icin ~6 ornek) referans
    bolgesinden (~12 ornek) farklidir:
        r_ref   ~ 100 * 0.5^(1/36) = 98.1
        r_krater~  80 * 0.5^(1/18) = 77.0
        derinlik~ 21.1
    Test bu TURETILEN degere gore kurulur; 20.0'a gore kurup bandi genisletmek
    sistematik bir yanliligi rastgele gurultu gibi gostermek olurdu."""
    x = _kure_parcaciklari(r=100.0, n=40000, seed=9)
    d = np.linalg.norm(x, axis=1)
    cosang = x[:, 2] / np.maximum(d, 1e-300)
    # +z kutbunda 30 derecelik koni icinde yaricapi 80'e indir
    cukur = (cosang > np.cos(np.radians(30.0))) & (d > 80.0)
    x = x[~cukur]
    cs = crater_profile(x, center=np.zeros(3),
                        impact_direction=np.array([0.0, 0.0, -1.0]),
                        reference_radius=100.0, outer_angle_deg=60.0)
    assert cs.depth == pytest.approx(21.1, rel=0.15), cs.depth
    assert cs.rim_angle_deg == pytest.approx(30.0, abs=8.0), cs.rim_angle_deg
    assert cs.diameter > 0.0 and cs.volume > 0.0
    # her kutu asgari orneklem sartini gecmis olmali (az orneklenen kutu,
    # max(sapma) uzerinden hayali derinlik uretir — bu kusur olculdu)
    assert cs.diagnostics["bin_counts_min"] >= 5, cs.diagnostics
    assert cs.diagnostics["empty_bins"] == 0, cs.diagnostics


def test_az_orneklenen_kutu_hayali_derinlik_uretmez():
    """Cok kutulu profilde az orneklenen kutular ATLANIR, derinlige girmez.

    Regresyon: esit ACILI kutulama + max(sapma) ile, hicbir cukur olmayan
    duz bir kurede 40 m'lik hayali krater olculuyordu."""
    x = _kure_parcaciklari(r=100.0, n=40000, seed=9)
    cs = crater_profile(x, center=np.zeros(3),
                        impact_direction=np.array([0.0, 0.0, -1.0]),
                        reference_radius=100.0, outer_angle_deg=60.0, n_bins=20)
    assert abs(cs.depth) < 4.0, cs.depth       # cukur yok -> derinlik ~0
    assert cs.global_radius_change == pytest.approx(0.0, abs=3.0)


def test_kuresel_buzusme_kratere_karismaz():
    """Cisim TUMUYLE kuculurse krater derinligi ~0, kuresel degisim negatif."""
    x = 0.9 * _kure_parcaciklari(r=100.0, n=40000, seed=9)
    cs = crater_profile(x, center=np.zeros(3),
                        impact_direction=np.array([0.0, 0.0, -1.0]),
                        reference_radius=100.0, outer_angle_deg=60.0)
    assert abs(cs.depth) < 5.0, cs.depth
    assert cs.global_radius_change == pytest.approx(-10.0, abs=2.0), cs.global_radius_change


def test_sessiz_nan_yerine_acik_hata():
    """Sifir kutle / gecersiz kutu sayisi sessiz NaN uretmemeli.

    Sessiz NaN yanlis sayidan daha kotudur: nereden geldigi gorunmez ve
    zincirin ilerisinde 'olculdu' diye rapor edilir."""
    x = np.zeros((3, 3))
    v = np.zeros((3, 3))
    with pytest.raises(ValueError, match="toplam kutle pozitif"):
        momentum_transfer(x, v, np.zeros(3),
                          impactor_momentum=np.array([0.0, 0.0, -1.0]))
    xf = np.tile(np.array([0.0, 0.0, 300.0]), (3, 1))
    with pytest.raises(ValueError, match="kutleleri sifir"):
        catalog_ejecta(xf, v, np.zeros(3), center=np.zeros(3),
                       surface_normal=np.array([0.0, 0.0, 1.0]),
                       control_radius=100.0, escape_speed=0.1, target_mass=1.0)
    with pytest.raises(ValueError, match="min_per_bin"):
        crater_profile(_kure_parcaciklari(n=2000), center=np.zeros(3),
                       impact_direction=np.array([0.0, 0.0, -1.0]),
                       reference_radius=100.0, min_per_bin=0)


def test_krater_gecersiz_girdi():
    x = _kure_parcaciklari(n=2000)
    with pytest.raises(ValueError, match="sifir uzunlukta"):
        crater_profile(x, center=np.zeros(3), impact_direction=np.zeros(3),
                       reference_radius=100.0)
    with pytest.raises(ValueError, match="referans yaricap"):
        crater_profile(x, center=np.zeros(3),
                       impact_direction=np.array([0.0, 0.0, -1.0]),
                       reference_radius=0.0)
    with pytest.raises(ValueError, match="outer_angle_deg"):
        crater_profile(x, center=np.zeros(3),
                       impact_direction=np.array([0.0, 0.0, -1.0]),
                       reference_radius=100.0, outer_angle_deg=200.0)


# =========================== periyot arayuzu ===========================

def test_periyot_ileri_geri_tutarli():
    b = 3.0
    pc = period_change(b, DART_MOMENTUM)
    assert beta_from_period_change(pc.delta_period, DART_MOMENTUM) == pytest.approx(b, rel=1e-12)


def test_dart_olculen_periyottan_beta():
    """DART'in olculen -33.0 dakikasi, bu basit modelde beta ~ 3.2 verir.

    Literaturde bildirilen beta ~ 3.6'dir (Cheng ve digerleri 2023). Fark
    (~%11) beklenendir: burada dairesel yorunge + birinci mertebe tegetsel
    itki varsayiliyor, gercek analizde disbukeylik ve tam yorunge modeli var.
    Test bu farki GIZLEMEZ — bandi buna gore konur."""
    b = beta_from_period_change(DIMORPHOS_SYSTEM["measured_period_change"], DART_MOMENTUM)
    assert 2.5 < b < 4.5, b
    assert b == pytest.approx(3.22, abs=0.05), b


def test_periyot_isareti_dogru():
    """Yorungeye TERS momentum periyodu KISALTIR."""
    assert period_change(3.0, DART_MOMENTUM, along_track=-1.0).delta_period < 0.0
    assert period_change(3.0, DART_MOMENTUM, along_track=+1.0).delta_period > 0.0


def test_beta_buyudukce_periyot_degisimi_buyur():
    d = [abs(period_change(b, DART_MOMENTUM).delta_period) for b in (1.0, 2.0, 4.0)]
    assert d[0] < d[1] < d[2]
    assert d[2] / d[0] == pytest.approx(4.0, rel=1e-12)   # dogrusal


def test_birinci_mertebe_gecerlilik_bayragi():
    pc = period_change(3.0, DART_MOMENTUM)
    assert pc.diagnostics["dv_over_v_orbital"] < 0.02
    assert pc.diagnostics["first_order_valid"] is True


def test_yorunge_hizi_mertebesi():
    """Dimorphos yorunge hizi ~17 cm/s olmali."""
    pc = period_change(1.0, DART_MOMENTUM)
    assert 0.1 < pc.orbital_speed < 0.3, pc.orbital_speed


def test_periyot_gecersiz_girdi():
    with pytest.raises(ValueError, match="mermi momentumu pozitif"):
        period_change(3.0, 0.0)
    with pytest.raises(ValueError, match="hedef kutlesi"):
        period_change(3.0, DART_MOMENTUM, target_mass=0.0)
    with pytest.raises(ValueError, match="along_track"):
        period_change(3.0, DART_MOMENTUM, along_track=2.0)
    with pytest.raises(ValueError, match="along_track = 0"):
        beta_from_period_change(-100.0, DART_MOMENTUM, along_track=0.0)


# ---------------------------------------------------------------------
# Krater cikaricisinin OLCULMUS sinirlari
#
# ONCE YANLIS BIR KUSUR BILDIRDIM: `impact_direction`'i kraterin MERKEZ
# YONU sanip verdim; oysa o merminin GIDIS yonudur ve krater
# `-impact_direction` tarafindadir. Yanlis isaretle cikarici KARSI
# KUTBA bakiyor ve dogal olarak 0 buluyordu.
# "Cikarici 80 m'lik krateri goremiyor" sonucu bu yuzden YANLISTI.
# Asagisi dogru yonelimle olculmus GERCEK sinirdir.
# ---------------------------------------------------------------------

def _kure_krater(D, d_kr, R=82.0, s=3.5, seed=7):
    """Bozulmamış küreye **bilinen** bir krater oy.

    Krater `+x`'te; `impact_direction` bu yüzden **`-x`**'tir.
    """
    rng = np.random.default_rng(seed)
    n = int(4 * np.pi * R * R / (s * s))
    u = rng.uniform(-1, 1, n)
    ph = rng.uniform(0, 2 * np.pi, n)
    st = np.sqrt(1 - u * u)
    yon = np.column_stack([st * np.cos(ph), st * np.sin(ph), u])
    merk = np.array([1.0, 0.0, 0.0])
    ya = np.arcsin(min(D / 2 / R, 1.0))
    ca = yon @ merk
    ic = ca > np.cos(ya)
    a = np.arccos(np.clip(ca, -1, 1))
    r = np.full(n, R)
    r[ic] = R - d_kr * (1.0 - (a[ic] / ya) ** 2)
    return r[:, None] * yon, R * yon, -merk, R


def test_krater_YANLIS_yonelimde_sifir_verir():
    """`impact_direction` ters verilirse çıkarıcı **karşı kutba** bakar.

    Bu bir kusur değil, **kullanım hatası** — ama sessizce `0`
    döndüğü için kusur sanılabiliyor. Test bunu kayda geçiriyor.
    """
    from dartrift.observables.crater_shape import crater_profile
    x, x0, idir, R = _kure_krater(40.0, 8.0, s=2.0)
    kr = crater_profile(x, center=np.zeros(3), impact_direction=-idir,
                        reference_radius=R, x_reference=x0)
    assert kr.depth == 0.0 and kr.diameter == 0.0


def test_krater_DOGRU_yonelimde_derinligi_goruyor():
    """Doğru yönelimde krater **görülüyor** — ama medyan yüzünden sığ."""
    from dartrift.observables.crater_shape import crater_profile
    x, x0, idir, R = _kure_krater(40.0, 8.0, s=2.0)
    kr = crater_profile(x, center=np.zeros(3), impact_direction=idir,
                        reference_radius=R, x_reference=x0)
    # `0.` kutu 0-12,84 derece ve MEDYAN aliniyor; parabolik kraterin
    # medyani tepe derinliginin ~yarisi. Olculen: 3,51 m (gercek 8 m).
    assert 0.3 * 8.0 < kr.depth < 0.7 * 8.0, kr.depth


def test_krater_KUCUK_krateri_goremiyor_SINIR():
    """`D = 20 m` (yarı açı `7°`) `0.` kutudan (`12,84°`) **küçük**.

    Medyan neredeyse kımıldamıyor → `0`. Bu **ölçülmüş bir sınır**;
    çözünürlük artırmak da düzeltmiyor.
    """
    from dartrift.observables.crater_shape import crater_profile
    for s in (3.5, 2.0, 1.2):
        x, x0, idir, R = _kure_krater(20.0, 4.0, s=s)
        kr = crater_profile(x, center=np.zeros(3), impact_direction=idir,
                            reference_radius=R, x_reference=x0)
        # Tam sifir degil, KAYAN NOKTA gurultusu (1e-14). Onemli olan
        # 4 m'lik gercek derinligin HIC gorunmemesi.
        assert kr.depth < 1e-9, (s, kr.depth)
        assert kr.diameter == 0.0, (s, kr.diameter)


def test_krater_ekseni_kutusu_SEYREKSE_hata_veriyor():
    """`0` döndürmektense *"ölçemedim"* demek doğrudur (yeni koruma)."""
    from dartrift.observables.crater_shape import crater_profile
    x, x0, idir, R = _kure_krater(40.0, 8.0, s=3.5)   # yalnizca 4 parcacik
    with pytest.raises(ValueError, match="carpma ekseni kutusunda"):
        crater_profile(x, center=np.zeros(3), impact_direction=idir,
                       reference_radius=R, x_reference=x0)


# ---------------------------------------------------------------------------
# kacis_bekleyenler — "bekle" ile "bosuna bekliyorsun" arasini ayiran tani
# ---------------------------------------------------------------------------

def _bekleyen_sahne():
    """Elle kurulmus, her kovada BILINEN sayida parcacik olan sahne.

    R = 10, v_kacis = 1. Konumlar +x ekseninde, yani `v_r = v_x`.
    """
    x = np.array([
        [8.0, 0.0, 0.0],    # 0 iceride, v_r = 2 > 1   -> BEKLEYEN, t = 1.0
        [6.0, 0.0, 0.0],    # 1 iceride, v_r = 4 > 1   -> BEKLEYEN, t = 1.0
        [5.0, 0.0, 0.0],    # 2 iceride, v_r = 0,5     -> yavas, hicbir kova
        [9.0, 0.0, 0.0],    # 3 iceride, v_r = -3      -> ICERI gidiyor
        [12.0, 0.0, 0.0],   # 4 disarida, v_r = 5 > 1  -> KACTI
        [15.0, 0.0, 0.0],   # 5 disarida, v_r = 0,2    -> YAVAS DISI
        [7.0, 0.0, 0.0],    # 6 MERMI (hedef degil)    -> hicbir kova
    ], dtype=np.float64)
    v = np.zeros_like(x)
    v[:, 0] = [2.0, 4.0, 0.5, -3.0, 5.0, 0.2, 9.0]
    m = np.ones(len(x))
    hedef = np.array([True, True, True, True, True, True, False])
    return x, v, m, hedef


def test_kacis_bekleyenler_kovalar_dogru():
    x, v, m, hedef = _bekleyen_sahne()
    d = kacis_bekleyenler(x, v, m, hedef=hedef, R=10.0, v_esc=1.0)

    assert d["n_bekleyen"] == 2, "iceride hizli giden 2 parcacik var"
    assert d["n_kacti"] == 1
    assert d["n_yavas_disi"] == 1
    assert d["yargi"] == "bekleyen_var"
    # Mermi (indeks 6) iceride ve cok hizli ama HEDEF degil; sayilmamali.
    assert d["n_bekleyen"] + d["n_kacti"] + d["n_yavas_disi"] == 4


def test_kacis_bekleyenler_gecis_suresi_elle_hesapla():
    """`t = (R - r) / v_r` — iki bekleyen de tam 1,0 s veriyor."""
    x, v, m, hedef = _bekleyen_sahne()
    d = kacis_bekleyenler(x, v, m, hedef=hedef, R=10.0, v_esc=1.0)
    # (10-8)/2 = 1,0   ve   (10-6)/4 = 1,0
    assert d["t_gecis_min"] == pytest.approx(1.0)
    assert d["t_gecis_medyan"] == pytest.approx(1.0)
    assert d["t_gecis_p90"] == pytest.approx(1.0)


def test_kacis_bekleyenler_bekleyen_yoksa_NaN_uretir():
    """Bekleyen yokken sayi UYDURULMAZ.

    Bu testin butun mesele: `t_gecis_medyan = 0` gibi bir varsayilan,
    "hemen cikacak" diye okunur ve tam TERS karari verdirir.
    """
    x = np.array([[5.0, 0.0, 0.0], [6.0, 0.0, 0.0]])
    v = np.zeros_like(x)          # hicbiri hareket etmiyor
    m = np.ones(2)
    hedef = np.ones(2, dtype=bool)
    d = kacis_bekleyenler(x, v, m, hedef=hedef, R=10.0, v_esc=1.0)

    assert d["n_bekleyen"] == 0
    assert d["yargi"] == "bekleyen_yok"
    assert np.isnan(d["t_gecis_medyan"])
    assert np.isnan(d["t_gecis_min"])
    assert np.isnan(d["t_gecis_p90"])


def test_kacis_bekleyenler_merkezdeki_parcacik_patlatmaz():
    """`r = 0`'da radyal yon tanimsiz — bolme hatasi da olmamali."""
    x = np.array([[0.0, 0.0, 0.0], [8.0, 0.0, 0.0]])
    v = np.array([[100.0, 0.0, 0.0], [2.0, 0.0, 0.0]])
    m = np.ones(2)
    hedef = np.ones(2, dtype=bool)
    d = kacis_bekleyenler(x, v, m, hedef=hedef, R=10.0, v_esc=1.0)
    # Merkezdeki parcacik icin v_r = 0 cikar; hizli sayilmaz.
    assert d["n_bekleyen"] == 1
    assert np.isfinite(d["t_gecis_medyan"])


def test_kacis_bekleyenler_kutle_kesri_hedefe_gore():
    x, v, m, hedef = _bekleyen_sahne()
    m = m.copy()
    m[0] = 3.0                      # bekleyenlerden biri agir
    d = kacis_bekleyenler(x, v, m, hedef=hedef, R=10.0, v_esc=1.0)
    # bekleyen kutle = 3 + 1 = 4; hedef kutlesi = 3+1+1+1+1+1 = 8
    assert d["bekleyen_kutle_kesri"] == pytest.approx(4.0 / 8.0)


def test_kacis_bekleyenler_uzunluk_uyusmazligi_hata():
    x = np.zeros((3, 3))
    with pytest.raises(ValueError, match="ayni uzunlukta"):
        kacis_bekleyenler(x, np.zeros((2, 3)), np.ones(3),
                             hedef=np.ones(3, dtype=bool), R=1.0, v_esc=1.0)
