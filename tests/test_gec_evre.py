"""ADR-0050 — geç evre hızlı entegrasyon şeması ve uzak kaçan dondurma.

Kaynak: Raducan & Jutzi 2022 (*PSJ* 3, 128), Raducan ve diğ. 2022
(Hayabusa2 SCI) — `docs/LITERATUR-DART-SIMULASYONLARI.md` L1, L3.
"""
from __future__ import annotations

import inspect

import numpy as np
import pytest

from dartrift.cpu_reference import sph_ref as R
from dartrift.cpu_reference.materials import (
    ALUMINYUM_TILLOTSON,
    DamageParams,
    GravityParams,
    MaterialParams,
    PorosityParams,
    StrengthParams,
)
from dartrift.particles import warp_available

pytestmark = pytest.mark.skipif(not warp_available(), reason="warp yok")

ALFA0 = 1.3
RHO0 = 2700.0
A_GEC = 1.0e5


def _mat(**kw):
    return MaterialParams(
        eos="tillotson", density_method="continuity",
        strength=StrengthParams(enabled=True, Y0=1e4, mu_f=0.6, YM=1.5e9,
                                shear_G=2.27e10),
        porosity=PorosityParams(enabled=True, alpha0=ALFA0, Pe=1e6, Ps=1e8,
                                n_exp=2.0),
        gravity=GravityParams(enabled=False), **kw)


def _kafes():
    g = np.arange(-2, 3) * 0.5
    return np.stack(np.meshgrid(g, g, g, indexing="ij"), -1).reshape(-1, 3)


def _cozucu(*, rho=None, S0=None, v=None, mat=None, **kw):
    from dartrift.warp_core.solver_solid import WarpSolid3D

    x = _kafes()
    n = len(x)
    rho_d = np.full(n, RHO0 / ALFA0) if rho is None else rho
    if S0 is None:
        S0 = np.zeros((n, 3, 3))
        S0[:, 0, 1] = S0[:, 1, 0] = 2.0e3
    s = WarpSolid3D(x, np.zeros_like(x) if v is None else v,
                    np.full(n, RHO0 / ALFA0 * 0.125), np.zeros(n), 0.65,
                    mat or _mat(), R.RefParams(), S0=S0,
                    alpha0=np.full(n, ALFA0), rho_durum=rho_d, device="cpu", **kw)
    s.hazirla()
    return s


def test_varsayilan_GECIS_YOK_ve_kayma_modulu_malzemeninki():
    s = _cozucu()
    assert s.gec_evre is None
    assert s._G_etkin == _mat().strength.shear_G
    assert s.dondurulmus_sayisi == 0


def test_KAYNAK_kayma_modulu_her_yerde_ETKIN_degerden_okunuyor():
    """Gerilme hızı, dt ve enerji tanısı aynı `G`'yi görmeli; biri eski
    değerde kalırsa geçiş sessizce yarım uygulanır."""
    from dartrift.warp_core import solver_solid

    kaynak = inspect.getsource(solver_solid.WarpSolid3D)
    assert "F(self.mat.strength.shear_G)" not in kaynak
    assert "self.mat.strength.shear_G / rho" not in kaynak
    assert kaynak.count("self._G_etkin") >= 5


def test_gecis_BASINCI_yeni_EOS_A_gec_mu_bolu_alpha():
    n = len(_kafes())
    rho = np.full(n, RHO0 / ALFA0)
    rho[3] = 1.02 * RHO0 / ALFA0          # rho*alpha/rho0 = 1,02 -> mu = 0,02
    s = _cozucu(rho=rho)
    P_once = s.P.numpy()[3]
    s.gec_evreye_gec(A_GEC, t=0.5)
    P = s.P.numpy()
    mu = rho[3] * ALFA0 / RHO0 - 1.0
    assert P[3] == pytest.approx(A_GEC * mu / ALFA0, rel=1e-9)
    assert abs(P[3]) < 1e-4 * abs(P_once)   # eski Tillotson'dan ~5 mertebe kucuk


