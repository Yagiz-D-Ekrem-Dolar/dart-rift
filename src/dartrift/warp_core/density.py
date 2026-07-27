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
    h: F,
    radius32: wp.float32,
    rho: wp.array(dtype=F),
):
    i = wp.tid()
    xi = x[i]
    acc = F(0.0)
    q = wp.hash_grid_query(grid, x32[i], radius32)
    j = int(0)
    while wp.hash_grid_query_next(q, j):
        r = wp.length(xi - x[j])
        qq = r / h
        if qq < F(2.0):
            acc += m[j] * w3d(qq, h)
    rho[i] = acc


@wp.kernel
def continuity_rate_3d(
    grid: wp.uint64,
    x32: wp.array(dtype=wp.vec3),
    x: wp.array(dtype=V3),
    v: wp.array(dtype=V3),
    m: wp.array(dtype=F),
    h: F,
    radius32: wp.float32,
    drho_dt: wp.array(dtype=F),
):
    i = wp.tid()
    xi = x[i]
    vi = v[i]
    acc = F(0.0)
    q = wp.hash_grid_query(grid, x32[i], radius32)
    j = int(0)
    while wp.hash_grid_query_next(q, j):
        rij = xi - x[j]
        acc += m[j] * wp.dot(vi - v[j], grad_w3d(rij, h))
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
