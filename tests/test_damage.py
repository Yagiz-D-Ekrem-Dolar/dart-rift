"""Grady-Kipp hasar modeli testleri (P2 §1.3 STRETCH kapatildi, ADR-0027).

DOGRULAMA STRATEJISI: her sinav, cevabi ANALITIK ya da FIZIKSEL olarak bilinen
bir duruma dayanir — kodun kendi ciktisina degil.
"""

import numpy as np
import pytest

from dartrift.cpu_reference.damage_ref import (
    activated_flaw_count,
    apply_damage,
    damage_rate,
    local_scalar_strain,
    max_principal_stress,
    seed_flaws,
    weibull_strain_scale,
    youngs_modulus,
)
from dartrift.cpu_reference.materials import DamageParams

DP = DamageParams(enabled=True, k_weibull=1.0e29, m_weibull=9.0,
                  crack_speed_frac=0.4, n_flaws_per_particle=10.0)
K_BULK, G_SHEAR = 2.67e10, 2.27e10


# --------------------------- elastik baglantilar ---------------------------

def test_young_modulu_formulu():
    """E = 9KG/(3K+G)."""
    assert youngs_modulus(K_BULK, G_SHEAR) == pytest.approx(
        9 * K_BULK * G_SHEAR / (3 * K_BULK + G_SHEAR), rel=1e-14)


def test_young_modulu_siniri():
    """G -> 0 iken E -> 0; K -> sonsuz iken E -> 3G."""
    assert youngs_modulus(K_BULK, 1e-6) < 1e-5
    assert youngs_modulus(1e30, G_SHEAR) == pytest.approx(3 * G_SHEAR, rel=1e-6)


def test_gecersiz_modul_reddedilir():
    for a, b in ((0.0, 1.0), (1.0, 0.0), (-1.0, 1.0)):
        with pytest.raises(ValueError, match="pozitif"):
            youngs_modulus(a, b)


# --------------------------- asal gerilme ---------------------------

def test_maks_asal_gerilme_kosegen():
    """S kosegen ise sigma = diag(S) - P; en buyugu donmeli."""
    P = np.array([-1.0e6, 1.0e6, 0.0])
    S = np.zeros((3, 3, 3))
    S[0] = np.diag([2.0e6, -1.0e6, -1.0e6])
    got = max_principal_stress(P, S)
    assert got == pytest.approx([3.0e6, -1.0e6, 0.0], rel=1e-12)


def test_maks_asal_gerilme_kesme():
    """Saf kesme: S = [[0,t,0],[t,0,0],[0,0,0]] -> ozdegerler {+t, -t, 0}."""
    t = 5.0e6
    S = np.zeros((1, 3, 3))
    S[0, 0, 1] = S[0, 1, 0] = t
    assert max_principal_stress(np.zeros(1), S)[0] == pytest.approx(t, rel=1e-12)


def test_maks_asal_gerilme_donme_altinda_degismez():
    """Ozdegerler donme degismezidir; keyfi bir donme sonucu degistirmemeli."""
    rng = np.random.default_rng(5)
    S = rng.normal(size=(3, 3))
    S = 0.5 * (S + S.T) * 1e7
    P = np.array([2.0e6])
    q, _ = np.linalg.qr(rng.normal(size=(3, 3)))
    S_rot = q @ S @ q.T
    a = max_principal_stress(P, S[None, :, :])[0]
    b = max_principal_stress(P, S_rot[None, :, :])[0]
    assert a == pytest.approx(b, rel=1e-10)


def test_basmada_gerinim_sifir():
    """P > 0 (basma) ve S = 0 -> cekme yok -> gerinim 0."""
    eps = local_scalar_strain(np.array([1.0e9]), np.zeros((1, 3, 3)), K_BULK, G_SHEAR)
    assert eps[0] == 0.0


def test_cekmede_gerinim_pozitif():
    eps = local_scalar_strain(np.array([-1.0e8]), np.zeros((1, 3, 3)), K_BULK, G_SHEAR)
    assert eps[0] == pytest.approx(1.0e8 / youngs_modulus(K_BULK, G_SHEAR), rel=1e-12)


