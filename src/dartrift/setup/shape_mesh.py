"""PDS sekil mesh hatti: temizleme, yonlendirme, inside/signed-distance (P3-FR-01).

Dis bagimlilik YOK — yalnizca NumPy. Sebep: TRUBA'ya paket kurulamiyor
(ADR-0005) ve mesh islemleri icin gereken sey (kapali ucgen agi uzerinde
hacim, yonlendirme, icerde-mi testi) birkac yuz satirda yazilabiliyor.

TASARIM NOTU — neden isin testi "ray casting + kolon kovalari":
Parcacik doldurma bir KAFES uzerinde yapilir (P3-FR-02), yani sorgu noktalari
duzenli. Bu durumda +z yonunde isin atip kesisim PARITESINE bakmak hem kesin
hem hizlidir. Genellestirilmis sarim sayisi (winding number) daha gurbuzdur
ama O(N*F)'tir ve 2e6 parcacik x 1e5 ucgen olceginde kullanilamaz.

Dogrulama stratejisi: sentetik mesh'lerde (kure, elipsoid) HACIM analitik
olarak bilinir. Icerde-mi testi bozuksa doldurulan hacim tutmaz — yani test
kendi kendini denetler, ayrica bir "mesh dogru mu" iddiasi gerekmez.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

__all__ = [
    "TriMesh",
    "load_obj",
    "clean_mesh",
    "orient_outward",
    "inside_points",
    "signed_distance",
    "icosphere",
    "ellipsoid",
]


@dataclass(frozen=True)
class TriMesh:
    """Kapali ucgen agi. `v` (V,3) koseler, `f` (F,3) ucgen kose indeksleri."""

    v: np.ndarray
    f: np.ndarray

    def __post_init__(self) -> None:
        v = np.asarray(self.v, dtype=np.float64)
        f = np.asarray(self.f, dtype=np.int64)
        if v.ndim != 2 or v.shape[1] != 3:
            raise ValueError(f"koseler (V,3) olmali, {v.shape} geldi")
        if f.ndim != 2 or f.shape[1] != 3:
            raise ValueError(f"yuzler (F,3) olmali, {f.shape} geldi")
        if f.size and (f.min() < 0 or f.max() >= len(v)):
            raise ValueError("yuz indeksi kose dizisinin disinda")
        object.__setattr__(self, "v", v)
        object.__setattr__(self, "f", f)

    # -- temel geometri ----------------------------------------------------
    @property
    def tri(self) -> np.ndarray:
        """(F,3,3) — her ucgenin uc kosesi."""
        return self.v[self.f]

    @property
    def volume(self) -> float:
        """Isaretli hacim (diverjans teoremi). Disa donuk normalde POZITIF.

        V = (1/6) sum_T  a . (b x c)   — kapali ag icin kesin.
        """
        a, b, c = self.tri[:, 0], self.tri[:, 1], self.tri[:, 2]
        return float(np.sum(np.einsum("ij,ij->i", a, np.cross(b, c))) / 6.0)

    @property
    def area(self) -> float:
        a, b, c = self.tri[:, 0], self.tri[:, 1], self.tri[:, 2]
        return float(0.5 * np.sum(np.linalg.norm(np.cross(b - a, c - a), axis=1)))

    @property
    def bounds(self) -> tuple[np.ndarray, np.ndarray]:
        return self.v.min(axis=0), self.v.max(axis=0)

    @property
    def centroid(self) -> np.ndarray:
        """Hacim agirlikli merkez (kutle merkezi, homojen yogunlukta)."""
        a, b, c = self.tri[:, 0], self.tri[:, 1], self.tri[:, 2]
        vol6 = np.einsum("ij,ij->i", a, np.cross(b, c))          # 6*V_tet
        cen = (a + b + c) / 4.0                                   # tetra merkezi
        tot = np.sum(vol6)
        if abs(tot) < 1.0e-300:
            return self.v.mean(axis=0)
        return (vol6 @ cen) / tot

    def is_edge_manifold(self) -> bool:
        """Her kenar TAM iki ucgende gorunmeli (kapali, delik yok).

        Bu kontrol atlanirsa hacim ve icerde-mi testi sessizce yanlis olur:
        delikli bir agda isin sayimi paritesi bozulur.
        """
        e = np.concatenate([self.f[:, [0, 1]], self.f[:, [1, 2]], self.f[:, [2, 0]]])
        e = np.sort(e, axis=1)
        _, counts = np.unique(e, axis=0, return_counts=True)
        return bool(np.all(counts == 2))


# ---------------------------------------------------------------------------
# Yukleme
# ---------------------------------------------------------------------------
def load_obj(path) -> TriMesh:
    """Wavefront OBJ oku (PDS sekil modelleri bu bicimde dagitilir).

    Yalnizca `v` ve `f` satirlari okunur; normaller/dokular yok sayilir
    (yonlendirme zaten `orient_outward` ile hacim isaretinden belirlenir).
    Poligon yuzler ucgen yelpazeye bolunur.
    """
    verts: list[tuple[float, float, float]] = []
    faces: list[tuple[int, int, int]] = []
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if line.startswith("v "):
                p = line.split()
                verts.append((float(p[1]), float(p[2]), float(p[3])))
            elif line.startswith("f "):
                # "f 1/2/3 4//5 6" gibi bicimlerde ilk alan kose indeksidir
                idx = [int(tok.split("/")[0]) for tok in line.split()[1:]]
                # OBJ 1-tabanli; negatif indeks sondan sayar
                idx = [i - 1 if i > 0 else len(verts) + i for i in idx]
                for k in range(1, len(idx) - 1):       # ucgen yelpaze
                    faces.append((idx[0], idx[k], idx[k + 1]))
    return TriMesh(np.array(verts, dtype=np.float64),
                   np.array(faces, dtype=np.int64).reshape(-1, 3))


# ---------------------------------------------------------------------------
# Temizleme ve yonlendirme
# ---------------------------------------------------------------------------
def clean_mesh(mesh: TriMesh, weld_tol: float = 0.0) -> TriMesh:
    """Yinelenen kose, dejenere yuz ve kullanilmayan koseleri temizle.

    `weld_tol > 0` ise koseler o tolerans kadar yuvarlanarak kaynatilir; PDS
    mesh'lerinde ayni nokta farkli yuzlerde mikro-farkla gorunebiliyor ve bu,
    kenar-manifoldlugu sahte olarak bozuyor.
    """
    v, f = mesh.v, mesh.f
    if weld_tol > 0.0:
        key = np.round(v / weld_tol).astype(np.int64)
        _, first, inv = np.unique(key, axis=0, return_index=True, return_inverse=True)
        v = v[first]
        f = inv[f]
    # dejenere: ayni koseyi iki kez kullanan ucgenler
    ok = (f[:, 0] != f[:, 1]) & (f[:, 1] != f[:, 2]) & (f[:, 2] != f[:, 0])
    f = f[ok]
    # sifir alanli ucgenler
    tri = v[f]
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    f = f[np.linalg.norm(n, axis=1) > 0.0]
    # kullanilmayan koseler
    used, f = np.unique(f, return_inverse=True)
    return TriMesh(v[used], f.reshape(-1, 3))


def orient_outward(mesh: TriMesh) -> TriMesh:
    """Normaller disa donuk olacak sekilde yonlendir (hacim > 0).

    Not: bu, TUM ucgenlerin tutarli yonlendirildigini VARSAYAR ve yalnizca
    global isareti duzeltir. Tutarsiz bir agda hacim zaten anlamsizdir; onu
    `is_edge_manifold` + hacim kontrolu yakalar.
    """
    return mesh if mesh.volume >= 0.0 else TriMesh(mesh.v, mesh.f[:, ::-1])


# ---------------------------------------------------------------------------
# Icerde-mi testi
# ---------------------------------------------------------------------------
def inside_points(mesh: TriMesh, pts: np.ndarray, cells: int = 64) -> np.ndarray:
    """`pts` (N,3) noktalarindan hangileri mesh'in ICINDE? -> (N,) bool.

    Yontem: her noktadan +z yonunde isin atilir, kesilen ucgen sayisinin
    PARITESI alinir (tek = icerde). Hizlandirma: ucgenler xy duzleminde
    duzgun bir `cells x cells` kafese, sinir kutularina gore dagitilir; her
    nokta yalnizca kendi hucresindeki ucgenlere karsi sinanir.

    SINIR DURUMU — neden "top-left" kurali sart:
    Isin tam bir kenardan ya da koseden gecerse, o kenari/koseyi paylasan
    ucgenlerin HEPSI kesisim sayar ve parite bozulur. Bu teorik bir kaygi
    degil: ikosferi bolunce (0,0,r) noktasinda bir kose olusur ve merkezden
    atilan +z isini tam oradan gecer; 6 ucgen birden sayilip nokta DISARIDA
    sanilir (test bunu yakaladi).

    Cozum, rasterlestirmeden bilinen YARI-ACIK kenar kurali: kenar
    fonksiyonu sifirsa, kesisim yalnizca kenar "ust ya da sol" ise sayilir.
    Iki komsu ucgen ortak kenari TERS yonde dolastigi icin, bu kural o
    kenari ikisinden TAM BIRINE verir — parite korunur.
    """
    pts = np.asarray(pts, dtype=np.float64)
    if pts.ndim != 2 or pts.shape[1] != 3:
        raise ValueError(f"noktalar (N,3) olmali, {pts.shape} geldi")
    n_pts = len(pts)
    if n_pts == 0:
        return np.zeros(0, dtype=bool)

    tri = mesh.tri                                    # (F,3,3)
    lo, hi = mesh.bounds
    span = np.maximum(hi[:2] - lo[:2], 1.0e-300)
    inv = cells / span

    def _cell(xy: np.ndarray) -> np.ndarray:
        c = np.floor((xy - lo[:2]) * inv).astype(np.int64)
        return np.clip(c, 0, cells - 1)

    # --- ucgenleri hucrelere dagit ---
    t_lo = _cell(tri[:, :, :2].min(axis=1))
    t_hi = _cell(tri[:, :, :2].max(axis=1))
    bucket: dict[int, list[int]] = {}
    for t in range(len(tri)):
        for cx in range(t_lo[t, 0], t_hi[t, 0] + 1):
            for cy in range(t_lo[t, 1], t_hi[t, 1] + 1):
                bucket.setdefault(cx * cells + cy, []).append(t)

    # --- noktalari hucrelere gore grupla ---
    p_cell = _cell(pts[:, :2])
    key = p_cell[:, 0] * cells + p_cell[:, 1]
    order = np.argsort(key, kind="stable")
    out = np.zeros(n_pts, dtype=bool)

    a_all, b_all, c_all = tri[:, 0], tri[:, 1], tri[:, 2]
    start = 0
    ks = key[order]
    while start < n_pts:
        stop = start + int(np.searchsorted(ks[start:], ks[start], side="right"))
        idx = order[start:stop]
        tl = bucket.get(int(ks[start]))
        if tl:
            t = np.asarray(tl, dtype=np.int64)
            a, b, c = a_all[t], b_all[t], c_all[t]      # (T,3)
            p = pts[idx]                                # (P,3)
            hit = _covers_xy(a, b, c, p)                # (P,T) yari-acik kapsama
            lam = _bary_xy(a, b, c, p)                  # (P,T,3)
            z_hit = (lam[..., 0] * a[None, :, 2] + lam[..., 1] * b[None, :, 2]
                     + lam[..., 2] * c[None, :, 2])
            crossing = hit & (z_hit > p[:, None, 2])
            out[idx] = (np.count_nonzero(crossing, axis=1) % 2) == 1
        start = stop
    return out


def _edge_fn(v0: np.ndarray, v1: np.ndarray, p: np.ndarray) -> np.ndarray:
    """2B kenar fonksiyonu: (v1-v0) x (p-v0). Isaret, p'nin hangi yanda oldugu."""
    return ((v1[None, :, 0] - v0[None, :, 0]) * (p[:, None, 1] - v0[None, :, 1])
            - (v1[None, :, 1] - v0[None, :, 1]) * (p[:, None, 0] - v0[None, :, 0]))


