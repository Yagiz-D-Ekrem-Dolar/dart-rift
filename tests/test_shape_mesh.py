"""P3-FR-01: sekil mesh hatti — temizleme, yonlendirme, hacim, icerde-mi.

DOGRULAMA STRATEJISI: sentetik mesh'lerde hacim ANALITIK olarak bilinir
(kure 4/3 pi r^3, elipsoid 4/3 pi abc). Boylece iki bagimsiz yol karsilastirilir:
  (a) diverjans teoremiyle mesh hacmi
  (b) icerde-mi testiyle doldurulan kafes hacmi
Ikisi de analitige yakinsamak zorunda. Icerde-mi testi bozuksa (b) tutmaz —
yani test, "mesh dogru" diye ayri bir iddiaya ihtiyac duymaz.
"""

import numpy as np
import pytest

from dartrift.setup.shape_mesh import (
    TriMesh,
    clean_mesh,
    ellipsoid,
    icosphere,
    inside_points,
    load_obj,
    orient_outward,
    signed_distance,
)


class TestLoadObj:
    """OBJ okuma — PDS sekil modelleri bu bicimde gelir.

    Bu yol FAZ 3 boyunca HIC test edilmemisti (kapsam %0 gosterdi) ve tam da
    gercek veri geldiginde kullanilacak olan yol. Sentetik OBJ'lerle sinaniyor.
    """

    @staticmethod
    def _yaz(tmp_path, metin):
        p = tmp_path / "m.obj"
        p.write_text(metin, encoding="utf-8")
        return p

    def test_ucgen_tetrahedron(self, tmp_path):
        """Birim tetrahedron: 4 kose, 4 yuz, hacim 1/6."""
        p = self._yaz(tmp_path, (
            "v 0 0 0\nv 1 0 0\nv 0 1 0\nv 0 0 1\n"
            "f 1 3 2\nf 1 2 4\nf 1 4 3\nf 2 3 4\n"))
        m = load_obj(p)
        assert len(m.v) == 4 and len(m.f) == 4
        assert abs(m.volume) == pytest.approx(1.0 / 6.0, rel=1e-12)

    def test_yorum_ve_bilinmeyen_satirlar_atlanir(self, tmp_path):
        p = self._yaz(tmp_path, (
            "# yorum\nmtllib a.mtl\nvn 0 0 1\nvt 0 0\n"
            "v 0 0 0\nv 1 0 0\nv 0 1 0\nv 0 0 1\n"
            "usemtl x\nf 1 3 2\nf 1 2 4\nf 1 4 3\nf 2 3 4\n"))
        m = load_obj(p)
        assert len(m.v) == 4 and len(m.f) == 4

    def test_kose_dokusu_normal_indeksleri(self, tmp_path):
        """`f 1/2/3` ve `f 1//3` bicimlerinde ilk alan kose indeksidir."""
        p = self._yaz(tmp_path, (
            "v 0 0 0\nv 1 0 0\nv 0 1 0\nv 0 0 1\n"
            "f 1/1/1 3/3/3 2/2/2\nf 1//1 2//2 4//4\n"
            "f 1/1 4/4 3/3\nf 2 3 4\n"))
        m = load_obj(p)
        assert len(m.f) == 4
        assert abs(m.volume) == pytest.approx(1.0 / 6.0, rel=1e-12)

    def test_poligon_yuz_ucgen_yelpazeye_bolunur(self, tmp_path):
        """Dortgen yuz 2 ucgene bolunmeli (kup: 6 dortgen -> 12 ucgen)."""
        v = "\n".join(f"v {x} {y} {z}"
                      for x in (0, 1) for y in (0, 1) for z in (0, 1))
        # kose sirasi: (x,y,z) = 000,001,010,011,100,101,110,111 -> 1..8
        f = ("f 1 3 4 2\nf 5 6 8 7\nf 1 2 6 5\n"
             "f 3 7 8 4\nf 1 5 7 3\nf 2 4 8 6\n")
        m = load_obj(self._yaz(tmp_path, v + "\n" + f))
        assert len(m.v) == 8
        assert len(m.f) == 12          # 6 dortgen x 2
        assert abs(m.volume) == pytest.approx(1.0, rel=1e-12)

    def test_negatif_indeks_sondan_sayar(self, tmp_path):
        """OBJ negatif indeksi 'sondan' anlaminda kullanir."""
        p = self._yaz(tmp_path, (
            "v 0 0 0\nv 1 0 0\nv 0 1 0\nv 0 0 1\n"
            "f -4 -2 -3\nf -4 -3 -1\nf -4 -1 -2\nf -3 -2 -1\n"))
        m = load_obj(p)
        assert len(m.f) == 4
        assert abs(m.volume) == pytest.approx(1.0 / 6.0, rel=1e-12)

    def test_okunan_mesh_islenebilir(self, tmp_path):
        """Okunan mesh, hattin geri kalanina (yonlendirme, ic testi) girebilmeli."""
        from dartrift.setup.shape_mesh import inside_points, orient_outward

        p = self._yaz(tmp_path, (
            "v 0 0 0\nv 1 0 0\nv 0 1 0\nv 0 0 1\n"
            "f 1 3 2\nf 1 2 4\nf 1 4 3\nf 2 3 4\n"))
        m = orient_outward(load_obj(p))
        assert m.volume > 0.0
        assert m.is_edge_manifold()
        icte = np.array([[0.2, 0.2, 0.2]])
        disarida = np.array([[5.0, 5.0, 5.0]])
        assert bool(inside_points(m, icte)[0]) is True
        assert bool(inside_points(m, disarida)[0]) is False


