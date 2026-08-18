"""Gercek PDS Dimorphos sekil modeli — G3 C7'nin veri tarafi.

Bu testler **veri varsa** kosar, yoksa ATLANIR: depo veri tasimaz (100+ MB),
veri `scripts/fetch_pds_shapemodel.py` ile indirilir ve
`data_manifest/dart_shapemodel.json` manifestiyle kayda gecer.

DOGRULAMA STRATEJISI: sekil modelinin gecerliligi, DIS KAYNAKLA kontrol
edilir — Daly ve digerleri (2023, Nature) Dimorphos icin esdeger yaricapi
~75 m veriyor. Kendi okuyucumuzun ciktisini kendi beklentimizle degil,
yayimlanmis bir sayiyla karsilastiriyoruz.
"""

import json
import os
from pathlib import Path

import numpy as np
import pytest

from dartrift.setup.shape_mesh import load_obj, orient_outward

REPO = Path(__file__).resolve().parents[1]
MANIFEST = REPO / "data_manifest" / "dart_shapemodel.json"


def _manifest() -> dict | None:
    if not MANIFEST.is_file():
        return None
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def _kokler(m: dict) -> list[Path]:
    """Veri dizini adaylari — manifest TASINABILIR oldugu icin arama gerekir.

    Sira: ortam degiskeni, manifestin uretildigi dizin, depo icindeki
    varsayilan. Boylece ayni manifest hem TRUBA'da hem yerelde calisir.
    """
    kok = []
    if os.environ.get("DARTRIFT_PDS_DIR"):
        kok.append(Path(os.environ["DARTRIFT_PDS_DIR"]))
    if m.get("data_root"):
        kok.append(Path(m["data_root"]))
    kok.append(REPO / "data" / "pds")
    return kok


def _urun(ad_parcasi: str) -> Path | None:
    m = _manifest()
    if m is None:
        return None
    for u in m.get("products", []):
        if ad_parcasi in u["filename"]:
            for kok in _kokler(m):
                p = kok / u["filename"]
                if p.is_file():
                    return p
    return None


def _gerekli(ad_parcasi: str) -> Path:
    p = _urun(ad_parcasi)
    if p is None:
        pytest.skip(f"PDS urunu yok ({ad_parcasi}); "
                    "scripts/fetch_pds_shapemodel.py ile indirin")
    return p


# --------------------------- manifest ---------------------------

def test_manifest_semasi():
    m = _manifest()
    if m is None:
        pytest.skip("data_manifest/dart_shapemodel.json yok")
    assert m["bundle"] == "urn:nasa:pds:dart_shapemodel::1.0"
    assert m["products"], "manifest bos"
    for u in m["products"]:
        assert u["product_id"] and u["sha256"], u
        assert len(u["sha256"]) == 64
        assert u["bytes"] > 0


def test_manifest_resmi_md5_ile_dogrulanmis():
    """Kendi karmamiz 'diskte ne var' der; ARSIVIN karmasi 'dogru dosya mi'.

    Ikisi ayri sorudur. Manifest her urun icin arsivin resmi MD5'ini de
    tasimali ve eslesme kaydedilmis olmali."""
    m = _manifest()
    if m is None:
        pytest.skip("manifest yok")
    dogrulanmamis = [u["filename"] for u in m["products"] if not u.get("md5_verified")]
    assert not dogrulanmamis, f"resmi MD5 ile dogrulanmamis urunler: {dogrulanmamis}"


# --------------------------- sekil modeli ---------------------------

def test_dimorphos_boyutu_yayimlanan_degerle_uyusuyor():
    """DIS KAYNAK: Daly ve dig. (2023) Dimorphos esdeger yaricapi ~75 m.

    Model KILOMETRE cinsinden; `units="km"` verilmezse cisim 1000 kat kucuk
    cikar ve bu test tam da onu yakalar."""
    p = _gerekli("dimorphos_g_0972mm")
    mesh = orient_outward(load_obj(p, units="km"))
    r_eq = float((3.0 * mesh.volume / (4.0 * np.pi)) ** (1.0 / 3.0))
    assert 70.0 < r_eq < 82.0, f"esdeger yaricap {r_eq:.2f} m — beklenen ~75 m"


