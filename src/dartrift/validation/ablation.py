"""Ablasyon matrisi (P2-FR-06): her modul kapatilinca sonuc beklenen yonde.

Senaryo: bazalt kurenin ice cokme sikismasi (radyal ic hiz). Ayni IC dort
konfigurasyonla kosulur; her modulun izi olculur:

- dayanim ACIK  -> deviatorik gerilme ve plastik is uretilir (kapaliyken sifir)
- porozite ACIK -> alpha ezilir (< alpha0); kapaliyken alpha == 1 sabit
- yercekimi ACIK-> potansiyel enerji butceye girer (kapaliyken 0)
"""

from __future__ import annotations

import numpy as np

from ..cpu_reference.materials import (
    GravityParams,
    MaterialParams,
    PorosityParams,
    StrengthParams, TillotsonParams)
from ..cpu_reference.solid_ref import SolidState, budgets_solid, run_solid
from ..cpu_reference.sph_ref import RefParams
from .gravity import _uniform_sphere


def _base_ic(n: int = 350):
    # TEK KAYNAK: kutle `rho0`'dan kuruluyor ve EOS de `tillotson`. Ikisi ayri
    # yazilirsa (once oyleydi: burada 2700, TillotsonParams'ta da 2700) tesaduf
    # eseri tutarlar ve `TillotsonParams.rho0` degisince bu kurulum SESSIZCE
    # on-gerilmeli bir baslangic durumu olcer. K7'nin tam kalibi.
    rho0 = TillotsonParams().rho0
    R = 1.0
    x = _uniform_sphere(n, R, seed=515151)
    v = -50.0 * x  # radyal ice cokme (v ~ 50 m/s kabukta)
    # h/dx = 2.0 esdegeri: Wendland C2 icin ~268 komsu (ADR-0013)
    h = 2.0 * (4.0 * np.pi / 3.0 / n) ** (1.0 / 3.0) * R
    m_solid = rho0 * (4.0 / 3.0) * np.pi * R**3 / n
    return x, v, m_solid, h


def run_ablation_case(
    strength: bool, porosity: bool, gravity: bool, n: int = 350, t_end: float = 2.0e-3
) -> dict:
    x, v, m_solid, h = _base_ic(n)
    pp = PorosityParams(enabled=porosity, alpha0=1.4, Pe=5.0e6, Ps=2.0e9, n_exp=2.0)
    alpha_init = pp.alpha0 if porosity else 1.0
    m = np.full(n, m_solid / alpha_init)
    mat = MaterialParams(
        eos="tillotson",
        strength=StrengthParams(enabled=strength, Y0=1.0e6, mu_f=0.8, YM=1.5e9,
                                shear_G=2.27e10),
        porosity=pp,
        gravity=GravityParams(enabled=gravity, G=6.6743e-4, eps=0.05, mode="direct"),
        # G buyutuldu: laboratuvar-olcekli kurede etki olculebilir olsun
    )
    num = RefParams(cfl=0.2)
    state = SolidState(x=x.copy(), v=v.copy(), m=m, u=np.zeros(n), h=h,
                       active=np.ones(n, bool), alpha=np.full(n, alpha_init))
    diag = run_solid(state, mat, num, t_end, budget_every=10**9)
    vm = np.sqrt(1.5 * np.einsum("nab,nab->n", state.S, state.S))
    b = budgets_solid(state)
    return {
        "config": {"strength": strength, "porosity": porosity, "gravity": gravity},
        "vm_max": float(np.max(vm)),
        "plastic_cum": state.plastic_u_total,
        "alpha_min": float(np.min(state.alpha)),
        "alpha_max": float(np.max(state.alpha)),
        "e_pot": b["e_pot"],
        "p_max": float(np.max(state.P)),
        "n_steps": diag["n_steps"],
    }


def run_ablation_matrix(n: int = 350) -> dict:
    """Dort konfigurasyonluk matris + beklenen-yon dogrulamalari."""
    base = run_ablation_case(False, False, False, n)
    st = run_ablation_case(True, False, False, n)
    po = run_ablation_case(False, True, False, n)
    gr = run_ablation_case(False, False, True, n)
    checks = {
        "strength_produces_deviatoric": st["vm_max"] > 1e3 and base["vm_max"] == 0.0,
        "strength_produces_plastic_work": st["plastic_cum"] > 0.0
        and base["plastic_cum"] == 0.0,
        "porosity_crushes_alpha": po["alpha_min"] < 1.4 - 1e-6
        and po["alpha_max"] <= 1.4 + 1e-12,
        "no_porosity_alpha_stays_1": base["alpha_min"] == 1.0 and base["alpha_max"] == 1.0,
        "gravity_adds_potential": gr["e_pot"] < 0.0 and base["e_pot"] == 0.0,
    }
    return {
        "cases": {"base": base, "strength": st, "porosity": po, "gravity": gr},
        "checks": checks,
        "all_expected": all(checks.values()),
    }