# --------------------------- Weibull kusurlari ---------------------------

def test_weibull_olcegi_formulu():
    """eps = (1/(kV))^(1/m)."""
    assert weibull_strain_scale(1e29, 9.0, 1.0) == pytest.approx(
        (1.0 / 1e29) ** (1.0 / 9.0), rel=1e-14)


def test_weibull_olcegi_bazalt_mertebesi():
    """Varsayilanlar bazalt icin ~10-40 MPa cekme dayanimi vermeli.

    Bu bir DIS KAYNAK kontrolu: bazalt cekme dayanimi literaturde 10-30 MPa.
    Parametreler saf uydurma degilse bu bandi tutturmali."""
    eps = weibull_strain_scale(1e29, 9.0, 1.0)
    sigma = eps * youngs_modulus(K_BULK, G_SHEAR)
    assert 5.0e6 < sigma < 6.0e7, sigma


def test_kusur_tohumlama_deterministik():
    a = seed_flaws(500, 1.0, DP, 11)
    b = seed_flaws(500, 1.0, DP, 11)
    assert np.array_equal(a[0], b[0]) and np.array_equal(a[1], b[1])


def test_kusur_tohumlama_tohuma_duyarli():
    a = seed_flaws(500, 1.0, DP, 11)
    c = seed_flaws(500, 1.0, DP, 12)
    assert not np.array_equal(a[0], c[0])


def test_kusur_sayisi_korunur():
    """Toplam kusur sayisi n_flaws_per_particle * N olmali."""
    n = 800
    _, nf = seed_flaws(n, 1.0, DP, 3)
    assert nf.sum() == pytest.approx(DP.n_flaws_per_particle * n, rel=1e-12)


def test_eps_min_weibull_dagilimina_uyuyor():
    """En zayif kusurun dagilimi teorik Weibull ile uyusmali.

    N_toplam kusur, V_toplam hacme dagitildiginda j'inci kusurun gerinimi
    (j/(k V))^(1/m)'dir. En kucugu j=1'e karsilik gelir; parcacik basina en
    zayif kusurun MEDYANI, tek-parcacik olceginin mertebesinde olmali."""
    n, v_p = 4000, 1.0
    e, _ = seed_flaws(n, v_p, DP, 17)
    fin = np.isfinite(e)
    assert fin.sum() > 0.99 * n, "kusursuz parcacik orani cok yuksek"
    # tek parcacik hacminde ilk kusur olcegi
    olcek = weibull_strain_scale(DP.k_weibull, DP.m_weibull, v_p)
    assert 0.3 * olcek < np.median(e[fin]) < 3.0 * olcek, (np.median(e[fin]), olcek)


def test_kusur_gecersiz_girdi():
    with pytest.raises(ValueError, match="n_particles"):
        seed_flaws(0, 1.0, DP, 1)
    with pytest.raises(ValueError, match="hacmi pozitif"):
        seed_flaws(10, 0.0, DP, 1)
    with pytest.raises(ValueError, match="k_weibull"):
        seed_flaws(10, 1.0, DamageParams(k_weibull=0.0), 1)


# --------------------------- aktivasyon ve hiz ---------------------------

def test_esik_altinda_kusur_acilmaz():
    eps_min = np.array([1.0e-3])
    n_fl = np.array([10.0])
    assert activated_flaw_count(np.array([0.5e-3]), eps_min, n_fl, DP)[0] == 0.0
    assert activated_flaw_count(np.array([1.0e-3]), eps_min, n_fl, DP)[0] == 0.0


def test_esik_ustunde_kusur_acilir_ve_sinirlanir():
    eps_min = np.array([1.0e-3, 1.0e-3])
    n_fl = np.array([10.0, 10.0])
    n = activated_flaw_count(np.array([1.2e-3, 1.0e-1]), eps_min, n_fl, DP)
    assert 0.0 < n[0] < 10.0
    assert n[1] == 10.0, "kusur sayisi ustunde sinirlanmali"


