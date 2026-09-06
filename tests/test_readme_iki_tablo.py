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


def test_bilimsel_tablo_TAMAMLANMADIGINI_soyluyor() -> None:
    """Tablo *"bitti"* izlenimi vermemeli.

    Eskiden başlıkta `**açık**` aranıyordu. `2026-09-06`'da `S1–S8`
    geçti ve başlık sadeleşti; ama **`S9–S12` düştü/yapılamadı** ve
    tablo bunu taşımak zorunda. Sınav biçimden AMACA çevrildi:
    düşen ölçüt **görünür** olacak.
    """
    i = README.index("BİLİMSEL DOĞRULAMA")
    blok = README[i:README.index("Açık kusurlar:", i)]
    assert "DÜŞTÜ" in blok or "YAPILAMADI" in blok, (
        "bilimsel tablo yalnizca GECTI tasiyorsa okuyan 'bitti' saniyor"
    )


def test_mühendislik_kapilari_bilimsel_iddia_YAPMIYOR() -> None:
    """Ayrımın **gerekçesi** yazılı olmalı, yoksa biri yine birleştirir."""
    assert "Bunların hiçbiri şunu kanıtlamaz" in README
    assert "momentum aktarımını doğru modelliyor" in README


def test_bilimsel_olcutlerin_hepsi_DURUM_tasiyor() -> None:
    """`S1 – S12`: her satır GEÇTİ/KISMİ/DÜŞTÜ/YAPILAMADI demeli."""
    for s in ("S1", "S2", "S3", "S4", "S5", "S6",
              "S7", "S8", "S9", "S10", "S11", "S12"):
        i = README.index(f"| **{s}** |")
        satir = README[i:README.index("\n", i)]
        assert any(k in satir for k in
                   ("GEÇTİ", "KISMİ", "DÜŞTÜ", "ölçülmedi",
                    "YAPILAMADI")), satir


def test_DUSEN_olcutler_gizlenmiyor() -> None:
    """Düşen ölçütler README'de **açıkça** yazmalı.

    `2026-09-06`: `S5`/`S7` GEÇTİ'ye döndü (kazıyı durduran kuvvet
    bulundu, ayırt edilebilirlik gösterildi) ama `S9 – S12` düştü.
    Sınav SABİT SATIR NUMARASINA değil, **düşenlerin görünür
    olmasına** bakıyor — yoksa tablo bir sonraki turda sessizce
    yeşile boyanabilir.
    """
    dusenler = []
    for s in ("S9", "S10", "S11", "S12"):
        i = README.index(f"| **{s}** |")
        satir = README[i:README.index("\n", i)]
        if "DÜŞTÜ" in satir or "YAPILAMADI" in satir:
            dusenler.append(s)
    assert len(dusenler) >= 3, (
        f"dort acik olcutten en az ucu dusmus gorunmeli, {dusenler} bulundu"
    )


def test_savunulabilir_cumle_yazili() -> None:
    """Jüriye söylenebilecek cümleler README'de dursun.

    Ve yanlarında **söylenemeyeni** de taşımalı — tek başına
    olumlu cümleler over-claim olur.
    """
    i = README.index("savunulabilir bilimsel cümle")
    blok = README[i:i + 1400]
    # olculmus sayilar cumlelerin ICINDE olmali
    assert "0,47" in blok, "H&H sonucu sayisiz yazilmis"
    assert "1006" in blok or "0,94" in blok, "ayirt edilebilirlik sayisiz"
    # ve SINIR da yazili olmali
    assert "söyleyemiyoruz" in blok or "değil" in blok, (
        "yalniz olumlu cumleler var -- neyi soyleyemedigimiz yazilmali"
    )
