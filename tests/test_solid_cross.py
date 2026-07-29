"""FAZ 2 CPU<->GPU paritesi + FAZ 1'e indirgeme kaniti."""

import dataclasses

import numpy as np
import pytest

from dartrift.cpu_reference import sph_ref as R
from dartrift.cpu_reference.materials import (
    GravityParams,
    MaterialParams,
    PorosityParams,
    StrengthParams,
)
from dartrift.cpu_reference.solid_ref import (
    SolidState,
    evaluate_solid,
    step_kdk_solid,
)
from dartrift.particles import warp_available, warp_devices
from dartrift.validation.gravity import _uniform_sphere

needs_warp = pytest.mark.skipif(not warp_available(), reason="warp yok")


def _full_physics_setup(n=150):
    rho0 = 2700.0
    x = _uniform_sphere(n, 1.0, seed=616161)
    v = -30.0 * x
    h = 1.3 * (4.0 * np.pi / 3.0 / n) ** (1.0 / 3.0)
    pp = PorosityParams(enabled=True, alpha0=1.3, Pe=1e6, Ps=1e9, n_exp=2.0)
    m = np.full(n, (rho0 / pp.alpha0) * (4.0 / 3.0) * np.pi / n)
    mat = MaterialParams(
        eos="tillotson",
        strength=StrengthParams(enabled=True, Y0=1e6, mu_f=0.8, YM=1.5e9, shear_G=2.27e10),
        porosity=pp,
        gravity=GravityParams(enabled=True, G=6.6743e-4, eps=0.05, mode="direct"),
    )
    num = R.RefParams(cfl=0.2)
    return x, v, m, h, mat, num, pp


class TestReductionToPhase1:
    def test_solid_with_modules_off_equals_hydro(self):
        """S=0, moduller kapali -> kati cozucu FAZ 1 hidrodinamigine indirgenir."""
        from dartrift.validation.conservation import build_cloud_ic

        ic = build_cloud_ic(200)
        n = len(ic["m"])
        num = R.RefParams()
        hydro = R.RefState(x=ic["x"].copy(), v=ic["v"].copy(), m=ic["m"],
                           u=ic["u"].copy(), h=ic["h"], active=np.ones(n, bool))
        R.evaluate(hydro, num)
        mat = MaterialParams(
            eos="ideal_gas", gamma=1.4,
            strength=StrengthParams(enabled=False),
            porosity=PorosityParams(enabled=False),
            gravity=GravityParams(enabled=False),
        )
        solid = SolidState(x=ic["x"].copy(), v=ic["v"].copy(), m=ic["m"],
                           u=ic["u"].copy(), h=ic["h"], active=np.ones(n, bool))
        evaluate_solid(solid, mat, num)
        assert np.allclose(solid.rho, hydro.rho, rtol=1e-13)
        assert np.allclose(solid.P, hydro.P, rtol=1e-13)
        scale_a = np.max(np.abs(hydro.a)) + 1e-300
        assert np.max(np.abs(solid.a - hydro.a)) / scale_a < 1e-11
        scale_u = np.max(np.abs(hydro.dudt)) + 1e-300
        assert np.max(np.abs(solid.dudt - hydro.dudt)) / scale_u < 1e-11


@needs_warp
class TestSolidCpuGpuCross:
    N_STEPS = 5
    DT = 5.0e-7

    def _run_cpu(self):
        x, v, m, h, mat, num, pp = _full_physics_setup()
        st = SolidState(x=x.copy(), v=v.copy(), m=m, u=np.zeros(len(m)), h=h,
                        active=np.ones(len(m), bool),
                        alpha=np.full(len(m), pp.alpha0))
        evaluate_solid(st, mat, num)
        for _ in range(self.N_STEPS):
            step_kdk_solid(st, mat, num, self.DT)
        return st

    def _run_warp(self, device):
        from dartrift.warp_core.solver_solid import WarpSolid3D

        x, v, m, h, mat, num, pp = _full_physics_setup()
        sol = WarpSolid3D(x.copy(), v.copy(), m, np.zeros(len(m)), h, mat, num,
                          alpha0=np.full(len(m), pp.alpha0), device=device)
        for _ in range(self.N_STEPS):
            sol.step(self.DT)
        return sol.state_numpy()

    def _compare(self, st, s):
        for name, ref, got in (
            ("x", st.x, s["x"]), ("v", st.v, s["v"]), ("u", st.u, s["u"]),
            ("P", st.P, s["P"]), ("alpha", st.alpha, s["alpha"]),
            ("S", st.S, s["S"]),
        ):
            scale = np.max(np.abs(ref)) + 1e-300
            err = np.max(np.abs(ref - got)) / scale
            assert err < 1.0e-8, f"{name}: goreli sapma {err:.2e}"

    def test_warp_cpu_device_matches_reference(self):
        self._compare(self._run_cpu(), self._run_warp("cpu"))

    @pytest.mark.gpu
    def test_cuda_matches_reference(self):
        if not any(d.startswith("cuda") for d in warp_devices()):
            pytest.skip("CUDA yok")
        self._compare(self._run_cpu(), self._run_warp("cuda:0"))


@pytest.mark.skipif(not warp_available(), reason="warp yok")
class TestContinuityDensityCross(TestSolidCpuGpuCross):
    """ADR-0015: sureklilik yogunlugu icin de CPU referansi = GPU cekirdegi.

    rho artik bir DURUM degiskeni ve integratorde ilerletiliyor; ayri bir
    ayriklastirma yolu oldugu icin capraz kontrolu ayrica yapilmali.
    """

    def _setup(self):
        x, v, m, h, mat, num, pp = _full_physics_setup()
        return x, v, m, h, dataclasses.replace(mat, density_method="continuity"), num, pp

    def _run_cpu(self):
        x, v, m, h, mat, num, pp = self._setup()
        st = SolidState(x=x.copy(), v=v.copy(), m=m, u=np.zeros(len(m)), h=h,
                        active=np.ones(len(m), bool),
                        alpha=np.full(len(m), pp.alpha0),
                        # ADR-0022: gozenekli malzemede gerilmesiz baslangic
                        # rho*alpha = rho0_kati gerektirir. Burada rho0 yazmak
                        # (eski hali) malzemeyi t=0'da sikismis baslatiyordu ve
                        # GPU cozucusunun kurdugu baslangictan farkliydi.
                        rho=np.full(len(m), mat.tillotson.rho0 / pp.alpha0))
        evaluate_solid(st, mat, num)
        for _ in range(self.N_STEPS):
            step_kdk_solid(st, mat, num, self.DT)
        return st

    def _run_warp(self, device):
        from dartrift.warp_core.solver_solid import WarpSolid3D

        x, v, m, h, mat, num, pp = self._setup()
        sol = WarpSolid3D(x.copy(), v.copy(), m, np.zeros(len(m)), h, mat, num,
                          alpha0=np.full(len(m), pp.alpha0), device=device)
        for _ in range(self.N_STEPS):
            sol.step(self.DT)
        return sol.state_numpy()

    def _compare(self, st, s):
        super()._compare(st, s)
        scale = np.max(np.abs(st.rho)) + 1e-300
        assert np.max(np.abs(st.rho - s["rho"])) / scale < 1.0e-8, "rho sapmasi"
        # rho gercekten EVRILDI mi? Sabit kalsaydi bu test bos olurdu.
        rho0 = self._setup()[4].tillotson.rho0
        assert np.max(np.abs(st.rho - rho0)) / rho0 > 1.0e-6, "rho hic degismemis"
