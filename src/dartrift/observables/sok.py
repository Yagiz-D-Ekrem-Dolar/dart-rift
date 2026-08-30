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


def sok_gecti(rho, alpha0, *, v_carpma: float = 6144.9,
              kesir: float = GECME_KESRI) -> bool:
    """Bu koşuda şok kuruldu mu — ADR-0049'un ön koşulu."""
    alt, _ = hugoniot_bandi(v_carpma)
    return sikisma_max(rho, alpha0) >= kesir * alt
