"""E3 düzeneğinin başlangıç koşulu doğru mu? (GPU gerekmez)

Koşunun kendisi GPU ister ama **kurulum** CPU'da tam olarak sınanabilir —
ve asıl sessiz hatalar oradadır: üç kol aynı fiziksel problemi çözmüyorsa
ölçülen fark arayüzden değil, farklı başlangıç koşulundan gelir. ADR-0011'in
tam olarak yakaladığı hata buydu.
"""
from __future__ import annotations

import numpy as np
import pytest

from dartrift.validation.sedov import H_OVER_DX, build_sedov_ic
from dartrift.validation.shock_interface import build_two_zone_sedov_ic

N_KABA, LAM, R_IN = 16, 2, 0.15
H = H_OVER_DX / N_KABA


def _kur(n: int, lam: int):
    return build_two_zone_sedov_ic(n, lam, R_IN, H)


def test_lam1_build_sedov_ic_ile_ayni_kafes() -> None:
    """`lam=1` tek popülasyondur ve mevcut üreteçle **birebir** aynı olmalı.

    Aynı değilse iki kol farklı kafeslerde koşar ve tüm kıyas anlamsızdır.
    """
    a = _kur(N_KABA, 1)
    b = build_sedov_ic(N_KABA)
    assert np.array_equal(a["x"], b["x"])
    assert np.allclose(a["m"], b["m"], rtol=0, atol=0)
    assert np.allclose(a["u"], b["u"])


def test_kutle_yerel_hucre_hacminden_geliyor() -> None:
    """ADR-0030: `m = ρ₀·dx³` — **yerel**."""
    d = _kur(N_KABA, LAM)
    dx_k = 1.0 / N_KABA
    dx_i = dx_k / LAM
    benzersiz = np.unique(np.round(d["m"], 15))
    assert len(benzersiz) == 2, benzersiz
    assert np.isclose(benzersiz.max(), dx_k ** 3)
    assert np.isclose(benzersiz.min(), dx_i ** 3)
    assert np.isclose(benzersiz.max() / benzersiz.min(), LAM ** 3)


def test_tek_populasyonda_toplam_kutle_tam() -> None:
    """Küp hacmi 1, `ρ₀ = 1` → toplam kütle **tam** 1."""
    for n, lam in ((N_KABA, 1), (N_KABA * LAM, 1)):
        assert _kur(n, lam)["total_mass"] == pytest.approx(1.0, abs=1e-12)


def test_iki_bolgeli_kutle_sapmasi_kucuk_ve_n_ile_azaliyor() -> None:
    """Küre sınırı iki kafesle döşenemez; sapma **ölçülür ve azalmalı**.

    Ölçülen: n=16 → %0,0977, n=32 → %0,0732, n=64 → %0,0134.
    Sedov'da `r ~ (E/ρ)^{1/5}` olduğu için yarıçapa etkisi beşte biridir.
    """
    sapmalar = []
    for n in (16, 32, 64):
        a = _kur(n, 1)["total_mass"]
        b = build_two_zone_sedov_ic(n, LAM, R_IN, H_OVER_DX / n)["total_mass"]
        sapmalar.append(abs(b - a) / a)
    assert sapmalar[0] < 2.0e-3, sapmalar
    assert sapmalar[-1] < sapmalar[0], sapmalar
    # BOSLUK KONTROLU: sapma GERCEKTEN sifirdan farkli olmali, yoksa bu test
    # olmayan bir seyi koruyor demektir.
    assert sapmalar[0] > 1.0e-5, sapmalar


def test_enjekte_enerji_uc_kolda_ayni() -> None:
    """ADR-0011: aynı fiziksel problem. Enerji **kütle ağırlıklı** dağıtılır."""
    e = [_kur(N_KABA, 1)["energy_injected"],
         _kur(N_KABA, LAM)["energy_injected"],
         _kur(N_KABA * LAM, 1)["energy_injected"]]
    assert max(e) - min(e) < 1.0e-9 * max(e), e
    assert all(x == pytest.approx(1.0) for x in e), e


def test_enjeksiyon_bolgesi_dolu() -> None:
    """BOŞLUK KONTROLÜ: enjeksiyon hiç parçacığa denk gelmiyorsa test boştur."""
    for n, lam in ((N_KABA, 1), (N_KABA, LAM), (N_KABA * LAM, 1)):
        assert _kur(n, lam)["n_injected"] >= 8


def test_ince_bolge_enjeksiyon_destegini_kapsiyor() -> None:
    """`r_inner` enjeksiyon desteğinden (`2·h_inject = 0,08`) **büyük** olmalı.

    Küçük olsaydı arayüz enjeksiyon bölgesinin **içinden** geçerdi ve ölçülen
    şey şok geçişi değil, enjeksiyonun bozulması olurdu.
    """
    from dartrift.validation.sedov import H_INJECT
    assert R_IN > 2.0 * H_INJECT


def test_gecersiz_argumanlar_reddediliyor() -> None:
    with pytest.raises(ValueError, match="lam pozitif"):
        build_two_zone_sedov_ic(N_KABA, 0, R_IN, H)
    with pytest.raises(ValueError, match="r_inner"):
        build_two_zone_sedov_ic(N_KABA, LAM, 0.7, H)
    with pytest.raises(ValueError, match="r_inner"):
        build_two_zone_sedov_ic(N_KABA, LAM, -0.1, H)


def test_bolgeler_dolu() -> None:
    d = _kur(N_KABA, LAM)
    r = np.linalg.norm(d["x"], axis=1)
    assert int((r < R_IN).sum()) > 50
    assert int((r >= R_IN).sum()) > 500
