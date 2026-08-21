"""`a17_carpma_bolgesi_malzemesi` — bölge özeti ve tarama aritmetiği.

A17'de ölçülen şey şu: krater bölgesinin kütlesi ezici çoğunlukla
matris ama **ortalama mukavemetini blok belirliyor**. O ayrımı yapan
iki işlev burada sınanıyor, çünkü ikisi de sessizce yanlış olabilir:

- `_bolge_ozeti` blok payını **kütlece** mi yoksa sayıca mı veriyor
  (`%7,4` ile `%4,5` farklı sayılar ve farklı şey söylüyorlar),
- `_tarama_etkisi` blokların taramadan **bağımsız** olduğunu doğru
  yansıtıyor mu.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from a17_carpma_bolgesi_malzemesi import (  # noqa: E402
    BOULDER_Y0_PA,
    _bolge_ozeti,
    _tarama_etkisi,
)


class _Sahne:
    """`Scene`/`RefinedScene`'in `_bolge_ozeti`'nin kullandığı yüzü."""

    def __init__(self, x, m, Y0, is_boulder, is_impactor):
        self.x = np.asarray(x, np.float64)
        self.m = np.asarray(m, np.float64)
        self.Y0 = np.asarray(Y0, np.float64)
        self.is_boulder = np.asarray(is_boulder, bool)
        self.is_impactor = np.asarray(is_impactor, bool)
        self.impact_point = np.zeros(3)


def _sahne():
    # iki hafif matris (r=1), bir agir blok (r=2), bir mermi (r=1)
    x = [[1.0, 0, 0], [0, 1.0, 0], [0, 0, 2.0], [0, 0, -1.0]]
    m = [100.0, 100.0, 800.0, 1.0]
    y0 = [1.0e4, 1.0e4, BOULDER_Y0_PA, 1.0e4]
    return _Sahne(x, m, y0, [False, False, True, False],
                  [False, False, False, True])


def test_mermi_bolgeye_KATILMIYOR() -> None:
    """Bölge hedefin malzemesini ölçüyor; mermi kütlesi karışırsa yanlış."""
    o = _bolge_ozeti(_sahne(), 1.5)
    assert o["n"] == 2
    assert o["kutle_kg"] == 200.0


def test_blok_payi_KUTLECE_ve_SAYICA_ayri() -> None:
    """Ağır tek blok: kütle payı büyük, sayı payı küçük."""
    o = _bolge_ozeti(_sahne(), 3.0)
    assert o["n"] == 3
    assert o["blok_kutle_payi"] == 800.0 / 1000.0
    assert abs(o["blok_sayi_payi"] - 1.0 / 3.0) < 1e-12


def test_kutle_agirlikli_Y0_bloga_kayiyor() -> None:
    """Kütlece %80 blok -> ortalama matrisin kat kat üstünde."""
    o = _bolge_ozeti(_sahne(), 3.0)
    bekle = (800.0 * BOULDER_Y0_PA + 200.0 * 1.0e4) / 1000.0
    assert abs(o["Y0_kutle_agirlikli_Pa"] - bekle) < 1e-6
    assert o["Y0_medyan_Pa"] == 1.0e4  # medyan hala matris


def test_bos_bolge_sessizce_sifir_dondurmuyor() -> None:
    o = _bolge_ozeti(_sahne(), 0.1)
    assert o["n"] == 0
    assert "blok_kutle_payi" not in o


def test_tarama_bloklarin_payini_DEGISTIRMIYOR() -> None:
    """Aritmetik: blok terimi `matrix_Y0`'dan bagimsiz."""
    t = _tarama_etkisi(0.0738)
    d = t["kutle_agirlikli_Y0_Pa"]
    assert d["1"] > 0.9 * 0.0738 * BOULDER_Y0_PA
    # alti mertebelik tarama, orani birkac kattan fazla oynatmiyor
    assert t["oran_max_min"] < 10.0
    # blok yoksa tarama TAM alti mertebe oynatir
    t0 = _tarama_etkisi(0.0)
    assert t0["oran_max_min"] > 1.0e5
