"""Mühendislik defterinin dizini **eksiksiz** mi?

S2'nin kök nedeni: bir belgeyi `str.replace` ile güncellerken çapa tutmadı ve
değişiklik **sessizce düştü**. Bu tam olarak 4 Ağustos'ta bir kez daha oldu —
`docs/defter/README.md`'ye KAYIT-020 satırı eklenemedi ama commit atıldı.

Kural (KUSUR-KAYDI S2): *belge güncellemesi de bir çıktıdır, denetlenmelidir.*
Bu test dizinin **kendisini** sınar: her KAYIT dosyasının dizinde bir satırı
olmalı ve dizindeki her satır **var olan** bir dosyaya işaret etmeli.

Boşluk kontrolü (ADR-0040): dosyalar gerçekten bulunuyor mu? Bulunmazsa test
boş bir doğruyu sınar; `test_defter_bos_degil` bunu engeller.
"""
from __future__ import annotations

import re
from pathlib import Path

DEFTER = Path(__file__).resolve().parents[1] / "docs" / "defter"


def _kayitlar() -> list[Path]:
    return sorted(DEFTER.glob("KAYIT-*.md"))


def _dizin_metni() -> str:
    return (DEFTER / "README.md").read_text(encoding="utf-8")


def test_defter_bos_degil() -> None:
    """BOŞLUK KONTROLÜ: dosyalar yoksa aşağıdaki testler boş doğru sınar."""
    assert len(_kayitlar()) >= 10, f"beklenenden az kayıt: {len(_kayitlar())}"
    assert (DEFTER / "README.md").exists()


def test_her_kayit_dizinde_var() -> None:
    metin = _dizin_metni()
    eksik = [k.name for k in _kayitlar() if k.name not in metin]
    assert not eksik, f"dizinde OLMAYAN kayıtlar: {eksik}"


def test_dizindeki_her_bag_var_olan_dosyaya_gidiyor() -> None:
    metin = _dizin_metni()
    kirik = [ad for ad in re.findall(r"\((KAYIT-[^)]+\.md)\)", metin)
             if not (DEFTER / ad).exists()]
    assert not kirik, f"KIRIK bağlar: {kirik}"


def test_kayit_numaralari_benzersiz_ve_sirali() -> None:
    nolar = [int(re.match(r"KAYIT-(\d+)", k.name).group(1)) for k in _kayitlar()]
    assert len(nolar) == len(set(nolar)), f"YİNELENEN numara: {nolar}"
    assert nolar == sorted(nolar)
    # Boşluk olmamalı: atlanan numara, kaybolmuş bir kayıt demektir.
    assert nolar == list(range(nolar[0], nolar[0] + len(nolar))), (
        f"numara ATLANMIŞ: {nolar}")
