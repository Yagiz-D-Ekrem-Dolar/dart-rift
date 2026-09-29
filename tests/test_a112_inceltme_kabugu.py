"""A112 — inceltme kabuğu sahnenin şeklinden kurulur (elipsoit küreye dönmez)."""
from __future__ import annotations

import numpy as np
import pytest

from dartrift.inference.forward import _inceltme_kabugu
from dartrift.setup.refine import kademe_ayristir, refine_scene_kademeli
from dartrift.setup.scene import build_scene

KADEME = kademe_ayristir(["48:5.6", "24:2.8", "12:1.4", "6:0.7", "3:0.35"], 7.0)
KURE = dict(bulk_density=1600.0, radius=75.0, model_class="M0",
            impactor_mass=500.0, impactor_speed=6000.0, impactor_density=1000.0)
ELIPS = dict(bulk_density=2376.0, model_class="M0", impactor_mass=579.4,
             impactor_speed=6144.9, impactor_density=1000.0, shape="ellipsoid",
             radius=None, semi_axes=[88.5, 87.0, 58.0])


def _kur(kw):
    s = build_scene(spacing=7.0, root_seed=20260906, n_impactor=200,
                    device="cpu", **kw)
    rs = refine_scene_kademeli(s, _inceltme_kabugu(kw, s), KADEME,
                               malzeme_kaynagi="geometri", mermi_h_kipi="kendi")
    return s, rs


def _yari_eksenler(rs):
    x = np.asarray(rs.x)[~np.asarray(rs.is_impactor, bool)]
    return [float(np.percentile(np.abs(x[:, k]), 99.5)) for k in range(3)]


def test_kure_dalinda_kabuk_DEGISMEDI():
    """Varsayılan (küresel) yolda kabuk hâlâ `target_radius`lu icosphere."""
    s = build_scene(spacing=7.0, root_seed=1, device="cpu", n_impactor=200, **KURE)
    mesh = _inceltme_kabugu(KURE, s)
    r = np.linalg.norm(np.asarray(mesh.v), axis=1)
    assert r.min() == pytest.approx(r.max(), rel=1e-9)          # kure
    assert r.mean() == pytest.approx(float(s.target_radius), rel=1e-9)


def test_ELIPSOIT_basikligi_inceltmeden_SONRA_korunuyor():
    s, rs = _kur(ELIPS)
    a, b, c = _yari_eksenler(rs)
    # kisa eksen (58 m) korunmali; A112'den ONCE 72,9 m'ye sisiyordu
    assert c == pytest.approx(58.0, abs=3.0)
    # basiklik: kisa/uzun orani kureye (1,0) degil elipsoide yakin olmali
    assert c / max(a, b) < 0.80


def test_ELIPSOIT_kutlesi_inceltmede_KORUNUYOR():
    s, rs = _kur(ELIPS)
    fark = (float(rs.m.sum()) - float(s.m.sum())) / float(s.m.sum())
    assert abs(fark) < 0.01            # A112'den once +%5,5 idi


def test_kure_gerilemesi_kutle_korunuyor():
    s, rs = _kur(KURE)
    fark = (float(rs.m.sum()) - float(s.m.sum())) / float(s.m.sum())
    assert abs(fark) < 0.01


def test_eksik_semi_axes_HATA():
    s = build_scene(spacing=7.0, root_seed=1, device="cpu", n_impactor=200, **KURE)
    with pytest.raises(ValueError, match="semi_axes"):
        _inceltme_kabugu({"shape": "ellipsoid"}, s)
