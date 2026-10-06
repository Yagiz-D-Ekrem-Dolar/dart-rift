"""`β`'yı üç çarpanına ayırmak — `β`'nın `Y₀`'ya duyarsızlığının **sebebi**.

Kaçan ejektanın çarpma ekseni boyunca taşıdığı momentum, tanım gereği üç
çarpanın ürünüdür:

    p_ejekta = M_kaçan · v_ort · kos_ort        (kos = momentum ağırlıklı)
    β − 1 ≈ K · p_ejekta / p_mermi

`K`, momentum defterinin `R` yüzeyi tanımından ve bağlı kalan ama hareket
eden maddeden gelen **sabit** önçarpandır (ölçüldü: `0,835 ± 0,005`, `Y₀`
`1 → 50 Pa` boyunca yalnız `%1,4` değişiyor — KAYIT-073).

**Ölçülen sonuç (W2 kıyas sahnesi, `t_geçiş = 1,0 s`, 600 s):**

| büyüklük | `Y₀` üssü |
|---|---|
| `M_kaçan` | `−0,3221` |
| `v_ort` | `+0,1866` |
| `kos_ort` | `+0,0585` |
| **toplam** | **`−0,0769`** |
| `β − 1` (bağımsız ölçüm) | **`−0,0760`** |

Üç üs toplanıp `β`'nın üssünü `%1,3` içinde veriyor. Yani:

> **`β`, `Y₀`'ya duyarsız değil — üç GÜÇLÜ etkinin birbirini götürmesinden
> duyarsız GÖRÜNÜYOR.** Dayanım artınca çok daha az madde kaçıyor
> (`−0,32`), ama kaçan daha hızlı (`+0,19`) ve daha toplu (`+0,06`).

Çıkarım için sonucu: `β`'yı tek gözlemli olarak kullanmak, üç bağımsız
bilgiyi **çarpıp** birini tutmaktır. `M_kaçan`'ı ayrı gözlemli olarak
eklemek `Y₀`'yu `4,2` kat daha iyi sıkıştırır (ADR-0053 §3).
"""
from __future__ import annotations

import numpy as np

__all__ = ["ONCARPAN_K", "ONCARPAN_K_SD", "ONCARPAN_K_DART",
           "ONCARPAN_K_DART_SD", "TOPLAM_KURALI_TOLERANS",
           "OLCULEN_AYRISMA", "ejekta_bilesenleri", "ayrisma_ussleri"]

#: Ölçülen önçarpan `K = (β−1) · p_mermi / (M·v·kos)`'ün tersi:
#: `M·v·kos/(p·(β−1)) = 0,8347 ± 0,0052` (3 koşu, `Y₀` 1–50 Pa).
ONCARPAN_K = 0.8347
ONCARPAN_K_SD = 0.0052
#: **ÖNÇARPAN SAHNEYE BAĞLI** (ölçüldü 2026-10-06, KAYIT-076). DART sahnesinde
#: (DO1/DO2/DN kolları, `Y₀` `500`/`5000` Pa ve `25 m` kaçık nişan) kimlik
#: **tam** çıkıyor: `M·v·kos / (p·b) = 1,000 ± 0,006`. W2 kıyas sahnesindeki
#: `0,835` o sahneye özgüdür (momentum defterinin `R` yüzeyi `75 m` küreye
#: göre tanımlı). Yani `b = K_sahne · M·v·kos / p` ve `K_DART⁻¹ = 1,000`.
#: `ejekta_bilesenleri(..., p_mermi=...)` varsayılan olarak `ONCARPAN_K`
#: (W2 değeri) kullanır; DART sahnesinde `b_tahmin`'i `0,835`'e **bölmek**
#: gerekir. Bu yüzden `b_tahmin` bir **tanı**dır, kilitli sayı değil.
ONCARPAN_K_DART = 1.000
ONCARPAN_K_DART_SD = 0.006
#: Toplam kuralı (`Σ üs = β`'nın üssü) bu bağıl farkın altında kalmalı.
#: Ölçülen `%1,3`; eşik `%10` — kural **anlamlı** ama sayısal türevlerin
#: gürültüsüne yer bırakıyor.
TOPLAM_KURALI_TOLERANS = 0.10

#: W2 kıyas sahnesinde ölçülen bileşenler (`t_geçiş = 1,0 s`, `600 s`).
#: `Y₀ [Pa] → (M_kaçan [kg], v_ort [m/s], kos_ort, β−1)`. KAYIT-073.
OLCULEN_AYRISMA: dict[float, tuple[float, float, float, float]] = {
    1.0: (5.3728e7, 0.30638, 0.61516, 3.3889),
    10.0: (2.6028e7, 0.48311, 0.71922, 3.0699),
    50.0: (1.5207e7, 0.63378, 0.77136, 2.4938),
}


