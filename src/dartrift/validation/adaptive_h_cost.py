"""A′-1 — parçacık başına `h`'nin **komşu arama bedeli** (GPU gerekmez).

## Neden bu, A′'nın kefesindeki asıl sayı

ADR-0041 §3.8'den sonra A′ öne geçti; kalan tek ölçülmemiş şey **mimari
bedeli**. Kod okundu ve düğüm bulundu:

```
warp_core/hash_grid.py:42    def build(self, x64, support: float) -> float:
warp_core/hash_grid.py:47        self.grid.build(points=self.x32, radius=radius32)
warp_core/density.py:26      q = wp.hash_grid_query(grid, x32[i], radius32)
```

Izgara **tek bir** destek yarıçapıyla kurulur ve sorgular da tek bir
`radius32` kullanır. Parçacık başına `h` ile ızgara **en büyük** desteğe
(`2·h_maks`) göre kurulmak zorundadır; her parçacık kendi `h`'sine göre
**eler**.

Sonuç: **ince** parçacıklar gereğinden çok aday tarar. Bu bir tahmin
değil — ölçülebilir bir geometri sorusudur:

> Bir ince parçacık, `2·h_maks` içinde **kaç** aday görüyor ve bunların
> **kaçı** kendi `2·h_i`'si içinde kalıyor?

Oran, komşu aramasının **boşa giden** kısmıdır.

## Neden önemli

A′ maliyeti **düşürmek** için seçilir (her yeri inceltmemek). Komşu arama
`(h_maks/h_i)³` kat pahalılaşırsa tasarruf küçülür — ve ince bölge zaten
parçacıkların çoğunu barındırır.

Kaçınmanın yolu **seviye başına ayrı ızgara**dır; o da ek mimaridir ve bu
ölçüm onun **ne kadar gerekli** olduğunu söyler.

**Boşluk kontrolü (ADR-0040):** `λ = 1`'de (tek `h`) boşa giden oran **1,0**
olmalı — hiçbir israf yok. Olmazsa ölçüm bozuktur.
"""
from __future__ import annotations

import numpy as np

__all__ = ["measure_neighbour_waste", "measure_multilevel_waste"]