def _lattice(lo, hi, n):
    """Hucre MERKEZLERI — mesh koselerine denk gelmemesi icin yarim kaydirma."""
    ax = [np.linspace(lo[k], hi[k], n, endpoint=False) + (hi[k] - lo[k]) / (2 * n)
          for k in range(3)]
    return np.stack(np.meshgrid(*ax, indexing="ij"), -1).reshape(-1, 3)


class TestMeshGeometry:
    def test_sphere_volume_converges_to_analytic(self):
        """Bolunme arttikca mesh hacmi 4/3 pi r^3'e YAKINSAMALI."""
        exact = 4.0 / 3.0 * np.pi
        errs = [abs(icosphere(s, 1.0).volume - exact) / exact for s in (1, 2, 3)]
        assert errs[0] > errs[1] > errs[2], errs
        assert errs[-1] < 0.01, errs

    def test_ellipsoid_volume_analytic(self):
        a, b, c = 2.0, 1.5, 1.0
        m = ellipsoid(a, b, c, subdiv=4)
        exact = 4.0 / 3.0 * np.pi * a * b * c
        assert abs(m.volume - exact) / exact < 0.005, m.volume

    def test_volume_is_positive_after_orientation(self):
        """Ters yonlendirilmis ag duzeltilmeli; hacim isareti anlamlidir."""
        m = icosphere(2, 1.0)
        flipped = TriMesh(m.v, m.f[:, ::-1])
        assert flipped.volume < 0.0
        assert orient_outward(flipped).volume > 0.0
        assert orient_outward(flipped).volume == pytest.approx(m.volume, rel=1e-12)

    def test_mesh_is_edge_manifold(self):
        """Kapali ag: her kenar TAM iki ucgende. Delikli agda hacim anlamsiz."""
        assert icosphere(2, 1.0).is_edge_manifold()
        assert ellipsoid(2.0, 1.0, 1.0, 3).is_edge_manifold()

    def test_hole_is_detected(self):
        """Bosluk kontrolu: delik acilinca manifold testi DUSMELI."""
        m = icosphere(2, 1.0)
        holed = TriMesh(m.v, m.f[:-1])          # bir ucgen cikar
        assert not holed.is_edge_manifold()

    def test_centroid_of_centered_sphere_is_origin(self):
        assert np.allclose(icosphere(3, 1.0).centroid, 0.0, atol=1e-12)

    def test_centroid_tracks_translation(self):
        m = icosphere(3, 1.0)
        shift = np.array([5.0, -2.0, 1.0])
        moved = TriMesh(m.v + shift, m.f)
        assert np.allclose(moved.centroid, shift, atol=1e-10)


