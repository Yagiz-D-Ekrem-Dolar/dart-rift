"""P2-VR-05: duzgun kure alani analitik g(r)'ye yakin; BH direct ile eslesir."""

import numpy as np
import pytest

from dartrift.cpu_reference.gravity_ref import bh_accel, build_octree, compute_gravity_direct
from dartrift.validation.gravity import _uniform_sphere, run_uniform_sphere


class TestTreeCorrectness:
    def test_tree_mass_and_com(self):
        x = _uniform_sphere(500)
        m = np.random.default_rng(1).uniform(0.5, 1.5, 500)
        tree = build_octree(x, m)
        assert tree.mass[0] == pytest.approx(float(np.sum(m)), rel=1e-12)
        com = (m @ x) / np.sum(m)
        assert np.allclose(tree.com[0], com, rtol=1e-12)

    def test_perm_is_permutation(self):
        x = _uniform_sphere(300)
        tree = build_octree(x, np.ones(300))
        assert sorted(tree.perm.tolist()) == list(range(300))

    def test_theta_zero_equals_direct(self):
        # theta -> 0: agac hicbir monopol kullanamaz -> dogrudan toplamla ozdes
        x = _uniform_sphere(200)
        m = np.full(200, 1.0 / 200)
        tree = build_octree(x, m)
        g_bh, phi_bh = bh_accel(x, np.arange(200), tree, x, m, 1.0, 0.02, 1e-9)
        g_d, phi_d = compute_gravity_direct(x, m, 1.0, 0.02)
        assert np.allclose(g_bh, g_d, rtol=1e-10, atol=1e-13)
        assert np.allclose(phi_bh, phi_d, rtol=1e-10)


class TestUniformSphereField:
    @pytest.fixture(scope="class")
    def result(self):
        return run_uniform_sphere(n=4000, theta=0.5)

    def test_bh_matches_direct(self, result):
        assert result["bh_vs_direct_median_rel"] < 0.005, result
        assert result["bh_vs_direct_max_rel"] < 0.05, result

    def test_field_matches_analytic_interior(self, result):
        # kabuk-ortalamali radyal g(r), analitik G M r/R^3'e yakin olmali;
        # tek-parcacik alani Poisson gurultusune gomulur ve esik KONMAZ
        # (yalnizca raporlanir) — dogru karsilastirma kabuk ortalamasidir.
        assert result["shell_mean_rel_err_max"] < 0.05, result
        assert result["shell_mean_rel_err_avg"] < 0.03, result


class TestErrorScaling:
    """Esigi gecmek yetmez: hatalar TEORININ soyledigi gibi mi olcekleniyor?

    Kapida iki olcut de kilpayi geciyor (BH medyan %0.435 vs %0.5; kabuk
    %4.65 vs %5). Tek bir sayi, esigin altinda kalmasinin dogru NEDENDEN mi
    yoksa tesadufen mi oldugunu soylemez. Asagidaki iki test, iki ayri hata
    kaynagini birbirinden ayirir:
        BH hatasi  -> yalnizca acilma acisi theta'ya bagli (agac yaklasimi)
        kabuk hatasi -> yalnizca n'e bagli (Poisson ornekleme gurultusu)
    Bu ayrim olculdu: theta degistirilince kabuk hatasi HIC degismiyor,
    n degistirilince BH medyani neredeyse sabit kaliyor.
    """

    def test_bh_error_grows_with_opening_angle(self):
        """Acilma kriteri dogrulugu GERCEKTEN kontrol ediyor mu?

        Bozuk bir agac da tek bir esigi tesadufen gecebilir; ama hatanin
        theta ile duzgun buyumesi, monopol yaklasiminin dogru yerde devreye
        girdigini gosterir. Olculen: %0.054 / %0.435 / %1.060 (n=4000).
        """
        errs = [
            run_uniform_sphere(n=4000, theta=t)["bh_vs_direct_median_rel"]
            for t in (0.3, 0.5, 0.7)
        ]
        assert errs[0] < errs[1] < errs[2], errs
        # theta=0.3 belirgin sekilde daha dogru olmali (olculen: ~8 kat)
        assert errs[0] < 0.3 * errs[1], errs

    def test_shell_metric_is_stable_across_n(self):
        """ADR-0017: kabuk metrigi ORNEKLEME GURULTUSUNU degil ALANI olcmeli.

        Eski taban (kabuk basina >=50 parcacik) metrigi n'de MONOTON OLMAYAN
        hale getiriyordu — n=2000'de %8.97, yani esigin (%5) neredeyse iki
        kati; n=4000'de %4.65. Sebep, 64 parcacikli bir kabugun ortalamasinin
        gurultusuydu. Taban 200'e cikarilinca olcum kararlilastu.

        Bu test tek bir esigi degil, metrigin cozunurlukten BAGIMSIZ davrandigini
        sabitler: eski hatayi geri getiren bir degisiklik burada yakalanir.
        """
        errs = {n: run_uniform_sphere(n=n)["shell_mean_rel_err_max"]
                for n in (4000, 8000, 16000)}
        for n, e in errs.items():
            assert e < 0.05, (n, errs)
        # hicbir n digerinden 3 kattan fazla sapmamali (eski hal: 5.5 kat)
        assert max(errs.values()) / min(errs.values()) < 3.0, errs

    def test_undersampled_n_raises_instead_of_passing_silently(self):
        """Yetersiz n'de olcut SESSIZCE gecmemeli, acik hata vermeli."""
        with pytest.raises(ValueError, match="yetersiz"):
            run_uniform_sphere(n=800)
