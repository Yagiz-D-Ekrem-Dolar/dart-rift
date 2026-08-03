"""Kapinin KANIT URETEN kodunu sinar (`validation/scene_checks`).

NICIN GEREKLI: bu modul yalnizca `scripts/run_g3_gate.py` tarafindan cagriliyor,
kapi da pytest'i AYRI BIR SUREC olarak kosturdugu icin hicbir test onu import
etmiyordu. Kapsam olcumu bunu %0.0 olarak gosterdi.

Kanit ureten kodun kendisi sinanmazsa, kapi yanlis bir sayiyi guvenle
raporlar ve hicbir sey yakalamaz — kapinin varlik sebebini bosa cikarir.
Buradaki testler sonuclarin BEKLENEN ANAHTARLARI tasidigini ve degerlerin
fiziksel olarak makul araliklarda oldugunu dogrular.

Fixture'lar MODUL kapsamindadir: senaryolar pahalidir (yigin uretimi, sahne
kurulumu) ve her test icin yeniden kosmalari bos maliyettir.
"""

import numpy as np
import pytest

from dartrift.validation.scene_checks import (
    run_impactor_convergence,
    run_observable_selftest,
    run_rubble_quality,
    run_scene_determinism,
    run_shape_pipeline,
)


@pytest.fixture(scope="module")
def shape():
    return run_shape_pipeline()


@pytest.fixture(scope="module")
def rubble():
    return run_rubble_quality()


@pytest.fixture(scope="module")
def impactor():
    return run_impactor_convergence()


@pytest.fixture(scope="module")
def obs():
    return run_observable_selftest()


@pytest.fixture(scope="module")
def scene():
    return run_scene_determinism()


# --------------------------- sekil hatti ---------------------------

def test_sekil_anahtarlari(shape):
    for k in ("cases", "volume_error_ladder", "volume_converges",
              "all_manifold", "max_volume_rel_err"):
        assert k in shape, k


def test_sekil_manifold_ve_yakinsak(shape):
    assert shape["all_manifold"] is True
    assert shape["volume_converges"] is True
    assert shape["max_volume_rel_err"] < 0.01


def test_sekil_merdiveni_monoton_azaliyor(shape):
    e = shape["volume_error_ladder"]
    assert len(e) == 3 and e[0] > e[1] > e[2]


def test_sekil_hacimleri_analitige_yakin(shape):
    for ad, c in shape["cases"].items():
        assert c["volume_rel_err"] < 0.01, (ad, c)
        assert c["n_faces"] > 0 and c["n_vertices"] > 0


# --------------------------- moloz yigini ---------------------------

def test_yigin_yogunluk_ve_komsuluk(rubble):
    assert rubble["bulk_density_rel_err"] < 0.01
    # FCC teorik komsuluk 12; ic bolgede buna ulasmali
    assert 11.0 <= rubble["coordination_interior_mean"] <= 12.01


def test_yigin_determinizm_ve_heterojenlik(rubble):
    assert rubble["deterministic"] is True
    assert rubble["alpha0_distinct"] is True and rubble["Y0_distinct"] is True


def test_yigin_doyma_bayragi_kesirle_tutarli(rubble):
    """Kesir hedefin belirgin altindaysa doyma bayragi ACIK olmali.

    Bayrak kapaliyken dusuk kesir donmek, ulasilamayan bir hedefi sessizce
    kabul etmek olurdu."""
    if rubble["boulder_fraction_measured"] < 0.9 * rubble["boulder_fraction_target"]:
        assert rubble["boulder_saturated"] is True, rubble


# --------------------------- mermi yakinsamasi ---------------------------

def test_mermi_uc_cozunurluk_ve_yakinsama(impactor):
    assert impactor["n_resolutions"] >= 3          # P3-VR-02
    assert impactor["volume_error_converges"] is True


def test_mermi_nokta_parcacik_degil(impactor):
    assert impactor["no_point_particle"] is True
    assert impactor["min_particles_across"] >= 5.0


