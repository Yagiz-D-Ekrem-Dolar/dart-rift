"""C-2 — örtüşmeli eşleme momentumu koruyor mu?

## Neden bu, C'nin **asıl** riski

A ve A′ momentumu **tam** korur (ölçülen `< 1e-12`, KAYIT-020 §1 ve
KAYIT-024 §1), çünkü SPH'in simetrik kuvvet biçimi antisimetriktir:
`f_ij = −f_ji`. Her etkinin tepkisi **aynı sistemin içindedir**.

Örtüşmeli eşlemede bu güvence **yoktur**. Hayaletler *dayatılır*: A alanı
hayaletlerinden kuvvet alır, ama o kuvvetin tepkisi B alanında **görünmez**.
Örtüşen alan yöntemlerinin bilinen zayıf noktası budur.

## Zaman integrasyonu gerekmiyor

Kayma `t = 0`'da **doğrudan** ölçülebilir.

### İlk tasarımım yanlıştı — ve sayı bunu söyledi (S8)

Önce şunu yazdım: *"eşlenmiş toplam **sıfır** olmalı."* Ölçtüm: `0,9789`.
Ama **λ=2 ile λ=4 için birebir aynı** çıktı. Aynı çıkması, ölçülen şeyin
**eşleme çözünürlüğünden bağımsız** olduğunu söylüyordu.

Sebep: bir **alt küme** için `Σ m a` zaten sıfır değildir — çevresindeki
madde onu iter, bu **fizikseldir**. Üstelik `B_gerçek`ten dış kabuğu
(kesik komşuluklu) dışlamıştım ve o kabuğun tepkisi hiç sayılmıyordu.

### Doğru kıyas: sıfıra değil, **tek parça cevabına**

```
kayma  =  |F_eşlenmiş − F_tekparça|  /  ölçek
```

`F_tekparça`, **aynı bölgenin** tek çözünürlüklü (ince) bir kafeste ölçülen
net kuvvetidir. Dış kabuk etkisi **iki tarafta da** vardır ve sadeleşir.

**Boşluk kontrolü (ADR-0040):** tek parçada **tüm** parçacıkların toplamı
`Σ m a = 0` **tam** olmalı (antisimetri). Olmazsa ölçüm aracı bozuktur.

## Alan seçimi

**Düzgün** basınç işe yaramaz: orada kuvvetler zaten sıfırdır ve kayma
önemsiz olarak sıfır çıkar (boş bir doğru). **Doğrusal** basınç rampası
kullanılır: kuvvetler önemsiz değildir ama tek parça çözümde toplamları
yine **tam sıfırdır**.

"""
from __future__ import annotations

import numpy as np

from ..cpu_reference.sph_ref import kernel_dwdq, kernel_w

__all__ = ["net_force", "measure_coupling_conservation"]

RHO = 2700.0


def _lattice(spacing: float, half: float) -> np.ndarray:
    n = int(np.floor(half / spacing))
    e = np.arange(-n, n + 1) * spacing
    xx, yy, zz = np.meshgrid(e, e, e, indexing="ij")
    return np.column_stack([xx.ravel(), yy.ravel(), zz.ravel()])


def net_force(x: np.ndarray, m: np.ndarray, P: np.ndarray, h: float,
              subset: np.ndarray | None = None, block: int = 256) -> np.ndarray:
    """`Σ_{i∈subset} m_i a_i`, `a_i = −Σ_j m_j (P_i+P_j)/ρ² ∇_i W_ij`.

    `subset` verilmezse **tüm** parçacıklar toplanır ve sonuç antisimetri
    gereği **tam sıfır** olmalıdır.
    """
    x = np.ascontiguousarray(x, np.float64)
    m = np.ascontiguousarray(m, np.float64)
    P = np.ascontiguousarray(P, np.float64)
    n = len(m)
    if subset is None:
        subset = np.ones(n, bool)
    toplam = np.zeros(3)
    idx = np.flatnonzero(subset)
    for b0 in range(0, len(idx), block):
        sel = idx[b0:b0 + block]
        d = x[sel, None, :] - x[None, :, :]
        r = np.sqrt(np.einsum("ijk,ijk->ij", d, d))
        guv = r > 1.0e-300
        r_g = np.where(guv, r, 1.0)
        k = np.where(guv, kernel_dwdq(r / h, h, 3) / (h * r_g), 0.0)
        pij = (P[sel, None] + P[None, :]) / (RHO * RHO)
        ag = m[None, :] * pij * k
        a = -np.einsum("ij,ijk->ik", ag, d)
        toplam += np.einsum("i,ij->j", m[sel], a)
    return toplam


