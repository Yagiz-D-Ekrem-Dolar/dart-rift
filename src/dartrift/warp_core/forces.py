"""Antisimetrik kuvvet + tutarli enerji + Monaghan/Balsara AV (P1-FR-03/05).

KRITIK sozlesme (DR-RIFT-P1 §2.3): ivme ve du/dt AYNI simetrik `term` ile
kurulur; f_ij = -f_ji bit-yakin saglanir, momentum makine hassasiyetine
yakin korunur ve enerji formu momentumla tutarlidir.
"""

from __future__ import annotations

import warp as wp

from ..cpu_reference.sph_ref import AV_EPS, BALSARA_EPS
from .kernel_fn import grad_w1d, grad_w3d

F = wp.float64
V3 = wp.vec3d

# Yakalanan Python float'lar f32'ye duser; FP64 sabitler tipli gomulur.
AV_EPS_C = wp.constant(F(float(AV_EPS)))
BALSARA_EPS_C = wp.constant(F(float(BALSARA_EPS)))


@wp.func
def artificial_visc(
    vr: F, r2: F, h: F, c_bar: F, rho_bar: F, f_bar: F, alpha: F, beta: F
) -> F:
    """Monaghan Pi_ij (Balsara olcekli); yaklasan ciftlerde etkin (§2.5)."""
    if vr >= F(0.0):
        return F(0.0)
    mu = h * vr / (r2 + AV_EPS_C * h * h)
    return f_bar * (-alpha * c_bar * mu + beta * mu * mu) / rho_bar


@wp.kernel
def divcurl_3d(
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
    divv: wp.array(dtype=F),
    fbal: wp.array(dtype=F),
):
    i = wp.tid()
    xi = x[i]
    vi = v[i]
    div = F(0.0)
    curl = V3(F(0.0), F(0.0), F(0.0))
    q = wp.hash_grid_query(grid, x32[i], radius32)
    j = int(0)
    while wp.hash_grid_query_next(q, j):
        gw = grad_w3d(xi - x[j], h)
        vji = v[j] - vi
        div += m[j] * wp.dot(vji, gw)
        curl += m[j] * wp.cross(vji, gw)
    div = div / rho[i]
    curl_mag = wp.length(curl) / rho[i]
    divv[i] = div
    if use_balsara != 0:
        fbal[i] = wp.abs(div) / (wp.abs(div) + curl_mag + BALSARA_EPS_C * cs[i] / h)
    else:
        fbal[i] = F(1.0)


@wp.kernel
def forces_3d(
    grid: wp.uint64,
    x32: wp.array(dtype=wp.vec3),
    x: wp.array(dtype=V3),
    v: wp.array(dtype=V3),
    m: wp.array(dtype=F),
    rho: wp.array(dtype=F),
    P: wp.array(dtype=F),
    cs: wp.array(dtype=F),
    fbal: wp.array(dtype=F),
    h: F,
    radius32: wp.float32,
    alpha_av: F,
    beta_av: F,
    a: wp.array(dtype=V3),
    dudt: wp.array(dtype=F),
):
    i = wp.tid()
    xi = x[i]
    vi = v[i]
    p_over_i = P[i] / (rho[i] * rho[i])
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
            term = p_over_i + P[j] / (rho[j] * rho[j]) + pi_ij
            acc += (-m[j] * term) * gw
            du += F(0.5) * m[j] * term * wp.dot(vij, gw)
    a[i] = acc
    dudt[i] = du


@wp.kernel
def forces_1d(
    x: wp.array(dtype=F),
    v: wp.array(dtype=F),
    m: wp.array(dtype=F),
    rho: wp.array(dtype=F),
    P: wp.array(dtype=F),
    cs: wp.array(dtype=F),
    n: int,
    h: F,
    alpha_av: F,
    beta_av: F,
    a: wp.array(dtype=F),
    dudt: wp.array(dtype=F),
):
    i = wp.tid()
    xi = x[i]
    vi = v[i]
    p_over_i = P[i] / (rho[i] * rho[i])
    acc = F(0.0)
    du = F(0.0)
    for j in range(n):
        dx = xi - x[j]
        r = wp.abs(dx)
        qq = r / h
        if qq < F(2.0) and r > F(1.0e-12):
            gw = grad_w1d(dx, h)
            dv = vi - v[j]
            vr = dv * dx
            c_bar = F(0.5) * (cs[i] + cs[j])
            rho_bar = F(0.5) * (rho[i] + rho[j])
            # 1B'de kesme yok -> Balsara f=1 (sph_ref ile ayni sozlesme)
            pi_ij = artificial_visc(vr, r * r, h, c_bar, rho_bar, F(1.0), alpha_av, beta_av)
            term = p_over_i + P[j] / (rho[j] * rho[j]) + pi_ij
            acc += -m[j] * term * gw
            du += F(0.5) * m[j] * term * dv * gw
    a[i] = acc
    dudt[i] = du


@wp.kernel
def divv_1d(
    x: wp.array(dtype=F),
    v: wp.array(dtype=F),
    m: wp.array(dtype=F),
    rho: wp.array(dtype=F),
    n: int,
    h: F,
    divv: wp.array(dtype=F),
):
    i = wp.tid()
    xi = x[i]
    vi = v[i]
    div = F(0.0)
    for j in range(n):
        dx = xi - x[j]
        div += m[j] * (v[j] - vi) * grad_w1d(dx, h)
    divv[i] = div / rho[i]
