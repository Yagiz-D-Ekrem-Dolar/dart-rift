"""ADR-0054 (C1) — gözlenen `β` hedefinin sahnenin kütlesiyle tutarlılığı.

Bu sınavlar **karar vermiyor**; ADR'nin dayandığı sayıların kodun kendisinden
çıktığını ve kilitli `3,12`'nin kaynağının eski sahne kütlesi olduğunu
kayda geçiriyor.
"""
from __future__ import annotations

import numpy as np
import pytest

from dartrift.observables import dart_gozlemleri as G
from dartrift.observables import period_interface as PI

M_DY2 = 4.2980e9          # KAYIT-072: uretim sahnesinin olculen kutlesi
M_ESKI = 4.160e9          # PROTOKOL-U S1'in sahnesi (eski kure)
P_MERMI = 579.4 * 6144.9  # Daly 2023


def test_Cheng_kunyesi_birincil_kaynakla_uyumlu():
    """arXiv:2303.03464: `β = 3,61 (+0,19 / −0,25)`, `ρ_ref = 2400`."""
    assert G.CHENG_BETA_2400 == 3.61
    assert G.CHENG_BETA_SIGMA == (0.25, 0.19)      # (-, +) asimetrik
    assert G.CHENG_RHO_REF == 2400.0
    # yayinlanan aralik: rho 1500-3300 -> beta 2,2-4,9
    assert G.cheng_beta(1500.0)["beta"] == pytest.approx(2.2, abs=0.05)
    assert G.cheng_beta(3300.0)["beta"] == pytest.approx(4.9, abs=0.05)


def test_kilitli_3p12_ESKI_sahnenin_kutlesinden_geliyor():
    """ADR-0054 §2: `3,12`, `M = 4,16e9` ile türetilmiş; üretim sahnesi `4,298e9`."""
    dT = PI.DIMORPHOS_SYSTEM["measured_period_change"]
    b_eski = PI.beta_from_period_change(dT, P_MERMI, target_mass=M_ESKI)
    b_yeni = PI.beta_from_period_change(dT, P_MERMI, target_mass=M_DY2)
    assert b_eski == pytest.approx(3.12, abs=0.005)      # PROTOKOL-U S1
    assert b_yeni == pytest.approx(3.221, abs=0.005)     # uretim sahnesi
    # beta gozlem kutleyle neredeyse DOGRU ORANTILI: yorungenin kendisi de
    # kutleye bagli oldugu icin oran tam dogrusal DEGIL (sapma ~1,3e-4).
    oran = b_yeni / b_eski
    assert oran == pytest.approx(M_DY2 / M_ESKI, rel=1e-3)
    assert oran != M_DY2 / M_ESKI          # tam dogrusal OLMADIGI kayitta


def test_onerilen_hedef_ve_DY2_uygunsuzlugu():
    """ADR-0054 §4 tablosu: `I` `1,54` → `0,63`; sd DARALIYOR."""
    d = G.cheng_beta(hedef_kutlesi=M_DY2)
    assert d["beta"] == pytest.approx(3.5418, abs=0.001)
    s_ust = d["beta_ust"] - d["beta"]
    assert s_ust == pytest.approx(0.188, abs=0.002)
    assert s_ust < 0.34                      # gozlem sd'si DARALIYOR (sinav zorlasiyor)
    rel = 0.10668                            # dort terimin bagil toplami
    for hedef, s_g, bekle in ((3.12, 0.34, 1.54), (d["beta"], s_ust, 0.63)):
        payda = float(np.hypot(s_g, (hedef - 1.0) * rel))
        assert abs(3.7480 - hedef) / payda == pytest.approx(bekle, abs=0.02)


def test_DY2_nin_betasi_yayinlanan_yogunluk_araliginda():
    """ADR-0054 §4.3: `β = 3,748` → `ρ = 2512 kg/m³`, `1500–3300` içinde."""
    rho = (3.7480 + G.CHENG_SABIT) * G.CHENG_RHO_REF / G.CHENG_BETA_2400
    assert rho == pytest.approx(2511.7, abs=1.0)
    assert 1500.0 <= rho <= 3300.0
    assert G.cheng_beta(rho)["beta"] == pytest.approx(3.7480, abs=1e-9)


def test_sabit_3p61_almak_kutle_eslesmesini_kaciriyor():
    """§6: Cheng'in `ρ = 2400` varsayımı bizim sahnemizin kütlesi değil."""
    M_cheng = G.CHENG_RHO_REF * G.DIMORPHOS_SEKIL["hacim_m3"]
    assert M_cheng == pytest.approx(4.344e9, rel=1e-3)
    assert abs(M_cheng / M_DY2 - 1.0) == pytest.approx(0.0107, abs=0.002)
