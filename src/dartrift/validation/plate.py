"""1B plate impact senaryosu (P1 §6.2): iki blogun simetrik carpismasi.

Lineer ("basit sertlik") EOS ile analitik cozum kapali formdadir:
P = c0^2 (rho - rho0) icin, +-u hizlariyla carpisan ozdes bloklarda
sok hizi (malzemeye gore) U_s ve sok-arkasi durum:

    U_s   = (u + sqrt(u^2 + 4 c0^2)) / 2
    P*    = rho0 * U_s * u
    rho*  = rho0 * U_s / (U_s - u)
    v*    = 0   (simetri duzlemi)

Turetim: kutle + momentum sicrama kosullari + barotropik EOS (belgede).
"""

from __future__ import annotations

import numpy as np

from ..cpu_reference import sph_ref as R

C0 = 1.0
RHO0 = 1.0
U_IMPACT = 0.2  # her blok +-u ile yaklasir (u/c0 = 0.2: orta siddette sok)
T_END = 0.2
H_OVER_DX = 2.0


def analytic_post_shock(u: float = U_IMPACT, c0: float = C0, rho0: float = RHO0) -> dict:
    us = 0.5 * (u + np.sqrt(u * u + 4.0 * c0 * c0))
    return {
        "shock_speed_material": float(us),
        "p_star": float(rho0 * us * u),
        "rho_star": float(rho0 * us / (us - u)),
        "v_star": 0.0,
    }


def build_plate_ic(resolution: int) -> dict:
    dx = 1.0 / resolution
    x = np.arange(-0.75 + 0.5 * dx, 0.75, dx)
    n = x.size
    m = np.full(n, RHO0 * dx)
    v = np.where(x < 0.0, U_IMPACT, -U_IMPACT)
    u = np.zeros(n)  # lineer EOS barotropik; u yalnizca AV isinmasini izler
    active = (x > -0.6) & (x < 0.6)
    return {"x": x, "v": v, "m": m, "u": u, "h": H_OVER_DX * dx, "active": active, "dx": dx}


def run_plate_cpu(resolution: int, params: R.RefParams | None = None) -> dict:
    ic = build_plate_ic(resolution)
    params = params or R.RefParams(eos="linear", c0=C0, rho0=RHO0)
    state = R.RefState(
        x=ic["x"][:, None], v=ic["v"][:, None], m=ic["m"], u=ic["u"],
        h=ic["h"], active=ic["active"],
    )
    diag = R.run_sph(state, params, T_END)
    return _measure(state.x[:, 0], state.rho, state.v[:, 0], state.P, diag, resolution)


def run_plate_warp(resolution: int, device: str, params: R.RefParams | None = None) -> dict:
    from ..warp_core.solver import WarpSPH1D

    ic = build_plate_ic(resolution)
    params = params or R.RefParams(eos="linear", c0=C0, rho0=RHO0)
    solver = WarpSPH1D(
        ic["x"], ic["v"], ic["m"], ic["u"], ic["h"], params,
        active=ic["active"].astype(np.uint8), device=device,
    )
    diag = solver.run(T_END)
    s = solver.state_numpy()
    return _measure(s["x"], s["rho"], s["v"], s["P"], diag, resolution)


def _measure(x, rho, v, P, diag, resolution) -> dict:
    exact = analytic_post_shock()
    # sok her iki yana malzemeye gore U_s - u laboratuvar hiziyla acilir
    us_lab = exact["shock_speed_material"] - U_IMPACT
    half_width = us_lab * T_END
    margin = 0.25 * half_width + 4.0 * H_OVER_DX / resolution
    core = np.abs(x) < (half_width - margin)
    rho_star = float(np.mean(rho[core]))
    p_star = float(np.mean(P[core]))
    v_star = float(np.mean(v[core]))
    metrics = {
        "resolution": resolution,
        "exact": exact,
        "measured": {"rho_star": rho_star, "p_star": p_star, "v_star": v_star},
        "rel_err": {
            "rho_star": abs(rho_star - exact["rho_star"]) / exact["rho_star"],
            "p_star": abs(p_star - exact["p_star"]) / exact["p_star"],
            # v* = 0: mutlak hatayi carpma hiziyla olcekle
            "v_star": abs(v_star) / U_IMPACT,
        },
        "n_steps": diag["n_steps"],
    }
    metrics["max_rel_err"] = max(metrics["rel_err"].values())
    return metrics
