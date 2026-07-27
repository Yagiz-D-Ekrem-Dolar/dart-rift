"""P0-QR-03 altin-hash senaryosu: kanonik deterministik durum uretici.

Senaryo YALNIZCA tamsayi tabanli PCG64 uniform cekimleri kullanir (libm'e
bagimli normal/exp yok); bu sayede hash Windows/Linux/macOS'ta bit-esittir.
Senaryo tanimi KILITLIDIR — degistirmek altin hash'i kirar ve ADR gerektirir.
"""

from __future__ import annotations

import hashlib

import numpy as np

from dartrift.particles import ParticleStore
from dartrift.rng import element_generator

SCENARIO_NAME = "p0_canonical_v1"
SCENARIO_SEED = 104729
SCENARIO_N = 1000


def build_canonical_state(seed: int = SCENARIO_SEED, n: int = SCENARIO_N) -> ParticleStore:
    """Eleman-tohumlu, shard-bagimsiz kanonik baslangic durumu."""
    store = ParticleStore(n, precision="science")
    for i in range(n):
        gp = element_generator(seed, "particles", i)
        vals = gp.random(6)  # x,y,z,vx,vy,vz
        store.x[i] = -500.0 + 1000.0 * vals[0]
        store.y[i] = -500.0 + 1000.0 * vals[1]
        store.z[i] = -500.0 + 1000.0 * vals[2]
        store.vx[i] = -1.0 + 2.0 * vals[3]
        store.vy[i] = -1.0 + 2.0 * vals[4]
        store.vz[i] = -1.0 + 2.0 * vals[5]
        gm = element_generator(seed, "material", i)
        mvals = gm.random(3)  # rho, h, u
        store.rho[i] = 2000.0 + 1000.0 * mvals[0]
        store.h[i] = 0.05 + 0.10 * mvals[1]
        store.u[i] = 1.0e3 * mvals[2]
    store.mass[:] = 1.0e3
    store.cs[:] = 3.0e3
    store.mat_id[:] = 1
    return store


def state_hash(store: ParticleStore) -> str:
    """Alan adlarina gore sirali, dtype + ham bayt uzerinden SHA-256."""
    h = hashlib.sha256()
    fields = store.as_dict()
    for name in sorted(fields):
        arr = fields[name]
        h.update(name.encode("ascii"))
        h.update(str(arr.dtype).encode("ascii"))
        h.update(np.ascontiguousarray(arr).tobytes())
    return h.hexdigest()
