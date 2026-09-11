"""A75 — merminin kendi Tillotson EOS'u (uzman Soru 5).

Uzman: *"Bu kampanyanın çözücüsü tek Tillotson parametre setini bütün
parçacıklara uyguluyor. Çarpana ayrı yoğunluk/alpha ve Y0 verilmesi,
ayrı alüminyum EOS uygulanması demek değil."*

Kilitlenen:

1. Yönlendirme yokken ya da maske boşken hedef **bit-aynı**.
2. Mermi parçacıkları alüminyum Tillotson basıncını alıyor.
3. CPU referansı = Warp çekirdeği.
4. Farklı `ρ₀` REDDEDİLİYOR (ADR-0032 eşlemesi).
"""
from __future__ import annotations

import dataclasses

import numpy as np
import pytest

from dartrift.cpu_reference import sph_ref as R
from dartrift.cpu_reference.materials import (
    ALUMINYUM_TILLOTSON,
    GravityParams,
    MaterialParams,
    PorosityParams,
    StrengthParams,
    tillotson_pressure,
)
from dartrift.cpu_reference.solid_ref import SolidState, evaluate_solid, step_kdk_solid
from dartrift.particles import warp_available
from dartrift.validation.gravity import _uniform_sphere

needs_warp = pytest.mark.skipif(not warp_available(), reason="warp yok")


def test_aluminyum_parametreleri_TABLO_degerleri():
    t = ALUMINYUM_TILLOTSON
    assert (t.rho0, t.A, t.B, t.a, t.b) == (2700.0, 7.52e10, 6.5e10, 0.5, 1.63)
    assert (t.u0, t.u_iv, t.u_cv) == (5.0e6, 3.0e6, 1.39e7)
    assert (t.alpha_t, t.beta_t) == (5.0, 5.0)


def test_aluminyum_bazalttan_SERT():
    """Aynı sıkışmada alüminyum basıncı bazalttan büyük olmalı."""
    rho = np.array([3000.0])
    u = np.array([1.0e5])
    p_al = tillotson_pressure(rho, u, ALUMINYUM_TILLOTSON)[0]
    p_ba = tillotson_pressure(rho, u, MaterialParams().tillotson)[0]
    assert p_al > 2.0 * p_ba


def _kurulum(n=150):
    x = _uniform_sphere(n, 1.0, seed=616161)
    v = -30.0 * x
    h = 1.3 * (4.0 * np.pi / 3.0 / n) ** (1.0 / 3.0)
    pp = PorosityParams(enabled=True, alpha0=1.3, Pe=1e6, Ps=1e9, n_exp=2.0)
    m = np.full(n, (2700.0 / pp.alpha0) * (4.0 / 3.0) * np.pi / n)
    mat = MaterialParams(
        eos="tillotson", density_method="continuity",
        strength=StrengthParams(enabled=True, Y0=1e6, mu_f=0.8, YM=1.5e9,
                                shear_G=2.27e10),
        porosity=pp, gravity=GravityParams(enabled=False))
    a0 = np.full(n, pp.alpha0)
    maske = np.zeros(n, bool)
    maske[:25] = True
    a0[maske] = 1.0                       # mermi gozeneksiz
    m[maske] = 2700.0 * (4.0 / 3.0) * np.pi / n
    return x, v, m, h, mat, a0, maske


def _cpu(maske_ver: bool, n_adim=3):
    x, v, m, h, mat, a0, maske = _kurulum()
    st = SolidState(x=x.copy(), v=v.copy(), m=m, u=np.zeros(len(m)), h=h,
                    active=np.ones(len(m), bool), alpha=a0.copy(),
                    rho=2700.0 / a0,
                    mermi_maske=maske if maske_ver else None,
                    mermi_tillotson=ALUMINYUM_TILLOTSON if maske_ver else None)
    num = R.RefParams(cfl=0.2)
    evaluate_solid(st, mat, num)
    for _ in range(n_adim):
        step_kdk_solid(st, mat, num, 5.0e-7)
    return st, maske


