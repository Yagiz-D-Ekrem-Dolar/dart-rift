"""K21 — Tillotson EOS **toplam** mı? Sonlu girdi → sonlu çıktı.

Bulunuş: FAZ 4'ün E2 ölçümünde `RuntimeWarning: overflow encountered in exp`
görüldü. Kök neden: genleşmiş-sıcak kolda üs `-beta*(1/eta - 1)`'dir. `eta`
küçük **negatif** iken `1/eta` büyük negatif, üs büyük **pozitif** olur,
`exp` **taşar** (inf) ve `inf * ex2` (`ex2 = exp(-çok büyük) = 0`) **NaN**
verir. NaN oradan her komşu toplamına yayılır.

GPU'da bu **sessizdir** — `RuntimeWarning` yoktur. Yani bir üretim koşusu
baştan sona NaN üretip "bitti" diyebilirdi.

`rho <= 0` asla fizik değildir: süreklilikte `drho/dt = -rho*div(v)` üstel
azalır, sıfırı ancak `dt` fazla büyükse geçer. Bu yüzden EOS **toplam**
yapıldı (sonlu girdi → sonlu çıktı) ama sorun **maskelenmedi**: defter
`nonpositive_density_count` raporlar ve sıfırdan büyükse koşu geçersizdir.
"""
from __future__ import annotations

import numpy as np
import pytest

from dartrift.cpu_reference.materials import MaterialParams, tillotson_pressure

TP = MaterialParams(eos="tillotson").tillotson


def test_k21_negatif_yogunluk_sicak_enerji_sonlu() -> None:
    """DÜŞEBİLİRLİK: düzeltmeden önce bu tam olarak NaN veriyordu."""
    rho = np.array([-1.0e-9, -0.27, -27.0, -2700.0, 0.0])
    u = np.full(rho.shape, TP.u_cv * 2.0)          # SICAK kol
    P = tillotson_pressure(rho, u, TP)
    assert np.all(np.isfinite(P)), f"NaN/inf: {P}"


@pytest.mark.parametrize("u_carp", [0.0, 0.5, 1.0, 2.0, 10.0])
def test_k21_tum_enerji_kollarinda_sonlu(u_carp: float) -> None:
    rho = np.array([-1.0e12, -1.0, 0.0, 1.0e-12, 1.0, 2700.0, 1.0e5])
    u = np.full(rho.shape, TP.u_cv * u_carp)
    assert np.all(np.isfinite(tillotson_pressure(rho, u, TP)))


def _eski_formul(rho, u, p):
    """DÜZELTME ÖNCESİ ifade, birebir — gerileme kontrolü için."""
    rho = np.asarray(rho, np.float64)
    u = np.maximum(np.asarray(u, np.float64), 0.0)
    eta = rho / p.rho0
    mu_t = eta - 1.0
    omega = u / (p.u0 * eta * eta) + 1.0
    p_cold = (p.a + p.b / omega) * rho * u + p.A * mu_t + p.B * mu_t * mu_t
    ex = np.exp(-p.beta_t * (1.0 / eta - 1.0))
    ex2 = np.exp(-p.alpha_t * (1.0 / eta - 1.0) ** 2)
    p_hot = p.a * rho * u + (p.b * rho * u / omega + p.A * mu_t * ex) * ex2
    e = eta < 1.0
    h = e & (u >= p.u_cv)
    m = e & (u > p.u_iv) & (u < p.u_cv)
    out = p_cold.copy()
    out[h] = p_hot[h]
    if np.any(m):
        w = (u[m] - p.u_iv) / (p.u_cv - p.u_iv)
        out[m] = (1.0 - w) * p_cold[m] + w * p_hot[m]
    return out


