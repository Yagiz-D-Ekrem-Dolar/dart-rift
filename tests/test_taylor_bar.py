"""P2-VR-02: Taylor bar — son sekil literatur bandinda, parametre yonu dogru.

Vaka: EPP bakir (mu_f=0 -> von Mises), rijit duvara dik carpma
(Wilkins & Guinan 1973 tipi). Kabul bandi L/L0 in [0.60, 0.80] —
elastik-mukemmel-plastik modelle literaturde ~0.65-0.72 raporlanir; bant,
model-form farkini durustce kapsar ve ablasyonla (Y0 2x -> daha az kisalma)
desteklenir.
"""

import pytest

from dartrift.particles import warp_available, warp_devices

needs_warp = pytest.mark.skipif(not warp_available(), reason="warp yok")


def _needs_cuda():
    if not any(d.startswith("cuda") for d in warp_devices()):
        pytest.skip("CUDA yok")


@needs_warp
@pytest.mark.gpu
class TestTaylorBar:
    @pytest.fixture(scope="class")
    def result(self):
        _needs_cuda()
        from dartrift.validation.solids import run_taylor_bar

        return run_taylor_bar("cuda:0", v_impact=200.0, Y0=4.0e8)

    def test_length_ratio_in_literature_band(self, result):
        assert 0.60 <= result["L_over_L0"] <= 0.80, result

    def test_mushrooming_occurred(self, result):
        assert result["mushroom_ratio"] > 1.15, result

    def test_plastic_work_positive(self, result):
        assert result["plastic_cum"] > 0.0

    def test_energy_ledger_closes(self, result):
        assert result["energy_rel_err"] < 0.015, result

    def test_higher_yield_less_shortening(self, result):
        _needs_cuda()
        from dartrift.validation.solids import run_taylor_bar

        stiff = run_taylor_bar("cuda:0", v_impact=200.0, Y0=8.0e8)
        assert stiff["L_over_L0"] > result["L_over_L0"] + 0.02, (result, stiff)

    def test_summation_density_produces_spurious_tension_at_t0(self):
        """ADR-0015'in KOK NEDENI: summation, t=0'da devasa yapay cekme uretir.

        Hicbir dinamik olmadan, yalnizca alan degerlendirmesiyle: bu ince
        cubukta her parcacik serbest yuzeye 2h'den yakin oldugundan kernel
        eksikligi rho'yu ~0.4 rho0'a dusurur; lineer EOS bunu -0.5K'den buyuk
        bir cekmeye cevirir. Sureklilik formunda ayni anda rho = rho0'dir.
        """
        _needs_cuda()
        import numpy as np

        from dartrift.cpu_reference.materials import (
            GravityParams,
            MaterialParams,
            PorosityParams,
            StrengthParams,
        )
        from dartrift.cpu_reference.sph_ref import RefParams
        from dartrift.validation.solids import COPPER, build_taylor_ic
        from dartrift.warp_core.solver_solid import WarpSolid3D

        ic = build_taylor_ic(v_impact=200.0, nx=7)
        p_min = {}
        for dm in ("summation", "continuity"):
            mat = MaterialParams(
                eos="linear", c0=float(np.sqrt(COPPER["K"] / COPPER["rho0"])),
                rho0_linear=COPPER["rho0"],
                strength=StrengthParams(enabled=True, Y0=4.0e8, mu_f=0.0, YM=1e12,
                                        shear_G=COPPER["G"]),
                porosity=PorosityParams(enabled=False),
                gravity=GravityParams(enabled=False),
                density_method=dm,
            )
            sol = WarpSolid3D(ic["x"], ic["v"], ic["m"], ic["u"], ic["h"], mat,
                              RefParams(cfl=0.25), active=ic["active"], device="cuda:0")
            sol._eval()
            p_min[dm] = float(sol.state_numpy()["P"].min())
        assert p_min["summation"] < -0.5 * COPPER["K"], p_min
        assert abs(p_min["continuity"]) < 1.0e-6 * COPPER["K"], p_min

    def test_continuity_density_closes_ledger_summation_does_not(self):
        """ADR-0015 ablasyonu: defteri kapatan sey yogunluk formudur.

        Yapay gerilme (ADR-0014) bu senaryoda semptomu kismen bastiriyordu
        (%15.7 -> %14.0); kok nedeni gideren sureklilik formudur. Test, hangi
        modulun GERCEKTEN yuk tasidigini sabitler.
        """
        _needs_cuda()
        from dartrift.validation.solids import run_taylor_bar

        summ = run_taylor_bar("cuda:0", v_impact=200.0, Y0=4.0e8, nx=7,
                              density_method="summation")
        cont = run_taylor_bar("cuda:0", v_impact=200.0, Y0=4.0e8, nx=7,
                              density_method="continuity")
        assert summ["energy_rel_err"] > 0.05, summ
        assert cont["energy_rel_err"] < 0.015, cont
