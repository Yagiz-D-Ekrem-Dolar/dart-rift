"""Depodaki **bütün** Markdown bağlantıları var olan dosyaya gidiyor mu?

NEDEN VAR. `docs/defter/README.md` için bir bağlantı sınavı vardı
(`test_defter_index`), ama **geri kalan belgeler için yoktu**.
2026-11-01'de depo ilk kez baştan sona tarandı ve **beş kırık bağlantı**
bulundu; en eskisi `1e54bea`'dan beri (haftalar) duruyordu:

| belge | kırık hedef | gerçek ad |
|---|---|---|
| `FAZ4-SIKINTI-RAPORU.md` | `../adr/ADR-0055-…` | önek `../` fazlaydı |
| `ADR-0042` | `ADR-0004-determinizm.md` | `ADR-0004-rng-mimarisi.md` |
| `ADR-0043` | `ADR-0026-mermi-cozunurlugu.md` | `…-tekduze-agda-imkansiz.md` |
| `ADR-0044` | `ADR-0030-kutle-hacim-tutarliligi.md` | `…-kutle-gozeneklilikten-turer.md` |
| `ADR-0048` | `KAYIT-053_…_kutle-orani-ve-denetim.md` | `…_enerji-alti-parcacikta.md` |

Dördü **hatırlanan ad** ile **gerçek ad** arasındaki farktan doğdu: dosya
sonradan yeniden adlandırıldı, bağlantı eski adla kaldı. Hiçbir sınav
bakmadığı için sessizce kırık durdular.

Kural (KUSUR-KAYDI S2): *belge güncellemesi de bir çıktıdır,
denetlenmelidir.* Bu sınav o kuralı bütün depoya yayar.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
#: Taranan kokler: docs/ agaci + koktekiki ana belge.
KOKLER = (REPO / "docs",)
TEK_DOSYALAR = (REPO / "README.md", REPO / "CLAUDE.md")
#: Markdown baglantisi: `](hedef)` -- capa (`#...`) ve sema haric.
DESEN = re.compile(r"\]\(([^)\s]+)\)")
SEMALAR = ("http://", "https://", "mailto:", "#")


def _belgeler() -> list[Path]:
    yollar: list[Path] = []
    for kok in KOKLER:
        yollar += sorted(kok.rglob("*.md"))
    yollar += [p for p in TEK_DOSYALAR if p.is_file()]
    return yollar


def test_BOSLUK_belgeler_gercekten_bulunuyor() -> None:
    """BOŞLUK KONTROLÜ (ADR-0040): dosya yoksa aşağıdaki sınav boş geçer."""
    belgeler = _belgeler()
    assert len(belgeler) >= 100, f"beklenenden az belge: {len(belgeler)}"
    assert any(p.name == "README.md" for p in belgeler)


def test_BOSLUK_desen_gercekten_baglanti_yakaliyor() -> None:
    """Desen bozulursa sınav hiçbir şey denetlemez ve yine **geçer**."""
    ornek = "bak [ADR-0064](adr/ADR-0064-x.md) ve [web](https://a.b)"
    assert DESEN.findall(ornek) == ["adr/ADR-0064-x.md", "https://a.b"]
    toplam = sum(len(DESEN.findall(p.read_text(encoding="utf-8")))
                 for p in _belgeler())
    assert toplam >= 500, f"beklenenden az baglanti bulundu: {toplam}"


def test_hicbir_markdown_baglantisi_KIRIK_degil() -> None:
    kirik: list[str] = []
    for p in _belgeler():
        metin = p.read_text(encoding="utf-8")
        for hedef in DESEN.findall(metin):
            if hedef.startswith(SEMALAR):
                continue
            yol = hedef.split("#", 1)[0]
            if not yol:
                continue
            if not (p.parent / yol).resolve().exists():
                kirik.append(f"{p.relative_to(REPO)} -> {hedef}")
    assert not kirik, (
        f"{len(kirik)} KIRIK baglanti:\n  " + "\n  ".join(kirik))
