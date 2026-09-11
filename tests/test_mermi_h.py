"""Mermi `h/s` oranı — uzman Soru 5.

Uzman: *"'800' tek başına karar verdirmez; hedef ve çarpanın kendi
çözünürlükleri, h/s oranı ... ayrı sınanmalı. Mevcut yerel inceltme
çarpan noktalarını sabit tutup h'yi değiştirebildiği için yalnız hedefi
inceltmek temiz bir çarpan yakınsaması değildir."*

Ölçüldü: mermi `803` parçacık, kendi aralığı `~0,072 m`. `"merdiven"`
kipinde `h_mermi = 2 s_min`: kabada `h/s ≈ 10`, ortada `~5`, incede
`~2,4`. `"kendi"` kipinde her merdivende AYNI (`h/s = 2`).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))


@pytest.fixture(scope="module")
def kaba_sahne():
    from faz48_iki_asama import SAHNE

    from dartrift.inference.design import DART_UZAYI_S3, lhs_design
    from dartrift.inference.forward import sahne_parametreleri
    from dartrift.setup.scene import _build_mesh, build_scene

    th = lhs_design(DART_UZAYI_S3, 24, root_seed=20260906)[0]
    kaba = build_scene(spacing=7.0, device="cpu",
                       **sahne_parametreleri(th, {**SAHNE, "root_seed": 20260906}))
    mesh = _build_mesh("icosphere", radius=float(kaba.target_radius), subdiv=4)
    return kaba, mesh


def _kur(kaba_sahne, merdiven, kip):
    from dartrift.setup.refine import kademe_ayristir, refine_scene_kademeli

    kaba, mesh = kaba_sahne
    return refine_scene_kademeli(kaba, mesh, kademe_ayristir(merdiven, 7.0),
                                 mermi_h_kipi=kip)


KABA = ("48:5.6", "24:2.8", "12:1.4", "6:0.7", "3:0.35")
ORTA = ("48:2.8", "24:1.4", "12:0.7", "6:0.35", "3:0.175")


def test_merdiven_kipinde_mermi_h_s_KABADA_yaklasik_10(kaba_sahne):
    rs = _kur(kaba_sahne, KABA, "merdiven")
    assert rs.diagnostics["mermi_h_kipi"] == "merdiven"
    assert 8.0 < rs.diagnostics["mermi_h_bolu_s"] < 12.0
    assert np.all(rs.h[rs.is_impactor] == pytest.approx(0.70))


def test_kendi_kipinde_mermi_h_s_IKI_ve_merdivenden_BAGIMSIZ(kaba_sahne):
    a = _kur(kaba_sahne, KABA, "kendi")
    b = _kur(kaba_sahne, ORTA, "kendi")
    assert a.diagnostics["mermi_h_bolu_s"] == pytest.approx(2.0, rel=1e-6)
    np.testing.assert_array_equal(a.h[a.is_impactor], b.h[b.is_impactor])
    # hedef h'leri kip degismeden AYNI
    ref = _kur(kaba_sahne, KABA, "merdiven")
    np.testing.assert_array_equal(a.h[~a.is_impactor], ref.h[~ref.is_impactor])


def test_bilinmeyen_kip_REDDEDILIYOR(kaba_sahne):
    with pytest.raises(ValueError, match="mermi_h_kipi"):
        _kur(kaba_sahne, KABA, "yarim")


def test_ileri_model_varsayilani_MERDIVEN_ve_ozet_ayri():
    import inspect

    from dartrift.inference.forward import _fizik_ozeti, ileri_kosu_merdiven

    assert inspect.signature(ileri_kosu_merdiven).parameters[
        "mermi_h_kipi"].default == "merdiven"
    t = {"radius": 82.0}
    assert (_fizik_ozeti(t, "m", KABA, 7.0, 0.024)
            != _fizik_ozeti(t, "m", KABA, 7.0, 0.024, mermi_h_kipi="kendi"))
