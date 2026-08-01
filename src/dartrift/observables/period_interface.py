"""Yorunge periyodu arayuzu (P3-FR-08).

DART'in dogrudan olculen sonucu beta degil, Dimorphos'un Didymos etrafindaki
YORUNGE PERIYODUNDAKI degisimdir: -33.0 +/- 1.0 dakika (Thomas ve digerleri
2023, DART sonuclari). Simulasyon beta uretir; karsilastirilabilir olmasi
icin beta -> Delta_T donusumu gerekir.

BU BIR ARAYUZDUR, TAM BIR YORUNGE COZUCUSU DEGILDIR. Yaptigi is: dairesel,
kutle merkezi etrafinda iki cisim yaklasimiyla momentum degisimini periyot
degisimine cevirmek. Sinirlari acikca yazilidir (asagida) cunku bu donusum,
projenin Hera ile karsilastirilacak sayisini uretiyor — belirsizligi
gizlenemez.

TUREV. Dairesel yorungede periyot T = 2 pi sqrt(a^3 / (G M_top)). Tegetsel
bir hiz artisi dv, yari-buyuk ekseni degistirir. Vis-viva'dan dairesel
yorunge icin:
    da/a = 2 dv / v_yor           (birinci mertebe, tegetsel itki)
    dT/T = (3/2) da/a = 3 dv / v_yor
Hedefin kazandigi hiz dv = beta * p_mermi / M_hedef.

ISARET. Momentum, Dimorphos'un yorunge hareketine TERS verilirse yorunge
kuculur ve periyot AZALIR (DART'ta olan budur; bu yuzden -33 dakika).
`along_track` bileseni bu isareti tasir ve varsayilmaz — cagiran taraf
vermek zorundadir.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

__all__ = ["PeriodChange", "DIMORPHOS_SYSTEM", "period_change", "beta_from_period_change"]

# Didymos-Dimorphos sistemi (Daly ve digerleri 2023; Thomas ve digerleri 2023)
DIMORPHOS_SYSTEM = {
    "semi_major_axis": 1189.0,        # m (carpma oncesi)
    "period_before": 11.9216 * 3600., # s (11h 55m 18s)
    "primary_mass": 5.32e11,          # kg (Didymos)
    "secondary_mass": 4.3e9,          # kg (Dimorphos)
    "measured_period_change": -33.0 * 60.0,   # s  (-33.0 dakika)
    "measured_period_change_sigma": 1.0 * 60.,  # s (+/- 1.0 dakika)
}


@dataclass(frozen=True)
class PeriodChange:
    """Momentum aktarimindan periyot degisimi."""

    delta_period: float               # s (negatif = periyot kisaldi)
    delta_period_minutes: float
    delta_v: float                    # hedefin kazandigi hiz [m/s]
    delta_a: float                    # yari-buyuk eksen degisimi [m]
    orbital_speed: float              # m/s
    beta: float
    diagnostics: dict = field(default_factory=dict)


def _orbital_speed(a: float, m_total: float, G: float) -> float:
    if a <= 0.0 or m_total <= 0.0:
        raise ValueError("yari-buyuk eksen ve toplam kutle pozitif olmali")
    return math.sqrt(G * m_total / a)


def period_change(
    beta: float,
    impactor_momentum: float,
    *,
    target_mass: float = DIMORPHOS_SYSTEM["secondary_mass"],
    primary_mass: float = DIMORPHOS_SYSTEM["primary_mass"],
    semi_major_axis: float = DIMORPHOS_SYSTEM["semi_major_axis"],
    period_before: float = DIMORPHOS_SYSTEM["period_before"],
    along_track: float = -1.0,
    G: float = 6.6743e-11,
) -> PeriodChange:
    """beta'dan yorunge periyodu degisimini hesapla.

    `along_track` gelis yonunun yorunge hizina izdusumunun ISARETIDIR
    (-1 = tam ters, yani yorungeyi yavaslatan; +1 = hizlandiran). DART icin
    -1'e yakindir. Varsayilan -1'dir ama cagiran gecerse o kullanilir.

    SINIRLAR (kullanmadan once okunmali):
      * Dairesel yorunge varsayilir; gercek disbukeylik e ~ 0.03 goz ardi edilir.
      * Birinci mertebe (dv << v_yor) — DART'ta dv/v ~ 1e-3, gecerli.
      * Yalnizca tegetsel bilesen periyodu degistirir; radyal bilesen bu
        yaklasimda periyoda katkisiz sayilir.
      * Ejektanin ikincil yorunge etkisi ve gel-git sonumleme yoktur.
    """
    if impactor_momentum <= 0.0:
        raise ValueError("mermi momentumu pozitif olmali")
    if target_mass <= 0.0:
        raise ValueError("hedef kutlesi pozitif olmali")
    if period_before <= 0.0:
        raise ValueError("baslangic periyodu pozitif olmali")
    if not (-1.0 <= along_track <= 1.0):
        raise ValueError(f"along_track [-1,1] olmali, {along_track} geldi")

    m_tot = primary_mass + target_mass
    v_orb = _orbital_speed(semi_major_axis, m_tot, G)
    dv = beta * impactor_momentum / target_mass
    dv_t = along_track * dv                      # tegetsel bilesen (isaretli)

    da = 2.0 * semi_major_axis * dv_t / v_orb
    dT = 3.0 * period_before * dv_t / v_orb

    return PeriodChange(
        delta_period=dT,
        delta_period_minutes=dT / 60.0,
        delta_v=dv,
        delta_a=da,
        orbital_speed=v_orb,
        beta=float(beta),
        diagnostics={
            "dv_over_v_orbital": dv / v_orb,
            "along_track": along_track,
            "target_mass": target_mass,
            "total_mass": m_tot,
            "semi_major_axis": semi_major_axis,
            "period_before": period_before,
            "period_after": period_before + dT,
            # Birinci mertebe gecerlilik: ikinci mertebe duzeltme ~(dv/v)^2.
            # DART icin dv/v ~ 1.4e-2, yani duzeltme ~2e-4 — ihmal edilebilir.
            # Esik %5'te tutuldu; asilirsa tam yorunge cozumu gerekir.
            "first_order_valid": bool(dv / v_orb < 0.05),
        },
    )


def beta_from_period_change(
    delta_period: float,
    impactor_momentum: float,
    *,
    target_mass: float = DIMORPHOS_SYSTEM["secondary_mass"],
    primary_mass: float = DIMORPHOS_SYSTEM["primary_mass"],
    semi_major_axis: float = DIMORPHOS_SYSTEM["semi_major_axis"],
    period_before: float = DIMORPHOS_SYSTEM["period_before"],
    along_track: float = -1.0,
    G: float = 6.6743e-11,
) -> float:
    """Ters yon: olculen Delta_T'den beta cikar (`period_change`in tersi).

    DART'in olculen -33.0 dakikasini beta'ya cevirmek icin — yani modelin
    hedefleyecegi sayiyi uretmek icin — kullanilir.
    """
    if along_track == 0.0:
        raise ValueError("along_track = 0 iken periyot degismez; beta cikarilamaz")
    m_tot = primary_mass + target_mass
    v_orb = _orbital_speed(semi_major_axis, m_tot, G)
    dv_t = delta_period * v_orb / (3.0 * period_before)
    dv = dv_t / along_track
    return float(dv * target_mass / impactor_momentum)
