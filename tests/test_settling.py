"""Settling testleri (P3-FR-05, P3-VR-01).

GPU gerektirmeyen kisim burada; GPU'lu oturma kosusu `test_settling_gpu.py`
altinda ve `gpu` isaretiyle ayrilmistir (yerelde/TRUBA'da kosar, CI'da atlanir).
"""

import numpy as np
import pytest

from dartrift.setup.settling import G_GRAV, SettleResult, binding_energy


def test_baglanma_enerjisi_formulu():
    """(3/5) G M^2 / R — duzgun kure."""
    m, r = 1.0e9, 100.0
    assert binding_energy(m, r) == pytest.approx(0.6 * G_GRAV * m * m / r, rel=1e-14)


def test_baglanma_enerjisi_olcekleme():
    """M^2/R: kutle 2x -> 4x, yaricap 2x -> 1/2x."""
    e0 = binding_energy(1.0e9, 100.0)
    assert binding_energy(2.0e9, 100.0) / e0 == pytest.approx(4.0, rel=1e-14)
    assert binding_energy(1.0e9, 200.0) / e0 == pytest.approx(0.5, rel=1e-14)


def test_baglanma_enerjisi_pozitif_yaricap_ister():
    for r in (0.0, -1.0):
        with pytest.raises(ValueError, match="yaricap"):
            binding_energy(1.0, r)


def test_dimorphos_baglanma_enerjisi_buyuklugu():
    """Dis kaynak capraz kontrolu: Dimorphos icin E_bag ~ 9e6 J mertebesi.

    M ~ 4.3e9 kg, R ~ 82 m (Daly ve digerleri 2023, DART sonuclari).
    Bu, DART'in getirdigi ~1.1e10 J kinetik enerjinin ~1/1200'u — yani
    carpma, hedefi baglayan enerjiden mertebelerce buyuktur. Mertebe
    tutmuyorsa ya sabit ya formul yanlistir.
    """
    e = binding_energy(4.3e9, 82.0)
    assert 1.0e6 < e < 1.0e8, e
    # DART: 579.4 kg @ 6144.9 m/s -> E_kin / E_bag ~ 1e3
    assert 100.0 < (0.5 * 579.4 * 6144.9**2) / e < 1.0e4
    # kacis hizi ~ sqrt(2GM/R) ~ 8-9 cm/s olmali
    v_kac = np.sqrt(2.0 * G_GRAV * 4.3e9 / 82.0)
    assert 0.05 < v_kac < 0.15, v_kac


def test_sonuc_kabi_varsayilanlari():
    r = SettleResult(x=np.zeros((2, 3)), v=np.zeros((2, 3)),
                     rho=np.ones(2), alpha=np.ones(2), n_steps=0, t_end=0.0)
    assert r.converged is False          # sessizce "oldu" demez
    assert r.ke_series == [] and r.diagnostics == {}


def test_yercekimi_kapaliysa_reddeder():
    """Sartname oz-yercekimi altinda oturtma istiyor; kapaliysa sessizce
    'duz uzayda gevseme' yapip buna settling demek yanlis olur."""
    from dartrift.cpu_reference.materials import GravityParams, MaterialParams

    mat = MaterialParams(gravity=GravityParams(enabled=False))
    from dartrift.setup.settling import settle_pile
    with pytest.raises(ValueError, match="oz-yercekimi"):
        settle_pile(None, mat)


