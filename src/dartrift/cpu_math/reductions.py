"""Deterministik indirgemeler.

Paralel indirgemede toplama sirasi degisirse kayan-nokta sonucu degisir ve
determinizm kaybolur (DR-RIFT-P0 §3.1). Korunum butceleri bu yuzden SABIT
SIRALI, kompanse (Kahan) toplama ile hesaplanir.
"""

from __future__ import annotations

import numpy as np

__all__ = ["kahan_sum", "fixed_order_sum"]


def kahan_sum(values: np.ndarray) -> float:
    """Sirali Kahan (kompanse) toplam — tek gecis, deterministik.

    Naif toplama gore yuvarlama hatasini buyuk olcude azaltir; eleman sirasi
    sabit oldugu surece sonuc bit duzeyinde tekrarlanabilir.
    """
    arr = np.asarray(values, dtype=np.float64).ravel()
    total = 0.0
    comp = 0.0
    for v in arr:
        y = float(v) - comp
        t = total + y
        comp = (t - total) - y
        total = t
    return total


def fixed_order_sum(values: np.ndarray, block: int = 4096) -> float:
    """Sabit blok sirali toplam: bloklar icinde Kahan, bloklar arasi sirali Kahan.

    Buyuk dizilerde hiz/dogruluk dengesi; blok boyutu sabit oldugu surece sonuc
    deterministiktir (shard sayisindan bagimsiz).
    """
    arr = np.asarray(values, dtype=np.float64).ravel()
    if block < 1:
        raise ValueError(f"block >= 1 olmali: {block}")
    partials = [kahan_sum(arr[i : i + block]) for i in range(0, arr.size, block)]
    return kahan_sum(np.asarray(partials, dtype=np.float64))
