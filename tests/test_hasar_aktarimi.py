"""Hasar **aktarımı** — `D` kabalaştırmadan sağ çıkıyor mu.

Ölçülmüş kusur (2026-08-21): aşama-1'de şok geçerken Grady-Kipp hasarı
`D_max = 0,562`'ye çıkıyordu, aktarım onu **taşımıyordu** ve aşama-2
çözücüsü `D = 0` ile başlıyordu. Yani şokun ürettiği bütün hasar
`t₁`'de siliniyordu ve cisim çekmede yeniden *"sınırsız dayanıklı"*
oluyordu — ADR-0027'nin `β`'yı küçültür dediği tam durum.

Kusur **sessizdi**: `--hasarli` kolu hasarsız kolla aynı `β`'yı
veriyordu ve hiçbir defter tutmuyordu.
"""
from __future__ import annotations

import numpy as np
import pytest

from dartrift.setup.coarsen import coarsen_to_sites, sites_from_cloud
from dartrift.setup.two_stage import asama2_sahnesi_ucseviye


def _bulut(n=600, r=3.0, seed=11):
    rng = np.random.default_rng(seed)
    x = rng.normal(0.0, r, size=(n, 3))
    v = rng.normal(0.0, 50.0, size=(n, 3))
    m = rng.uniform(0.5, 2.0, n)
    e = rng.uniform(1e3, 1e5, n)
    D = rng.uniform(0.0, 1.0, n)
    return x, v, m, e, D


def test_kabalastirma_Sum_m_D_yi_TAM_koruyor() -> None:
    """`D` pasif skaler: kütleyle ağırlıklı toplamı korunmalı."""
    x, v, m, e, D = _bulut()
    k = coarsen_to_sites(x, v, m, e, sites_from_cloud(x, 1.5), hasar=D)
    assert k["hasar_kutle_hatasi"] < 1e-12, k["hasar_kutle_hatasi"]
    assert np.all(k["hasar"] >= 0.0) and np.all(k["hasar"] <= 1.0)


def test_kabalastirma_ARALIK_DISI_hasari_reddediyor() -> None:
    x, v, m, e, D = _bulut()
    D[3] = 1.5
    with pytest.raises(ValueError, match="araliginda"):
        coarsen_to_sites(x, v, m, e, sites_from_cloud(x, 1.5), hasar=D)


class _SahteA1:
    """Üç seviyeli aşama-1 sahnesinin asgari yüzü."""

    def __init__(self, n=600, s2=1.5):
        rng = np.random.default_rng(3)
        self.x = rng.normal(0.0, 3.0, size=(n, 3))
        self.v = np.zeros((n, 3))
        self.m = np.full(n, 1.0)
        self.alpha0 = np.full(n, 1.6)
        self.Y0 = np.full(n, 1.0e4)
        self.is_boulder = np.zeros(n, bool)
        self.is_impactor = np.zeros(n, bool)
        self.h = np.full(n, 2.0 * s2)
        # yarisi ince (kabalastirilacak), yarisi kopyalanacak
        self.is_fine = np.zeros(n, bool)
        self.is_fine[: n // 2] = True
        self.diagnostics = {"ucseviye": True, "s2": s2}


def _durum(a1, D):
    n = len(a1.m)
    return {"x": a1.x, "v": a1.v, "u": np.zeros(n), "D": D}


def test_aktarim_HASARI_TASIYOR() -> None:
    a1 = _SahteA1()
    n = len(a1.m)
    D = np.full(n, 0.4)
    s = asama2_sahnesi_ucseviye(a1, _durum(a1, D))
    assert s.hasar is not None
    assert s.diagnostics["hasar_max"] > 0.0
    # Kopyalanan bolge birebir, kabalastirilan bolge kutle-agirlikli
    # ortalama -> tekduze `D` her yerde ayni kalmali.
    assert np.allclose(s.hasar, 0.4, atol=1e-12)
    assert s.diagnostics["hasar_kutle_hatasi"] < 1e-12


def test_hasar_YOKSA_sifir_ve_defter_tutuyor() -> None:
    """Hasar kapalı koşuda `state_numpy` sıfır döner; yol aynı olmalı."""
    a1 = _SahteA1()
    s = asama2_sahnesi_ucseviye(a1, _durum(a1, np.zeros(len(a1.m))))
    assert s.diagnostics["hasar_max"] == 0.0
    assert np.all(s.hasar == 0.0)


def test_aktarim_D_UZUNLUGUNU_denetliyor() -> None:
    a1 = _SahteA1()
    d = _durum(a1, np.zeros(len(a1.m)))
    d["D"] = np.zeros(len(a1.m) - 1)
    with pytest.raises(ValueError, match="D uzunlugu"):
        asama2_sahnesi_ucseviye(a1, d)


@pytest.mark.warp
def test_cozucu_D0_yu_SESSIZCE_YUTMUYOR() -> None:
    """Hasar kapalıyken `D0` vermek **hata** olmalı, sessiz kayıp değil."""
    wp = pytest.importorskip("warp")
    assert wp is not None
    from dartrift.cpu_reference.materials import MaterialParams, StrengthParams
    from dartrift.warp_core.solver_solid import WarpSolid3D

    n = 8
    x = np.zeros((n, 3))
    x[:, 0] = np.arange(n) * 1.0
    kw = dict(v=np.zeros((n, 3)), m=np.ones(n), u=np.zeros(n), h=2.0)
    mat = MaterialParams(eos="linear", c0=100.0, rho0_linear=1000.0,
                         density_method="continuity",
                         strength=StrengthParams(enabled=True, Y0=1.0e4))
    with pytest.raises(ValueError, match="SESSIZCE"):
        WarpSolid3D(x, kw["v"], kw["m"], kw["u"], kw["h"], mat,
                    device="cpu", D0=np.full(n, 0.3))
