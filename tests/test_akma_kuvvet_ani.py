"""A72 — kuvvet anında akma sınırı (uzman yanıtı 2026-09-11).

Uzman ölçtü: `step_kdk_solid` ve `WarpSolid3D.step` gerilmeyi yarım
adım ilerletip kuvveti **geri döndürülmemiş** deneme gerilmesiyle
hesaplıyor; akma yüzeyine dönüş ancak adım sonunda. Saf kaymada
(`G = 2,27e10`, `γ̇ = 1/s`, `Δt = 1e-5`, `Y = 100 Pa`) kuvvetin
gördüğü eşdeğer gerilme `196 587,77 Pa` — `Y`'nin `1 966` katı.

Bu dosya üç şeyi kilitliyor:

1. Kusur **ölçülüyor** (`son` kipi): oran `≈ (√3/2) G γ̇ Δt / Y` ve
   `Δt` ile doğrusal.
2. Düzeltme **çalışıyor** (`ara` kipi): oran hiçbir değerlendirmede
   `1 + 1e-9`'u aşmıyor, `Y` tepkiye giriyor, enerji korunuyor.
3. CPU referansı ile Warp çekirdeği **aynı** şeyi yapıyor.
"""
from __future__ import annotations

import dataclasses

import numpy as np
import pytest

from dartrift.cpu_reference import sph_ref as R
from dartrift.cpu_reference.materials import (
    GravityParams,
    MaterialParams,
    PorosityParams,
    StrengthParams,
)
from dartrift.cpu_reference.solid_ref import (
    SolidState,
    budgets_solid,
    evaluate_solid,
    step_kdk_solid,
)
from dartrift.particles import warp_available

G_SH = 2.27e10
GAMMA_DOT = 1.0
DT = 1.0e-5
RHO0 = 2700.0
#: Uzmanın ölçtüğü sayı: (√3/2) G γ̇ Δt.
UZMAN_Q = 196_587.77


def _kafes(n: int = 5, s: float = 1.0) -> np.ndarray:
    g = (np.arange(n) - (n - 1) / 2.0) * s
    X, Y, Z = np.meshgrid(g, g, g, indexing="ij")
    return np.column_stack([X.ravel(), Y.ravel(), Z.ravel()])


def _mat(Y0: float) -> MaterialParams:
    # Basinca bagli surtunme KAPALI (mu_f = 0): Y(P) = Y0, uzmanin
    # kurulumu. Dogrusal EOS + sureklilik: dinlenmede P tam 0.
    return MaterialParams(
        eos="linear", c0=3000.0, rho0_linear=RHO0,
        density_method="continuity",
        strength=StrengthParams(enabled=True, Y0=Y0, mu_f=0.0, YM=1.5e9,
                                shear_G=G_SH),
        porosity=PorosityParams(enabled=False),
        gravity=GravityParams(enabled=False),
    )


def _durum(Y0: float) -> SolidState:
    x = _kafes()
    n = len(x)
    v = np.zeros_like(x)
    v[:, 0] = GAMMA_DOT * x[:, 1]          # saf kayma
    return SolidState(x=x, v=v, m=np.full(n, RHO0), u=np.zeros(n), h=1.3,
                      active=np.ones(n, bool), Y0=np.full(n, Y0),
                      rho=np.full(n, RHO0))


def _kos(Y0: float, kip: str, dt: float = DT, n_adim: int = 3):
    mat = _mat(Y0)
    num = R.RefParams(cfl=0.25, akma_kipi=kip)
    st = _durum(Y0)
    evaluate_solid(st, mat, num)
    e0 = budgets_solid(st, mat)["e_tot"]
    for _ in range(n_adim):
        step_kdk_solid(st, mat, num, dt)
    return st, mat, e0


# --- 1. kusur OLCULUYOR --------------------------------------------------

def test_son_kipte_kuvvet_akma_sinirini_1966_kat_asiyor():
    st, _, _ = _kos(100.0, "son")
    oran = st.akma_oran_max
    beklenen = UZMAN_Q / 100.0
    assert oran > 1000.0, f"asim olculmedi: {oran}"
    # uzmanin sayisi ilk adimda (S_n = 0) tam tutar; sonraki adimlarda
    # akma yuzeyindeki S_n ~Y kadar ekler -> %1 pay
    assert abs(oran - beklenen) / beklenen < 0.01, (oran, beklenen)