def measure_neighbour_waste(lam: float = 2.0, r_outer: float = 70.0,
                            r_inner: float = 25.0, spacing: float = 8.0,
                            h_over_spacing: float = 1.3,
                            block: int = 256) -> dict:
    """İnce parçacıkların taradığı aday sayısı / gerçekten gereken sayı.

    Tek ızgara `2·h_maks` yarıçapıyla kurulur; her parçacık kendi `2·h_i`'si
    içindekileri tutar. Oran **boşa giden** taramadır.
    """
    from .mass_ratio import build_two_zone

    if lam < 1.0:
        raise ValueError(f"lam >= 1 olmalı, {lam} geldi")
    z = build_two_zone(r_outer, r_inner, spacing, lam)
    x = np.ascontiguousarray(z["x"], np.float64)
    r = np.linalg.norm(x, axis=1)
    ic = r < r_inner
    h = np.where(ic, h_over_spacing * z["spacing_inner"],
                 h_over_spacing * z["spacing_outer"])
    h_max = float(h.max())
    sup_global = 2.0 * h_max                       # izgaranin kurulma yaricapi

    # Kenar etkisini disla: yuzeye yakin parcaciklar dogal olarak az komsu
    # gorur ve orani BOZAR (D1 kurali).
    kenar = r < r_outer - sup_global - 0.5 * spacing
    if int(kenar.sum()) < 50:
        raise ValueError(f"iç bölge çok küçük: {int(kenar.sum())}")

    n = len(x)
    idx = np.flatnonzero(kenar)
    aday = np.zeros(len(idx), np.int64)
    gercek = np.zeros(len(idx), np.int64)
    for b0 in range(0, len(idx), block):
        sel = idx[b0:b0 + block]
        d = x[sel, None, :] - x[None, :, :]
        rr = np.sqrt(np.einsum("ijk,ijk->ij", d, d))
        aday[b0:b0 + len(sel)] = np.sum(rr < sup_global, axis=1)
        gercek[b0:b0 + len(sel)] = np.sum(rr < 2.0 * h[sel, None], axis=1)

    ic_k = ic[idx]
    oran = aday / np.maximum(gercek, 1)
    kaba_k = ~ic_k

    def _ort(mask):
        return float(np.mean(oran[mask])) if mask.any() else float("nan")

    return {
        "lam": float(lam), "h_ratio": float(h_max / float(h.min())),
        "n_total": int(n), "n_measured": int(kenar.sum()),
        "n_fine": int(ic_k.sum()), "n_coarse": int(kaba_k.sum()),
        "global_support": sup_global,
        "waste_fine": _ort(ic_k),
        "waste_coarse": _ort(kaba_k),
        "waste_overall": float(np.mean(oran)),
        # Kuresel beklenti: (h_maks/h_i)^3. Olculen ondan SAPIYORSA sebebi
        # yazilmali (ornegin arayuz yakininda karisik komsuluk).
        "expected_fine": float((h_max / (h_over_spacing * z["spacing_inner"])) ** 3),
        # BOSLUK KONTROLU: lam=1'de israf TAM 1.0 olmali.
        "is_identity_case": bool(abs(lam - 1.0) < 1e-12),
        # ------------------------------------------------------------------
        # ASIL SORU: parcacik TASARRUFU, arama ISRAFINI karsiliyor mu?
        #
        # A' her yeri inceltmemek icin secilir. Kazanci PARCACIK SAYISIDIR;
        # bedeli tek izgarada ARAMA ISRAFIDIR. Net oran:
        #
        #   is(A')      = N(A') * ortalama_israf
        #   is(tumu_ince) = N(tumu_ince) * 1.0
        #
        # Oran 1'e yakinsa A' TEK IZGARAYLA hicbir sey kazandirmiyor demektir
        # ve seviye basina ayri izgara ZORUNLU hale gelir.
        # ------------------------------------------------------------------
        **_net_kazanc(z, lam, r_outer, spacing, float(np.mean(oran))),
    }


def _net_kazanc(z: dict, lam: float, r_outer: float, spacing: float,
                israf: float) -> dict:
    """A′'nın parçacık tasarrufu ile arama israfını **birlikte** değerlendir."""
    from ..setup.rubble_generator import FCC_VOLUME_FACTOR

    v_ince = (spacing / lam) ** 3 * FCC_VOLUME_FACTOR
    n_tumu_ince = (4.0 / 3.0) * np.pi * r_outer ** 3 / v_ince
    n_a = float(len(z["m"]))
    tasarruf = float(n_tumu_ince / n_a)
    return {
        "n_all_fine_equivalent": float(n_tumu_ince),
        "particle_saving": tasarruf,
        # <1 ise A' TEK IZGARAYLA daha ucuz; >1 ise DAHA PAHALI.
        "net_cost_vs_all_fine": float(israf / tasarruf),
        "single_grid_worthwhile": bool(israf / tasarruf < 0.5),
    }


