"""Oz-yercekimi benchmark'lari (P2-VR-05/06).

- Iki-cisim dairesel yorunge: enerji/faz drifti sinirli; BH = direct (2 cisim).
- Duzgun kure: g(r) analitik ic/dis alanla eslesir; BH vs direct alan hatasi.
- Soguk collapse: SPH + yercekimi, enerji muhasebesi (E_kin+E_int+E_pot) kapanir.
"""

from __future__ import annotations

import numpy as np

from ..cpu_reference.gravity_ref import bh_accel, build_octree, compute_gravity_direct
from ..cpu_reference.materials import (
    GravityParams,
    MaterialParams,
    PorosityParams,
    StrengthParams,
)
from ..cpu_reference.solid_ref import SolidState, run_solid
from ..cpu_reference.sph_ref import RefParams
from ..rng import element_generator


def run_two_body(n_orbits: float = 20.0, steps_per_orbit: int = 200) -> dict:
    """Esit kutleli dairesel ikili; sabit-dt leapfrog (KDK) — drift sinirli."""
    G = 1.0
    m1 = m2 = 0.5
    d = 1.0
    x = np.array([[-0.5 * d, 0, 0], [0.5 * d, 0, 0]], dtype=np.float64)
    v_circ = np.sqrt(G * (m1 + m2) / d) * 0.5
    v = np.array([[0, -v_circ, 0], [0, v_circ, 0]], dtype=np.float64)
    m = np.array([m1, m2])
    T = 2.0 * np.pi * d / (2.0 * v_circ)
    dt = T / steps_per_orbit
    n_steps = int(round(n_orbits * steps_per_orbit))

    def energy(x, v):
        ke = 0.5 * np.sum(m * np.sum(v * v, axis=1))
        r = np.linalg.norm(x[0] - x[1])
        return ke - G * m1 * m2 / r

    g, _ = compute_gravity_direct(x, m, G, 0.0)
    e0 = energy(x, v)
    e_max_err = 0.0
    for _ in range(n_steps):
        v += 0.5 * dt * g
        x += dt * v
        g, _ = compute_gravity_direct(x, m, G, 0.0)
        v += 0.5 * dt * g
        e_max_err = max(e_max_err, abs(energy(x, v) - e0) / abs(e0))
    r_final = float(np.linalg.norm(x[0] - x[1]))
    return {
        "n_orbits": n_orbits,
        "energy_max_rel_err": e_max_err,
        "radius_drift_rel": abs(r_final - d) / d,
    }


def _uniform_sphere(n: int, R: float = 1.0, seed: int = 424243) -> np.ndarray:
    pts = np.empty((n, 3))
    k = i = 0
    while k < n:
        g = element_generator(seed, "particles", i)
        p = 2.0 * g.random(3) - 1.0
        if p @ p <= 1.0:
            pts[k] = p * R
            k += 1
        i += 1
    return pts


