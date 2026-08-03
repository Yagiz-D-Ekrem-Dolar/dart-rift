"""P3-FR-02/03/04: moloz-yigini ureticisi — doldurma, iri-blok, malzeme alani.

Sartname bu gereksinimler icin ACIKCA geri-olcum istiyor:
  FR-02 "Yogunluk/paketlenme testi"
  FR-03 "fboulder geri-olcum testi"
Yani "orneklendi" demek yetmez; uretilen yigindan olculen deger hedefi
vermeli. Testler bu mantikla kurulmustur.
"""

import numpy as np
import pytest

from dartrift.setup.rubble_generator import (
    FCC_VOLUME_FACTOR,
    build_rubble_pile,
    coordination_number,
    fill_particles,
    particle_volume,
    place_boulders,
    sample_boulder_radii,
)
from dartrift.setup.shape_mesh import ellipsoid, icosphere, inside_points

RHO0_SOLID = 2700.0
RHO_BULK = 1800.0          # gozenekli yigin yogunlugu [kg/m^3]


class TestFilling:
    def test_all_particles_are_inside_mesh(self):
        m = icosphere(4, 100.0)
        x = fill_particles(m, spacing=12.0)
        assert len(x) > 100
        assert np.all(inside_points(m, x))

    def test_fcc_volume_factor_is_exact(self):
        """FCC'de V_p = s^3/sqrt(2). Turetme: a=s*sqrt(2), hucrede 4 parcacik."""
        assert FCC_VOLUME_FACTOR == pytest.approx(1.0 / np.sqrt(2.0), rel=1e-15)
        s = 3.0
        assert particle_volume(s, "fcc") == pytest.approx(s**3 / np.sqrt(2.0))
        assert particle_volume(s, "cubic") == pytest.approx(s**3)

    def test_filled_volume_matches_mesh_volume(self):
        """N * V_p ~ mesh hacmi. Bu, hem doldurmayi hem V_p'yi dogrular."""
        m = icosphere(4, 100.0)
        for packing in ("fcc", "cubic"):
            x = fill_particles(m, spacing=8.0, packing=packing)
            v_fill = len(x) * particle_volume(8.0, packing)
            assert v_fill == pytest.approx(m.volume, rel=0.05), (packing, v_fill)

    def test_fcc_interior_coordination_is_twelve(self):
        """FCC'nin tanimlayici ozelligi: ic bolgede 12 en yakin komsu.

        Bu, yerlesimin GERCEKTEN FCC oldugunu sabitler; kubik kafeste 6 cikar.
        """
        m = icosphere(4, 100.0)
        s = 10.0
        x = fill_particles(m, spacing=s)
        cn = coordination_number(x, s)
        deep = np.linalg.norm(x, axis=1) < 60.0        # yuzeyden uzak
        assert deep.sum() > 50
        assert int(np.median(cn[deep])) == 12, np.median(cn[deep])

    def test_cubic_interior_coordination_is_six(self):
        m = icosphere(4, 100.0)
        s = 10.0
        x = fill_particles(m, spacing=s, packing="cubic")
        cn = coordination_number(x, s)
        deep = np.linalg.norm(x, axis=1) < 60.0
        assert int(np.median(cn[deep])) == 6, np.median(cn[deep])

    def test_finer_spacing_gives_more_particles(self):
        m = icosphere(3, 100.0)
        n_coarse = len(fill_particles(m, spacing=20.0))
        n_fine = len(fill_particles(m, spacing=10.0))
        assert n_fine > 6 * n_coarse, (n_coarse, n_fine)

    def test_bad_spacing_rejected(self):
        with pytest.raises(ValueError, match="aralik"):
            fill_particles(icosphere(2, 1.0), spacing=0.0)

    def test_unknown_packing_rejected(self):
        with pytest.raises(ValueError, match="yerlesim"):
            fill_particles(icosphere(2, 1.0), spacing=0.5, packing="hex")


