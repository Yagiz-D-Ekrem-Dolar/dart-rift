"""Basinca bagli dayanim + von Mises return mapping (P2-FR-02, §5.2).

CPU referansi: cpu_reference/materials.py::return_mapping — ayni formuller.
Plastik is ic enerjiye gider: du = f(1-f)(S_t:S_t)/(2 G rho) >= 0.
"""

from __future__ import annotations

import warp as wp

F = wp.float64
M3 = wp.mat33d


@wp.struct
class StrengthWp:
    Y0: F
    mu_f: F
    YM: F
    shear_G: F


def make_strength_wp(p) -> StrengthWp:
    s = StrengthWp()
    s.Y0 = p.Y0
    s.mu_f = p.mu_f
    s.YM = p.YM
    s.shear_G = p.shear_G
    return s


@wp.func
def yield_stress(P: F, Y0: F, sp: StrengthWp) -> F:
    """Lundborg/Collins Y(P); cekmede Y0'a sabit (hasar D=0 bu fazda).

    Y0 PARCACIK BASINA gelir (struct'tan degil): moloz yiginlarinda bloklar
    matristen daha kohezyonludur (P3-FR-03/04) ve tek skaler bu ayrimi
    tasiyamaz. Homojen durumda dizi sabit doldurulur — tek kod yolu, dallanma
    yok, determinizm degismez.
    """
    Pp = wp.max(P, F(0.0))
    return Y0 + sp.mu_f * Pp / (F(1.0) + sp.mu_f * Pp / (sp.YM - Y0))


@wp.kernel
def return_mapping_k(
    S: wp.array(dtype=M3),
    P: wp.array(dtype=F),
    rho: wp.array(dtype=F),
    active: wp.array(dtype=wp.uint8),
    Y0: wp.array(dtype=F),
    sp: StrengthWp,
    plastic_du: wp.array(dtype=F),
):
    """S'yi akma yuzeyine cek; plastik isi TANI olarak dondur.

    `u` GUNCELLENMEZ (ADR-0012): deviatorik is zaten `dudt` icinde sayilir;
    burada ayrica eklemek cifte sayimdir. CPU referansi da ayni sozlesmeyi
    uygular (cpu_reference/solid_ref.py::_apply_strength_and_porosity).
    """
    i = wp.tid()
    if active[i] == wp.uint8(0):
        plastic_du[i] = F(0.0)
        return
    si = S[i]
    j2 = F(0.5) * wp.ddot(si, si)
    vm = wp.sqrt(F(3.0) * j2)
    y = yield_stress(P[i], Y0[i], sp)
    du = F(0.0)
    if vm > y and vm > F(0.0):
        f = y / vm
        S[i] = f * si
        du = f * (F(1.0) - f) * (F(2.0) * j2) / (F(2.0) * sp.shear_G * rho[i])
    plastic_du[i] = du


#: Kuvvet aninda "akma sinirini asti" sayilan oran esigi. Projeksiyon
#: sonrasi oran yuvarlama icinde 1 olur; 1e-9 o gurultunun cok ustunde,
#: olculen asimin (1 966 kat) cok altinda.
AKMA_ASIM_TOLERANSI = 1.0e-9


@wp.kernel
def akma_orani_k(
    S: wp.array(dtype=M3),
    P: wp.array(dtype=F),
    active: wp.array(dtype=wp.uint8),
    Y0: wp.array(dtype=F),
    sp: StrengthWp,
    oran_max: wp.array(dtype=F),
    asim_say: wp.array(dtype=wp.int32),
):
    """KUVVET ANINDA q / Y(P) -- rapor A72'nin olcusu.

    Her parcacik YALNIZ KENDI yuvasina yazar: atomik yok, sira yok,
    CPU ve GPU'da ayni sonuc. `oran_max` kosu boyunca parcacik basina
    en buyuk oran; `asim_say` esigi kac degerlendirmede astigi.
    """
    i = wp.tid()
    if active[i] == wp.uint8(0):
        return
    si = S[i]
    j2 = F(0.5) * wp.ddot(si, si)
    vm = wp.sqrt(F(3.0) * j2)
    y = yield_stress(P[i], Y0[i], sp)
    r = vm / wp.max(y, F(1.0e-300))
    if r > oran_max[i]:
        oran_max[i] = r
    if r > F(1.0) + F(AKMA_ASIM_TOLERANSI):
        asim_say[i] = asim_say[i] + 1


