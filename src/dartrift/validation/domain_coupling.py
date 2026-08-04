"""C-1 — iki alan eşlemesinin arayüz hatası **hangi mekanizmadan** geliyor?

## Neden bu ölçüm

[KAYIT-024](../../../docs/defter/KAYIT-024_2026-08-04_degisken-h-arayuzu-kotulestiriyor.md)
§6'da açıkça yazıldı:

> C'nin arayüzü de iki farklı `h`'nin buluştuğu yerdir. Eşleme, sınır boyunca
> **doğrudan SPH toplamıyla** yapılırsa **C yerel olarak A′'ya eşittir** ve
> aynı 3,2–6,5 kat cezayı öder. Örtüşme bölgesi + ara değerleme (AMR hayalet
> hücresi gibi) yapılırsa farklı olabilir — **ama bu ölçülmedi.**

Bu modül o boşluğu kapatır.

## C'nin mekanizması A′'dan neden farklı olabilir

Örtüşmeli eşlemede **hiçbir çözücü kütle süreksizliği görmez**:

- İnce alan yalnızca **ince** parçacıklar görür; örtüşme bandındaki hayaletler
  de incedir (kaba çözümden **ara değerlenerek** üretilir).
- Kaba alan yalnızca **kaba** parçacıklar görür; hayaletleri ince çözümden
  ara değerlenir.

Yani sıfırıncı mertebe tutarlılık her iki alanda da **tam** kalır (her biri
kendi düzgün kafesinde çalışır). Bedel, süreksizlikten değil **ara
değerlemeden** gelir.

## Ölçülen

SPH ara değerlemesi `f_i = Σ_j (m_j/ρ_j) W_ij f_j`:

| sınav | doğru cevap | ne ölçer |
|---|---|---|
| **sabit** alan (`f = 1`) | tam `1` | sıfırıncı mertebe (birim bölünmesi) |
| **doğrusal** alan (`f = x`) | tam `x` | birinci mertebe |
| **karesel** alan (`f = x²`) | `x² + c·h²` | çekirdeğin doğal yumuşatması |

İki yön ayrı ayrı ölçülür: **ince → kaba** (kaba alanın hayaletleri) ve
**kaba → ince** (ince alanın hayaletleri). İkincisi zordur: kaba veriden
ince çözünürlükte bilgi **üretilemez**.

**Boşluk kontrolü (ADR-0040):** aynı çözünürlükten aynı çözünürlüğe ara
değerleme (`λ = 1`) doğrusal alanı **makine hassasiyetinde** vermelidir.
Vermezse ara değerleyici bozuktur ve hiçbir sayı yorumlanamaz.
"""
from __future__ import annotations

import numpy as np

from ..cpu_reference.sph_ref import kernel_w

__all__ = ["sph_interpolate", "measure_coupling_error"]

RHO0 = 1.0


def _lattice(spacing: float, half: float) -> np.ndarray:
    n = int(np.floor(half / spacing))
    eksen = np.arange(-n, n + 1) * spacing
    xx, yy, zz = np.meshgrid(eksen, eksen, eksen, indexing="ij")
    return np.column_stack([xx.ravel(), yy.ravel(), zz.ravel()])


