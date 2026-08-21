"""**Boş sınav ve dolu sınav**: krater çıkarıcısı ne ölçüyor?

`2026-08-21`'de iki yönlü ölçüldü ve ikisi de kötü çıktı:

| sınav | olması gereken | **ölçülen** |
|---|---|---|
| çarpmamış, pürüzlü yüzey (`x == x_ref`) | `0` | **`0,26 m`** |
| gerçek `12 m` çukur, `508` kazılmış parçacık | `~12 m` | **`-0,03 m`** |
| ensemble yolunda çarpmamış sahne (40 nokta) | `0` | **`7,9 – 12,2 m`** |

Yani çıkarıcı **yokken var, varken yok** diyor. Raporlanan
derinliğin `%67,7`'si çarpmayla ilgisi olmayan tabandı; taban
çıkarılınca kalan sinyalin vekil kalitesi **negatif** (`q2 = -0,33`).

Bu, `krater_derinlik`'i doğrudan etkiliyor — `G4-C`'de `q2 = 0,907`
ile **en güçlü** gözlenebilirdi ve çıkarım ona dayanıyor.

> Bir gözlenebilirin parametrelerle güzel korele olması, ölçmek
> istediğin şeyi ölçtüğü anlamına gelmiyor. Taban da parametrelere
> bağlıysa korelasyon **tabandan** gelir.

Kusurlu testler `xfail(strict=True)`: düzeltildiği gün **düşerler**
ve rapor güncellenmek zorunda kalır. Rapor: `A19`.
"""
from __future__ import annotations

import numpy as np
import pytest

from dartrift.observables.crater_shape import crater_profile

#: Sentetik sahne icin genisletilmis kutulama. Uretim ayari
#: (`outer_angle_deg = 12`, `n_bins = 8`) eksen kutusuna `>= 5`
#: parcacik ister; bu testte o esigi karsilamak icin ~107 bin parcacik
#: gerekirdi. Sinanan sey KUTULAMA DEGIL, cikaricinin degismezleri.
AYAR = {"outer_angle_deg": 30.0, "n_bins": 4, "kutulama": "eksen",
        "yuzdelik": 95.0, "ejekta_yaricap_carpani": 1.05}
EKSEN = np.array([0.0, 0.0, -1.0])


def _kure(n: int, R: float, seed: int = 5) -> np.ndarray:
    """Düzgün dolu küre — Fibonacci yön + `r ~ u^(1/3)`."""
    rng = np.random.default_rng(seed)
    r = R * rng.random(n) ** (1.0 / 3.0)
    i = np.arange(n) + 0.5
    phi = np.arccos(1.0 - 2.0 * i / n)
    tht = np.pi * (1.0 + 5.0 ** 0.5) * i
    return r[:, None] * np.stack([np.cos(tht) * np.sin(phi),
                                  np.sin(tht) * np.sin(phi),
                                  np.cos(phi)], axis=1)


def _cukur(n: int, R: float, yari_aci_deg: float, derin: float):
    """Eksende düz tabanlı çukur açılmış küre; `(son, referans, n_kazilan)`."""
    x0 = _kure(n, R)
    x = x0.copy()
    r0 = np.linalg.norm(x0, axis=1)
    cos = (x0 @ EKSEN) / np.maximum(r0, 1e-30)
    kaz = (r0 > R - derin) & (cos > np.cos(np.radians(yari_aci_deg)))
    x[kaz] *= ((R - derin) / r0[kaz])[:, None]
    return x, x0, int(kaz.sum())


def _derinlik(x, x0, R=82.0) -> float:
    return float(crater_profile(x, center=np.zeros(3),
                                impact_direction=EKSEN, reference_radius=R,
                                x_reference=x0, **AYAR).depth)


def test_DUZGUN_yuzeyde_yer_degistirme_yoksa_derinlik_de_YOK() -> None:
    """Çıkarıcının tuttuğu tek değişmez — burası **geçiyor**."""
    x = _kure(12000, 82.0)
    assert _derinlik(x, x) == pytest.approx(0.0, abs=1e-9)


@pytest.mark.xfail(strict=True, reason="A19: puruzlu yuzey CARPMA OLMADAN "
                                       "derinlik uretiyor (olculen 0,26 m)")
def test_PURUZLU_yuzeyde_de_derinlik_YOK() -> None:
    """Moloz yığını yüzeyi pürüzlüdür; bu tek başına krater **değildir**.

    Ensemble yolunda bu taban `10,85 m`'ye kadar çıkıyor ve raporlanan
    derinliğin `%67,7`'sini oluşturuyor.
    """
    rng = np.random.default_rng(11)
    x = _kure(12000, 82.0)
    yuzey = np.linalg.norm(x, axis=1) > 0.9 * 82.0
    x = x.copy()
    x[yuzey] *= (1.0 + rng.normal(0.0, 3.0 / 82.0, int(yuzey.sum())))[:, None]
    assert _derinlik(x, x) == pytest.approx(0.0, abs=1e-3)


@pytest.mark.xfail(strict=True, reason="A19: GERCEK 12 m cukur olculmuyor "
                                       "(olculen -0,03 m, cap 0)")
def test_GERCEK_cukur_OLCULUYOR() -> None:
    """`12 m` derin, `15°` yarı-açılı çukur, `508` kazılmış parçacık.

    Çıkarıcı bunu görmüyor. Boşluk kontrolü olarak yazıldı ve
    **kusuru ortaya çıkardı**: yokken var diyen çıkarıcı, varken de
    yok diyor.
    """
    x, x0, n_kaz = _cukur(80000, 82.0, 15.0, 12.0)
    assert n_kaz > 300, n_kaz          # fikstur yeterince cozunmus mu
    assert _derinlik(x, x0) > 6.0


def test_fikstur_GERCEKTEN_cukur_aciyor() -> None:
    """Fikstür sınavı: yukarıdaki `xfail` benim hatam olmasın.

    Çukur **fiziksel olarak** oradaysa doğrudan ölçülebilir olmalı.
    """
    x, x0, n_kaz = _cukur(80000, 82.0, 15.0, 12.0)
    r, r0 = np.linalg.norm(x, axis=1), np.linalg.norm(x0, axis=1)
    iceri = (r - r0)
    assert n_kaz > 300
    assert iceri.min() < -11.0, iceri.min()      # en az 11 m iceri cekilmis
    assert np.median(iceri[iceri < -1e-9]) < -3.0