def test_mermi_kutle_momentum_tam(impactor):
    assert impactor["max_mass_rel_err"] < 1e-12
    assert impactor["max_momentum_rel_err"] < 1e-12


def test_mermi_hedefin_disinda_basliyor(impactor):
    assert impactor["starts_outside_target"] is True


def test_mermi_dik_carpma_geometrisi(impactor):
    assert impactor["impact_angle_deg"] == pytest.approx(0.0, abs=1e-12)
    assert impactor["cos_incidence"] == pytest.approx(1.0, abs=1e-12)


# --------------------------- gozlenebilir oz-sinavi ---------------------------

def test_beta_bilinen_degeri_geri_veriyor(obs):
    """Sahne beta=3.0 verecek sekilde kuruldu; cikarici onu bulmali."""
    assert obs["beta_recovery_rel_err"] < 1e-9, obs["beta_recovery_rel_err"]


def test_momentum_defteri_kapaniyor(obs):
    assert obs["momentum_closure"] < 1e-9, obs["momentum_closure"]


def test_duyarlilik_raporlaniyor(obs):
    assert obs["sensitivity_reported"] is True
    assert obs["beta_min"] <= obs["beta_median"] <= obs["beta_max"]
    assert obs["beta_relative_spread"] > 0.0


def test_uslu_yasa_usu_geri_kazaniliyor(obs):
    assert obs["ejecta_power_law_rel_err"] < 0.10, obs
    assert obs["ejecta_power_law_r2"] > 0.95, obs


def test_ejekta_konisi_makul(obs):
    # sahne 15-45 derece arasi uretiyor -> agirlikli ortalama bu bantta
    assert 15.0 < obs["ejecta_cone_angle_deg"] < 45.0
    assert obs["ejecta_direction_ok"] is True


def test_krater_kuresel_degisimden_ayrisiyor(obs):
    assert obs["crater_separates_global"] is True
    assert obs["crater_depth"] > 0.5 * obs["crater_depth_expected"]


def test_dart_periyodundan_beta_makul(obs):
    """ONCEKI BAND (2,5-4,5) HICBIR SEY AYIRT ETMIYORDU.

    Bu sayi FAZ 4+'ta modelin hedefleyecegi degerdir. 2 birim genisliginde bir
    band, dogru sonucla %10 sapmis sonucu ayni sayar. Olculen deger 3,2225'tir
    ve bu arayuzun (dairesel iki-cisim) kesin ciktisidir — dar tutulmali ki
    girdi sabitlerinden biri sessizce degisirse test bunu yakalasin.
    """
    assert obs["beta_from_dart_period"] == pytest.approx(3.2225, rel=1e-3)


def test_dart_beta_farki_kutle_varsayimina_baglaniyor(obs):
    """Yayinlanan ~3,6 ile aradaki %10,5 fark ACIKLANMIS olmali.

    Kritik olcum: Delta_T'nin +/-1,0 dakikalik bandi [3,125 ; 3,320] ve bu
    band 3,6'yi ICERMIYOR. Yani fark periyot olcumunun hatasiyla aciklanamaz;
    kaynagi kutle varsayimidir. beta kutleyle dogru orantili oldugundan
    yayinlanan degeri verecek kutle 4,80e9 kg'dir (varsayilan 4,3e9).
    Bunu "olcum belirsizligi icinde" diye gecistirmek olculene aykiri olurdu.
    """
    assert obs["beta_dart_low"] < obs["beta_from_dart_period"] < obs["beta_dart_high"]
    assert obs["beta_dart_band_covers_published"] is False, (
        "band 3,6'yi kapsiyorsa fark gercekten olcum hatasidir — "
        "o zaman bu testin gerekcesi degismistir, yeniden olcun")
    assert obs["beta_dart_vs_published_rel"] == pytest.approx(0.105, abs=0.01)
    assert obs["target_mass_for_published_beta"] == pytest.approx(4.80e9, rel=0.02)


