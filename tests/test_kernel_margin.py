"""Kenar payının tek kaynağı — ve **elle yazılmadığının** denetimi.

K7'nin kalıbı: aynı büyüklüğün birden fazla yerde yazılması. Pay formülü
(`2h + s/2`) dört modülde ayrı ayrı duruyordu; hepsi bugün aynıydı ama
hiçbir şey onları aynı tutmuyordu.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from dartrift.validation.kernel_margin import (SUPPORT_OVER_H, margin_factor,
                                               support_margin)

VAL = Path(__file__).resolve().parents[1] / "src" / "dartrift" / "validation"


def test_wendland_destegi_iki_h() -> None:
    """Wendland C2: `W(q) = 0` for `q ≥ 2` → destek `2h`."""
    from dartrift.cpu_reference.sph_ref import kernel_w

    assert SUPPORT_OVER_H == 2.0
    # KALIBRASYON: cekirdek gercekten 2h'de sifirlaniyor mu?
    assert float(kernel_w(2.0, 1.0, 3)) == 0.0
    assert float(kernel_w(1.99, 1.0, 3)) > 0.0


def test_pay_degerleri_eski_formulle_ayni() -> None:
    """Gerileme: tek kaynağa taşımak **sayıları değiştirmemeli**."""
    assert support_margin(10.4, 8.0) == pytest.approx(2.0 * 10.4 + 0.5 * 8.0)
    assert support_margin(10.4, 8.0, 2) == pytest.approx(4.0 * 10.4 + 0.5 * 8.0)
    assert margin_factor(1.3, 2) == pytest.approx(4.0 * 1.3 + 0.5)


def test_depth_paylari_ayiriyor() -> None:
    """`depth = 2`, `depth = 1`'den **kesinlikle** büyük olmalı."""
    bir = support_margin(10.4, 8.0, 1)
    iki = support_margin(10.4, 8.0, 2)
    assert iki > bir
    assert iki - bir == pytest.approx(SUPPORT_OVER_H * 10.4)


def test_gecersiz_girdi_reddediliyor() -> None:
    for h, s in ((0.0, 8.0), (-1.0, 8.0), (10.4, 0.0)):
        with pytest.raises(ValueError, match="pozitif"):
            support_margin(h, s)
    for d in (0, -1, 1.5):
        with pytest.raises(ValueError, match="depth"):
            support_margin(10.4, 8.0, d)
    with pytest.raises(ValueError, match="pozitif"):
        margin_factor(0.0)


def test_pay_formulu_ELLE_yazilmamis() -> None:
    """Doğrulama modüllerinde `2.0*h + 0.5*spacing` kalıbı kalmamalı.

    K7 dört kez tekrarladı; bu tarama beşincisini engeller. Bulunursa
    `support_margin`'e taşınmalı — ya da o satır neden ayrı olduğunu
    **yorumla açıklamalı** (yorumlar taranmıyor).
    """
    kalip = re.compile(r"\b[24]\.0\s*\*\s*h\w*\s*\+\s*0\.5\s*\*\s*(spacing|s_\w+)")
    hatali = []
    for f in sorted(VAL.glob("*.py")):
        if f.name == "kernel_margin.py":
            continue
        for no, satir in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if kalip.search(satir.split("#", 1)[0]):
                hatali.append(f"{f.name}:{no}: {satir.strip()}")
    assert not hatali, (
        "pay formülü ELLE yazılmış — `support_margin` kullanılmalı:\n"
        + "\n".join(hatali))


def test_tarama_bos_degil() -> None:
    """BOŞLUK KONTROLÜ: taranan dosya yoksa yukarıdaki test boş bir doğrudur."""
    assert len(list(VAL.glob("*.py"))) >= 10