class TestBoulderSampling:
    def test_power_law_radii_within_bounds(self):
        rng = np.random.default_rng(0)
        r = sample_boulder_radii(rng, 5000, 1.0, 10.0, q=3.0)
        assert r.min() >= 1.0 and r.max() <= 10.0

    def test_truncated_power_law_cdf_matches_exactly(self):
        """Orneklenen dagilim KESIN kuyruk CDF'sini vermeli.

        [r_min, r_max] araliginda kesilmis power-law icin p = 1-q olmak uzere
            P(R > r) = (r^p - r_max^p) / (r_min^p - r_max^p)
        Not: yaygin "N(>r) ~ r^(1-q)" yaklasimi yalnizca r << r_max icin
        gecerlidir; r_max yakininda kesilme log-log egimi DIKLESTIRIR. Ilk
        yazdigim test o yaklasimi kullandigi icin dusmustu — ORNEKLEYICI
        degil, TESTIN formulu yanlisti.
        """
        rng = np.random.default_rng(1)
        q, rmin, rmax = 3.0, 1.0, 20.0
        p = 1.0 - q
        r = sample_boulder_radii(rng, 400000, rmin, rmax, q)
        for t in (1.5, 2.5, 5.0, 10.0, 15.0):
            olculen = float(np.mean(r > t))
            teorik = (t**p - rmax**p) / (rmin**p - rmax**p)
            assert olculen == pytest.approx(teorik, abs=0.004), (t, olculen, teorik)

    def test_q_equals_one_branch(self):
        """q=1'de formul tekil; ayri kol log-uniform vermeli."""
        rng = np.random.default_rng(2)
        r = sample_boulder_radii(rng, 100000, 1.0, 100.0, q=1.0)
        lg = np.log10(r)
        assert lg.min() >= 0.0 and lg.max() <= 2.0
        assert np.mean(lg) == pytest.approx(1.0, abs=0.02)   # log-uniform ortasi

    def test_invalid_bounds_rejected(self):
        rng = np.random.default_rng(3)
        with pytest.raises(ValueError, match="r_min"):
            sample_boulder_radii(rng, 10, 5.0, 1.0, q=3.0)

    def test_boulders_do_not_overlap(self):
        m = icosphere(4, 100.0)
        bf = place_boulders(m, f_boulder=0.15, q=3.0, r_min=8.0, r_max=25.0,
                            root_seed=7)
        assert len(bf.radii) > 3
        c, r = bf.centers, bf.radii
        d = np.linalg.norm(c[:, None, :] - c[None, :, :], axis=2)
        need = r[:, None] + r[None, :]
        np.fill_diagonal(d, np.inf)
        assert np.all(d >= need - 1e-9), float((d - need).min())

    def test_boulder_centers_inside_mesh(self):
        m = icosphere(4, 100.0)
        bf = place_boulders(m, 0.1, 3.0, 8.0, 20.0, root_seed=11)
        assert np.all(inside_points(m, bf.centers))


class TestRubblePile:
    @pytest.fixture(scope="class")
    def m0(self):
        return build_rubble_pile(icosphere(4, 100.0), spacing=9.0,
                                 bulk_density=RHO_BULK, root_seed=42,
                                 rho0_solid=RHO0_SOLID, model_class="M0")

    def test_bulk_density_recovered(self, m0):
        """P3-FR-02 kabulu: toplam kutle / mesh hacmi = HEDEF yogunluk."""
        assert m0.bulk_density == pytest.approx(RHO_BULK, rel=0.05), m0.bulk_density

    def test_m0_is_homogeneous(self, m0):
        assert not m0.is_boulder.any()
        assert len(np.unique(m0.alpha0)) == 1
        assert len(np.unique(m0.Y0)) == 1

    def test_deterministic_same_seed(self):
        """ADR-0004: ayni tohum -> BIT-ESIT yigin (ensemble'in on kosulu)."""
        a = build_rubble_pile(icosphere(3, 100.0), 15.0, RHO_BULK, 5,
                              rho0_solid=RHO0_SOLID, model_class="M1", f_boulder=0.12,
                              r_min=18.0, r_max=40.0)
        b = build_rubble_pile(icosphere(3, 100.0), 15.0, RHO_BULK, 5,
                              rho0_solid=RHO0_SOLID, model_class="M1", f_boulder=0.12,
                              r_min=18.0, r_max=40.0)
        assert np.array_equal(a.x, b.x)
        assert np.array_equal(a.is_boulder, b.is_boulder)
        assert np.array_equal(a.boulders.radii, b.boulders.radii)

    def test_different_seed_gives_different_boulders(self):
        """Bosluk kontrolu: tohum GERCEKTEN kullaniliyor mu?"""
        kw = dict(spacing=15.0, bulk_density=RHO_BULK, rho0_solid=RHO0_SOLID,
                  model_class="M1",
                  f_boulder=0.12, r_min=18.0, r_max=40.0)
        a = build_rubble_pile(icosphere(3, 100.0), root_seed=1, **kw)
        b = build_rubble_pile(icosphere(3, 100.0), root_seed=2, **kw)
        assert not np.array_equal(a.is_boulder, b.is_boulder)

    def test_m1_requires_f_boulder(self):
        with pytest.raises(ValueError, match="f_boulder"):
            build_rubble_pile(icosphere(2, 100.0), 25.0, RHO_BULK, 1,
                              rho0_solid=RHO0_SOLID, model_class="M1", f_boulder=0.0)

    def test_unknown_class_rejected(self):
        with pytest.raises(ValueError, match="sinif"):
            build_rubble_pile(icosphere(2, 100.0), 25.0, RHO_BULK, 1,
                              rho0_solid=RHO0_SOLID, model_class="M9")


