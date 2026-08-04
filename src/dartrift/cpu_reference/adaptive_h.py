"""Parçacık başına `h` — **tek kaynak** yardımcıları (ADR-0041).

## Sözleşme

ADR-0041 §5b'de kilitlenen dört madde:

1. `h` **parçacık başına** taşınır; çift etkileşimi **simetrik**:
   `h_ij = ½(h_i + h_j)`.
2. `Ω` (grad-h) düzeltmesi uygulanır.
3. CPU referansı ve çapraz kontrol **aynı commit'te**.
4. **Skaler `h` yolu bit düzeyinde korunur** (ADR-0004, determinizm kilitli).

Dördüncüsü bu modülün tasarımını belirliyor: `h` skaler geldiğinde
`pair_h` **skalerin kendisini** döndürür, dolayısıyla çağıran taraftaki
ifadeler **birebir aynı** kalır ve yuvarlama değişmez.

> Bir sarmalayıcı `np.full(n, h)` döndürseydi `q = r/h_ij` bir dizi
> bölmesine dönerdi; NumPy aynı sonucu verir ama bunu **varsaymak** yerine
> skaler yolu hiç değiştirmemek daha güvenlidir. K21'in ilk düzeltmemde
> `1e-14` fark üretmesi bu dersin bedeliydi.

## Neden simetrik `h_ij`

KAYIT-024 dört simetrileştirme biçimini ölçtü. `average_h`
(`h_ij = ½(h_i+h_j)`) hem momentumu **tam** korur (`f_ij = −f_ji`) hem de
arayüzde ölçülen en düşük yapay kuvveti verir (8:1'de `1,0998` — diğerleri
`1,6806` ve `1,5978`).
"""
from __future__ import annotations

import numpy as np

__all__ = ["is_scalar_h", "pair_h", "per_particle_h", "max_h"]


def is_scalar_h(h) -> bool:
    """`h` tek bir sayı mı? (Skaler yol bit düzeyinde korunur.)"""
    return np.isscalar(h) or (isinstance(h, np.ndarray) and h.ndim == 0)


def pair_h(h, n: int):
    """Çift düzleştirme uzunluğu.

    - **skaler** `h` → skalerin **kendisi** (ifadeler değişmez, bit aynı)
    - **dizi** `h` → simetrik matris `½(h_i + h_j)`, şekil `(n, n)`
    """
    if is_scalar_h(h):
        return h
    a = np.asarray(h, dtype=np.float64)
    if a.shape != (n,):
        raise ValueError(f"h şekli {a.shape}, ({n},) olmalı")
    if np.any(a <= 0.0):
        raise ValueError(f"h pozitif olmalı; en küçük {float(a.min())}")
    return 0.5 * (a[:, None] + a[None, :])


def per_particle_h(h, n: int) -> np.ndarray:
    """Parçacık başına `h` dizisi — skaler ise yayılır.

    Balsara, viskozite ve `dt` gibi **tek parçacığa** ait büyüklüklerde
    kullanılır; orada çift matrisi değil, `h_i` gerekir.
    """
    if is_scalar_h(h):
        return np.full(n, float(h), dtype=np.float64)
    a = np.asarray(h, dtype=np.float64)
    if a.shape != (n,):
        raise ValueError(f"h şekli {a.shape}, ({n},) olmalı")
    return a


def max_h(h) -> float:
    """Komşu arama yarıçapı için en büyük `h` (KAYIT-031/033)."""
    return float(h) if is_scalar_h(h) else float(np.max(np.asarray(h)))
