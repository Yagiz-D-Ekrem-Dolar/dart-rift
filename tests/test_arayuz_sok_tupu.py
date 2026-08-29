"""Arayüz şok tüpü — düzenek doğru mu, ve şok basamağı geçiyor mu.

A25'in sorusu tüm Dimorphos sahnesini gerektirmiyor: *"şok `8×` bir
kütle basamağını geçer mi"* düzlemsel bir tüple **saniyeler** içinde
sorulabilir. Sahne koşusunda çok şey aynı anda değişiyor (küresel
geometri, gözeneklilik ızgarası, mermi bağlanması); burada **tek**
değişken basamağın büyüklüğü.

Düzeneğin kendisi yanlışsa yargı da yanlış olur — ilk sürümde enine
boyut **ince** aralıkla ölçekleniyordu ve kaba tarafta yalnızca `12`
parçacık kalıyordu. Burada kilitlenen şey o.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from arayuz_sok_tupu import RHO0, tup_sahnesi, yargi  # noqa: E402


def test_kutle_orani_katin_KUPU() -> None:
    for kat in (1.0, 2.0, 4.0, 20.0):
        assert tup_sahnesi(0.175, kat)["kutle_orani"] == pytest.approx(kat ** 3)


def test_KABA_tarafta_yeterli_parcacik_var() -> None:
    """İlk sürümde `12` parçacık kalıyordu ve ölçüm anlamsızlaşırdı."""
    for kat in (2.0, 4.0, 8.0):
        s = tup_sahnesi(0.175, kat)
        kaba = int((~s["ince"]).sum())
        assert kaba >= 200, (kat, kaba)


def test_ENINE_boyut_kaba_2h_den_buyuk() -> None:
    """Komşuluk düzlemsel kalsın: enine boyut `> 2h_kaba = 4 s_kaba`."""
    for kat in (2.0, 4.0, 8.0):
        s = tup_sahnesi(0.175, kat)
        kaba = ~s["ince"]
        y = s["x"][kaba][:, 1]
        enine = float(y.max() - y.min())
        assert enine > 4.0 * s["s_kaba"] * 0.9, (kat, enine, s["s_kaba"])


def test_maske_KONUMA_bagli_kat1_de_calisiyor() -> None:
    """`kat = 1` denetim kolu: aralık aynı, ama `x > 0` yine ayrılmalı."""
    s = tup_sahnesi(0.175, 1.0)
    assert s["ince"].sum() > 0 and (~s["ince"]).sum() > 0
    assert (s["x"][s["ince"], 0] < 0).all()
    assert (s["x"][~s["ince"], 0] >= 0).all()


def test_kutle_yogunluktan_tutarli() -> None:
    s = tup_sahnesi(0.175, 4.0)
    assert np.allclose(s["m"], RHO0 * s["s"] ** 3)
    assert s["h"] == pytest.approx(2.0 * s["s"])


def test_bozuk_kat_REDDEDILIYOR() -> None:
    with pytest.raises(ValueError, match="kat >= 1"):
        tup_sahnesi(0.175, 0.5)


def test_yargi_KABA_soklandiginda_GECTI_diyor() -> None:
    r = {"sikisma": np.array([0.3, 0.3, 0.05, 0.0]),
         "ince": np.array([True, True, False, False])}
    y = yargi(r)
    assert y["gecti"] and y["kaba_soklu"] == 1
    assert y["kaba_sik_max"] == pytest.approx(5.0)


def test_yargi_yalniz_ince_soklandiginda_GECMEDI_diyor() -> None:
    """Ölçülen durum: kaba tarafta **sıfır** şoklu (A25)."""
    r = {"sikisma": np.array([0.3, 0.2, 0.0, 0.0]),
         "ince": np.array([True, True, False, False])}
    y = yargi(r)
    assert not y["gecti"] and y["kaba_soklu"] == 0
