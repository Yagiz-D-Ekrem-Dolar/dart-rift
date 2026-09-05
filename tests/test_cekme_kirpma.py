"""Çekme kırpma tanı kolu — CPU'da sınanır.

NEDEN VAR. Bu bir **tanı kolu**; üretim davranışını DEĞİŞTİRMEMELİ.
En tehlikeli kusur, maske verilmediğinde sessizce bir şeyin
değişmesidir. İlk sınav tam onu kilitler.
"""
from __future__ import annotations

import numpy as np
import pytest

wp = pytest.importorskip("warp")


def _kucuk_sahne(n=64):
    rng = np.random.default_rng(7)
    x = rng.normal(scale=1.0, size=(n, 3))
    v = np.zeros((n, 3))
    m = np.full(n, 10.0)
    u = np.zeros(n)
    return x, v, m, u


def _cozucu(cekme_kirp_maske=None, dev="cpu"):
    from dartrift.cpu_reference.materials import (
        DamageParams,
        GravityParams,
        MaterialParams,
        PorosityParams,
        StrengthParams,
    )
    from dartrift.cpu_reference.sph_ref import RefParams
    from dartrift.warp_core.solver_solid import WarpSolid3D

    x, v, m, u = _kucuk_sahne()
    mat = MaterialParams(
        eos="tillotson",
        strength=StrengthParams(enabled=True, Y0=1.0e4, mu_f=0.6, YM=1.5e9,
                                shear_G=1.0e10, jaumann=True),
        porosity=PorosityParams(enabled=False),
        gravity=GravityParams(enabled=False),
        damage=DamageParams(enabled=False),
        density_method="continuity",
    )
    return WarpSolid3D(x, v, m, u, 1.5, mat, RefParams(cfl=0.25),
                       device=dev, check_every=10**9,
                       cekme_kirp_maske=cekme_kirp_maske)


def test_maske_yoksa_davranis_BIT_AYNI():
    """`None` verilince çekirdek hiç başlatılmamalı."""
    a = _cozucu(None)
    b = _cozucu(None)
    for _ in range(5):
        a.step(a.compute_dt())
        b.step(b.compute_dt())
    sa, sb = a.state_numpy(), b.state_numpy()
    for k in ("x", "v", "P", "rho", "u"):
        assert np.array_equal(sa[k], sb[k]), f"{k} bit-ayni degil"
    assert a._cekme_kirp is None


def test_kirpma_negatif_basinci_siliyor():
    s = _cozucu(np.ones(64, dtype=bool))
    s.step(s.compute_dt())
    P = s.state_numpy()["P"]
    assert (P >= 0.0).all(), f"kirpilmamis negatif basinc: {P.min()}"


def test_kirpma_YALNIZ_maskeliyi_etkiliyor():
    """Çekirdek doğrudan sınanır — atlayan sınav hiçbir şey kanıtlamaz.

    Basınç dizisini elle kurup çekirdeği başlatıyoruz: maskeli
    negatifler sıfırlanmalı, maskesizler AYNEN kalmalı, ve
    pozitifler HİÇ dokunulmamalı.
    """
    from dartrift.warp_core.cekme_kirpma import cekme_kirp

    s = _cozucu(np.zeros(64, dtype=bool))
    P0 = np.linspace(-3.0e7, 3.0e7, 64)
    maske = np.zeros(64, dtype=np.uint8)
    maske[::2] = 1                       # bir atlayarak maskele

    Pw = wp.array(P0.copy(), dtype=wp.float64, device=s.device)
    mw = wp.array(maske, dtype=wp.uint8, device=s.device)
    wp.launch(cekme_kirp, dim=64, inputs=[mw, Pw], device=s.device)
    P1 = Pw.numpy()

    kirpildi = (maske == 1) & (P0 < 0.0)
    assert (P1[kirpildi] == 0.0).all(), "maskeli negatifler kirpilmadi"
    assert np.array_equal(P1[maske == 0], P0[maske == 0]), (
        "maskesiz parcaciklara DOKUNULDU"
    )
    pozitif = (maske == 1) & (P0 >= 0.0)
    assert np.array_equal(P1[pozitif], P0[pozitif]), (
        "maskeli POZITIF basinclara dokunuldu -- yalniz cekme kirpilmali"
    )
    assert kirpildi.sum() > 0 and (maske == 0).sum() > 0, "sinav dejenere"

def test_maske_sekli_yanlissa_hata():
    with pytest.raises(ValueError, match="cekme_kirp_maske sekli"):
        _cozucu(np.ones(63, dtype=bool))


def test_kirpma_momentumu_bozmuyor():
    """Kırpma `P`'yi değiştirir ama çift kuvveti antisimetrik kalır."""
    s = _cozucu(np.ones(64, dtype=bool))
    p0 = (s.state_numpy()["m"][:, None] * s.state_numpy()["v"]).sum(axis=0)
    for _ in range(10):
        s.step(s.compute_dt())
    st = s.state_numpy()
    p1 = (st["m"][:, None] * st["v"]).sum(axis=0)
    olcek = max(float(np.abs(st["m"] * np.linalg.norm(st["v"], axis=1)).sum()),
                1.0)
    assert np.linalg.norm(p1 - p0) / olcek < 1e-12
