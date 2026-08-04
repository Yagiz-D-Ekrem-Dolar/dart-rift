"""A′ prototipi: **parçacık başına `h`** arayüz hatasını ne kadar düşürüyor?

## Neden

[KAYIT-023](../../../docs/defter/KAYIT-023_2026-08-04_cozunurlugu-h-belirliyor.md)
ölçtü ki çözülen ölçeği `h` belirliyor; dolayısıyla **A** (değişken kütle,
tek global `h`) ADR-0026'nın sorununu çözemez ve elendi. Geriye kalan
"mermiyi çöz" seçenekleri:

- **A′** — değişken kütle **+ parçacık başına `h`** (çekirdek/hash-grid/CFL
  mimari değişikliği)
- **C** — iki alan eşlemesi (her alanın kendi skaler `h`'si)

İkisi arasındaki seçim, A′'nın **mimari maliyetinin karşılığını verip
vermediğine** bağlıdır. Karşılığı, arayüzdeki yapay kuvvetin ne kadar
düştüğüdür. Bu modül **onu ölçer** — üretim çözücüsüne dokunmadan.

## Nasıl

Momentum korunumu, kuvvet biçiminin **antisimetrik** olmasını gerektirir
(KAYIT-020 §1'de `Σmᵢaᵢ ≈ 1e-16` ölçüldü). Parçacık başına `h` ile bunu
sağlamanın standart yolu **simetrik `h`**:

```
h_ij = 0.5 * (h_i + h_j)        ->  W_ij = W_ji ,  grad_i W_ij = -grad_j W_ji
```

İkinci bir yaygın seçenek **simetrik çekirdek** (Hernquist & Katz 1989):

```
W_ij = 0.5 * (W(r_ij, h_i) + W(r_ij, h_j))
```

İkisi de ölçülüyor; hangisinin daha iyi olduğu **tercihle değil ölçümle**
belirlenir.

## Sınav

Sıfırıncı mertebe tutarlılık: **düzgün** bir basınç alanında ayrık gradyan
sıfır vermelidir. Vermezse doğan şey **yapay kuvvettir**
([`mass_ratio`][dartrift.validation.mass_ratio] ile aynı sınav, aynı ölçek).

**Boşluk kontrolü (ADR-0040):** tek popülasyonda (`λ = 1`, tüm `h`'ler eşit)
her üç biçim de **makine sıfırı** vermeli. Vermezse prototip bozuktur.
"""
from __future__ import annotations

import numpy as np

from ..cpu_reference.sph_ref import kernel_dwdq, kernel_w

__all__ = ["evaluate_uniform_pressure", "compare_h_schemes"]

_SCHEMES = ("global_h", "average_h", "symmetric_kernel", "gradh")


