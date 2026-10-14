"""ADR-0060 dönüşüm sınavları — havuz dolmadan yazıldı (2026-10-14)."""

from __future__ import annotations

import numpy as np
import pytest

from dartrift.observables.beta_gelenegi import (
    ASGARI_KOSINUS,
    b_firlati_geleneginde,
    firlati_dogrultusu,
    gelenek_carpani,
)


def _sahne(theta_derece=22.0, n=400, tohum=3):
    """Çarpıcı `-z`'de; fırlatı `theta` kadar sapmış bir demet."""
    rng = np.random.default_rng(tohum)
    eU = np.array([0.0, 0.0, -1.0])
    t = np.radians(theta_derece)
    yon = np.array([np.sin(t), 0.0, np.cos(t)])        # geri tepme: +z'ye
    v = yon + 0.05 * rng.standard_normal((n, 3))
    m = np.full(n, 2.0)
    kacan = np.ones(n, bool)
    return v, m, kacan, eU


def test_ozdeslik_b_firlati_esittir_b_bolu_kos_kare():
    """Modülün vaadi: `b_fırlatı = b_çarpıcı / cos²θ`, tam olarak."""
    v, m, kacan, eU = _sahne()
    E, nP = firlati_dogrultusu(v, m, kacan)
    kos = float(E @ eU)
    p = 1234.5
    b_carpici = float((m[kacan] * (-(v[kacan] @ eU))).sum() / p)
    b_firlati = b_firlati_geleneginde(b_carpici, E, eU)
    # bagimsiz yol: dogrudan |P| / (p |cos|)
    assert b_firlati == pytest.approx(nP / (p * abs(kos)), rel=1e-12)
    assert b_firlati == pytest.approx(b_carpici / kos ** 2, rel=1e-12)


def test_duzeltme_DAIMA_buyutur():
    """`|cos θ| < 1` olduğundan çarpan `> 1`; yön seçilemez."""
    for aci in (1.0, 10.0, 22.0, 35.0, 55.0):
        v, m, kacan, eU = _sahne(aci)
        E, _ = firlati_dogrultusu(v, m, kacan)
        assert gelenek_carpani(E, eU) >= 1.0
        assert b_firlati_geleneginde(2.5, E, eU) >= 2.5


def test_tam_hizalida_carpan_bir():
    """`Ê ∥ ê_U` ise iki gelenek aynıdır."""
    eU = np.array([0.0, 0.0, -1.0])
    assert gelenek_carpani(-eU, eU) == pytest.approx(1.0, rel=1e-12)
    assert gelenek_carpani(eU, eU) == pytest.approx(1.0, rel=1e-12)


def test_isaret_onemsiz_kare_aliniyor():
    """`cos θ` negatif beklenir ama çarpan işarete duyarlı olmamalı."""
    eU = np.array([0.0, 0.0, -1.0])
    t = np.radians(22.0)
    E_arti = np.array([np.sin(t), 0.0, np.cos(t)])
    E_eksi = -E_arti
    assert gelenek_carpani(E_arti, eU) == pytest.approx(
        gelenek_carpani(E_eksi, eU), rel=1e-12)


def test_olculen_aralikta_oran_makul():
    """KAYIT-078 §6: `θ = 14,1°..27,7°` -> oran `1,063..1,275`."""
    eU = np.array([0.0, 0.0, -1.0])
    for aci, beklenen in ((14.1, 1.0630), (27.7, 1.2749)):
        t = np.radians(aci)
        E = np.array([np.sin(t), 0.0, np.cos(t)])
        assert gelenek_carpani(E, eU) == pytest.approx(beklenen, rel=2e-3)


def test_DIKLESIRKE_hata():
    """`1/cos²` ıraksarken sessizce devasa sayı dönmemeli."""
    eU = np.array([0.0, 0.0, -1.0])
    E = np.array([1.0, 0.0, 0.0])            # tam dik, cos = 0
    with pytest.raises(ValueError, match="iraksiyor"):
        gelenek_carpani(E, eU)
    kos = ASGARI_KOSINUS * 0.9
    E2 = np.array([np.sqrt(1 - kos ** 2), 0.0, -kos])
    with pytest.raises(ValueError, match="iraksiyor"):
        gelenek_carpani(E2, eU)


def test_birim_olmayan_vektorde_hata():
    eU = np.array([0.0, 0.0, -2.0])          # birim degil
    E = np.array([0.0, 0.0, 1.0])
    with pytest.raises(ValueError, match="birim vektor"):
        gelenek_carpani(E, eU)


def test_bos_kacan_ve_sifir_momentumda_hata():
    v, m, kacan, _ = _sahne()
    with pytest.raises(ValueError, match="kacan parcacik yok"):
        firlati_dogrultusu(v, m, np.zeros_like(kacan))
    # birbirini tam goturen iki parcacik: net momentum sifir
    v2 = np.array([[1.0, 0, 0], [-1.0, 0, 0]])
    with pytest.raises(ValueError, match="sifir"):
        firlati_dogrultusu(v2, np.array([1.0, 1.0]), np.ones(2, bool))


def test_olcek_degisimi_carpani_DEGISTIRMEZ():
    """`Ê` yön; kütle ya da hız ölçeği çarpanı etkilememeli."""
    v, m, kacan, eU = _sahne()
    E1, _ = firlati_dogrultusu(v, m, kacan)
    E2, _ = firlati_dogrultusu(3.7 * v, 11.0 * m, kacan)
    assert gelenek_carpani(E1, eU) == pytest.approx(
        gelenek_carpani(E2, eU), rel=1e-12)
