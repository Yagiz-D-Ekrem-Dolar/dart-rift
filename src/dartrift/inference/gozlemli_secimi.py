"""Gözemli seçimi — **üç** parametre için üç bağımsız kısıt aramak.

## Soru

`θ = (α_b, Y₀, f)` üç boyutlu. `rank(F) ≤ min(k, d)` olduğundan `k = 2`
gözemliyle en çok iki yön öğrenilir. Peki `k = 3` yapabilir miyiz?

`observables/aday_gozlemliler` kütüğü şunu gösteriyor: **DART'ın ölçtüğü
üç bağımsız büyüklük grubu var** —

| grup | ölçüm | durum |
|---|---|---|
| `periyot_degisimi` | `ΔT` → `β` | açık |
| `ejekta_kutlesi` | LICIACube fotometrisi | açık |
| `ejekta_hiz_dagilimi` | ejekta parlaklığının azalması | açık |
| `ejekta_konisi` | koni açısı | **A95 ile kapalı** |

Yani koni olmadan bile sayı **tam tutuyor**. Bu modül "yetiyor mu"yu
**ölçer**; cevabı varsaymaz.

## İki kural

1. **Aynı gruptan iki aday seçilemez.** `e_hiz` ile `v_p50` aynı ölçümün
   iki özeti; ikisini birlikte kullanmak, olmayan bilgiyi var saymaktır
   (ADR-0058 §3'ün `R = I` tuzağının gözemli seçimindeki hâli).
2. **`gozlenen = False` olan aday seçilemez.** Model-model karşılaştırması
   gözlem yerine konmaz.

## Yöntem

Havuzun tasarımından her aday için vekil kurulur, referans noktada
Jakobyen alınır (`tanimlanabilirlik.yerel_jakobyen`) ve alt kümeler
`tanimlanabilirlik.fisher_yonleri` ile değerlendirilir — **aynı eşik**
(`FISHER_ESIGI`) ve aynı sd formülü kullanılır, yeni bir ölçüt
uydurulmaz. Seçim ölçütü **E-eniyi**: en küçük özdeğeri büyüten alt küme,
çünkü soru "en zayıf yön öğrenilebiliyor mu".

**Yerel uyarı.** Jakobyen tek noktada alınır; doğrusal olmamanın kattığı
kıvrımı görmez. Bu yüzden seçim **ön eleme**dir: son söz, bütün önsel
kutusu üzerinde koşan posteriorun kenar daralmalarıdır.
"""
from __future__ import annotations

from itertools import combinations

import numpy as np

__all__ = ["aday_jakobyeni", "kosegen_kovaryans", "alt_kume_degeri",
           "grup_kisitli_secim", "secim_raporu"]


def aday_jakobyeni(space, X, Y: dict[str, np.ndarray], u0, adlar=None,
                   *, log_al: dict[str, bool] | None = None,
                   adim: float = 1e-3) -> tuple[np.ndarray, list[str]]:
    """Her aday için vekil kur, `u0`'da Jakobyen al → `(J (k,d), adlar)`.

    `X` doğal birimde tasarım `(N, d)`; `Y[ad]` o adayın `(N,)` değerleri.
    `log_al[ad]` ise vekil `log10` üzerinde kurulur (kütle gibi dekadlara
    yayılan büyüklükler için). `u0` **birim küpte** referans nokta.

    Sonlu olmayan değer taşıyan aday **atlanmaz, hata verir** — sessiz
    eksiltme yasak (kural 8).
    """
    from .surrogate import fit_surrogate
    from .tanimlanabilirlik import yerel_jakobyen

    X = np.atleast_2d(np.asarray(X, dtype=np.float64))
    u0 = np.asarray(u0, dtype=np.float64).ravel()
    if u0.size != space.ndim:
        raise ValueError(f"u0 boyutu {u0.size}, uzay {space.ndim}")
    if np.any(u0 < 0.0) or np.any(u0 > 1.0):
        raise ValueError("u0 birim kupte olmali")
    adlar = list(adlar if adlar is not None else sorted(Y))
    if not adlar:
        raise ValueError("en az bir aday gerekir")
    log_al = log_al or {}

    satirlar = []
    for ad in adlar:
        y = np.asarray(Y[ad], dtype=np.float64).ravel()
        if y.size != X.shape[0]:
            raise ValueError(f"{ad}: {y.size} deger, {X.shape[0]} tasarim noktasi")
        if not np.all(np.isfinite(y)):
            raise ValueError(f"{ad}: sonlu olmayan deger var "
                             f"({int(np.count_nonzero(~np.isfinite(y)))} nokta)")
        if log_al.get(ad, False):
            if np.any(y <= 0.0):
                raise ValueError(f"{ad}: log_al istendi ama pozitif olmayan deger var")
            y = np.log10(y)
        v = fit_surrogate(space, X, y)
        satirlar.append(yerel_jakobyen(
            lambda u, _v=v: np.atleast_1d(_v.predict(space.from_unit(
                np.atleast_2d(u)))[0]), u0, adim=adim)[0])
    return np.vstack(satirlar), adlar


