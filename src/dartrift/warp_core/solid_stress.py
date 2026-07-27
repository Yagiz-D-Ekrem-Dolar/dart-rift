"""Kati gerilme kernel'leri: hiz gradyani, Jaumann dS/dt, tam-tensor kuvvet.

CPU referansi cpu_reference/solid_ref.py ile birebir ayni denklemler
(P2 §2.1, §5.1). S = 0 iken forces_solid_3d FAZ 1 forces_3d'ye indirgenir
(test_solid_cross bunu sinar).
"""

from __future__ import annotations

import warp as wp

from .forces import BALSARA_EPS_C, artificial_visc
from .kernel_fn import grad_w3d

F = wp.float64
V3 = wp.vec3d
M3 = wp.mat33d


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
    i = wp.tid()
    xi = x[i]
    vi = v[i]
    li = M3(F(0.0), F(0.0), F(0.0), F(0.0), F(0.0), F(0.0), F(0.0), F(0.0), F(0.0))
    q = wp.hash_grid_query(grid, x32[i], radius32)
    j = 0
    while wp.hash_grid_query_next(q, j):
        gw = grad_w3d(xi - x[j], h)
        li += (m[j] / rho[j]) * wp.outer(v[j] - vi, gw)
    L[i] = li
    div = li[0, 0] + li[1, 1] + li[2, 2]
    divv[i] = div
    cx = li[2, 1] - li[1, 2]
    cy = li[0, 2] - li[2, 0]
    cz = li[1, 0] - li[0, 1]
    curl_mag = wp.sqrt(cx * cx + cy * cy + cz * cz)
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
    a: wp.array(dtype=V3),
    dudt: wp.array(dtype=F),
):
    """Tam-tensor antisimetrik cift kuvveti: T = (-P I + S)/rho^2 (P2 §4.1/8)."""
    i = wp.tid()
    xi = x[i]
    vi = v[i]
    ident = M3(F(1.0), F(0.0), F(0.0), F(0.0), F(1.0), F(0.0), F(0.0), F(0.0), F(1.0))
    t_i = (S[i] - P[i] * ident) / (rho[i] * rho[i])
    acc = V3(F(0.0), F(0.0), F(0.0))
    du = F(0.0)
    q = wp.hash_grid_query(grid, x32[i], radius32)
    j = 0
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
    a[i] = acc + g_ext[i]
    dudt[i] = du
