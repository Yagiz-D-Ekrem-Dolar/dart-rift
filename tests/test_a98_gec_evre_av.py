"""A98 — geç evrede yapay viskozite (AV) tanısı ve geçişte AV katsayıları.

Rapor A98: geç evrede (düşük ses hızlı malzeme) Monaghan AV'sinin gerilmesi
`~ ρ α c h |∇v|` ve `h` ile doğrusal ölçekleniyor. Bu sınavlar (1) tanının
çözücünün gerçekten uyguladığı AV'yi ölçtüğünü, (2) fiziğe dokunmadığını,
(3) geçişte katsayı değişiminin yalnız istenince olduğunu, (4) AV gücünün
aynı akış alanında `h` ile doğrusal büyüdüğünü sınar.
"""
from __future__ import annotations

import numpy as np
import pytest

from dartrift.cpu_reference import sph_ref as R
from dartrift.cpu_reference.materials import (
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


def _mat():
    return MaterialParams(
        eos="tillotson", density_method="continuity",
        strength=StrengthParams(enabled=True, Y0=10.0, mu_f=0.6, YM=1.5e9,
                                shear_G=2.27e10),
        porosity=PorosityParams(enabled=True, alpha0=ALFA0, Pe=1e6, Ps=1e8,
                                n_exp=2.0),
        gravity=GravityParams(enabled=False))


def _kafes(n_kenar: int, s: float, rng=None, gurultu: float = 0.0):
    g = (np.arange(n_kenar) - 0.5 * (n_kenar - 1)) * s
    x = np.stack(np.meshgrid(g, g, g, indexing="ij"), -1).reshape(-1, 3)
    if rng is not None and gurultu > 0.0:
        x = x + rng.uniform(-gurultu * s, gurultu * s, x.shape)
    return x


def _cozucu(x, v, s, *, num=None, komsu="hash"):
    from dartrift.warp_core.solver_solid import WarpSolid3D

    n = len(x)
    m = np.full(n, RHO0 / ALFA0 * s ** 3)
    sol = WarpSolid3D(x, v, m, np.zeros(n), 2.0 * s, _mat(),
                      num or R.RefParams(), alpha0=np.full(n, ALFA0),
                      device="cpu", komsu_arama=komsu)
    sol.hazirla()
    return sol


def _sikisma_akisi(x, eps=0.05):
    """Düzgün tek eksenli sıkışma `v = -ε x x̂`: div = -ε, curl = 0 → Balsara ~1."""
    v = np.zeros_like(x)
    v[:, 0] = -eps * x[:, 0]
    return v


# ------------------------------------------------------------ tanı doğruluğu
def test_tani_COZUCUNUN_UYGULADIGI_AV_ile_ayni():
    """AV açık ve kapalı iki çözücünün `dudt` ve ivme farkı = tanının AV'si."""
    rng = np.random.default_rng(3)
    s = 0.5
    x = _kafes(6, s, rng, 0.1)
    v = _sikisma_akisi(x)
    acik = _cozucu(x, v, s, num=R.RefParams(alpha_av=1.0, beta_av=2.0))
    kapali = _cozucu(x, v, s, num=R.RefParams(alpha_av=0.0, beta_av=0.0))
    d = acik.av_tanisi()
    fark_du = acik.dudt.numpy() - kapali.dudt.numpy()
    m = acik.m.numpy()
    assert d["P_av"] == pytest.approx(float(np.sum(m * fark_du)), rel=1e-10)
    assert d["P_av"] > 0.0
    fark_a = np.linalg.norm(acik.a.numpy() - kapali.a.numpy(), axis=1)
    assert np.max(fark_a) > 0.0
    # ivme payi (0, 1]; burada gerilme yok (P = 0, S = 0) -> tamami AV
    assert d["av_ivme_payi"] == pytest.approx(1.0)


def test_tani_FIZIGE_DOKUNMUYOR():
    rng = np.random.default_rng(4)
    s = 0.5
    x = _kafes(5, s, rng, 0.1)
    sol = _cozucu(x, _sikisma_akisi(x), s)
    once = {k: np.array(v, copy=True) for k, v in sol.state_numpy().items()}
    a_once = sol.a.numpy().copy()
    sol.av_tanisi()
    sonra = sol.state_numpy()
    for k, v in once.items():
        assert np.array_equal(v, sonra[k]), k
    assert np.array_equal(a_once, sol.a.numpy())


def test_tani_HASH_ve_BVH_ayni_gucu_veriyor():
    rng = np.random.default_rng(5)
    s = 0.5
    x = _kafes(5, s, rng, 0.1)
    v = _sikisma_akisi(x)
    ph = _cozucu(x, v, s, komsu="hash").av_tanisi()["P_av"]
    pb = _cozucu(x, v, s, komsu="bvh").av_tanisi()["P_av"]
    assert pb == pytest.approx(ph, rel=1e-9)


def test_tani_AV_KAPALIYKEN_sifir():
    s = 0.5
    x = _kafes(4, s)
    d = _cozucu(x, _sikisma_akisi(x), s,
                num=R.RefParams(alpha_av=0.0, beta_av=0.0)).av_tanisi()
    assert d["P_av"] == 0.0
    assert d["av_ivme_payi"] == 0.0


# ------------------------------------------------------ geçişte katsayılar
def test_gecis_AV_VERILMEZSE_ayni_nesne_bit_ayni():
    s = 0.5
    x = _kafes(4, s)
    sol = _cozucu(x, np.zeros_like(x), s)
    num_once = sol.num
    b = sol.gec_evreye_gec(A_GEC)
    assert sol.num is num_once
    assert b["av_once"] == b["av_sonra"] == [1.0, 2.0]


def test_gecis_AV_VERILINCE_katsayilar_ve_dt_degisiyor():
    rng = np.random.default_rng(6)
    s = 0.5
    x = _kafes(5, s, rng, 0.1)
    v = _sikisma_akisi(x, eps=5.0)
    a1 = _cozucu(x, v, s)
    a2 = _cozucu(x, v, s)
    a1.gec_evreye_gec(A_GEC)
    b = a2.gec_evreye_gec(A_GEC, alpha_av=0.1, beta_av=0.2)
    assert b["av_sonra"] == [0.1, 0.2]
    assert a2.num.alpha_av == 0.1 and a2.num.beta_av == 0.2
    # AV zaman adimini da kisitliyordu: kucuk AV -> dt buyuk ya da esit
    assert a2.compute_dt() >= a1.compute_dt()
    assert a2.av_tanisi()["P_av"] < a1.av_tanisi()["P_av"]


@pytest.mark.parametrize("kw", [{"alpha_av": -0.1}, {"beta_av": float("nan")}])
def test_gecis_GECERSIZ_AV_REDDEDILIYOR(kw):
    s = 0.5
    x = _kafes(4, s)
    sol = _cozucu(x, np.zeros_like(x), s)
    with pytest.raises(ValueError):
        sol.gec_evreye_gec(A_GEC, **kw)


# ----------------------------------------------------- mekanizma: h ile ölçek
def test_MEKANIZMA_ayni_akista_AV_gucu_h_ile_DOGRUSAL_buyuyor():
    """A98'in çekirdeği: aynı fiziksel akış, aralık yarıya → AV gücü ~yarıya.

    İki kafes aynı küpü doldurur (kenar 6 m), aynı sıkışma alanı, geç evre
    EOS'u. Kenar etkisinden kaçmak için yalnız küpün iç yarısı ölçülür.
    Fiziksel bir viskozite çözünürlükten BAĞIMSIZ olurdu (oran ~1).
    """
    L = 6.0
    oranlar = []
    guc = {}
    for s in (0.75, 0.375):
        n_k = int(round(L / s))
        x = _kafes(n_k, s, np.random.default_rng(11), 0.05)
        v = _sikisma_akisi(x, eps=0.05)
        sol = _cozucu(x, v, s)
        sol.gec_evreye_gec(A_GEC)
        ic = np.all(np.abs(x) < 0.25 * L, axis=1)
        d = sol.av_tanisi(maske=ic)
        # birim hacim basina guc
        guc[s] = d["P_av"] / (float(ic.sum()) * s ** 3)
    oranlar.append(guc[0.75] / guc[0.375])
    # h iki kat -> guc ~iki kat (dogrusal terim baskin; karesel terim
    # h^2 ile, burada kucuk). Fiziksel viskozitede oran 1 olurdu.
    assert 1.6 < oranlar[0] < 2.6, guc
