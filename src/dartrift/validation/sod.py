"""Sod sok tupu senaryosu (P1-VR-04): kurulum, kosu, analitik karsilastirma.

Kurulum: esit aralik + esit-olmayan kutle (sabit h zorunlulugu ile uyumlu;
ADR-0007). Sinir bantlari donmus (active=0) — dalgalar t_end'e kadar onlara
ulasmaz. Ayni senaryo hem CPU referansiyla hem Warp 1B cozucusuyle kosulur.
"""

from __future__ import annotations

import numpy as np

from ..cpu_reference import sph_ref as R
from .riemann import SOD_LEFT, SOD_RIGHT, sample_profile, solve_riemann

DOMAIN = (-0.75, 0.75)
T_END = 0.2
GAMMA = 1.4
H_OVER_DX = 2.0
FROZEN_BAND = 0.12  # alan kenarindan donmus bolge genisligi


def build_sod_ic(resolution: int) -> dict:
    """resolution = birim uzunluk basina parcacik; esit aralik, m_i = rho(x) dx."""
    dx = 1.0 / resolution
    x = np.arange(DOMAIN[0] + 0.5 * dx, DOMAIN[1], dx)
    n = x.size
    rho_init = np.where(x < 0.0, SOD_LEFT.rho, SOD_RIGHT.rho)
    p_init = np.where(x < 0.0, SOD_LEFT.P, SOD_RIGHT.P)
    m = rho_init * dx
    u = p_init / ((GAMMA - 1.0) * rho_init)
    v = np.zeros(n)
    h = H_OVER_DX * dx
    active = (x > DOMAIN[0] + FROZEN_BAND) & (x < DOMAIN[1] - FROZEN_BAND)
    return {"x": x, "v": v, "m": m, "u": u, "h": h, "active": active, "dx": dx}


def _plateau_mask(x: np.ndarray, lo: float, hi: float, margin: float) -> np.ndarray:
    return (x > lo + margin) & (x < hi - margin)


def measure_sod(x: np.ndarray, rho: np.ndarray, v: np.ndarray, P: np.ndarray, t: float) -> dict:
    """Post-sok plato degerlerini ve sok konumunu olc; analitikle kiyasla."""
    sol = solve_riemann(SOD_LEFT, SOD_RIGHT, GAMMA)
    margin = 0.03
    # sok-arkasi bolge: temas ile sok arasi
    m_post = _plateau_mask(x, sol.v_star * t, sol.shock_speed * t, margin)
    # temas solu bolge: genlesme kuyrugu ile temas arasi
    m_left = _plateau_mask(x, sol.tail_speed * t, sol.v_star * t, margin)
    # sok konumu: analitik sok-arkasi ile sag durum arasindaki gecis noktasi
    # (yogunlugun, iki degerin ortalamasini son kestigi yer)
    rho_mid = 0.5 * (sol.rho_star_right + SOD_RIGHT.rho)
    right_half = x > sol.v_star * t
    xs = x[right_half]
    rs = rho[right_half]
    above = rs > rho_mid
    shock_x = float(xs[above][-1]) if np.any(above) else float("nan")

    def rel(measured: float, exact: float) -> float:
        return abs(measured - exact) / abs(exact)

    rho_post = float(np.mean(rho[m_post]))
    v_post = float(np.mean(v[m_post]))
    p_post = float(np.mean(P[m_post]))
    rho_starl = float(np.mean(rho[m_left]))
    metrics = {
        "t": t,
        "exact": {
            "p_star": sol.p_star,
            "v_star": sol.v_star,
            "rho_star_right": sol.rho_star_right,
            "rho_star_left": sol.rho_star_left,
            "shock_speed": sol.shock_speed,
        },
        "measured": {
            "rho_post": rho_post,
            "v_post": v_post,
            "p_post": p_post,
            "rho_star_left": rho_starl,
            "shock_speed": shock_x / t,
        },
        "rel_err": {
            "rho_post": rel(rho_post, sol.rho_star_right),
            "v_post": rel(v_post, sol.v_star),
            "p_post": rel(p_post, sol.p_star),
            "rho_star_left": rel(rho_starl, sol.rho_star_left),
            "shock_speed": rel(shock_x / t, sol.shock_speed),
        },
    }
    metrics["max_rel_err"] = max(metrics["rel_err"].values())
    return metrics


