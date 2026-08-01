"""DART mermisi + carpma geometrisi testleri (P3-FR-06/07, P3-VR-02)."""

import math

import numpy as np
import pytest

from dartrift.setup.impactor import (
    DART_MASS,
    DART_MOMENTUM,
    DART_SPEED,
    build_impactor,
    impact_geometry,
    place_impactor,
    resolution_series,
)
from dartrift.setup.shape_mesh import ellipsoid, icosphere

# --------------------------- anma degerleri ---------------------------

def test_dart_sabitleri_tutarli():
    """p = m v — uc sabit birbirinden bagimsiz yazilamaz."""
    assert DART_MOMENTUM == pytest.approx(DART_MASS * DART_SPEED, rel=1e-15)
    assert DART_MOMENTUM == pytest.approx(3.5601e6, rel=1e-3)


def test_dart_kinetik_enerji_mertebesi():
    """~1.09e10 J — literaturde bildirilen mertebe."""
    e = 0.5 * DART_MASS * DART_SPEED**2
    assert 1.0e10 < e < 1.2e10, e


# --------------------------- ayriklastirma ---------------------------

def test_nokta_parcacik_yasak():
    """P3-FR-06 acikca nokta parcacigi yasakliyor."""
    with pytest.raises(ValueError, match="n_target"):
        build_impactor(1)
    with pytest.raises(ValueError, match="n_target"):
        build_impactor(7)


def test_kutle_tam_korunur():
    """Ayriklastirma kaba da olsa toplam kutle TAM olmali."""
    for n in (50, 500, 5000):
        imp = build_impactor(n)
        assert imp.total_mass == pytest.approx(DART_MASS, rel=1e-13)


def test_momentum_anma_degerini_verir():
    imp = build_impactor(1000)
    p = imp.momentum
    assert np.linalg.norm(p) == pytest.approx(DART_MOMENTUM, rel=1e-12)
    # varsayilan yon -z
    assert p[2] < 0.0 and abs(p[0]) < 1e-6 and abs(p[1]) < 1e-6


def test_kinetik_enerji_anma_degerini_verir():
    imp = build_impactor(1000)
    assert imp.kinetic_energy == pytest.approx(0.5 * DART_MASS * DART_SPEED**2, rel=1e-12)


def test_yaricap_yogunluktan_turer():
    """m = rho (4/3) pi R^3 — yaricap serbest parametre degil."""
    rho = 2700.0
    imp = build_impactor(1000, density=rho)
    v = DART_MASS / rho
    assert imp.radius == pytest.approx((3.0 * v / (4.0 * math.pi)) ** (1 / 3), rel=1e-13)
    # DART ~0.55 m capinda bir kure esdegeri
    assert 0.2 < imp.radius < 0.5, imp.radius


def test_cozunurluk_arttikca_hacim_hatasi_kuculur():
    """Ayriklastirma yakinsamali olmali; aksi halde 'daha cok parcacik' bos

    maliyet demektir. Kaba uctan ince uca hata monoton azalmasa bile
    BELIRGIN sekilde kuculmeli."""
    errs = [build_impactor(n).diagnostics["volume_error"] for n in (60, 600, 6000)]
    assert errs[-1] < errs[0], errs
    assert errs[-1] < 0.05, errs


def test_cap_boyunca_yeterli_parcacik():
    """Sok cozunurlugu icin cap boyunca en az ~5 parcacik (P3-FR-06 ruhu)."""
    d = build_impactor(500).diagnostics
    assert d["particles_across_diameter"] > 5.0, d


def test_etkin_yogunluk_makul():
    d = build_impactor(2000).diagnostics
    assert d["density_error"] < 0.05, d


def test_yon_normalize_edilir():
    imp = build_impactor(200, direction=np.array([0.0, 0.0, -7.3]))
    assert np.linalg.norm(imp.v[0]) == pytest.approx(DART_SPEED, rel=1e-13)


def test_sifir_yon_reddedilir():
    with pytest.raises(ValueError, match="sifir uzunluklu"):
        build_impactor(200, direction=np.zeros(3))


def test_gecersiz_fiziksel_parametreler():
    for kw in ({"mass": 0.0}, {"speed": -1.0}, {"density": 0.0}):
        with pytest.raises(ValueError, match="pozitif"):
            build_impactor(200, **kw)


def test_cozunurluk_serisi_en_az_uc_ister():
    """P3-VR-02: yakinsama en az 3 noktayla gosterilir."""
    with pytest.raises(ValueError, match="3 cozunurluk"):
        resolution_series([100, 1000])
    seri = resolution_series([100, 400, 1600])
    assert [s.n for s in seri] == sorted(s.n for s in seri)
    for s in seri:
        assert s.total_mass == pytest.approx(DART_MASS, rel=1e-13)


# --------------------------- carpma geometrisi ---------------------------

def test_kurede_dik_carpma():
    mesh = icosphere(3, 80.0)
    g = impact_geometry(mesh, np.array([0.0, 0.0, 1.0]))
    assert g.point[2] > 70.0
    # dik carpma: yon tam olarak -normal
    assert np.allclose(g.direction, -g.normal, atol=1e-12)
    assert g.diagnostics["cos_incidence"] == pytest.approx(1.0, abs=1e-12)


def test_normal_disa_bakar():
    mesh = icosphere(3, 80.0)
    for aim in (np.array([1.0, 0, 0]), np.array([0, -1.0, 0.3]), np.array([0.2, 0.4, -1.0])):
        g = impact_geometry(mesh, aim)
        assert float(np.dot(g.normal, g.point - mesh.centroid)) > 0.0