def test_gecerli_girdide_bit_ayni() -> None:
    """Düzeltme davranışı DEĞİŞTİRMEMELİ — determinizm kilitli (ADR-0004).

    Çarpım sırası bile korunmalı: `u0*(eta*eta)` ile `(u0*eta)*eta` farklı
    yuvarlar (ölçüldü: göreli ~1e-14).
    """
    rng = np.random.default_rng(20260804)
    rho = np.concatenate([rng.uniform(2700.0, 6000.0, 4000),
                          rng.uniform(1.0, 2700.0, 4000)])
    u = np.concatenate([rng.uniform(0.0, 4.0e6, 2000),
                        rng.uniform(4.7e6, 1.9e7, 3000),
                        rng.uniform(1.9e7, 1.0e8, 3000)])
    with np.errstate(all="ignore"):
        eski = _eski_formul(rho, u, TP)
    yeni = tillotson_pressure(rho, u, TP)
    assert np.array_equal(eski, yeni), (
        f"en büyük fark {np.max(np.abs(eski - yeni)):.6e}")


def test_gerileme_kontrolu_uc_kolu_da_kapsiyor() -> None:
    """BOŞLUK KONTROLÜ: yukarıdaki test gerçekten üç kolu da geziyor mu?

    Yalnızca sıkışmış kolu gezen bir örneklem, düzeltmenin dokunduğu
    genleşmiş kolları hiç sınamazdı ve test boş bir doğru olurdu.
    """
    rng = np.random.default_rng(20260804)
    rho = np.concatenate([rng.uniform(2700.0, 6000.0, 4000),
                          rng.uniform(1.0, 2700.0, 4000)])
    u = np.concatenate([rng.uniform(0.0, 4.0e6, 2000),
                        rng.uniform(4.7e6, 1.9e7, 3000),
                        rng.uniform(1.9e7, 1.0e8, 3000)])
    eta = rho / TP.rho0
    assert int(np.sum(eta >= 1.0)) > 100                      # sıkışmış
    assert int(np.sum((eta < 1.0) & (u >= TP.u_cv))) > 100    # sıcak
    assert int(np.sum((eta < 1.0) & (u > TP.u_iv)
                      & (u < TP.u_cv))) > 100                 # ara


def test_defter_negatif_yogunlugu_rapor_ediyor() -> None:
    """Sorun maskelenmiyor: defter sayıyor ve en küçük yoğunluğu yazıyor."""
    from dartrift.cpu_reference.solid_ref import SolidState, budgets_solid

    n = 8
    st = SolidState(x=np.zeros((n, 3)), v=np.zeros((n, 3)), m=np.ones(n),
                    u=np.zeros(n), h=1.0, active=np.ones(n, bool),
                    alpha=np.ones(n), rho=np.full(n, 2700.0))
    temiz = budgets_solid(st)
    assert temiz["nonpositive_density_count"] == 0
    assert temiz["state_is_finite"] is True

    st.rho[3] = -1.0                      # BOZ
    st.rho[5] = 0.0
    bozuk = budgets_solid(st)
    assert bozuk["nonpositive_density_count"] == 2, bozuk
    assert bozuk["rho_min"] == -1.0


def test_state_is_finite_gercekten_dusebiliyor() -> None:
    """BOŞLUK KONTROLÜ: bayrak sabit `True` olsa fark etmezdi.

    `state_is_finite` K21'in **ikinci** korumasıdır: EOS artık NaN üretmiyor
    ama başka bir yol üretirse defter görmeli. Bunu sınamanın tek yolu
    durumu **bozup** bayrağın düştüğünü görmektir.
    """
    from dartrift.cpu_reference.solid_ref import SolidState, budgets_solid

    n = 8
    for alan, deger in (("rho", np.nan), ("v", np.inf), ("u", np.nan)):
        st = SolidState(x=np.zeros((n, 3)), v=np.zeros((n, 3)), m=np.ones(n),
                        u=np.zeros(n), h=1.0, active=np.ones(n, bool),
                        alpha=np.ones(n), rho=np.full(n, 2700.0))
        assert budgets_solid(st)["state_is_finite"] is True, alan
        if alan == "v":
            st.v[2, 1] = deger
        else:
            getattr(st, alan)[2] = deger
        assert budgets_solid(st)["state_is_finite"] is False, alan