def test_dimorphos_eksen_boyutlari():
    """Dimorphos ~177 x 174 x 116 m (Daly ve dig. 2023)."""
    p = _gerekli("dimorphos_g_0972mm")
    mesh = orient_outward(load_obj(p, units="km"))
    lo, hi = mesh.bounds
    boy = np.sort(hi - lo)[::-1]
    assert 150.0 < boy[0] < 200.0, boy
    assert 150.0 < boy[1] < 200.0, boy
    assert 100.0 < boy[2] < 135.0, boy


def test_metre_saymak_bariz_yanlis_verir():
    """Birim tuzagini acikca sinar: 'm' dersek cisim 1000 kat kucuk cikar."""
    p = _gerekli("dimorphos_g_0972mm")
    mesh = orient_outward(load_obj(p, units="m"))
    r_eq = float((3.0 * mesh.volume / (4.0 * np.pi)) ** (1.0 / 3.0))
    assert r_eq < 1.0, r_eq          # 0.075 m — asteroit degil


def test_mesh_kapali_ve_manifold():
    p = _gerekli("dimorphos_g_0972mm")
    mesh = orient_outward(load_obj(p, units="km"))
    assert mesh.is_edge_manifold(), "PDS mesh'i kenar-manifold degil"
    # ADR-0038: kenar-manifold TERS SARIMI goremez ve YUKLENEN OBJ'de
    # karsilastirilacak analitik hacim YOKTUR — yakalayan baska sey yok.
    assert mesh.is_consistently_oriented(), (
        "PDS mesh'inde yonelim tutarsiz: bazi ucgenler ters sarilmis. "
        "Hacim (ve ondan turetilen yigin yogunlugu, blok hedefi, etkin "
        "yaricap) sessizce yanlis olurdu.")
    assert mesh.volume > 0.0, "disa yonlendirme sonrasi hacim pozitif olmali"


def test_cozunurlukler_ayni_hacme_yakinsiyor():
    """Uc cozunurluk ayni cismi tarif etmeli; hacimleri %1 icinde olmali."""
    hacimler = []
    for res in ("1940mm", "0972mm", "0487mm"):
        p = _urun(f"dimorphos_g_{res}")
        if p is None:
            continue
        hacimler.append(orient_outward(load_obj(p, units="km")).volume)
    if len(hacimler) < 2:
        pytest.skip("en az iki cozunurluk gerekli")
    h = np.array(hacimler)
    assert (h.max() - h.min()) / h.mean() < 0.01, h


def test_didymos_dimorphos_tan_buyuk():
    """Didymos birincil cisim: Dimorphos'tan mertebe olarak buyuk olmali."""
    pd = _urun("didymos_g_2329mm")
    pm = _urun("dimorphos_g_0972mm")
    if pd is None or pm is None:
        pytest.skip("her iki sekil modeli de gerekli")
    vd = orient_outward(load_obj(pd, units="km")).volume
    vm = orient_outward(load_obj(pm, units="km")).volume
    assert vd > 10.0 * vm, (vd, vm)


# --------------------------- hatta baglanti ---------------------------

def test_gercek_sekilden_sahne_kurulur():
    """P3-FR-01'in asil hedefi: gercek sekil modeli sahneye girebilmeli."""
    from dartrift.setup.scene import build_scene

    p = _gerekli("dimorphos_g_1940mm")
    s = build_scene(shape="obj", obj_path=str(p), obj_units="km", radius=None,
                    spacing=12.0, n_impactor=200, root_seed=5)
    assert s.n_target > 100
    assert s.diagnostics["shape"] == "obj"
    # hedef yaricapi yayimlanan degere yakin
    assert 70.0 < s.target_radius < 82.0, s.target_radius
    # yigin yogunlugu istenen degeri vermeli
    assert abs(s.diagnostics["bulk_density_measured"] - 1800.0) / 1800.0 < 0.02