class TestBoulderFractionRecovery:
    """P3-FR-03'un ACIK kabulu: 'fboulder geri-olcum testi'."""

    @pytest.mark.parametrize("f_target", [0.10, 0.20])
    def test_measured_fraction_tracks_target(self, f_target):
        """Makul hedeflerde geri-olculen oran hedefi vermeli."""
        pile = build_rubble_pile(
            ellipsoid(120.0, 100.0, 85.0, subdiv=4), spacing=7.0,
            bulk_density=RHO_BULK, rho0_solid=RHO0_SOLID, root_seed=3, model_class="M1",
            f_boulder=f_target, q=3.0, r_min=14.0, r_max=35.0)
        olculen = pile.boulder_volume_fraction
        assert not pile.diagnostics["boulder_saturated"], pile.diagnostics
        assert olculen == pytest.approx(f_target, abs=0.04), (f_target, olculen)

    def test_measured_fraction_tracks_PLACED_volume(self):
        """Asil dogruluk sarti: etiketleme, GERCEKTEN yerlesen bloklari izlemeli.

        Hedefe ulasilsin ulasilmasin, blok etiketli parcacik orani yerlesen
        blok hacminin mesh hacmine oranini vermeli. Bu, "hedef tutmadi" ile
        "etiketleme bozuk" durumlarini birbirinden AYIRIR.
        """
        pile = build_rubble_pile(
            ellipsoid(120.0, 100.0, 85.0, subdiv=4), spacing=6.0,
            bulk_density=RHO_BULK, rho0_solid=RHO0_SOLID, root_seed=8, model_class="M1",
            f_boulder=0.30, q=3.0, r_min=14.0, r_max=35.0)
        d = pile.diagnostics
        yerlesen_oran = d["boulder_volume_placed"] / d["mesh_volume"]
        assert pile.boulder_volume_fraction == pytest.approx(yerlesen_oran, abs=0.03), (
            pile.boulder_volume_fraction, yerlesen_oran)

    def test_saturation_is_reported_not_silent(self):
        """Ulasilamayan hedef SESSIZ kalmamali (bosluk kontrolu).

        Cok yuksek f_boulder'da cakismasiz yerlesim doyar; kod bunu
        `boulder_saturated` ile bildirmeli, yoksa cagiran taraf hedefe
        ulasildigini SANIR.
        """
        pile = build_rubble_pile(
            icosphere(3, 100.0), spacing=10.0, bulk_density=RHO_BULK,
            rho0_solid=RHO0_SOLID, root_seed=13, model_class="M1", f_boulder=0.75, q=3.0,
            r_min=15.0, r_max=30.0)
        d = pile.diagnostics
        assert d["boulder_volume_placed"] < d["boulder_volume_target"]
        assert d["boulder_saturated"] is True, d

    def test_more_boulders_means_higher_fraction(self):
        """Monotonluk: hedef artarsa olculen de artmali."""
        kw = dict(spacing=8.0, bulk_density=RHO_BULK, rho0_solid=RHO0_SOLID, root_seed=9,
                  model_class="M1", q=3.0, r_min=14.0, r_max=32.0)
        lo = build_rubble_pile(icosphere(4, 100.0), f_boulder=0.08, **kw)
        hi = build_rubble_pile(icosphere(4, 100.0), f_boulder=0.28, **kw)
        assert hi.boulder_volume_fraction > lo.boulder_volume_fraction + 0.08

    def test_boulder_particles_get_boulder_material(self):
        """Malzeme alani (P3-FR-04): blok parcaciklari DUSUK gozeneklilik,
        YUKSEK kohezyon almali."""
        pile = build_rubble_pile(icosphere(4, 100.0), 8.0, RHO_BULK, 4, rho0_solid=RHO0_SOLID,
                                 model_class="M1", f_boulder=0.2,
                                 r_min=14.0, r_max=30.0,
                                 boulder_alpha0=1.05,
                                 matrix_Y0=1.0e4, boulder_Y0=1.0e7)
        b, mtx = pile.is_boulder, ~pile.is_boulder
        assert b.any() and mtx.any()
        assert np.all(pile.alpha0[b] < pile.alpha0[mtx].min())
        assert np.all(pile.Y0[b] > pile.Y0[mtx].max())

    def test_diagnostics_are_consistent(self):
        pile = build_rubble_pile(icosphere(4, 100.0), 8.0, RHO_BULK, 6, rho0_solid=RHO0_SOLID,
                                 model_class="M1", f_boulder=0.15,
                                 r_min=14.0, r_max=30.0)
        d = pile.diagnostics
        assert d["n_particles"] == pile.n
        assert d["fill_ratio"] == pytest.approx(1.0, abs=0.06)
        assert d["n_boulders"] == len(pile.boulders.radii)
        assert d["boulder_volume_placed"] <= d["boulder_volume_target"] * 1.5


