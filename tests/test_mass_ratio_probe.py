"""FAZ 4.1 sondasının kendi denetimi.

Bu modül **kararı besleyen** ölçümü yapıyor (KAYIT-020, KAYIT-022) ama uzun
süre testsiz kaldı. Ölçüm aracının kendisi bozulursa hiçbir sayı yorumlanamaz
— bu, YÖNTEM'in *"ölçüm aracını da kalibre et"* kuralının test hâlidir.

Kapatılan sessiz bozulma yolları:

1. **Boşluk kontrolü**: 1:1'de taban **makine sıfırı** olmalı. Olmazsa
   ölçülen her "arayüz katkısı" düzeneğin kendi artığıdır (KAYIT-019 §3b'de
   tam olarak bu oldu: kenar payı çekirdek desteğinden küçüktü ve taban
   `0,0397` görünüyordu).
2. **Geometri denetimi**: pay + arayüz + iç yarıçap dış yarıçapı aşarsa
   "derin dış" bölge **boş** kalır ve ölçüm sessizce yalnızca iç bölgeyi
   ölçer.
3. **`rho_base`**: ADR-0030'un `m = ρ·V_p` değişmezi. Gerçek yığında skaler
   `rho0` kullanmak K7'yi tekrarlardı.
4. **Ayırt etme**: sonda kütle oranına gerçekten **duyarlı** olmalı; her
   şeye sıfır diyen bir sonda da 1:1'i geçerdi.
"""
from __future__ import annotations

import numpy as np
import pytest

from dartrift.validation.mass_ratio import (build_two_zone, _masks,
                                            measure_partition_of_unity,
                                            measure_spurious_acceleration)

R_OUT, R_IN, S, HOS = 70.0, 25.0, 8.0, 1.3


def test_bosluk_kontrolu_taban_makine_sifiri() -> None:
    """1:1'de mükemmel kafes düzgün basınçta HİÇ yapay kuvvet üretmemeli."""
    z = build_two_zone(R_OUT, R_IN, S, 1.0)
    d = measure_spurious_acceleration(z, HOS)
    assert d["field_is_uniform"] is True
    assert d["a_interface_over_reference"] < 1.0e-9, d["a_interface_over_reference"]


def test_sonda_kutle_oranina_duyarli() -> None:
    """KALİBRASYON: her şeye sıfır diyen bir sonda da 1:1'i geçerdi."""
    bir = measure_spurious_acceleration(build_two_zone(R_OUT, R_IN, S, 1.0), HOS)
    sekiz = measure_spurious_acceleration(build_two_zone(R_OUT, R_IN, S, 2.0), HOS)
    assert sekiz["a_interface_over_reference"] > 0.05, sekiz
    assert sekiz["a_rms_interface"] > 1.0e6 * max(bir["a_rms_interface"], 1e-300)


def test_kenar_payi_cekirdek_destegini_kapsiyor() -> None:
    """KAYIT-019 §3b: pay `2h` (Wendland C2 desteği) + yarım aralık olmalı.

    Bu sayı küçülürse yüzey artığı tabanı kirletir — ölçülen: pay `2,5·s`
    iken taban `0,0878`, `4,0·s` iken `0,0000`.
    """
    z = build_two_zone(R_OUT, R_IN, S, 1.0)
    h = HOS * S
    mk = _masks(z, h)
    assert mk["margin"] >= 2.0 * h, (mk["margin"], 2.0 * h)


def test_yetersiz_geometri_hata_veriyor() -> None:
    """Derin dış bölge boş kalacaksa SESSİZCE ölçme, HATA ver."""
    with pytest.raises(ValueError, match="geometri yetersiz"):
        measure_spurious_acceleration(build_two_zone(45.0, 25.0, 8.0, 1.0), HOS)


def test_bolgeler_dolu() -> None:
    """Geçerli geometride her iki bölge de gerçekten parçacık içermeli."""
    d = measure_spurious_acceleration(build_two_zone(R_OUT, R_IN, S, 2.0), HOS)
    assert d["n_interface"] > 50, d["n_interface"]
    assert d["n_deep"] > 50, d["n_deep"]


def test_momentum_artigi_makine_sifiri() -> None:
    """SPH'in simetrik kuvvet biçimi antisimetrik: Σmᵢaᵢ = 0.

    Bu ölçümün değil, ÇÖZÜCÜNÜN sınavıdır — ve bozuksa yukarıdaki hiçbir
    sayı yorumlanamaz.
    """
    for lam in (1.0, 2.0, 2.52):
        d = measure_spurious_acceleration(build_two_zone(R_OUT, R_IN, S, lam), HOS)
        assert d["net_momentum_residual"] < 1.0e-12, (lam, d["net_momentum_residual"])


