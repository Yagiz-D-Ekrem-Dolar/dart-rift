"""Kaçış sınıflaması — uzman Soru 10'un tanımı kilitli."""
from __future__ import annotations

import numpy as np
import pytest

from dartrift.observables.kacis import G_SI, kacis_siniflari

R = 10.0
M_TOP = 1.0e9


def _kure(n=4000, tohum=0):
    rng = np.random.default_rng(tohum)
    u = rng.normal(size=(n, 3))
    u /= np.linalg.norm(u, axis=1)[:, None]
    r = R * rng.random(n) ** (1.0 / 3.0)
    x = u * r[:, None]
    return x, np.zeros_like(x), np.full(n, M_TOP / n)


def _v_esc():
    return np.sqrt(2.0 * G_SI * M_TOP / R)


def _yuzey_parcaciklari(x, v, hiz, k, bas):
    r = np.linalg.norm(x, axis=1)
    idx = np.argsort(-r)[bas:bas + k]
    v[idx] = hiz * x[idx] / r[idx, None]
    return idx


def test_hizlilar_BAGSIZ_yavaslar_BAGLI():
    x, v, m = _kure()
    hizli = _yuzey_parcaciklari(x, v, 10.0 * _v_esc(), 20, 0)
    yavas = _yuzey_parcaciklari(x, v, 0.1 * _v_esc(), 20, 20)
    s = kacis_siniflari(x, v, m, R=R)
    assert s["yakinsadi"]
    assert np.all(s["bagsiz_maske"][hizli])
    assert not np.any(s["bagsiz_maske"][yavas])
    assert s["M_bagsiz_hedef"] == pytest.approx(20 * M_TOP / len(m))


def test_GALILE_degismez():
    x, v, m = _kure()
    _yuzey_parcaciklari(x, v, 10.0 * _v_esc(), 20, 0)
    a = kacis_siniflari(x, v, m, R=R)
    b = kacis_siniflari(x, v + np.array([5.0, -3.0, 1.0]), m, R=R)
    assert np.array_equal(a["bagsiz_maske"], b["bagsiz_maske"])


def test_sabit_olcutun_KACIRDIGI_ic_madde_SAYILIYOR():
    """`r < R` ama `ε > 0`: defterin `r > R` şartı bunu saymaz."""
    x, v, m = _kure()
    r = np.linalg.norm(x, axis=1)
    ic = np.flatnonzero((r > 0.8 * R) & (r < 0.95 * R))[:30]
    v[ic] = 20.0 * _v_esc() * x[ic] / r[ic, None]
    s = kacis_siniflari(x, v, m, R=R)
    assert s["M_bagsiz_iceride_hedef"] == pytest.approx(30 * M_TOP / len(m))
    assert s["M_bagsiz_disarida_hedef"] == 0.0


def test_YINELEME_bagli_kutleyi_guncelliyor_ve_duruyor():
    x, v, m = _kure()
    _yuzey_parcaciklari(x, v, 10.0 * _v_esc(), 200, 0)
    s = kacis_siniflari(x, v, m, R=R)
    assert s["yakinsadi"] and 2 <= s["n_tur"] <= 5
    assert s["M_bagli"] == pytest.approx(M_TOP * (1 - 200 / len(m)))


def test_azami_tur_asilirsa_YAKINSAMADI_der():
    x, v, m = _kure()
    _yuzey_parcaciklari(x, v, 10.0 * _v_esc(), 200, 0)
    s = kacis_siniflari(x, v, m, R=R, azami_tur=1)
    assert s["yakinsadi"] is False


def test_sinirdaki_parcacik_BAYRAKLANIYOR():
    x, v, m = _kure()
    r = np.linalg.norm(x, axis=1)
    i = int(np.argmax(r))
    # tam kacis hizi (sinirda)
    phi = -G_SI * M_TOP / r[i]
    v[i] = np.sqrt(-2.0 * phi) * x[i] / r[i]
    s = kacis_siniflari(x, v, m, R=R, sinir_payi=1e-2)
    assert s["n_sinirda"] >= 1