def _top_left(v0: np.ndarray, v1: np.ndarray) -> np.ndarray:
    """Kenar "ust ya da sol" mu? (yari-acik kapsama kurali, (1,T))

    Iki komsu ucgen ortak kenari TERS yonde dolasir; bu yuzden bu bayrak
    tam birinde True olur ve kenar ustundeki nokta BIR kez sayilir.
    """
    dy = v1[:, 1] - v0[:, 1]
    dx = v1[:, 0] - v0[:, 0]
    return ((dy > 0.0) | ((dy == 0.0) & (dx < 0.0)))[None, :]


def _covers_xy(a: np.ndarray, b: np.ndarray, c: np.ndarray,
               p: np.ndarray) -> np.ndarray:
    """xy izdusumunde ucgen noktayi kapsiyor mu? (P,T), YARI-ACIK."""
    w0 = _edge_fn(a, b, p)                 # c'nin karsisindaki kenar
    w1 = _edge_fn(b, c, p)                 # a'nin karsisindaki
    w2 = _edge_fn(c, a, p)                 # b'nin karsisindaki
    area2 = w0 + w1 + w2                   # p'den bagimsiz: 2 * isaretli alan
    flip = area2 < 0.0                     # CW ucgeni CCW'ye cevir
    w0 = np.where(flip, -w0, w0)
    w1 = np.where(flip, -w1, w1)
    w2 = np.where(flip, -w2, w2)
    tl0, tl1, tl2 = _top_left(a, b), _top_left(b, c), _top_left(c, a)
    # CW ucgende kenar yonu de terslenir -> top-left bayragi da terslenir
    tl0 = np.where(flip, ~tl0, tl0)
    tl1 = np.where(flip, ~tl1, tl1)
    tl2 = np.where(flip, ~tl2, tl2)
    ok0 = (w0 > 0.0) | ((w0 == 0.0) & tl0)
    ok1 = (w1 > 0.0) | ((w1 == 0.0) & tl1)
    ok2 = (w2 > 0.0) | ((w2 == 0.0) & tl2)
    return ok0 & ok1 & ok2 & (area2 != 0.0)   # dejenere izdusum sayilmaz


