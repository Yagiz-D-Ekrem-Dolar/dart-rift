"""A11 — ensemble'ın krater ayarları kolu **üretimi bozmamalı**.

`krater_capi` ölü (40 durumun hepsinde `6,69 m`, sıfır yayılım) ve kök
neden nicemleme: `λ₂ = 2`'de yalnızca `n_bins = 8` çalışıyor, o da
`±1,5°` → çapta `±4,3 m`. Parametrelerin yarattığı oynama (`~1,4 m`)
bunun **altında** kalıyor.

`--lam2` ve `--n-bins` o ölçümü koşulabilir yapmak için açıldı. Bu
dosyanın işi tek şey: **açılan kol üretim ayarlarını değiştirmiyor.**
Bir tanı bayrağının varsayılanı sessizce kaydırması, bu depoda daha
önce olmuş bir hata sınıfı (rapor A14: `--gozeneksiz` sahneyi de katı
kurmak zorundaydı).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from faz412_Y0_duyarliligi import _krater_ayarlari  # noqa: E402

from dartrift.inference.forward import KRATER_AYARLARI_DART  # noqa: E402


def test_varsayilan_URETIM_ayarlarini_birebir_veriyor() -> None:
    assert _krater_ayarlari(None) == KRATER_AYARLARI_DART


def test_kaynak_sozluk_MUTASYONA_ugramiyor() -> None:
    """Kopya döndürülmeli; yoksa bir çağrı üretimi kalıcı bozar."""
    once = dict(KRATER_AYARLARI_DART)
    d = _krater_ayarlari(16)
    d["n_bins"] = 999
    assert KRATER_AYARLARI_DART == once


def test_n_bins_eziliyor_ve_GERISI_ayni_kaliyor() -> None:
    d = _krater_ayarlari(16)
    assert d["n_bins"] == 16
    for k, v in KRATER_AYARLARI_DART.items():
        if k != "n_bins":
            assert d[k] == v


def test_anlamsiz_n_bins_REDDEDILIYOR() -> None:
    with pytest.raises(ValueError, match="n_bins en az 4"):
        _krater_ayarlari(3)