def measure_coupling_conservation(lam: float = 2.0, spacing_coarse: float = 1.0,
                                  h_over_spacing: float = 1.3,
                                  half: float = 8.0,
                                  r_split: float = 3.0,
                                  overlap: float | None = None,
                                  dP_dx: float = 1.0e8) -> dict:
    """Tek parça ile eşlenmiş sistemin net kuvvetini kıyasla.

    Alan **doğrusal**: `P = dP_dx · x`. Kuvvetler önemsiz değildir ama tek
    parça toplamı **tam sıfırdır**.
    """
    s_k = float(spacing_coarse)
    s_i = s_k / float(lam)
    h_k, h_i = h_over_spacing * s_k, h_over_spacing * s_i
    ort = 2.0 * h_k if overlap is None else float(overlap)
    if r_split - ort <= 2.0 * h_i:
        raise ValueError(
            f"örtüşme sığmıyor: r_split={r_split}, örtüşme={ort:.2f}, 2h_ince={2*h_i:.2f}")

    # ------------------------------------------------------------------
    # ILK TASARIMIM YANLISTI (S8). "Eslenmis toplam SIFIR olmali" dedim ve
    # `0,9789` olctum — ama lam=2 ile lam=4 icin BIREBIR AYNI cikti. Ayni
    # cikmasi, olculen seyin ESLEME COZUNURLUGUNDEN BAGIMSIZ oldugunu
    # soyluyordu: kayma eslemeden degil, `B_gercek`ten disladigim DIS
    # KABUGUN sayilmayan tepkisinden geliyordu.
    #
    # Bir alt kume icin `Σ m a` zaten SIFIR DEGILDIR — cevresindeki madde
    # onu iter, bu FIZIKSELDIR. Dogru kiyas sifira degil, **TEK PARCA
    # cevabina**dir:
    #     kayma = |F_eslenmis − F_tekparca| / olcek
    # ------------------------------------------------------------------
    # BOSLUK KONTROLU (araci kalibre eder): tek parcada TUM parcaciklarda
    # `Σ m a = 0` TAM olmali (antisimetri).
    x1 = _lattice(s_k, half)
    m1 = np.full(len(x1), RHO * s_k ** 3)
    P1 = dP_dx * x1[:, 0]
    net_hepsi = net_force(x1, m1, P1, h_k)
    olcek_hepsi = float(np.sum(m1)) * abs(dP_dx) / RHO

    # ------------------------------------------------------------------
    # IKINCI DUZELTME (S8'in devami). Tek parca INCE referansi, esleme
    # hatasinin YANINDA bir COZUNURLUK farki da tasiyordu: kaba alanin
    # kuvvetleri kaba `h` ile, referansinki ince `h` ile hesaplaniyordu.
    # Olculdu: lam=2 -> 0,15231 ama lam=3 -> 0,00583 (TERS yonde) — yani
    # olculen sey eslemenin kendisi degildi.
    #
    # KORUNUM SORUSU REFERANSSIZ SORULABILIR. Eslenmis sistemin toplam
    # momentum degisimi:
    #     Σ_A_gercek m a^A + Σ_B_gercek m a^B
    # Her alanin GERCEK-GERCEK etkilesimleri kendi icinde ANTISIMETRIKTIR
    # ve toplamda sadelesir. Geriye YALNIZCA hayalet kuvvetleri kalir:
    #     = F(A_gercek <- A_hayalet)  +  F(B_gercek <- B_hayalet)
    # Momentum korunuyorsa bu TAM SIFIRDIR. Referans gerekmez.
    #
    # SART: `B_gercek` B'nin TUM hayalet-olmayan parcaciklarini icermeli.
    # Ilk surumde dis kabugu dislamistim ve o yuzden ic toplam sadelesmiyordu
    # (S8'in kok nedeni).
    # ------------------------------------------------------------------
    xa_t = _lattice(s_i, half)
    ra = np.linalg.norm(xa_t, axis=1)
    xa = xa_t[ra < r_split + ort]
    ma = np.full(len(xa), RHO * s_i ** 3)
    Pa = dP_dx * xa[:, 0]
    a_gercek = np.linalg.norm(xa, axis=1) < r_split

    xb_t = _lattice(s_k, half)
    rb = np.linalg.norm(xb_t, axis=1)
    xb = xb_t[rb > r_split - ort]
    mb = np.full(len(xb), RHO * s_k ** 3)
    Pb = dP_dx * xb[:, 0]
    b_gercek = np.linalg.norm(xb, axis=1) > r_split       # TUMU (dis kabuk dahil)
    if int(a_gercek.sum()) < 20 or int(b_gercek.sum()) < 20:
        raise ValueError(
            f"bölge boş: A={int(a_gercek.sum())}, B={int(b_gercek.sum())}")

    net_es = net_force(xa, ma, Pa, h_i, a_gercek) + net_force(xb, mb, Pb, h_k,
                                                              b_gercek)
    olcek = float(np.sum(ma[a_gercek]) + np.sum(mb[b_gercek])) * abs(dP_dx) / RHO
    kayma = float(np.linalg.norm(net_es)) / olcek

    return {
        "lam": float(lam), "r_split": float(r_split), "overlap": ort,
        "h_coarse": h_k, "h_fine": h_i,
        "n_A_real": int(a_gercek.sum()), "n_B_real": int(b_gercek.sum()),
        "n_A_total": int(len(xa)), "n_B_total": int(len(xb)),
        # BOSLUK KONTROLU: tum parcaciklarda toplam TAM SIFIR (antisimetri).
        "monolithic_all_net_rel": float(np.linalg.norm(net_hepsi) / olcek_hepsi),
        "monolithic_is_exact": bool(
            float(np.linalg.norm(net_hepsi) / olcek_hepsi) < 1.0e-12),
        # ASIL SAYI: eslenmis sistemin toplam net kuvveti — SIFIR olmali.
        "conservation_drift_rel": kayma,
        "drift_vec": net_es.tolist(),
    }
