"""Yogunluk kernel'leri: summation + sureklilik capraz-kontrolu (P1-FR-02)."""

from __future__ import annotations

import warp as wp

from .kernel_fn import grad_w1d, grad_w3d, w1d, w3d

F = wp.float64
V3 = wp.vec3d


@wp.kernel
def density_3d(
    grid: wp.uint64,
    x32: wp.array(dtype=wp.vec3),
    x: wp.array(dtype=V3),
    m: wp.array(dtype=F),
    h: wp.array(dtype=F),
    radius32: wp.float32,
    rho: wp.array(dtype=F),
):
    # ADR-0041: `h` PARCACIK BASINA dizidir; cift uzunlugu SIMETRIKTIR
    # (h_i + h_j)/2. Tum h esitken bu TAM OLARAK h verir (h+h = 2h ve
    # 0.5*2h = h, ikisi de kayipsiz) -> bit uyumu korunur.
    i = wp.tid()
    xi = x[i]
    hi = h[i]
    acc = F(0.0)
    q = wp.hash_grid_query(grid, x32[i], radius32)
    j = int(0)
    while wp.hash_grid_query_next(q, j):
        hij = F(0.5) * (hi + h[j])
        r = wp.length(xi - x[j])
        qq = r / hij
        if qq < F(2.0):
            acc += m[j] * w3d(qq, hij)
    rho[i] = acc


@wp.kernel
def continuity_rate_3d(
    grid: wp.uint64,
    x32: wp.array(dtype=wp.vec3),
    x: wp.array(dtype=V3),
    v: wp.array(dtype=V3),
    m: wp.array(dtype=F),
    h: wp.array(dtype=F),
    radius32: wp.float32,
    drho_dt: wp.array(dtype=F),
):
    i = wp.tid()
    xi = x[i]
    hi = h[i]
    vi = v[i]
    acc = F(0.0)
    q = wp.hash_grid_query(grid, x32[i], radius32)
    j = int(0)
    while wp.hash_grid_query_next(q, j):
        rij = xi - x[j]
        acc += m[j] * wp.dot(vi - v[j],
                             grad_w3d(rij, F(0.5) * (hi + h[j])))
    drho_dt[i] = acc


@wp.kernel
def density_1d(
    x: wp.array(dtype=F),
    m: wp.array(dtype=F),
    n: int,
    h: F,
    rho: wp.array(dtype=F),
):
    i = wp.tid()
    xi = x[i]
    acc = F(0.0)
    for j in range(n):
        qq = wp.abs(xi - x[j]) / h
        if qq < F(2.0):
            acc += m[j] * w1d(qq, h)
    rho[i] = acc


@wp.kernel
def continuity_rate_1d(
    x: wp.array(dtype=F),
    v: wp.array(dtype=F),
    m: wp.array(dtype=F),
    n: int,
    h: F,
    drho_dt: wp.array(dtype=F),
):
    i = wp.tid()
    xi = x[i]
    vi = v[i]
    acc = F(0.0)
    for j in range(n):
        dx = xi - x[j]
        acc += m[j] * (vi - v[j]) * grad_w1d(dx, h)
    drho_dt[i] = acc