def test_hasar_hizi_basmada_sifir():
    """Basmada gerinim 0 -> hasar hizi 0. Kirik olusumu CEKME olayidir."""
    eps = local_scalar_strain(np.array([1.0e9]), np.zeros((1, 3, 3)), K_BULK, G_SHEAR)
    r = damage_rate(eps, np.array([1e-3]), np.array([10.0]), np.array([4000.0]), 0.1, DP)
    assert r[0] == 0.0


def test_hasar_hizi_gerinimle_artar():
    e = np.array([1.1e-3, 2.0e-3, 5.0e-3])
    r = damage_rate(e, np.full(3, 1.0e-3), np.full(3, 1.0e6),
                    np.full(3, 4000.0), 0.1, DP)
    assert r[0] < r[1] < r[2]


def test_hasar_hizi_gecersiz_yaricap():
    with pytest.raises(ValueError, match="r_s"):
        damage_rate(np.array([1e-3]), np.array([1e-3]), np.array([1.0]),
                    np.array([4000.0]), 0.0, DP)


# --------------------------- uygulama ---------------------------

def test_hasar_yalnizca_cekmeyi_zayiflatir():
    """P > 0 (basma) DEGISMEZ; P < 0 (cekme) (1-D) ile carpilir.

    Basmayi da zayiflatmak kraterlesmeyi tamamen yanlis yapardi: sok onunde
    malzeme basma altindadir ve orada dayanim kaybi fiziksel degildir."""
    P = np.array([1.0e8, -1.0e8])
    S = np.zeros((2, 3, 3))
    D = np.array([0.5, 0.5])
    p_new, _ = apply_damage(P, S, D)
    assert p_new[0] == pytest.approx(1.0e8), "basma zayiflatildi — YANLIS"
    assert p_new[1] == pytest.approx(-0.5e8)


def test_hasar_deviatorigi_zayiflatir():
    S = np.zeros((1, 3, 3))
    S[0, 0, 1] = S[0, 1, 0] = 1.0e7
    _, s_new = apply_damage(np.zeros(1), S, np.array([0.25]))
    assert s_new[0, 0, 1] == pytest.approx(0.75e7)


def test_tam_hasar_cekmeyi_sifirlar():
    p_new, s_new = apply_damage(np.array([-1.0e8]), np.ones((1, 3, 3)), np.array([1.0]))
    assert p_new[0] == 0.0
    assert np.all(s_new == 0.0)


def test_hasar_sifirken_hicbir_sey_degismez():
    """Ablasyon: D = 0 -> P ve S aynen kalmali (bit-ayni)."""
    rng = np.random.default_rng(2)
    P = rng.normal(size=5) * 1e8
    S = rng.normal(size=(5, 3, 3)) * 1e7
    p_new, s_new = apply_damage(P, S, np.zeros(5))
    assert np.array_equal(p_new, P)
    assert np.array_equal(s_new, S)


def test_hasar_araligi_kisilir():
    """D dizisi [0,1] disinda gelse bile uygulama kisar."""
    p_new, _ = apply_damage(np.array([-1.0e8, -1.0e8]), np.zeros((2, 3, 3)),
                            np.array([-0.5, 2.0]))
    assert p_new[0] == pytest.approx(-1.0e8)   # D<0 -> 0 gibi
    assert p_new[1] == 0.0                     # D>1 -> 1 gibi


# --------------------------- GPU ---------------------------

