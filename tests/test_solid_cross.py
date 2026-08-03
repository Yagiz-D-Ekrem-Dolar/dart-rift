"""FAZ 2 CPU<->GPU paritesi + FAZ 1'e indirgeme kaniti."""

import dataclasses

import numpy as np
import pytest

from dartrift.cpu_reference import sph_ref as R
from dartrift.cpu_reference.materials import (
    DamageParams,
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


@pytest.mark.skipif(not warp_available(), reason="warp yok")
class TestDamageCross(TestSolidCpuGpuCross):
    """ADR-0027: hasarin ENTEGRASYON SIRASI da capraz kontrol edilir.

    NEDEN GEREKLI. Hasar modulunun testleri FORMULLERI dogruluyordu (asal
    gerilme, kusur sayimi, hiz, uygulama) ve GPU testleri "hasar sonucu
    degistiriyor mu" diye soruyordu. Ikisi de gecerken, DONGU duzeyinde
    ciddi bir kusur aylarca yasayabilirdi — nitekim yasadi: `apply_damage_k`
    gerilmeyi YERINDE carpiyordu ve `_eval()` adim basina iki kez
    cagrildigindan S her adimda (1-D)^2 ile kuculuyordu (olculen sapma
    5 adimda 1000 kat). Hicbir formul testi bunu goremezdi cunku hicbir
    formul yanlis degildi.

    Bu sinif eksigi kapatir: bagimsiz bir CPU uygulamasi ayni KDK sirasini
    yurutur (hiz ham gerilmeden, tasinan gerilme ayri, D tam adimda ve
    monoton) ve N adim sonra iki durum karsilastirilir. Sira farki burada
    ancak sayisal gurultu kadar sapma verebilir.
    """

    N_STEPS = 10
    DT = 5.0e-7
    SEED = 3
    # Genlesme hizi olcerek secildi. Taban kurulum (v = -30x, ICE dogru) basma
    # uretir ve D TAM SIFIR kalir; isareti cevirmek de yetmiyor. Olculen:
    #   carpan   gerinim_maks   D_maks    D>0
    #    x1      8,78e-05       0,0000      0/150   (eps_min medyani 8,80e-04)
    #    x6      5,26e-04       0,0000      0/150
    #    x10     8,74e-04       0,0001      6/150
    #    x20 (10 adim)  3,63e-03  0,0922  147/150   <-- secilen
    # Yani bu carpan keyfi degil: kusurlarin cogunlugunun ACILDIGI ve hasarin
    # olculebilir buyuklukte oldugu en dusuk mertebe.
    V_SCALE = 20.0

    def _setup(self):
        x, v, m, h, mat, num, pp = _full_physics_setup()
        mat = dataclasses.replace(
            mat,
            density_method="continuity",
            damage=DamageParams(enabled=True, k_weibull=1.0e29, m_weibull=9.0),
        )
        return x, -self.V_SCALE * v, m, h, mat, num, pp

    def _run_cpu(self):
        from dartrift.cpu_reference.solid_ref import seed_solid_damage

        x, v, m, h, mat, num, pp = self._setup()
        st = SolidState(x=x.copy(), v=v.copy(), m=m, u=np.zeros(len(m)), h=h,
                        active=np.ones(len(m), bool),
                        alpha=np.full(len(m), pp.alpha0),
                        rho=np.full(len(m), mat.tillotson.rho0 / pp.alpha0))
        seed_solid_damage(st, mat, seed=self.SEED)
        evaluate_solid(st, mat, num)
        for _ in range(self.N_STEPS):
            step_kdk_solid(st, mat, num, self.DT)
        return st

    def _run_warp(self, device):
        from dartrift.warp_core.solver_solid import WarpSolid3D

        x, v, m, h, mat, num, pp = self._setup()
        sol = WarpSolid3D(x.copy(), v.copy(), m, np.zeros(len(m)), h, mat, num,
                          alpha0=np.full(len(m), pp.alpha0), device=device,
                          damage_seed=self.SEED)
        for _ in range(self.N_STEPS):
            sol.step(self.DT)
        out = sol.state_numpy()
        out["D"] = sol.D.numpy()
        return out

    def _compare(self, st, s):
        # Once TESTIN BOS OLMADIGINI kanitla: hasar gercekten buyudu mu?
        # Esikler olculen degerlerden (D_maks 0,092; 147/150 parcacik) rahat
        # bir pay birakilarak secildi. Bunlar olmadan, hasar hic buyumese bile
        # "CPU = GPU" gecerdi — sifiri sifirla karsilastirmak.
        assert st.D.max() > 1.0e-2, (
            f"CPU referansinda D yeterince buyumemis (maks {st.D.max():.2e}) — "
            "senaryo cekme uretmiyor, bu karsilastirma hicbir sey sinamaz")
        assert np.count_nonzero(st.D > 0.0) > st.n // 2, (
            "hasar yalnizca birkac parcacikta — kusur alani ornekleme yapmiyor")
        TestSolidCpuGpuCross._compare(self, st, s)
        scale = np.max(np.abs(st.rho)) + 1e-300
        assert np.max(np.abs(st.rho - s["rho"])) / scale < 1.0e-8, "rho sapmasi"
        # D dogrudan karsilastirilir: [0,1] araliginda oldugu icin MUTLAK esik
        # dogru olcu; goreli esik D->0 olan parcaciklarda anlamsiz buyurdu.
        assert np.max(np.abs(st.D - s["D"])) < 1.0e-9, (
            f"D sapmasi {np.max(np.abs(st.D - s['D'])):.3e}")
        # Hasar monoton ve kisik
        assert np.all(s["D"] >= 0.0) and np.all(s["D"] <= 1.0)


