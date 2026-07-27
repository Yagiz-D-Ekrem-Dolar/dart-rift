"""SoA duzenine uygun 3-vektor islemleri (x[], y[], z[] ayri diziler)."""

from __future__ import annotations

import numpy as np

__all__ = ["dot3", "cross3", "norm3", "normalize3"]

_Arr = np.ndarray
_Triplet = tuple[_Arr, _Arr, _Arr]


def dot3(a: _Triplet, b: _Triplet) -> _Arr:
    """Eleman-bazli ic carpim: a.b"""
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross3(a: _Triplet, b: _Triplet) -> _Triplet:
    """Eleman-bazli dis carpim: a x b"""
    cx = a[1] * b[2] - a[2] * b[1]
    cy = a[2] * b[0] - a[0] * b[2]
    cz = a[0] * b[1] - a[1] * b[0]
    return cx, cy, cz


def norm3(a: _Triplet) -> _Arr:
    """Eleman-bazli Oklid normu |a|."""
    return np.sqrt(dot3(a, a))


def normalize3(a: _Triplet, eps: float = 0.0) -> _Triplet:
    """Birim vektore olcekle; sifir-norm vektorde ZeroDivisionError yerine acik hata.

    eps > 0 verilirse norm < eps olan girdiler hata uretir (sessiz NaN yok).
    """
    n = norm3(a)
    bad = n <= eps if eps > 0.0 else n == 0.0
    if np.any(bad):
        raise FloatingPointError(
            f"normalize3: {int(np.count_nonzero(bad))} vektorun normu sifira cok yakin"
        )
    return a[0] / n, a[1] / n, a[2] / n
