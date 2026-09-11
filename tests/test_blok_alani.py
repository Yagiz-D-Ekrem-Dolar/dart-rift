"""A74 — blok alanı: hedef kesir, gerçek hacim, geometriden malzeme.

Uzman (2026-09-11) üç kusur gösterdi, üçü de burada ÖLÇÜLDÜ:

1. **Kesir düğmesi ölü.** v1 yerleştirici sonlu deneme bütçesinde
   doyuyor: aynı tohumla `f = 0,4304` ve `0,55` AYNI 23 bloğu veriyor
   (SHA eşit), gerçekleşen `0,3707`. Ölçüldü: üç tohumun üçünde de
   (`0,349 – 0,371`'de doyuyor).
2. **Yüzeyde blok yok.** 14 yönlü "tamamen içinde" sınaması.
3. **İnce parçacık malzemeyi kabadan kopyalıyor.** Kaba kafesin
   örneklemediği blok ince ağda HİÇ görünmüyor.

v2 (`place_boulders_v2`) ve `malzeme_kaynagi = "geometri"` bunları
kapatıyor; v1 ve `"kaba"` varsayılan olarak BİT-AYNI kalıyor.
"""
from __future__ import annotations

import hashlib
from types import SimpleNamespace

import numpy as np
import pytest

from dartrift.setup.refine import _ince_malzeme
from dartrift.setup.rubble_generator import (
    BoulderField,
    _NoktaIzgarasi,
    assign_material,
    blok_hacim_kesri,
    build_rubble_pile,
    kure_birlesimi_ici,
    place_boulders,
    place_boulders_v2,
)
from dartrift.setup.scene import _build_mesh


@pytest.fixture(scope="module")
def mesh82():
    return _build_mesh("icosphere", radius=82.0, subdiv=4)


def _sha(bf: BoulderField) -> str:
    h = hashlib.sha256()
    h.update(np.ascontiguousarray(bf.centers).tobytes())
    h.update(np.ascontiguousarray(bf.radii).tobytes())
    return h.hexdigest()


# --- 1. v1 kusuru KILITLI (duzeltilmedi, belgelendi) --------------------

def test_v1_iki_farkli_kesir_AYNI_geometriyi_veriyor(mesh82):
    """Uzmanın ölçümü: tohum `20260906`, 23 blok, küre kesri `0,3707`."""
    a = place_boulders(mesh82, 0.4303689, 3.0, 14.0, 42.0, 20260906)
    b = place_boulders(mesh82, 0.55, 3.0, 14.0, 42.0, 20260906)
    assert _sha(a) == _sha(b), "v1 artik doymuyorsa bu test guncellenmeli"
    assert len(a.radii) == 23
    assert a.volume / mesh82.volume == pytest.approx(0.3707, abs=5e-4)


# --- 2. v2 hedefe ULASIYOR ya da acikca DOYUYOR ------------------------

@pytest.mark.parametrize("f", [0.25, 0.30, 0.43])
def test_v2_hedef_hacim_kesrine_ULASIYOR(mesh82, f):
    """Aşım üst sınırı TÜRETİLMİŞ: son eklenen blok en çok bir
    `r_max` bloğudur, ama büyükten küçüğe dizildiği için pratikte küçük;
    ölçülen aşım `0,003 – 0,005`. Eşik: `4/3 π r_max³ / V` (tek blok)."""
    bf, t = place_boulders_v2(mesh82, f, 3.0, 14.0, 42.0, 20260906)
    assert not t["doydu"]
    tek_blok = 4.0 / 3.0 * np.pi * 42.0 ** 3 / mesh82.volume
    assert f <= t["f_gercek"] < f + tek_blok
    # bagimsiz yeniden olcum ayni sayiyi vermeli (ayni MC noktalari)
    mc = blok_hacim_kesri(mesh82, bf, root_seed=20260906)
    assert mc["f"] == pytest.approx(t["f_gercek"], abs=1e-12)


