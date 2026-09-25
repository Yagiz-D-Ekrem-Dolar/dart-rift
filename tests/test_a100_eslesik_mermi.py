"""A100 — merdivenle öz-benzer mermi (`eslesik_mermi_sayisi`).

P1 3×3 matrisi: 24 ms `β`'sı hedef/mermi aralık oranına bağlı; köşegenler
(hedef ve mermi birlikte incelirken) birbirine çok yakın. Yardımcı, mermi
parçacık sayısını en ince hedef aralığından türetir.
"""
from __future__ import annotations

import pytest

from dartrift.setup.impactor import build_impactor, eslesik_mermi_sayisi


def test_P1_KOSEGEN_SERISINI_veriyor():
    # L1 mermisi 500 kg, 1000 kg/m3; kaba/orta/ince en ince aralik
    n = [eslesik_mermi_sayisi(s, mass=500.0, density=1000.0, oran=3.65)
         for s in (0.35, 0.175, 0.0875)]
    assert n[0] == pytest.approx(800, rel=0.01)
    assert n[1] == pytest.approx(6400, rel=0.01)
    assert n[2] == pytest.approx(51200, rel=0.01)
    # aralik yariya -> sayi 8 kat
    assert n[1] / n[0] == pytest.approx(8.0, rel=1e-3)
    assert n[2] / n[1] == pytest.approx(8.0, rel=1e-3)


@pytest.mark.parametrize("s_min", [0.35, 0.175])
def test_URETILEN_MERMININ_ARALIGI_hedef_bolu_oran(s_min):
    oran = 3.65
    n = eslesik_mermi_sayisi(s_min, mass=500.0, density=1000.0, oran=oran)
    imp = build_impactor(n, mass=500.0, speed=6000.0, density=1000.0)
    # sayi tamsayiya yuvarlaniyor: araliktaki bagil sapma <= 1/(6 n)
    assert imp.spacing == pytest.approx(s_min / oran, rel=1e-3)


@pytest.mark.parametrize("kw", [
    {"s_hedef_min": 0.0}, {"s_hedef_min": -1.0}, {"oran": 0.0},
    {"mass": float("nan")}, {"density": float("inf")},
])
def test_GECERSIZ_girdi_reddedilir(kw):
    arg = {"s_hedef_min": 0.35, "mass": 500.0, "density": 1000.0, "oran": 3.65}
    arg.update(kw)
    s = arg.pop("s_hedef_min")
    with pytest.raises(ValueError):
        eslesik_mermi_sayisi(s, **arg)


def test_COK_AZ_PARCACIK_reddedilir():
    with pytest.raises(ValueError, match="< 8"):
        eslesik_mermi_sayisi(0.35, mass=500.0, density=1000.0, oran=0.5)
