"""Settling testleri (P3-FR-05, P3-VR-01).

GPU gerektirmeyen kisim burada; GPU'lu oturma kosusu `test_settling_gpu.py`
altinda ve `gpu` isaretiyle ayrilmistir (yerelde/TRUBA'da kosar, CI'da atlanir).
"""

import numpy as np
import pytest

from dartrift.setup.settling import G_GRAV, SettleResult, binding_energy


def test_baglanma_enerjisi_formulu():
    """(3/5) G M^2 / R — duzgun kure."""
    m, r = 1.0e9, 100.0
    assert binding_energy(m, r) == pytest.approx(0.6 * G_GRAV * m * m / r, rel=1e-14)


def test_baglanma_enerjisi_olcekleme():
    """M^2/R: kutle 2x -> 4x, yaricap 2x -> 1/2x."""
    e0 = binding_energy(1.0e9, 100.0)
    assert binding_energy(2.0e9, 100.0) / e0 == pytest.approx(4.0, rel=1e-14)
    assert binding_energy(1.0e9, 200.0) / e0 == pytest.approx(0.5, rel=1e-14)


def test_baglanma_enerjisi_pozitif_yaricap_ister():
    for r in (0.0, -1.0):
        with pytest.raises(ValueError, match="yaricap"):
            binding_energy(1.0, r)


def test_dimorphos_baglanma_enerjisi_buyuklugu():
    """Dis kaynak capraz kontrolu: Dimorphos icin E_bag ~ 9e6 J mertebesi.

    M ~ 4.3e9 kg, R ~ 82 m (Daly ve digerleri 2023, DART sonuclari).
    Bu, DART'in getirdigi ~1.1e10 J kinetik enerjinin ~1/1200'u — yani
    carpma, hedefi baglayan enerjiden mertebelerce buyuktur. Mertebe
    tutmuyorsa ya sabit ya formul yanlistir.
    """
    e = binding_energy(4.3e9, 82.0)
    assert 1.0e6 < e < 1.0e8, e
    # DART: 579.4 kg @ 6144.9 m/s -> E_kin / E_bag ~ 1e3
    assert 100.0 < (0.5 * 579.4 * 6144.9**2) / e < 1.0e4
    # kacis hizi ~ sqrt(2GM/R) ~ 8-9 cm/s olmali
    v_kac = np.sqrt(2.0 * G_GRAV * 4.3e9 / 82.0)
    assert 0.05 < v_kac < 0.15, v_kac


def test_sonuc_kabi_varsayilanlari():
    r = SettleResult(x=np.zeros((2, 3)), v=np.zeros((2, 3)),
                     rho=np.ones(2), alpha=np.ones(2), n_steps=0, t_end=0.0)
    assert r.converged is False          # sessizce "oldu" demez
    assert r.ke_series == [] and r.diagnostics == {}


def test_yercekimi_kapaliysa_reddeder():
    """Sartname oz-yercekimi altinda oturtma istiyor; kapaliysa sessizce
    'duz uzayda gevseme' yapip buna settling demek yanlis olur."""
    from dartrift.cpu_reference.materials import GravityParams, MaterialParams

    mat = MaterialParams(gravity=GravityParams(enabled=False))
    from dartrift.setup.settling import settle_pile
    with pytest.raises(ValueError, match="oz-yercekimi"):
        settle_pile(None, mat)


def test_gecersiz_sonumleme_reddedilir():
    from dartrift.cpu_reference.materials import GravityParams, MaterialParams
    from dartrift.setup.settling import settle_pile

    mat = MaterialParams(gravity=GravityParams(enabled=True))
    for d in (-0.1, 1.0, 1.5):
        with pytest.raises(ValueError, match="damping"):
            settle_pile(None, mat, damping=d)