def test_birim_bolunmesi_kutle_orani_bir_iken_tam() -> None:
    """ADR-0030: Σ(m/ρ)W = 1. Tekdüze kütlede sapma ihmal edilebilir olmalı.

    Ölçülen (1:1, h/s = 1,3): her üç bölgede de `max_dev = 0,00381`.
    Eşik önce ölçüldü, sonra yazıldı (S1/S3'ün dersi).
    """
    pu = measure_partition_of_unity(build_two_zone(R_OUT, R_IN, S, 1.0), HOS)
    for bolge in ("interface", "deep_inner", "deep_outer"):
        assert pu[bolge]["n"] > 20, (bolge, pu[bolge])
        assert pu[bolge]["max_dev"] < 0.01, (bolge, pu[bolge])


def test_rho_base_distansiyonu_dogru_kuruyor() -> None:
    """`rho_base` ne işe yarıyor — **iki kez yanlış tahmin ettim, ölçtüm.**

    *Birinci tahminim:* "yanlış taban kullanılırsa yapay kuvvet büyür."
    **Ölçtüm: `1,29e-15` — hâlâ makine sıfırı.** Sebep: kütlelerin **tekdüze**
    bir çarpanla ölçeklenmesi FCC kafesin simetrisini bozmaz; düzgün bir
    alanda `Σ_j ∇W = 0` kalır ve kuvvet doğmaz.

    *İkinci tahminim:* "yanlış yol basıncın işaretini çevirir."
    **Ölçtüm: ters yönde.** Basınç `m`'den değil `ρ` ve `α`'dan gelir;
    `rho_base` verilmeyince `ρ = 2700·1,01`, `α = 1` ve `P = +2,6967e+08`
    olur — normal bir sıkışma. İşareti çeviren şey benim `rho_base`'i
    **distansiyonsuz** eklememdi: `ρ = 2400·1,01`, `α = 1` → `ρ_katı = 2424
    < ρ₀` → **gerilme**, `P = −2,4503e+09`. `α = ρ₀/ρ_taban` ile düzeldi.

    Gerçekte `rho_base`'in yaptığı şudur: `α = ρ₀/ρ_taban` kurar, böylece
    `ρ_katı = ρ₀` olur ve `eps` gerçek bir sıkışma verir — gerçek çözücünün
    gözenekli malzemede yaptığının aynısı (ADR-0022/0031).

    Verilmezse bozulan şey **kuvvet değil, ADR-0030'un değişmezidir**:
    `m/ρ = V_p` artık tutmaz.
    """
    z = dict(build_two_zone(R_OUT, R_IN, S, 1.0))
    v_p = S ** 3 / np.sqrt(2.0)
    z["m"] = z["m"] * (2400.0 / 2700.0)          # YIGIN yogunluguna gecir
    taban = z["m"] / v_p
    assert np.allclose(taban, 2400.0), taban[:3]

    d = measure_spurious_acceleration(z, HOS, rho_base=taban)
    assert d["P_applied"] > 0.0, d["P_applied"]                    # SIKISMA
    assert abs(d["alpha_range"][0] - 2700.0 / 2400.0) < 1.0e-12    # distansiyon
    assert d["a_interface_over_reference"] < 1.0e-9

    # ADR-0030 degismezi: rho_base VERILMEZSE m/rho = V_p BOZULUR.
    assert abs(float(np.mean(z["m"] / 2700.0)) / v_p - 1.0) > 0.10   # bozuk
    assert abs(float(np.mean(z["m"] / taban)) / v_p - 1.0) < 1.0e-12  # duzgun


def test_rho_base_sekil_denetimi() -> None:
    z = build_two_zone(R_OUT, R_IN, S, 1.0)
    with pytest.raises(ValueError, match="rho_base"):
        measure_spurious_acceleration(z, HOS, rho_base=np.ones(3))


def test_tek_populasyon_kipi() -> None:
    """`interior_mask` verildiğinde iki bölgeli maskeler devre dışı kalmalı."""
    z = build_two_zone(R_OUT, R_IN, S, 1.0)
    r = np.linalg.norm(z["x"], axis=1)
    mk = r < R_OUT - (2.0 * HOS * S + 0.5 * S)
    d = measure_spurious_acceleration(z, HOS, interior_mask=mk)
    assert d["single_population_mode"] is True
    assert d["n_interface"] == int(mk.sum())
    assert d["a_interface_over_reference"] < 1.0e-9

    with pytest.raises(ValueError, match="BOS"):
        measure_spurious_acceleration(z, HOS, interior_mask=np.zeros(len(r), bool))
