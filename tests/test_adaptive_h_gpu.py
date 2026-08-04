"""A′ (parçacık başına `h`) — **GPU** doğrulaması (CUDA yoksa atlanır).

`c7eebea` GPU tarafını yazdı ama yerelde GPU olmadığı için **koşamadı**.
S9'un dersi gereği ("atlanan test geçti değildir") bu dosya, A′'nın
çekirdek iddialarını TRUBA'da **koşulabilir** hâle getiriyor — tek seferlik
bir betik olarak değil, her kapı koşusunda tekrarlanan bir test olarak.

## Üç sınav, üçü de **gerçek bir kusura** bağlı

| # | sınav | hangi kusuru yakalar | kaynağı |
|---|---|---|---|
| 1 | skaler `h` ≡ tekdüze dizi `h`, **bit düzeyinde** | `h_ij = ½(h+h)` yuvarlamayı değiştiriyorsa | ilk K21 düzeltmem `1e-14` fark üretmişti |
| 2 | değişken `h`'de `Σ mᵢaᵢ = 0` **tam** | bir çift büyüklüğü hâlâ **asimetrik** `h` kullanıyorsa | CPU referansında yakalandı: net/ölçek **4,0e5** |
| 3 | değişken `h`'de **CPU = GPU** | portun sessiz sapması | K1'in kök nedeni tam bu boşluğun **yokluğuydu** |

Ölçülen değerler KAYIT-034'te.
"""
from __future__ import annotations

import numpy as np
import pytest

from dartrift.cpu_reference.materials import (DamageParams, GravityParams,
                                              MaterialParams, PorosityParams,
                                              StrengthParams)
from dartrift.cpu_reference.solid_ref import SolidState, evaluate_solid
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
H0 = 1.3


def _cuda_ya_da_atla() -> str:
    from dartrift.particles import warp_available, warp_devices

    if not warp_available():
        pytest.skip("warp yok")
    dev = [d for d in warp_devices() if str(d).startswith("cuda")]
    if not dev:
        pytest.skip("CUDA yok")
    return str(dev[0])


def _kur(yan: int = 7, seed: int = 4043):
    """Hafifçe bozulmuş kübik kafes — düzgün kafesin simetrisi kusur saklar."""
    rng = np.random.default_rng(seed)
    s = 1.0
    e = (np.arange(yan) - yan / 2.0) * s
    xx, yy, zz = np.meshgrid(e, e, e, indexing="ij")
    x = np.column_stack([xx.ravel(), yy.ravel(), zz.ravel()])
    x = x + rng.normal(0.0, 0.05 * s, x.shape)
    m = np.full(len(x), 2700.0 * s ** 3)
    v = rng.normal(0.0, 5.0, x.shape)
    u = np.full(len(x), 1.0e4)
    return x, v, m, u


def _gpu(x, v, m, u, h, dev):
    from dartrift.warp_core.solver_solid import WarpSolid3D

    sol = WarpSolid3D(x, v, m, u, h, MAT, NUM, device=dev)
    sol._eval()
    return sol.state_numpy()


def test_skaler_ve_tekduze_dizi_BIT_AYNI() -> None:
    """ADR-0041 §5b madde 4: skaler yol **bit düzeyinde** korunur.

    `h_ij = ½(h_i + h_j)` tekdüze `h`'de cebirsel olarak `h`'dir; ama
    kayan noktada `0.5*(h+h)` yalnızca `h` **tam** çıkarsa bit aynıdır.
    İkinin kuvvetiyle çarpma tam olduğu için çıkar — bu test onu
    **varsaymak** yerine ölçüyor.
    """
    dev = _cuda_ya_da_atla()
    x, v, m, u = _kur()
    skaler = _gpu(x, v, m, u, H0, dev)
    dizi = _gpu(x, v, m, u, np.full(len(m), H0), dev)
    for ad in ("P", "cs", "a", "rho"):
        assert np.array_equal(skaler[ad], dizi[ad]), (
            f"{ad}: bit farkı {np.max(np.abs(skaler[ad] - dizi[ad])):.3e}")


def test_degisken_h_momentumu_TAM_koruyor() -> None:
    """Simetrik `h_ij` ⇒ `f_ij = −f_ji` ⇒ `Σ mᵢaᵢ = 0` yuvarlama tabanında.

    Tek bir çift büyüklüğü `h_j` yerine `h_i` kullansa kalıntı
    `1e5` mertebesine fırlar (CPU referansında tam bu oldu).
    """
    dev = _cuda_ya_da_atla()
    x, v, m, u = _kur()
    rng = np.random.default_rng(11)
    h_var = H0 * rng.uniform(0.6, 1.6, len(m))
    st = _gpu(x, v, m, u, h_var, dev)
    net = np.abs(np.sum(st["m"][:, None] * st["a"], axis=0))
    olcek = float(np.sum(st["m"] * np.linalg.norm(st["a"], axis=1)))
    assert olcek > 0.0, "ivme tümüyle sıfır — sınav anlamsız"
    assert float(np.max(net)) / olcek < 1e-12, (
        f"momentum kalıntısı {float(np.max(net)) / olcek:.3e}")


def test_degisken_h_CPU_GPU_ayni() -> None:
    """K1'in kök nedeni: değişken `h` yolunun çapraz kontrolü **yoktu**."""
    dev = _cuda_ya_da_atla()
    x, v, m, u = _kur()
    rng = np.random.default_rng(11)
    h_var = H0 * rng.uniform(0.6, 1.6, len(m))
    gpu = _gpu(x, v, m, u, h_var, dev)
    cpu = SolidState(x=x.copy(), v=v.copy(), m=m.copy(), u=u.copy(), h=h_var,
                     active=np.ones(len(m), bool), alpha=np.ones(len(m)),
                     rho=gpu["rho"].copy())
    evaluate_solid(cpu, MAT, NUM)
    for ad in ("P", "cs", "a"):
        ref = getattr(cpu, ad)
        olc = max(float(np.max(np.abs(ref))), 1e-300)
        assert float(np.max(np.abs(gpu[ad] - ref))) / olc < 1e-10, (
            f"{ad}: göreli fark {float(np.max(np.abs(gpu[ad] - ref))) / olc:.3e}")


def test_h_dizisi_hatali_sekilde_REDDEDILIYOR() -> None:
    """Yanlış şekilli `h` sessizce yayılmamalı — **patlamalı**."""
    dev = _cuda_ya_da_atla()
    x, v, m, u = _kur()
    from dartrift.warp_core.solver_solid import WarpSolid3D

    with pytest.raises((ValueError, AssertionError)):
        WarpSolid3D(x, v, m, u, np.full(len(m) + 3, H0), MAT, NUM, device=dev)
