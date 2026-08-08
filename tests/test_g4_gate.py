"""G4 kapı yargısı **kod olarak** — kapının kendisi sınanıyor (FAZ 4.7)."""
from __future__ import annotations

import pytest

from dartrift.validation.g4_gate import (A1_MERMI_PARCACIK, A3_KUTLE_SAPMASI,
                                         B1_BETA_FARKI, KOSULLU_KABULLER,
                                         Olcut, degerlendir)

TAM_44 = {"A1_mermi_parcacik_cap": 2.6, "A2_r_ince_carpani": 8.0,
          "A3_kutle_sapmasi": 2.25e-05, "B1_beta_farki": 0.04,
          "B3_Aprime_daha_yakin": 1.0}
TAM_45 = {"B2_durulmus": 1.0, "B4_enerji_egim": 0.92}
TAM_46 = {"c1_kapsama": 1.0, "c2_en_dar": 0.142, "c3_gecti": True,
          "kuru": False}


def test_hicbir_olcum_yoksa_KAPI_GECMEZ() -> None:
    """Boşluk kontrolü: veri yokken kapı geçerse ölçüt boştur."""
    r = degerlendir()
    assert r.gecti is False
    assert len(r.kosulmayanlar) == 10
    assert r.dusenler == []


def test_TAM_veriyle_kapi_GECIYOR() -> None:
    r = degerlendir(TAM_44, TAM_45, TAM_46)
    assert r.a_gecti and r.b_gecti and r.c_gecti
    assert r.gecti is True
    assert r.kosulmayanlar == [] and r.dusenler == []


def test_KISMI_gecis_yok() -> None:
    """A ve B geçse bile C eksikse kapı geçmez."""
    r = degerlendir(TAM_44, TAM_45, None)
    assert r.a_gecti and r.b_gecti
    assert r.c_gecti is False
    assert r.gecti is False


def test_KURU_KIP_sayilmiyor() -> None:
    """Kuru kip hattın çalıştığını gösterir, kapıyı **geçirmez**."""
    r = degerlendir(TAM_44, TAM_45, dict(TAM_46, kuru=True))
    assert r.c_gecti is False
    assert set(r.kosulmayanlar) == {"C1", "C2", "C3"}
    assert r.gecti is False
    assert "kuru kip" in r.markdown()


@pytest.mark.parametrize("anahtar,deger,kimlik", [
    ("A1_mermi_parcacik_cap", 1.4, "A1"),
    ("A2_r_ince_carpani", 1.0, "A2"),
    ("A3_kutle_sapmasi", 0.02, "A3"),
    ("B1_beta_farki", 0.30, "B1"),
    ("B3_Aprime_daha_yakin", 0.0, "B3"),
])
def test_her_44_olcutu_AYRI_AYRI_dusebiliyor(anahtar, deger, kimlik) -> None:
    """ADR-0040: bir kriter düşebilmelidir — her biri **tek tek** sınanıyor."""
    r = degerlendir(dict(TAM_44, **{anahtar: deger}), TAM_45, TAM_46)
    assert kimlik in r.dusenler
    assert r.gecti is False


@pytest.mark.parametrize("anahtar,deger,kimlik", [
    ("B2_durulmus", 0.0, "B2"),
    ("B4_enerji_egim", 1.6, "B4"),
])
def test_her_45_olcutu_AYRI_AYRI_dusebiliyor(anahtar, deger, kimlik) -> None:
    r = degerlendir(TAM_44, dict(TAM_45, **{anahtar: deger}), TAM_46)
    assert kimlik in r.dusenler
    assert r.gecti is False


@pytest.mark.parametrize("anahtar,deger,kimlik", [
    ("c1_kapsama", 0.667, "C1"),
    ("c2_en_dar", 0.80, "C2"),
    ("c3_gecti", False, "C3"),
])
def test_her_46_olcutu_AYRI_AYRI_dusebiliyor(anahtar, deger, kimlik) -> None:
    r = degerlendir(TAM_44, TAM_45, dict(TAM_46, **{anahtar: deger}))
    assert kimlik in r.dusenler
    assert r.gecti is False


def test_EKSIK_anahtar_gecti_sayilmiyor() -> None:
    """Bir anahtar hiç yoksa `koşulmadı`dır, `geçti` değil."""
    eksik = {k: v for k, v in TAM_44.items() if k != "B1_beta_farki"}
    r = degerlendir(eksik, TAM_45, TAM_46)
    assert "B1" in r.kosulmayanlar
    assert "B1" not in r.dusenler
    assert r.gecti is False


def test_NAN_gecti_sayilmiyor() -> None:
    r = degerlendir(dict(TAM_44, B1_beta_farki=float("nan")), TAM_45, TAM_46)
    assert "B1" in r.kosulmayanlar
    assert r.gecti is False


def test_rapor_KOSULLU_KABULLERI_yaziyor() -> None:
    """Kapı geçse **bile** koşullar raporda kalmalı."""
    m = degerlendir(TAM_44, TAM_45, TAM_46).markdown()
    assert "GEÇİLDİ" in m
    assert "Koşullu kabuller" in m
    for k in KOSULLU_KABULLER:
        assert k[:40] in m


def test_rapor_GECEMEDIGINDE_nedeni_yaziyor() -> None:
    m = degerlendir(TAM_44, TAM_45, None).markdown()
    assert "GEÇİLEMEDİ" in m
    assert "koşulmayan ölçütler" in m
    assert "Kısmi geçiş yoktur" in m


def test_esikler_BELGE_ile_ayni() -> None:
    """Aynı sayı iki yerde yazılı; ayrışırsa test kırılsın (2. turun dersi)."""
    from pathlib import Path

    m = (Path(__file__).resolve().parents[1] / "docs" /
         "G4-OLCUTLERI.md").read_text(encoding="utf-8")
    assert f"{A1_MERMI_PARCACIK:g}".replace(".", ",") in m
    assert f"%{B1_BETA_FARKI * 100:g}" in m
    assert f"%{A3_KUTLE_SAPMASI * 100:g}".replace(".", ",") in m


def test_olcut_yonu_HER_IKI_yonde_calisiyor() -> None:
    assert Olcut("x", "", 0.5, 1.0, "<").gecti is True
    assert Olcut("x", "", 1.5, 1.0, "<").gecti is False
    assert Olcut("x", "", 1.5, 1.0, ">=").gecti is True
    assert Olcut("x", "", 0.5, 1.0, ">=").gecti is False
    assert Olcut("x", "", None, 1.0, "<").gecti is False
