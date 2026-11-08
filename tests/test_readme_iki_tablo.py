"""README **iki ayrı** doğrulama tablosu taşıyor mu.

Bir dış geri bildirim şunu söyledi: *"`G0 ✅ G1 ✅ G2 ✅ G3 ✅` gören
bir jüri üyesi bilinçaltında 'fizik doğrulandı' diye düşünebilir."*
Haklı — `G` kapıları **çözücünün** doğru denklemleri doğru çözdüğünü
gösteriyor, hedef problemin çözüldüğünü **değil**.

Bu test iki tablonun ayrı kalmasını kilitliyor. Birleştirilirse
yanıltıcılık geri gelir.

## 2026-11-08 — HANGİ belgeye baktığı değişti

Depo ön sayfası İngilizceye geçti ve iki tabloyu taşıyan Türkçe metin
`docs/README-TR.md`'ye taşındı. Bu test `README.md`'yi okuduğu için
**altı maddesi birden düştü** — tablolar kaybolmamıştı, test yanlış
dosyaya bakıyordu.

İki tablo denetimi, tabloları **taşıyan** belgeye yönlendirildi.
Testin amacı dosya adı değil, *düşen ölçütün görünür kalması*dır.

Ama ön sayfayı denetimsiz bırakmak da olmaz: biri İngilizce README'yi
yalnız başarılarla doldurabilirdi ve hiçbir sınav düşmezdi. Bu yüzden
`test_ON_SAYFA_de_dusenleri_gizlemiyor` eklendi — aşağıda.
"""
from __future__ import annotations

from pathlib import Path

KOK = Path(__file__).resolve().parents[1]

#: Iki dogrulama tablosunu TASIYAN belge.
README = (KOK / "docs" / "README-TR.md").read_text(encoding="utf-8")

#: Deponun ON SAYFASI (ingilizce). Ayri ve daha dar bir denetimi var.
ON_SAYFA = (KOK / "README.md").read_text(encoding="utf-8")


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


def test_ON_SAYFA_de_dusenleri_gizlemiyor() -> None:
    """İngilizce ön sayfa da *"her şey yolunda"* diyemez.

    İki tablo `docs/README-TR.md`'de. Ön sayfa onları tekrarlamak
    zorunda değil ama **sınırları taşımak** zorunda: biri burayı yalnız
    başarılarla doldurursa yukarıdaki testlerin hiçbiri düşmez, çünkü
    onlar başka dosyaya bakıyor. Bu test o boşluğu kapatır.

    Aranan şey biçim değil **amaç**: ön sayfa (a) neyi iddia
    ETMEDİĞİNİ ayrı bir başlıkta söylemeli, (b) yakınsamanın
    sağlanmadığını yazmalı, (c) çalışmayan yolu gizlememeli.
    """
    assert "does not claim" in ON_SAYFA.lower(), (
        "on sayfada 'neyi iddia etmiyoruz' bolumu yok")
    assert "NOT CONVERGED" in ON_SAYFA, (
        "yakinsama saglanmadigi on sayfada yazmiyor")
    assert "unmeasurable" in ON_SAYFA.lower(), (
        "olculemeyen gozlenebilir (krater) on sayfada gizlenmis")


def test_ON_SAYFA_arsivi_isaretliyor() -> None:
    """Eski Türkçe ön sayfa **arşiv** olduğunu söylemeli.

    İkisi yan yana durduğunda okuyan hangisinin güncel olduğunu
    bilmeli; `90/96` diyen bir belge işaretsiz dururken ön sayfa
    `96/96` diyorsa bu bir celiskidir, ikinci bir belge degil.
    """
    bas = README[:1200]
    assert "ARŞİV" in bas, "docs/README-TR.md arsiv oldugunu soylemiyor"
    assert "README.md" in bas, "guncel on sayfaya yonlendirme yok"
