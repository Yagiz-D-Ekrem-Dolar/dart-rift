"""Sıkıntı raporunun **kendisi** sınanıyor (FAZ 4).

Bir sıkıntı raporu güncellenmezse kötüden beter olur: okuyan onu doğru
sanar. Bu dosya raporun temel değişmezlerini koruyor.
"""
from __future__ import annotations

import re
from pathlib import Path

RAPOR = Path(__file__).resolve().parents[1] / "docs" / "FAZ4-SIKINTI-RAPORU.md"


def test_rapor_VAR() -> None:
    assert RAPOR.is_file(), "FAZ4-SIKINTI-RAPORU.md yok"


def test_ACIK_sikintilar_KOTAYA_baglaniyor() -> None:
    """En önemli engel açıkça yazılı ve **kanıtlı** olmalı."""
    m = RAPOR.read_text(encoding="utf-8")
    assert "AssocGrpCPUMinutesLimit" in m
    assert "7 200 096" in m and "7 200 000" in m
    assert "1460742" in m, "kuyruktaki isin numarasi yazili degil"


def test_hicbir_satir_SILINMEZ_kurali_yazili() -> None:
    m = RAPOR.read_text(encoding="utf-8")
    assert "hiçbir satır silinmez" in m.lower()


def test_KAPANAN_ve_ACIK_sayilari_TABLOLARLA_tutuyor() -> None:
    """Başlıktaki sayı, tablolardaki satır sayısıyla uyuşmalı.

    Bir rapor kendi özetiyle çelişirse okuyan hangisine inanacağını
    bilemez. Sayılar **türetilmiyor** (elle yazılıyor) o yüzden burada
    denetleniyor.
    """
    m = RAPOR.read_text(encoding="utf-8")
    kapanan = int(re.search(r"\*\*Kapanan:\*\* (\d+)", m).group(1))
    acik = int(re.search(r"\*\*Açık:\*\* (\d+)", m).group(1))

    # ACIK: "### A1 ..." basliklari -- AMA kapananlar YERINDE KALIYOR
    # ("hicbir satir silinmez" kurali), o yuzden basligin kendisinde
    # KAPANDI gecenler sayilmaz. Ilk surum hepsini sayiyordu ve A6/A7/A8
    # kapaninca test kirildi: 10 baslik vs Acik=6.
    a_basliklar = re.findall(r"^### (A\d+) —(.*)$", m, flags=re.M)
    a_acik = [k for k, bas in a_basliklar if "KAPANDI" not in bas]
    a_kapali = [k for k, bas in a_basliklar if "KAPANDI" in bas]
    assert len(a_acik) == acik, (
        f"acik A-basliklari {a_acik} ({len(a_acik)}) ile "
        f"Acik={acik} tutmuyor; yerinde kapananlar: {a_kapali}")
    # Numaralar BENZERSIZ olmali: ayni A numarasi iki kez yazilmis olmasin.
    tum = [k for k, _ in a_basliklar]
    assert len(tum) == len(set(tum)), f"tekrar eden A numarasi: {tum}"

    # KAPANAN: §2'de IKI bicim var ve ikisi de sayilmali --
    #   eski girdiler tablo satiri  : "| 7 | belirti | ... |"
    #   yeni girdiler alt baslik    : "### 24 — kollar farkli t_sim'e ..."
    # Ilk surum yalnizca tablo satirlarini sayiyordu; 24-37 eklenince
    # test "Kapanan=37 tutmuyor" dedi ama kusur RAPORDA degil TESTTEydi.
    bolum2 = m.split("## 2. KAPANAN")[1].split("## 3.")[0]
    numaralar = {int(x) for x in re.findall(r"^\| (\d+) \|", bolum2, flags=re.M)}
    numaralar |= {int(x) for x in re.findall(r"^### (\d+) ", bolum2, flags=re.M)}
    assert numaralar == set(range(1, kapanan + 1)), (
        f"numaralar {sorted(numaralar)} ile Kapanan={kapanan} tutmuyor")


def test_DOGRU_yapilanlar_bolumu_var() -> None:
    """Yalnızca hataları listeleyen rapor ne işe yaradığını göstermez."""
    m = RAPOR.read_text(encoding="utf-8")
    assert "doğru** yapılanlar" in m or "doğru yapılanlar" in m.lower()


def test_TEKRARLANAN_kaliplar_sayiliyor() -> None:
    """Bir hata iki kez olduysa **kalıp**tır ve öyle işaretlenmeli."""
    m = RAPOR.read_text(encoding="utf-8")
    assert "kalıp" in m.lower()
    assert "ölçmeden yazmak" in m


def test_kusurlarin_HICBIRI_cozucude_denmiyor_KANITSIZ() -> None:
    """"Hiçbiri çözücüde değil" iddiası sınıflandırmayla desteklenmeli."""
    m = RAPOR.read_text(encoding="utf-8")
    assert "Hiçbiri SPH çözücüsünde değil" in m
    assert "## 3. Kusurların" in m, "siniflandirma bolumu yok"
