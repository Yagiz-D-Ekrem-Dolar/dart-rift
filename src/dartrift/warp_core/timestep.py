"""CFL + ivme zaman-adimi kriterleri ve kisit sinifi tanisi (P1-FR-06/07).

dt = C_cfl * min_i( h/(c_i + 1.2*(alpha*c_i + beta*h*|div v_i|)),
                    sqrt(h/|a_i|) )

Kernel'ler parcacik-basina iki adayi uretir; global min ve "hangi kriter
belirledi" istatistigi deterministik olarak host tarafinda (NumPy, sabit
sirali) hesaplanir — min islemi siralamadan bagimsizdir.
"""

from __future__ import annotations

import numpy as np
import warp as wp

F = wp.float64
V3 = wp.vec3d

_ACCEL_TINY = 1.0e-300
_TINY_C = wp.constant(F(_ACCEL_TINY))  # yakalanan Python float f32'ye duserdi


@wp.kernel
def dt_candidates_3d(
    cs: wp.array(dtype=F),
    divv: wp.array(dtype=F),
    a: wp.array(dtype=V3),
    h: wp.array(dtype=F),
    alpha_av: F,
    beta_av: F,
    dt_cfl: wp.array(dtype=F),
    dt_acc: wp.array(dtype=F),
):
    # ADR-0041: `dt` PARCACIK basina h ile; cift buyuklugu degil.
    i = wp.tid()
    hi = h[i]
    visc = cs[i] + F(1.2) * (alpha_av * cs[i] + beta_av * hi * wp.abs(divv[i]))
    if visc < _TINY_C:
        visc = _TINY_C
    dt_cfl[i] = hi / visc
    amag = wp.length(a[i])
    if amag < _TINY_C:
        amag = _TINY_C
    dt_acc[i] = wp.sqrt(hi / amag)


@wp.kernel
def dt_candidates_1d(
    cs: wp.array(dtype=F),
    divv: wp.array(dtype=F),
    a: wp.array(dtype=F),
    h: F,
    alpha_av: F,
    beta_av: F,
    dt_cfl: wp.array(dtype=F),
    dt_acc: wp.array(dtype=F),
):
    i = wp.tid()
    visc = cs[i] + F(1.2) * (alpha_av * cs[i] + beta_av * h * wp.abs(divv[i]))
    if visc < _TINY_C:
        visc = _TINY_C
    dt_cfl[i] = h / visc
    amag = wp.abs(a[i])
    if amag < _TINY_C:
        amag = _TINY_C
    dt_acc[i] = wp.sqrt(h / amag)


def reduce_timestep(
    dt_cfl: np.ndarray, dt_acc: np.ndarray, active: np.ndarray, cfl: float
) -> tuple[float, dict]:
    """Adaylardan global dt + kisit istatistigi (P1-FR-07)."""
    act = active.astype(bool)
    c = dt_cfl[act]
    a = dt_acc[act]
    dt = cfl * float(np.minimum(c, a).min())
    n = max(int(act.sum()), 1)
    frac_cfl = float(np.count_nonzero(c <= a)) / n
    winner = "cfl_viscous" if float(c.min()) <= float(a.min()) else "acceleration"
    return dt, {
        "dt": dt,
        "binding_criterion": winner,
        "pct_cfl_viscous": 100.0 * frac_cfl,
        "pct_acceleration": 100.0 * (1.0 - frac_cfl),
    }


def summarize_timestep_stats(stats: list[dict]) -> dict:
    """Kosu-boyu kisit ozetini cikar (tani logu; gate raporuna girer)."""
    if not stats:
        return {"n_steps": 0}
    n = len(stats)
    n_cfl = sum(1 for s in stats if s["binding_criterion"] == "cfl_viscous")
    return {
        "n_steps": n,
        "binding_cfl_viscous_pct": 100.0 * n_cfl / n,
        "binding_acceleration_pct": 100.0 * (n - n_cfl) / n,
        "mean_pct_particles_cfl": float(np.mean([s["pct_cfl_viscous"] for s in stats])),
        "dt_min": float(min(s["dt"] for s in stats)),
        "dt_max": float(max(s["dt"] for s in stats)),
    }
