"""Kusur kaydi BELGESI de sinanir — o da bir teslim urunudur.

NEDEN VAR. `docs/KUSUR-KAYDI.md` rapor yazimini besleyen ana belgedir. Uc
bolum icerir ve bunlarin TUTARLI olmasi gerekir: ozet tablo, govde bolumleri,
ve ADR referanslari. Uc kusur (K10, K11, K12) bu belgeye eklenirken
`str.replace` cagrilarinin capasi tutmadi (Turkce 'i' vs 'ı') ve UCU DE
SESSIZCE kayboldu; tablo K11/K12'yi gosteriyordu ama govdede bolumleri yoktu,
K10 ise hicbir yerde yoktu.

Bu, kayitta belgelenen kusurlarin TAM AYNI SINIFI: sessiz basarisizlik,
dogrulanmamis varsayim. Belge kendi kuralina uymak zorunda.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
KAYIT = REPO / "docs" / "KUSUR-KAYDI.md"
ADR_DIZIN = REPO / "docs" / "adr"


@pytest.fixture(scope="module")
def metin() -> str:
    assert KAYIT.is_file(), f"kusur kaydi yok: {KAYIT}"
    return KAYIT.read_text(encoding="utf-8")


def _tablo_kimlikleri(t: str) -> list[str]:
    return re.findall(r"^\| (K\d+|S\d+|B\d+) ", t, re.M)


def _govde_kimlikleri(t: str) -> list[str]:
    return re.findall(r"^## (K\d+|S\d+|B\d+) ", t, re.M)


def test_tablo_ve_govde_birebir_ayni(metin):
    """Her tablo satirinin bir govde bolumu OLMALI ve tersi de.

    Kirilirsa: bir kusur eklenirken yalnizca yarisi islenmis demektir —
    tam olarak K10/K11/K12'de olan sey.
    """
    tablo, govde = _tablo_kimlikleri(metin), _govde_kimlikleri(metin)
    assert tablo, "ozet tablo bos"
    eksik_govde = [k for k in tablo if k not in govde]
    eksik_tablo = [k for k in govde if k not in tablo]
    assert not eksik_govde, f"tabloda var, govdede YOK: {eksik_govde}"
    assert not eksik_tablo, f"govdede var, tabloda YOK: {eksik_tablo}"
    assert tablo == govde, f"SIRA farkli: tablo={tablo} govde={govde}"


def test_kimlikler_bosluksuz_ve_tekrarsiz(metin):
    """K1..Kn kesintisiz olmali; atlanan numara 'kayip kusur' demektir."""
    k = [int(x[1:]) for x in _tablo_kimlikleri(metin) if x.startswith("K")]
    assert len(k) == len(set(k)), f"tekrarlanan kimlik: {k}"
    assert k == sorted(k), f"sirasiz: {k}"
    assert k == list(range(1, len(k) + 1)), f"bosluk var: {k}"


def test_her_kusurun_olculen_etkisi_var(metin):
    """Kaydin kendi kurali: 'hicbir sayi tahmin degildir'.

    Her govde bolumunde en az bir SAYI gecmeli — olcum olmadan kusur kaydi
    yalnizca bir iddiadir.
    """
    bolumler = re.split(r"^## ", metin, flags=re.M)[1:]
    sayisiz = []
    for b in bolumler:
        basl = b.split("\n", 1)[0].strip()
        kimlik = basl.split(" ")[0]
        if not re.match(r"^[KSB]\d+$", kimlik):
            continue
        if not re.search(r"\d[\d.,]*e[+-]?\d|\d+,\d+|%\d|\d+\.\d+", b):
            sayisiz.append(kimlik)
    assert not sayisiz, f"olculen sayi icermeyen kusur kaydi: {sayisiz}"


def test_atifta_bulunulan_ADRler_gercekten_var(metin):
    """Tabloda anilan her ADR dosyasi diskte OLMALI."""
    anilan = set(re.findall(r"\| (00\d\d)(?: ek)? \|", metin))
    assert anilan, "tabloda ADR sutunu bos"
    mevcut = {f.name.split("-")[1] for f in ADR_DIZIN.glob("ADR-*.md")}
    eksik = sorted(anilan - mevcut)
    assert not eksik, f"kayitta anilan ama diskte olmayan ADR: {eksik}"


def test_bu_turun_ADRleri_kayitta_aniliyor(metin):
    """ADR-0029..0033 bu turun kararlari; kayitta izleri olmali."""
    for adr in ("0029", "0030", "0031", "0032", "0033"):
        assert adr in metin, f"ADR-{adr} kusur kaydinda anilmiyor"