def test_v2_farkli_kesirler_FARKLI_sahneler(mesh82):
    shalar, gercek = set(), []
    for f in (0.25, 0.30, 0.43):
        bf, t = place_boulders_v2(mesh82, f, 3.0, 14.0, 42.0, 20260906)
        shalar.add(_sha(bf))
        gercek.append(t["f_gercek"])
    assert len(shalar) == 3
    assert gercek == sorted(gercek)


def test_v2_ulasilamayan_kesri_BILDIRIYOR(mesh82):
    """14–42 m bloklarla `R = 82`'de ölçülen tavan `~0,49–0,51`."""
    _, t = place_boulders_v2(mesh82, 0.55, 3.0, 14.0, 42.0, 20260906)
    assert t["doydu"] and t["f_gercek"] < 0.55


def test_v2_yuzeyi_kesen_bloklara_IZIN_veriyor(mesh82):
    _, t = place_boulders_v2(mesh82, 0.30, 3.0, 14.0, 42.0, 20260906)
    assert t["n_yuzeyi_kesen"] > 0
    assert t["yuzey_kesisimi"] is True


def test_v2_fiziksel_blok_boyutlarinda_calisiyor(mesh82):
    """`r = 1,7 – 6,5 m`: binlerce blok, saniyeler içinde, tam hedef."""
    bf, t = place_boulders_v2(mesh82, 0.30, 3.0, 1.7, 6.5, 20260906)
    assert not t["doydu"]
    assert t["n_blok"] > 1000
    assert 0.30 <= t["f_gercek"] < 0.30 + 4.0 / 3.0 * np.pi * 6.5 ** 3 / mesh82.volume


def test_v2_sabit_bloklar_ONCE_ve_AYNEN_yerlesiyor(mesh82):
    sabit = [((0.0, 0.0, 75.0), 6.5), ((10.0, 0.0, 70.0), 3.0)]
    bf, t = place_boulders_v2(mesh82, 0.20, 3.0, 1.7, 6.5, 20260906,
                              sabit_bloklar=sabit)
    assert t["n_sabit"] == 2
    np.testing.assert_array_equal(bf.centers[0], [0.0, 0.0, 75.0])
    assert bf.radii[0] == 6.5 and bf.radii[1] == 3.0


def test_v2_cakisan_sabit_bloklar_REDDEDILIYOR(mesh82):
    with pytest.raises(ValueError, match="cakisiyor"):
        place_boulders_v2(mesh82, 0.2, 3.0, 1.7, 6.5, 1,
                          sabit_bloklar=[((0, 0, 70), 5.0), ((1, 0, 70), 5.0)])


def test_v2_bloklar_CAKISMIYOR(mesh82):
    bf, _ = place_boulders_v2(mesh82, 0.30, 3.0, 1.7, 6.5, 7)
    C, R = bf.centers, bf.radii
    rng = np.random.default_rng(0)
    for i in rng.choice(len(R), size=200, replace=False):
        d = np.linalg.norm(C - C[i], axis=1)
        d[i] = np.inf
        assert np.all(d >= R + R[i] - 1e-9)


def test_v2_DETERMINISTIK(mesh82):
    a, _ = place_boulders_v2(mesh82, 0.30, 3.0, 14.0, 42.0, 5)
    b, _ = place_boulders_v2(mesh82, 0.30, 3.0, 14.0, 42.0, 5)
    assert _sha(a) == _sha(b)


# --- build_rubble_pile v2 ------------------------------------------------

def test_yigin_v2_ulasilamayan_kesirde_HATA(mesh82):
    with pytest.raises(ValueError, match="ULASILAMADI"):
        build_rubble_pile(mesh82, spacing=7.0, bulk_density=1800.0,
                          root_seed=20260906, rho0_solid=2700.0,
                          model_class="M1", f_boulder=0.55, q=3.0,
                          r_min=14.0, r_max=42.0, blok_uretici="v2")


