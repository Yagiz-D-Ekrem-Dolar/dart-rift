"""Kati mekanigi benchmark senaryolari (P2-VR-01/02/03).

- Rijit donme: kinematik surulen donmede S, R S0 R^T gibi evrilmeli (Jaumann);
  donme terimleri kapatilinca hata O(1) olmali (ablasyon kaniti).
- Elastik dalga: 1B cubukta kucuk genlikli darbe hizi sqrt((K+4G/3)/rho).
- Taylor bar: EPP bakir cubugun rijit duvara carpmasi; L/L0 literatur bandinda
  ve Y'ye gore dogru yonde degisiyor (GPU).
"""

from __future__ import annotations

import numpy as np

from ..cpu_reference.materials import (
    GravityParams,
    MaterialParams,
    PorosityParams,
    StrengthParams,
)
from ..cpu_reference.solid_ref import SolidState, evaluate_solid
from ..cpu_reference.sph_ref import RefParams

# ---------------------------------------------------------------------------
# Rijit donme (P2-VR-01)
# ---------------------------------------------------------------------------


def _ball_lattice(n_side: int, radius: float = 0.5) -> np.ndarray:
    dxl = 2.0 * radius / n_side
    ax = (np.arange(n_side) + 0.5) * dxl - radius
    xx, yy, zz = np.meshgrid(ax, ax, ax, indexing="ij")
    x = np.column_stack([xx.ravel(), yy.ravel(), zz.ravel()])
    return x[np.sqrt(np.sum(x * x, axis=1)) < radius]


def run_rigid_rotation(
    n_side: int = 12,
    omega: float = 1.0,
    quarter_turns: float = 0.5,
    n_steps: int = 300,
    jaumann: bool = True,
) -> dict:
    """z-ekseni etrafinda kinematik rijit donme; S'nin es-donmesini olc.

    Konum/hiz her adimda ANALITIK olarak dayatilir (kinematik surme) —
    boylece yalnizca gerilme-evrimi izole test edilir. Kabul: ic bolgede
    ||S_son - R S0 R^T|| / ||S0|| kucuk (Jaumann acikken).
    """
    x0 = _ball_lattice(n_side)
    n = x0.shape[0]
    dxl = 1.0 / n_side
    h = H_OVER_DX_3D * dxl
    rho0 = 2700.0
    m = np.full(n, rho0 * dxl**3)
    mat = MaterialParams(
        eos="linear", c0=3000.0, rho0_linear=rho0,
        strength=StrengthParams(enabled=True, Y0=1e12, mu_f=0.0, YM=1e13,
                                shear_G=2.27e10, jaumann=jaumann),
        porosity=PorosityParams(enabled=False),
        gravity=GravityParams(enabled=False),
    )  # Y0 dev: akma DEVREYE GIRMESIN, saf gerilme evrimi izlensin
    num = RefParams(alpha_av=0.0, beta_av=0.0)  # kinematik: AV alakasiz

    s0 = 1.0e6
    S0 = np.zeros((n, 3, 3))
    S0[:, 0, 0] = s0
    S0[:, 1, 1] = -s0  # izsiz (deviatorik) baslangic gerilmesi

    state = SolidState(x=x0.copy(), v=np.zeros_like(x0), m=m, u=np.zeros(n),
                       h=h, active=np.ones(n, bool), S=S0.copy())

    total_angle = quarter_turns * np.pi
    dt = total_angle / omega / n_steps
    for k in range(n_steps):
        t = k * dt
        c, s = np.cos(omega * t), np.sin(omega * t)
        rot = np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])
        state.x = x0 @ rot.T
        state.v = np.column_stack(
            [-omega * state.x[:, 1], omega * state.x[:, 0], np.zeros(n)]
        )
        evaluate_solid(state, mat, num)
        state.S += dt * state.dSdt  # kinematik surmede yalniz S evrilir

    theta = omega * total_angle / omega  # toplam aci
    c, s = np.cos(theta), np.sin(theta)
    rot_f = np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])
    S_exact = rot_f @ S0[0] @ rot_f.T
    r0 = np.sqrt(np.sum(x0 * x0, axis=1))
    interior = r0 < 0.5 - 2.5 * h
    err = np.sqrt(np.einsum("nab,nab->n", state.S - S_exact, state.S - S_exact))
    rel = float(np.median(err[interior])) / np.sqrt(np.sum(S0[0] * S0[0]))
    # yapay gerilme uretimi: von Mises degisimi (donme invaryanti olmali)
    j2_0 = 0.5 * np.sum(S0[0] * S0[0])
    j2_f = 0.5 * np.einsum("nab,nab->n", state.S, state.S)
    vm_drift = float(np.median(np.abs(np.sqrt(3 * j2_f[interior]) - np.sqrt(3 * j2_0))))
    return {
        "n": n,
        "jaumann": jaumann,
        "angle_deg": np.degrees(theta),
        "rel_err_vs_rotated": rel,
        "vm_drift_rel": vm_drift / np.sqrt(3 * j2_0),
    }


