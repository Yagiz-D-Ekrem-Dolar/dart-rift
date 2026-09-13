"""Çarpma sahası koşullaması — Protokol L sonucunun gereği.

L ölçtü: 24 ms'deki `β`'yı istatistiksel iç yapı değil, çarpma noktası
altındaki BLOK belirliyor (bloğa çarpma `β−1 ≈ 0,03`, matrise `≈ 0,5`;
en yakın blok `≤ 0,35 m` ↔ `≥ 2,2 m`). Uzman: *"Çarpma noktasında
bilinen yüzey bloklarını koşullayın; bilinmeyen iç yapıyı
rastgeleleştirin."*
"""
from __future__ import annotations

import numpy as np
import pytest

from dartrift.setup.rubble_generator import place_boulders_v2
from dartrift.setup.scene import _build_mesh, build_scene

ORTAK = dict(radius=30.0, spacing=2.0, model_class="M1", f_boulder=0.25,
             r_min=1.0, r_max=3.0, root_seed=7, blok_uretici="v2",
             boulder_alpha0=1.1, device="cpu")


def _hedef(s):
    h = ~np.asarray(s.is_impactor, bool)
    return np.asarray(s.x)[h], np.asarray(s.is_boulder)[h]


def test_matris_sahasi_yaricap_icinde_BLOK_YOK():
    s = build_scene(**ORTAK, carpma_sahasi="matris", saha_yaricapi=4.0)
    p = np.asarray(s.impact_point)
    C, R = s.blok_alani.centers, s.blok_alani.radii
    assert len(R) > 10
    assert np.all(np.linalg.norm(C - p, axis=1) >= R + 4.0 - 1e-9)
    x, b = _hedef(s)
    assert not np.any(b[np.linalg.norm(x - p, axis=1) < 4.0])


def test_blok_sahasi_carpma_noktasi_BLOGUN_ICINDE():
    s = build_scene(**ORTAK, carpma_sahasi="blok", saha_blok_yaricapi=3.0)
    p, n = np.asarray(s.impact_point), np.asarray(s.surface_normal)
    np.testing.assert_allclose(s.blok_alani.centers[0], p - 1.5 * n, atol=1e-12)
    assert s.blok_alani.radii[0] == 3.0
    x, b = _hedef(s)
    yakin = np.linalg.norm(x - p, axis=1) < 1.5
    assert yakin.any() and np.all(b[yakin])


def test_rastgele_varsayilan_BIT_AYNI():
    a = build_scene(**ORTAK)
    b = build_scene(**ORTAK, carpma_sahasi="rastgele")
    assert a.digest == b.digest
    v1 = {**ORTAK, "blok_uretici": "v1"}
    assert build_scene(**v1).digest == build_scene(**v1).digest


def test_kosullama_v2_ISTER_ve_bilinmeyen_REDDEDILIYOR():
    with pytest.raises(ValueError, match="v2"):
        build_scene(**{**ORTAK, "blok_uretici": "v1"}, carpma_sahasi="matris")
    with pytest.raises(ValueError, match="carpma_sahasi"):
        build_scene(**ORTAK, carpma_sahasi="kenar")


def test_yasak_bolge_dogrudan_yerlestiricide():
    mesh = _build_mesh("icosphere", radius=82.0, subdiv=4)
    m = np.array([0.0, 0.0, 82.0])
    bf, t = place_boulders_v2(mesh, 0.25, 3.0, 1.7, 6.5, 3,
                              yasak_bolgeler=[(m, 5.0)])
    assert t["n_yasak_bolge"] == 1 and not t["doydu"]
    assert np.all(np.linalg.norm(bf.centers - m, axis=1) >= bf.radii + 5.0 - 1e-9)
