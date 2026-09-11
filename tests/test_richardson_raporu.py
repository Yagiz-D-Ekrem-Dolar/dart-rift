"""Richardson + tolerans kapısı — uzmanın formülleri ve uyarıları kilitli.

(`test_yakinsama_raporu.py` ayrı ve kilitli Protokol R'nin sınavı.)
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_yol = Path(__file__).resolve().parents[1] / "scripts" / "richardson_raporu.py"
_spec = importlib.util.spec_from_file_location("richardson_raporu", _yol)
yr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(yr)


def test_uzmanin_iki_nokta_sayilari():
    """Soru 18(c): `p = 1 → 5,560`, `p = 2 → 5,820` (Protokol I verisi)."""
    s = yr.iki_noktadan_sinirlar(6.340, 5.950)
    assert s[1.0] == pytest.approx(5.560, abs=1e-3)
    assert s[2.0] == pytest.approx(5.820, abs=1e-3)


@pytest.mark.parametrize("p", [1.0, 2.0, 3.0])
def test_bilinen_mertebe_ve_limit_GERI_KAZANILIYOR(p):
    x = [5.0 + 0.8 * h ** p for h in (4.0, 2.0, 1.0)]
    r = yr.richardson(*x)
    assert r["durum"] == "UYGUN"
    assert r["p"] == pytest.approx(p, abs=1e-12)
    assert r["x_yildiz"] == pytest.approx(5.0, abs=1e-12)


def test_salinimli_farklarda_FORMUL_ZORLANMIYOR():
    r = yr.richardson(6.3, 5.9, 6.1)
    assert r["durum"] == "SALINIMLI ya da DUZ"
    assert r["x_yildiz"] != r["x_yildiz"]       # nan


def test_gurultu_icindeki_farklarda_OKUNMAZ():
    r = yr.richardson(6.34, 5.95, 5.80, s_c=0.12, s_m=0.11, s_f=0.11)
    assert r["durum"] == "GURULTU ICINDE"


def test_asimptotik_olmayan_mertebe_REDDEDILIYOR():
    r = yr.richardson(10.0, 5.0, 4.99)          # p ~ 8,97
    assert r["durum"] == "ASIMPTOTIK DEGIL"


def test_tolerans_kapisi_HATA_CUBUGU_buyudukce_ZORLASIYOR():
    """Uzmanın ters teşvik uyarısı: σ büyüdükçe geçmek KOLAYLAŞMAMALI."""
    x = [5.0 + 0.8 * h ** 2 for h in (4.0, 2.0, 1.0)]
    r = yr.richardson(*x)
    # ince seviyenin gercek hatasi |5,8 - 5,0| = 0,8 (ilk surumde tolerans
    # 0,35 secilmisti -- gecilemez bir esikti, test dustu)
    assert r["hata_ince"] == pytest.approx(0.8)
    tol = 0.9
    assert yr.yakinsama_yargisi(r, tol, s_f=0.01)["karar"] == "YAKINSAMIS"
    assert yr.yakinsama_yargisi(r, tol, s_f=0.10)["karar"] == "YAKINSAMAMIS"


def test_tolerans_ONCEDEN_secilmeli():
    r = yr.richardson(*[5.0 + h ** 2 for h in (4.0, 2.0, 1.0)])
    with pytest.raises(ValueError, match="KOSUDAN ONCE"):
        yr.yakinsama_yargisi(r, 0.0, 0.0)


def test_uygun_olmayan_durum_yargiya_OKUNMAZ_diye_gecer():
    r = yr.richardson(6.3, 5.9, 6.1)
    assert yr.yakinsama_yargisi(r, 1.0, 0.0)["karar"] == "OKUNMAZ"


def test_gci_BILGI_olarak_tasiniyor_sigma_degil():
    x = [5.0 + 0.8 * h ** 2 for h in (4.0, 2.0, 1.0)]
    r = yr.richardson(*x)
    y = yr.yakinsama_yargisi(r, 1.0, 0.0)
    assert "gci_ince_bilgi" in y and y["gci_ince_bilgi"] == pytest.approx(
        1.25 * (x[1] - x[2]) / 3.0)


def test_kilitli_protokol_R_betigi_DOKUNULMADAN_duruyor():
    """`yakinsama_raporu.py` kilitli; bu betik onun yerine GEÇMEZ."""
    kilitli = (Path(__file__).resolve().parents[1] / "scripts"
               / "yakinsama_raporu.py").read_text(encoding="utf-8")
    assert "def richardson(" not in kilitli or "Protokol R" in kilitli
