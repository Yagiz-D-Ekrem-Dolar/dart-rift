"""ADR-0050 — β iki yöntem, ejekta koni açısı, elipsoit "dışarıda" ölçütü."""
from __future__ import annotations

import numpy as np
import pytest

from dartrift.observables.beta_iki_yontem import (
    beta_iki_yontem,
    beta_kutle_merkezi,
    ejekta_koni_acisi,
)
from dartrift.observables.momentum_defteri import disarida_maskesi, momentum_defteri
from dartrift.observables.momentum_transfer import escape_speed

G = 6.6743e-11


def _govde(n=2000, R=80.0, rho=1800.0, seed=1):
    rng = np.random.default_rng(seed)
    p = rng.uniform(-1, 1, (4 * n, 3))
    p = p[np.linalg.norm(p, axis=1) <= 1.0][:n] * R
    M = rho * 4.0 / 3.0 * np.pi * R ** 3
    return p, np.full(len(p), M / len(p)), M


def _durum(*, V_govde=1e-2, ejekta_hiz=5.0, n_ej=200, yavas=None, R=80.0):
    """Gövde `+ê` yönünde `V_govde` ile, ejekta `−ê` yönünde dışarıda."""
    e = np.array([0.0, 0.0, -1.0])
    xg, mg, M = _govde(R=R)
    vg = np.tile(V_govde * e, (len(xg), 1))
    rng = np.random.default_rng(7)
    xe = np.column_stack([rng.normal(0, 3, n_ej), rng.normal(0, 3, n_ej),
                          np.full(n_ej, 1.5 * R)])
    ve = np.tile(-ejekta_hiz * e, (n_ej, 1))
    me = np.full(n_ej, 1.0e4)
    x = np.vstack([xg, xe])
    v = np.vstack([vg, ve])
    m = np.concatenate([mg, me])
    if yavas is not None:
        x = np.vstack([x, yavas[0]])
        v = np.vstack([v, yavas[1]])
        m = np.concatenate([m, [yavas[2]]])
    P = m @ v
    p_imp = float(P @ e)
    return x, v, m, e, p_imp, M


def test_iki_yontem_SINIFLAMA_AYNIYKEN_esit_ve_beklenen_degerde():
    x, v, m, e, p_imp, M = _durum()
    R = 80.0
    v_esc = escape_speed(M, R)
    f = np.zeros(len(m))
    r = beta_iki_yontem(x, v, m, mermi_kesri=f, R=R, v_esc=v_esc, ehat=e,
                        p_imp=p_imp)
    P_ej = 200 * 1.0e4 * 5.0            # -e yonunde
    beklenen = 1.0 + P_ej / p_imp
    assert r["beta_kacan"] == pytest.approx(beklenen, rel=1e-9)
    assert r["beta_km"] == pytest.approx(beklenen, rel=1e-9)
    assert abs(r["fark_km_eksi_kacan"]) < 1e-9
    assert r["defter_kapandi"]


def test_iki_yontem_YAVAS_bagsiz_maddede_AYRISIYOR():
    """`r = 2R`'de `0,9·v_esc(R)` ile dışa giden madde: hız eşiğinin altında
    (yöntem 1 saymaz) ama `½v² = 0,81 GM/R > GM/2R` → enerjice bağsız
    (yöntem 2 sayar). Fark tam olarak onun momentumu."""
    R = 80.0
    _, _, M = _govde(R=R)
    v_esc = escape_speed(M, R)
    e = np.array([0.0, 0.0, -1.0])
    m_y = 5.0e5
    yavas = (np.array([[0.0, 0.0, 2.0 * R]]),
             np.array([[0.0, 0.0, 0.9 * v_esc]]), m_y)
    x, v, m, e, p_imp, M = _durum(yavas=yavas)
    r = beta_iki_yontem(x, v, m, mermi_kesri=np.zeros(len(m)), R=R,
                        v_esc=v_esc, ehat=e, p_imp=p_imp)
    assert r["fark_km_eksi_kacan"] == pytest.approx(m_y * 0.9 * v_esc / p_imp,
                                                   rel=1e-6)


def test_beta_km_p_imp_SIFIR_REDDEDILIYOR():
    x, v, m, e, _, _ = _durum()
    with pytest.raises(ValueError, match="p_imp"):
        beta_kutle_merkezi(x, v, m, R=80.0, ehat=e, p_imp=0.0)


