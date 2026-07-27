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

    def test_artificial_stress_improves_energy_ledger(self):
        """ADR-0014 ablasyonu: yapay gerilme KAPALIYKEN defter kapanmamali.

        Serbest yuzeyli bu senaryoda cekme kararsizligi enerji uretir; yapay
        gerilme onu bastirir. Test, modulun GERCEKTEN ise yaradigini gosterir
        (bir ozelligin ADI, calistigi anlamina gelmez).
        """
        _needs_cuda()
        from dartrift.validation.solids import run_taylor_bar

        off = run_taylor_bar("cuda:0", v_impact=200.0, Y0=4.0e8, nx=7,
                             artificial_stress=False)
        on = run_taylor_bar("cuda:0", v_impact=200.0, Y0=4.0e8, nx=7,
                            artificial_stress=True)
        assert on["energy_rel_err"] < off["energy_rel_err"], (off, on)
