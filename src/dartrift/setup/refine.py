"""A′'yı **DART sahnesine** bağla: çarpma noktası çevresinde yerel incelme.

## Neden gerekli

ADR-0026'nın kapattığı sorun şuydu: DART mermisi (~1,3 m) hedefin
çözünürlüğünden (`spacing` ~7 m) **küçük**. `measure_longrun` bunu zaten
raporluyor:

```
mermi cozunurlugu: ... HEDEF aralagina gore X parcacik/cap
UYARI: mermi hedef cozunurlugunun altinda — erken zamanli
       baglanma COZULMEMIS (ADR-0026)
```

Her yeri inceltmek `λ³` kat parçacık demek. A′ (ADR-0041) tam da bunun
için seçildi: **yalnızca çarpma bölgesi** incelir ve `h` **parçacık
başına** taşınır.

KAYIT-037 ölçtü ki bu, tam malzeme modelinde incelme kazancının
**%67,1**'ini veriyor; yalnızca parçacık eklemek (tek `h`) **%9,1**.

## Yapılan şey

İki sahne kurulur — biri `spacing`, biri `spacing/λ` — ve çarpma noktası
çevresinde `r_ince` yarıçaplı bir küre içinde **ince** sahnenin hedef
parçacıkları, dışında **kaba** sahnenin hedef parçacıkları kullanılır.
Mermi her zaman **ince** sahneden gelir (asıl amaç onu çözmek).

`h` parçacık başına: ince bölgede `2·spacing/λ`, kaba bölgede `2·spacing`.

## Bilerek yapılmayan

**Kütle korunumu tam değildir.** İki farklı kafes aynı küreyi farklı
döşer; sınırda küçük bir kütle uyuşmazlığı kalır. Ölçülüyor ve
`diagnostics`'e yazılıyor — gizlenmiyor. KAYIT-036'da aynı büyüklük küp
geometrisinde `%0,073` çıkmıştı.
"""
from __future__ import annotations

import numpy as np

__all__ = ["refine_scene", "RefinedScene"]


class RefinedScene:
    """`Scene` ile aynı alanlar + **parçacık başına `h`**.

    Ayrı bir sınıf, `Scene`'in değişmezlerini (tek `spacing`) bozmamak
    için: bu nesnenin **iki** aralığı var ve `spacing` tek başına
    anlamlı değil.
    """

    __slots__ = ("x", "v", "m", "alpha0", "Y0", "h", "is_impactor",
                 "is_boulder", "is_fine", "spacing_coarse", "spacing_fine",
                 "target_radius", "impact_point", "impact_direction",
                 "surface_normal", "diagnostics")

    def __init__(self, **kw):
        for k in self.__slots__:
            setattr(self, k, kw[k])

    @property
    def n(self) -> int:
        return len(self.m)

    @property
    def n_target(self) -> int:
        return int(np.count_nonzero(~self.is_impactor))

    @property
    def target_mass(self) -> float:
        return float(np.sum(self.m[~self.is_impactor]))

    @property
    def impactor_momentum(self) -> np.ndarray:
        s = self.is_impactor
        return np.sum(self.m[s, None] * self.v[s], axis=0)