def test_koni_TEK_YONLU_akista_sifir():
    v = np.tile([0.0, 0.0, 3.0], (50, 1))
    k = ejekta_koni_acisi(v, np.ones(50))
    assert k["koni_tam_acisi_derece"] == pytest.approx(0.0, abs=1e-6)


def test_koni_YARIM_KUREYE_duzgun_yayilmada_kuramsal_deger():
    """cos θ yarım kürede düzgün → P(θ ≤ θ*) = 1 − cos θ* → %90: θ* = 84,26°."""
    rng = np.random.default_rng(11)
    n = 200_000
    cz = rng.uniform(0.0, 1.0, n)
    ph = rng.uniform(0.0, 2 * np.pi, n)
    s = np.sqrt(1 - cz ** 2)
    v = np.column_stack([s * np.cos(ph), s * np.sin(ph), cz])
    k = ejekta_koni_acisi(v, np.ones(n), kesir=0.9, eksen=[0, 0, 1])
    assert k["koni_tam_acisi_derece"] == pytest.approx(
        2 * np.degrees(np.arccos(0.1)), abs=0.3)


def test_koni_gecersiz_kesir_REDDEDILIYOR():
    with pytest.raises(ValueError, match="kesir"):
        ejekta_koni_acisi(np.ones((3, 3)), np.ones(3), kesir=1.0)


def test_disarida_KURE_ve_ESIT_EKSENLI_elipsoit_ayni():
    rng = np.random.default_rng(2)
    x = rng.uniform(-100, 100, (5000, 3))
    a = disarida_maskesi(x, R=80.0)
    b = disarida_maskesi(x, R=80.0, yari_eksenler=(80.0, 80.0, 80.0))
    assert np.array_equal(a, b)


def test_disarida_BASIK_elipsoitte_uzun_eksen_ucu_ICERIDE():
    """Dimorphos (L2): 88,5 × 87 × 58 m; `R_eş ≈ 75,6 m`."""
    ax = (88.5, 87.0, 58.0)
    R_es = (ax[0] * ax[1] * ax[2]) ** (1 / 3)
    uc = np.array([[88.0, 0.0, 0.0]])                 # uzun eksen ucunun hemen ici
    assert disarida_maskesi(uc, R=R_es)[0]            # kure olcutu: DISARIDA (yanlis)
    assert not disarida_maskesi(uc, R=R_es, yari_eksenler=ax)[0]
    kutup = np.array([[0.0, 0.0, 60.0]])              # kisa eksen ucunun disi
    assert disarida_maskesi(kutup, R=R_es, yari_eksenler=ax)[0]


def test_disarida_gecersiz_eksen_REDDEDILIYOR():
    with pytest.raises(ValueError, match="yari_eksenler"):
        disarida_maskesi(np.zeros((1, 3)), R=1.0, yari_eksenler=(1.0, 0.0, 1.0))


def test_defter_yari_eksenler_None_ile_ESKI_sonucla_BIT_AYNI():
    x, v, m, e, p_imp, M = _durum()
    f = np.zeros(len(m))
    kw = dict(mermi_kesri=f, R=80.0, v_esc=escape_speed(M, 80.0), ehat=e,
              p_imp=p_imp)
    a = momentum_defteri(x, v, m, **kw)
    b = momentum_defteri(x, v, m, **kw, yari_eksenler=None)
    c = momentum_defteri(x, v, m, **kw, yari_eksenler=(80.0, 80.0, 80.0))
    assert a["beta_hedef"] == b["beta_hedef"] == c["beta_hedef"]



def test_KONI_KENAR_acisi_kutle_yuzdeliginden_GENIS():
    """Gözlem koninin görünen kenarını ölçüyor; model tarafında %99 açısı
    raporlanıyor ve %90'dan dar olamaz."""
    x, v, m, e, p_imp, M = _durum()
    rng = np.random.default_rng(5)
    v = v.copy()
    ej = slice(len(v) - 200, len(v))
    v[ej] = v[ej] + rng.normal(0.0, 2.0, (200, 3))
    r = beta_iki_yontem(x, v, m, mermi_kesri=np.zeros(len(m)), R=80.0,
                        v_esc=escape_speed(M, 80.0), ehat=e, p_imp=p_imp)
    assert r["koni_kenar_derece"] >= r["koni_tam_acisi_derece"]
