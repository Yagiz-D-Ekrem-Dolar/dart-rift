"""Warp SPH cozucu orkestratoru — kernel sirasi DR-RIFT-P1 §4.1 sozlesmesi.

Iki cozucu:
- WarpSPH3D: hash-grid komsu aramali 3B cozucu (Sedov, korunum, capraz test).
- WarpSPH1D: brute-force 1B cozucu (Sod, plate; CPU referansiyla ayni fizik).

Her ikisi de `dartrift.cpu_reference.RefParams`'i tuketir: fizik parametreleri
TEK kaynaktan gelir (ADR-0006 baglama sozlesmesi). Butceler host tarafinda
sabit-sirali NumPy toplamiyla hesaplanir (determinizm).
"""

from __future__ import annotations

import numpy as np
import warp as wp

from ..cpu_reference.sph_ref import RefParams
from ..invariants import InvariantReport, InvariantViolation, Violation
from ..particles import _init_warp
from . import density as D
from . import eos_test as E
from . import forces as FK
from . import integrator as I
from . import timestep as T
from .hash_grid import GridManager

F = wp.float64
V3 = wp.vec3d


def _budget_row(t: float, m: np.ndarray, v: np.ndarray, u: np.ndarray) -> dict:
    if v.ndim == 1:
        v = v[:, None]
    ke = 0.5 * float(np.sum(m * np.sum(v * v, axis=1)))
    ie = float(np.sum(m * u))
    mom = v.T @ m
    return {
        "t": t,
        "mass": float(np.sum(m)),
        "momentum": [float(p) for p in mom],
        "mom_scale": float(np.sum(m * np.sqrt(np.sum(v * v, axis=1)))),
        "e_kin": ke,
        "e_int": ie,
        "e_tot": ke + ie,
    }


def _check_finite(step: int, **fields: np.ndarray) -> None:
    """Hafif invariant denetimi (G0 cercevesi): NaN/Inf ve rho<=0 yakala."""
    report = InvariantReport(step=step, level="science")
    for name, arr in fields.items():
        bad = ~np.isfinite(arr if arr.ndim == 1 else arr.reshape(len(arr), -1)).all(
            axis=-1 if arr.ndim > 1 else 0
        )
        bad = np.atleast_1d(bad)
        if bad.ndim == 0 or bad.shape == ():  # pragma: no cover - guvenlik
            continue
        if arr.ndim == 1:
            bad = ~np.isfinite(arr)
        else:
            bad = ~np.all(np.isfinite(arr.reshape(arr.shape[0], -1)), axis=1)
        if bad.any():
            idx = np.flatnonzero(bad)
            report.violations.append(
                Violation(name, "NaN/Inf", int(idx.size), tuple(int(i) for i in idx[:8]))
            )
    if "rho" in fields:
        rho = fields["rho"]
        neg = np.isfinite(rho) & (rho <= 0.0)
        if neg.any():
            idx = np.flatnonzero(neg)
            report.violations.append(
                Violation("rho", "yogunluk <= 0", int(idx.size), tuple(int(i) for i in idx[:8]))
            )
    if not report.ok:
        raise InvariantViolation(report)


class _WarpSPHBase:
    """Ortak kosu dongusu: KDK + timestep + butce + invariant denetimi."""

    dim = 0

    def __init__(self, params: RefParams, device: str, check_every: int = 25):
        self.params = params
        self.device = device
        self.check_every = check_every
        self._evaluated = False
        self._step_count = 0

    # alt siniflar: _eval(), _dt_candidates(), _kick_v/_kick_u(half_dt),
    # _drift(dt), _accumulate_continuity(dt), state_numpy()

    def compute_dt(self) -> tuple[float, dict]:
        self._dt_candidates()
        return T.reduce_timestep(
            self.dt_cfl.numpy(), self.dt_acc.numpy(), self.active.numpy(), self.params.cfl
        )

    def step(self, dt: float) -> None:
        """KDK + tam-trapez u guncellemesi (sph_ref.step_kdk ile ayni sira).

        Iki degerlendirme/adim: enerji formunun momentumla TUTARLILIGI icin
        u, D(x_n,v_n) ve D(x_n1,v_n1) oranlarinin ortalamasiyla ilerletilir
        (tek-degerlendirme O(dt) enerji sapmasi birakiyordu; ADR-0007).
        """
        if not self._evaluated:
            self._eval()
            self._evaluated = True
        half = dt * 0.5
        self._kick_v(half)
        self._kick_u(half)  # D(x_n, v_n)
        self._drift(dt)
        if getattr(self, "rho_cont", None) is not None:
            # CPU referansiyla ayni yerlesim: drift SONRASI, v_half ile
            self._accumulate_continuity(dt)
        self._eval()  # (x_n1, v_half)
        self._kick_v(half)
        self._eval()  # (x_n1, v_n1) -> tutarli onbellek
        self._kick_u(half)
        self._step_count += 1

    def run(
        self,
        t_end: float,
        max_steps: int = 500_000,
        budget_every: int = 10,
    ) -> dict:
        if not self._evaluated:
            self._eval()
            self._evaluated = True
        s = self.state_numpy()
        t = 0.0
        series = [_budget_row(t, s["m"], s["v"], s["u"])]
        ts_stats: list[dict] = []
        n_steps = 0
        while t < t_end and n_steps < max_steps:
            dt, stats = self.compute_dt()
            dt = min(dt, t_end - t)
            self.step(dt)
            t += dt
            n_steps += 1
            ts_stats.append(stats)
            if n_steps % budget_every == 0 or t >= t_end:
                s = self.state_numpy()
                series.append(_budget_row(t, s["m"], s["v"], s["u"]))
            if n_steps % self.check_every == 0:
                s = self.state_numpy()
                _check_finite(n_steps, rho=s["rho"], u=s["u"], v=s["v"], x=s["x"])
        return {
            "t_end": t,
            "n_steps": n_steps,
            "budget_series": series,
            "timestep_stats": ts_stats,
            "timestep_summary": T.summarize_timestep_stats(ts_stats),
        }


