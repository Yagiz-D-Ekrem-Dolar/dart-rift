"""Keskin çekirdek anahtarı `h_orani` (h = oran · s_yerel).

COZUNURLUK-DENETIMI §8.3: sonucun `h`'ye mi parçacık sayısına mı bağlı
olduğunu ucuz bir koşuyla sınamak için. Varsayılan `2,0` → bit-aynı; verilince
çözücüye giden bütün `h`'ler `oran/2` ile ölçeklenir.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))


def test_OZET_varsayilanda_ayni_verilince_farkli():
    from dartrift.inference.forward import _fizik_ozeti

    t = {"radius": 82.0}
    a = _fizik_ozeti(t, "m", ("48:5.6",), 7.0, 0.024)
    b = _fizik_ozeti(t, "m", ("48:5.6",), 7.0, 0.024, h_orani=2.0)
    c = _fizik_ozeti(t, "m", ("48:5.6",), 7.0, 0.024, h_orani=1.5)
    assert a == b
    assert a != c


class _Yakalandi(Exception):
    pass


def _h_yakala(monkeypatch, **kw):
    """Çözücü kurulurken `h`'yi yakala ve dur (koşu yok)."""
    from faz48_iki_asama import SAHNE, _mat

    import dartrift.warp_core.solver_solid as SS
    from dartrift.inference.forward import ileri_kosu_merdiven

    yakalanan = {}

    class _Sahte:
        def __init__(self, x, v, m, u, h, *a, **k):
            yakalanan["h"] = np.array(h, dtype=np.float64, copy=True)
            yakalanan["n"] = len(x)
            raise _Yakalandi

    monkeypatch.setattr(SS, "WarpSolid3D", _Sahte)
    with pytest.raises(_Yakalandi):
        ileri_kosu_merdiven(
            np.array([[1.15, 1.0e4, 0.25]]), material=_mat(), device="cpu",
            t_end=1e-4, kademeler=("48:5.6", "24:2.8"), spacing=7.0,
            sahne_taban={**SAHNE, "root_seed": 20260906},
            sok_yargisi=False, **kw)
    return yakalanan


def test_H_ORANI_butun_h_leri_olcekliyor(monkeypatch):
    varsayilan = _h_yakala(monkeypatch)
    keskin = _h_yakala(monkeypatch, h_orani=1.5)
    assert keskin["n"] == varsayilan["n"]
    assert np.allclose(keskin["h"], 0.75 * varsayilan["h"], rtol=1e-15,
                       atol=0.0)
    iki = _h_yakala(monkeypatch, h_orani=2.0)
    assert np.array_equal(iki["h"], varsayilan["h"])


@pytest.mark.parametrize("oran", [1.0, 0.5, 3.5, float("nan"), float("inf")])
def test_GECERSIZ_oran_reddedilir(oran):
    from faz48_iki_asama import SAHNE, _mat

    from dartrift.inference.forward import ileri_kosu_merdiven

    with pytest.raises(ValueError, match="h_orani"):
        ileri_kosu_merdiven(
            np.array([[1.15, 1.0e4, 0.25]]), material=_mat(), device="cpu",
            t_end=1e-4, kademeler=("48:5.6", "24:2.8"), spacing=7.0,
            sahne_taban={**SAHNE, "root_seed": 20260906},
            sok_yargisi=False, h_orani=oran)