def test_egik_carpma_acisi():
    """Gelis yonuyle normal arasindaki aci, istenen aciyi TAM vermeli."""
    mesh = icosphere(3, 80.0)
    for a in (0.0, 15.0, 45.0, 70.0):
        g = impact_geometry(mesh, np.array([0.0, 0.0, 1.0]), angle_deg=a)
        cos_t = float(np.dot(-g.direction, g.normal))
        assert math.degrees(math.acos(min(1.0, cos_t))) == pytest.approx(a, abs=1e-9)
        assert np.linalg.norm(g.direction) == pytest.approx(1.0, rel=1e-13)


def test_gecersiz_aci_reddedilir():
    mesh = icosphere(2, 10.0)
    for a in (-1.0, 90.0, 120.0):
        with pytest.raises(ValueError, match="carpma acisi"):
            impact_geometry(mesh, np.array([0.0, 0.0, 1.0]), angle_deg=a)


def test_azimut_tegetsel_bileseni_dondurur():
    """Azimut degisince aci AYNI kalmali, yalnizca tegetsel yon donmeli.

    Aci YUZEY NORMALINE gore olculur; ikosferde carpilan fasetin normali
    tam radyal degildir, dolayisiyla z eksenine gore olcmek yanlis olur."""
    mesh = icosphere(3, 80.0)
    a = 30.0
    gs = [impact_geometry(mesh, np.array([0.0, 0.0, 1.0]), a, az)
          for az in (0.0, 90.0, 180.0)]
    nrm = gs[0].normal
    for g in gs:
        assert np.allclose(g.normal, nrm, atol=1e-12)   # ayni faset
        cos_t = float(np.dot(-g.direction, g.normal))
        assert math.degrees(math.acos(min(1.0, cos_t))) == pytest.approx(a, abs=1e-9)
    # az=0 ve az=180 tegetsel bilesende zit olmali
    tan = [g.direction + float(np.dot(g.direction, nrm)) * -nrm for g in gs]
    assert np.allclose(tan[0], -tan[2], atol=1e-9)
    assert not np.allclose(tan[0], tan[1], atol=1e-6)
    assert abs(float(np.dot(tan[0], tan[1]))) < 1e-9   # az=0 ile az=90 dik


def test_elipsoitte_normal_kureden_farkli():
    """Duzensiz sekilde normal, merkez-noktasi yonuyle AYNI DEGILDIR.

    Bu, egikligin neden normale gore tanimlandigini gosterir: 'z eksenine
    gore' demek elipsoitte baska bir carpma acisi olurdu."""
    mesh = ellipsoid(100.0, 60.0, 40.0, subdiv=3)
    aim = np.array([1.0, 1.0, 1.0])
    g = impact_geometry(mesh, aim)
    radial = g.point - mesh.centroid
    radial /= np.linalg.norm(radial)
    assert float(np.dot(g.normal, radial)) < 0.999, "elipsoitte normal radyal olamaz"


# --------------------------- yerlestirme ---------------------------

def test_mermi_hedefe_degmeden_baslar():
    mesh = icosphere(3, 80.0)
    g = impact_geometry(mesh, np.array([0.0, 0.0, 1.0]))
    imp = place_impactor(build_impactor(500), g)
    # her parcacik carpma noktasinin disinda olmali
    d = np.linalg.norm(imp.x - mesh.centroid, axis=1)
    assert d.min() > 80.0, float(d.min())


def test_yerlestirme_kutle_ve_momentumu_korur():
    mesh = icosphere(3, 80.0)
    g = impact_geometry(mesh, np.array([0.3, 0.0, 1.0]), angle_deg=20.0)
    imp = place_impactor(build_impactor(500), g)
    assert imp.total_mass == pytest.approx(DART_MASS, rel=1e-13)
    assert np.linalg.norm(imp.momentum) == pytest.approx(DART_MOMENTUM, rel=1e-12)
    # hiz yonu gelis yonuyle ayni
    v = imp.v[0] / np.linalg.norm(imp.v[0])
    assert np.allclose(v, g.direction, atol=1e-12)


def test_yerlestirme_merkezi_dogru():
    mesh = icosphere(3, 80.0)
    g = impact_geometry(mesh, np.array([0.0, 0.0, 1.0]))
    imp0 = build_impactor(500)
    imp = place_impactor(imp0, g, standoff=5.0)
    merkez = np.mean(imp.x, axis=0)
    assert np.allclose(merkez, g.point - 5.0 * g.direction, atol=1e-9)


def test_negatif_standoff_reddedilir():
    mesh = icosphere(2, 80.0)
    g = impact_geometry(mesh, np.array([0.0, 0.0, 1.0]))
    with pytest.raises(ValueError, match="standoff"):
        place_impactor(build_impactor(100), g, standoff=-1.0)


def test_isin_en_uzak_yuzeyi_secer():
    """Merkezden atilan isin ic kabuklari degil DIS yuzeyi bulmali."""
    mesh = icosphere(3, 80.0)
    g = impact_geometry(mesh, np.array([0.0, 0.0, 1.0]))
    assert g.diagnostics["hit_distance"] == pytest.approx(
        np.linalg.norm(g.point - mesh.centroid), rel=1e-12)
    assert g.diagnostics["hit_distance"] > 70.0