@pytest.mark.gpu
class TestDamageGPU:
    @staticmethod
    def _needs_cuda():
        from dartrift.particles import warp_available, warp_devices

        if not warp_available() or not any(
                d.startswith("cuda") for d in warp_devices()):
            pytest.skip("CUDA yok")

    @staticmethod
    def _kafes(nside=8, L=4.0):
        g = (np.arange(nside) + 0.5) / nside - 0.5
        x = np.stack(np.meshgrid(g, g, g, indexing="ij"), -1).reshape(-1, 3) * L
        dx = L / nside
        return x, np.full(len(x), 2700.0 * dx**3), 2.0 * dx

    @staticmethod
    def _mat(damage: bool):
        from dartrift.cpu_reference.materials import (
            GravityParams,
            MaterialParams,
            PorosityParams,
            StrengthParams,
        )
        return MaterialParams(
            eos="tillotson",
            strength=StrengthParams(enabled=True, Y0=1.0e5, mu_f=0.8, YM=1.5e9,
                                    shear_G=G_SHEAR, jaumann=True),
            porosity=PorosityParams(enabled=False),
            gravity=GravityParams(enabled=False),
            damage=DamageParams(enabled=damage, k_weibull=1.0e29, m_weibull=9.0),
            density_method="continuity",
        )

    def _solve(self, damage: bool, v_scale: float, steps: int = 40):
        from dartrift.cpu_reference.sph_ref import RefParams
        from dartrift.warp_core.solver_solid import WarpSolid3D

        x, m, h = self._kafes()
        s = WarpSolid3D(x, x * v_scale, m, np.zeros(len(x)), h, self._mat(damage),
                        RefParams(cfl=0.25), device="cuda:0", check_every=10**9,
                        damage_seed=3)
        for _ in range(steps):
            s.step(s.compute_dt())
        return s

    def test_cekmede_hasar_buyur(self):
        self._needs_cuda()
        s = self._solve(True, v_scale=50.0)
        b = s.budgets()
        assert b["damage_max"] > 0.0
        assert b["strain_max"] > 0.0

    def test_basmada_ic_bolgede_hasar_olusmaz(self):
        """Ice dogru hiz -> basma -> IC BOLGEDE kusur acilmamali.

        IKI OLCUM TUZAGI, ikisi de olculerek ogrenildi:

        1. **"Ic bolge" secmek gerekli.** Kupun serbest yuzeyinde SPH cekirdegi
           eksiktir; hiz gradyani izotropik olmaktan cikar, kucuk bir deviatorik
           gerilme dogar ve bazi asal yonler cekmeye gecer. Bu hasar modelinin
           degil serbest yuzey ayriklastirmasinin ozelligidir.

        2. **Kisa kosmak gerekli.** Ilk denememde 40 adim kostum ve ic bolgede
           D = 1.0 buldum. Kusur modelde degildi: h=1 m, c_uzun ~ 3348 m/s ->
           kup boyu ses gecisi ~1.2e-3 s, 40 adim ise ~3.0e-3 s. Yani sikismali
           dalga serbest yuzeyden yansiyip CEKMEYE donmustu — bu gercek fizik
           (spallasyon) ve model dogru davraniyordu. Test yanlis ANA bakiyordu.
           Simdi yansimadan once, ses gecis suresinin acikca altinda olculur.
        """
        self._needs_cuda()
        from dartrift.cpu_reference.sph_ref import RefParams
        from dartrift.warp_core.solver_solid import WarpSolid3D

        x, m, h = self._kafes()
        s = WarpSolid3D(x, x * -50.0, m, np.zeros(len(x)), h, self._mat(True),
                        RefParams(cfl=0.25), device="cuda:0", check_every=10**9,
                        damage_seed=3)
        c_long = np.sqrt(4.0 / 3.0 * G_SHEAR / 2700.0)
        t_ses = 4.0 / c_long            # kup boyu ses gecis suresi
        t = 0.0
        adim = 0
        while t < 0.25 * t_ses:         # yansima YOK bolgesi
            dt = s.compute_dt()
            s.step(dt)
            t += dt
            adim += 1
        st = s.state_numpy()
        ic = np.all(np.abs(x) < 2.0 - h, axis=1)
        assert ic.sum() > 0, "ic bolge bos — kafes cok kucuk"
        assert t < t_ses, (t, t_ses)
        assert st["D"][ic].max() == 0.0, (
            f"basma altinda ({adim} adim, t={t:.3e}s < t_ses={t_ses:.3e}s) "
            f"ic bolgede hasar olustu: {st['D'][ic].max()}")

    def test_hasar_araliginda_ve_monoton(self):
        self._needs_cuda()
        from dartrift.cpu_reference.sph_ref import RefParams
        from dartrift.warp_core.solver_solid import WarpSolid3D

        x, m, h = self._kafes()
        s = WarpSolid3D(x, x * 50.0, m, np.zeros(len(x)), h, self._mat(True),
                        RefParams(cfl=0.25), device="cuda:0", check_every=10**9,
                        damage_seed=3)
        onceki = np.zeros(len(x))
        for _ in range(30):
            s.step(s.compute_dt())
            d = s.state_numpy()["D"]
            assert np.all(d >= 0.0) and np.all(d <= 1.0)
            assert np.all(d >= onceki - 1e-15), "HASAR GERI DONDU — onarim yok olmali"
            onceki = d

    def test_ablasyon_hasar_kapaliyken_ayni(self):
        """damage.enabled=False -> hasarsiz kosuyla BIT-AYNI olmali."""
        self._needs_cuda()
        a = self._solve(False, v_scale=50.0).state_numpy()
        b = self._solve(False, v_scale=50.0).state_numpy()
        assert np.array_equal(a["x"], b["x"])
        assert np.array_equal(a["D"], np.zeros(len(a["D"])))

    def test_hasar_durumu_bozmaz_tekrarli_eval(self):
        """REGRESYON: `_eval()` tekrar cagrilinca S BIRIKIMLI kuculmemeli.

        Bulunan kusur: `apply_damage_k` `S[i] = f*S[i]` diye YERINDE
        carpiyordu. `S` bir DURUM degiskenidir (`kick_S_3d` ile integre edilir,
        hicbir yerde yeniden hesaplanmaz) ve `_eval()` adim basina IKI kez
        cagrilir — yani S her adimda (1-D)^2 ile kuculuyordu, birikimli.

        Olculen (D = 0.5 sabit, hicbir fiziksel evrim yok):
            S0 = 1.0e7
            1./2./3./4. _eval() -> 5.0e6 / 2.5e6 / 1.25e6 / 6.25e5
        `P` kurtuluyordu cunku EOS onu her eval yeniden hesapliyor.

        Duzeltme: hasar AYRI dizilere (`P_eff`, `S_eff`) yazar; `S` durumuna
        dokunmaz. Bu test tam o davranisi kilitler."""
        self._needs_cuda()
        from dartrift.cpu_reference.sph_ref import RefParams
        from dartrift.warp_core.solver_solid import WarpSolid3D

        x, m, h = self._kafes()
        s = WarpSolid3D(x, np.zeros_like(x), m, np.zeros(len(x)), h,
                        self._mat(True), RefParams(cfl=0.25), device="cuda:0",
                        check_every=10**9, damage_seed=3)
        D = np.full(len(x), 0.5)
        S0 = np.zeros((len(x), 3, 3))
        S0[:, 0, 1] = S0[:, 1, 0] = 1.0e7
        s.S.assign(np.ascontiguousarray(S0))

        for _ in range(4):
            s.D.assign(D)                      # D sabit tut: buyume olmasin
            s.D_cbrt.assign(np.cbrt(D))
            s._eval()
            # DURUM bozulmamali
            assert s.S.numpy()[0, 0, 1] == pytest.approx(1.0e7, rel=1e-12), (
                "hasar DURUMU degistirdi — birikimli kuculme kusuru geri geldi")
            # TASINAN gerilme (1-D) ile zayiflamis olmali, HER SEFERINDE ayni
            assert s.S_eff.numpy()[0, 0, 1] == pytest.approx(0.5e7, rel=1e-12)

    def test_hasar_tasinan_gerilmeyi_zayiflatir(self):
        """`S_eff = (1-D) S` ve basma basinci DEGISMEZ."""
        self._needs_cuda()
        from dartrift.cpu_reference.sph_ref import RefParams
        from dartrift.warp_core.solver_solid import WarpSolid3D

        x, m, h = self._kafes()
        s = WarpSolid3D(x, np.zeros_like(x), m, np.zeros(len(x)), h,
                        self._mat(True), RefParams(cfl=0.25), device="cuda:0",
                        check_every=10**9, damage_seed=3)
        S0 = np.zeros((len(x), 3, 3))
        S0[:, 0, 1] = S0[:, 1, 0] = 1.0e7
        s.S.assign(np.ascontiguousarray(S0))
        for d in (0.0, 0.25, 1.0):
            s.D.assign(np.full(len(x), d))
            s.D_cbrt.assign(np.full(len(x), np.cbrt(d)))
            s._eval()
            assert s.S_eff.numpy()[0, 0, 1] == pytest.approx((1.0 - d) * 1.0e7,
                                                             rel=1e-12), d
            # basma (P>0) zayiflamamali
            p, pe = s.P.numpy(), s.P_eff.numpy()
            basma = p > 0.0
            if basma.any():
                assert np.allclose(pe[basma], p[basma]), "basma zayiflatildi"

    def test_hasar_sonucu_degistiriyor(self):
        """Hasar acikken sonuc kapaliyken ile AYNI OLMAMALI.

        Ayni cikarsa modul hic baglanmamis demektir — 'eklendi ama calismiyor'
        durumu bu testle yakalanir."""
        self._needs_cuda()
        a = self._solve(False, v_scale=50.0).state_numpy()
        b = self._solve(True, v_scale=50.0).state_numpy()
        assert not np.array_equal(a["x"], b["x"])

    def test_dayanimsiz_hasar_reddedilir(self):
        """Deviatorik gerilme yokken hasar modeli anlamsizdir."""
        self._needs_cuda()
        import dataclasses

        from dartrift.cpu_reference.materials import StrengthParams
        from dartrift.cpu_reference.sph_ref import RefParams
        from dartrift.warp_core.solver_solid import WarpSolid3D

        mat = self._mat(True)
        mat = dataclasses.replace(mat, strength=StrengthParams(enabled=False))
        x, m, h = self._kafes()
        with pytest.raises(ValueError, match="dayanim ister"):
            WarpSolid3D(x, np.zeros_like(x), m, np.zeros(len(x)), h, mat,
                        RefParams(), device="cuda:0")

    def test_gpu_asal_gerilme_cpu_ile_ayni(self):
        """GPU kapali-form ozdeger, CPU eigvalsh ile uyusmali."""
        self._needs_cuda()
        import warp as wp

        from dartrift.warp_core.damage_gradykipp import DamageWp

        rng = np.random.default_rng(9)
        n = 256
        S = rng.normal(size=(n, 3, 3)) * 1e7
        S = 0.5 * (S + np.transpose(S, (0, 2, 1)))
        P = rng.normal(size=n) * 1e8
        beklenen = max_principal_stress(P, S)

        from dartrift.warp_core.damage_gradykipp import (
            max_principal_stress as gpu_mps,
        )

        @wp.kernel
        def _k(P: wp.array(dtype=wp.float64), S: wp.array(dtype=wp.mat33d),
               dp: DamageWp, out: wp.array(dtype=wp.float64)):
            i = wp.tid()
            out[i] = gpu_mps(P[i], S[i])

        dp = DamageWp()
        dp.m_weibull = 9.0
        dp.crack_speed_frac = 0.4
        dp.r_s = 1.0
        dp.youngs_E = 1.0
        out = wp.zeros(n, dtype=wp.float64, device="cuda:0")
        wp.launch(_k, dim=n, inputs=[
            wp.array(P, dtype=wp.float64, device="cuda:0"),
            wp.array(S, dtype=wp.mat33d, device="cuda:0"), dp, out],
            device="cuda:0")
        got = out.numpy()
        olcek = np.maximum(np.abs(beklenen), 1e3)
        assert np.max(np.abs(got - beklenen) / olcek) < 1e-10


