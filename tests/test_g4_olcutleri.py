"""G4 eşiklerinin **ölçümden önce** sabitlendiğini koruyan testler.

ADR-0040: bir kriter düşebilmelidir. Ölçümden sonra yazılan eşik,
ölçüme uydurulmuş eşiktir. Bu dosya eşikleri **koda** bağlıyor: biri
belgeyi değiştirirse test kırılır ve değişiklik görünür olur.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

BELGE = Path(__file__).resolve().parents[1] / "docs" / "G4-OLCUTLERI.md"

#: Ölçümden ÖNCE sabitlenen eşikler. Bir sayı değişecekse eşik
#: **düşer** ve nedeni bir ADR'ye yazılır — sessizce güncellenmez.
ESIKLER = {
    "A1_mermi_parcacik_cap": 2.0,
    "A2_r_ince_carpani": 3.0,
    "A3_kutle_sapmasi": 0.005,
    "B1_beta_farki": 0.10,
    "B4_enerji_egim": 1.0,
    "C2_posterior_daralma": 0.50,
}


def test_belge_VAR_ve_olcumden_once_yazildi() -> None:
    assert BELGE.is_file(), "G4-OLCUTLERI.md yok"
    m = BELGE.read_text(encoding="utf-8")
    assert "ölçümden **önce**" in m or "ölçümden önce" in m.lower()
    assert "ADR-0040" in m, "düşebilirlik kuralına atıf yok"


@pytest.mark.parametrize("ad,deger", sorted(ESIKLER.items()))
def test_esik_belgede_GECIYOR(ad: str, deger: float) -> None:
    """Her eşik belgede **yazılı** olmalı — kod ile belge ayrışmasın."""
    m = BELGE.read_text(encoding="utf-8")
    if deger < 1.0:
        aday = [f"%{deger * 100:g}".replace(".", ","), f"{deger:g}"]
    else:
        aday = [f"{deger:g}".replace(".", ","), f"{deger:g}"]
    assert any(a in m for a in aday), f"{ad}={deger} belgede bulunamadı ({aday})"


def test_UC_parca_da_zorunlu() -> None:
    """Kısmi geçiş yok — kapının tanımı bu."""
    m = BELGE.read_text(encoding="utf-8")
    assert "Kısmi geçiş yok" in m
    for p in ("G4-A", "G4-B", "G4-C"):
        assert p in m, p


def test_her_olcutun_DUSME_KOSULU_yazili() -> None:
    """Düşemeyen bir ölçüt, ölçüt değildir (ADR-0040)."""
    m = BELGE.read_text(encoding="utf-8")
    assert m.count("Düşme koşul") >= 3, "her bölümde düşme koşulu olmalı"


def test_B1_esiginin_GEREKCESI_yazili() -> None:
    """`%10` keyfî olmadığı için nereden geldiği belgede olmalı."""
    m = BELGE.read_text(encoding="utf-8")
    assert "B1 eşiği neden" in m
    assert "bilinçli olarak gevşek" in m, "gevşeklik itiraf edilmeli"


def test_A3_zaten_OLCULDU_ve_gecti() -> None:
    """Ölçülmüş tek eşik; değeri belgede ve gerçek ölçümle tutarlı."""
    m = BELGE.read_text(encoding="utf-8")
    assert "2,25e-05" in m
    olculen = 2.2515615479570688e-05
    assert olculen < ESIKLER["A3_kutle_sapmasi"]


def test_kosullu_ADR_ler_ISARETLI() -> None:
    """ADR-0041/0042 koşullu; G4 geçse bile bu kapı raporunda kalmalı."""
    m = BELGE.read_text(encoding="utf-8")
    assert "ADR-0041" in m and "ADR-0042" in m
    assert "koşullu" in m


def test_hicbir_olcut_GECTI_diye_isaretlenmemis_olmadan_olculmus() -> None:
    """Koşulmamış bir ölçüt "geçti" yazamaz — §6 tablosu denetleniyor."""
    m = BELGE.read_text(encoding="utf-8")
    bolum = m.split("## 6.")[-1]
    satirlar = [s for s in bolum.splitlines() if s.startswith("| ")]
    for s in satirlar:
        if "geçti" in s:
            # Gecti diyen satirin bir SAYISI olmali.
            assert re.search(r"`[-+0-9.,e]+`", s), f"sayısız 'geçti': {s}"
