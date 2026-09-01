r"""Kabuk betikleri `pipefail` kullanıyor mu.

Bu deponun tarihindeki ortak tema: **program "başarılı" diyor ama
ölçüm başka bir şeyi temsil ediyor.**

| | |
|---|---|
| fizik sürümü | `β = 1,4112` — hedef ejektası değil, mermi geri tepmesi |
| araç sürümü | `pytest ... \| tail` — `pytest` düşse de çıkış kodu `0` |

İkisinde de çözüm aynı: **başarı bayrağına değil, başarının nasıl
üretildiğine** güvenmek.

`set -o pipefail` olmadan bir boru hattının çıkış kodu **son**
komutundan gelir. `pytest` düşüp `tail` başarılı olursa dışarıya `0`
çıkar — ve bu bir kez gerçekten oldu: düşük testle push edildi.
"""
from __future__ import annotations

from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SLURM = sorted((REPO / "docs" / "truba").glob("*.slurm"))
KABUK = sorted(REPO.glob("scripts/*.sh"))


def _govde(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


@pytest.mark.parametrize("yol", SLURM + KABUK,
                         ids=lambda p: p.name)
def test_kabuk_betikleri_HATADA_DURUYOR(yol: Path) -> None:
    """`set -u` yetmiyordu: boru hattı hatayı yutuyor."""
    g = _govde(yol)
    assert "set -" in g, f"{yol.name}: hic `set -` yok"
    # `pipefail` ya acikca ya `set -euo pipefail` icinde olmali
    assert "pipefail" in g, (
        f"{yol.name}: `pipefail` YOK -- boru hattinda dusen komut "
        f"sessizce yutulur (bu depoda bir kez oldu: dusuk testle push)")


def test_en_az_bir_betik_var() -> None:
    """Test hiçbir dosya bulamazsa sessizce geçerdi."""
    assert len(SLURM + KABUK) >= 1, "denetlenecek kabuk betigi bulunamadi"


def test_kural_belgede_yazili() -> None:
    """Kuralın gerekçesi kaybolmasın."""
    k = (REPO / "docs" / "FAZ4-SIKINTI-RAPORU.md").read_text(encoding="utf-8")
    assert "pipefail" in k, "kural rapora yazilmamis"
