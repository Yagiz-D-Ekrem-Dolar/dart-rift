"""P2-VR-04: crush curve fiziksel; alpha>=1; geri genlesme yok; is dogru."""

import numpy as np
import pytest

from dartrift.cpu_reference.materials import PorosityParams
from dartrift.validation.porous import run_crush_cycle, run_porous_plate


class TestCrushPointModel:
    @pytest.fixture(scope="class")
    def cycle(self):
        return run_crush_cycle()

    def test_loading_monotone(self, cycle):
        assert cycle["monotonic_loading"]

    def test_alpha_never_below_one(self, cycle):
        assert cycle["alpha_min"] >= 1.0

    def test_full_compaction_reached(self, cycle):
        assert cycle["alpha_reaches_1"]

    def test_no_reexpansion_on_unload(self, cycle):
        # kirmizi-takim: bosaltmada geri genlesme YOK (histerezis fiziksel)
        assert cycle["no_reexpansion"]
        assert cycle["alpha_unload_final"] == 1.0

    def test_compaction_work_positive_monotone(self, cycle):
        assert cycle["compaction_work_positive"]
        assert cycle["total_work_norm"] > 0.0

    def test_elastic_regime_below_Pe(self, cycle):
        assert cycle["elastic_below_Pe"]

    def test_crush_curve_shape(self):
        pp = PorosityParams(enabled=True)
        # Pe'de alpha0, Ps'de 1, arada monoton azalan
        P = np.linspace(pp.Pe, pp.Ps, 50)
        a = pp.crush_alpha(P)
        assert a[0] == pytest.approx(pp.alpha0, rel=1e-12)
        assert a[-1] == pytest.approx(1.0, abs=1e-12)
        assert np.all(np.diff(a) <= 0)


class TestPorousPlateAblation:
    """SPH duzeyinde porozite etkisi: ayni carpma, porozite acik/kapali."""

    @pytest.fixture(scope="class")
    def pair(self):
        return run_porous_plate(porous=True), run_porous_plate(porous=False)

    def test_porosity_reduces_shock_pressure(self, pair):
        porous, solid = pair
        assert porous["p_peak_core"] < 0.85 * solid["p_peak_core"], (porous, solid)

    def test_shocked_region_is_crushed(self, pair):
        porous, _ = pair
        assert porous["alpha_core_mean"] < 1.4 - 1e-3

    def test_alpha_stays_physical(self, pair):
        porous, solid = pair
        assert porous["alpha_all_ge_1"] and solid["alpha_all_ge_1"]
