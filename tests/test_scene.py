"""Sahne birlestirici testleri (FAZ 3 teslimi: tek yeniden uretilebilir sahne)."""

import numpy as np
import pytest

from dartrift.config import ConfigError, load_config
from dartrift.setup.impactor import DART_MASS, DART_MOMENTUM
from dartrift.setup.scene import build_scene, scene_from_config

BASE = dict(radius=82.0, spacing=8.0, n_impactor=400, root_seed=11)
M1 = dict(BASE, model_class="M1", f_boulder=0.25, q=3.0, r_min=16.0, r_max=48.0)


# --------------------------- determinizm ---------------------------

def test_ayni_tohum_ayni_sahne():
    assert build_scene(**M1).digest == build_scene(**M1).digest


def test_tohum_degisince_sahne_degisir():
    a = build_scene(**M1)
    c = build_scene(**dict(M1, root_seed=12))
    assert a.digest != c.digest


def test_homojen_sahnede_tohum_etkisiz():
    """M0'da rastgelelik YOKTUR; ayni sahne cikmasi dogru davranistir.

    Bu testi yazmamin sebebi: ilk denememde M0'da tohum degistirip 'digest
    degismedi' diye kusur sandim. Kusur yoktu — M0 tamamen deterministik bir
    kafes dolduruyor. Beklentiyi kayda geciriyorum ki bir daha yanlis
    okunmasin."""
    a = build_scene(**BASE)
    b = build_scene(**dict(BASE, root_seed=99))
    assert a.digest == b.digest


def test_digest_yalnizca_fiziksel_durumu_kapsar():
    """Tani sozlugu degisse bile karma degismemeli (makineler arasi kararlilik)."""
    a = build_scene(**BASE)
    b = build_scene(**BASE)
    object.__setattr__(b, "diagnostics", {"tamamen": "farkli"})
    assert a.digest == b.digest


# --------------------------- korunum ---------------------------

def test_mermi_kutlesi_ve_momentumu_korunur():
    s = build_scene(**BASE)
    sel = s.is_impactor
    assert float(np.sum(s.m[sel])) == pytest.approx(DART_MASS, rel=1e-12)
    assert float(np.linalg.norm(s.impactor_momentum)) == pytest.approx(
        DART_MOMENTUM, rel=1e-12)


def test_hedef_mermiden_mertebelerce_agir():
    s = build_scene(**BASE)
    assert s.diagnostics["mass_ratio_target_over_impactor"] > 1.0e6


def test_hedef_yogunlugu_geri_olculur():
    s = build_scene(**BASE, bulk_density=1800.0)
    assert s.diagnostics["bulk_density_measured"] == pytest.approx(1800.0, rel=0.01)


# --------------------------- malzeme ---------------------------

def test_mermi_gozeneksiz():
    """Mermi uzay aracidir; hedefin gozenekli matris malzemesini almamali."""
    s = build_scene(**M1)
    assert np.all(s.alpha0[s.is_impactor] == 1.0)
    assert np.any(s.alpha0[~s.is_impactor] > 1.0)


def test_bloklar_matristen_ayri_malzeme():
    s = build_scene(**M1)
    t = ~s.is_impactor
    assert len(np.unique(s.alpha0[t])) > 1
    assert len(np.unique(s.Y0[t])) > 1
    # blok daha dayanikli, daha az gozenekli
    b, mtx = s.is_boulder & t, (~s.is_boulder) & t
    assert s.Y0[b].max() > s.Y0[mtx].max()
    assert s.alpha0[b].max() < s.alpha0[mtx].max()


def test_mermi_hedefe_degmeden_baslar():
    s = build_scene(**BASE)
    d = np.linalg.norm(s.x[s.is_impactor], axis=1)
    assert d.min() > 82.0, float(d.min())


def test_hedef_durgun_baslar():
    """Settling kosulmadan hedefin hizi TAM sifir olmali; aksi halde beta
    olcumu mermiden gelmeyen bir hareketle kirlenir."""
    s = build_scene(**BASE)
    assert np.all(s.v[~s.is_impactor] == 0.0)


def test_carpma_yonu_birim_ve_iceri():
    s = build_scene(**BASE)
    assert np.linalg.norm(s.impact_direction) == pytest.approx(1.0, rel=1e-13)
    assert float(np.dot(s.impact_direction, s.surface_normal)) < 0.0


def test_egik_carpma_gecer():
    s = build_scene(**dict(BASE, angle_deg=45.0, azimuth_deg=30.0))
    cos_t = float(np.dot(-s.impact_direction, s.surface_normal))
    assert np.degrees(np.arccos(min(1.0, cos_t))) == pytest.approx(45.0, abs=1e-9)