class WarpSPH3D(_WarpSPHBase):
    dim = 3

    def __init__(
        self,
        x: np.ndarray,
        v: np.ndarray,
        m: np.ndarray,
        u: np.ndarray,
        h: float,
        params: RefParams,
        active: np.ndarray | None = None,
        device: str = "cuda:0",
        track_continuity: bool = False,
        check_every: int = 25,
    ):
        _init_warp()
        super().__init__(params, device, check_every)
        n = len(m)
        self.n = n
        self.h = float(h)
        self.support = 2.0 * self.h
        dev = device
        self.x = wp.array(np.asarray(x, np.float64), dtype=V3, device=dev)
        self.v = wp.array(np.asarray(v, np.float64), dtype=V3, device=dev)
        self.m = wp.array(np.asarray(m, np.float64), dtype=F, device=dev)
        self.u = wp.array(np.asarray(u, np.float64), dtype=F, device=dev)
        act = np.ones(n, np.uint8) if active is None else np.asarray(active, np.uint8)
        self.active = wp.array(act, dtype=wp.uint8, device=dev)
        for name in ("rho", "P", "cs", "divv", "fbal", "dudt", "dt_cfl", "dt_acc"):
            setattr(self, name, wp.zeros(n, dtype=F, device=dev))
        self.a = wp.zeros(n, dtype=V3, device=dev)
        self.gridman = GridManager(n, dev)
        self._radius32 = 0.0
        self.rho_cont = None
        self._cont_rate = None
        if track_continuity:
            self.rho_cont = wp.zeros(n, dtype=F, device=dev)
            self._cont_rate = wp.zeros(n, dtype=F, device=dev)
        self._cont_initialized = False

    def _launch(self, kernel, inputs):
        wp.launch(kernel, dim=self.n, inputs=inputs, device=self.device)

    def _eval(self) -> None:
        self._radius32 = self.gridman.build(self.x, self.support)
        gid = self.gridman.id
        r32 = wp.float32(self._radius32)
        h = F(self.h)
        self._launch(D.density_3d, [gid, self.gridman.x32, self.x, self.m, h, r32, self.rho])
        if self.rho_cont is not None and not self._cont_initialized:
            wp.copy(self.rho_cont, self.rho)
            self._cont_initialized = True
        if self.params.eos == "ideal_gas":
            self._launch(E.eos_ideal_gas, [self.rho, self.u, F(self.params.gamma), self.P, self.cs])
        elif self.params.eos == "linear":
            self._launch(
                E.eos_linear,
                [self.rho, F(self.params.c0), F(self.params.rho0), self.P, self.cs],
            )
        else:
            raise ValueError(f"bilinmeyen test EOS'u: {self.params.eos!r}")
        self._launch(
            FK.divcurl_3d,
            [gid, self.gridman.x32, self.x, self.v, self.m, self.rho, self.cs, h, r32,
             1 if self.params.use_balsara else 0, self.divv, self.fbal],
        )
        self._launch(
            FK.forces_3d,
            [gid, self.gridman.x32, self.x, self.v, self.m, self.rho, self.P, self.cs,
             self.fbal, h, r32, F(self.params.alpha_av), F(self.params.beta_av),
             self.a, self.dudt],
        )

    def _dt_candidates(self) -> None:
        self._launch(
            T.dt_candidates_3d,
            [self.cs, self.divv, self.a, F(self.h), F(self.params.alpha_av),
             F(self.params.beta_av), self.dt_cfl, self.dt_acc],
        )

    def _kick_v(self, half_dt: float) -> None:
        self._launch(I.kick_v_3d, [self.v, self.a, self.active, F(half_dt)])

    def _kick_u(self, half_dt: float) -> None:
        self._launch(I.kick_u_3d, [self.u, self.dudt, self.active, F(half_dt)])

    def _drift(self, dt: float) -> None:
        self._launch(I.drift_3d, [self.x, self.v, self.active, F(dt)])

    def _accumulate_continuity(self, dt: float) -> None:
        # drift sonrasi cagrilir; grid henuz eski konumlara ait olabilir,
        # CPU referansi da ayni sekilde (yeni konum, eski komsu kumesi degil,
        # burute-force yeni konum) hesaplar — 3B grid'i tazele:
        self._radius32 = self.gridman.build(self.x, self.support)
        gid = self.gridman.id
        self._launch(
            D.continuity_rate_3d,
            [gid, self.gridman.x32, self.x, self.v, self.m, F(self.h),
             wp.float32(self._radius32), self._cont_rate],
        )
        self._launch(I.accumulate_scalar_3d, [self.rho_cont, self._cont_rate, self.active, F(dt)])

    def state_numpy(self) -> dict:
        out = {
            "x": self.x.numpy().astype(np.float64),
            "v": self.v.numpy().astype(np.float64),
            "m": self.m.numpy(),
            "u": self.u.numpy(),
            "rho": self.rho.numpy(),
            "P": self.P.numpy(),
            "cs": self.cs.numpy(),
            "divv": self.divv.numpy(),
            "a": self.a.numpy().astype(np.float64),
        }
        if self.rho_cont is not None:
            out["rho_cont"] = self.rho_cont.numpy()
        return out


