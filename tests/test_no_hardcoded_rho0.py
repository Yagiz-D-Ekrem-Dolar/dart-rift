"""Tillotson kullanan hiçbir modül `rho0`'ı **elle yazmamalı**.

K7'nin kök nedeni: *bir büyüklük iki yerde yazılıysa ve ikincisi birinciden
türetilmiyorsa, üretim değerlerinde tesadüfen tutar ve biri değişince
ötekini sessizce bozar.*

Bulunuş (4 Ağustos taraması): `validation/ablation.py` ve
`validation/porous.py` kütleyi **yerel** `rho0 = 2700.0` ile kuruyor, ama
EOS `tillotson` ve `TillotsonParams.rho0` da **ayrıca** 2700. İkisi bağlı
değildi. Canlı bir hata değildi — ama hiçbir şey onları bağlı tutmuyordu.

`TillotsonParams.rho0` değişseydi bu doğrulamalar **ön-gerilmeli** bir
başlangıç durumu ölçer ve yine "geçti" derdi.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from dartrift.cpu_reference.materials import TillotsonParams

SRC = Path(__file__).resolve().parents[1] / "src" / "dartrift"
RHO0 = TillotsonParams().rho0


def _tillotson_kullanan_dosyalar() -> list[Path]:
    return [f for f in SRC.rglob("*.py")
            if 'eos="tillotson"' in f.read_text(encoding="utf-8")
            or "eos='tillotson'" in f.read_text(encoding="utf-8")]


def test_tarama_bos_degil() -> None:
    """BOŞLUK KONTROLÜ: hiç dosya bulunmazsa test boş bir doğru sınar."""
    assert len(_tillotson_kullanan_dosyalar()) >= 3, _tillotson_kullanan_dosyalar()


@pytest.mark.parametrize("dosya", _tillotson_kullanan_dosyalar(),
                         ids=lambda p: p.name)
def test_rho0_elle_yazilmamis(dosya: Path) -> None:
    """`rho0`/`rho` **atamalarında** `2700` sabiti geçmemeli."""
    hatali = []
    for no, satir in enumerate(dosya.read_text(encoding="utf-8").splitlines(), 1):
        kod = satir.split("#", 1)[0]
        if re.search(r"\brho0?(_solid|_linear)?\s*[:=][^=]*\b2700(\.0*)?\b", kod):
            hatali.append(f"{dosya.name}:{no}: {satir.strip()}")
    assert not hatali, (
        "rho0 ELLE yazılmış — TillotsonParams().rho0'dan türetilmeli:\n"
        + "\n".join(hatali))


def test_kanonik_deger_hala_bazalt() -> None:
    """Tek kaynağın kendisi beklenen değerde mi (Benz & Asphaug 1999 bazalt)."""
    assert RHO0 == pytest.approx(2700.0)


def test_turetilen_sabitler_tek_kaynakla_ayni() -> None:
    from dartrift.validation.mass_ratio import RHO0_SOLID
    assert RHO0_SOLID == RHO0