def ejekta_bilesenleri(v, m, *, ehat, v_esc, mermi_kesri=None,
                       p_mermi: float | None = None) -> dict:
    """Son durumdan `β`'nın üç çarpanı.

    `ehat` **çarpma yönü** (mermi hangi yöne gidiyorsa); ejekta ters yöne
    gittiği için kosinüs `−v·ehat/|v|` ile ölçülür. `kos_ort` **momentum
    ağırlıklı** (`m·|v|`), çünkü momentuma katkıyı o ağırlık belirler.

    `p_mermi` verilirse `b_tahmin = ONCARPAN_K · M·v·kos / p_mermi` de döner.
    Kaçan parçacık `< 30` ise `ValueError` — üç çarpan gürültüden okunamaz.
    """
    v = np.asarray(v, dtype=np.float64)
    m = np.asarray(m, dtype=np.float64).ravel()
    e = np.asarray(ehat, dtype=np.float64).ravel()
    if v.ndim != 2 or v.shape[1] != 3 or v.shape[0] != m.size:
        raise ValueError(f"v (N,3) ve m (N,) olmali: {v.shape}, {m.shape}")
    n_e = float(np.linalg.norm(e))
    if e.size != 3 or not (n_e > 0.0):
        raise ValueError("ehat sifir olmayan 3-vektor olmali")
    e = e / n_e
    if not (float(v_esc) > 0.0):
        raise ValueError("v_esc pozitif olmali")
    if mermi_kesri is not None:
        hedef = ~(np.asarray(mermi_kesri, dtype=np.float64).ravel() > 0.5)
        v, m = v[hedef], m[hedef]
    hiz = np.linalg.norm(v, axis=1)
    kac = hiz > float(v_esc)
    if int(kac.sum()) < 30:
        raise ValueError(f"kacan parcacik {int(kac.sum())} (< 30): "
                         f"uc carpan gurultuden okunamaz")
    vv, mm, ss = v[kac], m[kac], hiz[kac]
    kos = -(vv @ e) / ss
    M = float(mm.sum())
    v_ort = float(np.average(ss, weights=mm))
    kos_ort = float(np.average(kos, weights=mm * ss))
    out = {"M_kacan": M, "v_ort": v_ort, "kos_ort": kos_ort,
           "n_kacan": int(kac.sum()), "p_eksen": float(np.sum(mm * -(vv @ e))),
           "carpim": M * v_ort * kos_ort}
    if p_mermi is not None:
        if not (float(p_mermi) > 0.0):
            raise ValueError("p_mermi pozitif olmali")
        out["b_tahmin"] = ONCARPAN_K * out["carpim"] / float(p_mermi)
    return out


def ayrisma_ussleri(ayrisma: dict | None = None) -> dict:
    """Üç bileşenin `Y₀` üsleri ve **toplam kuralı** sınaması.

    `ayrisma`: `Y₀ → (M, v, kos, b)`. Verilmezse `OLCULEN_AYRISMA`.
    Döner: her bileşenin üssü, toplam, `b`'nin kendi üssü, bağıl fark ve
    `toplam_kurali` (`"TUTUYOR"` / `"TUTMUYOR"`).
    """
    d = OLCULEN_AYRISMA if ayrisma is None else ayrisma
    if len(d) < 2:
        raise ValueError("en az 2 Y0 noktasi gerekir")
    Y = np.array(sorted(d), dtype=np.float64)
    if np.any(Y <= 0.0):
        raise ValueError("Y0 > 0 olmali")
    sutun = np.array([d[float(y)] for y in Y], dtype=np.float64)
    if sutun.shape[1] != 4 or np.any(sutun <= 0.0):
        raise ValueError("her nokta (M, v, kos, b) ve hepsi pozitif olmali")
    us = {}
    for j, ad in enumerate(("M_kacan", "v_ort", "kos_ort", "b")):
        us[ad] = float(np.polyfit(np.log(Y), np.log(sutun[:, j]), 1)[0])
    toplam = us["M_kacan"] + us["v_ort"] + us["kos_ort"]
    bagil = abs(toplam - us["b"]) / abs(us["b"])
    return {"usler": us, "toplam": toplam, "b_ussu": us["b"],
            "bagil_fark": bagil, "tolerans": TOPLAM_KURALI_TOLERANS,
            "toplam_kurali": ("TUTUYOR" if bagil <= TOPLAM_KURALI_TOLERANS
                              else "TUTMUYOR"),
            "M_kazanci": abs(us["M_kacan"]) / abs(us["b"]),
            "goturme": ("GOTURME VAR: M'nin ussu b'nin ussunden buyuk, "
                        "yani b uc etkinin BIRBIRINI GOTURMESIYLE kuculuyor"
                        if abs(us["M_kacan"]) > abs(us["b"]) else
                        "goturme yok: b en duyarli bilesen kadar duyarli")}