def l1_density_error(x: np.ndarray, rho: np.ndarray, t: float) -> float:
    """Aktif bolgede analitik yogunluga karsi L1 hatasi (yakinsama olcusu)."""
    sol = solve_riemann(SOD_LEFT, SOD_RIGHT, GAMMA)
    rho_ex, _, _ = sample_profile(sol, x, t)
    core = (x > -0.4) & (x < 0.4)
    return float(np.mean(np.abs(rho[core] - rho_ex[core])))


def momentum_wall_closure(diag: dict) -> dict:
    """Momentum butcesi kapanisi (izole DEGIL — donmus bantlar duvar gibi davranir).

    Dalgalar duvarlara ulasmadigi surece aktif bolgeye net momentum akisi tam
    olarak (P_L - P_R) * t'dir (momentum teoremi). Olculen kazanc bununla
    kapanmalidir; bu, duz korunumdan daha guclu bir butce testidir.
    """
    s0 = diag["budget_series"][0]
    s1 = diag["budget_series"][-1]
    gained = s1["momentum"][0] - s0["momentum"][0]
    expected = (SOD_LEFT.P - SOD_RIGHT.P) * s1["t"]
    return {
        "gained": float(gained),
        "wall_impulse_expected": float(expected),
        "closure_rel_err": abs(gained - expected) / abs(expected),
    }


def run_sod_cpu(resolution: int, params: R.RefParams | None = None) -> dict:
    """Sod'u CPU referansiyla kostur; metrik + korunum + tani dondur."""
    ic = build_sod_ic(resolution)
    params = params or R.RefParams(gamma=GAMMA)
    state = R.RefState(
        x=ic["x"][:, None], v=ic["v"][:, None], m=ic["m"], u=ic["u"],
        h=ic["h"], active=ic["active"],
    )
    diag = R.run_sph(state, params, T_END, track_continuity=True)
    metrics = measure_sod(state.x[:, 0], state.rho, state.v[:, 0], state.P, T_END)
    metrics["conservation"] = R.conservation_errors(diag)
    metrics["momentum_budget"] = momentum_wall_closure(diag)
    metrics["l1_rho"] = l1_density_error(state.x[:, 0], state.rho, T_END)
    metrics["n_steps"] = diag["n_steps"]
    metrics["resolution"] = resolution
    metrics["continuity_max_rel_dev"] = float(
        np.max(np.abs(state.rho_cont[state.active] - state.rho[state.active])
               / state.rho[state.active])
    )
    metrics["profile"] = {
        "x": state.x[:, 0].tolist(),
        "rho": state.rho.tolist(),
        "v": state.v[:, 0].tolist(),
        "P": state.P.tolist(),
    }
    return metrics


def run_sod_warp(resolution: int, device: str, params: R.RefParams | None = None) -> dict:
    """Sod'u Warp 1B cozucusuyle kostur (ayni IC, ayni olcum)."""
    from ..warp_core.solver import WarpSPH1D

    ic = build_sod_ic(resolution)
    params = params or R.RefParams(gamma=GAMMA)
    solver = WarpSPH1D(
        ic["x"], ic["v"], ic["m"], ic["u"], ic["h"], params,
        active=ic["active"].astype(np.uint8), device=device, track_continuity=True,
    )
    diag = solver.run(T_END)
    s = solver.state_numpy()
    metrics = measure_sod(s["x"], s["rho"], s["v"], s["P"], T_END)
    metrics["conservation"] = R.conservation_errors(diag)
    metrics["momentum_budget"] = momentum_wall_closure(diag)
    metrics["l1_rho"] = l1_density_error(s["x"], s["rho"], T_END)
    metrics["n_steps"] = diag["n_steps"]
    metrics["resolution"] = resolution
    metrics["timestep_summary"] = diag["timestep_summary"]
    act = s["rho"] > 0
    metrics["continuity_max_rel_dev"] = float(
        np.max(np.abs(s["rho_cont"][act] - s["rho"][act]) / s["rho"][act])
    )
    metrics["profile"] = {
        "x": s["x"].tolist(), "rho": s["rho"].tolist(),
        "v": s["v"].tolist(), "P": s["P"].tolist(),
    }
    return metrics
