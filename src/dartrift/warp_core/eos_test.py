"""FAZ 1 test EOS'lari: ideal gaz (Sod/Sedov) ve lineer sertlik (plate).

Tillotson FAZ 2'de gelir; buradaki EOS'lar sok testlerinin analitik
cozumleriyle karsilastirma icindir.
"""

from __future__ import annotations

import warp as wp

F = wp.float64


@wp.kernel
def eos_ideal_gas(
    rho: wp.array(dtype=F),
    u: wp.array(dtype=F),
    gamma: F,
    P: wp.array(dtype=F),
    cs: wp.array(dtype=F),
):
    i = wp.tid()
    p = (gamma - F(1.0)) * rho[i] * u[i]
    P[i] = p
    if p > F(0.0):
        cs[i] = wp.sqrt(gamma * p / rho[i])
    else:
        cs[i] = F(0.0)


@wp.kernel
def eos_linear(
    rho: wp.array(dtype=F),
    c0: F,
    rho0: F,
    P: wp.array(dtype=F),
    cs: wp.array(dtype=F),
):
    i = wp.tid()
    P[i] = c0 * c0 * (rho[i] - rho0)
    cs[i] = c0