def test_asim_zaman_adimiyla_DOGRUSAL():
    o1 = _kos(100.0, "son", dt=DT)[0].akma_oran_max
    o2 = _kos(100.0, "son", dt=DT / 2)[0].akma_oran_max
    o4 = _kos(100.0, "son", dt=DT / 4)[0].akma_oran_max
    assert abs(o2 / o1 - 0.5) < 0.01, o2 / o1
    assert abs(o4 / o1 - 0.25) < 0.01, o4 / o1


def test_son_kipte_ilk_adim_Y_den_BAGIMSIZ():
    """Uzman: `Y = 1, 100, 1e4, 1e6` için ilk adımın hız tepkisi aynı."""
    hizlar = []
    for y in (1.0, 100.0, 1.0e4, 1.0e6):
        st, _, _ = _kos(y, "son", n_adim=1)
        hizlar.append(st.v.copy())
    for v in hizlar[1:]:
        assert np.array_equal(v, hizlar[0]), "son kipte Y ilk adima girdi"


# --- 2. duzeltme CALISIYOR -----------------------------------------------

@pytest.mark.parametrize("Y0", [1.0, 100.0, 1.0e4, 1.0e6])
def test_ara_kipte_kuvvet_HICBIR_ZAMAN_akma_sinirini_asmiyor(Y0):
    st, _, _ = _kos(Y0, "ara")
    assert st.akma_oran_max <= 1.0 + 1.0e-9, st.akma_oran_max


def test_ara_kipte_Y_tepkiye_GIRIYOR():
    v_zayif = _kos(1.0, "ara", n_adim=1)[0].v
    v_guclu = _kos(1.0e6, "ara", n_adim=1)[0].v
    fark = np.max(np.abs(v_zayif - v_guclu))
    assert fark > 0.0, "ara kipte de Y hiz tepkisine girmiyor"


def test_ara_kipte_DEVIATORIK_hiz_tepkisi_akma_orani_kadar_kuculuyor():
    """Uzman: `Y = 100 Pa`'da kütle ağırlıklı `Δv` normu `~19,5×` küçüldü.

    İlk sürüm bu testte TOPLAM `Δv`'yi ölçüyordu ve oran `3,65` çıktı
    (eşik `> 5` uydurmaydı, düştü). Sebep ölçüldü: bu kafeste tepkinin
    büyüğü BASINÇTAN geliyor ve basınç iki kipte AYNI. Kusur deviatorik
    kısımda; onu ayırmak için dayanımı KAPALI aynı koşu çıkarılır.

    Deviatorik tepki kuvvetin gördüğü gerilmeyle orantılıdır, yani
    oran `(√3/2) G γ̇ Δt / Y = 1 965,88` olmalı. Ölçülen `1 966,1`.
    Eşik bu TÜRETİLMİŞ sayının `%1`'i -- ayarlanmış değil.
    """
    def _v(kip, dayanim=True):
        mat = _mat(100.0)
        if not dayanim:
            mat = dataclasses.replace(
                mat, strength=dataclasses.replace(mat.strength, enabled=False))
        num = R.RefParams(cfl=0.25, akma_kipi=kip)
        st = _durum(100.0)
        evaluate_solid(st, mat, num)
        for _ in range(3):
            step_kdk_solid(st, mat, num, DT)
        return st.v, st.m

    v_bas, m = _v("son", dayanim=False)       # yalniz basinc tepkisi

    def _norm(d):
        return float(np.sqrt(np.sum(m[:, None] * d * d)))

    dev_son = _norm(_v("son")[0] - v_bas)
    dev_ara = _norm(_v("ara")[0] - v_bas)
    oran = dev_son / max(dev_ara, 1e-300)
    beklenen = UZMAN_Q / 100.0
    assert abs(oran - beklenen) / beklenen < 0.01, (oran, beklenen)


def test_ara_kipte_ENERJI_korunuyor():
    for kip in ("son", "ara"):
        st, mat, e0 = _kos(100.0, kip)
        e1 = budgets_solid(st, mat)["e_tot"]
        ek = 0.5 * float(np.sum(st.m * np.sum(_durum(100.0).v ** 2, axis=1)))
        assert abs(e1 - e0) / ek < 1.0e-6, (kip, (e1 - e0) / ek)


def test_ara_kipte_plastik_is_POZITIF_ve_raporlaniyor():
    st, _, _ = _kos(100.0, "ara")
    assert st.plastic_u_ara > 0.0


