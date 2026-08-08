"""Koşucu betiklerinin **yol** bağımlılıkları (FAZ 4).

Sabit yazılmış bir depo yolu, depo taşındığında ya da başka bir
kullanıcıyla koşulduğunda **sessizce** yanlış `src`'yi bulur (ya da hiç
bulmaz). Bu dosya zincirin bu hataya geri düşmemesini sağlıyor.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

KOK = Path(__file__).resolve().parents[1]
KOSUCULAR = sorted((KOK / "scripts").glob("faz4*.py"))


def test_kosucu_bulundu() -> None:
    """Boşluk kontrolü: dosya bulunamazsa aşağıdaki testler **boş** geçer."""
    assert len(KOSUCULAR) >= 6, [p.name for p in KOSUCULAR]


@pytest.mark.parametrize("p", KOSUCULAR, ids=lambda p: p.name)
def test_SABIT_depo_yolu_YOK(p: Path) -> None:
    kaynak = p.read_text(encoding="utf-8")
    assert "/arf/scratch" not in kaynak, (
        f"{p.name} sabit TRUBA yolu iceriyor -- REPO'yu __file__'dan turet")


@pytest.mark.parametrize("p", KOSUCULAR, ids=lambda p: p.name)
def test_REPO_dosyadan_turetiliyor(p: Path) -> None:
    kaynak = p.read_text(encoding="utf-8")
    assert "Path(__file__).resolve().parents[1]" in kaynak, p.name


@pytest.mark.parametrize("p", KOSUCULAR, ids=lambda p: p.name)
def test_sozdizimi_gecerli(p: Path) -> None:
    """Bir koşucu ancak koşulduğunda derlenir — sözdizimi hatası kotayı yakar."""
    ast.parse(p.read_text(encoding="utf-8"), filename=str(p))


def test_zincir_betigi_TUM_adimlari_cagiriyor() -> None:
    """Zincir eksik bir adım çağırırsa kapı sessizce "koşulmadı" der."""
    z = (KOK / "scripts" / "faz4_zincir.sh").read_text(encoding="utf-8")
    for ad in ("faz44_dart_yakinsama.py", "faz45_durulma.py",
               "faz46_sentetik_kurtarma.py", "faz47_g4_kapi.py"):
        assert ad in z, ad
    # `set -e` OLMAMALI: bir adim duserse kalanlar da kosmali.
    assert "set -e" not in z.replace("set -u", "")


@pytest.mark.parametrize("p", KOSUCULAR, ids=lambda p: p.name)
def test_UTF8_korumasi_var(p: Path) -> None:
    """Başlıklarda `—` ve `A′` geçiyor; cp1254 konsolda çökerdi.

    Gerçekten oldu: `faz47_g4_kapi.py` `UnicodeEncodeError` ile düştü ve
    ürettiği raporu yok etti. SLURM işi `PYTHONIOENCODING=utf-8` veriyor
    ama betikler **elle** de koşulabilir.
    """
    kaynak = p.read_text(encoding="utf-8")
    assert "_akis.reconfigure" in kaynak, (
        f"{p.name} UTF-8 korumasi icermiyor")