def kosegen_kovaryans(sigma) -> np.ndarray:
    """Köşegen kovaryans — **varsayım olduğu açıkça yazılı**.

    ADR-0058 §3 ölçtü: `β` ile `M_ejekta` korelasyonlu ve `ρ = 0` almak
    `α_b`'nin daralmasını `0,372 → 0,708` değiştiriyor. Yani köşegen
    kovaryans bir **kolaylık**tır; gerçek `R` havuzun vekil artıklarından
    ölçülür ve bu fonksiyonun çıktısı yalnız ön eleme içindir.
    """
    s = np.asarray(sigma, dtype=np.float64).ravel()
    if s.size == 0 or np.any(~np.isfinite(s)) or np.any(s <= 0.0):
        raise ValueError("sigma pozitif ve sonlu olmali")
    return np.diag(s ** 2)


def alt_kume_degeri(J: np.ndarray, kov: np.ndarray, indeks,
                    *, esik: float | None = None) -> dict:
    """Bir alt kümenin tanımlanabilirlik değeri (`fisher_yonleri` ile).

    Döner: `ogrenilen`, `en_kucuk_ozdeger`, `ozdegerler`, `sd_oran`
    (önsel sd'ye göre, `1` = hiç öğrenilmedi).
    """
    from .tanimlanabilirlik import FISHER_ESIGI, fisher_yonleri

    ix = list(indeks)
    if not ix:
        raise ValueError("bos alt kume")
    Js = np.asarray(J, dtype=np.float64)[ix, :]
    Ks = np.asarray(kov, dtype=np.float64)[np.ix_(ix, ix)]
    r = fisher_yonleri(Js, Ks, esik=FISHER_ESIGI if esik is None else float(esik))
    lam = np.asarray(r["ozdegerler"], dtype=np.float64)
    return {"indeks": ix, "ogrenilen": int(r["ogrenilen_yon_sayisi"]),
            "ust_sinir": int(r["ust_sinir"]), "esik": float(r["esik"]),
            "ozdegerler": lam.tolist(),
            "en_kucuk_ozdeger": float(np.min(lam)),
            "sd_oran": list(r["yaklasik_sd_oran"])}


