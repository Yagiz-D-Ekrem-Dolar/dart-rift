"""A101 — geç evrede düzeltilmiş süreklilik `dρ/dt = −ρ tr(L)`.

Düzeltilmemiş SPH diverjansı serbest yüzeyde hacim değişiminin yalnız
`~%50`'sini görüyor (rapor A101, `docs/COZUNURLUK-DENETIMI.md` §3). Bu
sınavlar (1) anahtar verilmezse yolun bit-aynı kaldığını, (2) verilince
yoğunluk hızının `−ρ tr(L)` olduğunu, (3) düzgün genleşmede serbest yüzeydeki
parçacığın da **tam** hacim değişimini gördüğünü sınar.
"""
from __future__ import annotations

import dataclasses

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


def _mat(yontem: str = "continuity"):
    return MaterialParams(
        eos="tillotson", density_method=yontem,
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


def _cozucu(x, v, s, *, yontem="continuity", komsu="bvh"):
    from dartrift.warp_core.solver_solid import WarpSolid3D

    n = len(x)
    m = np.full(n, RHO0 / ALFA0 * s ** 3)
    sol = WarpSolid3D(x, v, m, np.zeros(n), 2.0 * s, _mat(yontem),
                      R.RefParams(), alpha0=np.full(n, ALFA0),
                      device="cpu", komsu_arama=komsu)
    sol.hazirla()
    return sol


def _yuzey_uzakligi(x, s):
    """Küp kafeste parçacığın en yakın yüze uzaklığı (s biriminde)."""
    yari = np.max(np.abs(x), axis=0) + 0.5 * s
    return np.min(yari[None, :] - np.abs(x), axis=1) / s


def test_ANAHTAR_VERILMEZSE_sph_diverjansi_bit_ayni():
    rng = np.random.default_rng(11)
    s = 0.5
    x = _kafes(6, s, rng, 0.1)
    v = 0.05 * x
    sol = _cozucu(x, v, s)
    b = sol.gec_evreye_gec(A_GEC)
    assert b["sureklilik"] == "sph"
    assert sol._sureklilik_L is False
    rho = sol.rho.numpy()
    assert np.array_equal(sol.drhodt.numpy(), -rho * sol.divv.numpy())


def test_ANAHTAR_VERILINCE_drhodt_eksi_rho_iz_L():
    rng = np.random.default_rng(12)
    s = 0.5
    x = _kafes(6, s, rng, 0.1)
    v = 0.05 * x + 0.01 * rng.standard_normal(x.shape)
    sol = _cozucu(x, v, s)
    b = sol.gec_evreye_gec(A_GEC, duzeltilmis_sureklilik=True)
    assert b["sureklilik"] == "trL"
    L = sol.L.numpy().reshape(-1, 3, 3)
    iz = L[:, 0, 0] + L[:, 1, 1] + L[:, 2, 2]
    assert np.allclose(sol.drhodt.numpy(), -sol.rho.numpy() * iz,
                       rtol=1e-12, atol=0.0)


@pytest.mark.parametrize("komsu", ["bvh", "hash"])
def test_DUZGUN_GENLESMEDE_yuzey_parcacigi_TAM_hacim_degisimi_goruyor(komsu):
    """`v = ε x`: gerçek `∇·v = 3ε` her yerde, serbest yüzey dahil."""
    s = 0.5
    eps = 0.05
    x = _kafes(8, s)
    v = eps * x
    eski = _cozucu(x, v, s, komsu=komsu)
    eski.gec_evreye_gec(A_GEC)
    yeni = _cozucu(x, v, s, komsu=komsu)
    yeni.gec_evreye_gec(A_GEC, duzeltilmis_sureklilik=True)
    d = _yuzey_uzakligi(x, s)
    yuzey = d < 0.75            # en dis katman
    ic = d > 2.5                # cekirdek tam
    oran_eski = -eski.drhodt.numpy() / eski.rho.numpy() / (3.0 * eps)
    oran_yeni = -yeni.drhodt.numpy() / yeni.rho.numpy() / (3.0 * eps)
    # eski yol: icte ~dogru, YUZEYDE yarim (A101'in olcumu). 8^3 kupte en ic
    # katman bile yuzeye 3,5 s uzakta (destek 4 s) -> icte 0,9994.
    assert np.allclose(oran_eski[ic], 1.0, atol=1e-3)
    assert float(np.mean(oran_eski[yuzey])) == pytest.approx(0.50, abs=0.02)
    # yeni yol: HER YERDE tam (dogrusal alani duzeltilmis gradyan tam verir)
    assert np.allclose(oran_yeni, 1.0, rtol=0.0, atol=1e-9)


def test_SUREKLILIK_DISI_YOGUNLUKTA_reddedilir():
    s = 0.5
    x = _kafes(4, s)
    sol = _cozucu(x, np.zeros_like(x), s, yontem="summation")
    with pytest.raises(ValueError, match="continuity"):
        sol.gec_evreye_gec(A_GEC, duzeltilmis_sureklilik=True)


def test_GECIS_SONRASI_ADIM_yeni_yolu_kullaniyor():
    """Adım atıldıktan sonra da (yeniden değerlendirmede) tr(L) kullanılır."""
    rng = np.random.default_rng(13)
    s = 0.5
    x = _kafes(6, s, rng, 0.05)
    v = 0.05 * x
    sol = _cozucu(x, v, s)
    sol.gec_evreye_gec(A_GEC, duzeltilmis_sureklilik=True)
    for _ in range(3):
        sol.step(sol.compute_dt())
    sol.hazirla()
    L = sol.L.numpy().reshape(-1, 3, 3)
    iz = L[:, 0, 0] + L[:, 1, 1] + L[:, 2, 2]
    assert np.allclose(sol.drhodt.numpy(), -sol.rho.numpy() * iz,
                       rtol=1e-12, atol=0.0)
    assert np.all(np.isfinite(sol.rho.numpy()))


def test_ILERI_KOSU_gec_evre_anahtari_taniniyor():
    """`gec_evre["duzeltilmis_sureklilik"]` bilinmeyen anahtar sayılmaz."""
    import inspect

    from dartrift.inference import forward

    kaynak = inspect.getsource(forward.ileri_kosu_merdiven)
    assert '"duzeltilmis_sureklilik"' in kaynak
    # dataclass alanlari degismedi (RefParams'a yeni alan eklenmedi)
    assert "sureklilik" not in {f.name for f in dataclasses.fields(R.RefParams)}