def _bary_xy(a: np.ndarray, b: np.ndarray, c: np.ndarray,
             p: np.ndarray) -> np.ndarray:
    """xy izdusumunde barycentric agirliklar (P,T,3) — z ara degeri icin."""
    w0 = _edge_fn(a, b, p)
    w1 = _edge_fn(b, c, p)
    w2 = _edge_fn(c, a, p)
    area2 = w0 + w1 + w2
    safe = np.where(area2 != 0.0, area2, 1.0)
    return np.stack([w1 / safe, w2 / safe, w0 / safe], axis=-1)


def signed_distance(mesh: TriMesh, pts: np.ndarray) -> np.ndarray:
    """Isaretli mesafe: icerde NEGATIF, disarida POZITIF.

    Kaba kuvvet O(N*F) — yalnizca KUCUK sorgular icindir (yuzey metrikleri,
    krater derinligi). Parcacik doldurma icin `inside_points` kullanilir.
    """
    pts = np.asarray(pts, dtype=np.float64)
    tri = mesh.tri
    a, b, c = tri[:, 0], tri[:, 1], tri[:, 2]
    d = np.empty(len(pts))
    for i, p in enumerate(pts):
        d[i] = np.sqrt(np.min(_point_tri_dist2(p, a, b, c)))
    return np.where(inside_points(mesh, pts), -d, d)