def _pair_terms(x: np.ndarray, h: np.ndarray, scheme: str):
    """Çift geometrisi ve çekirdek türevleri — O(N²), N küçük tutulmalı."""
    d = x[:, None, :] - x[None, :, :]                 # r_i - r_j
    r = np.sqrt(np.einsum("ijk,ijk->ij", d, d))
    np.fill_diagonal(r, 0.0)
    guv = r > 1.0e-300
    # `np.where` bolmeyi YINE DE hesaplar; paydayi guvenli yap ki
    # uyari gercek sorunlari gizlemesin (deger degismez).
    r_g = np.where(guv, r, 1.0)

    if scheme == "average_h":
        hij = 0.5 * (h[:, None] + h[None, :])
        q = np.where(guv, r / hij, 0.0)
        dwdq = kernel_dwdq(q, hij, 3)
        # grad_i W_ij = dW/dq * (1/h_ij) * (x_i - x_j)/r
        katsayi = np.where(guv, dwdq / (hij * r_g), 0.0)
    elif scheme == "global_h":
        hg = float(np.max(h))                         # KABA bolgeye gore
        q = np.where(guv, r / hg, 0.0)
        dwdq = kernel_dwdq(q, hg, 3)
        katsayi = np.where(guv, dwdq / (hg * r_g), 0.0)
    elif scheme == "gradh":
        # Uyarlamali SPH'in DOGRU bicimi (Springel & Hernquist 2002;
        # Price & Monaghan 2004): `h` degisken oldugunda sifirinci mertebe
        # tutarlilik ancak grad-h (Omega) duzeltmesiyle korunur. Onceki uc
        # sema bu terimi ATLIYOR — o yuzden A'ye HAKSIZLIK ediyorlardi.
        #
        # Burada yalnizca cift katsayilari donuyor; Omega ve iki-cekirdek
        # toplami `evaluate_uniform_pressure` icinde uygulanir.
        raise RuntimeError("gradh semasi _pair_terms uzerinden cagrilmaz")
    elif scheme == "symmetric_kernel":
        # W_ij = 0.5*(W(r,h_i) + W(r,h_j)) -> gradyani da ortalamadir
        hi = np.broadcast_to(h[:, None], r.shape)
        hj = np.broadcast_to(h[None, :], r.shape)
        qi = np.where(guv, r / hi, 0.0)
        qj = np.where(guv, r / hj, 0.0)
        ki = np.where(guv, kernel_dwdq(qi, hi, 3) / (hi * r_g), 0.0)
        kj = np.where(guv, kernel_dwdq(qj, hj, 3) / (hj * r_g), 0.0)
        katsayi = 0.5 * (ki + kj)
    else:
        raise ValueError(f"bilinmeyen şema: {scheme!r}, {_SCHEMES} bekleniyordu")
    np.fill_diagonal(katsayi, 0.0)
    return d, r, katsayi, guv


def _dwdh(q: np.ndarray, h: np.ndarray, w: np.ndarray,
          dwdq: np.ndarray) -> np.ndarray:
    """`∂W/∂h` (3B): `W = (C/h³)·f(q)`, `q = r/h` →  `-(3W + q·∂W/∂q)/h`."""
    return -(3.0 * w + q * dwdq) / h


def _gradh_acceleration(x: np.ndarray, m: np.ndarray, h: np.ndarray,
                        rho: float, P: float, block: int = 512) -> np.ndarray:
    """Uyarlamalı SPH'in **grad-h düzeltmeli** kuvveti.

    `h_i = η (m_i/ρ_i)^{1/3}` ⇒ `∂h_i/∂ρ_i = −h_i/(3ρ_i)` ve

    ```
    Ω_i = 1 + (h_i / 3ρ_i) · Σ_j m_j ∂W_ij(h_i)/∂h_i
    a_i = −Σ_j m_j [ P_i/(Ω_i ρ_i²) ∇_i W_ij(h_i)
                   + P_j/(Ω_j ρ_j²) ∇_i W_ij(h_j) ]
    ```

    Bu biçim momentumu **tam** korur (her çift terimi antisimetriktir).

    `N×N×3` dizi **hiç oluşturulmaz**: `i` üzerinden bloklanır. 7000 parçacıkta
    tek parça hesap ~1,2 GB isterdi.
    """
    n = len(m)
    omega = np.empty(n)
    # --- 1. gecis: Omega
    for b0 in range(0, n, block):
        b1 = min(b0 + block, n)
        d = x[b0:b1, None, :] - x[None, :, :]
        r = np.sqrt(np.einsum("ijk,ijk->ij", d, d))
        guv = r > 1.0e-300
        hi = np.broadcast_to(h[b0:b1, None], r.shape)
        qi = np.where(guv, r / hi, 0.0)
        wi = np.where(guv, kernel_w(qi, hi, 3), 0.0)
        di = np.where(guv, kernel_dwdq(qi, hi, 3), 0.0)
        omega[b0:b1] = 1.0 + (h[b0:b1] / (3.0 * rho)) * np.einsum(
            "j,ij->i", m, _dwdh(qi, hi, wi, di))
    pi = P / (omega * rho * rho)

    # --- 2. gecis: ivme
    a = np.empty((n, 3))
    for b0 in range(0, n, block):
        b1 = min(b0 + block, n)
        d = x[b0:b1, None, :] - x[None, :, :]
        r = np.sqrt(np.einsum("ijk,ijk->ij", d, d))
        guv = r > 1.0e-300
        r_g = np.where(guv, r, 1.0)
        hi = np.broadcast_to(h[b0:b1, None], r.shape)
        hj = np.broadcast_to(h[None, :], r.shape)
        qi = np.where(guv, r / hi, 0.0)
        qj = np.where(guv, r / hj, 0.0)
        k_i = np.where(guv, kernel_dwdq(qi, hi, 3) / (hi * r_g), 0.0)
        k_j = np.where(guv, kernel_dwdq(qj, hj, 3) / (hj * r_g), 0.0)
        ag = m[None, :] * (pi[b0:b1, None] * k_i + pi[None, :] * k_j)
        a[b0:b1] = -np.einsum("ij,ijk->ik", ag, d)
    return a


