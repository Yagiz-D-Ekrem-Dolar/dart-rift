"""İç enerji tabanı çekirdeği — kırpıyor mu, **sayıyor** mu.

A21: `tillotson_p` negatif `u`'yu sıfır sayıyordu ama durum değişkeni
kırpılmıyordu; hedef parçacıklarının `%44,5`'i negatife düşmüştü.

Taban eklemek tek başına yetmez: **sessizce kırpmak** bir kaçak
kaynağını başkasıyla değiştirmek olurdu. Bu yüzden kırpılan enerji
parçacık başına biriktiriliyor ve buradaki testler ikisini birden
sınıyor.
"""
from __future__ import annotations

import numpy as np
import pytest

wp = pytest.importorskip("warp")

pytestmark = pytest.mark.warp


def _kos(u0, dudt, half_dt, tabanli: bool):
    from dartrift.warp_core import integrator as I
    from dartrift.warp_core.solver_solid import F
    wp.init()
    n = len(u0)
    u = wp.array(np.asarray(u0, np.float64), dtype=F, device="cpu")
    d = wp.array(np.asarray(dudt, np.float64), dtype=F, device="cpu")
    act = wp.array(np.ones(n, np.uint8), dtype=wp.uint8, device="cpu")
    kir = wp.zeros(n, dtype=F, device="cpu")
    if tabanli:
        wp.launch(I.kick_u_3d_tabanli, dim=n,
                  inputs=[u, d, act, kir, F(half_dt)], device="cpu")
    else:
        wp.launch(I.kick_u_3d, dim=n, inputs=[u, d, act, F(half_dt)],
                  device="cpu")
    return u.numpy().copy(), kir.numpy().copy()


def test_TABANSIZ_cekirdek_negatife_iniyor() -> None:
    """Bugünkü davranış — A21'in kaynağı."""
    u, _ = _kos([10.0, 10.0], [-100.0, +100.0], 1.0, tabanli=False)
    assert u[0] == pytest.approx(-90.0)
    assert u[1] == pytest.approx(110.0)


def test_TABANLI_cekirdek_sifirin_ALTINA_inmiyor() -> None:
    u, _ = _kos([10.0, 10.0], [-100.0, +100.0], 1.0, tabanli=True)
    assert u[0] == 0.0
    assert u[1] == pytest.approx(110.0)


def test_KIRPILAN_enerji_sayiliyor() -> None:
    """Kırpılan miktar defterde olmalı; sessizce yok olmamalı."""
    u, kir = _kos([10.0, 10.0], [-100.0, +100.0], 1.0, tabanli=True)
    # 10 + (-100) = -90 -> 0 ; kirpilan 90
    assert kir[0] == pytest.approx(90.0)
    assert kir[1] == 0.0


def test_KIRPILAN_birikiyor() -> None:
    """Arka arkaya iki adımda kırpılan toplanmalı."""
    from dartrift.warp_core import integrator as I
    from dartrift.warp_core.solver_solid import F
    wp.init()
    u = wp.array(np.array([0.0]), dtype=F, device="cpu")
    d = wp.array(np.array([-5.0]), dtype=F, device="cpu")
    act = wp.array(np.ones(1, np.uint8), dtype=wp.uint8, device="cpu")
    kir = wp.zeros(1, dtype=F, device="cpu")
    for _ in range(3):
        wp.launch(I.kick_u_3d_tabanli, dim=1,
                  inputs=[u, d, act, kir, F(1.0)], device="cpu")
    assert u.numpy()[0] == 0.0
    assert kir.numpy()[0] == pytest.approx(15.0)


def test_POZITIF_kolda_iki_cekirdek_BIREBIR_ayni() -> None:
    """Taban yalnızca negatife dokunmalı; aksi halde sessiz sapma olur."""
    rng = np.random.default_rng(3)
    u0 = rng.uniform(10.0, 100.0, 64)
    dudt = rng.uniform(0.0, 50.0, 64)          # hepsi pozitif
    a, _ = _kos(u0, dudt, 0.5, tabanli=False)
    b, kir = _kos(u0, dudt, 0.5, tabanli=True)
    assert np.array_equal(a, b)
    assert np.all(kir == 0.0)


def test_PASIF_parcacik_dokunulmuyor() -> None:
    from dartrift.warp_core import integrator as I
    from dartrift.warp_core.solver_solid import F
    wp.init()
    u = wp.array(np.array([5.0, 5.0]), dtype=F, device="cpu")
    d = wp.array(np.array([-100.0, -100.0]), dtype=F, device="cpu")
    act = wp.array(np.array([0, 1], np.uint8), dtype=wp.uint8, device="cpu")
    kir = wp.zeros(2, dtype=F, device="cpu")
    wp.launch(I.kick_u_3d_tabanli, dim=2,
              inputs=[u, d, act, kir, F(1.0)], device="cpu")
    assert u.numpy()[0] == pytest.approx(5.0)   # pasif: degismedi
    assert u.numpy()[1] == 0.0                  # aktif: tabana carpti
    assert kir.numpy()[0] == 0.0
