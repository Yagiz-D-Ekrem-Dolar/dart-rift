"""`dt` **en küçük** `h` ile belirlenir — A′'nın kararlılık değişmezi.

## Neden ayrı bir test

A′'da ince bölgenin `h`'si kaba bölgenin yarısı. `dt` **en büyük** `h`
ile hesaplanırsa ince parçacıklar CFL'yi **ihlal eder** ve koşu sessizce
kararsızlaşır — çünkü patlama hemen olmaz, birikir.

Kod okundu ve doğru: `solver_solid.py:79` `_h_np = _h` (dizi),
`compute_dt` global `min` alıyor. Ama bu **sınanmıyordu**. Biri
`_h_np`'yi `self.h`'ye (skaler `max`) çevirse test kırılmadan geçerdi.

CPU referansı aynı formülü kullanıyor (`per_particle_h`), dolayısıyla
değişmez **GPU'suz** sınanabilir.

## Ayrıca: ensemble maliyet modelinin dayanağı

[`ensemble_cost`](../src/dartrift/validation/ensemble_cost.py) A′'nın
`dt`'sini `dt_kaba/λ` alıyor. O varsayım **bu** değişmezden geliyor;
değişmez düşerse maliyet tablosu da yanlış olur.
"""
from __future__ import annotations

import numpy as np
import pytest

from dartrift.cpu_reference.materials import (
    DamageParams,
    GravityParams,
    MaterialParams,
    PorosityParams,
    StrengthParams,
)
from dartrift.cpu_reference.solid_ref import SolidState, compute_timestep_solid, evaluate_solid
from dartrift.cpu_reference.sph_ref import RefParams

MAT = MaterialParams(
    eos="tillotson",
    strength=StrengthParams(enabled=True, Y0=1.0e5, mu_f=0.8, YM=1.5e9,
                            shear_G=2.27e10, jaumann=True),
    porosity=PorosityParams(enabled=False),
    gravity=GravityParams(enabled=False),
    damage=DamageParams(enabled=False),
    density_method="continuity")
NUM = RefParams(cfl=0.2)


def _durum(h, yan=6, seed=17):
    g = np.random.default_rng(seed)
    s = 1.0
    e = (np.arange(yan) - yan / 2.0) * s
    xx, yy, zz = np.meshgrid(e, e, e, indexing="ij")
    x = np.column_stack([xx.ravel(), yy.ravel(), zz.ravel()])
    x = x + g.normal(0.0, 0.03 * s, x.shape)
    n = len(x)
    st = SolidState(x=x, v=g.normal(0.0, 3.0, x.shape),
                    m=np.full(n, 2700.0 * s ** 3), u=np.full(n, 1.0e4),
                    h=h, active=np.ones(n, bool), alpha=np.ones(n),
                    # `continuity` modunda baslangic rho'su ZORUNLU.
                    # Ayni deger her kolda -> `dt` farki YALNIZCA h'den.
                    rho=np.full(n, 2700.0))
    evaluate_solid(st, MAT, NUM)
    return st


def test_dt_EN_KUCUK_h_ile_belirleniyor() -> None:
    """Karışık `h`'de `dt`, **en küçük** `h`'nin skaler koşusuyla aynı olmalı.

    Eğer `dt` en büyük `h` ile hesaplanıyor olsaydı, karışık koşu
    `h_büyük` koşusuyla eşleşirdi — bu test onu ayırt ediyor.
    """
    n = 6 ** 3
    h_kucuk, h_buyuk = 1.3, 2.6
    karisik = np.full(n, h_buyuk)
    karisik[: n // 2] = h_kucuk           # yarisi INCE

    dt_kucuk = compute_timestep_solid(_durum(h_kucuk), MAT, NUM)
    dt_buyuk = compute_timestep_solid(_durum(h_buyuk), MAT, NUM)
    dt_karisik = compute_timestep_solid(_durum(karisik), MAT, NUM)

    # Bosluk kontrolu: iki skaler kosu AYIRT EDILEBILIR olmali.
    assert dt_kucuk < 0.9 * dt_buyuk, (dt_kucuk, dt_buyuk)
    # Karisik kosu KUCUK olana yakin olmali, BUYUK olana degil.
    assert abs(dt_karisik - dt_kucuk) < abs(dt_karisik - dt_buyuk), (
        dt_kucuk, dt_karisik, dt_buyuk)
    assert dt_karisik < dt_buyuk


def test_dt_h_ile_yaklasik_DOGRUSAL() -> None:
    """`dt_cfl ~ h/(c+...)` — `h` yarıya inince `dt` de kabaca yarıya.

    `ensemble_cost`'un `dt_kaba/λ` varsayımı **bu** ölçümden geliyor.
    Tam doğrusal değil (ivme ve gerinim kriterleri de var), o yüzden
    tolerans geniş ama yön kesin.
    """
    dt1 = compute_timestep_solid(_durum(2.6), MAT, NUM)
    dt2 = compute_timestep_solid(_durum(1.3), MAT, NUM)
    oran = dt1 / dt2
    assert 1.3 < oran < 2.6, f"dt orani {oran} -- h ile olcekleme kirilmis"


def test_TEK_ince_parcacik_dt_yi_DUSURUYOR() -> None:
    """`min` gerçekten global mi? Bir tek parçacık yetmeli.

    Ortalama alınıyor olsaydı tek parçacık `dt`'yi kayda değer
    düşürmezdi — bu test o ayrımı yapıyor.
    """
    n = 6 ** 3
    tek = np.full(n, 2.6)
    tek[0] = 0.65                          # TEK parcacik, dortte bir h
    dt_tekduze = compute_timestep_solid(_durum(2.6), MAT, NUM)
    dt_tek = compute_timestep_solid(_durum(tek), MAT, NUM)
    assert dt_tek < 0.6 * dt_tekduze, (dt_tek, dt_tekduze)


def test_ensemble_cost_dt_VARSAYIMI_bu_teste_dayaniyor() -> None:
    """Belge bağı: maliyet modeli `dt_kaba/λ` diyor ve nedeni burada."""
    from dartrift.validation.ensemble_cost import OLCULEN, _senaryolar

    s = {x.ad: x for x in _senaryolar()}
    assert s["A-prime"].dt_s == pytest.approx(
        OLCULEN["dt_kaba_s"] / OLCULEN["lam"])
    assert s["tekduze-kaba"].dt_s == pytest.approx(OLCULEN["dt_kaba_s"])
