"""README **iki ayrı** doğrulama tablosu taşıyor mu.

Bir dış geri bildirim şunu söyledi: *"`G0 ✅ G1 ✅ G2 ✅ G3 ✅` gören
bir jüri üyesi bilinçaltında 'fizik doğrulandı' diye düşünebilir."*
Haklı — `G` kapıları **çözücünün** doğru denklemleri doğru çözdüğünü
gösteriyor, hedef problemin çözüldüğünü **değil**.

Bu test iki tablonun ayrı kalmasını kilitliyor. Birleştirilirse
yanıltıcılık geri gelir.
"""
from __future__ import annotations

from pathlib import Path

README = (Path(__file__).resolve().parents[1] / "README.md").read_text(
    encoding="utf-8")


def test_IKI_ayri_baslik_var() -> None:
    assert "MÜHENDİSLİK DOĞRULAMASI" in README
    assert "BİLİMSEL DOĞRULAMA" in README


def test_bilimsel_tablo_ACIK_oldugunu_soyluyor() -> None:
    i = README.index("BİLİMSEL DOĞRULAMA")
    assert "**açık**" in README[i:i + 60]


def test_mühendislik_kapilari_bilimsel_iddia_YAPMIYOR() -> None:
    """Ayrımın **gerekçesi** yazılı olmalı, yoksa biri yine birleştirir."""
    assert "Bunların hiçbiri şunu kanıtlamaz" in README
    assert "momentum aktarımını doğru modelliyor" in README


def test_bilimsel_olcutlerin_hepsi_DURUM_tasiyor() -> None:
    """`S1 – S8`: her satır GEÇTİ/KISMİ/DÜŞTÜ/ölçülmedi demeli."""
    for s in ("S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8"):
        i = README.index(f"| **{s}** |")
        satir = README[i:README.index("\n", i)]
        assert any(k in satir for k in
                   ("GEÇTİ", "KISMİ", "DÜŞTÜ", "ölçülmedi")), satir


def test_DUSEN_olcutler_gizlenmiyor() -> None:
    """`S5` ve `S7` düştü; README bunu **açıkça** yazmalı."""
    for s in ("S5", "S7"):
        i = README.index(f"| **{s}** |")
        assert "DÜŞTÜ" in README[i:README.index("\n", i)], s


def test_savunulabilir_cumle_yazili() -> None:
    """Jüriye söylenebilecek tek cümle README'de dursun."""
    i = README.index("savunulabilir bilimsel cümle")
    blok = README[i:i + 400]
    assert "üretemiyor" in blok
    assert "gürültü tabanında" in blok