def test_gecis_SES_HIZI_ve_ZAMAN_ADIMI_buyuyor():
    s = _cozucu()
    cs_once = float(np.median(s.cs.numpy()))
    dt_once = s.compute_dt()
    k = s.gec_evreye_gec(A_GEC)
    cs = float(np.median(s.cs.numpy()))
    assert cs == pytest.approx(np.sqrt(A_GEC / RHO0), rel=1e-3)
    assert cs < 1e-2 * cs_once
    assert s.compute_dt() > 50.0 * dt_once
    assert k["oran"] == pytest.approx(A_GEC / _mat().tillotson.A)


def test_gecis_KAYMA_MODULU_ve_GERILME_ayni_oranla_olcekleniyor():
    s = _cozucu()
    S_once = s.S.numpy().copy()
    k = s.gec_evreye_gec(A_GEC)
    assert s._G_etkin == pytest.approx(_mat().strength.shear_G * k["oran"])
    np.testing.assert_allclose(s.S.numpy(), S_once * k["oran"], rtol=1e-12)


def test_gerilme_olcekle_False_S_DOKUNULMUYOR():
    s = _cozucu()
    S_once = s.S.numpy().copy()
    s.gec_evreye_gec(A_GEC, gerilme_olcekle=False)
    np.testing.assert_array_equal(s.S.numpy(), S_once)


def test_gecis_KINETIK_ve_IC_ENERJI_surekli():
    rng = np.random.default_rng(3)
    v = rng.normal(0.0, 2.0, (len(_kafes()), 3))
    s = _cozucu(v=v)
    for _ in range(3):
        s.step(1e-6)
    b0 = s.budgets()
    s.gec_evreye_gec(A_GEC)
    b1 = s.budgets()
    assert b1["e_kin"] == b0["e_kin"]
    assert b1["e_int"] == b0["e_int"]


def test_MERMI_EOS_de_geciyor():
    n = len(_kafes())
    maske = np.zeros(n, bool)
    maske[:5] = True
    rho = np.full(n, RHO0 / ALFA0)
    rho[:10] = 1.01 * RHO0 / ALFA0
    s = _cozucu(rho=rho, mermi_tillotson=ALUMINYUM_TILLOTSON, mermi_maske=maske)
    s.gec_evreye_gec(A_GEC)
    P = s.P.numpy()
    mu = 1.01 - 1.0
    # mermi (0-4) ve hedef (5-9) ayni yumusak EOS: ikisi de A_gec * mu / alpha
    np.testing.assert_allclose(P[:10], A_GEC * mu / ALFA0, rtol=1e-6)


@pytest.mark.parametrize("A", [0.0, -1.0, float("nan"), 3.0e10])
def test_gecersiz_A_REDDEDILIYOR(A):
    s = _cozucu()
    with pytest.raises(ValueError, match="A_gec"):
        s.gec_evreye_gec(A)


def test_IKINCI_gecis_REDDEDILIYOR():
    s = _cozucu()
    s.gec_evreye_gec(A_GEC)
    with pytest.raises(ValueError, match="ikinci"):
        s.gec_evreye_gec(A_GEC)


def test_HASAR_modeliyle_REDDEDILIYOR():
    s = _cozucu(mat=_mat(damage=DamageParams(enabled=True)))
    with pytest.raises(ValueError, match="hasar"):
        s.gec_evreye_gec(A_GEC)


def test_gecisten_sonra_kosu_SONLU_kaliyor():
    rng = np.random.default_rng(5)
    v = rng.normal(0.0, 1.0, (len(_kafes()), 3))
    s = _cozucu(v=v)
    s.gec_evreye_gec(A_GEC)
    for _ in range(20):
        s.step(s.compute_dt())
    st = s.state_numpy()
    for k in ("x", "v", "u", "rho", "P", "S"):
        assert np.all(np.isfinite(st[k])), k


