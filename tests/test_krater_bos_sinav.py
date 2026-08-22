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


# ===================================================================
# A19'un CARESI: yerdegistirme tabanli olcu
# ===================================================================

from dartrift.observables.crater_shape import (  # noqa: E402
    krater_yerdegistirme,
)

#: Mermi `+z` yonunde gidiyor -> carpma cismin `-z` tarafinda.
GELIS = np.array([0.0, 0.0, 1.0])


def _yeni(x, x0, R=82.0):
    return krater_yerdegistirme(x, x0, impact_direction=GELIS,
                                reference_radius=R)


def test_YENI_kimildamamis_DUZGUN_yuzeyde_sifir() -> None:
    x = _kure(20000, 82.0)
    k = _yeni(x, x)
    assert k.derinlik == 0.0
    assert np.isnan(k.cap), "krater yokken cap uydurulmamali"


def test_YENI_kimildamamis_PURUZLU_yuzeyde_de_SIFIR() -> None:
    """A19'un kok nedeni buydu; yeni olcu cebirsel olarak bagisik.

    Puruz `x` ve `x_reference`'ta AYNI oldugu icin farkta cikar gider.
    """
    rng = np.random.default_rng(11)
    x = _kure(20000, 82.0)
    yuzey = np.linalg.norm(x, axis=1) > 0.9 * 82.0
    x = x.copy()
    x[yuzey] *= (1.0 + rng.normal(0.0, 3.0 / 82.0, int(yuzey.sum())))[:, None]
    k = _yeni(x, x)
    assert k.derinlik == 0.0
    assert np.isnan(k.cap)


def _cukur_gelis(n, R, yari_aci_deg, taban_r, puruz=0.0, seed=5):
    """`GELIS` yonune gore `-z` kutbunda duz tabanli cukur."""
    x0 = _kure(n, R, seed=seed)
    if puruz > 0.0:
        rng = np.random.default_rng(seed + 1)
        yuz = np.linalg.norm(x0, axis=1) > 0.9 * R
        x0 = x0.copy()
        x0[yuz] *= (1.0 + rng.normal(0.0, puruz / R, int(yuz.sum())))[:, None]
    x = x0.copy()
    r0 = np.linalg.norm(x0, axis=1)
    cos = (x0 @ (-GELIS)) / np.maximum(r0, 1e-30)
    kaz = (r0 > taban_r) & (cos > np.cos(np.radians(yari_aci_deg)))
    x[kaz] *= (taban_r / r0[kaz])[:, None]
    return x, x0, int(kaz.sum())


def test_YENI_GERCEK_cukuru_goruyor() -> None:
    """`12 m` derin, `15°` çukur — eski ölçü `-0,03 m` diyordu."""
    x, x0, n_kaz = _cukur_gelis(20000, 82.0, 15.0, 70.0)
    assert n_kaz > 100
    k = _yeni(x, x0)
    assert k.derinlik > 5.0, k.derinlik
    # cap ~ 2 R sin(15 der) = 42,4 m; kutu genisligi kadar tolerans
    assert 30.0 < k.cap < 60.0, k.cap


def test_YENI_PURUZ_cukuru_bozmuyor() -> None:
    duz = _yeni(*_cukur_gelis(20000, 82.0, 15.0, 70.0)[:2])
    pur = _yeni(*_cukur_gelis(20000, 82.0, 15.0, 70.0, puruz=3.0)[:2])
    assert abs(pur.derinlik - duz.derinlik) < 0.35 * duz.derinlik


def test_YENI_daha_DERIN_cukur_daha_BUYUK_derinlik() -> None:
    sig = _yeni(*_cukur_gelis(20000, 82.0, 15.0, 76.0)[:2])
    derin = _yeni(*_cukur_gelis(20000, 82.0, 15.0, 70.0)[:2])
    assert derin.derinlik > sig.derinlik


def test_YENI_daha_GENIS_cukur_daha_BUYUK_cap() -> None:
    dar = _yeni(*_cukur_gelis(20000, 82.0, 10.0, 70.0)[:2])
    genis = _yeni(*_cukur_gelis(20000, 82.0, 25.0, 70.0)[:2])
    assert genis.cap > dar.cap


def test_YENI_COZUNURLUKTEN_bagimsiz() -> None:
    """Parçacık sayısı `4` katına çıkınca ölçü kaymamalı."""
    az = _yeni(*_cukur_gelis(20000, 82.0, 15.0, 70.0)[:2])
    cok = _yeni(*_cukur_gelis(80000, 82.0, 15.0, 70.0)[:2])
    assert abs(cok.derinlik - az.derinlik) < 0.20 * az.derinlik
    assert abs(cok.cap - az.cap) < 0.20 * az.cap


def test_YENI_bozuk_girdiyi_REDDEDIYOR() -> None:
    x = _kure(2000, 82.0)
    with pytest.raises(ValueError, match="ayni olmali"):
        krater_yerdegistirme(x, x[:100], impact_direction=GELIS,
                             reference_radius=82.0)
    with pytest.raises(ValueError, match="sifir vektor"):
        krater_yerdegistirme(x, x, impact_direction=np.zeros(3),
                             reference_radius=82.0)
    with pytest.raises(ValueError, match="pozitif"):
        krater_yerdegistirme(x, x, impact_direction=GELIS,
                             reference_radius=-1.0)