class TestMassPorosityConsistency:
    """ADR-0030: kutle ile gozeneklilik TUTARLI olmak zorunda.

    Bulunan kusur: kutle `bulk_density * V_p` ile TEKDUZE atiliyordu, cozucu
    ise `rho = rho0_solid/alpha0` atiyor (ADR-0022). SPH'de parcacigin hacmi
    `m/rho`'dur ve kafeste kapladigi hacme (`V_p`) esit olmali; degilse birim
    bolunmesi `sum_j (m_j/rho_j) W_ij = 1` bozulur.

    Olculen (h'den bagimsiz, uc h'de): M0 1.067 (+%6,7), M1 blok 0.77-0.80.
    Ayni dizilim toplam yogunlukla bloklarda -7,624e+09 Pa yapay cekme
    veriyordu. G3 C2 kutle butcesini (m), C3 gerilmesiz baslangici (rho)
    olcuyordu; TUTARLILIGA bakan kriter YOKTU.
    """

    @staticmethod
    def _pile(**kw):
        varsayilan = dict(spacing=8.0, bulk_density=RHO_BULK,
                          rho0_solid=RHO0_SOLID, root_seed=4)
        return build_rubble_pile(icosphere(4, 100.0), **{**varsayilan, **kw})

    @pytest.mark.parametrize("kw", [
        dict(model_class="M0"),
        dict(model_class="M1", f_boulder=0.20, r_min=14.0, r_max=30.0),
        dict(model_class="M1", f_boulder=0.05, r_min=14.0, r_max=30.0),
    ])
    def test_m_bolu_rho_parcacik_hacmine_esit(self, kw):
        """ASIL DEGISMEZ: m_i/rho_i = V_p, her parcacikta."""
        from dartrift.setup.rubble_generator import particle_volume

        pile = self._pile(**kw)
        v_p = particle_volume(pile.spacing, "fcc")
        rho = RHO0_SOLID / pile.alpha0
        oran = (pile.m / rho) / v_p
        assert np.allclose(oran, 1.0, rtol=1e-12), (
            f"m/(rho*V_p) araligi [{oran.min():.6f}, {oran.max():.6f}] — "
            "1 olmali, yoksa SPH birim bolunmesi bozulur")
        # tani da bunu bildirmeli
        d = pile.diagnostics
        assert d["volume_consistency_min"] == pytest.approx(1.0, rel=1e-12)
        assert d["volume_consistency_max"] == pytest.approx(1.0, rel=1e-12)

    def test_hedef_yigin_yogunlugu_TAM_tutturuluyor(self):
        """`bulk_density` bir HEDEF; cozulen alpha onu tam tutturmali.

        Eski hali hedefi kutleyle "tutturuyor" gorunuyordu ama yogunluk alani
        baska bir cisim tarif ediyordu. Simdi ikisi ayni cisim.
        """
        for kw in (dict(model_class="M0"),
                   dict(model_class="M1", f_boulder=0.20, r_min=14.0, r_max=30.0)):
            pile = self._pile(**kw)
            d = pile.diagnostics
            assert d["bulk_density_achieved"] == pytest.approx(RHO_BULK, rel=1e-12), kw
            # yogunluk alanindan hesaplanan kutle de ayni cismi vermeli
            rho = RHO0_SOLID / pile.alpha0
            assert float(np.mean(rho)) == pytest.approx(RHO_BULK, rel=1e-12), kw

    def test_bloklar_gercekten_daha_agir(self):
        """Kati kaya gozenekli matristen YOGUNDUR.

        Eskiden blok ve matris parcaciklari AYNI kutleye sahipti; yani "blok"
        yalnizca bir etiketti. Olculen yeni oran: +%65.
        """
        pile = self._pile(model_class="M1", f_boulder=0.20, r_min=14.0, r_max=30.0)
        b, mtx = pile.is_boulder, ~pile.is_boulder
        assert b.any() and mtx.any()
        assert pile.m[b].min() > pile.m[mtx].max(), (
            f"blok kutlesi {pile.m[b].min():.4e} matris {pile.m[mtx].max():.4e}")
        oran = pile.m[b][0] / pile.m[mtx][0]
        # alpha oranindan tam olarak belirlenir: m ~ 1/alpha
        beklenen = pile.alpha0[mtx][0] / pile.alpha0[b][0]
        assert oran == pytest.approx(beklenen, rel=1e-12)
        assert oran > 1.3, oran

    def test_celisik_matrix_alpha0_SESSIZ_gecmiyor(self):
        """Elle verilen alpha hedefi tutturmuyorsa HATA — sessizce farkli bir
        cisim uretmek gozeneklilik cikariminin girdisini gorunmeden kaydirirdi.

        1.6, tam olarak kusurun eski degeridir: rho0=2700 ile yigin yogunlugu
        1687.5 demek, ama hedef 1800 yaziliydi.
        """
        with pytest.raises(ValueError, match="sapiyor") as exc:
            self._pile(model_class="M0", matrix_alpha0=1.6)
        mesaj = str(exc.value)
        # Hata, TUTTURAN degeri de soylemeli — yoksa kullanici ne yapacagini
        # bilemez ve en kolay yol tutarsizligi geri getirmek olur.
        assert "1.5" in mesaj, mesaj
        assert "matrix_alpha0=None" in mesaj, mesaj

    def test_tutarli_matrix_alpha0_KABUL_ediliyor(self):
        """Cozulen degeri elle vermek gecerli olmali (kapi kapanmasin)."""
        cozulen = self._pile(model_class="M0").diagnostics["matrix_alpha0_solved"]
        pile = self._pile(model_class="M0", matrix_alpha0=cozulen)
        assert pile.diagnostics["matrix_alpha0_was_solved"] is False
        assert pile.diagnostics["bulk_density_achieved"] == pytest.approx(
            RHO_BULK, rel=1e-9)

    def test_rho0_solid_zorunlu(self):
        """Kok neden: uretici rho0'i HIC BILMIYORDU. Artik bilmek zorunda."""
        with pytest.raises(TypeError, match="rho0_solid"):
            build_rubble_pile(icosphere(2, 100.0), 25.0, RHO_BULK, 1)

    def test_ulasilamaz_hedef_ACIK_reddediliyor(self):
        """Bloklar tek basina hedefi asiyorsa sessizce yaklasik cozum yok."""
        from dartrift.setup.rubble_generator import matrix_alpha0_for_bulk_density

        with pytest.raises(ValueError, match="ulasilamaz"):
            # bloklar parcaciklarin %90'i ve her biri 2571 kg/m^3 -> 1800 imkansiz
            matrix_alpha0_for_bulk_density(1800.0, 2700.0, 1.05, 0.90)
        with pytest.raises(ValueError, match="fiziksel degil"):
            # katidan yogun matris istemek
            matrix_alpha0_for_bulk_density(2800.0, 2700.0, 1.05, 0.0)