def test_ikinci_degerlendirme_YUVARLAMA_DUZEYINDE_idempotent():
    """Aynı durumda iki kez değerlendirme: ikinci projeksiyon etkisiz.

    İlk sürüm BİT eşitliği istiyordu ve düştü (ölçüldü): projeksiyon
    sonrası `vm` yeniden hesaplandığında yuvarlamayla `Y`'yi birkaç ulp
    aşabiliyor, ikinci çağrı `S`'yi o kadar oynatıyor. Bu fizik değil
    yuvarlama; kilitlenen şey onun yuvarlama düzeyinde KALMASI ve
    plastik işin fiilen artmaması.
    """
    mat = _mat(100.0)
    num = R.RefParams(akma_kipi="ara")
    st = _durum(100.0)
    evaluate_solid(st, mat, num)
    st.S[:] = 0.0
    st.S[:, 0, 1] = st.S[:, 1, 0] = 1.0e5        # akma disi deneme
    evaluate_solid(st, mat, num)
    s1, w1 = st.S.copy(), st.plastic_u_ara
    evaluate_solid(st, mat, num)
    assert np.max(np.abs(st.S - s1)) <= 1.0e-14 * np.max(np.abs(s1))
    assert st.plastic_u_ara - w1 <= 1.0e-12 * w1


def test_bilinmeyen_kip_REDDEDILIYOR():
    with pytest.raises(ValueError, match="akma_kipi"):
        _kos(100.0, "yarim", n_adim=1)


# --- 3. CPU referansi = Warp cekirdegi -----------------------------------

def _warp(Y0: float, kip: str, n_adim: int = 3, device: str = "cpu"):
    from dartrift.warp_core.solver_solid import WarpSolid3D

    st = _durum(Y0)
    sol = WarpSolid3D(st.x.copy(), st.v.copy(), st.m, np.zeros(st.n), 1.3,
                      _mat(Y0), R.RefParams(cfl=0.25, akma_kipi=kip),
                      Y0=np.full(st.n, Y0), device=device)
    for _ in range(n_adim):
        sol.step(DT)
    return sol


@pytest.mark.skipif(not warp_available(), reason="warp yok")
@pytest.mark.parametrize("kip", ["son", "ara"])
def test_warp_cpu_referansla_AYNI(kip):
    ref, _, _ = _kos(100.0, kip)
    s = _warp(100.0, kip).state_numpy()
    for ad, a, b in (("x", ref.x, s["x"]), ("v", ref.v, s["v"]),
                     ("u", ref.u, s["u"]), ("S", ref.S, s["S"])):
        olcek = np.max(np.abs(a)) + 1e-300
        assert np.max(np.abs(a - b)) / olcek < 1.0e-8, (kip, ad)


@pytest.mark.skipif(not warp_available(), reason="warp yok")
def test_warp_akma_tanisi_iki_kipi_AYIRIYOR():
    son = _warp(100.0, "son").akma_tanisi()
    ara = _warp(100.0, "ara").akma_tanisi()
    assert abs(son["oran_max"] - UZMAN_Q / 100.0) / (UZMAN_Q / 100.0) < 0.01
    assert son["n_asan_parcacik"] == 125, "uzman: 125/125 asiyor"
    assert ara["oran_max"] <= 1.0 + 1.0e-9
    assert ara["n_asan_parcacik"] == 0
    assert ara["plastic_cum_ara"] > 0.0
    assert son["akma_kipi"] == "son" and ara["akma_kipi"] == "ara"


@pytest.mark.skipif(not warp_available(), reason="warp yok")
def test_warp_varsayilan_kip_SON_ve_bit_ayni():
    """`akma_kipi` verilmeyen eski çağrı ile açık `son` BİT-AYNI."""
    from dartrift.warp_core.solver_solid import WarpSolid3D

    st = _durum(100.0)
    num_eski = R.RefParams(cfl=0.25)
    sol = WarpSolid3D(st.x.copy(), st.v.copy(), st.m, np.zeros(st.n), 1.3,
                      _mat(100.0), num_eski, Y0=np.full(st.n, 100.0),
                      device="cpu")
    for _ in range(3):
        sol.step(DT)
    a = sol.state_numpy()
    b = _warp(100.0, "son").state_numpy()
    for k in ("x", "v", "u", "S", "rho"):
        assert np.array_equal(a[k], b[k]), k
    assert dataclasses.fields(num_eski)  # RefParams dataclass kalmali


@pytest.mark.skipif(not warp_available(), reason="warp yok")
def test_warp_bilinmeyen_kip_REDDEDILIYOR():
    with pytest.raises(ValueError, match="akma_kipi"):
        _warp(100.0, "yarim", n_adim=0)