def _point_tri_dist2(p: np.ndarray, a: np.ndarray, b: np.ndarray,
                     c: np.ndarray) -> np.ndarray:
    """Noktanin her ucgene KARE mesafesi (Ericson, Real-Time Collision Det.)."""
    ab, ac, ap = b - a, c - a, p - a
    d1 = np.einsum("ij,ij->i", ab, ap)
    d2 = np.einsum("ij,ij->i", ac, ap)
    bp = p - b
    d3 = np.einsum("ij,ij->i", ab, bp)
    d4 = np.einsum("ij,ij->i", ac, bp)
    cp = p - c
    d5 = np.einsum("ij,ij->i", ab, cp)
    d6 = np.einsum("ij,ij->i", ac, cp)
    va = d3 * d6 - d5 * d4
    vb = d5 * d2 - d1 * d6
    vc = d1 * d4 - d3 * d2
    den = va + vb + vc
    with np.errstate(invalid="ignore", divide="ignore"):
        v = np.where(den != 0.0, vb / den, 0.0)
        w = np.where(den != 0.0, vc / den, 0.0)
    q = a + v[:, None] * ab + w[:, None] * ac          # yuz ici izdusum
    # kenar/kose bolgeleri
    q = np.where(((d1 <= 0) & (d2 <= 0))[:, None], a, q)
    q = np.where(((d3 >= 0) & (d4 <= d3))[:, None], b, q)
    q = np.where(((d6 >= 0) & (d5 <= d6))[:, None], c, q)
    t_ab = np.clip(np.where(d1 != d3, d1 / np.where(d1 != d3, d1 - d3, 1.0), 0.0), 0, 1)
    q = np.where(((vc <= 0) & (d1 >= 0) & (d3 <= 0))[:, None], a + t_ab[:, None] * ab, q)
    t_ac = np.clip(np.where(d2 != d6, d2 / np.where(d2 != d6, d2 - d6, 1.0), 0.0), 0, 1)
    q = np.where(((vb <= 0) & (d2 >= 0) & (d6 <= 0))[:, None], a + t_ac[:, None] * ac, q)
    bc_den = (d4 - d3) + (d5 - d6)
    t_bc = np.clip(np.where(bc_den != 0.0, (d4 - d3) / np.where(bc_den != 0.0, bc_den, 1.0),
                            0.0), 0, 1)
    q = np.where(((va <= 0) & ((d4 - d3) >= 0) & ((d5 - d6) >= 0))[:, None],
                 b + t_bc[:, None] * (c - b), q)
    dq = p - q
    return np.einsum("ij,ij->i", dq, dq)


