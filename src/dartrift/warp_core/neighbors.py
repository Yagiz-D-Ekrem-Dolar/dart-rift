"""Komsu listesi cikarma kernel'leri — parite testleri icin (P1-FR-01).

Uretim kernel'leri komsulari listeye YAZMADAN yerinde tuketir (density/forces);
buradaki kernel'ler hash-grid komsu kumesinin brute-force ile birebir ayni
oldugunu kanitlamak icin listeyi acikca cikarir.
"""

from __future__ import annotations

import warp as wp

F = wp.float64
V3 = wp.vec3d


@wp.kernel
def gather_neighbors_grid(
    grid: wp.uint64,
    x32: wp.array(dtype=wp.vec3),
    x: wp.array(dtype=V3),
    support: F,
    radius32: wp.float32,
    max_nb: int,
    counts: wp.array(dtype=wp.int32),
    lists: wp.array2d(dtype=wp.int32),
):
    i = wp.tid()
    xi = x[i]
    cnt = 0
    q = wp.hash_grid_query(grid, x32[i], radius32)
    j = 0
    while wp.hash_grid_query_next(q, j):
        r = wp.length(xi - x[j])
        if r < support:  # kesin FP64 filtre
            if cnt < max_nb:
                lists[i, cnt] = j
            cnt += 1
    counts[i] = cnt


@wp.kernel
def gather_neighbors_brute(
    x: wp.array(dtype=V3),
    n: int,
    support: F,
    max_nb: int,
    counts: wp.array(dtype=wp.int32),
    lists: wp.array2d(dtype=wp.int32),
):
    i = wp.tid()
    xi = x[i]
    cnt = 0
    for j in range(n):
        r = wp.length(xi - x[j])
        if r < support:
            if cnt < max_nb:
                lists[i, cnt] = j
            cnt += 1
    counts[i] = cnt
