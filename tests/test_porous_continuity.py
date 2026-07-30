"""P2-FR-04 + ADR-0022: SUREKLILIK yogunlugu + GOZENEKLILIK birlikte dogru mu?

BOSLUK KAYDI: bu kombinasyon hicbir testte kosulmuyordu —
  - `test_solid_cross.py`: gozeneklilik ACIK ama yogunluk TOPLAMA (summation)
  - `test_taylor_bar.py` : yogunluk SUREKLILIK ama gozeneklilik KAPALI
Ikisi birlikte kullanildiginda baslangic yogunlugu alpha0'a bolunmuyordu.

P-alpha modelinde  P = P_kati(rho*alpha, u) / alpha  oldugundan, gerilmesiz
bir baslangic  rho*alpha = rho0_kati,  yani  rho = rho0_kati/alpha0  gerektirir.
Bolme yapilmayinca alpha0=1.5 icin rho*alpha = 4050 oluyor ve DURGUN cisim
13.35 GPa basinc altinda basliyordu. Bir carpma senaryosunda bu, enerji
defterini %92.9 hatayla bozuyordu (ayni kosu gozeneklilik kapaliyken %0.56).
"""

import numpy as np
import pytest

from dartrift.cpu_reference.materials import (
    GravityParams,
    MaterialParams,
    PorosityParams,
    StrengthParams,
)
from dartrift.cpu_reference.sph_ref import RefParams
from dartrift.particles import warp_available, warp_devices

ALPHA0 = 1.5


def _mat(porosity: bool, alpha0: float = ALPHA0) -> MaterialParams:
    return MaterialParams(
        eos="tillotson",
        strength=StrengthParams(enabled=True, Y0=1.0e5, mu_f=0.6, YM=1.5e9,
                                shear_G=2.27e10, jaumann=True),
        porosity=PorosityParams(enabled=porosity, alpha0=alpha0, Pe=1.0e6,
                                Ps=1.0e8, n_exp=2.0),
        gravity=GravityParams(enabled=False),
        density_method="continuity",
    )


def _kafes(nside: int = 12, L: float = 40.0):
    g = (np.arange(nside) + 0.5) / nside - 0.5
    x = np.stack(np.meshgrid(g, g, g, indexing="ij"), -1).reshape(-1, 3) * L
    dxl = L / nside
    return x, np.full(len(x), 2700.0 * dxl**3), 2.0 * dxl


def _needs_cuda():
    if not warp_available() or not any(d.startswith("cuda") for d in warp_devices()):
        pytest.skip("CUDA yok")


@pytest.mark.gpu
class TestPorousContinuityInitialState:
    @pytest.mark.parametrize("alpha0", [1.0, 1.5, 2.5])
    def test_rest_state_has_zero_pressure(self, alpha0):
        """Gerilmesiz gozenekli malzeme P=0 ile baslamali — alpha0 ne olursa olsun."""
        _needs_cuda()
        from dartrift.warp_core.solver_solid import WarpSolid3D

        x, m, h = _kafes()
        s = WarpSolid3D(x, np.zeros_like(x), m, np.zeros(len(x)), h,
                        _mat(True, alpha0), RefParams(), device="cuda:0")
        s._eval()
        st = s.state_numpy()
        # Ic bolgede (yuzey etkisi olmayan) basinc sifir olmali
        r = np.max(np.abs(x), axis=1)
        ic = r < 0.30 * np.max(r)
        assert ic.sum() > 10, ic.sum()
        p_scale = 2.67e10          # Tillotson A: dogal basinc olcegi
        assert np.max(np.abs(st["P"][ic])) < 1.0e-6 * p_scale, (
            alpha0, float(np.max(np.abs(st["P"][ic]))))

    def test_bulk_density_reflects_distension(self):
        """rho = rho0_kati / alpha0 (yigin yogunlugu), rho0_kati DEGIL."""
        _needs_cuda()
        from dartrift.warp_core.solver_solid import WarpSolid3D

        x, m, h = _kafes()
        s = WarpSolid3D(x, np.zeros_like(x), m, np.zeros(len(x)), h,
                        _mat(True), RefParams(), device="cuda:0")
        rho = s.state_numpy()["rho"]
        assert np.allclose(rho, 2700.0 / ALPHA0, rtol=1e-12), float(rho[0])

    def test_cpu_reference_agrees(self):
        """CPU referansi da ayni baslangici kurmali (capraz kontrolun on sarti)."""
        from dartrift.cpu_reference.solid_ref import SolidState, run_solid

        x, m, h = _kafes(nside=8)
        n = len(x)
        st = SolidState(x=x, v=np.zeros_like(x), m=m, u=np.zeros(n), h=h,
                        active=np.ones(n, bool), alpha=np.full(n, ALPHA0))
        run_solid(st, _mat(True), RefParams(), t_end=0.0, max_steps=0)
        assert np.allclose(st.rho, 2700.0 / ALPHA0, rtol=1e-12), float(st.rho[0])