# ---------------------------------------------------------------- dondurma
def _uzak_cozucu():
    n = len(_kafes())
    v = np.zeros((n, 3))
    s = _cozucu(v=v)
    x = s.x.numpy().astype(np.float64)
    # 0: uzakta ve disa hizli -> dondurulur
    # 1: uzakta ama iceri       -> dondurulmez
    # 2: yakinda ve disa hizli  -> dondurulmez
    x[0] = [30.0, 0.0, 0.0]
    x[1] = [0.0, 30.0, 0.0]
    x[2] = [1.5, 0.0, 0.0]
    vv = s.v.numpy().astype(np.float64)
    vv[0] = [50.0, 0.0, 0.0]
    vv[1] = [0.0, -50.0, 0.0]
    vv[2] = [50.0, 0.0, 0.0]
    import warp as wp

    s.x = wp.array(x, dtype=wp.vec3d, device="cpu")
    s.v = wp.array(vv, dtype=wp.vec3d, device="cpu")
    return s


def test_uzak_ve_disa_kacan_DONDURULUYOR_digerleri_degil():
    s = _uzak_cozucu()
    k = s.uzak_kacanlari_dondur(R=1.0, v_esc=1.0, k_uzak=3.0)
    act = s.active.numpy().astype(bool)
    assert k == 1 and s.dondurulmus_sayisi == 1
    assert not act[0] and act[1] and act[2]
    # ikinci cagri ayni parcacigi yeniden saymaz
    assert s.uzak_kacanlari_dondur(R=1.0, v_esc=1.0, k_uzak=3.0) == 0


def test_dondurulan_parcacik_HAREKET_ETMIYOR():
    s = _uzak_cozucu()
    s.uzak_kacanlari_dondur(R=1.0, v_esc=1.0, k_uzak=3.0)
    x0 = s.x.numpy()[0].copy()
    v0 = s.v.numpy()[0].copy()
    for _ in range(3):
        s.step(1e-6)
    np.testing.assert_array_equal(s.x.numpy()[0], x0)
    np.testing.assert_array_equal(s.v.numpy()[0], v0)


def test_k_uzak_birden_kucuk_REDDEDILIYOR():
    s = _cozucu()
    with pytest.raises(ValueError, match="k_uzak"):
        s.uzak_kacanlari_dondur(R=1.0, v_esc=1.0, k_uzak=1.0)


# ------------------------------------------------------- A92: donmus etkilesim
def _yercekimli_bulut():
    """Yerçekimi açık küçük bulut + uzakta dışa kaçan tek parçacık."""
    from dartrift.warp_core.solver_solid import WarpSolid3D

    x = _kafes()
    n = len(x)
    x = np.vstack([x, [[40.0, 0.0, 0.0]]])
    v = np.zeros((n + 1, 3))
    v[-1] = [30.0, 0.0, 0.0]
    m = np.full(n + 1, RHO0 / ALFA0 * 0.125)
    m[-1] = 50.0 * m[0]                        # agir: tek yonlu cekim belirgin olsun
    mat = MaterialParams(
        eos="tillotson", density_method="continuity",
        strength=StrengthParams(enabled=True, Y0=1e4, mu_f=0.6, YM=1.5e9,
                                shear_G=2.27e10),
        porosity=PorosityParams(enabled=True, alpha0=ALFA0, Pe=1e6, Ps=1e8,
                                n_exp=2.0),
        gravity=GravityParams(enabled=True, G=6.6743e-3, eps=0.1, mode="direct"))
    s = WarpSolid3D(x, v, m, np.zeros(n + 1), 0.65, mat, R.RefParams(),
                    alpha0=np.full(n + 1, ALFA0),
                    rho_durum=np.full(n + 1, RHO0 / ALFA0), device="cpu")
    s.hazirla()
    return s


def _P(s):
    st = s.state_numpy()
    return st["m"] @ st["v"]


def test_A92_dondurma_yoksa_etkilesim_kutlesi_AYNI_NESNE():
    s = _cozucu()
    assert s._m_etk is s.m