class TestCleaning:
    def test_degenerate_faces_removed(self):
        m = icosphere(1, 1.0)
        bad = TriMesh(m.v, np.vstack([m.f, [[0, 0, 1]]]))   # dejenere ucgen
        assert len(clean_mesh(bad).f) == len(m.f)

    def test_weld_merges_duplicate_vertices(self):
        """Ayni nokta iki kez gecerse kenar-manifoldlugu SAHTE olarak bozulur."""
        m = icosphere(1, 1.0)
        v2 = np.vstack([m.v, m.v[0] + 1e-12])
        f2 = m.f.copy()
        # kose 0'i yalnizca BAZI yuzlerde kopyasiyla degistir -> ag yirtilir
        touch = np.flatnonzero((f2 == 0).any(axis=1))
        half = touch[: len(touch) // 2]
        blk = f2[half]
        blk[blk == 0] = len(m.v)
        f2[half] = blk
        broken = TriMesh(v2, f2)
        assert not broken.is_edge_manifold()
        assert clean_mesh(broken, weld_tol=1e-9).is_edge_manifold()

    def test_cleaning_preserves_volume(self):
        m = icosphere(2, 1.0)
        assert clean_mesh(m).volume == pytest.approx(m.volume, rel=1e-12)


class TestInsideTest:
    def test_sphere_inside_matches_analytic(self):
        """Analitik kure ile karsilastir: yanlis siniflanan nokta orani kucuk."""
        m = icosphere(4, 1.0)
        pts = _lattice([-1.5] * 3, [1.5] * 3, 40)
        got = inside_points(m, pts)
        exact = np.linalg.norm(pts, axis=1) < 1.0
        # uyusmazlik yalnizca YUZEY yakininda olmali (mesh kureyi tam temsil etmez)
        bad = got != exact
        assert bad.mean() < 0.01, bad.mean()
        r = np.linalg.norm(pts[bad], axis=1)
        assert np.all(np.abs(r - 1.0) < 0.12), (r.min(), r.max())

    def test_filled_volume_matches_mesh_volume(self):
        """BAGIMSIZ IKI YOL: doldurulan kafes hacmi ~ diverjans hacmi."""
        m = ellipsoid(2.0, 1.2, 0.8, subdiv=4)
        lo, hi = m.bounds
        pad = 0.05 * (hi - lo)
        n = 60
        pts = _lattice(lo - pad, hi + pad, n)
        cell = np.prod((hi - lo + 2 * pad) / n)
        vol_fill = float(np.count_nonzero(inside_points(m, pts))) * cell
        assert vol_fill == pytest.approx(m.volume, rel=0.02), (vol_fill, m.volume)

    def test_points_far_outside_are_outside(self):
        m = icosphere(3, 1.0)
        far = np.array([[10.0, 0, 0], [0, -8.0, 0], [0, 0, 5.0], [3.0, 3.0, 3.0]])
        assert not inside_points(m, far).any()

    def test_center_is_inside(self):
        m = ellipsoid(2.0, 1.0, 1.5, 3)
        assert inside_points(m, np.zeros((1, 3)))[0]

    def test_result_is_translation_invariant(self):
        """Icerde-mi testi kafes konumuna degil GEOMETRIYE bagli olmali."""
        m = icosphere(3, 1.0)
        pts = _lattice([-1.4] * 3, [1.4] * 3, 24)
        shift = np.array([7.0, -3.0, 11.0])
        a = inside_points(m, pts)
        b = inside_points(TriMesh(m.v + shift, m.f), pts + shift)
        assert np.array_equal(a, b)

    def test_empty_query_is_safe(self):
        assert inside_points(icosphere(1), np.zeros((0, 3))).shape == (0,)


class TestSignedDistance:
    def test_sign_convention_inside_negative(self):
        m = icosphere(3, 1.0)
        pts = np.array([[0.0, 0, 0], [2.0, 0, 0]])
        d = signed_distance(m, pts)
        assert d[0] < 0.0 and d[1] > 0.0, d

    def test_distance_magnitude_on_sphere(self):
        """Kurede |sdf| ~ | |x| - r | olmali."""
        m = icosphere(4, 1.0)
        pts = np.array([[0.0, 0, 0], [0.5, 0, 0], [1.5, 0, 0], [0, 3.0, 0]])
        d = signed_distance(m, pts)
        beklenen = np.array([-1.0, -0.5, 0.5, 2.0])
        assert np.allclose(d, beklenen, atol=0.02), (d, beklenen)
