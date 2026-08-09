"""İki aşamalı çözünürlük — **aşama-2 sahnesinin kurulması**.

ADR-0043'ün önerdiği şema:

1. **Aşama-1:** `λ ≈ 19`, `r_iç ≈ 3 m` — mermi **çözülmüş** (`A1 ≥ 2`).
   `t₁ = 4,767e-3 s`'e kadar koş (FAZ 4.5'in ölçtüğü bağlanma süresi).
2. **Kabalaştır:** ince bölgeyi `sites_from_cloud` + `coarsen_to_sites`
   ile aşama-2 çözünürlüğüne indir (**Lagrange'cı**, §4d).
3. **Aşama-2:** `λ = 2`, `r_iç = 25 m` ile `t_end`'e kadar devam.

Bu modül **3. adımın sahnesini** kuruyor: kabalaştırılmış bulut ile
aşama-2'nin geri kalanı **birleştiriliyor**.

## Asıl zorluk: **çifte sayım**

Kabalaştırılmış parçacıklar aşama-1'in ince bölgesinden geliyor ve
aşama-2'nin **kendi** parçacıkları da orada duruyor. İkisi de
bırakılırsa o bölgenin kütlesi **iki katına** çıkar.

> Bu, ADR-0030'un değişmezini doğrudan deler ve `β`'yı bozar. Çözüm:
> aşama-2'nin **çakışan** parçacıkları **çıkarılır**; hangileri olduğu
> `atilan_maske` ile raporlanır ve kütle defteri **tutturulur**.

## Çıkarma ölçütü **konum değil, kaynak**

Naif yol *"kabalaştırılmış parçacığa yakın olanları at"* olurdu ve
mesafe eşiği **keyfî** olurdu. Bunun yerine aşama-2'nin
`r_iç_asama1` içinde **başlamış** parçacıkları atılıyor: aşama-1 o
bölgenin maddesini zaten taşıyor.

> Ölçüt Lagrange'cı: *"bu madde aşama-1'de mi vardı"* — geometrik bir
> yakınlık değil.
"""
from __future__ import annotations

import numpy as np

from .coarsen import coarsen_to_sites, komsu_sagligi, sites_from_cloud

__all__ = ["asama2_sahnesi", "IkiAsamaSahne"]


class IkiAsamaSahne:
    """Aşama-2'ye verilecek birleşik durum + **kütle defteri**."""

    __slots__ = ("x", "v", "m", "e", "h", "alpha0", "Y0", "is_boulder",
                 "is_impactor", "kaynak", "diagnostics")

    def __init__(self, **kw):
        for k in self.__slots__:
            setattr(self, k, kw[k])

    @property
    def n(self) -> int:
        return len(self.m)


