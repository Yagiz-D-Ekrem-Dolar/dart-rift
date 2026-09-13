"""A80 — buharlaşmış ya da dağılmış maddede dayanım kesmesi."""
from __future__ import annotations

import inspect
from pathlib import Path

import numpy as np
import pytest

from dartrift.cpu_reference import sph_ref as R
from dartrift.cpu_reference.materials import (
    ALUMINYUM_TILLOTSON,
    GravityParams,
    MaterialParams,
    PorosityParams,
    StrengthParams,
    TillotsonParams,
)
from dartrift.particles import warp_available

pytestmark = pytest.mark.skipif(not warp_available(), reason="warp yok")

ALFA0 = 1.3
RHO0 = 2700.0
U_IV = TillotsonParams().u_iv


def _mat():
    return MaterialParams(
        eos="tillotson", density_method="continuity",
        strength=StrengthParams(enabled=True, Y0=1e4, mu_f=0.6, YM=1.5e9,
                                shear_G=2.27e10),
        porosity=PorosityParams(enabled=True, alpha0=ALFA0, Pe=1e6, Ps=1e8,
                                n_exp=2.0),
        gravity=GravityParams(enabled=False))


def _kafes():
    g = np.arange(-2, 3) * 0.5
    return np.stack(np.meshgrid(g, g, g, indexing="ij"), -1).reshape(-1, 3)


def _cozucu(*, u=None, rho=None, S0=None, **kw):
    from dartrift.warp_core.solver_solid import WarpSolid3D

    x = _kafes()
    n = len(x)
    rho_d = np.full(n, RHO0 / ALFA0) if rho is None else rho
    if S0 is None:
        S0 = np.zeros((n, 3, 3))
        S0[:, 0, 1] = S0[:, 1, 0] = 2.0e3     # akma sinirinin (1e4) altinda
    s = WarpSolid3D(x, np.zeros_like(x), np.full(n, RHO0 / ALFA0 * 0.125),
                    np.zeros(n) if u is None else u, 0.65, _mat(), R.RefParams(),
                    S0=S0, alpha0=np.full(n, ALFA0), rho_durum=rho_d,
                    device="cpu", **kw)
    s.hazirla()
    return s


def test_varsayilan_None_BIT_AYNI_ve_cekirdek_yok():
    a = _cozucu()
    b = _cozucu(dayanim_kesme=None)
    assert a.S.numpy().tobytes() == b.S.numpy().tobytes()
    assert a.compute_dt() == b.compute_dt()
    assert a.kesme_tanisi() == {}


def test_SICAK_parcacikta_S_sifir_soguklar_DOKUNULMUYOR():
    n = len(_kafes())
    u = np.zeros(n)
    u[12] = 1.3 * U_IV
    s = _cozucu(u=u, dayanim_kesme={"eta_kes": 0.5})
    S = s.S.numpy()
    ref = _cozucu(u=u).S.numpy()
    assert np.all(S[12] == 0.0) and s.kesik.numpy()[12] == 1
    diger = np.arange(n) != 12
    np.testing.assert_array_equal(S[diger], ref[diger])
    t = s.kesme_tanisi()
    assert t["n_kesik"] == 1 and t["kesik_kutle_kesri"] == pytest.approx(1 / n)


def test_GENLESMIS_parcacikta_S_sifir():
    n = len(_kafes())
    rho = np.full(n, RHO0 / ALFA0)
    rho[7] = 0.4 * RHO0 / ALFA0           # rho*alpha/rho0 = 0,4 < 0,5
    rho[8] = 0.6 * RHO0 / ALFA0           # 0,6 >= 0,5: kesilmez
    s = _cozucu(rho=rho, dayanim_kesme={"eta_kes": 0.5})
    k = s.kesik.numpy()
    assert k[7] == 1 and k[8] == 0
    assert np.all(s.S.numpy()[7] == 0.0) and np.any(s.S.numpy()[8] != 0.0)


def test_dt_COKUSU_kesmeyle_kalkiyor():
    """Ölçülen mekanizma: ρ → 0 iken √(4G/3ρ) ve S/ρ ivmesi dt'yi sıfıra
    indiriyor. Üretimdeki gibi matris basıncı çekmede kırpılı (P = 0).

    Ölçüldü (bu kafes): kesmesiz `dt = 1,6e-8 s`, ivme `3,8e12 m/s²`;
    kesmeyle `dt = 1,8e-5 s`, ivme `0,89 m/s²`. Kırpma olmadan (P < 0)
    basınç terimi ayrıca tekil kalıyor — kesme onu çözmüyor, çözmemeli.
    """
    n = len(_kafes())
    rho = np.full(n, RHO0 / ALFA0)
    rho[12] = 1e-3                          # M kaba t5'teki parcacik
    kirp = np.ones(n, bool)
    eski = _cozucu(rho=rho, cekme_kirp_maske=kirp).compute_dt()
    yeni = _cozucu(rho=rho, cekme_kirp_maske=kirp,
                   dayanim_kesme={"eta_kes": 0.5}).compute_dt()
    assert yeni > 100.0 * eski


def test_MERMI_kendi_u_iv_esigini_kullaniyor():
    n = len(_kafes())
    maske = np.zeros(n, bool)
    maske[:5] = True
    u = np.full(n, 0.5 * (ALUMINYUM_TILLOTSON.u_iv + U_IV))   # ikisinin arasi
    assert ALUMINYUM_TILLOTSON.u_iv < u[0] < U_IV
    s = _cozucu(u=u, dayanim_kesme={"eta_kes": 0.5},
                mermi_tillotson=ALUMINYUM_TILLOTSON, mermi_maske=maske)
    k = s.kesik.numpy().astype(bool)
    assert np.all(k[maske]) and not np.any(k[~maske])


def test_adim_sonunda_SAKLANAN_S_de_sifir():
    n = len(_kafes())
    u = np.zeros(n)
    u[12] = 2.0 * U_IV
    s = _cozucu(u=u, dayanim_kesme={"eta_kes": 0.5})
    for _ in range(3):
        s.step(s.compute_dt())
    assert np.all(s.S.numpy()[12] == 0.0)
    assert np.all(np.isfinite(s.state_numpy()["v"]))


def test_gecersiz_esikler_ADIYLA_duser():
    with pytest.raises(ValueError, match="eta_kes"):
        _cozucu(dayanim_kesme={"eta_kes": 1.2})
    with pytest.raises(ValueError, match="u_kes"):
        _cozucu(dayanim_kesme={"eta_kes": 0.5, "u_kes": -1.0})


def test_fizik_ozeti_yalniz_ACIKKEN_degisiyor_ve_surucu_bayragi_geciriyor():
    from dartrift.inference import forward

    arg = ({}, _mat(), ("3:0.35",), 7.0, 0.024)
    assert forward._fizik_ozeti(*arg) == forward._fizik_ozeti(*arg, dayanim_kesme=False)
    assert forward._fizik_ozeti(*arg) != forward._fizik_ozeti(*arg, dayanim_kesme=True)
    kaynak = inspect.getsource(forward.ileri_kosu_merdiven)
    assert "dayanim_kesme=({\"eta_kes\": DAYANIM_KESME_ETA} if dayanim_kesme" in kaynak
    assert forward.DAYANIM_KESME_ETA == 0.5
    surucu = (Path(__file__).resolve().parents[1] / "scripts"
              / "faz5_ensemble_merdiven.py").read_text(encoding="utf-8")
    assert "dayanim_kesme=a.dayanim_kesme" in surucu
