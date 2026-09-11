"""Üç çözünürlükte yakınsama — Richardson + önceden seçilmiş tolerans.

> `scripts/yakinsama_raporu.py` AYRI ve kilitli bir betik (Protokol R,
> `f865a7e`). Bu dosya onun yerine geçmez; uzmanın Soru 18 formüllerini
> ve tolerans kapısını üçüncü seviye (ince merdiven) kampanyası için
> kuruyor.

Uzman (Soru 18):

- *"Üç nokta, `x(h) = x_* + C h^p` modelindeki üç bilinmeyeni
  kestirmek için asgari sayıdır; asimptotik rejimi kanıtlamaz."*
- *"Farklar aynı işarette, anlamlı büyüklükte ve öncü hata modeli uygun
  olmalı. Salınımlı/çok küçük farklarda formülü zorlamayın."*
- *"'2 sigma altında' yakınsama/eşdeğerlik kanıtı değildir: hata çubuğu
  büyüdükçe geçmek kolaylaşır. Bilimsel tolerans önceden seçilmeli;
  sayısal farkın belirsizlik aralığı bu toleransın içine girmeli."*
- *"GCI'yi kendiliğinden Gauss sigma'sı saymayın."*

Eşit oran `r` için:

    p   = log[(x_c − x_m)/(x_m − x_f)] / log r
    x_* = x_f + (x_f − x_m)/(r^p − 1)

Yakınsama yargısı **tolerans kapısıdır**, sigma testi değil:
`|x_f − x_*| + k σ_f ≤ δ` ise YAKINSAMIŞ. σ büyüdükçe geçmek
ZORLAŞIR — uzmanın uyardığı ters teşviki kapatır.
"""
from __future__ import annotations

import math

#: Seviyeler arası `h` oranı (merdivenler bunu koruyor).
ORAN = 2.0
#: Farkların gürültüden ayrışması için gereken kat.
ANLAMLI_SIGMA = 2.0
#: Öncü hata mertebesi için makul aralık (SPH + şok: 0,5 – 4).
P_ARALIGI = (0.5, 4.0)
#: Roache GCI güvenlik katsayısı (üç seviye).
FS_UC = 1.25
#: Tolerans kapısında belirsizlik çarpanı.
TOLERANS_K = 2.0


def richardson(x_c: float, x_m: float, x_f: float, *, s_c: float = 0.0,
               s_m: float = 0.0, s_f: float = 0.0, oran: float = ORAN) -> dict:
    """Üç eşleşmiş seviyeden `p`, `x_*`, GCI ve UYGUNLUK durumu."""
    d1 = x_c - x_m
    d2 = x_m - x_f
    sig1 = math.hypot(s_c, s_m)
    sig2 = math.hypot(s_m, s_f)
    out = {"d_kaba_orta": d1, "d_orta_ince": d2, "sigma_d1": sig1,
           "sigma_d2": sig2, "p": float("nan"), "x_yildiz": float("nan"),
           "gci_ince": float("nan"), "hata_ince": float("nan")}
    if d1 == 0.0 or d2 == 0.0 or d1 * d2 < 0.0:
        out["durum"] = "SALINIMLI ya da DUZ"
        return out
    if abs(d1) <= ANLAMLI_SIGMA * sig1 or abs(d2) <= ANLAMLI_SIGMA * sig2:
        out["durum"] = "GURULTU ICINDE"
        return out
    p = math.log(d1 / d2) / math.log(oran)
    out["p"] = p
    if not (P_ARALIGI[0] <= p <= P_ARALIGI[1]):
        out["durum"] = "ASIMPTOTIK DEGIL"
        return out
    payda = oran ** p - 1.0
    out["x_yildiz"] = x_f + (x_f - x_m) / payda
    out["hata_ince"] = abs(x_f - out["x_yildiz"])
    out["gci_ince"] = FS_UC * abs(d2) / payda
    out["durum"] = "UYGUN"
    return out


def yakinsama_yargisi(r: dict, tolerans: float, s_f: float) -> dict:
    """Tolerans kapısı: `|x_f − x_*| + k σ_f ≤ δ`."""
    if tolerans <= 0.0:
        raise ValueError("tolerans pozitif ve KOSUDAN ONCE secilmis olmali")
    if r.get("durum") != "UYGUN":
        return {"karar": "OKUNMAZ", "sebep": r.get("durum", "?")}
    ust = r["hata_ince"] + TOLERANS_K * s_f
    return {"karar": "YAKINSAMIS" if ust <= tolerans else "YAKINSAMAMIS",
            "hata_ust_siniri": ust, "tolerans": tolerans,
            "gci_ince_bilgi": r["gci_ince"]}


def iki_noktadan_sinirlar(x_c: float, x_m: float, ps=(1.0, 2.0),
                          oran: float = ORAN) -> dict:
    """VARSAYIMLI iki nokta kestirimi — sonuç değil, duyarlılık örneği.

    Uzman: *"İki noktadan varsayımsız sonlu bir sınır yok."*
    """
    return {p: x_m + (x_m - x_c) / (oran ** p - 1.0) for p in ps}
