"""Kaynak dosyalarında **kodlama hijyeni**: A106'nın çaresini tamamlar.

## A106 kapandı ama çaresi EKSİK kalmıştı

A106 (2026-09-28) şöyle kapatılmıştı: *"Düzeltme: bütün JSON
okuma/yazma `encoding="utf-8"`."* 2026-11-01'de depo ilk kez **AST ile
baştan sona** tarandı ve kodlama verilmeyen **28** metin G/Ç çağrısı
daha bulundu (`open`, `read_text`, `write_text`). Yani çare üç dosyada
uygulanmış, geri kalanda uygulanmamıştı; hiçbir sınav bakmadığı için
fark edilmedi.

Kusur gerçektir, kozmetik değil: Python'un varsayılan kodlaması
Windows'ta `cp1254`. A106'nın kendi anlatımı — *"`∝` bu kodlamada yok →
`UnicodeEncodeError`; **yargı doğru hesaplanmış olsa bile rapor
çöküyordu**"*. TRUBA `utf-8` olduğu için orada görünmüyor.

## İkinci sınıf: kaynakta UTF-8 BOM

Aynı tarama dört dosyanın **BOM** (`EF BB BF`) ile başladığını buldu:
`scene_checks.py`, `measure_impact_energy_offset.py`, `run_g3_gate.py`,
`run_red_team.py`. Python bunları **koşturur** (kodlama sezgisi BOM'u
yutar), ama `ast.parse(p.read_text(encoding="utf-8"))` **`SyntaxError`
verir** — yani bütün statik analiz bu dosyalarda **kör** kalır.
Deponun var olan AST sınavı (`test_kosucu_yollari`) yalnız
`scripts/faz4*.py`'ye bakıyordu, dördü de kapsam dışıydı.

Bu, A33'ün sınıfı: *sınav geçti, kusur duruyordu.*

> Kural (KUSUR-KAYDI S2): belge de, kaynak hijyeni de bir çıktıdır ve
> **denetlenmelidir**.
"""
from __future__ import annotations

import ast
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
KOKLER = ("src", "scripts", "tests")
#: `Path.read_text(encoding, errors, newline)` -> 1. konumsal kodlamadir.
#: `Path.write_text(data, encoding, ...)`      -> 2. konumsal kodlamadir.
#: `open(file, mode, buffering, encoding, ...)` -> 4. konumsal kodlamadir.
KONUMSAL = {"read_text": 1, "write_text": 2, "open": 4}


def _dosyalar() -> list[Path]:
    yollar: list[Path] = []
    for kok in KOKLER:
        yollar += sorted((REPO / kok).rglob("*.py"))
    return yollar


def _cagri_adi(c: ast.Call) -> str | None:
    if isinstance(c.func, ast.Name):
        return c.func.id
    if isinstance(c.func, ast.Attribute):
        return c.func.attr
    return None


def _ikili_kip(c: ast.Call) -> bool:
    """`mode` icinde `b` varsa ikili akis -- `encoding` YASAK.

    Kip KACINCI konumda oldugu cagri bicimine gore DEGISIR:

        open(yol, "rb+")   -> gomulu islev,  kip args[1]
        yol.open("rb+")    -> Path metodu,   kip args[0]

    Eskiden yalniz `args[1]` bakiliyordu ve `Path.open("rb+")` ikili
    SAYILMIYORDU. Sonuc (2026-11-08): `ensemble.py`'nin yarim kalmis
    JSONL satirini `rb+` ile yoklayan -- ve DOGRU olan -- kodu
    "kodlama vermiyor" diye raporlandi. Oysa ikili akisa `encoding`
    verilmesi `ValueError` atar; sinav imkansiz bir sey istiyordu.

    Ayrim `c.func`'tan yapilir: `ast.Attribute` ise metot cagrisidir.
    """
    metot = isinstance(c.func, ast.Attribute)
    kip_indis = 0 if metot else 1
    kip = None
    if len(c.args) > kip_indis and isinstance(c.args[kip_indis], ast.Constant):
        kip = c.args[kip_indis].value
    for k in c.keywords:
        if k.arg == "mode" and isinstance(k.value, ast.Constant):
            kip = k.value.value
    return isinstance(kip, str) and "b" in kip


def _kodlama_verildi(c: ast.Call, ad: str) -> bool:
    if any(k.arg == "encoding" for k in c.keywords):
        return True
    return len(c.args) >= KONUMSAL[ad]