class WarpSPH1D(_WarpSPHBase):
    dim = 1

    def __init__(
        self,
        x: np.ndarray,
        v: np.ndarray,
        m: np.ndarray,
        u: np.ndarray,
        h: float,
        params: RefParams,
        active: np.ndarray | None = None,
        device: str = "cuda:0",
        track_continuity: bool = False,
        check_every: int = 50,
    ):
        _init_warp()
        super().__init__(params, device, check_every)
        n = len(m)
        self.n = n
        self.h = float(h)
        dev = device
        for name, src in (("x", x), ("v", v), ("m", m), ("u", u)):
            setattr(self, name, wp.array(np.asarray(src, np.float64).ravel(), dtype=F, device=dev))
        act = np.ones(n, np.uint8) if active is None else np.asarray(active, np.uint8)
        self.active = wp.array(act, dtype=wp.uint8, device=dev)
        for name in ("rho", "P", "cs", "divv", "a", "dudt", "dt_cfl", "dt_acc"):
            setattr(self, name, wp.zeros(n, dtype=F, device=dev))
        self.rho_cont = None
        self._cont_rate = None
        if track_continuity:
            self.rho_cont = wp.zeros(n, dtype=F, device=dev)
            self._cont_rate = wp.zeros(n, dtype=F, device=dev)
        self._cont_initialized = False

    def _launch(self, kernel, inputs):
        wp.launch(kernel, dim=self.n, inputs=inputs, device=self.device)

    def _eval(self) -> None:
        h = F(self.h)
        self._launch(D.density_1d, [self.x, self.m, self.n, h, self.rho])
        if self.rho_cont is not None and not self._cont_initialized:
            wp.copy(self.rho_cont, self.rho)
            self._cont_initialized = True
        if self.params.eos == "ideal_gas":
            self._launch(E.eos_ideal_gas, [self.rho, self.u, F(self.params.gamma), self.P, self.cs])
        elif self.params.eos == "linear":
            self._launch(
                E.eos_linear,
                [self.rho, F(self.params.c0), F(self.params.rho0), self.P, self.cs],
            )
        else:
            raise ValueError(f"bilinmeyen test EOS'u: {self.params.eos!r}")
        self._launch(FK.divv_1d, [self.x, self.v, self.m, self.rho, self.n, h, self.divv])
        self._launch(
            FK.forces_1d,
            [self.x, self.v, self.m, self.rho, self.P, self.cs, self.n, h,
             F(self.params.alpha_av), F(self.params.beta_av), self.a, self.dudt],
        )

    def _dt_candidates(self) -> None:
        self._launch(
            T.dt_candidates_1d,
            [self.cs, self.divv, self.a, F(self.h), F(self.params.alpha_av),
             F(self.params.beta_av), self.dt_cfl, self.dt_acc],
        )

    def _kick_v(self, half_dt: float) -> None:
        self._launch(I.kick_v_1d, [self.v, self.a, self.active, F(half_dt)])

    def _kick_u(self, half_dt: float) -> None:
        self._launch(I.kick_u_1d, [self.u, self.dudt, self.active, F(half_dt)])

    def _drift(self, dt: float) -> None:
        self._launch(I.drift_1d, [self.x, self.v, self.active, F(dt)])

    def _accumulate_continuity(self, dt: float) -> None:
        self._launch(
            D.continuity_rate_1d,
            [self.x, self.v, self.m, self.n, F(self.h), self._cont_rate],
        )
        self._launch(I.accumulate_1d, [self.rho_cont, self._cont_rate, self.active, F(dt)])

    def state_numpy(self) -> dict:
        out = {
            name: getattr(self, name).numpy()
            for name in ("x", "v", "m", "u", "rho", "P", "cs", "divv", "a")
        }
        if self.rho_cont is not None:
            out["rho_cont"] = self.rho_cont.numpy()
        return out