def grup_kisitli_secim(adaylar, J: np.ndarray, kov_tam: np.ndarray,
                       *, k: int, esik: float | None = None) -> dict:
    """`k` adaylı en iyi alt küme — **grup başına en çok bir**, yalnız gözlenen.

    Ölçüt **E-eniyi**: en küçük Fisher özdeğerini büyüten alt küme. Eşitlikte
    öğrenilen yön sayısı, sonra özdeğerlerin toplamı.

    `adaylar`: `J`'nin satırlarıyla **aynı sırada** `Aday` nesneleri.
    Uygun alt küme yoksa `genel = "YETERLI GOZLENEN GRUP YOK"`.
    """
    adaylar = list(adaylar)
    J = np.atleast_2d(np.asarray(J, dtype=np.float64))
    if len(adaylar) != J.shape[0]:
        raise ValueError(f"{len(adaylar)} aday, {J.shape[0]} Jakobyen satiri")
    if int(k) < 1:
        raise ValueError("k >= 1 olmali")
    secilebilir = [i for i, a in enumerate(adaylar) if a.gozlenen]
    gruplar = {i: adaylar[i].karsilik_grubu for i in secilebilir}
    acik_grup = sorted(set(gruplar.values()))
    if len(acik_grup) < int(k):
        return {"genel": "YETERLI GOZLENEN GRUP YOK", "k": int(k),
                "acik_grup": acik_grup, "en_iyi": None}

    en_iyi = None
    for ix in combinations(secilebilir, int(k)):
        if len({gruplar[i] for i in ix}) != len(ix):
            continue                                  # ayni gruptan iki aday
        d = alt_kume_degeri(J, kov_tam, ix, esik=esik)
        anahtar = (d["en_kucuk_ozdeger"], d["ogrenilen"], sum(d["ozdegerler"]))
        if en_iyi is None or anahtar > en_iyi[0]:
            en_iyi = (anahtar, d)
    if en_iyi is None:
        return {"genel": "GRUP KISITI ALTINDA ALT KUME YOK", "k": int(k),
                "acik_grup": acik_grup, "en_iyi": None}
    d = en_iyi[1]
    return {"genel": "SECILDI", "k": int(k), "acik_grup": acik_grup,
            "adlar": [adaylar[i].ad for i in d["indeks"]],
            "gruplar": [adaylar[i].karsilik_grubu for i in d["indeks"]],
            "en_iyi": d}


def secim_raporu(adaylar, J: np.ndarray, kov_tam: np.ndarray,
                 *, d_parametre: int, esik: float | None = None) -> dict:
    """`k = 1 … d_parametre` için en iyi seçimler ve **kilitli** yargı.

    | yargı | koşul |
    |---|---|
    | `UC YON DA OGRENILIYOR` | `k = d` seçiminde `ogrenilen == d` |
    | `IKI YON OGRENILIYOR` | `ogrenilen == d − 1` |
    | `BIR YON OGRENILIYOR` | `ogrenilen == 1` |
    | `HICBIR YON OGRENILMIYOR` | `ogrenilen == 0` |

    Rapor ayrıca **en zayıf yönün** `sd_oran`'ını verir: `1,0` o yönde
    posteriorun önselden farksız olduğu anlamına gelir.
    """
    d = int(d_parametre)
    if d < 1:
        raise ValueError("d_parametre >= 1 olmali")
    basamaklar = {}
    for k in range(1, d + 1):
        basamaklar[k] = grup_kisitli_secim(adaylar, J, kov_tam, k=k, esik=esik)
    son = basamaklar[d]
    if son["en_iyi"] is None:
        return {"basamaklar": basamaklar, "d_parametre": d,
                "genel": son["genel"]}
    ogr = son["en_iyi"]["ogrenilen"]
    ad = {d: "UC YON DA OGRENILIYOR" if d == 3 else f"{d} YON OGRENILIYOR"}
    genel = ad.get(ogr) if ogr == d else (
        "HICBIR YON OGRENILMIYOR" if ogr == 0 else
        f"{ogr} YON OGRENILIYOR ({d} parametre icin YETMIYOR)")
    return {"basamaklar": basamaklar, "d_parametre": d,
            "secilen": son["adlar"], "gruplar": son["gruplar"],
            "ozdegerler": son["en_iyi"]["ozdegerler"],
            "en_kucuk_ozdeger": son["en_iyi"]["en_kucuk_ozdeger"],
            "esik": son["en_iyi"]["esik"],
            "en_zayif_sd_oran": float(max(son["en_iyi"]["sd_oran"])),
            "ogrenilen": ogr, "genel": genel,
            "uyari": ("Jakobyen TEK noktada alindi; dogrusal olmamanin "
                      "kattigi kivrim gorulmuyor. Son soz butun onsel kutusu "
                      "uzerinde kosan posteriorun kenar daralmalaridir.")}
