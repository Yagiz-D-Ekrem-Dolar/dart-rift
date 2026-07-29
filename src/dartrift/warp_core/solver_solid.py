"""Warp kati SPH cozucusu — FAZ 2 kernel sirasi (DR-RIFT-P2 §4.1).

cpu_reference/solid_ref.py ile ayni fizik ve ayni KDK + tam-trapez iskeleti;
test_solid_cross kucuk-N'de bit-yakin pariteyi sinar. Her modul (dayanim,
porozite, yercekimi) MaterialParams uzerinden acilir/kapanir (ablasyon,
P2-FR-06).
"""

from __future__ import annotations

import numpy as np
import warp as wp

from ..cpu_reference.materials import MaterialParams
from ..cpu_reference.sph_ref import RefParams
from ..invariants import InvariantViolation  # noqa: F401 (kapi betikleri yakalar)
from ..particles import _init_warp
from . import density as D
from . import eos_test as E
from . import integrator as I
from . import solid_stress as SS
from .eos_tillotson import eos_solid, make_tillotson_wp
from .gravity_tree import GravitySolver
from .hash_grid import GridManager
from .porosity_palpha import make_porosity_wp, porosity_update_k
from .solver import _budget_row, _check_finite
from .strength_lundborg import make_strength_wp, return_mapping_k

F = wp.float64
V3 = wp.vec3d
M3 = wp.mat33d