# ---------------------------------------------------------------------------
# Sentetik mesh'ler — testler ve motor gelistirme icin
# ---------------------------------------------------------------------------
def icosphere(subdiv: int = 2, radius: float = 1.0) -> TriMesh:
    """Ikosahedron bolunmesiyle kure. Hacim analitik: (4/3) pi r^3'e yakinsar."""
    t = (1.0 + 5.0**0.5) / 2.0
    v = np.array([
        [-1, t, 0], [1, t, 0], [-1, -t, 0], [1, -t, 0],
        [0, -1, t], [0, 1, t], [0, -1, -t], [0, 1, -t],
        [t, 0, -1], [t, 0, 1], [-t, 0, -1], [-t, 0, 1],
    ], dtype=np.float64)
    f = np.array([
        [0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11],
        [1, 5, 9], [5, 11, 4], [11, 10, 2], [10, 7, 6], [7, 1, 8],
        [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9],
        [4, 9, 5], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1],
    ], dtype=np.int64)
    for _ in range(subdiv):
        v, f = _subdivide(v, f)
    v = radius * v / np.linalg.norm(v, axis=1, keepdims=True)
    return orient_outward(TriMesh(v, f))


def _subdivide(v: np.ndarray, f: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Her ucgeni kenar orta noktalarindan dorde bol (1-4 bolunme).

    Orta noktalar KOMSU ucgenler arasinda PAYLASILIR (mid sozlugu); yoksa ag
    yirtilir ve kenar-manifoldlugu bozulur.
    """
    mid: dict[tuple[int, int], int] = {}
    vl = list(v)
    nf: list[list[int]] = []

    def _mid(i: int, j: int) -> int:
        k = (min(i, j), max(i, j))
        if k not in mid:
            mid[k] = len(vl)
            vl.append((vl[i] + vl[j]) / 2.0)
        return mid[k]

    for i0, i1, i2 in f:
        a, b, c = _mid(i0, i1), _mid(i1, i2), _mid(i2, i0)
        nf += [[i0, a, c], [i1, b, a], [i2, c, b], [a, b, c]]
    return np.array(vl, dtype=np.float64), np.array(nf, dtype=np.int64)


def ellipsoid(a: float, b: float, c: float, subdiv: int = 3) -> TriMesh:
    """Elipsoid. Hacim analitik: (4/3) pi a b c."""
    s = icosphere(subdiv, 1.0)
    return orient_outward(TriMesh(s.v * np.array([a, b, c]), s.f))
