"""Oz-yercekimi referanslari: dogrudan N^2 + Barnes-Hut halat-agaci (P2 §2.5).

Agac CPU'da deterministik kurulur (sabit oktant sirasi, DFS yerlesimi) ve
"halat" (rope) dizileriyle duzlestirilir: her dugumun `first_child` (ac) ve
`next_skip` (atla) indeksi vardir. Boylece gezinme YIGITSIZDIR — ayni diziler
GPU kernel'inde de birebir kullanilir (warp_core/gravity_tree.py).

Aciklik kriteri: node_size / dist < theta  =>  monopol kullan.
Yumusatma: Plummer, (r^2 + eps^2)^(1/2).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .solid_ref import compute_gravity_direct  # dogrudan N^2 (referans)

__all__ = ["compute_gravity_direct", "RopeTree", "build_octree", "bh_accel"]

_LEAF_SIZE = 8


@dataclass
class RopeTree:
    """Duzlestirilmis oktree (DFS sirali, halatli)."""

    com: np.ndarray  # (M,3) kutle merkezi
    mass: np.ndarray  # (M,)
    size: np.ndarray  # (M,) dugum kenar uzunlugu
    first_child: np.ndarray  # (M,) ic dugumde ilk cocuk, yaprakta -1
    next_skip: np.ndarray  # (M,) atlama halati (-1 = bitti)
    leaf_start: np.ndarray  # (M,) yaprakta perm dilim baslangici
    leaf_count: np.ndarray  # (M,) yaprakta parcacik sayisi
    perm: np.ndarray  # (N,) yaprak dilimlerinin parcacik indeksleri

    @property
    def n_nodes(self) -> int:
        return len(self.mass)


def build_octree(x: np.ndarray, m: np.ndarray, leaf_size: int = _LEAF_SIZE) -> RopeTree:
    """Deterministik oktree: sabit oktant sirasi, DFS + halat kurulumu."""
    x = np.asarray(x, dtype=np.float64)
    m = np.asarray(m, dtype=np.float64)
    n = x.shape[0]
    lo = x.min(axis=0)
    hi = x.max(axis=0)
    center0 = 0.5 * (lo + hi)
    size0 = float(np.max(hi - lo)) * 1.0000001 + 1.0e-300

    com_l: list[np.ndarray] = []
    mass_l: list[float] = []
    size_l: list[float] = []
    first_l: list[int] = []
    end_l: list[int] = []  # alt-agacin DFS bitis indeksi
    lstart_l: list[int] = []
    lcount_l: list[int] = []
    perm_out: list[int] = []

    def rec(idx: np.ndarray, center: np.ndarray, size: float) -> int:
        """Dugumu tahsis et; DFS yerlesiminde alt-agac [node, end) araligidir."""
        node = len(mass_l)
        msum = float(np.sum(m[idx]))
        cm = (m[idx] @ x[idx]) / msum
        com_l.append(cm)
        mass_l.append(msum)
        size_l.append(size)
        first_l.append(-1)
        end_l.append(-1)
        lstart_l.append(-1)
        lcount_l.append(0)
        if len(idx) <= leaf_size:
            lstart_l[node] = len(perm_out)
            lcount_l[node] = len(idx)
            perm_out.extend(int(i) for i in idx)
        else:
            # sabit oktant sirasi (0..7): deterministik DFS
            rel = x[idx] >= center[None, :]
            octant = (
                rel[:, 0].astype(int) * 4 + rel[:, 1].astype(int) * 2 + rel[:, 2].astype(int)
            )
            half = 0.5 * size
            for o in range(8):
                sel = idx[octant == o]
                if sel.size == 0:
                    continue
                off = np.array(
                    [half * (0.5 if (o >> 2) & 1 else -0.5),
                     half * (0.5 if (o >> 1) & 1 else -0.5),
                     half * (0.5 if o & 1 else -0.5)]
                )
                child = rec(sel, center + off, half)
                if first_l[node] < 0:
                    first_l[node] = child
        end_l[node] = len(mass_l)  # tum cocuklar tahsis edildi -> alt-agac sonu
        return node

    import sys as _sys

    old_limit = _sys.getrecursionlimit()
    _sys.setrecursionlimit(max(old_limit, 10 * int(np.log2(n + 2)) * 8 + 10_000))
    try:
        rec(np.arange(n), center0, size0)
    finally:
        _sys.setrecursionlimit(old_limit)

    m_nodes = len(mass_l)
    first = np.array(first_l, dtype=np.int32)
    ends = np.array(end_l, dtype=np.int32)
    skip = np.where(ends < m_nodes, ends, -1).astype(np.int32)

    return RopeTree(
        com=np.array(com_l),
        mass=np.array(mass_l),
        size=np.array(size_l),
        first_child=first,
        next_skip=skip,
        leaf_start=np.array(lstart_l, dtype=np.int32),
        leaf_count=np.array(lcount_l, dtype=np.int32),
        perm=np.array(perm_out, dtype=np.int32),
    )


def bh_accel(
    targets: np.ndarray,
    target_idx: np.ndarray | None,
    tree: RopeTree,
    x: np.ndarray,
    m: np.ndarray,
    G: float,
    eps: float,
    theta: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Halat-agaci gezinmesiyle Barnes-Hut ivme + potansiyel (CPU referans).

    target_idx verilirse yaprak dongusunde oz-etkilesim (i==j) atlanir.
    """
    targets = np.asarray(targets, dtype=np.float64)
    nt = targets.shape[0]
    g = np.zeros((nt, 3))
    phi = np.zeros(nt)
    eps2 = eps * eps
    for t in range(nt):
        p = targets[t]
        self_i = -1 if target_idx is None else int(target_idx[t])
        node = 0
        while node != -1:
            d = tree.com[node] - p
            dist2 = d @ d + eps2
            dist = np.sqrt(dist2)
            if tree.first_child[node] < 0:  # yaprak: parcaciklari dogrudan topla
                s0 = tree.leaf_start[node]
                for k in range(tree.leaf_count[node]):
                    j = int(tree.perm[s0 + k])
                    if j == self_i:
                        continue
                    dj = x[j] - p
                    r2 = dj @ dj + eps2
                    inv = 1.0 / np.sqrt(r2)
                    g[t] += G * m[j] * dj * inv / r2
                    phi[t] -= G * m[j] * inv
                node = tree.next_skip[node]
            elif tree.size[node] / dist < theta:  # yeterince uzak: monopol
                g[t] += G * tree.mass[node] * d / (dist2 * dist)
                phi[t] -= G * tree.mass[node] / dist
                node = tree.next_skip[node]
            else:  # ac
                node = tree.first_child[node]
    return g, phi