def test_beta_ISARET_kurali_defterle_ayni():
    """Kaçan madde `−ê` yönünde gidiyorsa `β > 1`."""
    x, v, m = _kure()
    e = np.array([0.0, 0.0, -1.0])        # mermi -z yonunde gidiyor
    # carpma yuzu +z; ejekta +z yonunde (yani -e) kaciyor
    ust = np.flatnonzero(x[:, 2] > 0.9 * R)[:10]
    v[ust] = np.array([0.0, 0.0, 10.0 * _v_esc()])
    s = kacis_siniflari(x, v, m, R=R, ehat=e, p_imp=1.0e6)
    assert s["P_bagsiz_hedef_eksenel"] < 0.0
    assert s["beta_enerji"] > 1.0


def test_iceri_giden_hizli_madde_BETAYA_girmiyor():
    """Ölçülen yapıt: şoklanıp İÇERİ giden madde de `ε > 0`; ilk sürüm
    onu `β`'ya katıp `β_enerji = 0,84` (< 1) veriyordu."""
    x, v, m = _kure()
    e = np.array([0.0, 0.0, -1.0])
    r = np.linalg.norm(x, axis=1)
    ic = np.flatnonzero((x[:, 2] > 0.5 * R) & (r < 0.9 * R))[:20]
    v[ic] = np.array([0.0, 0.0, -20.0 * _v_esc()])      # iceri, hizli
    s = kacis_siniflari(x, v, m, R=R, ehat=e, p_imp=1.0e6)
    assert s["M_bagsiz_hedef"] > 0.0                   # eps > 0
    assert s["M_bagsiz_disa_hedef"] == 0.0             # ama disa degil
    assert s["beta_enerji"] == pytest.approx(1.0)      # beta'ya girmiyor
    assert s["beta_enerji_tum"] < 1.0                  # eski tanim yanlis


def test_stres_dalgasi_yuzeyi_EJEKTA_degil_h_mesafesiyle():
    """Yüzey `mm` yer değiştirip `v_esc`'nin üstünde dışa gidiyor:
    `ε > 0` ve dışa ama KENDİ desteğinden çıkmamış → ejekta değil."""
    x, v, m = _kure()
    r = np.linalg.norm(x, axis=1)
    ust = np.flatnonzero(r > 0.95 * R)[:50]
    x1 = x.copy()
    x1[ust] *= 1.0005                                  # ~5 mm
    v[ust] = 3.0 * _v_esc() * x[ust] / r[ust, None]
    s = kacis_siniflari(x1, v, m, R=R, x0=x, h=0.5,
                        ehat=np.array([0.0, 0.0, -1.0]), p_imp=1.0e6)
    assert s["M_bagsiz_disa_hedef"] > 0.0
    assert s["M_ejekta_hedef"] == 0.0
    assert s["beta_sinifi"] == "ejekta" and s["beta_enerji"] == pytest.approx(1.0)


def test_ayrilmis_sinifi_x0_ISTER():
    x, v, m = _kure()
    s = kacis_siniflari(x, v, m, R=R)
    assert "M_ayrilmis_hedef" not in s
    x1 = x.copy()
    top = np.flatnonzero(np.linalg.norm(x, axis=1) > 0.95 * R)[:5]
    x1[top] *= 1.02
    v[top] = 0.5 * _v_esc() * x[top] / np.linalg.norm(x[top], axis=1)[:, None]
    s = kacis_siniflari(x1, v, m, R=R, x0=x)
    assert s["M_ayrilmis_hedef"] == pytest.approx(5 * M_TOP / len(m))
    assert s["M_ayrilmis_bagsiz_hedef"] == 0.0     # yavas: ayrilmis ama bagli


def test_mermi_kesri_AYRI_sayiliyor():
    x, v, m = _kure()
    idx = _yuzey_parcaciklari(x, v, 10.0 * _v_esc(), 10, 0)
    f = np.zeros(len(m))
    f[idx[:4]] = 1.0
    s = kacis_siniflari(x, v, m, R=R, mermi_kesri=f)
    birim = M_TOP / len(m)
    assert s["M_bagsiz_mermi"] == pytest.approx(4 * birim)
    assert s["M_bagsiz_hedef"] == pytest.approx(6 * birim)