def gradh_margin_factor(h_over_spacing: float) -> float:
    """grad-h ölçümünde kenar payı neden **iki kat destek** olmalı.

    Diğer şemalarda `i`'nin hatası yalnızca kendi komşuluğuna bağlıdır; pay
    `2h` yeter (KAYIT-019 §3b). grad-h'de kuvvet **komşunun** `Ω_j`'sini de
    kullanır ve `Ω_j` o komşunun **kendi** komşuluğundan gelir. Yani yüzeyin
    kestiği bilgi **bir çekirdek daha** içeri sızar.

    Ölçüldü (λ=1, `r_out=70`, `s=8`, `h/s=1,3`): `Ω` iç bölgede tam düzgün
    (yayılım `6,7e-16`) ama grad-h ivmesi `7,69e-06` — diğer üç şema
    `1,86e-15`. Fark tamamen bu sızıntıdandı.
    """
    return 4.0 * h_over_spacing + 0.5


def evaluate_uniform_pressure(x: np.ndarray, m: np.ndarray, h: np.ndarray,
                              scheme: str, rho: float = 2700.0,
                              P: float = 2.6967e8) -> dict:
    """Düzgün `P` ve `ρ`'da ivme — doğru cevap **tam sıfır**.

    `a_i = -Σ_j m_j (P_i/ρ_i² + P_j/ρ_j²) ∇_i W_ij`; düzgün alanda
    `= -(2P/ρ²) Σ_j m_j ∇_i W_ij`.
    """
    x = np.ascontiguousarray(x, np.float64)
    m = np.ascontiguousarray(m, np.float64)
    h = np.ascontiguousarray(h, np.float64)
    if not (len(x) == len(m) == len(h)):
        raise ValueError(f"boyutlar uyuşmuyor: {len(x)}, {len(m)}, {len(h)}")
    if scheme == "gradh":
        a = _gradh_acceleration(x, m, h, rho, P)
    else:
        d, r, katsayi, _ = _pair_terms(x, h, scheme)
        # sum_j m_j * grad_i W_ij   (vektor)
        agirlik = katsayi * m[None, :]
        grad_toplam = np.einsum("ij,ijk->ik", agirlik, d)
        a = -(2.0 * P / (rho * rho)) * grad_toplam
    # Momentum korunumu: SUM m_i a_i TAM SIFIR olmali (antisimetri).
    net = float(np.linalg.norm((m[:, None] * a).sum(axis=0)))
    olcek_m = float(np.sum(m * np.linalg.norm(a, axis=1))) or 1.0
    return {"a": a, "a_norm": np.linalg.norm(a, axis=1),
            "momentum_residual": net / olcek_m,
            "a_reference_scale": abs(P) / (rho * float(np.max(h)))}


def _two_zone(r_outer: float, r_inner: float, spacing: float, lam: float,
              h_over_spacing: float, ramp_width: float = 0.0) -> dict:
    """`mass_ratio.build_two_zone` ile **aynı** geometri, ama `h` de döner."""
    from .mass_ratio import build_two_zone

    z = build_two_zone(r_outer, r_inner, spacing, lam)
    rr = np.linalg.norm(z["x"], axis=1)
    ic = rr < r_inner
    # A' TAM OLARAK SUDUR: h YEREL aralikla olceklenir.
    h_ic = h_over_spacing * z["spacing_inner"]
    h_dis = h_over_spacing * z["spacing_outer"]
    if ramp_width <= 0.0:
        h = np.where(ic, h_ic, h_dis)                    # ANI sicrama
    else:
        # KADEMELI: `r_inner` cevresinde `ramp_width` genisliginde bir bantta
        # `h` duzgun (smoothstep) degisir. Gercek uyarlamali SPH'de `h`
        # zaten sureklidir; ani sicrama en KOTU durumdur.
        t = np.clip((rr - (r_inner - 0.5 * ramp_width)) / ramp_width, 0.0, 1.0)
        yumusak = t * t * (3.0 - 2.0 * t)                # smoothstep
        h = h_ic + (h_dis - h_ic) * yumusak
    return {**z, "h": h, "r": rr, "inner_mask": ic}


