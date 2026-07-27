"""Ortak test yardimcilari."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from dartrift.particles import ParticleStore

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


def make_valid_store(n: int = 16, precision: str = "science") -> ParticleStore:
    """Tum invariantlari saglayan doldurulmus bir depo uret."""
    store = ParticleStore(n, precision)
    rng = np.random.default_rng(12345)
    store.x[:] = rng.uniform(-1.0, 1.0, n)
    store.y[:] = rng.uniform(-1.0, 1.0, n)
    store.z[:] = rng.uniform(-1.0, 1.0, n)
    store.vx[:] = rng.uniform(-10.0, 10.0, n)
    store.vy[:] = rng.uniform(-10.0, 10.0, n)
    store.vz[:] = rng.uniform(-10.0, 10.0, n)
    store.rho[:] = 2600.0
    store.u[:] = 1.0e3
    store.P[:] = 0.0
    store.cs[:] = 3.0e3
    store.mass[:] = 1.0
    store.h[:] = 0.1
    store.mat_id[:] = 1
    return store
