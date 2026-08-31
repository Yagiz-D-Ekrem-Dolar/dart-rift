"""Terk edilmiş parametre uzayı üretim betiklerine **sızmasın**.

## Neden bu test var

ADR-0044 `DART_UZAYI`'nı terk etti (*"`ρ_yığın` kısıtıyla TUTARSIZ"*)
ama sabit **silinmedi** — RULES.txt gereği karar geri alınabilsin diye.
Sonuç: sabit hâlâ import edilebilir ve `faz5_ensemble_merdiven.py` onu
**koşulsuz** kullanıyordu. TRUBA işi `1539871` (K5 pilot) böyle koştu ve
`19/24` noktası S3'ün gerekçeli `1,30` sınırının dışında kaldı.

> Deponun tekrarlayan kalıbı: **karar belgede kilitli, kodda değil.**
> Bu test kilidi koda taşıyor.

Terk edilmiş uzay hâlâ kullanılabilir — ama **açıkça istenerek**
(`--eski-uzay`), sessizce varsayılan olarak değil.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
TERK = "DART_UZAYI"
KABUL = "DART_UZAYI_S3"

#: Çıkarım tasarımı üreten betikler. Yeni bir tane eklenirse buraya da
#: eklenmeli; liste boş kalırsa test kendini geçersiz sayar.
URETIM = ("faz5_ensemble_merdiven.py",)


def _kaynak(ad: str) -> str:
    y = REPO / "scripts" / ad
    assert y.exists(), f"{ad} yok — liste güncellenmeli"
    return y.read_text(encoding="utf-8")


def test_liste_bos_degil() -> None:
    """BOŞLUK KONTROLÜ: liste boşsa aşağıdaki testler boş doğru sınar."""
    assert URETIM


@pytest.mark.parametrize("ad", URETIM)
def test_tasarim_KABUL_EDILEN_uzaydan_uretiliyor(ad: str) -> None:
    """`lhs_design` / `factorial_design` çağrısı terk edilmiş uzayı
    **doğrudan** almamalı."""
    s = _kaynak(ad)
    kotu = re.findall(rf"(?:lhs_design|factorial_design)\(\s*{TERK}\s*[,)]", s)
    assert not kotu, (
        f"{ad}: tasarım TERK EDİLMİŞ {TERK}'ndan üretiliyor "
        f"(ADR-0044). Kabul edilen uzay {KABUL}.")


@pytest.mark.parametrize("ad", URETIM)
def test_terk_edilmis_uzay_ancak_ACIK_bayrakla(ad: str) -> None:
    """Terk edilmiş uzay geçilebilir olmalı ama **istenerek**."""
    s = _kaynak(ad)
    if TERK not in s.replace(KABUL, ""):
        return                      # hic kullanmiyorsa sorun yok
    assert "--eski-uzay" in s, (
        f"{ad}: {TERK} kullanılıyor ama onu isteyen bir bayrak yok; "
        f"sessizce varsayılan olamaz.")


@pytest.mark.parametrize("ad", URETIM)
def test_terk_edilmis_uzay_kullanilirsa_UYARI_basiliyor(ad: str) -> None:
    """Sonuç yanlışlıkla S3 önseli sanılmasın."""
    s = _kaynak(ad)
    if "--eski-uzay" not in s:
        return
    assert "TERK EDILMIS" in s or "TERK EDİLMİŞ" in s, (
        f"{ad}: eski uzay seçilince ekrana uyarı basılmalı")


def test_ADR_0044_terk_notu_duruyor() -> None:
    """Terk kaydı `design.py`'de kalmalı — silinirse bu test anlamsızlaşır."""
    s = (REPO / "src" / "dartrift" / "inference" / "design.py").read_text(
        encoding="utf-8")
    assert "deprecated:: ADR-0044" in s
    assert "uygulanabilir oranı `0`" in s
    # Kabul edilen uzay gercekten tanimli mi
    assert f"{KABUL} = ParamSpace(" in s