def measure_multilevel_waste(lam: float = 2.0, r_outer: float = 70.0,
                             r_inner: float = 25.0, spacing: float = 8.0,
                             h_over_spacing: float = 1.3,
                             block: int = 256) -> dict:
    """A′-2 — **seviye başına ayrı ızgara** israfı `1,0`'a düşürüyor mu?

    KAYIT-031 tek ızgarada israfı ölçtü (8:1'de `5,13×`, 16:1'de `10,06×`)
    ve çok seviyeli aramanın **ön koşul** olduğunu söyledi. Bu ölçüm o
    iddiayı sınar.

    ## Doğru sorgu yarıçapı

    Simetrik (`average_h`) biçimde bir `(i, j)` çiftinin etkileşim yarıçapı
    `2·h_ij = h_i + h_j`'dir. Yani parçacık `i`, **her seviye** `L` için o
    seviyenin ızgarasını `h_i + h_L` yarıçapıyla sorgulamalıdır.

    Tek ızgarada bu yarıçap **her zaman** `2·h_maks`'tır — ince parçacıklar
    için gereğinden büyük. Çok seviyeli aramada her sorgu **kendi** çiftine
    göre daraltılır.

    **Boşluk kontrolü (ADR-0040):** `λ = 1`'de tek seviye vardır ve iki
    yöntem **aynı** sonucu vermelidir; israf ikisinde de `1,0`.
    """
    from .mass_ratio import build_two_zone

    if lam < 1.0:
        raise ValueError(f"lam >= 1 olmalı, {lam} geldi")
    z = build_two_zone(r_outer, r_inner, spacing, lam)
    x = np.ascontiguousarray(z["x"], np.float64)
    r = np.linalg.norm(x, axis=1)
    ic = r < r_inner
    h_i_val = h_over_spacing * z["spacing_inner"]
    h_k_val = h_over_spacing * z["spacing_outer"]
    h = np.where(ic, h_i_val, h_k_val)
    h_max = float(h.max())
    seviyeler = sorted({float(h_i_val), float(h_k_val)})

    kenar = r < r_outer - 2.0 * h_max - 0.5 * spacing
    if int(kenar.sum()) < 50:
        raise ValueError(f"iç bölge çok küçük: {int(kenar.sum())}")

    idx = np.flatnonzero(kenar)
    tek_izgara = np.zeros(len(idx), np.int64)
    cok_seviye = np.zeros(len(idx), np.int64)
    gercek = np.zeros(len(idx), np.int64)
    for b0 in range(0, len(idx), block):
        sel = idx[b0:b0 + block]
        d = x[sel, None, :] - x[None, :, :]
        rr = np.sqrt(np.einsum("ijk,ijk->ij", d, d))
        hi = h[sel, None]
        hj = h[None, :]
        # GERCEKTEN gereken: simetrik yaricap h_i + h_j
        ger = rr < (hi + hj)
        gercek[b0:b0 + len(sel)] = np.sum(ger, axis=1)
        # TEK izgara: her zaman 2*h_maks
        tek_izgara[b0:b0 + len(sel)] = np.sum(rr < 2.0 * h_max, axis=1)
        # COK SEVIYE: her seviye L kendi yaricapiyla (h_i + h_L) sorgulanir
        toplam = np.zeros(len(sel), np.int64)
        for hL in seviyeler:
            bu_seviye = np.isclose(h, hL)[None, :]
            toplam += np.sum((rr < (hi + hL)) & bu_seviye, axis=1)
        cok_seviye[b0:b0 + len(sel)] = toplam

    ger_g = np.maximum(gercek, 1)
    israf_tek = tek_izgara / ger_g
    israf_cok = cok_seviye / ger_g
    ic_k = ic[idx]

    def _ort(a, mask):
        return float(np.mean(a[mask])) if mask.any() else float("nan")

    return {
        "lam": float(lam), "n_levels": len(seviyeler),
        "n_measured": int(kenar.sum()), "n_fine": int(ic_k.sum()),
        "single_grid_waste_fine": _ort(israf_tek, ic_k),
        "single_grid_waste_overall": float(np.mean(israf_tek)),
        "multilevel_waste_fine": _ort(israf_cok, ic_k),
        "multilevel_waste_overall": float(np.mean(israf_cok)),
        # Kazanc: tek izgaraya gore kac kat daha az aday taraniyor?
        "improvement": float(np.mean(israf_tek) / max(float(np.mean(israf_cok)),
                                                      1e-300)),
        # BOSLUK KONTROLU: lam=1'de tek seviye var, ikisi AYNI olmali.
        "single_level_case": bool(len(seviyeler) == 1),
        # Cok seviyeli arama israfi 1'e YAKIN mi? (Tam 1 olmaz: ayni
        # seviyedeki komsular icin h_i + h_L = 2h_i, dogru; farkli
        # seviyedekiler icin de dogru. Yani TAM 1 beklenir.)
        "multilevel_is_exact": bool(abs(float(np.mean(israf_cok)) - 1.0) < 1e-12),
    }
