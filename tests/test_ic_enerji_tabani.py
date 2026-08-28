"""İç enerji **tabanı yok**: durum negatife düşüyor, EOS onu görmüyor.

`2026-08-21`'de ölçüldü. `tillotson_p` basıncı hesaplarken

    u = wp.max(u_in, 0.0)

diyor — yani **negatif `u`'yu sıfır sayıyor**. Ama durum değişkeni
hiçbir yerde kırpılmıyor (`integrator.py`: `u[i] += half_dt*dudt[i]`).

Sonuç ölçüldü (`t = 0,2 s`, hedef parçacıkları):

| koşu | `u < 0` olan | en negatif | tutulan enerji |
|---|---|---|---|
| `λ₁ = 38` | `4 641 / 10 424` (`%44,5`) | `-12,06 J/kg` | `-7,0e6 J` (`%0,06`) |
| tek aşama | `4 942 / 11 183` (`%44,2`) | `-694 J/kg` | `-3,0e8 J` (**`%2,76`**) |

İki ayrı sorun:

1. **Defter ile fizik ayrışıyor.** `Σ m u` korunuyor ve
   `test_conservation` bunu doğruluyor — ama basınç `max(u, 0)`
   gördüğü için *dinamiğin gördüğü* enerji defterdekinden farklı.
2. **Negatif `u` bir borç.** O parçacık sonradan ısıtıldığında önce
   borcunu kapatıyor; EOS ısınmayı ancak `u > 0` olunca görüyor.
   Yani şok cephesinin arkasındaki madde **olması gerekenden uzun
   süre soğuk kalıyor**.

Bu, A17'nin *"enerji hedefe geçiyor ama akış olmuyor"* ölçümüyle ve
ADR-0028'in kaydettiği `%1,5`'lik enerji hatasıyla aynı mertebede.

Test `xfail(strict=True)`: taban eklendiği gün **düşer** ve rapor
güncellenmek zorunda kalır. Rapor: `A21`.
"""
from __future__ import annotations

import numpy as np
import pytest

from dartrift.cpu_reference.materials import TillotsonParams


def _tillotson_p_referans(rho: float, u: float, p: TillotsonParams) -> float:
    """CPU referansındaki ile aynı kırpma — `u = max(u, 0)`."""
    uu = max(u, 0.0)
    eta = rho / p.rho0
    mu = eta - 1.0
    return (p.a + p.b / (uu / (p.u0 * eta * eta) + 1.0)) * rho * uu + p.A * mu


def test_EOS_negatif_u_yu_SIFIR_sayiyor() -> None:
    """Kırpmanın kendisi: `u = -100` ile `u = 0` aynı basıncı verir."""
    p = TillotsonParams()
    rho = p.rho0
    assert _tillotson_p_referans(rho, -100.0, p) == pytest.approx(
        _tillotson_p_referans(rho, 0.0, p))
    assert _tillotson_p_referans(rho, -1.0e6, p) == pytest.approx(
        _tillotson_p_referans(rho, 0.0, p))


def test_kirpma_ENERJIYI_gorunmez_kiliyor() -> None:
    """Negatif `u` taşıyan bir parçacık, defterde var fizikte yok.

    `Σ m u` defteri `-1e8 J` derken basınç `0` görüyor: iki sayı
    arasındaki fark **kaybolan** enerjidir.
    """
    m = np.array([1.0e4, 1.0e4])
    u = np.array([-500.0, +500.0])
    defter = float(np.sum(m * u))                 # 0 J
    fizik = float(np.sum(m * np.maximum(u, 0.0)))  # 5e6 J
    assert defter == pytest.approx(0.0)
    assert fizik == pytest.approx(5.0e6)
    assert fizik - defter == pytest.approx(5.0e6), (
        "defter ile fizik arasindaki fark, kirpmanin yuttugu enerjidir")


@pytest.mark.xfail(strict=True, reason="A21: durum degiskeni u kirpilmiyor; "
                                       "hedefin %44,5'inde u < 0 olculdu")
def test_INTEGRATOR_ic_enerjiyi_TABANDA_tutmali() -> None:
    """İntegratör `u`'yu `0`'ın altına indirmemeli.

    Bugün indiriyor. Bu test, taban eklendiği gün geçmeye başlar.
    """
    from dartrift.warp_core import integrator
    kaynak = __import__("inspect").getsource(integrator)
    # Bir taban varsa `u` guncellemesinin yaninda bir max/clamp gorulmeli.
    satirlar = [s for s in kaynak.splitlines() if "u[i]" in s and "+" in s]
    assert satirlar, "u guncellemesi bulunamadi -- test bayatlamis"
    assert any("max" in s or "clamp" in s for s in satirlar), (
        f"u guncellemesinde taban yok: {satirlar}")
