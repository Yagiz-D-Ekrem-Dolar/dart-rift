"""P-alpha porozite benchmark'lari (P2-VR-04).

1) Nokta modeli: tek-eksenli crush cevrimi — yukleme monoton, alpha >= 1,
   bosaltmada geri genlesme yok (histerezis), sikisma isi pozitif/monoton.
2) SPH ablasyonu: 1B plate impact porozite acik/kapali — porozite sok
   basincini dusurmeli ve sok arkasinda alpha < alpha0 (ezilme) olmali.
"""

from __future__ import annotations

import numpy as np

from ..cpu_reference.materials import (
    GravityParams,
    MaterialParams,
    PorosityParams,
    StrengthParams,
    porosity_update, TillotsonParams)
from ..cpu_reference.solid_ref import SolidState, run_solid
from ..cpu_reference.sph_ref import RefParams


def run_crush_cycle(pp: PorosityParams | None = None, n_pts: int = 200) -> dict:
    """Yukleme (0 -> 1.2 Ps) + bosaltma (-> 0) cevrimi; nokta modeli."""
    pp = pp or PorosityParams(enabled=True)
    p_load = np.linspace(0.0, 1.2 * pp.Ps, n_pts)
    p_unload = p_load[::-1]
    alpha = np.array([pp.alpha0])
    alphas_load = []
    work = 0.0
    works = []
    for p in p_load:
        a_new, w = porosity_update(alpha, np.array([p]), pp)
        work += float(w[0])
        alpha = a_new
        alphas_load.append(float(alpha[0]))
        works.append(work)
    alphas_unload = []
    for p in p_unload:
        a_new, w = porosity_update(alpha, np.array([p]), pp)
        work += float(w[0])
        alpha = a_new
        alphas_unload.append(float(alpha[0]))
    al = np.array(alphas_load)
    au = np.array(alphas_unload)
    return {
        "alpha_load": al.tolist(),
        "alpha_unload_final": float(au[-1]),
        "monotonic_loading": bool(np.all(np.diff(al) <= 1.0e-15)),
        "alpha_min": float(min(al.min(), au.min())),
        "alpha_reaches_1": bool(al[-1] == 1.0),
        "no_reexpansion": bool(np.all(np.diff(au) <= 1.0e-15)),
        "compaction_work_positive": bool(np.all(np.diff(works) >= -1e-30)),
        "total_work_norm": work,
        "elastic_below_Pe": bool(
            np.all(al[p_load <= pp.Pe] == pp.alpha0)
        ),
    }


def run_porous_plate(resolution: int = 200, porous: bool = True) -> dict:
    """1B plate impact (Tillotson bazalt), porozite acik/kapali (ablasyon).

    Beklenen: porozite ACIKKEN sok arkasi tepe basinci DUSER (ezilme enerji
    yutar) ve sok gecen bolgede alpha < alpha0.
    """
    # TEK KAYNAK (bkz. ablation.py'deki ayni not): kutle ile EOS ayni
    # `rho0`'i kullanmali, iki yerde yazilmamali.
    rho0 = TillotsonParams().rho0
    dxl = 1.0 / resolution
    x = np.arange(-0.75 + 0.5 * dxl, 0.75, dxl)
    n = x.size
    v_imp = 200.0  # m/s — Pe << P_sok << Ps araligina duser
    pp = PorosityParams(enabled=porous, alpha0=1.4, Pe=5.0e6, Ps=2.0e9, n_exp=2.0)
    mat = MaterialParams(
        eos="tillotson",
        strength=StrengthParams(enabled=False),
        porosity=pp,
        gravity=GravityParams(enabled=False),
    )
    alpha_init = pp.alpha0 if porous else 1.0
    # bulk yogunluk: rho_solid / alpha (ayni kati malzeme, gozenekli yerlesim)
    m = np.full(n, (rho0 / alpha_init) * dxl)
    v = np.where(x < 0.0, v_imp, -v_imp)
    active = (x > -0.6) & (x < 0.6)
    state = SolidState(
        x=x[:, None], v=v[:, None], m=m, u=np.zeros(n), h=2.0 * dxl,
        active=active, alpha=np.full(n, alpha_init),
    )
    num = RefParams(cfl=0.25)
    t_end = 0.25 / 3145.0  # sok ~0.18 birim yol alir (cs_bazalt ~ 3145 m/s)
    diag = run_solid(state, mat, num, t_end, budget_every=10**9)
    core = np.abs(x) < 0.05
    return {
        "porous": porous,
        "p_peak_core": float(np.max(state.P[core])),
        "alpha_core_mean": float(np.mean(state.alpha[core])),
        "alpha_min": float(np.min(state.alpha)),
        "alpha_all_ge_1": bool(np.all(state.alpha >= 1.0 - 1e-12)),
        "n_steps": diag["n_steps"],
    }
