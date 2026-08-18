"""A′ prototipinin kendi denetimi.

Prototip **kararı besleyecek** (A′ mi, C mi?), o yüzden kendisi de sınanır.
Kapatılan sessiz bozulma yolları:

1. **Boşluk kontrolü**: `λ = 1`'de tüm `h`'ler eşittir; dört şema da
   **makine sıfırı** vermelidir. Vermezse prototip bozuktur — nitekim
   grad-h tam olarak burada düştü ve kenar payının yetersiz olduğu ortaya
   çıktı (`gradh_margin_factor`).
2. **Momentum**: dört biçim de antisimetrik olmalı; `Σmᵢaᵢ = 0`. Bir şema
   momentumu korumuyorsa onun "daha az hata" vermesi anlamsızdır.
3. **Bağımsız doğrulama**: `global_h` şeması, tam çözücüyle ölçülen
   `mass_ratio` sonucuna yakın çıkmalı. İki bağımsız yol aynı sayıyı
   vermiyorsa biri bozuktur.
"""
from __future__ import annotations

import numpy as np
import pytest

from dartrift.validation.variable_h import (
    _SCHEMES,
    _two_zone,
    compare_h_schemes,
    evaluate_uniform_pressure,
    gradh_margin_factor,
)

# grad-h payi 4h oldugu icin geometri buyuk olmali: r_out >= r_in + 7s.
R_OUT, R_IN, S, HOS = 88.0, 24.0, 8.0, 1.3


@pytest.fixture(scope="module")
def taban() -> dict:
    return compare_h_schemes(lams=(1.0,), r_outer=R_OUT, r_inner=R_IN,
                             spacing=S, h_over_spacing=HOS)


def test_bosluk_kontrolu_tum_semalar_makine_sifiri(taban: dict) -> None:
    """`λ = 1`: tüm `h`'ler eşit → dört şema da tam sıfır vermeli."""
    s = taban["rows"][0]
    for sema in _SCHEMES:
        assert s[f"{sema}_over_ref"] < 1.0e-9, (sema, s[f"{sema}_over_ref"])
    assert taban["baseline_clean"] is True


def test_bolgeler_dolu(taban: dict) -> None:
    """Pay şemaya göre değişiyor; hiçbirinde bölge boşalmamalı."""
    s = taban["rows"][0]
    for sema in _SCHEMES:
        assert s[f"{sema}_n_interface"] >= 20, (sema, s[f"{sema}_n_interface"])


def test_gradh_payi_geometri_denetimini_sikilastiriyor() -> None:
    """grad-h payı `4h`; geometri denetimini **o** belirlemeli.

    İlk yazdığım test şuydu: *"grad-h'nin ölçüm bölgesi daha küçük olmalı."*
    **Ölçtüm, yanlıştı:** `440 < 440`. Arayüz bandı (`|r−r_in| < h`) her iki
    payın da **içinde** kaldığı için sayılar eşit çıkıyor — pay ayrımı
    uygulanıyor ama bu bandda görünmüyor.

    Ayrımı **davranışsal** olarak sınamak gerekiyor: `r_out=70, r_in=25`
    geometrisinde standart pay (`2h+s/2 = 24,8`) **sığar**
    (`70−24,8 = 45,2 > 35,4`) ama grad-h payı (`4h+s/2 = 45,6`) **sığmaz**
    (`70−45,6 = 24,4 < 35,4`). Hata **yalnızca** grad-h payı yüzünden gelir.
    """
    h_max = HOS * S
    assert gradh_margin_factor(HOS) * S > 2.0 * h_max + 0.5 * S

    # Standart pay SIGAR ama grad-h payi SIGMAZ -> hata beklenir.
    assert 70.0 - (2.0 * h_max + 0.5 * S) > 25.0 + h_max          # std sigar
    assert 70.0 - (gradh_margin_factor(HOS) * S) < 25.0 + h_max   # gradh sigmaz
    with pytest.raises(ValueError, match="grad-h payi"):
        compare_h_schemes(lams=(1.0,), r_outer=70.0, r_inner=25.0,
                          spacing=S, h_over_spacing=HOS)


def test_momentum_tum_semalarda_korunuyor() -> None:
    r = compare_h_schemes(lams=(1.0, 2.0), r_outer=R_OUT, r_inner=R_IN,
                          spacing=S, h_over_spacing=HOS)
    assert r["all_conserve_momentum"] is True
    for satir in r["rows"]:
        for sema in _SCHEMES:
            assert satir[f"{sema}_momentum"] < 1.0e-12, (sema, satir)


def test_h_gercekten_degisken() -> None:
    """KALİBRASYON: `λ > 1`'de `h` gerçekten iki değer almalı.

    Almazsa şemalar arasında fark olamaz ve tüm kıyas boş bir doğru olur.
    """
    z1 = _two_zone(R_OUT, R_IN, S, 1.0, HOS)
    z2 = _two_zone(R_OUT, R_IN, S, 2.0, HOS)
    assert float(np.ptp(z1["h"])) == 0.0
    assert float(np.ptp(z2["h"])) > 0.4 * float(np.max(z2["h"]))


def test_kademeli_gecis_h_yi_yumusatiyor() -> None:
    ani = _two_zone(R_OUT, R_IN, S, 2.0, HOS, ramp_width=0.0)
    kad = _two_zone(R_OUT, R_IN, S, 2.0, HOS, ramp_width=32.0)
    # Ayni uc degerler, ama ARADA degerler olmali.
    assert np.isclose(ani["h"].min(), kad["h"].min())
    assert np.isclose(ani["h"].max(), kad["h"].max())
    ara = (kad["h"] > kad["h"].min() * 1.05) & (kad["h"] < kad["h"].max() * 0.95)
    assert int(ara.sum()) > 50, int(ara.sum())
    assert int(((ani["h"] > ani["h"].min() * 1.05)
                & (ani["h"] < ani["h"].max() * 0.95)).sum()) == 0


def test_gradh_pay_carpani() -> None:
    assert gradh_margin_factor(1.3) == pytest.approx(4.0 * 1.3 + 0.5)
    assert gradh_margin_factor(2.0) > gradh_margin_factor(1.3)


def test_bilinmeyen_sema_reddediliyor() -> None:
    z = _two_zone(R_OUT, R_IN, S, 1.0, HOS)
    with pytest.raises(ValueError, match="bilinmeyen şema"):
        evaluate_uniform_pressure(z["x"], z["m"], z["h"], "yok_boyle_sema")


def test_boyut_uyusmazligi_reddediliyor() -> None:
    z = _two_zone(R_OUT, R_IN, S, 1.0, HOS)
    with pytest.raises(ValueError, match="boyutlar uyuşmuyor"):
        evaluate_uniform_pressure(z["x"], z["m"], z["h"][:-1], "global_h")


def test_yetersiz_geometri_hata_veriyor() -> None:
    """grad-h payı sığmıyorsa SESSİZCE ölçme, HATA ver."""
    with pytest.raises(ValueError, match="geometri yetersiz"):
        compare_h_schemes(lams=(1.0,), r_outer=70.0, r_inner=25.0,
                          spacing=S, h_over_spacing=HOS)
