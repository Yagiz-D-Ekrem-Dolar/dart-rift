"""Wendland C2 cekirdegi — Warp device fonksiyonlari (P1-FR-04).

3B (DR-RIFT-P1 §2.4):
    W(q)    = 21/(16*pi*h^3) * (1 - q/2)^4 * (2q + 1),   0 <= q < 2
    dW/dq   = 21/(16*pi*h^3) * (-5q) * (1 - q/2)^3

1B (ayni aile, 1B normalizasyon; Sod/plate dogrulamalari icin):
    W(q)    = 5/(8h) * (1 - q/2)^3 * (1.5q + 1)
    dW/dq   = 5/(8h) * (-3q) * (1 - q/2)^2

dW/dq ifadeleri cebirsel sadelestirmedir; testler sartnamedeki acilimla ve
sayisal turevle karsilastirir. Tum aritmetik FP64.
"""

from __future__ import annotations

import warp as wp

F = wp.float64
V3 = wp.vec3d

_PI = 3.141592653589793

# ONEMLI: Warp, fonksiyon govdesinde yakalanan Python float'lari f32 sabite
# cevirir; FP64 sabitler wp.constant ile TIPLI olarak gomulmelidir.
C3D = wp.constant(F(21.0 / (16.0 * _PI)))
C1D = wp.constant(F(0.625))  # 5/8


@wp.func
def w3d(q: F, h: F) -> F:
    """3B Wendland C2 W(q,h); q = r/h, destek q < 2."""
    if q >= F(2.0):
        return F(0.0)
    c = C3D / (h * h * h)
    t = F(1.0) - F(0.5) * q
    return c * t * t * t * t * (F(2.0) * q + F(1.0))


@wp.func
def dwdq3d(q: F, h: F) -> F:
    """3B Wendland C2 dW/dq."""
    if q >= F(2.0):
        return F(0.0)
    c = C3D / (h * h * h)
    t = F(1.0) - F(0.5) * q
    return c * (F(-5.0) * q) * t * t * t


@wp.func
def grad_w3d(rij: V3, h: F) -> V3:
    """grad_i W(x_i - x_j, h); r -> 0 icin 0 (P1 §5.1)."""
    r = wp.length(rij)
    if r < F(1.0e-12):
        return V3(F(0.0), F(0.0), F(0.0))
    q = r / h
    if q >= F(2.0):
        return V3(F(0.0), F(0.0), F(0.0))
    return (dwdq3d(q, h) / (h * r)) * rij


@wp.func
def w1d(q: F, h: F) -> F:
    """1B Wendland C2 W(q,h)."""
    if q >= F(2.0):
        return F(0.0)
    c = C1D / h  # 5/8h
    t = F(1.0) - F(0.5) * q
    return c * t * t * t * (F(1.5) * q + F(1.0))


@wp.func
def dwdq1d(q: F, h: F) -> F:
    """1B Wendland C2 dW/dq."""
    if q >= F(2.0):
        return F(0.0)
    c = C1D / h
    t = F(1.0) - F(0.5) * q
    return c * (F(-3.0) * q) * t * t


@wp.func
def grad_w1d(dx: F, h: F) -> F:
    """1B grad_i W(x_i - x_j, h) (isaretli)."""
    r = wp.abs(dx)
    if r < F(1.0e-12):
        return F(0.0)
    q = r / h
    if q >= F(2.0):
        return F(0.0)
    return dwdq1d(q, h) / h * (dx / r)


# ---------------------------------------------------------------------------
# Test yardimcilari: device fonksiyonlarini dizi uzerinde calistiran kernel'ler
# (CPU referansiyla birebir karsilastirma icin; uretim yolunda kullanilmazlar)
# ---------------------------------------------------------------------------


@wp.kernel
def _eval_w3d(qs: wp.array(dtype=F), h: F, out_w: wp.array(dtype=F), out_d: wp.array(dtype=F)):
    i = wp.tid()
    out_w[i] = w3d(qs[i], h)
    out_d[i] = dwdq3d(qs[i], h)


@wp.kernel
def _eval_w1d(qs: wp.array(dtype=F), h: F, out_w: wp.array(dtype=F), out_d: wp.array(dtype=F)):
    i = wp.tid()
    out_w[i] = w1d(qs[i], h)
    out_d[i] = dwdq1d(qs[i], h)


def eval_kernel_on_device(qs, h: float, dim: int, device: str):
    """W ve dW/dq degerlerini device fonksiyonlariyla hesapla (test koprusu)."""
    import numpy as np

    q_arr = wp.array(np.asarray(qs, dtype=np.float64), dtype=F, device=device)
    out_w = wp.zeros(len(qs), dtype=F, device=device)
    out_d = wp.zeros(len(qs), dtype=F, device=device)
    kern = _eval_w3d if dim == 3 else _eval_w1d
    wp.launch(kern, dim=len(qs), inputs=[q_arr, F(h)], outputs=[out_w, out_d], device=device)
    return out_w.numpy(), out_d.numpy()