# ---------------------------------------------------------------------------
# Elastik dalga (P2-VR-03)
# ---------------------------------------------------------------------------


def run_elastic_wave(resolution: int = 400) -> dict:
    """1B cubukta kucuk basinc darbesi; olculen hiz sqrt((K+4G/3)/rho)."""
    rho0 = 2700.0
    K = 2.67e10  # lineer EOS: K = c0^2 rho0
    G_sh = 2.27e10
    c0 = np.sqrt(K / rho0)
    c_long = np.sqrt((K + 4.0 * G_sh / 3.0) / rho0)

    L = 1.0
    dxl = L / resolution
    x = np.arange(-0.1 + 0.5 * dxl, L + 0.1, dxl)
    n = x.size
    m = np.full(n, rho0 * dxl)
    amp = 1.0e-3 * c_long
    x_c0 = 0.15
    sig = 0.02
    v = amp * np.exp(-((x - x_c0) / sig) ** 2)
    active = (x > -0.05) & (x < L + 0.05)

    mat = MaterialParams(
        eos="linear", c0=c0, rho0_linear=rho0,
        strength=StrengthParams(enabled=True, Y0=1e12, mu_f=0.0, YM=1e13, shear_G=G_sh),
        porosity=PorosityParams(enabled=False), gravity=GravityParams(enabled=False),
    )
    num = RefParams(alpha_av=0.1, beta_av=0.2, cfl=0.25)  # kucuk genlik: az AV

    from ..cpu_reference.solid_ref import run_solid

    state = SolidState(x=x[:, None], v=v[:, None], m=m, u=np.zeros(n),
                       h=2.0 * dxl, active=active)
    t_end = 0.4 / c_long  # darbe ~0.4 birim yol alsin
    run_solid(state, mat, num, t_end, budget_every=10**9)

    # tepe konumu: kutle-agirlikli hiz profili tepesi (parabolik incelik)
    vx = state.v[:, 0]
    pk = int(np.argmax(vx))
    xs = state.x[:, 0]
    if 0 < pk < n - 1:
        y0, y1, y2 = vx[pk - 1], vx[pk], vx[pk + 1]
        den = y0 - 2 * y1 + y2
        x_pk = xs[pk] + (0.5 * (y0 - y2) / den) * dxl if abs(den) > 0 else xs[pk]
    else:  # pragma: no cover - guvenlik
        x_pk = xs[pk]
    speed = (x_pk - x_c0) / t_end  # run_solid dt'yi t_end'e kirpar: t == t_end
    return {
        "resolution": resolution,
        "c_long_theory": float(c_long),
        "c0_bulk": float(c0),
        "speed_measured": float(speed),
        "rel_err": abs(speed - c_long) / c_long,
        "distinguishes_bulk": abs(speed - c_long) < abs(speed - c0),
    }


# ---------------------------------------------------------------------------
# Taylor bar (P2-VR-02) — GPU
# ---------------------------------------------------------------------------

COPPER = dict(rho0=8930.0, K=1.40e11, G=4.77e10)

# Wendland C2 icin 3B komsu sayisi: h/dx = 2.0 -> ~268 komsu (ADR-0013).
# Onceki 1.3 degeri yalnizca ~74 komsu veriyordu; Sedov'da %16 hataya yol
# acan ayni yetersizlik burada da gecerlidir.
H_OVER_DX_3D = 2.0


