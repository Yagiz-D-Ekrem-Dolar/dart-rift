"""`_eval()` DURUMU DEGISTIRMEZ — yapisal degismez (invariant).

NEDEN AYRI BIR DOSYA: bu, tek bir modulun testi degil, cozucunun tamamini
baglayan bir sozlesme. Ihlali sessizdir ve modul testleriyle yakalanmaz.

Bulunan kusur (bkz. ADR-0027 eki, is 1446269): `apply_damage_k` gerilmeyi
YERINDE carpiyordu (`S[i] = f*S[i]`). `S` bir DURUM degiskenidir ve `_eval()`
KDK adimi basina IKI kez cagrilir; sonuc her adimda S <- (1-D)^2 S oldu.
Olcum: D=0.5 sabit, hicbir fiziksel evrim yokken S 1.0e7 -> 4.88e3 (5 adim).
Hasar testlerinin hepsi "hasar sonucu degistiriyor mu" diye soruyordu;
degistiriyordu — ama yanlis nedenle. Bu yuzden hicbiri kusuru gormedi.

Dogru soru sudur: **alan degerlendirmesi bir SAF FONKSIYONDUR.** Durumdan
turetilmis nicelikleri (rho_toplam, P, cs, L, hizlar, kuvvetler) hesaplar;
durumun kendisini (x, v, rho_sureklilik, u, S, alpha, D) ASLA yazmaz. Durumu
yalnizca `step()` icindeki tekmeler/surukleme ve guncelleyiciler degistirir.

Bu test o sozlesmeyi dogrudan olcer: `_eval()` iki kez cagrilir ve tum durum
dizilerinin BIT DUZEYINDE ayni kalmasi beklenir. Turetilmis dizilerin de ayni
kalmasi gerekir — degisiyorlarsa girdileri degismis demektir, yani bir yerde
durum sizmasi vardir.
"""

from __future__ import annotations

import numpy as np
import pytest

# durum: `step()` disinda DEGISMEMELI. turetilmis: iki eval arasi ayni kalmali
# (girdileri degismediginden). Ikisini de kontrol ediyoruz ki sizinti nerede
# olursa olsun gorunsun.
DURUM = ("x", "v", "rho", "u", "S", "alpha", "D", "D_cbrt")
TURETILMIS = ("P", "cs", "L", "divv", "a", "dudt", "dSdt", "drhodt",
              "g", "phi", "strain", "dDdt_cbrt", "P_eff", "S_eff")


def _needs_cuda():
    from dartrift.particles import warp_available, warp_devices

    if not warp_available() or not any(
            d.startswith("cuda") for d in warp_devices()):
        pytest.skip("CUDA yok")


def _oku(s, adlar):
    out = {}
    for a in adlar:
        arr = getattr(s, a, None)
        if arr is None:
            continue
        out[a] = np.array(arr.numpy(), copy=True)
    return out


def _kur(damage: bool, gravity: bool, porosity: bool):
    from dartrift.cpu_reference.materials import (
        DamageParams,
        GravityParams,
        MaterialParams,
        PorosityParams,
        StrengthParams,
    )
    from dartrift.cpu_reference.sph_ref import RefParams
    from dartrift.warp_core.solver_solid import WarpSolid3D

    nside, L = 6, 4.0
    g = (np.arange(nside) + 0.5) / nside - 0.5
    x = np.stack(np.meshgrid(g, g, g, indexing="ij"), -1).reshape(-1, 3) * L
    dx = L / nside
    m = np.full(len(x), 2700.0 * dx**3)
    h = 2.0 * dx
    # sifir olmayan hiz alani: L, divv, dSdt, dudt gercekten dolsun. Sifir
    # baslangicta her sey sifir kalir ve test hicbir sey olcmez.
    v = np.stack([x[:, 1], -x[:, 0], 0.3 * x[:, 2]], -1) * 5.0
    mat = MaterialParams(
        eos="tillotson",
        strength=StrengthParams(enabled=True, Y0=1.0e5, mu_f=0.8, YM=1.5e9,
                                shear_G=2.27e10, jaumann=True),
        porosity=PorosityParams(enabled=porosity),
        gravity=GravityParams(enabled=gravity),
        damage=DamageParams(enabled=damage, k_weibull=1.0e29, m_weibull=9.0),
        density_method="continuity",
    )
    return WarpSolid3D(x, v, m, np.zeros(len(x)), h, mat, RefParams(cfl=0.25),
                       device="cuda:0", check_every=10**9, damage_seed=3)


@pytest.mark.parametrize(
    ("damage", "gravity", "porosity"),
    [
        (False, False, False),   # taban
        (True, False, False),    # kusurun bulundugu yol
        (True, True, True),      # hepsi acik
    ],
)
def test_eval_durumu_degistirmez(damage, gravity, porosity):
    """Iki ardisik `_eval()`: durum BIT DUZEYINDE ayni kalmali."""
    _needs_cuda()
    s = _kur(damage, gravity, porosity)
    s._eval()
    once = _oku(s, DURUM)
    s._eval()
    sonra = _oku(s, DURUM)
    for ad in once:
        assert np.array_equal(once[ad], sonra[ad]), (
            f"`_eval()` DURUMU degistirdi: {ad!r} "
            f"(ilk {np.ravel(once[ad])[:3]} -> ikinci {np.ravel(sonra[ad])[:3]}). "
            "Alan degerlendirmesi saf olmali; durumu yalnizca step() yazar.")


@pytest.mark.parametrize("damage", [False, True])
def test_eval_turetilmisleri_tekrarlanabilir(damage):
    """Girdiler ayniysa cikti da AYNI olmali — tekrar cagri fark uretmemeli.

    Turetilmis bir dizi ikinci evalde degisiyorsa, girdilerinden biri birinci
    evalde yazilmistir: durum sizmasinin dolayli izi. `S_eff` icin bu testin
    kirilmis hali kusurun tam olarak kendisiydi.
    """
    _needs_cuda()
    s = _kur(damage, False, False)
    s._eval()
    once = _oku(s, TURETILMIS)
    s._eval()
    sonra = _oku(s, TURETILMIS)
    for ad in once:
        assert np.array_equal(once[ad], sonra[ad]), (
            f"turetilmis {ad!r} ikinci evalde degisti — girdisi bozuluyor")