@pytest.mark.gpu
class TestPorousImpactEnergyLedger:
    """Gozeneklilik ACIKKEN enerji defteri kapanmali (regresyon: %92.9 idi)."""

    @staticmethod
    def _impact_error(porosity: bool, nside: int = 32, n_steps: int = 150) -> float:
        """Kucuk mermi + kure hedef. Geometri, mermi kafesin ICINDE kalacak
        sekilde secilir (hedef yaricapi kutu yari-genisliginin %35'i)."""
        from dartrift.warp_core.solver_solid import WarpSolid3D

        H = 120.0                      # kutu yari-genisligi
        R = 0.35 * H                   # hedef yaricapi
        dxl = 2.0 * H / nside
        g = (np.arange(nside) + 0.5) / nside - 0.5
        x = np.stack(np.meshgrid(g, g, g, indexing="ij"), -1).reshape(-1, 3) * (2.0 * H)
        hedef = np.linalg.norm(x, axis=1) < R
        z_c = R + 3.0 * dxl
        mermi = np.linalg.norm(x - np.array([0.0, 0.0, z_c]), axis=1) < 2.0 * dxl
        assert z_c + 2.0 * dxl < H, "mermi kutu disinda kaliyor"
        keep = hedef | mermi
        xs = x[keep]
        v = np.zeros_like(xs)
        v[mermi[keep], 2] = -1000.0
        # bosluk kontrolu: mermi gercekten var mi? (yoksa e0=0 olur ve test
        # hicbir sey sinamaz)
        assert mermi.sum() >= 8, int(mermi.sum())
        assert hedef.sum() >= 500, int(hedef.sum())   # anlamli bir hedef
        s = WarpSolid3D(xs, v, np.full(len(xs), 2700.0 * dxl**3), np.zeros(len(xs)),
                        2.0 * dxl, _mat(porosity), RefParams(cfl=0.25),
                        device="cuda:0", check_every=10**9)
        e0 = s.budgets()["e_tot"]
        assert abs(e0) > 0.0, "baslangic enerjisi sifir — kurulum bozuk"
        for _ in range(n_steps):
            s.step(s.compute_dt())
        return abs(s.budgets()["e_tot"] - e0) / abs(e0)

    def test_initial_state_regression_fixed(self):
        """ADR-0022 regresyonu: hata %92.9'dan asagi inmis olmali.

        Bu, baslangic durumu duzeltmesinin (rho = rho0/alpha0) tuttugunu
        sabitler. Kalan hata AYRI bir acik kusurdur (asagidaki xfail).
        """
        _needs_cuda()
        por = self._impact_error(True)
        assert por < 0.20, por

    def test_nonporous_ledger_is_tight_and_resolution_stable(self):
        """Kontrol: gozeneklilik KAPALIYKEN defter siki ve cozunurlukten bagimsiz.

        Bu, semanin kendisinin saglam oldugunu ve asagidaki kusurun
        GOZENEKLILIGE ozgu oldugunu gosterir.
        """
        _needs_cuda()
        a = self._impact_error(False, nside=32)
        b = self._impact_error(False, nside=44)
        assert a < 0.01 and b < 0.01, (a, b)
        assert abs(b - a) < 0.005, (a, b)

    def test_porous_ledger_matches_solid_ledger(self):
        """Gozeneklilik acmak enerji defterini BOZMAMALI (ADR-0023).

        Bu test uzun sure `xfail` idi. Kusurun kaynagi P-alpha guncellemesinin
        ACIK yapilmasiydi: alpha, bir onceki adimin P'sinden okunuyordu ve sert
        Tillotson EOS'unda ASIRI ATIYORDU — sikistirma hizindan bagimsiz olarak
        tek adimda 1.5'ten 1.0'a cokuyordu. Ortuk (bisection) cozumle
        duzeltildi.
        """
        _needs_cuda()
        por = self._impact_error(True)
        sol = self._impact_error(False)
        assert por < sol + 0.01, (por, sol)

    def test_porous_ledger_does_not_grow_with_resolution(self):
        """Kusurun IMZASI cozunurlukle buyuyen hataydi; artik buyumemeli.

        Eskiden: nside 32 -> 44'te %6.74 -> %15.81 (buyuyor -> kesme hatasi
        DEGIL, sistematik bosluk). ADR-0020'deki ayirt edici mantigin tersi.
        """
        _needs_cuda()
        a = self._impact_error(True, nside=32)
        b = self._impact_error(True, nside=44)
        assert a < 0.02 and b < 0.02, (a, b)
        assert b < a + 0.01, (a, b)

    def test_internal_energy_stays_physical_during_crush(self):
        """Gozenek cokmesi malzemeyi ISITMALI; u NEGATIFE dusmemeli.

        Eskiden toplam ic enerji -5.97e11 J'ye iniyordu (fiziksel degil).
        """
        _needs_cuda()
        from dartrift.warp_core.solver_solid import WarpSolid3D

        H, R, nside = 120.0, 42.0, 32
        dxl = 2.0 * H / nside
        g = (np.arange(nside) + 0.5) / nside - 0.5
        x = np.stack(np.meshgrid(g, g, g, indexing="ij"), -1).reshape(-1, 3) * (2.0 * H)
        hedef = np.linalg.norm(x, axis=1) < R
        z_c = R + 3.0 * dxl
        mermi = np.linalg.norm(x - np.array([0.0, 0.0, z_c]), axis=1) < 2.0 * dxl
        keep = hedef | mermi
        xs = x[keep]
        v = np.zeros_like(xs)
        v[mermi[keep], 2] = -1000.0
        s = WarpSolid3D(xs, v, np.full(len(xs), 2700.0 * dxl**3), np.zeros(len(xs)),
                        2.0 * dxl, _mat(True), RefParams(cfl=0.25),
                        device="cuda:0", check_every=10**9)
        for _ in range(150):
            s.step(s.compute_dt())
        st = s.state_numpy()
        u_top = float(np.sum(st["m"] * st["u"]))
        assert u_top > 0.0, u_top
        assert np.all(st["alpha"] >= 1.0), float(st["alpha"].min())
