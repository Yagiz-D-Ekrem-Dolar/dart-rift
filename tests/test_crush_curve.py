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


class TestPerParticleCrushCeiling:
    """ADR-0031: crush egrisinin TAVANI parcacik basinadir.

    Bulunan kusur: tavan malzemenin SKALER `PorosityParams.alpha0` degerinden
    aliniyordu. Gozeneklilik ise parcacik basinadir (P3-FR-03/04: bloklar
    gozeneksiz, matris gozenekli). Baslangic distansiyonu bu skaleri ASAN her
    parcacik ILK ADIMDA tavana EZILIYOR, `rho*alpha = rho0` gerilmesiz
    baslangic sarti bozuluyor ve devasa YAPAY CEKME doguyordu.

    Olculdu (is 1449888, H100; yigin matrisi 1.7273, malzeme skaleri 1.6):
        adim 0: alpha=1.727253  P= 0.0000e+00 Pa  KE=0
        adim 1: alpha=1.600000  P= 0.0000e+00 Pa  KE=8.23e-08 J   <-- EZILDI
        adim 2: alpha=1.600000  P=-1.1389e+09 Pa  KE=3.36e+10 J
        adim 4: alpha=1.600000  P=-1.1294e+09 Pa  KE=8.29e+11 J
    Tavan yigina uygun verilince alpha SABIT kaliyor ve KE ~ 1e-6 J.
    KE orani: 8.587e+17.

    Kusur ADR-0030 ile GORUNUR oldu ama HEP VARDI: onceden yigin matrisinin
    alpha0'i tesadufen malzemeninkine esitti (1.6 = 1.6), bloklar ise
    (1.05 < 1.6) geri-genlesme yasagiyla korunuyordu.
    """

    @staticmethod
    def _pp(alpha0=1.6):
        from dartrift.cpu_reference.materials import PorosityParams
        return PorosityParams(enabled=True, alpha0=alpha0, Pe=1.0e6,
                              Ps=1.0e8, n_exp=2.0)

    def test_tavan_parcacik_basina_uygulaniyor(self):
        """Esik altinda (P <= Pe) her parcacik KENDI alpha0'ini korumali."""
        pp = self._pp(1.6)
        a_ref = np.array([1.7273, 1.6, 1.05, 1.2])
        P = np.zeros(4)                       # P <= Pe: hicbir ezilme olmamali
        out = pp.crush_alpha(P, a_ref)
        assert np.allclose(out, a_ref), out
        # ESKI davranis: hepsi skalere ezilirdi
        eski = pp.crush_alpha(P)
        assert np.allclose(eski, 1.6)
        assert eski[0] < a_ref[0] - 0.1, "kusurun olcusu kayboldu mu?"

    def test_tavan_verilmezse_skaler_kullanilir(self):
        """Geriye donuk: homojen kosularda davranis DEGISMEMELI."""
        pp = self._pp(1.5)
        P = np.array([0.0, 5.0e7, 2.0e8])
        assert np.allclose(pp.crush_alpha(P), pp.crush_alpha(P, np.full(3, 1.5)))

    def test_ortuk_cozum_tavani_koruyor(self):
        """`solve_alpha_implicit` gerilmesiz baslangici BOZMAMALI."""
        from dartrift.cpu_reference.materials import (
            MaterialParams, StrengthParams)
        from dartrift.cpu_reference.materials import solve_alpha_implicit

        pp = self._pp(1.6)
        mat = MaterialParams(eos="tillotson", porosity=pp,
                             strength=StrengthParams(enabled=False))
        rho0 = mat.tillotson.rho0
        a_ref = np.array([1.7273, 1.6, 1.05])
        rho = rho0 / a_ref                    # gerilmesiz: rho*alpha = rho0
        u = np.zeros(3)
        yeni = solve_alpha_implicit(a_ref.copy(), rho, u, mat, alpha_ref=a_ref)
        assert np.allclose(yeni, a_ref, rtol=1e-9), (yeni, a_ref)
        # tavansiz (eski hali) 1.7273'u 1.6'ya EZERDI
        eski = solve_alpha_implicit(a_ref.copy(), rho, u, mat)
        assert eski[0] < 1.65, eski
        assert a_ref[0] - eski[0] > 0.1, "kusurun olcusu kayboldu mu?"

    def test_gercek_basma_hala_eziyor(self):
        """Bosluk kontrolu: tavan parcacik basina olunca crush ISLEVI kaybolmamali."""
        from dartrift.cpu_reference.materials import (
            MaterialParams, StrengthParams)
        from dartrift.cpu_reference.materials import solve_alpha_implicit

        pp = self._pp(1.6)
        mat = MaterialParams(eos="tillotson", porosity=pp,
                             strength=StrengthParams(enabled=False))
        a_ref = np.array([1.7273, 1.6])
        rho = (mat.tillotson.rho0 / a_ref) * 1.5     # GERCEKTEN sikistirilmis
        u = np.zeros(2)
        yeni = solve_alpha_implicit(a_ref.copy(), rho, u, mat, alpha_ref=a_ref)
        assert np.all(yeni < a_ref), (yeni, a_ref)
        assert np.all(yeni >= 1.0)
