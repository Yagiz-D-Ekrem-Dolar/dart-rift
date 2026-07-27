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
