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

__all__ = ["asama2_sahnesi", "asama2_sahnesi_ucseviye", "IkiAsamaSahne"]


class IkiAsamaSahne:
    """Aşama-2'ye verilecek birleşik durum + **kütle defteri**."""

    __slots__ = ("x", "v", "m", "e", "h", "alpha0", "Y0", "is_boulder",
                 "is_impactor", "mermi_kesri", "hasar", "rho", "kaynak",
                 "diagnostics")

    def __init__(self, **kw):
        for k in self.__slots__:
            setattr(self, k, kw[k])

    @property
    def n(self) -> int:
        return len(self.m)


def asama2_sahnesi(a1_durum: dict, a1_ince_maske, a1_m, a1_alpha0, a1_Y0,
                   a1_is_boulder, a2, r_ince_a1: float,
                   a1_is_impactor=None) -> IkiAsamaSahne:
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
    a1_is_impactor
        Aşama-1'in mermi maskesi. **Zorunlu**: bölge kütle
        karşılaştırmasında mermi çıkarılmalı (aşama-2'de karşılığı yok).
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
    # `is_impactor` DOGRULAMASI burada yapiliyor cunku artik kesir olarak
    # kabalastirmaya giriyor. Once asagidaydi ve indeksleme ondan once
    # geldigi icin bilgilendirici ValueError yerine IndexError atiyordu.
    if a1_is_impactor is None:
        raise ValueError("`a1_is_impactor` zorunlu — mermi kütlesi bölge "
                         "karşılaştırmasından çıkarılmalı")
    imp1 = np.asarray(a1_is_impactor, dtype=bool)
    if imp1.shape != ince.shape:
        raise ValueError(f"is_impactor {imp1.shape}, ince {ince.shape} — "
                         f"aynı olmalı")
    f_mermi1 = imp1.astype(np.float64)
    kaba = coarsen_to_sites(x1, v1, m1, e1, siteler,
                            alpha0=np.asarray(a1_alpha0)[ince],
                            Y0=np.asarray(a1_Y0)[ince],
                            is_boulder=np.asarray(a1_is_boulder)[ince],
                            mermi_kesri=f_mermi1[ince])

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
    f_mermi = np.concatenate([
        kaba["mermi_kesri"],
        np.asarray(a2.is_impactor, bool)[tut].astype(np.float64)])
    kaynak = np.concatenate([np.zeros(nk, np.int8),
                             np.ones(int(tut.sum()), np.int8)])

    m_a1 = float(m1.sum())
    m_akt = float(kaba["m"].sum())
    # BOLGE KUTLE UYUSMAZLIGI: asama-1'in ince bolgesi ile asama-2'nin
    # ATILAN bolgesi AYNI fiziksel hacmi temsil ediyor, ama iki FARKLI
    # kafesle orneklenmis. Aradaki fark bir ayriklastirma farkidir ve
    # aktarim korunumunun GORMEDIGI bir seydir.
    #
    # Mermi ayri tutuluyor: o asama-2'de zaten YOK (yuzeyin ustunde
    # basliyor ve `r_ince_a1` icinde degil).
    #
    # `is_impactor` AYRI bir parametre olarak geliyor. Ilk surumde
    # `a1_durum.get("is_impactor", ...)` yaziyordu ve `state_numpy()` o
    # anahtari HIC dondurmuyor -- yani mermi kutlesi SESSIZCE hic
    # cikarilmazdi ve uyusmazlik oldugundan buyuk gorunurdu.
    # (`imp1` yukarida dogrulandi ve kurulmustu.)
    m_mermi = float(np.asarray(a1_m, dtype=np.float64)[ince & imp1].sum())
    m_a1_hedef = m_a1 - m_mermi
    m_atilan = float(np.asarray(a2.m)[atilan].sum())
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
        "asama2_atilan_kutle": m_atilan,
        "aktarilan_kutle": m_akt,
        "aktarilan_mermi_kutlesi": m_mermi,
        # ~0 olmasi BEKLENMIYOR: iki kafes ayni hacmi farkli ornekliyor.
        # Buyukse birlesik sahnenin krater bolgesi SISTEMATIK olarak
        # fazla/eksik kutle tasir ve `beta` dogrudan etkilenir.
        "bolge_kutle_uyusmazligi": (abs(m_a1_hedef - m_atilan)
                                    / max(m_atilan, 1e-300)),
        # Asama-2 SPH ile ilerletecek: komsu yetiyor mu?
        # KOMSULAR BIRLESIK sahnede sayilir. Yalnizca aktarilanlar
        # arasinda saymak "her parcacik komsusuz" gibi YANILTICI bir
        # sonuc veriyordu (on ucusta medyan 27, <30 orani 1.000).
        "komsu": komsu_sagligi(kaba["x"], h=2.0 * s2,
                               cevre=np.asarray(a2.x)[tut]),
        "mermi_kutle_hatasi": float(kaba["mermi_kutle_hatasi"]),
        "mermi_kutlesi": float((m * f_mermi).sum()),
    })
    return IkiAsamaSahne(x=x, v=v, m=m, e=e, h=h, alpha0=alpha0, Y0=Y0,
                         is_boulder=blok, is_impactor=is_imp,
                         mermi_kesri=f_mermi,
                         # Iki seviyeli yol hasar TASIMIYOR: bu surum
                         # zaten ADR-0043 §4f ile emekli (momentumun
                         # %69'unu atiyordu). Alan sifir veriliyor ki
                         # `__slots__` eksik kalmasin ve okuyan bunun
                         # bir SECIM oldugunu gorsun.
                         hasar=np.zeros(len(m)),
                         # Yogunluk da tasinmiyor -- ayni gerekce (A24).
                         rho=None, kaynak=kaynak,
                         diagnostics=tani)


