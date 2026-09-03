"""Şok sınavı — **kütüphane** tarafı (ADR-0049).

`scripts/sok_sinavi.py` bir tanı aracı; ileri model onu içe aktaramaz
(betikler paket değil). Bu modül aynı ölçütü kütüphanede veriyor ki
:func:`~dartrift.inference.forward.ileri_kosu_merdiven` ensemble
içinde kullanabilsin.

Ölçüt **dışarıdan**: Rankine-Hugoniot, `Us = C0 + S·up`
(`C0 = 2 600 m/s`, `S = 1,5`, bazalt). DART hızında (`6 144,9 m/s`)
sıkışma bandı `%45,6 – 74,3`.
"""
from __future__ import annotations

import numpy as np

C0_BAZALT = 2600.0
S_BAZALT = 1.5
RHO0_KATI = 2700.0
#: Bandin ALT ucunun bu kesrine ulasan kosu "sok kuruldu" sayilir.
#: `0,1` -> `%4,56`; A23'te `lam2 = 8` (`%1,68`) DUSER, `lam2 = 20`
#: (`%22,0`) GECER. Esik o iki olcumun ARASINDA ve ikisine de yakin
#: degil.
GECME_KESRI = 0.1


def hugoniot_bandi(v_carpma: float = 6144.9) -> tuple[float, float]:
    """`up ∈ [v/4, v/2]` için sıkışma bandı (yüzde)."""
    def sik(up: float) -> float:
        Us = C0_BAZALT + S_BAZALT * up
        return 100.0 * (Us / (Us - up) - 1.0)
    return sik(v_carpma / 4.0), sik(v_carpma / 2.0)


def sikisma_max(rho, alpha0) -> float:
    """En yüksek sıkışma (yüzde), her parçacığın **kendi** `α₀`'ıyla."""
    rho = np.asarray(rho, dtype=np.float64)
    a0 = np.asarray(alpha0, dtype=np.float64)
    if rho.shape != a0.shape:
        raise ValueError(f"rho {rho.shape} ile alpha0 {a0.shape} ayni olmali")
    if np.any(a0 <= 0.0):
        raise ValueError("alpha0 pozitif olmali")
    return 100.0 * float(np.max(rho * a0 / RHO0_KATI - 1.0))


#: UST SINIR (Protokol v2, rapor A35). Bandin ust kenarinin bu kati
#: asilirsa sok yakalama BOZULMUS sayilir. `1,2` payi bandin kendisinin
#: sezgisel olmasindan geliyor: `up in [v/4, v/2]` ayni malzeme ve
#: empedanstaki simetrik duzlemsel carpma icin dogru, DART'ta (aluminyum
#: mermi -> gozenekli bazalt) arayuz hizi empedans eslesmesiyle belirlenir.
#: Yani `%74,3` kesin bir tavan DEGIL; pay onu kesin sanmamak icin.
UST_PAY = 1.2


def sok_gecti(rho, alpha0, *, v_carpma: float = 6144.9,
              kesir: float = GECME_KESRI,
              ust_pay: float = UST_PAY) -> bool:
    """Bu koşuda şok kuruldu mu — ADR-0049'un ön koşulu.

    ## Protokol v2 (2026-09-03): **iki taraflı**

    v1 yalnızca alt sınırı kontrol ediyordu. `L2`'nin düşük AV kolu
    sıkışmayı `%75,65`'e çıkardı — bandın **üstünde** — ve kapı
    `SOK_VAR` dedi. Oysa Hugoniot'u aşmak şok yakalamanın
    **bozulduğunun** işareti: yetersiz yapay viskoziteyle parçacık iç
    içe geçmesi ve şok sonrası salınım.

    > Ölçüt sonuçla **çürütüldü**; sessizce sürdürmek yerine
    > versiyonlanıp gerekçelendirildi (bkz. A35).

    `ust_pay` neden `1,2` ve neden `1,0` değil: bandın üst kenarı
    (`up = v/2`) **sezgisel**, empedans eşleşmesinden türetilmiş bir
    tavan değil. Pay, o belirsizliği kapıya yazıyor.
    """
    alt, ust = hugoniot_bandi(v_carpma)
    s = sikisma_max(rho, alpha0)
    return bool(kesir * alt <= s <= ust_pay * ust)


def sok_yargisi_ayrintili(rho, alpha0, *, v_carpma: float = 6144.9,
                          kesir: float = GECME_KESRI,
                          ust_pay: float = UST_PAY) -> dict:
    """Kapının **hangi yönden** düştüğü — tanı için."""
    alt, ust = hugoniot_bandi(v_carpma)
    s = sikisma_max(rho, alpha0)
    if s < kesir * alt:
        yargi = "SOK_YOK"
    elif s > ust_pay * ust:
        yargi = "SOK_ASIRI"          # Protokol v2: fiziksel tavan asildi
    elif s >= alt:
        yargi = "SOK_VAR"
    else:
        yargi = "KISMI"
    return {"sikisma_max_yuzde": s, "bant": (alt, ust),
            "alt_esik": kesir * alt, "ust_esik": ust_pay * ust,
            "yargi": yargi, "gecti": yargi in ("KISMI", "SOK_VAR")}