def sph_interpolate(x_hedef: np.ndarray, x_kaynak: np.ndarray,
                    m_kaynak: np.ndarray, rho_kaynak: np.ndarray,
                    f_kaynak: np.ndarray, h: float,
                    block: int = 256) -> dict:
    """`f_i = Σ_j (m_j/ρ_j) W(|x_i − x_j|, h) f_j` — normalize **edilmemiş**.

    Normalize etmemek bilinçlidir: birim bölünmesinin kendisi ölçülecek
    büyüklüktür. Shepard normalizasyonu (`/Σ w`) sıfırıncı mertebeyi
    **tanım gereği** düzeltir ve sınavı boşaltırdı.
    """
    x_hedef = np.ascontiguousarray(x_hedef, np.float64)
    x_kaynak = np.ascontiguousarray(x_kaynak, np.float64)
    v_j = np.ascontiguousarray(m_kaynak / rho_kaynak, np.float64)
    f_kaynak = np.ascontiguousarray(f_kaynak, np.float64)
    if not (len(x_kaynak) == len(v_j) == len(f_kaynak)):
        raise ValueError("kaynak dizilerinin boyu uyuşmuyor")

    n = len(x_hedef)
    out = np.empty(n)
    birim = np.empty(n)
    for b0 in range(0, n, block):
        b1 = min(b0 + block, n)
        d = x_hedef[b0:b1, None, :] - x_kaynak[None, :, :]
        r = np.sqrt(np.einsum("ijk,ijk->ij", d, d))
        w = kernel_w(r / h, h, 3)
        out[b0:b1] = np.einsum("ij,j,j->i", w, v_j, f_kaynak)
        birim[b0:b1] = np.einsum("ij,j->i", w, v_j)
    return {"f": out, "partition_of_unity": birim}


def measure_coupling_error(lam: float = 2.0, spacing_coarse: float = 1.0,
                           h_over_spacing: float = 1.3,
                           half: float = 12.0) -> dict:
    """İnce→kaba ve kaba→ince ara değerleme hatası, üç alan üzerinde.

    Hedef noktalar **iç bölgeden** seçilir: kaynak kafesin kenarına `2h`'den
    yakın hedeflerde komşuluk **kesiktir** ve ölçülen şey ara değerleme
    hatası değil, kenar artığı olur (KAYIT-019 §3b'nin dersi).
    """
    if lam < 1.0:
        raise ValueError(f"lam >= 1 olmalı, {lam} geldi")
    s_k = float(spacing_coarse)
    s_i = s_k / float(lam)
    x_k, x_i = _lattice(s_k, half), _lattice(s_i, half)

    sonuc: dict = {"lam": float(lam), "spacing_coarse": s_k,
                   "spacing_inner": s_i, "n_coarse": int(len(x_k)),
                   "n_fine": int(len(x_i))}

    for ad, (x_kay, s_kay, x_hed) in (
            ("fine_to_coarse", (x_i, s_i, x_k)),
            ("coarse_to_fine", (x_k, s_k, x_i))):
        # `h` KAYNAGIN cozunurlugune baglidir: hayaleti ureten alan kendi
        # cekirdegiyle ara degerler.
        h = h_over_spacing * s_kay
        m = np.full(len(x_kay), RHO0 * s_kay ** 3)
        rho = np.full(len(x_kay), RHO0)
        pay = 2.0 * h
        ic = np.all(np.abs(x_hed) < half - pay, axis=1)
        if int(ic.sum()) < 20:
            raise ValueError(f"{ad}: iç bölge çok küçük ({int(ic.sum())})")
        xh = x_hed[ic]

        alanlar = {"constant": (np.ones(len(x_kay)), np.ones(len(xh))),
                   "linear": (x_kay[:, 0].copy(), xh[:, 0].copy()),
                   "quadratic": (x_kay[:, 0] ** 2, xh[:, 0] ** 2)}
        blok: dict = {"h": h, "n_targets": int(ic.sum()), "margin": pay}
        for alan, (f_kay, f_dogru) in alanlar.items():
            d = sph_interpolate(xh, x_kay, m, rho, f_kay, h)
            olcek = max(float(np.max(np.abs(f_dogru))), 1.0)
            blok[f"{alan}_max_err"] = float(np.max(np.abs(d["f"] - f_dogru)) / olcek)
            if alan == "constant":
                blok["partition_max_dev"] = float(
                    np.max(np.abs(d["partition_of_unity"] - 1.0)))
        sonuc[ad] = blok

    # BOSLUK KONTROLU: lam = 1'de iki yon de AYNI kafestir; dogrusal alan
    # makine hassasiyetinde gelmeli. (Cagiran taraf lam=1 ile kosturmali.)
    sonuc["is_identity_case"] = bool(abs(lam - 1.0) < 1e-12)
    return sonuc
