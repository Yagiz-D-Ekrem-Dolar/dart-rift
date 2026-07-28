"""P2-FR-03: Tillotson bazalt DIS REFERANSA karsi — sok Hugoniot'u.

Neden gerekli: `test_eos_tillotson.py` icindeki testlerin TAMAMI IC TUTARLILIK
sinar (referans durumda P=0, dal surekliligi, monotonluk, ses hizi tabani).
Bir birim hatasi ya da yanlis katsayi bunlarin hicbirini dusurmez — EOS kendi
icinde tutarli bicimde YANLIS olabilir. Hugoniot ise deneysel bir referanstir
ve EOS'un mutlak olcegini sinar.

Turetme (P0 = 0, u0 = 0 baslangicindan sok):
    Rankine-Hugoniot enerji:  u = 0.5 P (1/rho0 - 1/rho)
    bunu P = P_tillotson(rho, u) ile birlikte cozeriz (sabit nokta),
    sonra                     up = sqrt(P (1/rho0 - 1/rho))
                              Us = P / (rho0 up)
Bazalt deneyi dogrusal bir Us-up bagintisi verir: Us = c0 + s*up.
"""

import numpy as np
import pytest

from dartrift.cpu_reference.materials import TillotsonParams, tillotson_pressure

# Bazalt icin deneysel bant (kaynaklar arasi yayilim dahil)
C0_BAND = (2600.0, 3500.0)   # m/s
S_BAND = (1.2, 1.7)

# Uyum yalnizca FIZIKSEL OLARAK ANLAMLI araliga yapilir. rho/rho0 = 2'de
# Tillotson sikistirilmis dali P ~ 1260 GPa verir; bu hem deneysel veri
# araliginin hem de modelin gecerlilik bolgesinin cok otesidir ve uyumu
# bozar. DART carpmasi (6.1 km/s) icin ilgili bolge up ~ 3 km/s'ye kadardir.
RATIOS = (1.05, 1.10, 1.20, 1.30, 1.40, 1.50, 1.70)


def _hugoniot(t: TillotsonParams):
    up_l, us_l, p_l = [], [], []
    for ratio in RATIOS:
        rho = ratio * t.rho0
        dv = 1.0 / t.rho0 - 1.0 / rho
        u = 0.0
        for _ in range(300):
            p = float(tillotson_pressure(np.array([rho]), np.array([u]), t)[0])
            u_new = 0.5 * p * dv
            if abs(u_new - u) < 1e-10 * max(abs(u_new), 1.0):
                u = u_new
                break
            u = 0.5 * (u + u_new)          # gevsetme: sabit nokta kararli kalsin
        p = float(tillotson_pressure(np.array([rho]), np.array([u]), t)[0])
        up = np.sqrt(max(p * dv, 0.0))
        up_l.append(up)
        us_l.append(p / (t.rho0 * up))
        p_l.append(p)
    return np.array(up_l), np.array(us_l), np.array(p_l)


class TestBasaltHugoniot:
    @pytest.fixture(scope="class")
    def fit(self):
        up, us, p = _hugoniot(TillotsonParams())
        s, c0 = np.polyfit(up, us, 1)
        return {"up": up, "us": us, "p": p, "s": float(s), "c0": float(c0)}

    def test_intercept_matches_bulk_sound_speed_band(self, fit):
        """up -> 0 limitinde Us, hacimsel ses hizina yaklasmali."""
        assert C0_BAND[0] < fit["c0"] < C0_BAND[1], fit["c0"]

    def test_slope_in_experimental_band(self, fit):
        """Us-up egimi bazalt icin ~1.3-1.6; genis bant kaynak yayilimini kapsar."""
        assert S_BAND[0] < fit["s"] < S_BAND[1], fit["s"]

    def test_relation_is_linear(self, fit):
        """Us-up bagintisi bu aralikta DOGRUSAL olmali (deneyin temel bulgusu)."""
        pred = fit["c0"] + fit["s"] * fit["up"]
        rel = np.max(np.abs(pred - fit["us"]) / fit["us"])
        assert rel < 0.05, (rel, fit["us"], pred)

    def test_shock_is_compressive_and_monotone(self, fit):
        assert np.all(fit["p"] > 0.0), fit["p"]
        assert np.all(np.diff(fit["p"]) > 0.0), fit["p"]
        assert np.all(np.diff(fit["up"]) > 0.0), fit["up"]

    def test_shock_outruns_particle_velocity(self, fit):
        """Fiziksel zorunluluk: Us > up (aksi halde sok cephesi olusmaz)."""
        assert np.all(fit["us"] > fit["up"]), (fit["us"], fit["up"])

    def test_dart_relevant_pressure_range_covered(self, fit):
        """DART (6.1 km/s) temas bolgesi ~10-100 GPa; test bunu kapsamali."""
        assert fit["p"].min() < 2.0e9, fit["p"].min()
        assert fit["p"].max() > 1.0e11, fit["p"].max()
