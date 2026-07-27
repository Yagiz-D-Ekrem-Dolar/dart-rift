"""Sod sok tupu icin KESIN Riemann cozucusu (Toro, 4. bolum).

Ideal gaz, iki sabit durum arasindaki Riemann probleminin tam cozumu:
yildiz bolge basinci Newton-Raphson ile bulunur; profil (rho, v, P)
self-similar x/t degiskeninde ornekleyerek uretilir. SPH cozumu bu analitik
cozume karsi olculur (P1-VR-04).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class RiemannState:
    rho: float
    v: float
    P: float


@dataclass(frozen=True)
class SodSolution:
    """Kesin cozumun turetilmis buyuklukleri (gamma dahil)."""

    gamma: float
    left: RiemannState
    right: RiemannState
    p_star: float
    v_star: float
    rho_star_left: float  # temas yuzeyinin solu (genlesme sonrasi)
    rho_star_right: float  # temas yuzeyinin sagi (sok arkasi)
    shock_speed: float
    head_speed: float  # genlesme fani basi
    tail_speed: float  # genlesme fani kuyrugu


def _f_and_deriv(p: float, s: RiemannState, gamma: float) -> tuple[float, float]:
    """Toro'nun f_K(p) fonksiyonu ve turevi."""
    a = np.sqrt(gamma * s.P / s.rho)
    if p > s.P:  # sok
        A = 2.0 / ((gamma + 1.0) * s.rho)
        B = (gamma - 1.0) / (gamma + 1.0) * s.P
        sq = np.sqrt(A / (p + B))
        f = (p - s.P) * sq
        df = sq * (1.0 - 0.5 * (p - s.P) / (p + B))
    else:  # genlesme
        f = 2.0 * a / (gamma - 1.0) * ((p / s.P) ** ((gamma - 1.0) / (2.0 * gamma)) - 1.0)
        df = 1.0 / (s.rho * a) * (p / s.P) ** (-(gamma + 1.0) / (2.0 * gamma))
    return f, df


def solve_riemann(
    left: RiemannState, right: RiemannState, gamma: float = 1.4
) -> SodSolution:
    """Yildiz bolgeyi Newton-Raphson ile coz (Sod: sol genlesme + sag sok)."""
    p = 0.5 * (left.P + right.P)
    for _ in range(200):
        fl, dfl = _f_and_deriv(p, left, gamma)
        fr, dfr = _f_and_deriv(p, right, gamma)
        g = fl + fr + (right.v - left.v)
        dp = g / (dfl + dfr)
        p_new = max(p - dp, 1.0e-12)
        if abs(p_new - p) < 1.0e-14 * max(p, 1.0):
            p = p_new
            break
        p = p_new
    fl, _ = _f_and_deriv(p, left, gamma)
    fr, _ = _f_and_deriv(p, right, gamma)
    v_star = 0.5 * (left.v + right.v) + 0.5 * (fr - fl)

    gm, gp = gamma - 1.0, gamma + 1.0
    # sol taraf: Sod'da genlesme dalgasi (p_star < P_L)
    rho_star_left = left.rho * (p / left.P) ** (1.0 / gamma)
    a_left = np.sqrt(gamma * left.P / left.rho)
    a_star_left = a_left * (p / left.P) ** (gm / (2.0 * gamma))
    head = left.v - a_left
    tail = v_star - a_star_left
    # sag taraf: sok (p_star > P_R)
    rho_star_right = right.rho * ((p / right.P + gm / gp) / (gm / gp * p / right.P + 1.0))
    a_right = np.sqrt(gamma * right.P / right.rho)
    shock = right.v + a_right * np.sqrt((gp / (2.0 * gamma)) * p / right.P + gm / (2.0 * gamma))
    return SodSolution(
        gamma=gamma,
        left=left,
        right=right,
        p_star=float(p),
        v_star=float(v_star),
        rho_star_left=float(rho_star_left),
        rho_star_right=float(rho_star_right),
        shock_speed=float(shock),
        head_speed=float(head),
        tail_speed=float(tail),
    )


def sample_profile(sol: SodSolution, x: np.ndarray, t: float, x0: float = 0.0):
    """Kesin cozumu (rho, v, P) konum dizisinde ornekle (t > 0)."""
    g = sol.gamma
    gm, gp = g - 1.0, g + 1.0
    xi = (np.asarray(x, dtype=np.float64) - x0) / t
    rho = np.empty_like(xi)
    v = np.empty_like(xi)
    P = np.empty_like(xi)
    a_left = np.sqrt(g * sol.left.P / sol.left.rho)

    m_l = xi < sol.head_speed
    rho[m_l], v[m_l], P[m_l] = sol.left.rho, sol.left.v, sol.left.P

    m_fan = (~m_l) & (xi < sol.tail_speed)
    if np.any(m_fan):
        xif = xi[m_fan]
        vf = 2.0 / gp * (a_left + gm / 2.0 * sol.left.v + xif)
        af = a_left - gm / 2.0 * (vf - sol.left.v)
        rho[m_fan] = sol.left.rho * (af / a_left) ** (2.0 / gm)
        v[m_fan] = vf
        P[m_fan] = sol.left.P * (af / a_left) ** (2.0 * g / gm)

    m_sl = (xi >= sol.tail_speed) & (xi < sol.v_star)
    rho[m_sl], v[m_sl], P[m_sl] = sol.rho_star_left, sol.v_star, sol.p_star

    m_sr = (xi >= sol.v_star) & (xi < sol.shock_speed)
    rho[m_sr], v[m_sr], P[m_sr] = sol.rho_star_right, sol.v_star, sol.p_star

    m_r = xi >= sol.shock_speed
    rho[m_r], v[m_r], P[m_r] = sol.right.rho, sol.right.v, sol.right.P
    return rho, v, P


SOD_LEFT = RiemannState(rho=1.0, v=0.0, P=1.0)
SOD_RIGHT = RiemannState(rho=0.125, v=0.0, P=0.1)
