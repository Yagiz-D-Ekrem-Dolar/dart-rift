"""P1 §6.3: CPU referansi ile GPU cozucu kucuk-N deterministik vakada bit-yakin."""

import numpy as np
import pytest

from dartrift.cpu_reference import sph_ref as R
from dartrift.particles import warp_available, warp_devices
from dartrift.validation.conservation import build_cloud_ic

needs_warp = pytest.mark.skipif(not warp_available(), reason="warp yok")

N = 200
N_STEPS = 10
DT = 2.0e-4


def _run_cpu(ic, params):
    st = R.RefState(x=ic["x"].copy(), v=ic["v"].copy(), m=ic["m"], u=ic["u"].copy(),
                    h=ic["h"], active=np.ones(len(ic["m"]), bool))
    R.evaluate(st, params)
    for _ in range(N_STEPS):
        R.step_kdk(st, params, DT)
    return st


def _run_warp(ic, params, device):
    from dartrift.warp_core.solver import WarpSPH3D

    sol = WarpSPH3D(ic["x"].copy(), ic["v"].copy(), ic["m"], ic["u"].copy(),
                    ic["h"], params, device=device)
    for _ in range(N_STEPS):
        sol.step(DT)
    return sol.state_numpy()


@needs_warp
class TestCpuGpuCross:
    @pytest.fixture(scope="class")
    def setup(self):
        return build_cloud_ic(N), R.RefParams()

    def test_warp_cpu_device_matches_reference(self, setup):
        ic, params = setup
        st = _run_cpu(ic, params)
        s = _run_warp(ic, params, "cpu")
        for name, ref, got in (("x", st.x, s["x"]), ("v", st.v, s["v"]),
                               ("u", st.u, s["u"]), ("rho", st.rho, s["rho"])):
            scale = np.max(np.abs(ref)) + 1e-300
            err = np.max(np.abs(ref - got)) / scale
            assert err < 1.0e-9, f"{name}: goreli sapma {err:.2e} (bit-yakin degil)"

    def test_same_device_repeat_is_bitwise_identical(self, setup):
        ic, params = setup
        a = _run_warp(ic, params, "cpu")
        b = _run_warp(ic, params, "cpu")
        for name in ("x", "v", "u", "rho"):
            assert np.array_equal(a[name], b[name]), f"{name} tekrarda bit-esit degil"

    @pytest.mark.gpu
    def test_cuda_matches_reference(self, setup):
        if not any(d.startswith("cuda") for d in warp_devices()):
            pytest.skip("CUDA yok")
        ic, params = setup
        st = _run_cpu(ic, params)
        s = _run_warp(ic, params, "cuda:0")
        for name, ref, got in (("x", st.x, s["x"]), ("v", st.v, s["v"]),
                               ("u", st.u, s["u"])):
            scale = np.max(np.abs(ref)) + 1e-300
            err = np.max(np.abs(ref - got)) / scale
            assert err < 1.0e-9, f"{name}: CUDA goreli sapma {err:.2e}"

    @pytest.mark.gpu
    def test_cuda_repeat_is_bitwise_identical(self, setup):
        if not any(d.startswith("cuda") for d in warp_devices()):
            pytest.skip("CUDA yok")
        ic, params = setup
        a = _run_warp(ic, params, "cuda:0")
        b = _run_warp(ic, params, "cuda:0")
        for name in ("x", "v", "u", "rho"):
            assert np.array_equal(a[name], b[name]), f"{name} CUDA tekrarinda bit-esit degil"
