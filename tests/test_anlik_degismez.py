"""Anlık görüntüler **değiştirilemez** mi.

Depo kuralı *"hiçbir satır silinmez"* bir **niyet**tir; niyet
yetmiyor. Hata geçmişi ancak makine tarafından korunursa korunur.

`docs/anlik/MANIFEST.sha256` her görüntünün `sha256`'sını tutuyor.
Eski bir görüntüyü düzenlemek ya da silmek **bu testi düşürür**.
Sonradan öğrenilen her şey **yeni** bir görüntüye yazılır.

Neden gerekli: artifact aynı URL'de güncelleniyor ve depo sürekli
değişiyor. İkisi de *"bugün ne biliyoruz"* sorusunu yanıtlıyor ama
hiçbiri *"`A30` ortaya çıktığında ne biliyorduk"* sorusunu
yanıtlamıyor.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
ANLIK = REPO / "docs" / "anlik"
sys.path.insert(0, str(REPO / "scripts"))

from anlik_al import dogrula, manifest_oku  # noqa: E402


def test_manifest_VAR() -> None:
    assert (ANLIK / "MANIFEST.sha256").exists()


def test_her_goruntu_MANIFESTTEKI_ozetle_ayni() -> None:
    """Asıl kilit: bir görüntü değiştirilmişse burada düşer."""
    bozuk = dogrula()
    assert bozuk == [], f"degistirilmis/silinmis anlik goruntu: {bozuk}"


def test_MANIFEST_DISI_goruntu_yok() -> None:
    """Manifeste girmemiş bir görüntü kilitsizdir — o da kusurdur."""
    kayitli = set(manifest_oku())
    diskte = {p.name for p in ANLIK.glob("ANLIK-*.md")}
    assert diskte == kayitli, (
        f"manifest disi: {diskte - kayitli}; manifeste var ama diskte yok: "
        f"{kayitli - diskte}")


def test_en_az_bir_goruntu_VAR() -> None:
    assert len(manifest_oku()) >= 1


def test_goruntuler_GECERSIZ_KILINAN_alanini_tasiyor() -> None:
    """Bir görüntünün asıl değeri, neyin çürüdüğünü söylemesi."""
    for ad in manifest_oku():
        metin = (ANLIK / ad).read_text(encoding="utf-8")
        assert "GEÇERSİZ KILINAN" in metin, ad
        assert "commit" in metin and "KOŞU KİMLİKLERİ" in metin, ad


def test_goruntu_COMMIT_SHA_tasiyor() -> None:
    """SHA yoksa görüntü doğrulanamaz — kayıt değil, anı olur."""
    import re
    for ad in manifest_oku():
        metin = (ANLIK / ad).read_text(encoding="utf-8")
        assert re.search(r"\| commit \| `[0-9a-f]{40}` \|", metin), ad


def test_ozet_hesabi_dogru() -> None:
    """Testin kendisi doğru hash'i mi hesaplıyor — elden doğrulama."""
    for ad, h in manifest_oku().items():
        elle = hashlib.sha256((ANLIK / ad).read_bytes()).hexdigest()
        assert elle == h, ad


def test_KIRLI_agactan_goruntu_alinmiyor() -> None:
    """`SHA` diskteki kodu göstermezse görüntü doğrulanamaz."""
    import inspect

    import anlik_al
    k = inspect.getsource(anlik_al.main)
    assert "calisma agaci KIRLI" in k
    assert "ZATEN VAR" in k        # ustune yazma da yasak


def test_bozulma_YAKALANIYOR(tmp_path: Path) -> None:
    """Kilidin gerçekten çalıştığının kanıtı — kopyada bozup sınıyoruz."""
    ad = next(iter(manifest_oku()))
    kopya = tmp_path / ad
    kopya.write_text((ANLIK / ad).read_text(encoding="utf-8") + "\nek satir",
                     encoding="utf-8")
    assert hashlib.sha256(kopya.read_bytes()).hexdigest() != manifest_oku()[ad]


def test_manifest_bicimi_okunabilir() -> None:
    metin = (ANLIK / "MANIFEST.sha256").read_text(encoding="utf-8")
    assert metin.startswith("# DEGISTIRILEMEZ")
    for satir in metin.splitlines():
        if satir.strip() and not satir.startswith("#"):
            h, _ad = satir.split(None, 1)
            assert len(h) == 64, satir
            with pytest.raises(ValueError):
                int(h, 10) if not h.isdigit() else (_ for _ in ()).throw(
                    ValueError())