def test_yigin_v2_kesri_HACIMDEN_cozuyor_ve_sapmayi_RAPORLUYOR(mesh82):
    p = build_rubble_pile(mesh82, spacing=7.0, bulk_density=1800.0,
                          root_seed=20260906, rho0_solid=2700.0,
                          model_class="M1", f_boulder=0.30, q=3.0,
                          r_min=14.0, r_max=42.0, blok_uretici="v2")
    d = p.diagnostics
    assert d["blok_uretici"] == "v2"
    assert d["blok_f_gercek"] >= 0.30
    # matris distansiyonu HACIM kesrinden: rho_s [f/a_b + (1-f)/a_m] = rho_y
    f, ab, am = d["blok_f_gercek"], 1.05, d["matrix_alpha0_used"]
    assert 2700.0 * (f / ab + (1.0 - f) / am) == pytest.approx(1800.0, rel=1e-12)
    assert "yogunluk_sapmasi_kafes" in d and "blok_kesri_kafes" in d


def test_yigin_varsayilan_hala_v1(mesh82):
    p = build_rubble_pile(mesh82, spacing=7.0, bulk_density=1800.0,
                          root_seed=20260906, rho0_solid=2700.0,
                          model_class="M1", f_boulder=0.25, q=3.0,
                          r_min=14.0, r_max=42.0)
    assert p.diagnostics["blok_uretici"] == "v1"
    # v1'in kendi tutarliligi: yogunluk kafeste TAM tutuyor
    assert p.diagnostics["bulk_density_achieved"] == pytest.approx(1800.0, rel=1e-12)


# --- izgara ve birlesim: kaba kuvvete KARSI kesin ------------------------

def test_nokta_izgarasi_kaba_kuvvetle_AYNI():
    rng = np.random.default_rng(3)
    P = rng.uniform(-10, 10, (5000, 3))
    izg = _NoktaIzgarasi(P, hucre=2.5)
    for _ in range(50):
        c = rng.uniform(-12, 12, 3)
        r = float(rng.uniform(0.1, 6.0))
        beklenen = np.flatnonzero(np.sum((P - c) ** 2, axis=1) < r * r)
        assert np.array_equal(np.sort(izg.kure_ici(c, r)), beklenen)


def test_kure_birlesimi_assign_material_ile_AYNI():
    rng = np.random.default_rng(4)
    P = rng.uniform(-20, 20, (20000, 3))
    bf = BoulderField(rng.uniform(-15, 15, (40, 3)), rng.uniform(0.5, 4.0, 40))
    _, _, eski = assign_material(P, bf, 1.5, 1e4, 1.05, 1e7)
    assert np.array_equal(kure_birlesimi_ici(P, bf.centers, bf.radii), eski)


# --- 3. ince parcacik malzemesi: geometriden -----------------------------

def _kaba_sahne_1m_blok():
    """Kaba kafes `7 m`; `1 m`'lik blok iki kafes noktasının ARASINDA."""
    g = np.arange(-3, 4) * 7.0
    X = np.stack(np.meshgrid(g, g, g, indexing="ij"), -1).reshape(-1, 3)
    n = len(X)
    blok = BoulderField(np.array([[3.5, 3.5, 3.5]]), np.array([1.0]))
    return SimpleNamespace(
        x=X, is_impactor=np.zeros(n, bool),
        alpha0=np.full(n, 1.6), Y0=np.full(n, 1e4),
        is_boulder=np.zeros(n, bool), spacing=7.0,
        blok_alani=blok,
        malzeme_parametreleri={"matrix_alpha0": 1.6, "matrix_Y0": 1e4,
                               "boulder_alpha0": 1.05, "boulder_Y0": 1e7})