def run_uniform_sphere(n: int = 4000, theta: float = 0.5) -> dict:
    """Duzgun kure alani: binlenmis g(r) vs analitik; BH vs direct hatasi."""
    G = 1.0
    R = 1.0
    M = 1.0
    x = _uniform_sphere(n, R)
    m = np.full(n, M / n)
    eps = 0.02
    g_dir, phi_dir = compute_gravity_direct(x, m, G, eps)
    tree = build_octree(x, m)
    g_bh, phi_bh = bh_accel(x, np.arange(n), tree, x, m, G, eps, theta)

    # BH ve dogrudan alan farki
    gmag = np.sqrt(np.sum(g_dir * g_dir, axis=1))
    diff = np.sqrt(np.sum((g_bh - g_dir) ** 2, axis=1))
    bh_rel = float(np.max(diff / np.maximum(gmag, 1e-12)))
    bh_rel_med = float(np.median(diff / np.maximum(gmag, 1e-12)))

    # analitik: g(r) = G M r / R^3 (ic). Tek-parcacik alani Poisson gurultusune
    # gomulur (~%10, N=4000); dogru olcum KABUK-ORTALAMALI radyal bilesendir.
    r = np.sqrt(np.sum(x * x, axis=1))
    g_rad = -np.einsum("id,id->i", g_dir, x) / np.maximum(r, 1e-12)  # ice dogru +
    edges = np.linspace(0.3 * R, 0.9 * R, 9)
    shell_err = []
    for k in range(len(edges) - 1):
        sel = (r >= edges[k]) & (r < edges[k + 1])
        if np.count_nonzero(sel) < 50:
            continue
        r_mid = float(np.mean(r[sel]))
        g_shell = float(np.mean(g_rad[sel]))
        g_exact = G * M * r_mid / R**3
        shell_err.append(abs(g_shell - g_exact) / g_exact)
    # tani: tek-parcacik gurultu duzeyi (esik konmaz, raporlanir)
    g_exact_all = G * M * r / R**3
    sel_band = (r > 0.3 * R) & (r < 0.9 * R)
    noise = np.abs(gmag[sel_band] - g_exact_all[sel_band]) / g_exact_all[sel_band]
    return {
        "n": n,
        "theta": theta,
        "bh_vs_direct_max_rel": bh_rel,
        "bh_vs_direct_median_rel": bh_rel_med,
        "shell_mean_rel_err_max": float(np.max(shell_err)),
        "shell_mean_rel_err_avg": float(np.mean(shell_err)),
        "particle_noise_mean_rel": float(np.mean(noise)),
        "n_nodes": tree.n_nodes,
    }


def run_cold_collapse(n: int = 500, t_frac: float = 0.6) -> dict:
    """Soguk gaz kuresi cokusu (SPH + yercekimi): enerji muhasebesi kapanir.

    Baslangicta hidrostatik olmayan soguk kure; serbest-dusme zamaninin
    t_frac'ine kadar kosulur (sok olusumundan once). E_tot = KE+IE+PE korunur.
    """
    G = 1.0
    R = 1.0
    M = 1.0
    rho_mean = 3.0 * M / (4.0 * np.pi * R**3)
    t_ff = np.sqrt(3.0 * np.pi / (32.0 * G * rho_mean))
    x = _uniform_sphere(n, R)
    m = np.full(n, M / n)
    h = 2.0 * (4.0 * np.pi / 3.0 / n) ** (1.0 / 3.0) * R  # ADR-0013
    mat = MaterialParams(
        eos="ideal_gas", gamma=5.0 / 3.0,
        strength=StrengthParams(enabled=False),
        porosity=PorosityParams(enabled=False),
        gravity=GravityParams(enabled=True, G=G, eps=0.05 * R, mode="direct"),
    )
    num = RefParams(cfl=0.2)
    state = SolidState(x=x, v=np.zeros_like(x), m=m, u=np.full(n, 1.0e-4),
                       h=h, active=np.ones(n, bool))
    diag = run_solid(state, mat, num, t_frac * t_ff, budget_every=5)
    s = diag["budget_series"]
    e0 = s[0]["e_tot"]
    e_err = max(abs(row["e_tot"] - e0) for row in s) / abs(s[0]["e_pot"])
    p0 = np.array(s[0]["momentum"])
    p_scale = max(max(row["mom_scale"] for row in s), 1e-300)
    mom_err = max(
        float(np.max(np.abs(np.array(row["momentum"]) - p0))) for row in s
    ) / p_scale
    ke_grew = s[-1]["e_kin"] > 10.0 * s[0]["e_kin"] + 1e-12
    pe_dropped = s[-1]["e_pot"] < s[0]["e_pot"]
    return {
        "n": n,
        "t_over_tff": t_frac,
        "energy_rel_err_vs_pot": float(e_err),
        "momentum_rel": float(mom_err),
        "collapse_happened": bool(ke_grew and pe_dropped),
        "n_steps": diag["n_steps"],
    }
