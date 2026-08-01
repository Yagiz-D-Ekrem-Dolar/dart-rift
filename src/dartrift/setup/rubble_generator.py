"""Moloz-yigini ureticisi: doldurma, iri-blok, malzeme alani (P3-FR-02/03/04).

Uc is yapar:

1. **Doldurma** — mesh'in icini SPH parcaciklariyla doldurur. Varsayilan
   yerlesim FCC (yuzey merkezli kubik): SPH'de kubik kafese gore daha duzgun
   komsu dagilimi verir ve baslangicta yapay gerilme uretmez. Parcacik basina
   hacim FCC icin KESIN olarak `s^3/sqrt(2)`'dir (s = en yakin komsu araligi);
   kutleler bundan turetilir, boylece toplam kutle hedef yogunlugu verir.

2. **Iri-bloklar (M1)** — boyut dagilimi power-law ornekelenir, cakismalar
   cozulur, hacim orani GERI OLCULUR. "Orneklendi" demek yetmez; sartname
   P3-FR-03 acikca geri-olcum testi istiyor.

3. **Malzeme alani** — M0 (homojen) ve M1 (matris + gomulu bloklar) icin
   parcacik basina yogunluk/gozeneklilik/dayanim atanir.

DETERMINIZM: tum rasgelelik `dartrift.rng`'nin adlandirilmis akislarindan
gelir (ADR-0004). Ayni kok tohum -> ayni yigin, shard sayisindan bagimsiz.
Bu, ensemble cikariminin on kosuludur (FAZ 5): iki kosu arasindaki fark
yalnizca parametreden gelebilir.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..rng import stream_generator
from .shape_mesh import TriMesh, inside_points

__all__ = [
    "FCC_VOLUME_FACTOR",
    "RubblePile",
    "BoulderField",
    "fill_particles",
    "sample_boulder_radii",
    "place_boulders",
    "assign_material",
    "build_rubble_pile",
]

# FCC yerlesiminde parcacik basina hacim = s^3 / sqrt(2).
# Turetme: FCC kafes sabiti a, en yakin komsu araligi s = a/sqrt(2), hucre
# basina 4 parcacik -> V_p = a^3/4 = (s*sqrt(2))^3/4 = s^3/sqrt(2).
FCC_VOLUME_FACTOR = 1.0 / np.sqrt(2.0)


@dataclass(frozen=True)
class BoulderField:
    """Iri-blok kumesi: merkezler (B,3) ve yaricaplar (B,)."""

    centers: np.ndarray
    radii: np.ndarray

    @property
    def volume(self) -> float:
        return float(np.sum(4.0 / 3.0 * np.pi * self.radii**3))


@dataclass(frozen=True)
class RubblePile:
    """Uretilmis yigin: konum, kutle, malzeme alanlari ve tani sayilari."""

    x: np.ndarray                 # (N,3)
    m: np.ndarray                 # (N,)
    alpha0: np.ndarray            # (N,) baslangic distansiyonu (gozeneklilik)
    Y0: np.ndarray                # (N,) kohezyon [Pa]
    is_boulder: np.ndarray        # (N,) bool
    spacing: float
    mesh_volume: float
    boulders: BoulderField | None
    diagnostics: dict

    @property
    def n(self) -> int:
        return len(self.m)

    @property
    def bulk_density(self) -> float:
        """Toplam kutle / mesh hacmi — hedef yigin yogunlugunu vermeli."""
        return float(np.sum(self.m) / self.mesh_volume)

    @property
    def boulder_volume_fraction(self) -> float:
        """GERI OLCUM: blok etiketli parcaciklarin hacim orani (P3-FR-03)."""
        return float(np.count_nonzero(self.is_boulder) / max(self.n, 1))


# ---------------------------------------------------------------------------
# 1) Doldurma
# ---------------------------------------------------------------------------
def fill_particles(mesh: TriMesh, spacing: float, packing: str = "fcc",
                   cells: int = 64) -> np.ndarray:
    """Mesh'in icini `spacing` araligiyla doldur -> (N,3).

    `packing`:
      "fcc"   — yuzey merkezli kubik (varsayilan, SPH icin duzgun komsuluk)
      "cubic" — basit kubik (yalnizca karsilastirma/tani icin)

    Kafes, mesh sinir kutusundan yarim hucre KAYDIRILARAK kurulur: boylece
    kafes noktalari mesh koseleriyle cakismaz ve isin-atma testi dejenere
    duruma girmez (bkz. shape_mesh.inside_points).
    """
    if spacing <= 0.0:
        raise ValueError(f"aralik pozitif olmali, {spacing} geldi")
    lo, hi = mesh.bounds
    pad = spacing
    lo = lo - pad
    hi = hi + pad

    if packing == "cubic":
        axes = [np.arange(lo[k] + 0.5 * spacing, hi[k], spacing) for k in range(3)]
        pts = np.stack(np.meshgrid(*axes, indexing="ij"), -1).reshape(-1, 3)
    elif packing == "fcc":
        a = spacing * np.sqrt(2.0)                 # kafes sabiti
        basis = np.array([[0.0, 0.0, 0.0], [0.5, 0.5, 0.0],
                          [0.5, 0.0, 0.5], [0.0, 0.5, 0.5]]) * a
        n = np.ceil((hi - lo) / a).astype(int) + 1
        gi = [np.arange(n[k]) * a + lo[k] + 0.25 * a for k in range(3)]
        cell = np.stack(np.meshgrid(*gi, indexing="ij"), -1).reshape(-1, 3)
        pts = (cell[:, None, :] + basis[None, :, :]).reshape(-1, 3)
        pts = pts[np.all((pts >= lo) & (pts <= hi), axis=1)]
    else:
        raise ValueError(f"bilinmeyen yerlesim: {packing!r}")

    return pts[inside_points(mesh, pts, cells=cells)]


def particle_volume(spacing: float, packing: str = "fcc") -> float:
    """Parcacik basina hacim — kutle atamasinin temeli."""
    if packing == "fcc":
        return FCC_VOLUME_FACTOR * spacing**3
    if packing == "cubic":
        return spacing**3
    raise ValueError(f"bilinmeyen yerlesim: {packing!r}")


# ---------------------------------------------------------------------------
# 2) Iri-bloklar
# ---------------------------------------------------------------------------
def sample_boulder_radii(rng: np.random.Generator, n: int, r_min: float,
                         r_max: float, q: float) -> np.ndarray:
    """Power-law yaricap ornekleme: dN/dr ~ r^(-q), [r_min, r_max].

    Ters donusum: u ~ U(0,1) icin
        q != 1 : r = [ r_min^(1-q) + u (r_max^(1-q) - r_min^(1-q)) ]^(1/(1-q))
        q == 1 : r = r_min (r_max/r_min)^u
    """
    if not (0.0 < r_min < r_max):
        raise ValueError(f"0 < r_min < r_max gerekli: {r_min}, {r_max}")
    u = rng.random(n)
    if abs(q - 1.0) < 1.0e-12:
        return r_min * (r_max / r_min) ** u
    p = 1.0 - q
    return (r_min**p + u * (r_max**p - r_min**p)) ** (1.0 / p)


def place_boulders(mesh: TriMesh, f_boulder: float, q: float,
                   r_min: float, r_max: float, root_seed: int,
                   max_tries: int = 20000) -> BoulderField:
    """Hedef hacim oranina ulasana kadar cakismasiz blok yerlestir.

    Iki kabul sarti var:

    1. **Blok TAMAMEN mesh icinde olmali.** Yalnizca merkezi sinamak yetmez:
       olculdugunde bloklarin yarisindan cogu yuzeyden TASIYORDU (44 bloktan
       26'si) ve tasan kisimda parcacik olmadigi icin geri-olculen hacim
       orani sistematik olarak DUSUK cikiyordu (hedef 0.30 -> olculen 0.249).
       Kure uzerinde 14 nokta (6 eksen + 8 kosegen) sinanir.
    2. **Cakisma yok:** merkezler arasi mesafe >= r_i + r_j.

    Adaylar TOPLU uretilir ve tek `inside_points` cagrisiyla sinanir; tek tek
    sorgu, her cagrida ucgen kovalarini yeniden kurdugu icin cok yavasti.

    Hedefe ulasilamazsa SESSIZCE gecistirilmez: `saturated` bayragi ve
    yerlesen hacim dondurulur, cagiran taraf gorur.
    """
    if not (0.0 <= f_boulder < 1.0):
        raise ValueError(f"f_boulder [0,1) araliginda olmali, {f_boulder} geldi")
    rng = stream_generator(root_seed, "material")
    v_target = f_boulder * mesh.volume
    if v_target <= 0.0:
        return BoulderField(np.zeros((0, 3)), np.zeros(0))

    # kure uzerinde ornek yonler: 6 eksen + 8 kosegen (normalize)
    d1 = np.eye(3)
    dirs = np.vstack([d1, -d1, np.array(np.meshgrid([-1, 1], [-1, 1], [-1, 1]))
                      .T.reshape(-1, 3) / np.sqrt(3.0)])

    lo, hi = mesh.bounds
    centers: list[np.ndarray] = []
    radii: list[float] = []
    v_acc = 0.0
    batch = 512
    tries = 0
    while v_acc < v_target and tries < max_tries:
        n_b = min(batch, max_tries - tries)
        tries += n_b
        r_c = sample_boulder_radii(rng, n_b, r_min, r_max, q)
        c_c = lo + rng.random((n_b, 3)) * (hi - lo)
        # 14 yuzey noktasi + merkez, TEK sorguda
        probe = (c_c[:, None, :] + r_c[:, None, None] * dirs[None, :, :])
        flat = np.vstack([c_c, probe.reshape(-1, 3)])
        ins = inside_points(mesh, flat)
        ok = ins[:n_b] & ins[n_b:].reshape(n_b, len(dirs)).all(axis=1)
        for k in np.flatnonzero(ok):
            if v_acc >= v_target:
                break
            c, r = c_c[k], float(r_c[k])
            if centers:
                d = np.linalg.norm(np.asarray(centers) - c, axis=1)
                if np.any(d < np.asarray(radii) + r):
                    continue
            centers.append(c)
            radii.append(r)
            v_acc += 4.0 / 3.0 * np.pi * r**3
    return BoulderField(np.asarray(centers).reshape(-1, 3),
                        np.asarray(radii, dtype=np.float64))


# ---------------------------------------------------------------------------
# 3) Malzeme alani
# ---------------------------------------------------------------------------
def assign_material(x: np.ndarray, boulders: BoulderField | None,
                    matrix_alpha0: float, matrix_Y0: float,
                    boulder_alpha0: float, boulder_Y0: float
                    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Parcacik basina (alpha0, Y0, is_boulder) ata.

    M0 (homojen): `boulders=None` -> hepsi matris.
    M1 (iri-bloklu): blok icindeki parcaciklar daha DUSUK gozeneklilik
    (alpha0 kucuk) ve daha YUKSEK kohezyon alir — fiziksel olarak "matris
    icine gomulu saglam kaya".
    """
    n = len(x)
    is_b = np.zeros(n, dtype=bool)
    if boulders is not None and len(boulders.radii):
        for c, r in zip(boulders.centers, boulders.radii, strict=True):
            is_b |= np.sum((x - c) ** 2, axis=1) < r * r
    alpha0 = np.where(is_b, boulder_alpha0, matrix_alpha0)
    y0 = np.where(is_b, boulder_Y0, matrix_Y0)
    return alpha0, y0, is_b


# ---------------------------------------------------------------------------
# Ust duzey: tam yigin
# ---------------------------------------------------------------------------
def build_rubble_pile(
    mesh: TriMesh,
    spacing: float,
    bulk_density: float,
    root_seed: int,
    model_class: str = "M0",
    matrix_alpha0: float = 1.6,
    matrix_Y0: float = 1.0e4,
    boulder_alpha0: float = 1.05,
    boulder_Y0: float = 1.0e7,
    f_boulder: float = 0.0,
    q: float = 3.0,
    r_min: float | None = None,
    r_max: float | None = None,
    packing: str = "fcc",
) -> RubblePile:
    """Mesh'ten tam bir moloz yigini uret (P3-FR-02/03/04).

    `bulk_density` YIGIN yogunlugudur (gozenekler dahil). Parcacik kutlesi
    `rho_bulk * V_p` ile atanir; boylece toplam kutle mesh hacmi carpi hedef
    yogunluga esittir — testte geri olculur.

    `model_class`:
      "M0" homojen — tek malzeme.
      "M1" iri-bloklu — matris + power-law bloklar (f_boulder, q gerekli).
    """
    if model_class not in ("M0", "M1"):
        raise ValueError(f"desteklenmeyen sinif: {model_class!r} (M0|M1)")
    x = fill_particles(mesh, spacing, packing=packing)
    v_p = particle_volume(spacing, packing)
    m = np.full(len(x), bulk_density * v_p)

    boulders = None
    if model_class == "M1":
        if f_boulder <= 0.0:
            raise ValueError("M1 sinifi f_boulder > 0 gerektirir")
        rmin = r_min if r_min is not None else 2.0 * spacing
        rmax = r_max if r_max is not None else 8.0 * spacing
        boulders = place_boulders(mesh, f_boulder, q, rmin, rmax, root_seed)

    alpha0, y0, is_b = assign_material(
        x, boulders, matrix_alpha0, matrix_Y0, boulder_alpha0, boulder_Y0)

    diag = {
        "n_particles": int(len(x)),
        "particle_volume": float(v_p),
        "fill_volume": float(len(x) * v_p),
        "mesh_volume": float(mesh.volume),
        "fill_ratio": float(len(x) * v_p / mesh.volume) if mesh.volume else 0.0,
        "n_boulders": int(len(boulders.radii)) if boulders is not None else 0,
        "boulder_volume_target": float(f_boulder * mesh.volume),
        "boulder_volume_placed": float(boulders.volume) if boulders is not None else 0.0,
        "boulder_fraction_measured": float(np.count_nonzero(is_b) / max(len(x), 1)),
        "model_class": model_class,
    }
    # Doyma SESSIZ kalmamali: hedefe ulasilamadiysa cagiran taraf gormeli.
    v_t = diag["boulder_volume_target"]
    diag["boulder_saturated"] = bool(v_t > 0.0 and diag["boulder_volume_placed"] < 0.9 * v_t)
    return RubblePile(x=x, m=m, alpha0=alpha0, Y0=y0, is_boulder=is_b,
                      spacing=spacing, mesh_volume=float(mesh.volume),
                      boulders=boulders, diagnostics=diag)


def coordination_number(x: np.ndarray, spacing: float,
                        tol: float = 1.15) -> np.ndarray:
    """Her parcacigin `tol*spacing` icindeki komsu sayisi (tani).

    FCC'de ic bolgede 12 beklenir; yuzeyde daha az. Sartname P3-FR-02'nin
    "koordinasyon sayisi makul" kabulu bununla olculur.
    """
    from collections import defaultdict

    r = tol * spacing
    n = len(x)
    out = np.zeros(n, dtype=np.int32)
    # kova tabanli sayim: O(N * hucre_yogunlugu), kaba kuvvet O(N^2) degil
    cell = np.floor(x / r).astype(np.int64)
    buckets: dict[tuple[int, int, int], list[int]] = defaultdict(list)
    for i, c in enumerate(map(tuple, cell)):
        buckets[c].append(i)
    r2 = r * r
    for i in range(n):
        cx, cy, cz = cell[i]
        cnt = 0
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for j in buckets.get((cx + dx, cy + dy, cz + dz), ()):
                        if j != i and np.sum((x[i] - x[j]) ** 2) < r2:
                            cnt += 1
        out[i] = cnt
    return out