def asama2_sahnesi_ucseviye(a1, a1_durum: dict) -> IkiAsamaSahne:
    """**Üç seviyeli** aşama-1'den aşama-2'ye geçiş — momentum kaybı yok.

    ## İki seviyeli sürümün kusuru (ADR-0043 §4f)

    :func:`asama2_sahnesi` aşama-1'in **yalnızca ince** bölgesini alıp
    aşama-2'nin **dinlenmedeki** sahnesine ekliyordu. Aşama-1'in kaba
    bölgesi atılıyordu ve ölçüldü ki `t₁`'de momentumun **`%69`**'u
    tam oradaydı → `momentum_kapanis = 0,690`.

    ## Üç seviyelide sorun **ortadan kalkıyor**

    `refine_scene_ucseviye` ile `r₁ < r < r₂` bölgesi zaten aşama-2 ile
    **aynı aralıkta** (`s₂`). O yüzden:

    | bölge | ne yapılır |
    |---|---|
    | `r < r₁` (çekirdek + mermi) | Lagrange'cı **kabalaştırma** → `s₂` |
    | geri kalan | **birebir kopyalanır** (evrimleşmiş hâliyle) |

    Aşama-2'nin ayrı bir sahnesine **hiç ihtiyaç yok**; dolayısıyla
    çifte sayım da, atılan momentum da yok.

    > Momentum kapanışı artık **kabalaştırmanın** korunumuyla sınırlı
    > (`~1e-15`), geometriyle değil.
    """
    tani_a1 = getattr(a1, "diagnostics", {}) or {}
    if not tani_a1.get("ucseviye"):
        raise ValueError("`a1` üç seviyeli olmalı — `refine_scene_ucseviye` "
                         "ile kurun (iki seviyelide momentumun %69'u atılır, "
                         "ADR-0043 §4f)")
    s2 = float(tani_a1["s2"])
    ince = np.asarray(a1.is_fine, dtype=bool)
    if not ince.any():
        raise ValueError("aşama-1'de ince parçacık yok")
    for ad in ("x", "v", "u"):
        if ad not in a1_durum:
            raise KeyError(f"aşama-1 durumunda `{ad}` yok — "
                           f"anahtarlar: {sorted(a1_durum)}")
    x1 = np.asarray(a1_durum["x"], dtype=np.float64)
    v1 = np.asarray(a1_durum["v"], dtype=np.float64)
    e1 = np.asarray(a1_durum["u"], dtype=np.float64)
    if not (np.all(np.isfinite(x1)) and np.all(np.isfinite(v1))):
        raise ValueError("aşama-1 durumu sonlu değil — koşu patlamış")
    m1 = np.asarray(a1.m, dtype=np.float64)

    # MERMI KESRI: asama-1'de kimlik bir BAYRAK; kabalastirmadan sonra
    # karisim kacinilmaz oldugu icin KESIR olarak tasiniyor. Bkz.
    # `coarsen_to_sites`in `mermi_kesri` bolumu.
    f_mermi1 = np.asarray(a1.is_impactor, dtype=bool).astype(np.float64)
    # HASAR: `state_numpy` `D`yi hasar KAPALIYKEN de dondurur (sifir
    # dizisi), o yuzden kosulsuz okunur ve iki kol AYNI yoldan gecer.
    D1 = np.asarray(a1_durum.get("D", np.zeros(len(m1))), dtype=np.float64)
    if D1.shape != (len(m1),):
        raise ValueError(f"D uzunlugu {D1.shape} != {(len(m1),)}")
    # YOGUNLUK (rapor A24): asama-1'in urettigi SIKISMA buraya kadar
    # tasinmiyordu ve asama-2 cozucusu `rho`yu `rho0/alpha0` ile
    # kuruyordu -- yani sok her aktarimda SILINIYORDU. `u` tasindigi
    # icin asama-2 "sicak ama sikismamis" bir maddeyle basliyordu;
    # soklanmis madde icin bu OLANAKSIZ bir durum.
    rho1 = a1_durum.get("rho")
    if rho1 is not None:
        rho1 = np.asarray(rho1, dtype=np.float64)
        if rho1.shape != (len(m1),):
            raise ValueError(f"rho uzunlugu {rho1.shape} != {(len(m1),)}")
    kaba = coarsen_to_sites(
        x1[ince], v1[ince], m1[ince], e1[ince],
        sites_from_cloud(x1[ince], s2),
        alpha0=np.asarray(a1.alpha0)[ince], Y0=np.asarray(a1.Y0)[ince],
        is_boulder=np.asarray(a1.is_boulder)[ince],
        mermi_kesri=f_mermi1[ince],
        hasar=D1[ince],
        rho=None if rho1 is None else rho1[ince])

    dis = ~ince                       # zaten `s2` cozunurlugunde
    nk = len(kaba["m"])
    x = np.concatenate([kaba["x"], x1[dis]])
    v = np.concatenate([kaba["v"], v1[dis]])
    m = np.concatenate([kaba["m"], m1[dis]])
    e = np.concatenate([kaba["e"], e1[dis]])
    alpha0 = np.concatenate([kaba["alpha0"], np.asarray(a1.alpha0)[dis]])
    Y0 = np.concatenate([kaba["Y0"], np.asarray(a1.Y0)[dis]])
    blok = np.concatenate([kaba["is_boulder"],
                           np.asarray(a1.is_boulder, bool)[dis]])
    h = np.concatenate([np.full(nk, 2.0 * s2), np.asarray(a1.h)[dis]])
    is_imp = np.concatenate([np.zeros(nk, bool),
                             np.asarray(a1.is_impactor, bool)[dis]])
    # Kesir: kabalastirilan bolgede tasinan deger, kopyalanan bolgede
    # bayragin kendisi (orada karisim YOK, birebir kopya).
    f_mermi = np.concatenate([kaba["mermi_kesri"], f_mermi1[dis]])
    # Kopyalanan bolge hasarini BIREBIR tasir; kabalastirilan bolge
    # kutle-agirlikli ortalamayi.
    hasar = np.concatenate([kaba["hasar"], D1[dis]])
    # Kabalastirilan bolge HACIM KORUNUMLU ortalamayi, kopyalanan bolge
    # yogunlugu birebir tasir (orada birlesme YOK).
    rho = None if rho1 is None else np.concatenate([kaba["rho"], rho1[dis]])
    kaynak = np.concatenate([np.zeros(nk, np.int8),
                             np.ones(int(dis.sum()), np.int8)])

    # MOMENTUM DEFTERI: hicbir sey atilmadigi icin TAM tutmali.
    p_once = np.sum(m1[:, None] * v1, axis=0)
    p_sonra = np.sum(m[:, None] * v, axis=0)
    olcek = max(float(np.linalg.norm(p_once)), 1e-300)
    tani = dict(kaba["korunum"])
    tani.update({
        "ucseviye": True,
        "n_asama1_ince": int(ince.sum()), "n_aktarilan": nk,
        "n_kopyalanan": int(dis.sum()), "n_toplam": len(m),
        "n_asama2_atilan": 0,          # <-- artik ATILAN YOK
        "s_asama2": s2,
        "sahne_momentum_hatasi": float(np.linalg.norm(p_sonra - p_once)
                                       / olcek),
        "sahne_kutle_hatasi": abs(float(m.sum()) - float(m1.sum()))
                              / max(float(m1.sum()), 1e-300),
        "komsu": komsu_sagligi(kaba["x"], h=2.0 * s2, cevre=x1[dis]),
        # Kesir pasif skaler: toplam mermi kutlesi TAM korunmali.
        "mermi_kutle_hatasi": float(kaba["mermi_kutle_hatasi"]),
        "mermi_kutlesi": float((m * f_mermi).sum()),
        # HASAR DEFTERI: `Sum m D` TAM korunmali ve tasinan hasarin
        # buyuklugu GORUNMELI -- sifir cikarsa aktarim onu yine yutmus
        # demektir (A17'de tam bu oldu ve bir kosu boyunca fark
        # edilmedi).
        "hasar_kutle_hatasi": float(kaba["hasar_kutle_hatasi"]),
        "hasar_max": float(hasar.max()) if len(hasar) else 0.0,
        "hasar_kutle_agirlikli": float((m * hasar).sum()
                                       / max(float(m.sum()), 1e-300)),
    })
    # YOGUNLUK DEFTERI (A24): korunan buyukluk TOPLAM HACIM. Ve tasinan
    # sikismanin BUYUKLUGU gorunmeli -- sifir cikarsa aktarim soku yine
    # yutmus demektir. Hasarda tam bu olmus ve bir kosu boyunca fark
    # edilmemisti.
    if rho is not None:
        tani.update({
            "hacim_hatasi": float(kaba["hacim_hatasi"]),
            "rho_max": float(rho.max()),
            "rho_tasindi": True,
        })
    else:
        tani["rho_tasindi"] = False
    return IkiAsamaSahne(x=x, v=v, m=m, e=e, h=h, alpha0=alpha0, Y0=Y0,
                         is_boulder=blok, is_impactor=is_imp,
                         mermi_kesri=f_mermi, hasar=hasar, rho=rho,
                         kaynak=kaynak, diagnostics=tani)