class TestBulkDensityDefinitions:
    """ADR-0033: 'yigin yogunlugu' IKI farkli sey demek; ikisi de isimli.

      A) `RubblePile.bulk_density`              = sum(m) / V_mesh
      B) `diagnostics["bulk_density_achieved"]` = sum(m) / (N * V_p)

    Ikisinin orani TAM OLARAK dolum oranidir. Olculdu:
        ikosfer r=100 s=9  : dolum 0.9993  A=1798.80  B=1800.00
        ikosfer r=60  s=8  : dolum 0.9881  A=1778.51  B=1800.00
        elipsoit 120x100x85: dolum 0.9987  A=1797.65  B=1800.00
        ikosfer r=82  s=7  : dolum 1.0044  A=1807.98  B=1800.00
    Yani A hedeften -%1,19 ile +%0,44 sapar. Kusur DEGIL, iki ayri sorunun
    iki ayri yaniti — ama eski test bandi (rel=0.05) bu ayrimi YUTUYORDU ve
    hangisinin kullanildigi belirsizdi.
    """

    @pytest.mark.parametrize(("mesh_fn", "sp"), [
        (lambda: icosphere(4, 100.0), 9.0),
        (lambda: icosphere(3, 60.0), 8.0),
        (lambda: ellipsoid(120.0, 100.0, 85.0, subdiv=4), 7.0),
    ])
    def test_iki_tanim_dolum_oraniyla_bagli(self, mesh_fn, sp):
        pile = build_rubble_pile(mesh_fn(), spacing=sp, bulk_density=RHO_BULK,
                                 rho0_solid=RHO0_SOLID, root_seed=3,
                                 model_class="M0")
        d = pile.diagnostics
        # B hedefi TAM tutturur (ADR-0030)
        assert d["bulk_density_achieved"] == pytest.approx(RHO_BULK, rel=1e-12)
        # A = B * dolum orani — kapali form iliski, tolerans yok
        assert pile.bulk_density == pytest.approx(
            d["bulk_density_achieved"] * d["fill_ratio"], rel=1e-12)
        assert d["bulk_density_over_mesh"] == pytest.approx(
            pile.bulk_density, rel=1e-12)

    def test_ayriklastirilmis_hacim_ve_yaricap_tutarli(self):
        """Kutle ile yaricap AYNI hacim tanimindan gelmeli."""
        from dartrift.setup.rubble_generator import particle_volume

        pile = build_rubble_pile(icosphere(3, 60.0), spacing=8.0,
                                 bulk_density=RHO_BULK, rho0_solid=RHO0_SOLID,
                                 root_seed=3, model_class="M0")
        v_p = particle_volume(pile.spacing, "fcc")
        assert pile.discretised_volume == pytest.approx(pile.n * v_p, rel=1e-12)
        beklenen_r = (3.0 * pile.discretised_volume / (4.0 * np.pi)) ** (1.0 / 3.0)
        assert pile.discretised_radius == pytest.approx(beklenen_r, rel=1e-12)
        # mesh yaricapindan FARKLI olmali (aksi halde bu ayrim bos olurdu)
        r_mesh = (3.0 * pile.mesh_volume / (4.0 * np.pi)) ** (1.0 / 3.0)
        assert pile.discretised_radius != r_mesh
        assert abs(pile.discretised_radius / r_mesh - 1.0) < 0.02
