"""Kapi metriklerini JSON'a yazarken NumPy skalerlerini guvenle donustur.

Neden gerekli: dogrulama fonksiyonlari NumPy dizileri uzerinde calisir ve
`a > b` gibi karsilastirmalar Python `bool` yerine `np.bool_` uretir. Bu tip
JSON'a serilestirilemez. G2 kapisi TRUBA'da (kosu 1426162) tam da bu yuzden
coktu: FIZIGIN TAMAMI 41 dakika boyunca dogru kostu, sonra rapor yazimi
`TypeError: Object of type bool_ is not JSON serializable` ile dustu ve is
kapi ARIZASI gibi gorundu.

Donusturucu bilincli olarak DAR tutuldu: yalnizca NumPy skalerlerini ve
dizilerini cevirir, taniyamadigi tipte TypeError firlatir. Her seyi `str()`'e
ceviren genis bir yakalayici, gercek bir tip hatasini sessizce rapora
gomerdi — kapi kanitinda bu kabul edilemez.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np


def json_default(o: Any) -> Any:
    """`json.dumps(..., default=...)` icin NumPy -> Python donusturucu."""
    if isinstance(o, np.bool_):
        return bool(o)
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    raise TypeError(f"JSON'a yazilamayan tip: {type(o).__name__}")


def write_metrics(path: Path, metrics: dict) -> None:
    """Metrik sozlugunu JSON olarak yaz (NumPy skalerleri dahil)."""
    path.write_text(
        json.dumps(metrics, indent=2, ensure_ascii=False, default=json_default),
        encoding="utf-8",
    )