@needs_warp
class TestTimestepCross:
    """`dt` hesabi CPU referansiyla AYNI mi — kapsam bosluguydu.

    Bulunan bosluk: hicbir test `warp_core/timestep.py`'yi ya da
    `compute_timestep_solid`'i CAPRAZ kontrol etmiyordu. Ustelik
    `TestSolidCpuGpuCross` SABIT bir `DT` kullaniyor (5.0e-7), yani `dt`
    hesabi hic karsilastirilmamisti.

    Bu onemlidir: `dt` hem kararliligi hem dogrulugu belirler. GPU ile CPU
    farkli `dt` secseydi, sabit-dt capraz kontrolleri bunu GORMEZDI —
    ADR-0028'de olculen enerji kaymasi da tam olarak `O(dt)` kesme
    hatasiydi, yani `dt` dogrudan bilimsel sonuca giriyor.

    ADR-0040'un kurali burada da gecerli: sinav DUSEBILMELI. Bu yuzden
    yalnizca "ikisi de pozitif" degil, BIREBIR esitlik (goreli 1e-12)
    araniyor ve `dt`nin gercekten kisitlarla degistigi ayrica dogrulaniyor.
    """

    @staticmethod
    def _durumlar():
        """`dt`yi GERCEKTEN oynatani degistir.

        ILK YAZDIGIM HALI YANLIS VARSAYIYORDU: hizi 0.05x..5x aralikta
        degistirip `dt`nin oynayacagini sanmistim. OLCULDU (TRUBA is 1450286):

            hiz carpani   0.05      1        1        5
            dt          5.320e-06 5.402e-06 5.402e-06 5.421e-06
            yayilim     %1,9  -> bosluk kontrolu HAKLI OLARAK dustu

        Sebep fiziksel: CFL kisiti SES HIZINA baglidir (Tillotson bazaltta
        ~5000 m/s) ve denenen parcacik hizlari (1,5-150 m/s) onun yaninda
        ihmal edilebilir. Yani hiz `dt`yi bu rejimde SURMUYOR.

        `dt` gercekten `h` ve `cfl` ile oynar: dt_cfl = cfl * h / visc.
        Sinav onlarla kurulur; boylece esitlik GENIS bir aralikta sinanir.
        """
        x, v, m, h, mat, num, pp = _full_physics_setup()
        return [
            ("h/2, cfl=0.2", 0.5 * h, 0.2),
            ("h,   cfl=0.2", 1.0 * h, 0.2),
            ("2h,  cfl=0.2", 2.0 * h, 0.2),
            ("h,   cfl=0.05", 1.0 * h, 0.05),
        ], (x, v, m, mat, num, pp)

    def _cpu_dt(self, x, v, m, h, mat, num, pp, cfl):
        import dataclasses as _dc

        from dartrift.cpu_reference.solid_ref import compute_timestep_solid

        n2 = _dc.replace(num, cfl=cfl)
        st = SolidState(x=x.copy(), v=v.copy(), m=m, u=np.zeros(len(m)), h=h,
                        active=np.ones(len(m), bool),
                        alpha=np.full(len(m), pp.alpha0))
        evaluate_solid(st, mat, n2)
        return float(compute_timestep_solid(st, mat, n2))

    def _gpu_dt(self, x, v, m, h, mat, num, pp, cfl, device):
        import dataclasses as _dc

        from dartrift.warp_core.solver_solid import WarpSolid3D

        n2 = _dc.replace(num, cfl=cfl)
        sol = WarpSolid3D(x.copy(), v.copy(), m, np.zeros(len(m)), h, mat, n2,
                          alpha0=np.full(len(m), pp.alpha0), device=device,
                          check_every=10**9)
        sol._eval()
        return float(sol.compute_dt())

    def _kos(self, device):
        durumlar, (x, v, m, mat, num, pp) = self._durumlar()
        satir = []
        for ad, h, cfl in durumlar:
            c = self._cpu_dt(x, v, m, h, mat, num, pp, cfl)
            g = self._gpu_dt(x, v, m, h, mat, num, pp, cfl, device)
            satir.append((ad, c, g))
        return satir

    def _dogrula(self, satir):
        for ad, c, g in satir:
            assert c > 0.0 and np.isfinite(c), (ad, c)
            assert g == pytest.approx(c, rel=1e-12), (
                f"{ad}: CPU dt={c:.6e}, GPU dt={g:.6e}, "
                f"goreli fark {abs(g / c - 1):.2e}")
        # BOSLUK KONTROLU: dt gercekten duruma gore DEGISIYOR mu?
        # Hepsi ayni ciksaydi esitlik testi bos bir dogru olurdu.
        dts = [c for _, c, _ in satir]
        assert max(dts) / min(dts) > 1.5, (
            f"dt durumlar arasinda neredeyse hic degismiyor: {dts} — "
            "bu durumda esitlik testi hicbir sey sinamaz")

    def test_warp_cpu_device_dt_matches_reference(self):
        self._dogrula(self._kos("cpu"))

    @pytest.mark.gpu
    def test_cuda_dt_matches_reference(self):
        if not any(d.startswith("cuda") for d in warp_devices()):
            pytest.skip("CUDA yok")
        self._dogrula(self._kos("cuda:0"))
