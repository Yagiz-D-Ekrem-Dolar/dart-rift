"""GPU hash-grid komsu arama altyapisi (P1-FR-01).

Ana Plan Karar 5: hash-grid ILKELI hazir kullanilir (wp.HashGrid); komsu
dongusu mantigi ve simetri bizim kernel'lerimizdedir.

FP64 notu: wp.HashGrid konumlari float32 ister. Fizik FP64'te kalir; grid
YALNIZCA aday komsu kumesi uretir. Sorgu yaricapi f32 yuvarlama hatasini
ortmek icin PAY'la genisletilir ve gercek q < 2 filtresi kernel icinde FP64
ile yapilir — boylece f32 donusumu hicbir gercek komsuyu kaciramaz (ADR-0007).
"""

from __future__ import annotations

import numpy as np
import warp as wp

F = wp.float64
V3 = wp.vec3d

# f32 sorgu yaricapi payi: |x|<~1e3 olceklerde f32 goreli hatasi ~1e-7;
# 1e-4 goreli + 1e-6 mutlak pay bunu bol bol ortar.
QUERY_PAD_REL = 1.0e-4
QUERY_PAD_ABS = 1.0e-6


@wp.kernel
def _cast_to_f32(x64: wp.array(dtype=V3), x32: wp.array(dtype=wp.vec3)):
    i = wp.tid()
    p = x64[i]
    x32[i] = wp.vec3(wp.float32(p[0]), wp.float32(p[1]), wp.float32(p[2]))


class GridManager:
    """FP64 konumlardan f32 aday-komsu gridi kurar ve yeniden kullanir."""

    def __init__(self, n: int, device: str):
        self.device = device
        dim = int(max(16, min(256, round(n ** (1.0 / 3.0) * 1.5))))
        self.grid = wp.HashGrid(dim, dim, dim, device=device)
        self.x32 = wp.zeros(n, dtype=wp.vec3, device=device)

    def build(self, x64: wp.array, support: float) -> float:
        """Gridi kur; kernel'lerde kullanilacak f32 sorgu yaricapini dondur."""
        n = len(x64)
        wp.launch(_cast_to_f32, dim=n, inputs=[x64], outputs=[self.x32], device=self.device)
        radius32 = float(support * (1.0 + QUERY_PAD_REL) + QUERY_PAD_ABS)
        self.grid.build(points=self.x32, radius=radius32)
        return radius32

    @property
    def id(self):
        return self.grid.id


def brute_force_neighbors(x: np.ndarray, support: float) -> list[set[int]]:
    """Kucuk-N dogrulama: her parcacigin gercek komsu kumesi (kendisi dahil)."""
    x = np.asarray(x, dtype=np.float64)
    n = x.shape[0]
    out: list[set[int]] = []
    for i in range(n):
        d = np.sqrt(np.sum((x - x[i]) ** 2, axis=1))
        out.append(set(np.flatnonzero(d < support).tolist()))
    return out
