"""Sedov-Taylor patlamasi senaryosu (P1-VR-05).

Nokta enerji enjeksiyonu, kendine-benzer sok: r_s(t) = (E t^2 / (alpha rho0))^(1/5).
gamma=1.4 icin enerji integrali sabiti alpha = 0.8511 (Sedov 1959; Book 1994).
Sok yarcapi radyal yogunluk profilinin tepe noktasindan olculur.
"""

from __future__ import annotations

import numpy as np

from ..cpu_reference.sph_ref import RefParams

GAMMA = 1.4
SEDOV_ALPHA = 0.8511  # gamma=1.4, kuresel (Sedov/Book literatur degeri)
E_INJECT = 1.0
RHO0 = 1.0
U_BACKGROUND = 1.0e-6
H_OVER_DX = 1.25


def shock_radius_exact(t: float) -> float:
    return (E_INJECT * t * t / (SEDOV_ALPHA * RHO0)) ** 0.2


def build_sedov_ic(n_side: int) -> dict:
    """[-0.5,0.5]^3 kafesi; merkezde kernel-agirlikli enerji enjeksiyonu."""
    dx = 1.0 / n_side
    axis = (np.arange(n_side) + 0.5) * dx - 0.5
    xx, yy, zz = np.meshgrid(axis, axis, axis, indexing="ij")
    x = np.column_stack([xx.ravel(), yy.ravel(), zz.ravel()])
    n = x.shape[0]
    m = np.full(n, RHO0 * dx**3)
    u = np.full(n, U_BACKGROUND)
    h = H_OVER_DX * dx
    h_inj = 2.0 * h
    r = np.sqrt(np.sum(x * x, axis=1))
    # 3B Wendland C2 agirliklariyla enerji dagit
    q = r / h_inj
    t = np.maximum(1.0 - 0.5 * q, 0.0)
    w = np.where(q < 2.0, t**4 * (2.0 * q + 1.0), 0.0)
    wsum = np.sum(m * w)
    u += E_INJECT * w / wsum  # ozgul enerji: E * w_i / sum(m w)
    return {"x": x, "v": np.zeros_like(x), "m": m, "u": u, "h": h, "dx": dx}


def measure_shock_radius(x: np.ndarray, rho: np.ndarray, n_bins: int = 60) -> float:
    """Radyal binlenmis yogunluk profilinin tepe yaricapi (parabolik incelik)."""
    r = np.sqrt(np.sum(x * x, axis=1))
    r_max = 0.48
    edges = np.linspace(0.0, r_max, n_bins + 1)
    idx = np.digitize(r, edges) - 1
    prof = np.full(n_bins, np.nan)
    for b in range(n_bins):
        sel = idx == b
        if np.count_nonzero(sel) >= 8:
            prof[b] = np.mean(rho[sel])
    centers = 0.5 * (edges[:-1] + edges[1:])
    valid = np.isfinite(prof)
    pk = int(np.nanargmax(prof))
    # parabolik tepe inceltme (komsu binler mevcutsa)
    if 0 < pk < n_bins - 1 and valid[pk - 1] and valid[pk + 1]:
        y0, y1, y2 = prof[pk - 1], prof[pk], prof[pk + 1]
        denom = y0 - 2.0 * y1 + y2
        if abs(denom) > 1.0e-300:
            shift = 0.5 * (y0 - y2) / denom
            return float(centers[pk] + shift * (centers[1] - centers[0]))
    return float(centers[pk])


def run_sedov_warp(n_side: int, device: str, t_end: float = 0.06,
                   params: RefParams | None = None) -> dict:
    """Sedov'u Warp 3B hash-grid cozucusuyle kostur."""
    from ..warp_core.solver import WarpSPH3D

    ic = build_sedov_ic(n_side)
    params = params or RefParams(gamma=GAMMA)
    solver = WarpSPH3D(
        ic["x"], ic["v"], ic["m"], ic["u"], ic["h"], params, device=device,
    )
    diag = solver.run(t_end)
    s = solver.state_numpy()
    r_meas = measure_shock_radius(s["x"], s["rho"])
    r_exact = shock_radius_exact(t_end)
    from ..cpu_reference.sph_ref import conservation_errors

    cons = conservation_errors(diag)
    r_prof = np.sqrt(np.sum(s["x"] * s["x"], axis=1))
    return {
        "n_side": n_side,
        "t_end": t_end,
        "shock_radius_measured": r_meas,
        "shock_radius_exact": r_exact,
        "shock_radius_rel_err": abs(r_meas - r_exact) / r_exact,
        "conservation": cons,
        "n_steps": diag["n_steps"],
        "timestep_summary": diag["timestep_summary"],
        "profile": {
            "r": r_prof[:: max(1, len(r_prof) // 20000)].tolist(),
            "rho": s["rho"][:: max(1, len(r_prof) // 20000)].tolist(),
        },
    }
