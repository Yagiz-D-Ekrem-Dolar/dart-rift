"""Grady-Kipp hasar — GPU cekirdegi (Benz & Asphaug 1995).

CPU referansi: `cpu_reference/damage_ref.py` — ayni formuller, ayni sira.
Kusur TOHUMLAMASI GPU'da yapilmaz: bir kez, kurulumda, CPU'da deterministik
olarak uretilir ve dizi olarak gecirilir. Rasgeleligi GPU'ya tasimak
determinizmi kaybettirirdi (ADR-0004).
"""

from __future__ import annotations

import warp as wp

F = wp.float64
M3 = wp.mat33d


@wp.struct
class DamageWp:
    m_weibull: F
    crack_speed_frac: F
    r_s: F            # parcacigin etkin yaricapi [m]
    youngs_E: F       # Young modulu [Pa]


def make_damage_wp(p, r_s: float, youngs_E: float) -> DamageWp:
    d = DamageWp()
    d.m_weibull = p.m_weibull
    d.crack_speed_frac = p.crack_speed_frac
    d.r_s = r_s
    d.youngs_E = youngs_E
    return d


@wp.func
def max_principal_stress(P: F, S: M3) -> F:
    """sigma = -P I + S'nin EN BUYUK ozdegeri (cekme POZITIF).

    Simetrik 3x3 icin kapali form (Smith 1961). Iteratif cozucu YOK: sabit
    islem sayisi -> determinizm (ADR-0002).
    """
    a00 = S[0, 0] - P
    a11 = S[1, 1] - P
    a22 = S[2, 2] - P
    a01 = F(0.5) * (S[0, 1] + S[1, 0])
    a02 = F(0.5) * (S[0, 2] + S[2, 0])
    a12 = F(0.5) * (S[1, 2] + S[2, 1])

    p1 = a01 * a01 + a02 * a02 + a12 * a12
    q = (a00 + a11 + a22) / F(3.0)
    if p1 <= F(0.0):
        # kosegen: en buyuk kosegen eleman
        return wp.max(a00, wp.max(a11, a22))
    p2 = ((a00 - q) * (a00 - q) + (a11 - q) * (a11 - q)
          + (a22 - q) * (a22 - q) + F(2.0) * p1)
    p = wp.sqrt(p2 / F(6.0))
    if p <= F(0.0):
        return q
    ip = F(1.0) / p
    b00 = ip * (a00 - q)
    b11 = ip * (a11 - q)
    b22 = ip * (a22 - q)
    b01 = ip * a01
    b02 = ip * a02
    b12 = ip * a12
    detb = (b00 * (b11 * b22 - b12 * b12)
            - b01 * (b01 * b22 - b12 * b02)
            + b02 * (b01 * b12 - b11 * b02))
    r = F(0.5) * detb
    if r <= F(-1.0):
        phi = F(3.14159265358979323846) / F(3.0)
    elif r >= F(1.0):
        phi = F(0.0)
    else:
        phi = wp.acos(r) / F(3.0)
    return q + F(2.0) * p * wp.cos(phi)


@wp.func
def local_strain(P: F, S: M3, dp: DamageWp) -> F:
    """eps = max(sigma_max, 0) / E — yalnizca cekme kusur acar."""
    return wp.max(max_principal_stress(P, S), F(0.0)) / dp.youngs_E


@wp.func
def activated_flaws(strain: F, eps_min: F, n_flaws: F, dp: DamageWp) -> F:
    """Verili gerinimde acilmis kusur sayisi; kusur sayisiyla sinirli."""
    if eps_min <= F(0.0) or n_flaws <= F(0.0):
        return F(0.0)
    e = wp.max(strain, F(0.0))
    oran = e / eps_min
    if oran <= F(1.0):
        return F(0.0)
    n_act = wp.pow(oran, dp.m_weibull)
    return wp.min(n_act, n_flaws)