def build_taylor_ic(v_impact: float = 200.0, nx: int = 9):
    """SIMETRIK Taylor carpmasi: iki ozdes bakir cubuk, z=0 duzleminde carpisir.

    Klasik kurulum rijit bir duvar kullanir. Donmus parcacik katmani olarak
    modellendiginde cubuk parcaciklari duvara "gomuluyor", asiri basinc uretip
    enerji defterini patlatiyordu (olculdu: %576 enerji hatasi). Simetri
    duzlemi ayni sinir kosulunu (v_z = 0, kayma serbest) YAPAY parcacik
    olmadan saglar; tum parcaciklar aktiftir ve enerji korunumu gercekten
    olculebilir (ADR-0012).

    Ust cubugun uzunluk orani L/L0 klasik testle ayni buyuklugu olcer.
    """
    L0 = 0.0324
    D = 0.0064
    dxl = D / nx
    r_cyl = D / 2.0
    nz = int(round(L0 / dxl))
    ax = (np.arange(nx) + 0.5) * dxl - r_cyl
    az = (np.arange(nz) + 0.5) * dxl  # z in (0, L0)
    xx, yy, zz = np.meshgrid(ax, ax, az, indexing="ij")
    pts = np.column_stack([xx.ravel(), yy.ravel(), zz.ravel()])
    upper = pts[np.sqrt(pts[:, 0] ** 2 + pts[:, 1] ** 2) < r_cyl]
    lower = upper.copy()
    lower[:, 2] *= -1.0  # z=0 duzleminde ayna

    x = np.vstack([upper, lower])
    n_upper = upper.shape[0]
    n = x.shape[0]
    v = np.zeros_like(x)
    v[:n_upper, 2] = -v_impact  # ust cubuk asagi
    v[n_upper:, 2] = +v_impact  # alt cubuk yukari
    m = np.full(n, COPPER["rho0"] * dxl**3)
    return {
        "x": x, "v": v, "m": m, "u": np.zeros(n), "h": H_OVER_DX_3D * dxl,
        "active": np.ones(n, np.uint8), "n_bar": n_upper, "L0": L0, "dx": dxl,
    }


def run_taylor_bar(device: str, v_impact: float = 200.0, Y0: float = 4.0e8,
                   t_end: float = 6.0e-5, nx: int = 9) -> dict:
    """Taylor carpma testi (GPU): son uzunluk orani + enerji muhasebesi."""
    from ..warp_core.solver_solid import WarpSolid3D

    ic = build_taylor_ic(v_impact=v_impact, nx=nx)
    c0 = float(np.sqrt(COPPER["K"] / COPPER["rho0"]))
    mat = MaterialParams(
        eos="linear", c0=c0, rho0_linear=COPPER["rho0"],
        strength=StrengthParams(enabled=True, Y0=Y0, mu_f=0.0, YM=1e12,
                                shear_G=COPPER["G"]),  # mu_f=0 -> von Mises EPP
        porosity=PorosityParams(enabled=False),
        gravity=GravityParams(enabled=False),
    )
    num = RefParams(cfl=0.25)
    solver = WarpSolid3D(ic["x"], ic["v"], ic["m"], ic["u"], ic["h"], mat, num,
                         active=ic["active"], device=device)
    diag = solver.run(t_end, budget_every=25)
    s = solver.state_numpy()
    zb = s["x"][: ic["n_bar"], 2]
    rb = np.sqrt(s["x"][: ic["n_bar"], 0] ** 2 + s["x"][: ic["n_bar"], 1] ** 2)
    L_f = float(zb.max() - max(zb.min(), 0.0))
    foot = rb[zb < 3 * ic["dx"]]
    mushroom = float(foot.max() / (0.0064 / 2.0)) if foot.size else 1.0
    e0 = diag["budget_series"][0]["e_tot"]
    e_err = max(abs(r["e_tot"] - e0) for r in diag["budget_series"]) / abs(e0)
    return {
        "Y0": Y0,
        "v_impact": v_impact,
        "L_over_L0": L_f / ic["L0"],
        "mushroom_ratio": mushroom,
        "plastic_cum": diag["budget_series"][-1]["plastic_cum"],
        "energy_rel_err": e_err,
        "n_steps": diag["n_steps"],
        "n_bar": ic["n_bar"],
    }
