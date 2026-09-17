"""ADR-0050 — DART "üç küre" mermisi (Owen ve diğ. 2022; L9/L10).

Küre mermi `β`'yı zayıf hedefte `%10–20` fazla veriyor; DART modelleme grubu
gövde + iki panel küresini kullanıyor.
"""
from __future__ import annotations

import numpy as np
import pytest

from dartrift.setup.impactor import (
    DART_MASS,
    DART_SPEED,
    DART_UC_KURE,
    build_impactor,
    coklu_kure_mermi,
    impact_geometry,
    place_impactor,
)
from dartrift.setup.scene import build_scene
from dartrift.setup.shape_mesh import icosphere

SAHNE = dict(radius=20.0, spacing=2.0, bulk_density=1800.0, root_seed=1,
             model_class="M0", n_impactor=200, impactor_mass=DART_MASS,
             impactor_speed=DART_SPEED, device="cpu")


def _geom():
    return impact_geometry(icosphere(3, 20.0), np.array([0.0, 0.0, 1.0]))


def test_KUTLE_ve_MOMENTUM_tam_korunuyor():
    g = _geom()
    imp = coklu_kure_mermi(200, DART_UC_KURE, g)
    assert imp.total_mass == pytest.approx(DART_MASS, rel=1e-12)
    assert np.linalg.norm(imp.momentum) == pytest.approx(DART_MASS * DART_SPEED,
                                                         rel=1e-12)
    # hepsi ayni yonde gidiyor
    yon = imp.v / np.linalg.norm(imp.v, axis=1)[:, None]
    np.testing.assert_allclose(yon, np.broadcast_to(yon[0], yon.shape),
                               atol=1e-12)


def test_KURE_MERKEZLERI_gelis_yonune_DIK_dogruda():
    g = _geom()
    imp = coklu_kure_mermi(400, DART_UC_KURE, g)
    tani = imp.diagnostics["coklu_kure"]
    # parcaciklari kutleye gore kumele: uc yigin bekleniyor
    d = imp.x - imp.x.mean(axis=0)
    # gelis yonune izdusum farki kucuk, yanal ayrim 2 x 2,215 m
    boyuna = d @ g.direction
    yanal = d - boyuna[:, None] * g.direction[None, :]
    assert np.ptp(boyuna) < 1.0
    assert np.ptp(np.linalg.norm(yanal, axis=1)) > 2.0
    assert [t["pay"] for t in tani] == [0.88, 0.06, 0.06]


def test_YUVARLANMA_acisi_dizilimi_donduruyor():
    g = _geom()
    a = coklu_kure_mermi(400, DART_UC_KURE, g, yuvarlanma_deg=0.0)
    b = coklu_kure_mermi(400, DART_UC_KURE, g, yuvarlanma_deg=90.0)
    ya = a.x - a.x.mean(axis=0)
    yb = b.x - b.x.mean(axis=0)
    # ayni yayilim, farkli eksen
    assert np.ptp(np.linalg.norm(ya, axis=1)) == pytest.approx(
        np.ptp(np.linalg.norm(yb, axis=1)), rel=1e-9)
    assert not np.allclose(ya, yb)


@pytest.mark.parametrize("kureler", [(), ((0.5, 0.0), (0.4, 1.0)),
                                     ((1.2, 0.0), (-0.2, 1.0))])
def test_gecersiz_kutle_paylari_REDDEDILIYOR(kureler):
    g = _geom()
    with pytest.raises(ValueError, match="kureler bos|kutle paylari"):
        coklu_kure_mermi(200, kureler, g)


def test_TEK_KURE_payiyla_cagri_tek_kure_yerlestirmesiyle_AYNI():
    g = _geom()
    a = coklu_kure_mermi(200, ((1.0, 0.0),), g)
    b = place_impactor(build_impactor(200), g)
    np.testing.assert_allclose(a.x, b.x, atol=1e-12)
    np.testing.assert_allclose(a.v, b.v, atol=1e-12)
    np.testing.assert_allclose(a.m, b.m, rtol=1e-15)


def test_SAHNE_varsayilani_DEGISMIYOR_ve_uc_kure_taniya_giriyor():
    tek = build_scene(**SAHNE)
    uc = build_scene(**SAHNE, mermi_kureleri=DART_UC_KURE)
    assert tek.diagnostics["mermi_kureleri"] is None
    assert tek.digest == build_scene(**SAHNE).digest
    assert uc.digest != tek.digest
    k = uc.diagnostics["mermi_kureleri"]
    assert [t["ofset_m"] for t in k] == [0.0, -2.215, 2.215]
    # hedef tarafi AYNEN ayni (yalniz mermi degisti)
    h = ~tek.is_impactor
    np.testing.assert_array_equal(tek.x[h], uc.x[~uc.is_impactor])
    assert uc.m[uc.is_impactor].sum() == pytest.approx(DART_MASS, rel=1e-12)