@wp.kernel
def damage_rate_k(
    P: wp.array(dtype=F),
    S: wp.array(dtype=M3),
    eps_min: wp.array(dtype=F),
    n_flaws: wp.array(dtype=F),
    cs: wp.array(dtype=F),
    active: wp.array(dtype=wp.uint8),
    dp: DamageWp,
    dDdt_cbrt: wp.array(dtype=F),
    strain_out: wp.array(dtype=F),
):
    """d(D^(1/3))/dt = n_aktif * c_g / R_s. YALNIZCA hizi yazar.

    Hiz, alan degerlendirmesinde DONDURULUR ve tekmelerde uygulanir —
    rho/u/S ile ayni trapez yolundan gecsin diye (ADR-0007).

    Gerinim, HASARSIZ (ham) gerilmeden hesaplanir: hasar uygulanmis
    gerilmeden hesaplamak geri besleme dogurur ve hasar kendini yavaslatir.
    """
    i = wp.tid()
    if active[i] == wp.uint8(0):
        dDdt_cbrt[i] = F(0.0)
        strain_out[i] = F(0.0)
        return
    eps = local_strain(P[i], S[i], dp)
    strain_out[i] = eps
    n_act = activated_flaws(eps, eps_min[i], n_flaws[i], dp)
    dDdt_cbrt[i] = n_act * dp.crack_speed_frac * cs[i] / dp.r_s


@wp.kernel
def accumulate_damage_k(
    D_cbrt: wp.array(dtype=F),
    dDdt_cbrt: wp.array(dtype=F),
    D: wp.array(dtype=F),
    active: wp.array(dtype=wp.uint8),
    dt: F,
):
    """D^(1/3) ilerlet, D'yi turet, [0,1]'e kis ve MONOTONLUGU zorla.

    Hasar geri donmez: kirilan kaya kendini onarmaz. Bu fiziksel bir sarttir;
    sayisal gurultu D'yi dusurmeye kalkarsa engellenir.
    """
    i = wp.tid()
    if active[i] == wp.uint8(0):
        return
    c = D_cbrt[i] + dt * dDdt_cbrt[i]
    if c < F(0.0):
        c = F(0.0)
    if c > F(1.0):
        c = F(1.0)
    if c < D_cbrt[i]:          # geri donusum yok
        c = D_cbrt[i]
    D_cbrt[i] = c
    D[i] = c * c * c


@wp.kernel
def apply_damage_k(
    P: wp.array(dtype=F),
    S: wp.array(dtype=M3),
    D: wp.array(dtype=F),
    active: wp.array(dtype=wp.uint8),
    P_eff: wp.array(dtype=F),
    S_eff: wp.array(dtype=M3),
):
    """TASINAN gerilmeyi hesapla: yalnizca cekme zayiflar, basma degismez.

        P < 0 -> (1-D) P ;  P >= 0 aynen kalir ;  S -> (1-D) S

    Basmayi da zayiflatmak kraterlesmeyi yanlis yapardi: sok onunde malzeme
    basma altindadir ve orada dayanim kaybi fiziksel degildir.

    DURUMU DEGISTIRMEZ — AYRI DIZILERE YAZAR. Bu kritik: `S` bir DURUM
    degiskenidir (`kick_S_3d` ile integre edilir, hicbir yerde yeniden
    hesaplanmaz). Onceki surum `S[i] = f * S[i]` diye YERINDE carpiyordu ve
    `_eval()` adim basina IKI kez cagrildigi icin S her adimda (1-D)^2 ile
    kuculuyordu — birikimli olarak.

    Olculdu (D = 0.5 sabit, hicbir fiziksel evrim yokken):
        baslangic S = 1.0e7
        1./2./3./4. _eval() -> 5.0e6 / 2.5e6 / 1.25e6 / 6.25e5
        5 adim sonra          -> 4.88e3   (olmasi gereken 5.0e6, 1000 kat sapma)
    Yani deviatorik gerilme ussel olarak yok ediliyordu. `P` kurtuluyordu
    cunku EOS onu her eval yeniden hesapliyor; `S` hesaplamiyor.
    """
    i = wp.tid()
    if active[i] == wp.uint8(0):
        P_eff[i] = P[i]
        S_eff[i] = S[i]
        return
    d = D[i]
    if d <= F(0.0):
        P_eff[i] = P[i]
        S_eff[i] = S[i]
        return
    if d > F(1.0):
        d = F(1.0)
    f = F(1.0) - d
    if P[i] < F(0.0):
        P_eff[i] = f * P[i]
    else:
        P_eff[i] = P[i]
    S_eff[i] = f * S[i]
