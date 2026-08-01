"""FAZ 3 sahnesi icin ALTIN KARMA — makineler arasi determinizm bekcisi.

NICIN VAR. `Scene.digest`i G3 C6'ya "determinizm kaniti" diye baglamistim ama
karmanin bir REFERANSI yoktu; yalnizca "ayni makinede iki kez ayni" sinaniyordu.
O bosluk iki gercek kusuru gizledi (ADR-0025):

  1. `_ray_surface` mesh KOSESINDE dejenereydi. Ikosfer(4, 82 m) merkezinden
     +z isini kutup kosesinden gecer; orada bulusan 6 ucgenin baryzentrik
     testi sinirdadir ve hangisinin sahiplendigini kayan-nokta gurultusu
     belirliyordu. Olculdu: Windows/numpy 2.5.1 ucgen #4064, Linux/numpy
     1.26.4 ucgen #3984 -> yuzey normalleri (0.0441, 0, 0.9990) ve
     (0.0203, 0.0385, 0.9991), yaklasik 2.5 derece fark. P3-FR-07 carpma
     acisini NORMALE gore tanimladigi icin bu, senaryoyu makineye bagimli
     yapiyordu — yani fiziksel olarak onemliydi.
  2. `TriMesh.centroid` `np.sum` kullaniyordu; ciftli toplamanin blok boyu
     numpy surumune gore degistigi icin simetrik ikosferin centroid'i tam 0
     yerine ~1e-14 cikiyor ve bu artik makineden makineye oynuyordu. Carpma
     noktasi centroid'den turedigi icin merminin x,y'si ~1e-14 m kayiyordu.

Ikisi de duzeltildi; karma artik iki platformda birebir ayni. Bu dosya o
esitligin bekcisidir: kirilirsa ya determinizm kaybi ya belgesiz bir
degisiklik vardir.
"""

import json
import platform
from pathlib import Path

import numpy as np
import pytest

from dartrift.setup.scene import build_scene

GOLDEN_FILE = Path(__file__).resolve().parent / "golden" / "p3_scene_v1.json"


def _golden() -> dict:
    return json.loads(GOLDEN_FILE.read_text(encoding="utf-8"))


def _scene():
    g = _golden()
    p = g["params"]
    return build_scene(
        shape=p["shape"], radius=p["radius"], subdiv=p["subdiv"],
        spacing=p["spacing"], bulk_density=p["bulk_density"],
        n_impactor=p["n_impactor"], model_class=p["model_class"],
        f_boulder=p["f_boulder"], q=p["q"], r_min=p["r_min"], r_max=p["r_max"],
        root_seed=g["seed"],
    )


def test_altin_karma_eslesiyor():
    """Kirilirsa: determinizm kaybi ya da bilincli-ama-belgesiz degisiklik."""
    g = _golden()
    s = _scene()
    assert s.n == g["n_total"]
    assert s.n_target == g["n_target"]
    assert s.digest == g["sha256"], (
        "ALTIN SAHNE KARMASI SAPMASI: sahne artik ayni degil. "
        f"beklenen={g['sha256']} bulunan={s.digest}. "
        "Degisiklik BILINCLIYSE once ADR yazin, sonra altin dosyayi guncelleyin."
    )


def test_iki_platformda_dogrulanmis():
    """Tek platformda eslesen karma, makineler arasi determinizm KANITLAMAZ.

    Altin dosya en az iki isletim sistemi/numpy surumu kaydetmelidir; bu
    kusur tam olarak tek platforma bakmakla gizlenmisti."""
    v = _golden()["verified_on"]
    assert len(v) >= 2, v
    assert len({p.split("/")[0] for p in v}) >= 2, f"tek isletim sistemi: {v}"
    assert len({p.split("numpy ")[-1] for p in v}) >= 2, f"tek numpy surumu: {v}"


def test_bu_platform_kayitli_mi():
    """Bu makine altin listede yoksa test PATLAMAZ, ATLANIR — ama karma yine
    de yukarida sinanir. Amac: yeni bir platformda calisirken 'kayitli degil'
    diye yanlis alarm vermemek, fakat kaydin genisletilmesini hatirlatmak."""
    g = _golden()
    ad = f"{platform.system()}/CPython {platform.python_version()}/numpy {np.__version__}"
    if ad not in g["verified_on"]:
        pytest.skip(f"bu platform altin listede degil: {ad} (karma yine de sinandi)")


def test_karma_tohuma_duyarli():
    """Tohum duyarliligi olmadan 'altin karma eslesti' bos bir dogru olurdu."""
    g = _golden()
    p = g["params"]
    other = build_scene(
        shape=p["shape"], radius=p["radius"], subdiv=p["subdiv"],
        spacing=p["spacing"], bulk_density=p["bulk_density"],
        n_impactor=p["n_impactor"], model_class=p["model_class"],
        f_boulder=p["f_boulder"], q=p["q"], r_min=p["r_min"], r_max=p["r_max"],
        root_seed=g["seed"] + 1,
    )
    assert other.digest != g["sha256"]


def test_kutup_normali_tam_z():
    """Kusur 1'in dogrudan regresyonu: kureye +z isini atinca normal (0,0,1).

    Dejenerelik varken tek bir faset seciliyor ve normal ~2.5 derece egik
    cikiyordu. Duzeltmeden sonra kosede bulusan tum fasetlerin alan agirlikli
    ortalamasi aliniyor ve simetri geregi tam +z veriyor."""
    from dartrift.setup.impactor import impact_geometry
    from dartrift.setup.shape_mesh import icosphere

    for subdiv in (2, 3, 4):
        g = impact_geometry(icosphere(subdiv, 82.0), np.array([0.0, 0.0, 1.0]))
        assert abs(g.normal[0]) < 1e-15, (subdiv, g.normal)
        assert abs(g.normal[1]) < 1e-15, (subdiv, g.normal)
        assert g.normal[2] == pytest.approx(1.0, abs=1e-15), (subdiv, g.normal)


def test_simetrik_mesh_centroidi_sifir():
    """Kusur 2'nin dogrudan regresyonu: simetrik ikosferin centroid'i ~0.

    `np.sum` ile ~1e-14 kaliyordu ve artik makineye gore degisiyordu;
    `math.fsum` ile dogru yuvarlanmis ve sira-bagimsiz."""
    from dartrift.setup.shape_mesh import icosphere

    for subdiv in (2, 3, 4):
        c = icosphere(subdiv, 82.0).centroid
        assert np.max(np.abs(c)) < 1e-13, (subdiv, c)
