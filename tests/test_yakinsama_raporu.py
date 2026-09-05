"""Yakınsama raporu — **sonuçlardan önce** yazıldı ve testlendi.

`R2`/`R3` bitmeden yazılması kasıtlı: ölçütü sonuca uydurmayı
imkânsız kılıyor. Eşikler Protokol v2'den (`c94d74e`) geliyor,
buradan değil.

`σ_num` kuralı da veriden önce sabit: monoton -> gözlenen mertebe;
monoton değil -> muhafazakâr zarf.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from yakinsama_raporu import (  # noqa: E402
    A1_ESIK,
    A2_ESIK,
    NICELIKLER,
    bagil_fark,
    monoton,
    sigma_num,
)


def test_bagil_fark_DELTA_uzerinden_hesaplaniyor() -> None:
    """`0,030 -> 0,040`: `Δβ`'da `%25`; `β`'da olsaydı `%0,96`."""
    assert bagil_fark(0.030, 0.040) == pytest.approx(0.25)


def test_payda_SONRAKI_cozunurluk() -> None:
    """Daha ince çözünürlük referans alınmalı."""
    assert bagil_fark(1.0, 2.0) == pytest.approx(0.5)
    assert bagil_fark(2.0, 1.0) == pytest.approx(1.0)


def test_UC_NICELIK_birden_isteniyor() -> None:
    assert set(NICELIKLER) == {"delta_beta_hedef", "M_ejekta",
                               "P_ejekta_eksenel"}
    assert A2_ESIK < A1_ESIK


def test_monotonluk_dogru_ayirt_ediliyor() -> None:
    assert monoton([0.0, 0.033, 0.035])
    assert monoton([0.05, 0.04, 0.03])
    assert not monoton([0.03, 0.08, 0.02])       # salinimli
    assert not monoton([0.033, 0.033, 0.033])    # duz


def test_sigma_num_MONOTON_yakinsamada_mertebe_veriyor() -> None:
    s, yontem = sigma_num([0.0, 0.033, 0.0345])
    assert "mertebe" in yontem
    assert 0.0 < s < 0.001


def test_sigma_num_SALINIMLIDA_zarf() -> None:
    s, yontem = sigma_num([0.03, 0.08, 0.02])
    assert "zarf" in yontem
    assert s == pytest.approx(0.06)


def test_sigma_num_IRAKSAYANI_yakaliyor() -> None:
    """Monoton olmak yetmiyor — farklar **büyüyorsa** yakınsama yok.

    `[0, 0,033, 0,070]` monoton ama `p = −0,17`; Richardson formülü
    `3,7e10` gibi anlamsız bir sayı verirdi.
    """
    s, yontem = sigma_num([0.0, 0.033, 0.070])
    assert "IRAKSIYOR" in yontem
    assert s == pytest.approx(0.070)     # zarf, astronomik sayi DEGIL


def test_sigma_num_eksik_veriyle_nan() -> None:
    s, yontem = sigma_num([0.0, 0.033])
    assert yontem == "hesaplanamadi"
    assert s != s                        # nan


def test_esikler_PROTOKOLDEN_geliyor() -> None:
    """Bu betikte tanımlanmıyor, tekrarlanıyor — kaynak Protokol v2."""
    assert (A1_ESIK, A2_ESIK) == (0.20, 0.10)
    k = (REPO / "docs" / "truba" / "OLCUT-yakinsama-gozlenebilir.md"
         ).read_text(encoding="utf-8")
    assert "0,20" in k and "0,10" in k
