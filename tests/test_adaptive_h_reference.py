"""A′ uygulaması — CPU referansında parçacık başına `h` (ADR-0041).

Kilitlenen sözleşmenin dördüncü maddesi: **skaler `h` yolu bit düzeyinde
korunur.** Bu dosyanın ilk testi tam olarak onu sınar; gerisi değişken `h`
yolunun doğruluğunu.
"""
from __future__ import annotations

import numpy as np
import pytest

from dartrift.cpu_reference.adaptive_h import is_scalar_h, max_h, pair_h, per_particle_h


def test_skaler_h_SKALERIN_KENDISI_donuyor() -> None:
    """ADR-0041 §5b-4: skaler yol **hiç değişmemeli**.

    `pair_h` skaler için dizi döndürseydi `q = r/h_ij` bir dizi bölmesine
    dönerdi; NumPy aynı sonucu verir ama **varsaymak** yerine ifadeyi hiç
    değiştirmemek daha güvenlidir (K21'in ilk düzeltmesi `1e-14` fark
    üretmişti).
    """
    assert pair_h(2.5, 10) == 2.5
    assert is_scalar_h(2.5) and is_scalar_h(np.float64(2.5))
    assert not is_scalar_h(np.array([1.0, 2.0]))


def test_dizi_h_SIMETRIK_matris() -> None:
    h = np.array([1.0, 3.0, 5.0])
    m = pair_h(h, 3)
    assert m.shape == (3, 3)
    assert np.allclose(m, m.T)                      # SIMETRIK
    assert m[0, 1] == pytest.approx(2.0)            # (1+3)/2
    assert m[1, 2] == pytest.approx(4.0)            # (3+5)/2
    assert np.allclose(np.diag(m), h)               # h_ii = h_i


def test_gecersiz_h_reddediliyor() -> None:
    with pytest.raises(ValueError, match="şekli"):
        pair_h(np.array([1.0, 2.0]), 3)
    with pytest.raises(ValueError, match="pozitif"):
        pair_h(np.array([1.0, -2.0, 3.0]), 3)


def test_per_particle_h_skaleri_yayiyor() -> None:
    assert np.allclose(per_particle_h(2.5, 4), 2.5)
    assert per_particle_h(2.5, 4).shape == (4,)
    assert np.allclose(per_particle_h(np.array([1.0, 2.0]), 2), [1.0, 2.0])


def test_max_h() -> None:
    assert max_h(3.0) == 3.0
    assert max_h(np.array([1.0, 7.0, 2.0])) == 7.0


# --- GERILEME: cozucu skaler h ile BIT AYNI mi?

def _durum(h):
    from dartrift.cpu_reference.materials import (
        DamageParams,
        GravityParams,
        MaterialParams,
        PorosityParams,
        StrengthParams,
    )
    from dartrift.cpu_reference.solid_ref import SolidState

    rng = np.random.default_rng(4041)
    n = 60
    x = rng.uniform(-1.0, 1.0, (n, 3))
    mat = MaterialParams(
        eos="tillotson",
        strength=StrengthParams(enabled=True, Y0=1.0e5, mu_f=0.8, YM=1.5e9,
                                shear_G=2.27e10, jaumann=True),
        porosity=PorosityParams(enabled=False),
        gravity=GravityParams(enabled=False),
        damage=DamageParams(enabled=False),
        density_method="continuity")
    st = SolidState(x=x, v=rng.normal(0.0, 1.0, (n, 3)), m=np.full(n, 1.0e3),
                    u=np.full(n, 1.0e4), h=h, active=np.ones(n, bool),
                    alpha=np.ones(n), rho=np.full(n, 2700.0))
    return st, mat


def test_skaler_yol_BIT_AYNI() -> None:
    """Aynı skaler `h`, sarmalayıcıdan önce ve sonra **birebir** aynı sonuç.

    Doğrudan kıyaslayamayız (eski kod yok), ama eşdeğer bir değişmez var:
    `h = 2.0` skaler ile `h = np.full(n, 2.0)` dizi **aynı** sonucu vermeli,
    çünkü `h_ij = ½(2+2) = 2`. Fark çıkarsa sarmalayıcı yuvarlamayı
    değiştiriyor demektir.
    """
    from dartrift.cpu_reference.solid_ref import evaluate_solid
    from dartrift.cpu_reference.sph_ref import RefParams

    st_s, mat = _durum(2.0)
    st_d, _ = _durum(np.full(60, 2.0))
    evaluate_solid(st_s, mat, RefParams(cfl=0.2))
    evaluate_solid(st_d, mat, RefParams(cfl=0.2))
    for ad in ("P", "cs", "a", "divv", "dudt"):
        a, b = getattr(st_s, ad), getattr(st_d, ad)
        assert np.array_equal(a, b), (
            f"{ad}: skaler ve tekduze-dizi yollari AYRISTI, "
            f"en buyuk fark {np.max(np.abs(a - b)):.3e}")


def test_degisken_h_momentum_koruyor() -> None:
    """Simetrik `h_ij` ⇒ `f_ij = −f_ji` ⇒ `Σ mᵢaᵢ = 0` **tam**.

    Bu, `average_h` biçiminin seçilme sebebidir (KAYIT-024).
    """
    from dartrift.cpu_reference.solid_ref import evaluate_solid
    from dartrift.cpu_reference.sph_ref import RefParams

    rng = np.random.default_rng(7)
    h = rng.uniform(1.0, 3.0, 60)                  # GERCEKTEN degisken
    st, mat = _durum(h)
    evaluate_solid(st, mat, RefParams(cfl=0.2))
    net = np.abs(np.sum(st.m[:, None] * st.a, axis=0))
    olcek = float(np.sum(st.m * np.linalg.norm(st.a, axis=1))) or 1.0
    assert float(np.max(net)) / olcek < 1.0e-12, (net, olcek)
    # BOSLUK KONTROLU: h GERCEKTEN degisken mi (yoksa test bos olur)?
    assert float(np.ptp(h)) > 1.0


def test_degisken_h_sonucu_DEGISTIRIYOR() -> None:
    """KALİBRASYON: değişken `h`, skalerden **farklı** sonuç vermeli.

    Vermezse `pair_h` bağlanmamış demektir ve yukarıdaki testler boş.
    """
    from dartrift.cpu_reference.solid_ref import evaluate_solid
    from dartrift.cpu_reference.sph_ref import RefParams

    rng = np.random.default_rng(7)
    st_s, mat = _durum(2.0)
    st_d, _ = _durum(rng.uniform(1.0, 3.0, 60))
    evaluate_solid(st_s, mat, RefParams(cfl=0.2))
    evaluate_solid(st_d, mat, RefParams(cfl=0.2))
    fark = np.max(np.abs(st_s.a - st_d.a)) / max(np.max(np.abs(st_s.a)), 1e-300)
    assert fark > 1.0e-3, fark
