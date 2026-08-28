"""Şok sınavı — Rankine-Hugoniot referansı ve sıkışma ölçüsü.

Bu, deponun `β`'dan **bağımsız** ilk yakınsama ölçütü: doğru cevabı
dışarıdan biliyoruz. Araç yanlışsa yargı da yanlış olur, o yüzden
hem Hugoniot bağıntıları hem de tür ayrımı burada kilitleniyor.

Ölçülen (2026-08-21): hedefte hiçbir parçacık `%5`'ten fazla
sıkışmıyor; Hugoniot `%46 – 74` ister. **Model şok üretmiyor.**
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from sok_sinavi import (  # noqa: E402
    BLOK_ESIGI,
    RHO_BLOK,
    RHO_MATRIS,
    beklenen_bant,
    hugoniot,
    sikisma,
    sinav,
)

# ------------------------------------------------------------ Hugoniot

def test_hugoniot_ZAYIF_sokta_ses_hizina_gidiyor() -> None:
    """`up -> 0` iken `Us -> C0` ve sıkışma `-> 0`."""
    h = hugoniot(1.0)
    assert h["Us"] == pytest.approx(2601.5)
    assert h["sikisma_yuzde"] < 0.1


def test_hugoniot_GUCLU_sokta_sikisma_buyuyor() -> None:
    z = hugoniot(1000.0)
    g = hugoniot(3000.0)
    assert g["sikisma_yuzde"] > z["sikisma_yuzde"]
    assert g["P_Pa"] > z["P_Pa"]
    assert g["du_J_kg"] > z["du_J_kg"]


def test_hugoniot_ELDEN_hesapla_tutuyor() -> None:
    """`up = 3000`: `Us = 2600 + 4500 = 7100`; `rho/rho0 = 7100/4100`."""
    h = hugoniot(3000.0)
    assert h["Us"] == pytest.approx(7100.0)
    assert h["sikisma_orani"] == pytest.approx(7100.0 / 4100.0)
    assert h["P_Pa"] == pytest.approx(2700.0 * 7100.0 * 3000.0)


def test_hugoniot_bozuk_girdiyi_REDDEDIYOR() -> None:
    with pytest.raises(ValueError, match="up pozitif"):
        hugoniot(0.0)


def test_bant_DART_hizinda_literatur_mertebesinde() -> None:
    b = beklenen_bant(6144.9)
    alt, ust = b["sikisma_bandi"]
    assert 40.0 < alt < 50.0, alt
    assert 70.0 < ust < 80.0, ust


# ------------------------------------------------------------- sikisma

def test_sikisma_BLOK_ve_MATRISI_ayri_tabanla_olcuyor() -> None:
    """Tek taban kullanmak blokları `%67` sıkışmış gösterirdi.

    Bu bir kez öyle ölçüldü ve düzeltildi; test onu geri getirmiyor.
    """
    rho = np.array([RHO_MATRIS, RHO_BLOK])
    s = sikisma(rho)
    assert s[0] == pytest.approx(0.0, abs=1e-12)
    assert s[1] == pytest.approx(0.0, abs=1e-12)


def test_sikisma_alpha0_ILE_kesin() -> None:
    """`alpha0` verilince taban tam; blok/matris karışmıyor."""
    a0 = np.array([1.7564, 1.05])
    s = sikisma(np.array([RHO_MATRIS * 1.5, RHO_BLOK * 1.2]), a0)
    assert s[0] == pytest.approx(0.5, abs=1e-4)
    assert s[1] == pytest.approx(0.2, abs=1e-4)


def test_sikisma_alpha0_YOKSA_buyuk_sikismada_YANILIYOR() -> None:
    """Tahmin yolunun **sınırı**: `%50` sıkışmış matris blok sanılır.

    Bu bir kusur değil, belgelenmiş bir sınır — ve testte yazılı
    olması, birinin `alpha0`'sız yolu şok kurulduktan sonra
    kullanmasını engelliyor.
    """
    s = sikisma(np.array([RHO_MATRIS * 1.5]))       # 2306 > 2000 -> blok
    assert s[0] < 0.0, s[0]


def test_sikisma_alpha0_bozuksa_REDDEDIYOR() -> None:
    with pytest.raises(ValueError, match="ayni olmali"):
        sikisma(np.zeros(3) + RHO_MATRIS, np.array([1.0]))
    with pytest.raises(ValueError, match="alpha0 pozitif"):
        sikisma(np.array([RHO_MATRIS]), np.array([0.0]))


def test_blok_esigi_sikismis_matrisi_blok_SAYMIYOR() -> None:
    """`%20` sıkışmış matris `1845 kg/m³` — eşiğin (`2000`) altında."""
    assert RHO_MATRIS * 1.2 < BLOK_ESIGI


# --------------------------------------------------------------- sinav

def _sahne(sik_max: float, n: int = 1000):
    """`alpha0` ile birlikte döner — taban tahmine bırakılmıyor."""
    rho = np.full(n, RHO_MATRIS)
    rho[0] = RHO_MATRIS * (1.0 + sik_max)
    return (rho, np.full(n, 1.0e3), np.full(n, 100.0),
            np.full(n, 1.7564))


def test_sinav_SOK_YOK_diyor_olculen_degerlerde() -> None:
    """Ölçülen `%0,25` ve `%3,69` — ikisi de bandın çok altında."""
    for s in (0.0025, 0.03693):
        rho, u, mm, a0 = _sahne(s)
        r = sinav(rho, u, mm, alpha0=a0)
        assert r["yargi"] == "SOK_YOK", (s, r["yargi"])
        assert r["n_bant_icinde"] == 0


def test_sinav_SOK_VAR_diyor_Hugoniot_degerinde() -> None:
    """Boşluk kontrolü: gerçekten şoklanmış madde **görülmeli**."""
    rho, u, mm, a0 = _sahne(0.50)
    r = sinav(rho, u, mm, alpha0=a0)
    assert r["yargi"] == "SOK_VAR"
    assert r["n_bant_icinde"] >= 1


def test_sinav_KISMI_ara_bolgede() -> None:
    rho, u, mm, a0 = _sahne(0.20)
    r = sinav(rho, u, mm, alpha0=a0)          # bandin altinda ama %10'undan buyuk
    assert r["yargi"] == "KISMI"


def test_sinav_bandin_kacta_biri_dogru() -> None:
    rho, u, mm, a0 = _sahne(0.0456)
    r = sinav(rho, u, mm, alpha0=a0)        # bandin ALT ucunun onda biri
    assert r["bandin_kacta_biri"] == pytest.approx(0.1, abs=0.01)
