"""Izole korunum senaryosu (P1-VR-01..03) ve kesme/Balsara tanisi (P1-FR-05).

Korunum: vakumda genlesen izole gaz bulutu — dis kuvvet yok; kutle, momentum
ve toplam enerji korunmalidir. Kesme: saf dogrusal kayma akisinda Balsara
sinirlayicisinin yapay viskoziteyi bastirdigi tek kuvvet-degerlendirmesiyle
olculur (sinir kosulu gerektirmez).
"""

from __future__ import annotations

import numpy as np

from ..cpu_reference import sph_ref as R
from ..rng import element_generator


def build_cloud_ic(n: int, seed: int = 20260727) -> dict:
    """Birim kurede rastgele gaz bulutu; kucuk rastgele hizlar (shard-degismez RNG)."""
    x = np.empty((n, 3))
    v = np.empty((n, 3))
    k = 0
    i = 0
    while k < n:
        g = element_generator(seed, "particles", i)
        p = 2.0 * g.random(3) - 1.0
        if np.sum(p * p) <= 1.0:
            x[k] = p
            v[k] = 0.1 * (2.0 * element_generator(seed, "material", k).random(3) - 1.0)
            k += 1
        i += 1
    m = np.full(n, 1.0 / n)
    u = np.full(n, 1.0)
    # ortalama parcacik araligi ~ (V/n)^(1/3); h = 1.3 * aralik
    h = 1.3 * (4.0 / 3.0 * np.pi / n) ** (1.0 / 3.0)
    return {"x": x, "v": v, "m": m, "u": u, "h": h}


def run_conservation_cpu(n: int = 400, t_end: float = 0.3,
                         params: R.RefParams | None = None) -> dict:
    ic = build_cloud_ic(n)
    params = params or R.RefParams()
    state = R.RefState(
        x=ic["x"], v=ic["v"], m=ic["m"], u=ic["u"], h=ic["h"],
        active=np.ones(n, bool),
    )
    diag = R.run_sph(state, params, t_end)
    out = {"engine": "cpu", "n": n, **R.conservation_errors(diag)}
    out["n_steps"] = diag["n_steps"]
    return out


def run_conservation_warp(n: int, device: str, t_end: float = 0.3,
                          params: R.RefParams | None = None) -> dict:
    from ..warp_core.solver import WarpSPH3D

    ic = build_cloud_ic(n)
    params = params or R.RefParams()
    solver = WarpSPH3D(ic["x"], ic["v"], ic["m"], ic["u"], ic["h"], params,
                       device=device, track_continuity=True)
    diag = solver.run(t_end)
    out = {"engine": f"warp:{device}", "n": n, **R.conservation_errors(diag)}
    out["n_steps"] = diag["n_steps"]
    out["timestep_summary"] = diag["timestep_summary"]
    s = solver.state_numpy()
    out["continuity_max_rel_dev"] = float(
        np.max(np.abs(s["rho_cont"] - s["rho"]) / s["rho"])
    )
    return out


def shear_av_suppression(n_side: int = 12, shear_rate: float = 1.0) -> dict:
    """Saf kayma akisinda AV isinma oranini Balsara acik/kapali kiyasla.

    v_x = A*y alani div v = 0, |curl v| = A verir; Balsara f ~ 0 olmali ve
    du/dt isinmasi bastirilmali. Tek degerlendirme — integrasyona gerek yok.
    Ic bolgedeki (kenardan 2h iceride) parcaciklar olculur.
    """
    dx = 1.0 / n_side
    ax = (np.arange(n_side) + 0.5) * dx - 0.5
    xx, yy, zz = np.meshgrid(ax, ax, ax, indexing="ij")
    x = np.column_stack([xx.ravel(), yy.ravel(), zz.ravel()])
    n = x.shape[0]
    v = np.zeros_like(x)
    v[:, 0] = shear_rate * x[:, 1]
    m = np.full(n, dx**3)
    u = np.full(n, 10.0)  # yuksek ses hizi -> AV etkisi belirgin olcum
    h = 1.3 * dx

    def heating(use_balsara: bool) -> float:
        params = R.RefParams(use_balsara=use_balsara)
        st = R.RefState(x=x.copy(), v=v.copy(), m=m, u=u.copy(), h=h,
                        active=np.ones(n, bool))
        R.evaluate(st, params)
        interior = np.all(np.abs(st.x) < 0.5 - 2.0 * h, axis=1)
        return float(np.mean(np.abs(st.dudt[interior])))

    heat_on = heating(True)
    heat_off = heating(False)
    return {
        "heating_balsara_on": heat_on,
        "heating_balsara_off": heat_off,
        "suppression_ratio": heat_on / max(heat_off, 1.0e-300),
    }