def _warp(maske_ver: bool, *, bos_maske=False, n_adim=3):
    from dartrift.warp_core.solver_solid import WarpSolid3D

    x, v, m, h, mat, a0, maske = _kurulum()
    kw = {}
    if maske_ver:
        kw = {"mermi_tillotson": ALUMINYUM_TILLOTSON,
              "mermi_maske": np.zeros_like(maske) if bos_maske else maske}
    sol = WarpSolid3D(x.copy(), v.copy(), m, np.zeros(len(m)), h, mat,
                      R.RefParams(cfl=0.2), alpha0=a0, device="cpu", **kw)
    for _ in range(n_adim):
        sol.step(5.0e-7)
    return sol.state_numpy()


@needs_warp
def test_bos_maskeyle_hedef_BIT_AYNI():
    a = _warp(False)
    b = _warp(True, bos_maske=True)
    for k in ("x", "v", "u", "P", "rho", "S", "cs"):
        assert np.array_equal(a[k], b[k]), k


@needs_warp
def test_mermi_EOS_sonucu_DEGISTIRIYOR():
    a = _warp(False)
    b = _warp(True)
    assert not np.array_equal(a["P"], b["P"])


@needs_warp
def test_cpu_referansi_warp_ile_AYNI():
    st, _ = _cpu(True)
    s = _warp(True)
    for ad, ref, got in (("x", st.x, s["x"]), ("v", st.v, s["v"]),
                         ("u", st.u, s["u"]), ("P", st.P, s["P"]),
                         ("S", st.S, s["S"])):
        olcek = np.max(np.abs(ref)) + 1e-300
        assert np.max(np.abs(ref - got)) / olcek < 1e-8, ad


def test_cpu_mermi_basinci_ALUMINYUM():
    st, maske = _cpu(True, n_adim=0)
    rho_s = st.rho * st.alpha
    beklenen = tillotson_pressure(rho_s[maske], st.u[maske],
                                  ALUMINYUM_TILLOTSON) / st.alpha[maske]
    np.testing.assert_array_equal(st.P[maske], beklenen)


@needs_warp
def test_farkli_rho0_REDDEDILIYOR():
    from dartrift.warp_core.solver_solid import WarpSolid3D

    x, v, m, h, mat, a0, maske = _kurulum()
    kotu = dataclasses.replace(ALUMINYUM_TILLOTSON, rho0=2800.0)
    with pytest.raises(ValueError, match="ADR-0032"):
        WarpSolid3D(x, v, m, np.zeros(len(m)), h, mat, R.RefParams(),
                    alpha0=a0, device="cpu", mermi_tillotson=kotu,
                    mermi_maske=maske)


@needs_warp
def test_maskesiz_mermi_EOS_REDDEDILIYOR():
    from dartrift.warp_core.solver_solid import WarpSolid3D

    x, v, m, h, mat, a0, _ = _kurulum()
    with pytest.raises(ValueError, match="mermi_maske"):
        WarpSolid3D(x, v, m, np.zeros(len(m)), h, mat, R.RefParams(),
                    alpha0=a0, device="cpu", mermi_tillotson=ALUMINYUM_TILLOTSON)


def test_ileri_model_varsayilani_HEDEF_ve_ozet_ayri():
    import inspect

    from dartrift.inference.forward import _fizik_ozeti, ileri_kosu_merdiven

    assert inspect.signature(ileri_kosu_merdiven).parameters[
        "mermi_eos"].default == "hedef"
    taban = {"radius": 82.0}
    a = _fizik_ozeti(taban, "mat", ("48:5.6",), 7.0, 0.024)
    b = _fizik_ozeti(taban, "mat", ("48:5.6",), 7.0, 0.024, mermi_eos="hedef")
    c = _fizik_ozeti(taban, "mat", ("48:5.6",), 7.0, 0.024, mermi_eos="aluminyum")
    assert a == b and a != c