@wp.kernel
def dayanim_kes_k(
    S: wp.array(dtype=M3),
    rho: wp.array(dtype=F),
    u: wp.array(dtype=F),
    alpha: wp.array(dtype=F),
    active: wp.array(dtype=wp.uint8),
    u_kes: wp.array(dtype=F),
    rho0: F,
    eta_kes: F,
    kesik: wp.array(dtype=wp.uint8),
):
    """A80: buharlasmis ya da dagilmis maddede dayanim YOK.

    Olculdu (M kaba t5): u = 6e6 J/kg (u_iv = 4,7e6) ve rho 77 -> 0,001
    kg/m3'e genlesen bir parcacik |S| = sqrt(2/3) Y0'da KALDI. rho -> 0
    iken sqrt(4G/3rho) ve S/rho ivmesi sonsuza gidiyor, dt sifira iniyor,
    kosu nan. Fiziksel olarak da: u >= u_iv (Tillotson'un buharlasma
    esigi) ya da hacmi iki katina cikmis (rho*alpha/rho0 < eta_kes)
    granuler madde kayma gerilmesi TASIMAZ.

    Parcacik yalniz KENDI yuvasina yazar (atomik yok, sira yok).
    Durumsuz: madde yeniden sikisip soguyunca dayanim geri gelir
    (S sifirdan elastik olarak yeniden kurulur).
    """
    i = wp.tid()
    kesik[i] = wp.uint8(0)
    if active[i] == wp.uint8(0):
        return
    eta = rho[i] * alpha[i] / rho0
    if u[i] >= u_kes[i] or eta < eta_kes:
        kesik[i] = wp.uint8(1)
        S[i] = M3(F(0.0), F(0.0), F(0.0), F(0.0), F(0.0), F(0.0),
                  F(0.0), F(0.0), F(0.0))


@wp.kernel
def birikim_k(cum: wp.array(dtype=F), du: wp.array(dtype=F)):
    """Parcacik basina birikim -- her yuva kendi toplamini tutar."""
    i = wp.tid()
    cum[i] = cum[i] + du[i]


# ------------------------------------------------------------------------
# GERINIMLE KOHEZYON KAYBI (ADR-0050 ek; L1 Raducan & Jutzi 2022)
# ------------------------------------------------------------------------
@wp.kernel
def return_mapping_gerinim_k(
    S: wp.array(dtype=M3),
    P: wp.array(dtype=F),
    rho: wp.array(dtype=F),
    active: wp.array(dtype=wp.uint8),
    Y0: wp.array(dtype=F),
    sp: StrengthWp,
    plastic_du: wp.array(dtype=F),
    eps_p: wp.array(dtype=F),
):
    """`return_mapping_k` ile AYNI projeksiyon + esdeger plastik gerinim.

    Radyal donuste (von Mises) esdeger plastik gerinim artisi
    `Δε_p = (σ_eq,deneme − Y) / (3G)`; burada `σ_eq = vm`, `vm − Y = vm(1 − f)`.
    `eps_p` BIRIKIR (parcacik yalniz kendi yuvasina yazar). `plastic_du`
    `return_mapping_k` ile ayni formul -- iki cekirdek ayni S'yi uretir.
    """
    i = wp.tid()
    if active[i] == wp.uint8(0):
        plastic_du[i] = F(0.0)
        return
    si = S[i]
    j2 = F(0.5) * wp.ddot(si, si)
    vm = wp.sqrt(F(3.0) * j2)
    y = yield_stress(P[i], Y0[i], sp)
    du = F(0.0)
    if vm > y and vm > F(0.0):
        f = y / vm
        S[i] = f * si
        du = f * (F(1.0) - f) * (F(2.0) * j2) / (F(2.0) * sp.shear_G * rho[i])
        eps_p[i] = eps_p[i] + vm * (F(1.0) - f) / (F(3.0) * sp.shear_G)
    plastic_du[i] = du


@wp.kernel
def kohezyon_yumusat_k(
    Y0: wp.array(dtype=F),
    Y0_taban: wp.array(dtype=F),
    eps_p: wp.array(dtype=F),
    maske: wp.array(dtype=wp.uint8),
    eps_c: F,
    basamak: int,
):
    """`Y0 = Y0_taban · w(ε_p)`; `w` dogrusal `max(0, 1 − ε_p/ε_c)` ya da basamak.

    Yalniz `maske[i] != 0` parcaciklarda (or. matris). Kohezyon GERI GELMEZ:
    `ε_p` monoton birikir, `w` monoton azalir.
    """
    i = wp.tid()
    if maske[i] == wp.uint8(0):
        return
    w = F(1.0)
    if basamak != 0:
        if eps_p[i] >= eps_c:
            w = F(0.0)
    else:
        w = wp.max(F(0.0), F(1.0) - eps_p[i] / eps_c)
    Y0[i] = Y0_taban[i] * w