@pytest.mark.gpu
class TestSettlingGPU:
    """Kombinasyon sinavlari: settling + heterojen malzeme + agac denetimi.

    Bunlar ayri ayri test edilmisti; birlikte kosulmamislardi. Bu projedeki
    kusurlarin cogu tam bu bosluktan cikti (ADR-0022: sureklilik + porozite
    hic birlikte kosulmamisti)."""

    @staticmethod
    def _kur():
        from dartrift.cpu_reference.materials import (
            GravityParams,
            MaterialParams,
            PorosityParams,
            StrengthParams,
        )
        from dartrift.setup.rubble_generator import build_rubble_pile
        from dartrift.setup.shape_mesh import icosphere

        mat = MaterialParams(
            eos="tillotson",
            strength=StrengthParams(enabled=True, Y0=1.0e4, mu_f=0.6, YM=1.5e9,
                                    shear_G=2.27e10, jaumann=True),
            porosity=PorosityParams(enabled=True, alpha0=1.6, Pe=1.0e6,
                                    Ps=1.0e8, n_exp=2.0),
            gravity=GravityParams(enabled=True, G=G_GRAV, eps=0.0,
                                  mode="barnes_hut", theta=0.5),
            density_method="continuity",
        )
        pile = build_rubble_pile(
            icosphere(3, 60.0), spacing=8.0, bulk_density=1800.0, root_seed=5,
            rho0_solid=2700.0, model_class="M1", f_boulder=0.2, q=3.0,
            r_min=16.0, r_max=32.0)
        return mat, pile

    def _needs_cuda(self):
        from dartrift.particles import warp_available, warp_devices

        if not warp_available() or not any(
                d.startswith("cuda") for d in warp_devices()):
            pytest.skip("CUDA yok")

    def test_baslangic_durumu_tam_denge(self):
        """t=0'da SPH ivmesi TAM sifir; dengesiz tek kuvvet yercekimi.

        ADR-0024'un dayanagi budur. Sifir olmazsa settling'in anlami degisir
        ve P3-VR-01 baska bir sey olcuyor demektir."""
        self._needs_cuda()
        from dartrift.setup.settling import settle_pile

        mat, pile = self._kur()
        r = settle_pile(pile, mat, max_steps=40, report_every=40)
        assert r.diagnostics["a_sph_max_t0"] == 0.0
        assert r.diagnostics["a_gravity_max_t0"] > 0.0

    def test_esik_altinda_ve_yakinsadi(self):
        self._needs_cuda()
        from dartrift.setup.settling import settle_pile

        mat, pile = self._kur()
        r = settle_pile(pile, mat, max_steps=40, report_every=40)
        assert r.converged is True
        assert r.ke_final < r.ke_threshold
        assert np.isfinite([r.ke_final, r.diagnostics["rho_min"],
                            r.diagnostics["rho_max"]]).all()

    def test_parcacik_basina_Y0_cozucuye_ulasiyor(self):
        """Yigin blok/matris icin AYRI Y0 uretiyor; settling bunu gecirmezse
        bloklar gozeneksiz ama matris kadar zayif olurdu — yarim baglanmis
        heterojenlik, hic olmamasindan daha yaniltici."""
        self._needs_cuda()
        from dartrift.cpu_reference.sph_ref import RefParams
        from dartrift.warp_core.solver_solid import WarpSolid3D

        mat, pile = self._kur()
        assert len(np.unique(pile.Y0)) > 1, "yigin heterojen Y0 uretmedi"
        s = WarpSolid3D(np.ascontiguousarray(pile.x), np.zeros((pile.n, 3)),
                        pile.m, np.zeros(pile.n), 16.0, mat, RefParams(),
                        alpha0=np.ascontiguousarray(pile.alpha0),
                        Y0=np.ascontiguousarray(pile.Y0), device="cuda:0")
        assert np.array_equal(s.Y0.numpy(), pile.Y0)

    def test_parcacik_basina_Y0_SONUCU_degistiriyor(self):
        """Diziyi tasimak yetmez: akma dayanimi gercekten farkli mi davraniyor?

        Onceki test yalnizca `s.Y0` dizisinin SAKLANDIGINI denetliyordu. Dizi
        yerinde durup cekirdek skaler `mat.strength.Y0` kullansaydi o test yine
        gecerdi — heterojenlik kozmetik olurdu. Bu, hasar kusuruyla ayni sinif:
        parca dogru, butun sinanmamis.

        BU TESTIN ILK HALI KALDI VE TAHMINI YANLISTI. "Zayif kohezyon daha cok
        plastik is uretir" diye yazmistim (akma daha erken baslar). Olculen tam
        tersi cikti. Ters cevirmeden once ILISKI olculdu (is 1448928, H100,
        ayni kurulum, uc kol):

            kol           Y0_ort       plastik is
            hepsi-zayif   1,0000e+04   1,459238e+07 J
            heterojen     2,3565e+06   1,890912e+09 J
            hepsi-guclu   1,0000e+07   1,264309e+10 J

            heterojen / hepsi-zayif  = 129,58
            hepsi-guclu/ heterojen   =   6,69
            hepsi-guclu/ hepsi-zayif = 866,42   (Y0 orani 1000)

        FIZIK: tam plastik rejimde dagilim hizi sigma_akma * eps_nokta_p'dir,
        yani is yield gerilmesiyle ARTAR. Akmanin BASLANGICI ile BUYUKLUGUNU
        karistirmistim: dusuk Y0'da akma erken baslar ama her adimda cok az
        enerji atar; yuksek Y0'da gec baslar ve cok atar. Ikincisi baskin
        (866 kat / 1000 kat — hafif alt-dogrusal, cunku yuksek Y0'da bir kisim
        elastik kalir).

        ASIL KANIT KUSATMADIR: heterojen deger iki HOMOJEN sinirin TAM
        ARASINDA. Cekirdek herhangi bir SKALER kullansaydi heterojen kosu
        sinirlardan birine OTURURDU. Ustelik het/zayif = 129,58 iken ortalama
        Y0 orani 235,65 — yani sonuc ortalamanin da degil, gercek bir
        karisimin sonucu.
        """
        self._needs_cuda()
        from dartrift.cpu_reference.sph_ref import RefParams
        from dartrift.warp_core.solver_solid import WarpSolid3D

        mat, pile = self._kur()
        y_het = np.ascontiguousarray(pile.Y0)
        assert len(np.unique(y_het)) > 1

        def kos(y0):
            s = WarpSolid3D(np.ascontiguousarray(pile.x),
                            np.ascontiguousarray(pile.x) * 2.0,   # akmayi tetikle
                            pile.m, np.zeros(pile.n), 16.0, mat, RefParams(cfl=0.2),
                            alpha0=np.ascontiguousarray(pile.alpha0),
                            Y0=np.ascontiguousarray(y0), device="cuda:0",
                            check_every=10**9)
            for _ in range(20):
                s.step(s.compute_dt())
            return s.plastic_u_total

        pl_zayif = kos(np.full(pile.n, float(y_het.min())))
        pl_het = kos(y_het)
        pl_guclu = kos(np.full(pile.n, float(y_het.max())))

        # 1) MONOTONLUK: plastik is yield gerilmesiyle artar
        assert pl_zayif < pl_het < pl_guclu, (
            f"plastik is Y0 ile monoton artmali: zayif={pl_zayif:.6e}, "
            f"heterojen={pl_het:.6e}, guclu={pl_guclu:.6e}")
        # 2) KUSATMA: heterojen SINIRLARA OTURMAMALI — otururdu ise cekirdek
        #    parcacik basina diziyi degil bir skaleri kullaniyor demektir
        assert pl_het > 1.5 * pl_zayif, "heterojen, hepsi-zayif sinirina oturdu"
        assert pl_het < 0.67 * pl_guclu, "heterojen, hepsi-guclu sinirina oturdu"
        # 3) ETKI BUYUKLUGU: Y0 1000 kat degisince is en az 100 kat degismeli
        #    (olculen 866; esik brittle olmasin diye genis)
        assert pl_guclu / pl_zayif > 100.0, (
            f"Y0'in 1000 kat degismesi isi yalnizca "
            f"{pl_guclu / pl_zayif:.1f} kat degistirdi")

    def test_agac_suruklenmesi_yalnizca_K1_disinda_izlenir(self):
        """K=1'de yaklasiklik yok -> izleme de yok (her adim v kopyalamak bos
        maliyet). K>1'de denetim kaydi DOLU olmali."""
        self._needs_cuda()
        from dartrift.setup.settling import settle_pile

        mat, pile = self._kur()
        r1 = settle_pile(pile, mat, max_steps=40, report_every=40,
                         gravity_rebuild_every=1)
        assert r1.diagnostics["tree_drift_max_over_h"] is None
        r8 = settle_pile(pile, mat, max_steps=40, report_every=40,
                         gravity_rebuild_every=8)
        assert r8.diagnostics["tree_drift_max_over_h"] is not None
        assert r8.diagnostics["tree_drift_exceeded"] == 0

    def test_gecersiz_agac_araligi_reddedilir(self):
        self._needs_cuda()
        from dartrift.setup.settling import settle_pile

        mat, pile = self._kur()
        with pytest.raises(ValueError, match="gravity_rebuild_every"):
            settle_pile(pile, mat, max_steps=1, gravity_rebuild_every=0)
        with pytest.raises(ValueError, match="gravity_drift_tol"):
            settle_pile(pile, mat, max_steps=1, gravity_drift_tol=0.0)


def test_gecersiz_sonumleme_reddedilir():
    from dartrift.cpu_reference.materials import GravityParams, MaterialParams
    from dartrift.setup.settling import settle_pile

    mat = MaterialParams(gravity=GravityParams(enabled=True))
    for d in (-0.1, 1.0, 1.5):
        with pytest.raises(ValueError, match="damping"):
            settle_pile(None, mat, damping=d)