class TestFlawVolumeAndCrackPath:
    """ADR-0030 eki: kusur hacmi ile catlak yolu FARKLI hacimlerdir.

    Ikisi karistiriliyordu ve ikisi de olculebilir sekilde yanlisti:

      1. `r_s` (catlagin kat etmesi gereken uzunluk) KATI hacimden
         hesaplaniyordu. Catlak gozenekler dahil TUM parcacigi gecer, yani
         GEOMETRIK hacim gerekir. Olculdu (alpha=1.5): 3.8624 m yerine
         4.4214 m — %12,6 kucuk. dD/dt ~ 1/r_s oldugundan hasar %14,5 HIZLI
         buyuyordu.
      2. Kusurlar parcaciklara TEKDUZE dagitiliyordu (`rng.integers`). Bu
         yalnizca butun hacimler esitken dogrudur. ADR-0030'dan sonra moloz
         yigininda kusur hacmi gercekten degisiyor (blok 344.8 vs matris
         209.6 m^3, %56 yayilim) ve tekduze dagitim gozenekli matrise hak
         ettiginden fazla kusur verirdi.
    """

    def test_kusurlar_hacimle_orantili_dagitiliyor(self):
        """Iki kat hacim -> iki kat kusur."""
        n = 4000
        v = np.where(np.arange(n) < n // 2, 100.0, 200.0)
        _, nf = seed_flaws(n, v, DamageParams(enabled=True, k_weibull=1e29,
                                              m_weibull=9.0), 3)
        oran = nf[n // 2:].sum() / nf[:n // 2].sum()
        assert oran == pytest.approx(2.0, rel=0.05), oran

    def test_tekduze_hacimde_dagitim_duz(self):
        """Bosluk kontrolu: hacimler esitse hicbir yari ayricalikli olmamali."""
        n = 4000
        _, nf = seed_flaws(n, 150.0, DamageParams(enabled=True, k_weibull=1e29,
                                                  m_weibull=9.0), 3)
        oran = nf[n // 2:].sum() / nf[:n // 2].sum()
        assert oran == pytest.approx(1.0, rel=0.05), oran

    def test_hacimli_tohumlama_deterministik_ve_tohuma_duyarli(self):
        n = 500
        v = np.linspace(80.0, 300.0, n)
        dp = DamageParams(enabled=True, k_weibull=1e29, m_weibull=9.0)
        a, na = seed_flaws(n, v, dp, 7)
        b, nb = seed_flaws(n, v, dp, 7)
        c, _ = seed_flaws(n, v, dp, 8)
        assert np.array_equal(a, b) and np.array_equal(na, nb)
        assert not np.array_equal(a, c)

    def test_sifir_veya_negatif_hacim_reddediliyor(self):
        dp = DamageParams(enabled=True, k_weibull=1e29, m_weibull=9.0)
        with pytest.raises(ValueError, match="pozitif"):
            seed_flaws(4, np.array([1.0, 2.0, 0.0, 3.0]), dp, 1)

    def test_r_s_geometrik_hacimden_gelir(self):
        """`r_s` gozenekleri SAYAR; katı hacimden hesaplamak %14,5 hizli
        hasar veriyordu."""
        from dartrift.cpu_reference.materials import MaterialParams, PorosityParams, StrengthParams
        from dartrift.cpu_reference.solid_ref import SolidState, seed_solid_damage

        n, rho0, alpha = 200, 2700.0, 1.5
        v_geom = 362.04                      # kafeste kapladigi hacim
        m = np.full(n, (rho0 / alpha) * v_geom)
        st = SolidState(x=np.zeros((n, 3)), v=np.zeros((n, 3)), m=m,
                        u=np.zeros(n), h=1.0, active=np.ones(n, bool),
                        alpha=np.full(n, alpha))
        mat = MaterialParams(
            eos="tillotson",
            strength=StrengthParams(enabled=True),
            porosity=PorosityParams(enabled=True, alpha0=alpha),
            damage=DamageParams(enabled=True, k_weibull=1e29, m_weibull=9.0))
        seed_solid_damage(st, mat, seed=1)
        beklenen = (3.0 * v_geom / (4.0 * np.pi)) ** (1.0 / 3.0)
        assert st.r_s == pytest.approx(beklenen, rel=1e-12), (st.r_s, beklenen)
        # ESKI (katı hacimden) deger belirgin sekilde KUCUKTU — duzeltmenin olcusu
        eski = (3.0 * (v_geom / alpha) / (4.0 * np.pi)) ** (1.0 / 3.0)
        assert st.r_s / eski == pytest.approx(alpha ** (1.0 / 3.0), rel=1e-12)
        assert st.r_s > 1.10 * eski
