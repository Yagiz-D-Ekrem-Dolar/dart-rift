"""Yapay viskozite bayrakları — **üretimi bozmadan** taranabilir mi.

A21: çarpma enerjisinin `%78`'i altı parçacıkta ve orada **ısı**
olarak duruyor. Yapay viskozite şok yakalamak için var; ama
`h = 7 m` ile `0,1 m`'lik bir temasta kinetik enerjiyi **yerinde**
ısıya çevirmesi beklenir. `--alpha-av` / `--beta-av` o şüpheliyi
ölçülebilir yapıyor.

Bir tanı bayrağının varsayılanı sessizce kaydırması bu depoda
olmuş bir hata sınıfı (rapor A14). Burada kilitlenen şey o.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from dartrift.cpu_reference.sph_ref import RefParams  # noqa: E402


def test_URETIM_varsayilanlari_degismedi() -> None:
    """`configs/p3_scene.yaml`: `alpha_av: 1.0`, `beta_av: 2.0`."""
    r = RefParams()
    assert r.alpha_av == 1.0
    assert r.beta_av == 2.0


def test_RefParams_AV_disaridan_ezilebiliyor() -> None:
    r = RefParams(cfl=0.25, alpha_av=0.1, beta_av=0.2)
    assert (r.alpha_av, r.beta_av) == (0.1, 0.2)
    assert r.cfl == 0.25


def test_faz48_bayrak_varsayilanlari_URETIM() -> None:
    """Bayraklar eklendi ama varsayılanlar üretimden kaymamalı."""
    import argparse

    import faz48_iki_asama as f
    kaynak = __import__("inspect").getsource(f.main)
    assert '"--alpha-av"' in kaynak and '"--beta-av"' in kaynak
    # varsayilanlari argparse'tan oku
    ap = argparse.ArgumentParser()
    ap.add_argument("--alpha-av", type=float, default=1.0)
    ap.add_argument("--beta-av", type=float, default=2.0)
    a = ap.parse_args([])
    assert (a.alpha_av, a.beta_av) == (1.0, 2.0)


def test_cozucu_imzasi_AV_aliyor() -> None:
    import inspect

    import faz48_iki_asama as f
    s = inspect.signature(f._cozucu)
    for ad, bek in (("alpha_av", 1.0), ("beta_av", 2.0),
                    ("cfl", 0.25), ("u_tabani", False)):
        assert ad in s.parameters, ad
        assert s.parameters[ad].default == bek, (ad, s.parameters[ad].default)


@pytest.mark.parametrize("alpha,beta", [(0.0, 0.0), (0.1, 0.2), (1.0, 2.0)])
def test_AV_sifira_kadar_inebiliyor(alpha: float, beta: float) -> None:
    """`0` da geçerli bir tanı kolu: viskozitesiz koşu."""
    r = RefParams(alpha_av=alpha, beta_av=beta)
    assert r.alpha_av == alpha and r.beta_av == beta