def test_BOSLUK_dosyalar_bulunuyor() -> None:
    """BOŞLUK KONTROLÜ (ADR-0040): dosya yoksa aşağıdakiler boş geçer."""
    d = _dosyalar()
    assert len(d) >= 400, f"beklenenden az kaynak dosyasi: {len(d)}"


def test_hicbir_kaynak_dosyasi_BOM_ile_BASLAMIYOR() -> None:
    """BOM, `ast.parse`'ı düşürür ve statik analizi **kör** eder."""
    bomlu = [str(p.relative_to(REPO)) for p in _dosyalar()
             if p.read_bytes().startswith(b"\xef\xbb\xbf")]
    assert not bomlu, (
        f"{len(bomlu)} dosya UTF-8 BOM ile basliyor (ast.parse duser):\n  "
        + "\n  ".join(bomlu))


def test_BOSLUK_hepsi_AST_ile_ayristirilabiliyor() -> None:
    """Ayrıştırılamayan dosya aşağıdaki sınavı **sessizce** atlatır."""
    dusen = []
    for p in _dosyalar():
        try:
            ast.parse(p.read_text(encoding="utf-8"))
        except SyntaxError as e:
            dusen.append(f"{p.relative_to(REPO)}: {e}")
    assert not dusen, "AST ayristirmasi dusen dosya:\n  " + "\n  ".join(dusen)


def test_her_metin_GC_cagrisi_KODLAMA_veriyor() -> None:
    """A106'nın çaresi **bütün** depoda geçerli olmalı."""
    eksik: list[str] = []
    sayilan = 0
    for p in _dosyalar():
        for n in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
            if not isinstance(n, ast.Call):
                continue
            ad = _cagri_adi(n)
            if ad not in KONUMSAL:
                continue
            if ad == "open" and _ikili_kip(n):
                continue
            sayilan += 1
            if not _kodlama_verildi(n, ad):
                eksik.append(f"{p.relative_to(REPO)}:{n.lineno} {ad}")
    # BOSLUK KONTROLU: hic cagri bulunmazsa sinav bos gecer.
    assert sayilan >= 100, f"beklenenden az metin G/C cagrisi: {sayilan}"
    assert not eksik, (
        f"{len(eksik)} cagri kodlama vermiyor (Windows'ta cp1254 olur):\n  "
        + "\n  ".join(eksik))


def test_hicbir_cagri_kodlamayi_IKI_KEZ_vermiyor() -> None:
    """Konumsal **ve** anahtar kelime birlikte verilirse `TypeError`.

    Bu sınav, A106'nın çaresini otomatik uygularken benim ürettiğim
    gerçek bir hatayı yakaladı: `write_text(x, "utf-8",
    encoding="utf-8")` yedi yerde oluştu ve `ruff` onu **görmedi**.
    """
    cift: list[str] = []
    for p in _dosyalar():
        for n in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
            if not isinstance(n, ast.Call):
                continue
            ad = _cagri_adi(n)
            if ad not in KONUMSAL:
                continue
            if any(k.arg == "encoding" for k in n.keywords) \
                    and len(n.args) >= KONUMSAL[ad]:
                cift.append(f"{p.relative_to(REPO)}:{n.lineno} {ad}")
    assert not cift, (
        f"{len(cift)} cagri kodlamayi IKI KEZ veriyor (TypeError):\n  "
        + "\n  ".join(cift))


def test_IKILI_kip_her_iki_cagri_biciminde_taninir() -> None:
    """`_ikili_kip`'in 2026-11-08'de kapatılan deliği geri gelmesin.

    Kip, gömülü `open`'da ikinci konumda ama `Path.open`'da
    **birincide**. Eski kontrol yalnız ikinciye bakıyordu ve
    `yol.open("rb+")` ikili sayılmıyordu; doğru yazılmış bir kod
    "kodlama vermiyor" diye raporlanıyordu. İkili akışa `encoding`
    vermek `ValueError` attığı için bu, imkânsız bir talepti.
    """
    ikili = [
        'open(yol, "rb+")', 'open(yol, "wb")', 'open(yol, mode="rb")',
        'yol.open("rb+")', 'yol.open("wb")', 'yol.open(mode="rb")',
    ]
    metin = [
        'open(yol, "r", encoding="utf-8")', 'yol.open(encoding="utf-8")',
        'yol.open("w", encoding="utf-8")',
    ]
    for kaynak in ikili:
        c = ast.parse(kaynak, mode="eval").body
        assert _ikili_kip(c), f"ikili sayilmadi: {kaynak}"
    for kaynak in metin:
        c = ast.parse(kaynak, mode="eval").body
        assert not _ikili_kip(c), f"yanlislikla ikili sayildi: {kaynak}"
