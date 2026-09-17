"""Blokların **çözünürlük** tanısı (ADR-0050).

Raducan ve diğ. 2022 (*A&A* 665, L10; `docs/LITERATUR-DART-SIMULASYONLARI.md`
L8) moloz yığınında en küçük çözülebilen blok yarıçapını `2,5 m` olarak
alıyor ve bunu **blok başına ~30 SPH parçacığı** ile gerekçelendiriyor. Bizim
merdivenimizde çarpma noktasından uzakta aralık `5,6 m`'ye kadar çıkıyor; orada
`1,7 – 6,5 m` yarıçaplı bloklar **çözülmüyor** olabilir.

Bu bir **tanı**dır, kapı değil: sayı raporlanır, koşu düşürülmez. Ama
"bloklar modelde var" demekle "bloklar çözülmüş" demek aynı şey değildir ve
bu ayrım yazılı olmalıdır.
"""
from __future__ import annotations

import numpy as np

__all__ = ["blok_cozunurluk_tanisi", "ASGARI_PARCACIK"]

#: Blok başına asgari parçacık (L8'in çözünürlük gerekçesi).
ASGARI_PARCACIK = 30


def blok_cozunurluk_tanisi(x, m, merkezler, yaricaplar, *,
                           asgari_parcacik: int = ASGARI_PARCACIK) -> dict:
    """Her blokta kaç parçacık var; kaç blok **çözülmemiş**.

    Parameters
    ----------
    x, m
        Parçacık konumları `(N,3)` ve kütleleri `(N,)`.
    merkezler, yaricaplar
        Blok küreleri (`BoulderField.centers`, `.radii`).

    Döner: blok sayısı, parçacık sayılarının en küçük/ortanca/en büyüğü,
    çözülmemiş blok sayısı ve bunların **blok kütlesindeki payı**.
    """
    x = np.asarray(x, dtype=np.float64)
    m = np.asarray(m, dtype=np.float64)
    c = np.atleast_2d(np.asarray(merkezler, dtype=np.float64))
    r = np.atleast_1d(np.asarray(yaricaplar, dtype=np.float64))
    if len(c) != len(r):
        raise ValueError(f"merkez {len(c)} ve yaricap {len(r)} sayisi ayni olmali")
    if asgari_parcacik < 1:
        raise ValueError("asgari_parcacik >= 1 olmali")
    if len(r) == 0:
        return {"n_blok": 0, "n_parcacik_min": 0, "n_parcacik_ortanca": 0.0,
                "n_parcacik_max": 0, "n_cozulmemis": 0,
                "cozulmemis_kutle_payi": 0.0,
                "asgari_parcacik": int(asgari_parcacik)}
    sayilar = np.empty(len(r), dtype=np.int64)
    kutleler = np.empty(len(r), dtype=np.float64)
    for i, (ci, ri) in enumerate(zip(c, r, strict=True)):
        ic = np.sum((x - ci[None, :]) ** 2, axis=1) <= ri * ri
        sayilar[i] = int(np.count_nonzero(ic))
        kutleler[i] = float(m[ic].sum())
    az = sayilar < int(asgari_parcacik)
    top = float(kutleler.sum())
    return {
        "n_blok": int(len(r)),
        "n_parcacik_min": int(sayilar.min()),
        "n_parcacik_ortanca": float(np.median(sayilar)),
        "n_parcacik_max": int(sayilar.max()),
        "n_cozulmemis": int(az.sum()),
        "cozulmemis_kutle_payi": float(kutleler[az].sum() / top) if top > 0.0
        else float("nan"),
        "asgari_parcacik": int(asgari_parcacik),
        "yaricap_min_m": float(r.min()),
        "yaricap_max_m": float(r.max()),
    }