def compare_h_schemes(
    lams: tuple[float, ...] = (1.0, 1.26, 1.59, 2.0),
    r_outer: float = 70.0,
    r_inner: float = 25.0,
    spacing: float = 8.0,
    h_over_spacing: float = 1.3,
    ramp_width: float = 0.0,
) -> dict:
    """Üç şemayı aynı geometride kıyasla.

    Kenar payı **en büyük** `h`'ye göre alınır (`2·h_max + s/2`): kesik
    komşuluklu parçacıklar ölçüme girerse sonuç yüzey artığı olur — KAYIT-019
    §3b'de tam olarak bu oldu.
    """
    satirlar = []
    for lam in lams:
        z = _two_zone(r_outer, r_inner, spacing, lam, h_over_spacing,
                      ramp_width)
        h_max = float(np.max(z["h"]))
        # grad-h komsunun Omega_j'sini de kullanir -> bilgi BIR CEKIRDEK DAHA
        # iceri sizar; pay 4h olmali (bkz. `gradh_margin_factor`).
        paylar = {"gradh": 4.0 * h_max + 0.5 * spacing}
        pay_std = 2.0 * h_max + 0.5 * spacing
        pay_max = max(pay_std, paylar["gradh"])
        if r_outer - pay_max <= r_inner + h_max:
            raise ValueError(
                f"geometri yetersiz: r_outer={r_outer} ama en az "
                f"{pay_max + h_max + r_inner:.1f} gerek (grad-h payi {paylar['gradh']:.1f})")

        satir = {"lam": float(lam), "mass_ratio": float(lam ** 3),
                 "ramp_width": float(ramp_width),
                 "n_total": int(len(z["m"])),
                 "h_min": float(np.min(z["h"])), "h_max": h_max}
        for sema in _SCHEMES:
            pay = paylar.get(sema, pay_std)
            kenar = z["r"] < r_outer - pay
            arayuz = kenar & (np.abs(z["r"] - r_inner) < h_max)
            if arayuz.sum() < 20:
                raise ValueError(
                    f"{sema}: arayüz bölgesi çok küçük ({int(arayuz.sum())}), "
                    f"pay {pay:.1f} m")
            satir[f"{sema}_n_interface"] = int(arayuz.sum())
            d = evaluate_uniform_pressure(z["x"], z["m"], z["h"], sema)
            satir[f"{sema}_a_rms"] = float(
                np.sqrt(np.mean(d["a_norm"][arayuz] ** 2)))
            satir[f"{sema}_a_max"] = float(d["a_norm"][arayuz].max())
            satir[f"{sema}_over_ref"] = (
                satir[f"{sema}_a_max"] / d["a_reference_scale"])
            satir[f"{sema}_momentum"] = d["momentum_residual"]
        satirlar.append(satir)

    taban = satirlar[0]
    # BOSLUK KONTROLU: lam = 1'de tum h'ler esit -> uc sema da MAKINE SIFIRI.
    taban_temiz = bool(all(taban[f"{s}_over_ref"] < 1.0e-9 for s in _SCHEMES))
    # Momentum: uc sema da antisimetrik olmali.
    momentum_ok = bool(all(
        r[f"{s}_momentum"] < 1.0e-12 for r in satirlar for s in _SCHEMES))
    return {"rows": satirlar, "schemes": list(_SCHEMES),
            "baseline_clean": taban_temiz,
            "all_conserve_momentum": momentum_ok}
