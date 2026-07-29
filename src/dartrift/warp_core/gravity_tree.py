"""Oz-yercekimi kernel'leri: dogrudan N^2 (referans) + Barnes-Hut halat gezinmesi.

Agac CPU'da kurulur (cpu_reference/gravity_ref.py — deterministik DFS + halat);
GPU kernel'i ayni duzlestirilmis dizileri YIGITSIZ gezer (P2 §5.4).
Yumusatma: Plummer. Potansiyel, enerji muhasebesi icin birlikte hesaplanir.
"""

from __future__ import annotations

import numpy as np
import warp as wp

F = wp.float64
V3 = wp.vec3d


@wp.kernel
def gravity_direct_k(
    x: wp.array(dtype=V3),
    m: wp.array(dtype=F),
    n: int,
    G: F,
    eps2: F,
    g: wp.array(dtype=V3),
    phi: wp.array(dtype=F),
):
    i = wp.tid()
    xi = x[i]
    acc = V3(F(0.0), F(0.0), F(0.0))
    pot = F(0.0)
    for j in range(n):
        if j != i:
            d = x[j] - xi
            r2 = wp.dot(d, d) + eps2
            inv_r = F(1.0) / wp.sqrt(r2)
            acc += G * m[j] * d * inv_r / r2
            pot -= G * m[j] * inv_r
    g[i] = acc
    phi[i] = pot


@wp.kernel
def gravity_bh_k(
    x: wp.array(dtype=V3),
    m: wp.array(dtype=F),
    com: wp.array(dtype=V3),
    node_mass: wp.array(dtype=F),
    node_size: wp.array(dtype=F),
    first_child: wp.array(dtype=wp.int32),
    next_skip: wp.array(dtype=wp.int32),
    leaf_start: wp.array(dtype=wp.int32),
    leaf_count: wp.array(dtype=wp.int32),
    perm: wp.array(dtype=wp.int32),
    G: F,
    eps2: F,
    theta: F,
    g: wp.array(dtype=V3),
    phi: wp.array(dtype=F),
):
    i = wp.tid()
    p = x[i]
    acc = V3(F(0.0), F(0.0), F(0.0))
    pot = F(0.0)
    node = int(0)
    while node != -1:
        d = com[node] - p
        dist2 = wp.dot(d, d) + eps2
        dist = wp.sqrt(dist2)
        fc = first_child[node]
        if fc < 0:  # yaprak: parcaciklari dogrudan topla (oz-etkilesim haric)
            s0 = leaf_start[node]
            cnt = leaf_count[node]
            for k in range(cnt):
                j = int(perm[s0 + k])
                if j != i:
                    dj = x[j] - p
                    r2 = wp.dot(dj, dj) + eps2
                    inv_r = F(1.0) / wp.sqrt(r2)
                    acc += G * m[j] * dj * inv_r / r2
                    pot -= G * m[j] * inv_r
            node = int(next_skip[node])
        elif node_size[node] < theta * dist:  # acilma kriteri: monopol yeter
            acc += G * node_mass[node] * d / (dist2 * dist)
            pot -= G * node_mass[node] / dist
            node = int(next_skip[node])
        else:
            node = int(fc)
    g[i] = acc
    phi[i] = pot


class GravitySolver:
    """Konfigurasyona gore dogrudan N^2 veya Barnes-Hut hesaplayici."""

    def __init__(self, params, device: str):
        self.params = params
        self.device = device
        # Agac onbellegi: (konum_surumu -> GPU dizileri). Agac CPU'da Python'da
        # kuruluyor ve maliyeti ~O(N^1.2) (olculdu: 22.6 ms @ 4k, 187.3 ms @
        # 30k). `step()` icinde `_eval()` IKI kez cagrilir ve ikincisinde
        # KONUMLAR DEGISMEMISTIR (aradaki tek islem bir hiz tekmesidir), yani
        # ikinci agac birebir ayni cikar. Onbellek o kurulumu ve ona eslik
        # eden 9 GPU dizisi tahsisini tamamen ortadan kaldirir; sonuc bit
        # duzeyinde aynidir (ADR-0021).
        self._cache_version: int | None = None
        self._cache_arrays: tuple | None = None

    def compute(self, x_wp, m_wp, g_wp, phi_wp, x_np: np.ndarray, m_np: np.ndarray,
                x_version: int | None = None) -> None:
        n = len(m_wp)
        gp = self.params
        if gp.mode == "direct":
            wp.launch(
                gravity_direct_k, dim=n,
                inputs=[x_wp, m_wp, n, F(gp.G), F(gp.eps * gp.eps)],
                outputs=[g_wp, phi_wp], device=self.device,
            )
            return
        if gp.mode != "barnes_hut":
            raise ValueError(f"bilinmeyen yercekimi modu: {gp.mode!r}")
        dev = self.device
        if x_version is not None and x_version == self._cache_version:
            arrays = self._cache_arrays          # konumlar degismedi: agac ayni
        else:
            from ..cpu_reference.gravity_ref import build_octree

            tree = build_octree(x_np, m_np)
            arrays = (
                wp.array(tree.com, dtype=V3, device=dev),
                wp.array(tree.mass, dtype=F, device=dev),
                wp.array(tree.size, dtype=F, device=dev),
                wp.array(tree.first_child, dtype=wp.int32, device=dev),
                wp.array(tree.next_skip, dtype=wp.int32, device=dev),
                wp.array(tree.leaf_start, dtype=wp.int32, device=dev),
                wp.array(tree.leaf_count, dtype=wp.int32, device=dev),
                wp.array(tree.perm, dtype=wp.int32, device=dev),
            )
            self._cache_version = x_version
            self._cache_arrays = arrays
        wp.launch(
            gravity_bh_k, dim=n,
            inputs=[x_wp, m_wp, *arrays,
                    F(gp.G), F(gp.eps * gp.eps), F(gp.theta)],
            outputs=[g_wp, phi_wp], device=dev,
        )