def asama2_sahnesi(a1_durum: dict, a1_ince_maske, a1_m, a1_alpha0, a1_Y0,
                   a1_is_boulder, a2, r_ince_a1: float,
                   ) -> IkiAsamaSahne:
    """Aşama-1'in son durumunu aşama-2 sahnesine **birleştir**.

    Parameters
    ----------
    a1_durum
        Aşama-1 çözücüsünün `state_numpy()` çıktısı (`x`, `v`, `u`).
    a1_ince_maske
        Aşama-1'de **ince** olan parçacıklar (mermi dahil) — bunlar
        kabalaştırılacak.
    a2
        Aşama-2 sahnesi (`refine_scene_local(..., lam=2, r_ince=25)`).
    r_ince_a1
        Aşama-1'in ince yarıçapı. Aşama-2'nin bu yarıçap **içinde
        başlamış** parçacıkları atılır (çifte sayım koruması).
    """
    ince = np.asarray(a1_ince_maske, dtype=bool)
    if not ince.any():
        raise ValueError("aşama-1'de ince parçacık yok")
    x1 = np.asarray(a1_durum["x"], dtype=np.float64)[ince]
    v1 = np.asarray(a1_durum["v"], dtype=np.float64)[ince]
    if "u" not in a1_durum:
        raise KeyError("aşama-1 durumunda `u` (özgül iç enerji) yok — "
                       f"anahtarlar: {sorted(a1_durum)}")
    e1 = np.asarray(a1_durum["u"], dtype=np.float64)[ince]
    m1 = np.asarray(a1_m, dtype=np.float64)[ince]
    if not (np.all(np.isfinite(x1)) and np.all(np.isfinite(v1))):
        raise ValueError("aşama-1 durumu sonlu değil — koşu patlamış")

    s2 = float(a2.spacing_fine)
    siteler = sites_from_cloud(x1, s2)
    kaba = coarsen_to_sites(x1, v1, m1, e1, siteler,
                            alpha0=np.asarray(a1_alpha0)[ince],
                            Y0=np.asarray(a1_Y0)[ince],
                            is_boulder=np.asarray(a1_is_boulder)[ince])

    # --- CIFTE SAYIM KORUMASI: asama-2'nin `r_ince_a1` ICINDE BASLAMIS
    # parcaciklari atilir. Olcut LAGRANGE'ci: "bu madde asama-1'de mi
    # vardi", geometrik yakinlik DEGIL.
    mp = np.asarray(a2.impact_point, dtype=np.float64)
    d2 = np.linalg.norm(np.asarray(a2.x, dtype=np.float64) - mp[None, :],
                        axis=1)
    atilan = d2 < float(r_ince_a1)
    tut = ~atilan
    if not tut.any():
        raise ValueError(f"aşama-2'nin tamamı atılıyor (r_ince_a1="
                         f"{r_ince_a1}) — yarıçap sahneden büyük")

    nk = len(kaba["m"])
    x = np.concatenate([kaba["x"], np.asarray(a2.x)[tut]])
    v = np.concatenate([kaba["v"], np.asarray(a2.v)[tut]])
    m = np.concatenate([kaba["m"], np.asarray(a2.m)[tut]])
    e = np.concatenate([kaba["e"], np.zeros(int(tut.sum()))])
    alpha0 = np.concatenate([kaba["alpha0"], np.asarray(a2.alpha0)[tut]])
    Y0 = np.concatenate([kaba["Y0"], np.asarray(a2.Y0)[tut]])
    blok = np.concatenate([kaba["is_boulder"],
                           np.asarray(a2.is_boulder, bool)[tut]])
    # Aktarilan parcaciklar asama-2'nin INCE `h`sini alir: onlar ince
    # bolgede ve aralikari `s2`.
    h = np.concatenate([np.full(nk, 2.0 * s2), np.asarray(a2.h)[tut]])
    # Mermi maddesi artik hedefle KARISMIS durumda; ayri bir "mermi"
    # etiketi tasimiyor. Bu bilerek: `β` mermi MOMENTUMUNDAN hesaplanir
    # ve o sayi asama-1'den TASINIR, etiketten degil.
    is_imp = np.concatenate([np.zeros(nk, bool),
                             np.asarray(a2.is_impactor, bool)[tut]])
    kaynak = np.concatenate([np.zeros(nk, np.int8),
                             np.ones(int(tut.sum()), np.int8)])

    m_a1 = float(m1.sum())
    m_akt = float(kaba["m"].sum())
    tani = dict(kaba["korunum"])
    tani.update({
        "n_asama1_ince": int(ince.sum()),
        "n_aktarilan": nk,
        "n_asama2_tutulan": int(tut.sum()),
        "n_asama2_atilan": int(atilan.sum()),
        "n_toplam": len(m),
        "s_asama2": s2,
        "r_ince_a1": float(r_ince_a1),
        # KUTLE DEFTERI: aktarim kutle kaybetmemeli.
        "aktarim_kutle_hatasi": abs(m_akt - m_a1) / max(m_a1, 1e-300),
        "asama2_atilan_kutle": float(np.asarray(a2.m)[atilan].sum()),
        "aktarilan_kutle": m_akt,
        # Asama-2 SPH ile ilerletecek: komsu yetiyor mu?
        "komsu": komsu_sagligi(kaba["x"], h=2.0 * s2),
    })
    return IkiAsamaSahne(x=x, v=v, m=m, e=e, h=h, alpha0=alpha0, Y0=Y0,
                         is_boulder=blok, is_impactor=is_imp, kaynak=kaynak,
                         diagnostics=tani)