def test_kaba_kaynak_kucuk_blogu_KAYBEDIYOR_geometri_GERI_GETIRIYOR():
    """Uzman: kabanın örneklemediği `1 m` blokta ince noktaların HİÇBİRİ
    blok etiketi almadı. `"geometri"` onları geri getirmeli."""
    from dartrift.setup.refine import _en_yakin_indeks

    kaba = _kaba_sahne_1m_blok()
    s = 0.1
    g = np.arange(2.4, 4.6, s)
    ince = np.stack(np.meshgrid(g, g, g, indexing="ij"), -1).reshape(-1, 3)
    gercek = np.sum((ince - 3.5) ** 2, axis=1) < 1.0
    assert gercek.sum() > 1000

    idx = _en_yakin_indeks(kaba.x, ince, kaba.spacing)
    _, _, b_kaba = _ince_malzeme(kaba, ince, "kaba", idx=idx)
    a_geo, y_geo, b_geo = _ince_malzeme(kaba, ince, "geometri")
    assert b_kaba.sum() == 0, "kaba kaynak blogu gormemeliydi (uzman olcumu)"
    assert np.array_equal(b_geo, gercek)
    assert np.all(a_geo[gercek] == 1.05) and np.all(y_geo[gercek] == 1e7)
    assert np.all(a_geo[~gercek] == 1.6)


def test_geometri_kaynagi_parametresiz_sahnede_ACIK_hata():
    kaba = _kaba_sahne_1m_blok()
    kaba.malzeme_parametreleri = {}
    with pytest.raises(ValueError, match="malzeme_parametreleri"):
        _ince_malzeme(kaba, np.zeros((1, 3)), "geometri")


def test_bilinmeyen_malzeme_kaynagi_REDDEDILIYOR():
    with pytest.raises(ValueError, match="malzeme_kaynagi"):
        _ince_malzeme(_kaba_sahne_1m_blok(), np.zeros((1, 3)), "yakin")


def test_sahne_blok_alanini_ve_malzemeyi_TASIYOR():
    from dartrift.setup.scene import build_scene

    s = build_scene(radius=30.0, spacing=5.0, model_class="M1",
                    f_boulder=0.2, r_min=3.0, r_max=6.0, root_seed=11,
                    blok_uretici="v2", device="cpu")
    assert s.blok_alani is not None and len(s.blok_alani.radii) > 0
    mp = s.malzeme_parametreleri
    assert set(mp) >= {"matrix_alpha0", "matrix_Y0", "boulder_alpha0",
                       "boulder_Y0"}
    # kaba parcacik etiketleri geometriyle BIREBIR
    hedef = ~s.is_impactor
    assert np.array_equal(
        kure_birlesimi_ici(s.x[hedef], s.blok_alani.centers, s.blok_alani.radii),
        s.is_boulder[hedef])


def test_kademeli_inceltme_geometri_kaynagi_ETIKETLERI_geometriyle_esliyor():
    from dartrift.setup.refine import refine_scene_kademeli
    from dartrift.setup.scene import build_scene

    s = build_scene(radius=30.0, spacing=5.0, model_class="M1",
                    f_boulder=0.25, r_min=1.0, r_max=3.0, root_seed=11,
                    blok_uretici="v2", device="cpu")
    mesh = _build_mesh("icosphere", radius=float(s.target_radius), subdiv=4)
    kad = [(12.0, 2.0), (6.0, 4.0)]
    geo = refine_scene_kademeli(s, mesh, kad, malzeme_kaynagi="geometri")
    kab = refine_scene_kademeli(s, mesh, kad)
    ince = np.asarray(geo.is_fine) & ~np.asarray(geo.is_impactor)
    beklenen = kure_birlesimi_ici(np.asarray(geo.x)[ince], s.blok_alani.centers,
                                  s.blok_alani.radii)
    assert np.array_equal(np.asarray(geo.is_boulder)[ince], beklenen)
    # "kaba" kaynak ayni ince noktalarda geometriden SAPIYOR (kusur olculuyor)
    ince_k = np.asarray(kab.is_fine) & ~np.asarray(kab.is_impactor)
    bek_k = kure_birlesimi_ici(np.asarray(kab.x)[ince_k], s.blok_alani.centers,
                               s.blok_alani.radii)
    assert np.count_nonzero(np.asarray(kab.is_boulder)[ince_k] != bek_k) > 0
    assert geo.diagnostics["malzeme_kaynagi"] == "geometri"