def refine_scene(kaba, ince, r_ince: float) -> RefinedScene:
    """Kaba ve ince sahneyi **çarpma noktası çevresinde** birleştir.

    Parameters
    ----------
    kaba, ince
        `build_scene` çıktıları. **Aynı** tohum, şekil ve mermi ile,
        yalnızca `spacing` farklı kurulmuş olmalıdır.
    r_ince
        İnce bölgenin yarıçapı [m], çarpma noktasından ölçülür.

    Notes
    -----
    Mermi her zaman **ince** sahneden alınır — A′'nın varlık nedeni onu
    çözmek. Kaba sahnenin mermisi atılır.
    """
    if r_ince <= 0.0:
        raise ValueError(f"r_ince pozitif olmalı, {r_ince} geldi")
    if not (ince.spacing < kaba.spacing):
        raise ValueError(
            f"ince aralık kabadan küçük olmalı: {ince.spacing} vs {kaba.spacing}")
    lam = kaba.spacing / ince.spacing
    # Iki sahne AYNI carpma noktasini gormeli; yoksa birlestirme anlamsiz.
    kayma = float(np.linalg.norm(np.asarray(kaba.impact_point)
                                 - np.asarray(ince.impact_point)))
    if kayma > kaba.spacing:
        raise ValueError(
            f"iki sahnenin çarpma noktası {kayma:.3f} m ayrı "
            f"(kaba aralık {kaba.spacing}); aynı tohum/şekil kullanılmalı")

    mp = np.asarray(ince.impact_point, dtype=np.float64)
    k_hedef = ~kaba.is_impactor
    i_hedef = ~ince.is_impactor
    d_kaba = np.linalg.norm(kaba.x - mp[None, :], axis=1)
    d_ince = np.linalg.norm(ince.x - mp[None, :], axis=1)

    sec_kaba = k_hedef & (d_kaba >= r_ince)
    sec_ince = i_hedef & (d_ince < r_ince)
    sec_mermi = ince.is_impactor
    if not np.any(sec_ince):
        raise ValueError(f"ince bölge boş: r_ince={r_ince} çok küçük")
    if not np.any(sec_kaba):
        raise ValueError(f"kaba bölge boş: r_ince={r_ince} hedefi kaplıyor")

    def _al(ad):
        return np.concatenate([getattr(ince, ad)[sec_ince],
                               getattr(kaba, ad)[sec_kaba],
                               getattr(ince, ad)[sec_mermi]])

    n_i, n_k = int(sec_ince.sum()), int(sec_kaba.sum())
    n_m = int(sec_mermi.sum())
    h = np.concatenate([
        np.full(n_i, 2.0 * ince.spacing),
        np.full(n_k, 2.0 * kaba.spacing),
        np.full(n_m, 2.0 * ince.spacing),
    ])
    is_fine = np.concatenate([np.ones(n_i, bool), np.zeros(n_k, bool),
                              np.ones(n_m, bool)])
    is_imp = np.concatenate([np.zeros(n_i + n_k, bool), np.ones(n_m, bool)])

    # KUTLE UYUSMAZLIGI: iki kafes ayni kureyi farkli doser. Olculur, yazilir.
    m_yeni = float(np.sum(_al("m")[~is_imp]))
    m_kaba = float(np.sum(kaba.m[k_hedef]))
    sapma = abs(m_yeni - m_kaba) / m_kaba

    return RefinedScene(
        x=_al("x"), v=_al("v"), m=_al("m"), alpha0=_al("alpha0"),
        Y0=_al("Y0"), h=h, is_impactor=is_imp, is_boulder=_al("is_boulder"),
        is_fine=is_fine,
        spacing_coarse=float(kaba.spacing), spacing_fine=float(ince.spacing),
        target_radius=float(kaba.target_radius),
        impact_point=mp, impact_direction=np.asarray(ince.impact_direction),
        surface_normal=np.asarray(ince.surface_normal),
        diagnostics={
            "lam": float(lam), "kutle_orani": float(lam ** 3),
            "r_ince": float(r_ince),
            "n_ince": n_i, "n_kaba": n_k, "n_mermi": n_m,
            "n_toplam": n_i + n_k + n_m,
            # Her yeri inceltseydik kac parcacik olurdu?
            "n_tumu_ince": int(np.count_nonzero(i_hedef)) + n_m,
            "tasarruf": float((int(np.count_nonzero(i_hedef)) + n_m)
                              / max(n_i + n_k + n_m, 1)),
            "hedef_kutle_sapmasi": sapma,
            "h_min": float(h.min()), "h_max": float(h.max()),
        },
    )