# --------------------------- sahne determinizmi ---------------------------

def test_sahne_yeniden_uretilebilir_ve_tohuma_duyarli(scene):
    assert scene["reproducible"] is True
    # tohum duyarliligi olmadan 'yeniden uretilebilir' bos bir dogru olurdu
    assert scene["seed_sensitive"] is True


def test_sahne_karma_bicimi(scene):
    assert len(scene["digest"]) == 64
    assert all(ch in "0123456789abcdef" for ch in scene["digest"])


def test_sahne_fiziksel_butunluk(scene):
    assert scene["impactor_outside_target"] is True
    assert scene["target_at_rest"] is True
    assert scene["impactor_nonporous"] is True and scene["target_porous"] is True
    assert scene["material_heterogeneous"] is True


def test_sahne_kutle_momentum_korunumu(scene):
    assert scene["impactor_mass_rel_err"] < 1e-12
    assert scene["impactor_momentum_rel_err"] < 1e-12


def test_sahne_hedef_mermiden_cok_agir(scene):
    assert scene["mass_ratio"] > 1.0e6
    assert scene["n_target"] > scene["n_impactor"]


# --------------------------- sonluluk ---------------------------

def test_tum_kanit_alanlari_sonlu(shape, rubble, impactor, obs, scene):
    """Hicbir kanit alani NaN/inf olmamali — sessiz NaN 'olculdu' diye gecer."""
    for ad, r in (("shape", shape), ("rubble", rubble), ("impactor", impactor),
                  ("obs", obs), ("scene", scene)):
        for k, v in r.items():
            if isinstance(v, float):
                assert np.isfinite(v), f"{ad}.{k} = {v}"


def test_mermi_disarida_olcumu_VEKIL_DEGIL(scene):
    """ADR-0035: 'mermi hedefin disinda mi' DOGRUDAN olculur.

    Onceki olcut `|x|_min > target_radius` idi; `target_radius` ESDEGER KURE
    yaricapidir ve yalnizca KURE icin gecerli bir vekildir. Denetim kure
    uzerinde kosuldugu icin vekil TESADUFEN dogruydu — uretim konfigurasyonu
    ise gercek PDS seklini kullaniyor.

    Olculdu (Dimorphos oranlarinda elipsoit 88x87x65 m, KISA eksende carpma):
        r_eff                       = 39,59 m
        merminin en yakin parcacigi = 32,63 m
        vekil olcut (|x| > r_eff)   = False    <-- YANLIS NEGATIF
        mesh icindeki mermi parcaci = 0/207    <-- GERCEKTE DISARIDA
    """
    assert scene["impactor_outside_target"] is True
    assert scene["impactor_particles_inside_mesh"] == 0


def test_duzensiz_cisimde_de_mermi_disarida(scene):
    """Vekilin kirildigi yer: duzensiz cisim. Iki eksende de sinanir."""
    assert scene["irregular_all_outside"] is True
    assert all(v == 0 for v in scene["irregular_impactor_inside_mesh"].values()), \
        scene["irregular_impactor_inside_mesh"]


def test_vekil_olcutun_yanildigi_KAYITLI(scene):
    """Bosluk kontrolu: vekil gercekten yaniliyor mu?

    Yanilmiyorsa bu duzeltmenin gerekcesi kaybolmus demektir ve yukaridaki
    iki test bos bir dogruyu sinar. Kayit, kisa eksende vekilin YANLIS NEGATIF
    verdigini gostermeli.
    """
    assert scene["irregular_proxy_disagrees"] is True
    kisa = scene["irregular_detail"]["kisa_eksen"]
    assert kisa["n_inside_mesh"] == 0            # gercekte disarida
    assert kisa["proxy_says_outside"] is False   # ama vekil "degil" diyor
    assert kisa["min_dist"] < kisa["r_eff"]