def test_elipsoit_sahne():
    s = build_scene(shape="ellipsoid", semi_axes=[100.0, 70.0, 60.0],
                    radius=None, spacing=10.0, n_impactor=200, root_seed=3)
    assert s.n > 0 and s.n_target > 0


def test_obj_yolundan_sahne_kurulur(tmp_path):
    """Gercek PDS sekil modeli bu yoldan girecek; basarili yol da sinanmali.

    `shape="obj"` icin yalnizca HATA durumu test ediliyordu; basarili yol hic
    kosulmamisti. Gercek veri geldiginde ilk kez orada calisacak bir kod
    yolunu test edilmemis birakmak, en kotu zamanda surpriz demektir."""
    from dartrift.setup.shape_mesh import icosphere

    mesh = icosphere(2, 82.0)
    # .17g: float64'u tam gerideleyen en kisa gosterim. `!r` kullanmak numpy
    # skalerlerini "np.float64(-43.1)" diye yazar ve OBJ ayristirilamaz olur.
    satirlar = [f"v {float(p[0]):.17g} {float(p[1]):.17g} {float(p[2]):.17g}"
                for p in mesh.v]
    satirlar += [f"f {a + 1} {b + 1} {c + 1}" for a, b, c in mesh.f]
    obj = tmp_path / "hedef.obj"
    obj.write_text("\n".join(satirlar) + "\n", encoding="utf-8")

    s = build_scene(shape="obj", obj_path=str(obj), radius=None,
                    spacing=12.0, n_impactor=100, root_seed=7)
    assert s.n_target > 0
    assert s.diagnostics["shape"] == "obj"
    # OBJ'den okunan mesh, analitik ikosferle ayni hacmi vermeli
    assert s.mesh_volume == pytest.approx(mesh.volume, rel=1e-9)
    assert float(np.sum(s.m[s.is_impactor])) == pytest.approx(DART_MASS, rel=1e-12)


def test_gecersiz_sekil_reddedilir():
    with pytest.raises(ValueError, match="bilinmeyen sekil"):
        build_scene(shape="kup", spacing=8.0, n_impactor=100)
    with pytest.raises(ValueError, match="radius zorunlu"):
        build_scene(shape="icosphere", radius=None, spacing=8.0, n_impactor=100)
    with pytest.raises(ValueError, match="semi_axes zorunlu"):
        build_scene(shape="ellipsoid", semi_axes=None, spacing=8.0, n_impactor=100)
    with pytest.raises(ValueError, match="obj_path zorunlu"):
        build_scene(shape="obj", obj_path=None, spacing=8.0, n_impactor=100)


# --------------------------- config yolu ---------------------------

def test_config_sahnesi_kurulur(tmp_path):
    cfg = load_config("configs/p3_scene.yaml")
    assert cfg.scene is not None
    s = scene_from_config(cfg)
    assert s.n > 0
    # tohum config'den gelmeli, ayri bir alandan degil
    assert s.diagnostics["root_seed"] == cfg.random_seed


def test_config_sahnesiz_ise_acik_hata():
    cfg = load_config("configs/p0_smoke.yaml")
    with pytest.raises(ValueError, match="scene"):
        scene_from_config(cfg)


def test_sema_nokta_mermiyi_reddeder(tmp_path):
    """P3-FR-06 yasagi yalnizca kodda kalirsa bir config ile atlanabilirdi."""
    raw = (tmp_path / "kotu.yaml")
    raw.write_text(
        "schema_version: 1\nrun_id: kotu\nrandom_seed: 1\n"
        "numerics: {precision: fp64}\n"
        "scene:\n  target: {shape: icosphere, radius: 80.0, spacing: 8.0,"
        " bulk_density: 1800.0}\n  impactor: {n_particles: 1}\n",
        encoding="utf-8")
    with pytest.raises(ConfigError):
        load_config(raw)


def test_sema_M1_blok_kesri_ister(tmp_path):
    raw = (tmp_path / "kotu2.yaml")
    raw.write_text(
        "schema_version: 1\nrun_id: kotu2\nrandom_seed: 1\n"
        "numerics: {precision: fp64}\n"
        "scene:\n  target: {shape: icosphere, radius: 80.0, spacing: 8.0,"
        " bulk_density: 1800.0, model_class: M1}\n"
        "  impactor: {n_particles: 200}\n",
        encoding="utf-8")
    with pytest.raises(ConfigError):
        load_config(raw)
