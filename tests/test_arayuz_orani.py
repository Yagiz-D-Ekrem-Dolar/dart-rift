"""İnceltme arayüzündeki kütle basamağı — şok oradan geçebiliyor mu.

KAYIT-053: mermi kendisinden `80` kat ağır parçacığa çarpıyordu ve
şok hedefe **giremiyordu**. A24: cephe `3,41 m`'de hızı `0,0 m/s`
ile durdu; o yarıçapta ince parçacık `46,6 kg`, hemen dışındaki
`372 834 kg` — **oran `8 000`**.

Ölçülen (`2026-08-29`), üç seviyeli tek aşama:

| `λ` | en dik | aralık | yargı |
|---|---|---|---|
| `2` | `8` | `2,0×` | olağan |
| `8` | `512` | `8,0×` | tehlikeli |
| `20` | `8 000` | `20,0×` | tehlikeli |
| `40` | `64 000` | `40,0×` | tehlikeli |

**İnceltme arttıkça arayüz kötüleşiyor** — şoku doğuran şey aynı
anda onu hapsediyor.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from arayuz_orani import (  # noqa: E402
    OLAGAN_ORAN,
    TEHLIKE_ORANI,
    basamaklar,
    kademe_onerisi,
    oranlar,
)


def test_KAYAN_NOKTA_gurultusu_ayri_seviye_SAYILMIYOR() -> None:
    """`np.unique` bu depoda bir kez `40` sahte seviye saydı (A11)."""
    m = np.array([46.6, 46.6 * (1 + 1e-12), 46.6 * (1 - 1e-13), 372834.3])
    assert len(basamaklar(m)) == 2


def test_GERCEK_seviyeler_ayirt_ediliyor() -> None:
    k = basamaklar(np.array([46.6, 372834.3, 623668.2, 46.6]))
    assert len(k) == 3
    assert k[0] == pytest.approx(46.6)      # kucukten buyuge
    assert k[-1] == pytest.approx(623668.2)


def test_OLCULEN_lam20_arayuzu_yeniden_uretiliyor() -> None:
    """`46,6 -> 372 834` = `8 000`; aralıkta `20` kat."""
    r = oranlar(np.array([46.6, 372834.3, 623668.2]))
    assert r["en_dik"] == pytest.approx(8000.0, rel=1e-3)
    assert r["aralik_sicramasi"] == pytest.approx(20.0, rel=1e-3)
    assert r["yargi"] == "TEHLIKELI"


def test_OLAGAN_basamak_gecerli_sayiliyor() -> None:
    """AMR'de olağan basamak aralıkta `2`, kütlede `8`."""
    r = oranlar(np.array([1.0, 8.0, 64.0]))
    assert r["en_dik"] == pytest.approx(8.0)
    assert r["yargi"] == "OLAGAN"
    assert r["aralik_sicramasi"] == pytest.approx(2.0)


def test_DIK_ile_TEHLIKELI_ayri_esikler() -> None:
    assert oranlar(np.array([1.0, 50.0]))["yargi"] == "DIK"
    assert oranlar(np.array([1.0, 100.0]))["yargi"] == "TEHLIKELI"
    assert OLAGAN_ORAN < TEHLIKE_ORANI


def test_TEK_seviye_oran_uretmiyor() -> None:
    r = oranlar(np.array([46.6, 46.6, 46.6]))
    assert r["yargi"] == "TEK_SEVIYE"
    assert r["en_dik"] == 1.0 and len(r["oranlar"]) == 0


def test_kademe_onerisi_ELDEN_hesapla() -> None:
    """`8 000` -> `8^k >= 8 000` en küçük `k = 5` (`8^4 = 4 096`)
    -> **`4`** ara seviye."""
    assert kademe_onerisi(8000.0) == 4
    assert kademe_onerisi(64000.0) == 5       # 8^5 = 32 768 < 64 000 -> 6-1
    assert kademe_onerisi(512.0) == 2         # 8^3 = 512 -> 3-1
    assert kademe_onerisi(8.0) == 0           # zaten olagan


def test_INCELTME_ARTTIKCA_arayuz_KOTULESIYOR() -> None:
    """Kusurun özü: şoku doğuran şey aynı anda onu hapsediyor."""
    kaba = 372834.3
    dik = [oranlar(np.array([kaba / f, kaba]))["en_dik"]
           for f in (8.0, 512.0, 8000.0, 64000.0)]
    assert dik == sorted(dik)                 # monoton kotulesme
    assert dik[0] < TEHLIKE_ORANI < dik[-1]


def test_bozuk_girdi_REDDEDILIYOR() -> None:
    with pytest.raises(ValueError, match="pozitif"):
        basamaklar(np.array([1.0, 0.0]))
    with pytest.raises(ValueError, match=r"\(N,\)"):
        basamaklar(np.zeros((2, 2)) + 1.0)
    with pytest.raises(ValueError, match="bos olmayan"):
        basamaklar(np.array([]))


# ------------------------------------------- KABUK KALINLIGI (A25)

def test_kabuk_kalinligi_KOSTURULAN_merdivenin_kusurunu_yakaliyor() -> None:
    """`12:1.25 8:2.5 6:5 4.5:10 3:20` — dış üç kabuk **çok ince**.

    Bu kusur bir koşu **sırasında** fark edildi; test onu bir daha
    gözden kaçırılmaz kılıyor.
    """
    from arayuz_orani import kabuk_kalinligi
    k = kabuk_kalinligi([(12.0, 1.25), (8.0, 2.5), (6.0, 5.0),
                         (4.5, 10.0), (3.0, 20.0)], 3.5)
    yeterli = [d["yeterli"] for d in k]
    assert yeterli == [False, False, False, True, True]
    assert k[0]["kalinlik_s"] == pytest.approx(4.0 / 2.8, rel=1e-6)


def test_kabuk_kalinligi_OZ_BENZER_merdivende_SABIT_ve_yeterli() -> None:
    """`kalınlık/s = r/s` sabit — öz-benzerliğin **gerekli** olduğu yer."""
    from arayuz_orani import kabuk_kalinligi

    from dartrift.setup.refine import ozbenzer_kademeler
    k = kabuk_kalinligi(ozbenzer_kademeler(3.5, 3.0, 0.175, 24.0), 3.5)
    assert all(d["yeterli"] for d in k)
    dis = [d["kalinlik_s"] for d in k[:-1]]      # en ic kabuk r_ic = 0
    assert max(dis) - min(dis) < 1e-9
    assert dis[0] == pytest.approx(3.0 / 0.175 / 2.0, rel=1e-6)


def test_kabuk_kalinligi_EN_IC_kabuk_merkeze_kadar() -> None:
    from arayuz_orani import kabuk_kalinligi
    k = kabuk_kalinligi([(12.0, 2.5), (3.0, 20.0)], 3.5)
    assert k[-1]["r_ic"] == 0.0
    assert k[-1]["kalinlik_m"] == pytest.approx(3.0)


def test_kabuk_kalinligi_tek_kademe_REDDEDIYOR() -> None:
    from arayuz_orani import kabuk_kalinligi
    with pytest.raises(ValueError, match="en az iki kademe"):
        kabuk_kalinligi([(3.0, 20.0)], 3.5)
