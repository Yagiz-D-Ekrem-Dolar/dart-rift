"""`h` politikası ölçümü — `Ω`'nın çelişkisini çözen ölçüm (FAZ 4.3b)."""
from __future__ import annotations

import numpy as np
import pytest

from dartrift.validation.h_policy import (OMEGA_IS_UNITY_WHEN_H_FIXED,
                                          judge, neighbour_count)
from dartrift.validation.kernel_margin import SUPPORT_OVER_H


def test_komsu_sayisi_kuresel_hacim() -> None:
    """`N = (4/3)π(2h)³·ρ/m` — elle hesaplanan bir değere karşı."""
    beklenen = (4.0 / 3.0) * np.pi * (SUPPORT_OVER_H * 0.05) ** 3 * 1.0 / 1e-4
    assert neighbour_count(1.0, 0.05, 1e-4) == pytest.approx(beklenen, rel=1e-14)


def test_komsu_sayisi_yogunlukla_DOGRUSAL() -> None:
    """Sabit `h` ve `m`'de `N_komşu ∝ ρ` — çelişkinin sayısal çekirdeği.

    Şok 4 kat sıkıştırırsa komşu sayısı **4 katına** çıkar. Bu bir modelleme
    tercihi değil, sabit `h`'nin doğrudan sonucudur.
    """
    tek = neighbour_count(1.0, 0.05, 1e-4)
    dort = neighbour_count(4.0, 0.05, 1e-4)
    assert dort / tek == pytest.approx(4.0, rel=1e-14)


def test_komsu_sayisi_h_kupu_ile() -> None:
    """`N ∝ h³` — `dx` taraması bu yüzden komşu sayısını **küpsel** değiştirir."""
    oran = neighbour_count(1.0, 0.10, 1e-4) / neighbour_count(1.0, 0.05, 1e-4)
    assert oran == pytest.approx(8.0, rel=1e-14)


def test_omega_sabit_h_de_BIRIMDIR() -> None:
    """Türetim gereği: `∂h/∂ρ = 0` çarpanı `Ω`'yı **tam** 1 yapar.

    Bu bir ölçüm değil, bir **cebir**. Sabiti burada sabitliyoruz ki
    ileride biri `Ω`'yı sabit `h` yolunda hesaplamaya kalkarsa test
    kırılsın — o an ADR-0041 madde 4 de kırılmış olur.
    """
    assert OMEGA_IS_UNITY_WHEN_H_FIXED is True


def test_yargi_az_nokta_ile_BELIRSIZ() -> None:
    """İki nokta bir plato gösteremez (KAYIT-030'un dersi)."""
    s = [{"r_measured": 0.25, "N_komsu": 10.0},
         {"r_measured": 0.25, "N_komsu": 20.0}]
    assert judge(s)["karar"] == "belirsiz"


def test_yargi_kapsamayan_aralikta_BELIRSIZ() -> None:
    """Çalışma noktasını içermeyen tarama **yargı kuramaz** (KAYIT-029/033)."""
    s = [{"r_measured": 0.25, "N_komsu": 10.0 * k} for k in (1, 2, 4)]
    y = judge(s, swing={"N_komsu_p01": 5.0, "N_komsu_p99": 100.0})
    assert y["karar"] == "belirsiz"
    assert y["aralik_kapsiyor"] is False


def test_yargi_kapsayan_aralikta_KARAR_VERIR() -> None:
    """Tarama salınımı kapsıyorsa ve yayılım küçükse: sabit `h` yeterli."""
    s = [{"r_measured": 0.25, "N_komsu": 10.0 * k} for k in (1, 2, 4)]
    y = judge(s, swing={"N_komsu_p01": 12.0, "N_komsu_p99": 30.0})
    assert y["aralik_kapsiyor"] is True
    assert y["karar"] == "sabit_h_yeterli"


def test_yargi_buyuk_yayilimda_UYARLAMALI_ISTER() -> None:
    """Plato kayıyorsa karar tersine döner — ölçüt gerçekten iki yönlü."""
    s = [{"r_measured": r, "N_komsu": 10.0 * k}
         for r, k in ((0.24, 1), (0.26, 2), (0.30, 4))]
    y = judge(s, swing={"N_komsu_p01": 12.0, "N_komsu_p99": 30.0})
    assert y["karar"] == "uyarlamali_h_gerekli"
    assert y["r_yayilim"] > 0.02
