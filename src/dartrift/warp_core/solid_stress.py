"""Kati gerilme kernel'leri: hiz gradyani, Jaumann dS/dt, tam-tensor kuvvet.

CPU referansi cpu_reference/solid_ref.py ile birebir ayni denklemler
(P2 §2.1, §5.1). S = 0 iken forces_solid_3d FAZ 1 forces_3d'ye indirgenir
(test_solid_cross bunu sinar).
"""

from __future__ import annotations

import warp as wp

from .forces import BALSARA_EPS_C, artificial_visc
from .kernel_fn import grad_w3d, w3d

F = wp.float64
V3 = wp.vec3d
M3 = wp.mat33d


@wp.func
def tensile_R(P: F, rho: F, eps: F) -> F:
    """Monaghan (2000) yapay gerilme katsayisi; yalnizca cekmede (P<0) etkin."""
    if P < F(0.0):
        return -eps * P / (rho * rho)
    return F(0.0)


@wp.kernel
def velocity_gradient_3d(
    grid: wp.uint64,
    x32: wp.array(dtype=wp.vec3),
    x: wp.array(dtype=V3),
    v: wp.array(dtype=V3),
    m: wp.array(dtype=F),
    rho: wp.array(dtype=F),
    cs: wp.array(dtype=F),
    h: F,
    radius32: wp.float32,
    use_balsara: int,
    L: wp.array(dtype=M3),
    divv: wp.array(dtype=F),
    fbal: wp.array(dtype=F),
):
    """Hiz gradyani + div/curl + Balsara (cpu_reference/solid_ref ile ayni).

    Iki ayri buyukluk uretilir:
    (a) div/curl -> AV/Balsara icin, FAZ 1 ile BIREBIR ayni ayriklastirma:
        (1/rho_i) sum_j m_j (v_j - v_i) . gradW_ij
    (b) L -> gerilme evrimi icin, Randles-Libersky DUZELTMELI gradyan:
        L = [sum_j V_j (v_j-v_i) x gradW] . B^-1,  B = sum_j V_j (x_j-x_i) x gradW
        Duzeltme lineer hiz alanlarini tam yeniden urettirir (rijit donme
        objektifligi; ADR-0009). B tekilse duzeltmesiz forma dusulur.
    """
    i = wp.tid()
    xi = x[i]
    vi = v[i]
    zero = M3(F(0.0), F(0.0), F(0.0), F(0.0), F(0.0), F(0.0), F(0.0), F(0.0), F(0.0))
    l_raw = zero
    b_mat = zero
    div_acc = F(0.0)
    curl_acc = V3(F(0.0), F(0.0), F(0.0))
    q = wp.hash_grid_query(grid, x32[i], radius32)
    j = int(0)
    while wp.hash_grid_query_next(q, j):
        gw = grad_w3d(xi - x[j], h)
        vj_i = v[j] - vi
        xj_i = x[j] - xi
        vol_j = m[j] / rho[j]
        l_raw += vol_j * wp.outer(vj_i, gw)
        b_mat += vol_j * wp.outer(xj_i, gw)
        div_acc += m[j] * wp.dot(vj_i, gw)
        curl_acc += m[j] * wp.cross(vj_i, gw)
    div = div_acc / rho[i]
    curl_mag = wp.length(curl_acc) / rho[i]
    divv[i] = div
    if wp.abs(wp.determinant(b_mat)) > F(1.0e-6):
        L[i] = l_raw * wp.inverse(b_mat)
    else:
        L[i] = l_raw
    if use_balsara != 0:
        fbal[i] = wp.abs(div) / (wp.abs(div) + curl_mag + BALSARA_EPS_C * cs[i] / h)
    else:
        fbal[i] = F(1.0)


