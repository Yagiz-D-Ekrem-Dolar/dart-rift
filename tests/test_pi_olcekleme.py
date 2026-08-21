"""π-ölçekleme dış kıyasının **kendisi** sınanıyor.

Bu, deponun ilk **dış** doğrulaması: bugüne kadarki bütün ölçütler
modelin kendi iç tutarlılığınaydı (Sedov, Hugoniot, korunum). Dış
kıyas yanlışsa, model "doğrulandı" sanılır — o yüzden formülün
bilinen limitleri burada kilitleniyor.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from pi_olcekleme import (  # noqa: E402
    MALZEMELER,
    SEKIL_BANDI,
    Malzeme,
    hacimden_cap,
    krater_hacmi,
    mermi_yaricapi,
    sekil_yargisi,
    yercekimi_ivmesi,
)


def test_dimorphos_yercekimi_beklenen_mertebede() -> None:
    """`R = 82 m`, `rho = 1800` -> `g ~ 4e-5 m/s²`."""
    g = yercekimi_ivmesi()
    assert 3e-5 < g < 6e-5, g


def test_mermi_yaricapi_kutleyle_tutarli() -> None:
    r = mermi_yaricapi()
    assert 0.30 < r < 0.45, r
    # ters yonde: hacimden kutle geri gelmeli
    m = 2700.0 * (4.0 / 3.0) * math.pi * r ** 3
    assert m == pytest.approx(579.4)


def test_zayif_hedefte_krater_DAHA_BUYUK() -> None:
    """Mukavemet arttıkça krater küçülmeli — yönü yanlışsa her şey yanlış."""
    g, a = yercekimi_ivmesi(), mermi_yaricapi()
    hacim = {m.ad: krater_hacmi(m, g=g, a=a)["V_m3"] for m in MALZEMELER}
    assert hacim["kuru kum"] > hacim["kohezyonlu toprak"] > hacim["sert kaya"]


def test_rejim_ayrimi_dogru_yonde() -> None:
    """`Y = 0` -> yerçekimi rejimi; çok sert -> mukavemet rejimi."""
    g, a = yercekimi_ivmesi(), mermi_yaricapi()
    kum = next(m for m in MALZEMELER if m.ad == "kuru kum")
    kaya = next(m for m in MALZEMELER if m.ad == "sert kaya")
    assert krater_hacmi(kum, g=g, a=a)["rejim"] == "yercekimi"
    assert krater_hacmi(kaya, g=g, a=a)["rejim"] == "mukavemet"


def test_daha_hizli_carpma_DAHA_BUYUK_krater() -> None:
    g, a = yercekimi_ivmesi(), mermi_yaricapi()
    mal = MALZEMELER[0]
    yavas = krater_hacmi(mal, g=g, a=a, U=3000.0)["V_m3"]
    hizli = krater_hacmi(mal, g=g, a=a, U=12000.0)["V_m3"]
    assert hizli > yavas


def test_hacimden_cap_tersine_cevrilebiliyor() -> None:
    D = hacimden_cap(1000.0, 0.20)
    V = (math.pi / 8.0) * D ** 2 * (0.20 * D)
    assert V == pytest.approx(1000.0)
    with pytest.raises(ValueError):
        hacimden_cap(-1.0, 0.2)
    with pytest.raises(ValueError):
        hacimden_cap(1.0, 0.0)


# --------------------------------------------------------- sekil kiyasi

def test_sekil_bandi_literatur_degeri() -> None:
    """Bant değişirse yargı değişir; sabit burada kilitleniyor."""
    assert SEKIL_BANDI == (0.15, 0.30)


def test_canak_derin_ve_sig_ayrimi() -> None:
    assert sekil_yargisi(2.0, 10.0)["yargi"] == "canak"      # 0,20
    assert sekil_yargisi(20.0, 10.0)["yargi"] == "COK_DERIN"  # 2,0
    assert sekil_yargisi(0.5, 10.0)["yargi"] == "COK_SIG"     # 0,05
    assert sekil_yargisi(1.0, 0.0)["yargi"] == "olculemedi"


def test_modelin_OLCULEN_krateri_bandin_DISINDA() -> None:
    """Ölçülen `15,28 / 7,4916` -> `2,04`, bandın `6,8` katı.

    Bu test bir **bulguyu** kilitliyor: model çanak değil delik açıyor.
    Düzelirse test düşer ve rapor güncellenmelidir.
    """
    s = sekil_yargisi(15.28, 7.4916)
    assert s["yargi"] == "COK_DERIN"
    assert s["oran"] == pytest.approx(2.04, abs=0.01)
    assert s["banda_oran"] == pytest.approx(6.8, abs=0.1)


def test_ozel_malzeme_ile_de_calisiyor() -> None:
    """Sabitler dışarıdan verilebilmeli -- tek aileye çakılı değil."""
    mal = Malzeme("deneme", 0.45, 0.40, 0.3, 0.3, 1.0e4, "test")
    r = krater_hacmi(mal, g=yercekimi_ivmesi(), a=mermi_yaricapi())
    assert r["V_m3"] > 0.0 and math.isfinite(r["V_m3"])