class WarpSolid3D:
    """3B kati cozucu: yogunluk -> EOS(P-alpha) -> L -> dS/dt -> yercekimi -> kuvvet."""

    def __init__(
        self,
        x: np.ndarray,
        v: np.ndarray,
        m: np.ndarray,
        u: np.ndarray,
        h: float,
        mat: MaterialParams,
        num: RefParams | None = None,
        S0: np.ndarray | None = None,
        alpha0: np.ndarray | None = None,
        active: np.ndarray | None = None,
        device: str = "cuda:0",
        check_every: int = 50,
    ):
        _init_warp()
        self.mat = mat
        self.num = num or RefParams()
        self.device = device
        self.check_every = check_every
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
        s0 = np.zeros((n, 3, 3)) if S0 is None else np.asarray(S0, np.float64)
        self.S = wp.array(s0, dtype=M3, device=dev)
        a0 = (
            np.full(n, mat.porosity.alpha0 if mat.porosity.enabled else 1.0)
            if alpha0 is None
            else np.asarray(alpha0, np.float64)
        )
        self.alpha = wp.array(a0, dtype=F, device=dev)
        for name in ("rho", "P", "cs", "divv", "fbal", "dudt", "phi",
                     "drhodt", "plastic_du", "dt_cfl", "dt_acc"):
            setattr(self, name, wp.zeros(n, dtype=F, device=dev))
        self._continuity = mat.density_method == "continuity"
        if self._continuity:
            # rho artik bir DURUM degiskeni ve baslangici GOZENEKLILIGE
            # BAGLIDIR. P-alpha modelinde basinc P = P_kati(rho*alpha, u)/alpha
            # ile hesaplanir; gerilmesiz baslangic icin rho*alpha = rho0_kati,
            # yani rho = rho0_kati / alpha0 olmalidir.
            #
            # alpha0'a bolmeden (eski hali) malzeme daha t=0'da sikismis
            # sayiliyordu: alpha0=1.5 icin rho*alpha = 4050 ve P = 1.335e10 Pa
            # — durgun bir cisimde 13 GPa'lik hayali basinc. Bu, carpma
            # senaryosunda enerji defterini %92.9 hatayla bozuyordu (porozite
            # kapatilinca %0.56). Kombinasyon (sureklilik + porozite) hicbir
            # testte kosulmadigi icin gorulmemisti (ADR-0022).
            rho0 = mat.rho0_linear if mat.eos == "linear" else mat.tillotson.rho0
            self.rho = wp.array(np.asarray(rho0 / a0, np.float64), dtype=F, device=dev)
        elif mat.density_method != "summation":
            raise ValueError(f"bilinmeyen yogunluk yontemi: {mat.density_method!r}")
        self.a = wp.zeros(n, dtype=V3, device=dev)
        self.g = wp.zeros(n, dtype=V3, device=dev)
        self.L = wp.zeros(n, dtype=M3, device=dev)
        self.dSdt = wp.zeros(n, dtype=M3, device=dev)
        self.gridman = GridManager(n, dev)
        self._radius32 = 0.0
        self._tp = make_tillotson_wp(mat.tillotson)
        self._sp = make_strength_wp(mat.strength)
        self._pp = make_porosity_wp(mat.porosity)
        self._gravity = GravitySolver(mat.gravity, dev) if mat.gravity.enabled else None
        # yapay gerilme normalizasyonu W(dp): CPU referansiyla ayni deger
        from ..cpu_reference.sph_ref import kernel_w as _kw

        _dp = mat.artificial_stress.dp_over_h * self.h
        self._ast_w_dp = max(float(_kw(np.array([_dp / self.h]), self.h, 3)[0]), 1.0e-300)
        self._evaluated = False
        self._step_count = 0
        self._x_version = 0
        self.plastic_u_total = 0.0

    def _launch(self, kernel, inputs):
        wp.launch(kernel, dim=self.n, inputs=inputs, device=self.device)

    def _eval(self) -> None:
        self._radius32 = self.gridman.build(self.x, self.support)
        gid = self.gridman.id
        r32 = wp.float32(self._radius32)
        h = F(self.h)
        if not self._continuity:
            self._launch(D.density_3d, [gid, self.gridman.x32, self.x, self.m, h, r32, self.rho])
        if self.mat.eos == "tillotson":
            self._launch(eos_solid, [self.rho, self.u, self.alpha, self._tp, self.P, self.cs])
        elif self.mat.eos == "ideal_gas":
            self._launch(E.eos_ideal_gas, [self.rho, self.u, F(self.mat.gamma), self.P, self.cs])
        elif self.mat.eos == "linear":
            self._launch(
                E.eos_linear, [self.rho, F(self.mat.c0), F(self.mat.rho0_linear), self.P, self.cs]
            )
        else:
            raise ValueError(f"bilinmeyen EOS: {self.mat.eos!r}")
        self._launch(
            SS.velocity_gradient_3d,
            [gid, self.gridman.x32, self.x, self.v, self.m, self.rho, self.cs, h, r32,
             1 if self.num.use_balsara else 0, self.L, self.divv, self.fbal],
        )
        if self._continuity:
            self._launch(I.continuity_rate_3d, [self.rho, self.divv, self.drhodt])
        if self.mat.strength.enabled:
            self._launch(
                SS.stress_rate_3d,
                [self.L, self.S, F(self.mat.strength.shear_G),
                 1 if self.mat.strength.jaumann else 0, self.dSdt],
            )
        else:
            self.dSdt.zero_()
        if self._gravity is not None:
            # x_version: agac onbellegi icin. Konumlar yalnizca drift'te
            # degisir; step() icindeki ikinci _eval() ayni konumlari gorur ve
            # agac yeniden KURULMAZ (ADR-0021). Onbellek isabetinde GPU->CPU
            # kopyasi da atlanir.
            hit = (self._gravity._cache_version == self._x_version
                   and self._gravity._cache_arrays is not None
                   and self.mat.gravity.mode == "barnes_hut")
            x_np = None if hit else self.x.numpy().astype(np.float64)
            m_np = None if hit else self.m.numpy()
            self._gravity.compute(self.x, self.m, self.g, self.phi, x_np, m_np,
                                  x_version=self._x_version)
        else:
            self.g.zero_()
            self.phi.zero_()
        ast = self.mat.artificial_stress
        self._launch(
            SS.forces_solid_3d,
            [gid, self.gridman.x32, self.x, self.v, self.m, self.rho, self.P, self.S,
             self.cs, self.fbal, self.g, h, r32, F(self.num.alpha_av), F(self.num.beta_av),
             1 if ast.enabled else 0, F(ast.eps), F(ast.n_exp), F(self._ast_w_dp),
             self.a, self.dudt],
        )

    # -- KDK + tam trapez (solid_ref.step_kdk_solid ile ayni sira) ----------
    def step(self, dt: float) -> None:
        if not self._evaluated:
            self._eval()
            self._evaluated = True
        half = F(dt * 0.5)
        self._launch(I.kick_v_3d, [self.v, self.a, self.active, half])
        self._launch(I.kick_u_3d, [self.u, self.dudt, self.active, half])
        self._launch(SS.kick_S_3d, [self.S, self.dSdt, self.active, half])
        if self._continuity:
            self._launch(I.accumulate_scalar_3d, [self.rho, self.drhodt, self.active, half])
        self._launch(I.drift_3d, [self.x, self.v, self.active, F(dt)])
        self._x_version += 1          # konumlar degisti -> agac gecersiz
        self._eval()  # (x1, v_half)
        self._launch(I.kick_v_3d, [self.v, self.a, self.active, half])
        self._eval()  # (x1, v1)
        self._launch(I.kick_u_3d, [self.u, self.dudt, self.active, half])
        self._launch(SS.kick_S_3d, [self.S, self.dSdt, self.active, half])
        if self._continuity:
            self._launch(I.accumulate_scalar_3d, [self.rho, self.drhodt, self.active, half])
        if self.mat.strength.enabled:
            self._launch(
                return_mapping_k,
                [self.S, self.P, self.rho, self.active, self._sp, self.plastic_du],
            )
            self.plastic_u_total += float(
                np.sum(self.m.numpy() * self.plastic_du.numpy())
            )
        if self.mat.porosity.enabled:
            self._launch(porosity_update_k, [self.alpha, self.P, self.active, self._pp])
        self._step_count += 1

    def compute_dt(self, cfl: float | None = None) -> float:
        """CFL (boyuna elastik hiz) + ivme + gerinim (solid_ref ile ayni)."""
        cs = self.cs.numpy()
        rho = self.rho.numpy()
        if self.mat.strength.enabled:
            c_long = np.sqrt(cs**2 + (4.0 / 3.0) * self.mat.strength.shear_G / rho)
        else:
            c_long = cs
        divv = self.divv.numpy()
        visc = c_long + 1.2 * (
            self.num.alpha_av * c_long + self.num.beta_av * self.h * np.abs(divv)
        )
        dt_cfl = self.h / np.maximum(visc, 1e-300)
        a = self.a.numpy().astype(np.float64)
        amag = np.sqrt(np.sum(a * a, axis=1))
        dt_acc = np.sqrt(self.h / np.maximum(amag, 1e-300))
        lm = self.L.numpy().astype(np.float64).reshape(self.n, 9)
        lnorm = np.sqrt(np.sum(lm * lm, axis=1))
        dt_strain = 0.5 / np.maximum(lnorm, 1e-300)
        act = self.active.numpy().astype(bool)
        c = cfl if cfl is not None else self.num.cfl
        return c * float(np.min(np.minimum(np.minimum(dt_cfl, dt_acc), dt_strain)[act]))

    def budgets(self) -> dict:
        s = self.state_numpy()
        row = _budget_row(0.0, s["m"], s["v"], s["u"])
        ep = 0.5 * float(np.sum(s["m"] * s["phi"])) if self._gravity is not None else 0.0
        row["e_pot"] = ep
        row["e_tot"] = row["e_kin"] + row["e_int"] + ep
        row["plastic_cum"] = self.plastic_u_total
        if self.mat.strength.enabled:
            # TANI: deviatorik depolanmis elastik enerji (e_tot'a dahil DEGIL,
            # ADR-0012 — `u` bu isi zaten tasiyor)
            ss = np.einsum("nab,nab->n", s["S"], s["S"])
            row["e_dev_stored"] = float(
                np.sum(s["m"] * ss / (4.0 * self.mat.strength.shear_G * s["rho"]))
            )
        return row

    def run(self, t_end: float, max_steps: int = 500_000, budget_every: int = 10) -> dict:
        if not self._evaluated:
            self._eval()
            self._evaluated = True
        t = 0.0
        n_steps = 0
        row = self.budgets()
        row["t"] = t
        series = [row]
        while t < t_end and n_steps < max_steps:
            dt = self.compute_dt()
            dt = min(dt, t_end - t)
            self.step(dt)
            t += dt
            n_steps += 1
            if n_steps % budget_every == 0 or t >= t_end:
                row = self.budgets()
                row["t"] = t
                series.append(row)
            if n_steps % self.check_every == 0:
                s = self.state_numpy()
                _check_finite(n_steps, rho=s["rho"], u=s["u"], v=s["v"], x=s["x"])
        return {"t_end": t, "n_steps": n_steps, "budget_series": series}

    def state_numpy(self) -> dict:
        return {
            "x": self.x.numpy().astype(np.float64),
            "v": self.v.numpy().astype(np.float64),
            "m": self.m.numpy(),
            "u": self.u.numpy(),
            "rho": self.rho.numpy(),
            "P": self.P.numpy(),
            "cs": self.cs.numpy(),
            "S": self.S.numpy().astype(np.float64),
            "alpha": self.alpha.numpy(),
            "phi": self.phi.numpy(),
            "a": self.a.numpy().astype(np.float64),
        }