@wp.kernel
def stress_rate_3d(
    L: wp.array(dtype=M3),
    S: wp.array(dtype=M3),
    shear_G: F,
    use_jaumann: int,
    dSdt: wp.array(dtype=M3),
):
    """Jaumann objektif hiz: dS/dt = 2G eps_dev + S.spin^T + spin.S (P2 §5.1).

    use_jaumann=0 yalnizca objektiflik ablasyon testi icindir (P2-VR-01).
    """
    i = wp.tid()
    li = L[i]
    lt = wp.transpose(li)
    eps = F(0.5) * (li + lt)
    spin = F(0.5) * (li - lt)
    # iz DUZELTILMIS L'den (AV'nin divv'siyle karistirilmaz)
    tr3 = (eps[0, 0] + eps[1, 1] + eps[2, 2]) / F(3.0)
    ident = M3(F(1.0), F(0.0), F(0.0), F(0.0), F(1.0), F(0.0), F(0.0), F(0.0), F(1.0))
    dev = eps - tr3 * ident
    si = S[i]
    out = F(2.0) * shear_G * dev
    if use_jaumann != 0:
        out = out + si * wp.transpose(spin) + spin * si
    dSdt[i] = out


@wp.kernel
def kick_S_3d(
    S: wp.array(dtype=M3),
    dSdt: wp.array(dtype=M3),
    active: wp.array(dtype=wp.uint8),
    half_dt: F,
):
    i = wp.tid()
    if active[i] != wp.uint8(0):
        S[i] = S[i] + half_dt * dSdt[i]


@wp.kernel
def forces_solid_3d(
    grid: wp.uint64,
    x32: wp.array(dtype=wp.vec3),
    x: wp.array(dtype=V3),
    v: wp.array(dtype=V3),
    m: wp.array(dtype=F),
    rho: wp.array(dtype=F),
    P: wp.array(dtype=F),
    S: wp.array(dtype=M3),
    cs: wp.array(dtype=F),
    fbal: wp.array(dtype=F),
    g_ext: wp.array(dtype=V3),
    h: F,
    radius32: wp.float32,
    alpha_av: F,
    beta_av: F,
    ast_on: int,
    ast_eps: F,
    ast_n: F,
    ast_w_dp: F,
    a: wp.array(dtype=V3),
    dudt: wp.array(dtype=F),
):
    """Tam-tensor antisimetrik cift kuvveti: T = (-P I + S)/rho^2 (P2 §4.1/8).

    ast_* aciksa Monaghan (2000) yapay gerilmesi eklenir: cekme bolgesinde
    (P<0) parcacik kumelenmesini onler (ADR-0014). Yaptigi is enerji
    defterine ayni tutarlilikla girer.
    """
    i = wp.tid()
    xi = x[i]
    vi = v[i]
    ident = M3(F(1.0), F(0.0), F(0.0), F(0.0), F(1.0), F(0.0), F(0.0), F(0.0), F(1.0))
    t_i = (S[i] - P[i] * ident) / (rho[i] * rho[i])
    r_i = F(0.0)
    if ast_on != 0:
        r_i = tensile_R(P[i], rho[i], ast_eps)
    acc = V3(F(0.0), F(0.0), F(0.0))
    du = F(0.0)
    q = wp.hash_grid_query(grid, x32[i], radius32)
    j = int(0)
    while wp.hash_grid_query_next(q, j):
        rij = xi - x[j]
        r = wp.length(rij)
        qq = r / h
        if qq < F(2.0) and r > F(1.0e-12):
            gw = grad_w3d(rij, h)
            vij = vi - v[j]
            vr = wp.dot(vij, rij)
            c_bar = F(0.5) * (cs[i] + cs[j])
            rho_bar = F(0.5) * (rho[i] + rho[j])
            f_bar = F(0.5) * (fbal[i] + fbal[j])
            pi_ij = artificial_visc(vr, r * r, h, c_bar, rho_bar, f_bar, alpha_av, beta_av)
            t_j = (S[j] - P[j] * ident) / (rho[j] * rho[j])
            tgw = (t_i + t_j) * gw
            acc += m[j] * tgw - (m[j] * pi_ij) * gw
            du += F(-0.5) * m[j] * wp.dot(vij, tgw) + F(0.5) * m[j] * pi_ij * wp.dot(vij, gw)
            if ast_on != 0:
                r_pair = (r_i + tensile_R(P[j], rho[j], ast_eps)) * wp.pow(
                    w3d(qq, h) / ast_w_dp, ast_n
                )
                acc += (-m[j] * r_pair) * gw
                du += F(0.5) * m[j] * r_pair * wp.dot(vij, gw)
    a[i] = acc + g_ext[i]
    dudt[i] = du