def test_A92_donmus_parcacik_ETKILESIMDEN_cikiyor_gercek_kutle_kaliyor():
    s = _yercekimli_bulut()
    m_once = s.m.numpy().copy()
    assert s.uzak_kacanlari_dondur(R=1.5, v_esc=1.0, k_uzak=3.0) == 1
    assert s._m_etk.numpy()[-1] == 0.0
    np.testing.assert_array_equal(s.m.numpy(), m_once)        # gercek kutle
    np.testing.assert_array_equal(s._m_etk.numpy()[:-1], m_once[:-1])


def test_A92_donmus_parcacikla_MOMENTUM_KORUNUYOR():
    """İlk sürümde donmuş parçacık gövdeyi tek yönlü çekiyordu; toplam
    momentum (gerçek kütlelerle) her adımda kayıyordu."""
    s = _yercekimli_bulut()
    s.uzak_kacanlari_dondur(R=1.5, v_esc=1.0, k_uzak=3.0)
    P0 = _P(s)
    for _ in range(30):
        s.step(1e-5)
    olcek = abs(P0[0]) + 1e-300
    assert np.max(np.abs(_P(s) - P0)) / olcek < 1e-10


def test_A92_DONMADAN_once_cekim_GERCEKTEN_etkili():
    """Sınavın kör olmadığını göster: dondurmadan önce uzak ağır parçacık
    buluta anlamlı ivme veriyor (yani sıfırlama bir şeyi değiştiriyor)."""
    s = _yercekimli_bulut()
    m = s.m.numpy()[:-1]
    # Bulutun NET cekim kuvveti: ic kuvvetler ciftler halinde sifirlanir,
    # geriye yalniz uzak agir parcacigin cekimi kalir.
    F_once = m @ s.g.numpy()[:-1]
    s.uzak_kacanlari_dondur(R=1.5, v_esc=1.0, k_uzak=3.0)
    s.hazirla()
    F_sonra = m @ s.g.numpy()[:-1]
    assert abs(F_once[0]) > 0.0
    assert abs(F_sonra[0]) < 1e-9 * abs(F_once[0])



def test_A94_akma_yapisi_da_ETKIN_kayma_modulunu_goruyor():
    """Plastik iş tanısı (`plastic_du`) akma çekirdeğinde `sp.shear_G` ile
    hesaplanıyor; geçişte yapı yenilenmezse tanı `1/oran` kat yanlış olur."""
    s = _cozucu()
    assert s._sp.shear_G == s._G_etkin
    s.gec_evreye_gec(A_GEC)
    assert s._sp.shear_G == pytest.approx(s._G_etkin, rel=1e-15)
    assert s._sp.Y0 == _mat().strength.Y0 and s._sp.mu_f == _mat().strength.mu_f


def test_A94_gecis_sonrasi_plastik_is_ETKIN_G_ile_hesaplaniyor():
    """`S` ölçeklenmeden geçiş (`gerilme_olcekle=False`): aynı `S`, `oran`
    kat küçük `G` → elastik enerji `S²/(4Gρ)` ve plastik iş `1/oran` kat
    büyük olmalı. Yapı yenilenmeseydi (A94 öncesi) çekirdek eski `G`'yi
    kullanır ve oran `~1` çıkardı — sınav bunu ayırt ediyor."""
    n = len(_kafes())
    S0 = np.zeros((n, 3, 3))
    S0[:, 0, 1] = S0[:, 1, 0] = 5.0e4          # akma siniri (1e4) USTUNDE
    a = _cozucu(S0=S0.copy())
    a.step(1e-7)
    once = float(np.max(a.plastic_du.numpy()))
    b = _cozucu(S0=S0.copy())
    b.gec_evreye_gec(A_GEC, gerilme_olcekle=False)
    b.step(1e-7)
    sonra = float(np.max(b.plastic_du.numpy()))
    assert once > 0.0 and sonra > 0.0
    oran = A_GEC / _mat().tillotson.A
    assert sonra / once == pytest.approx(1.0 / oran, rel=0.5)
