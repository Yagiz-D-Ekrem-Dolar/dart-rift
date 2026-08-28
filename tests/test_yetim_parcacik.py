"""Yetim parçacık tanısı — komşu sayımı ve donmuş enerji.

Bulgu (`2026-08-21`, rapor A21): `λ₁ = 38` koşusunda `40` parçacığın
`14 m` içinde hiç komşusu yok ve bunlar gelen enerjinin **`%17,7`**'sini
taşıyor. Komşusuz bir SPH parçacığının `P dV`'si olmadığı için o iç
enerji **işe dönüşemez**.

Tanı aracı yanlış sayarsa bulgu da yanlış olur; komşu sayımı burada
elle hesaplanabilir düzeneklerle kilitleniyor.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from yetim_parcacik import KE_GELEN, komsu_say, yetim_tanisi  # noqa: E402


def test_TEK_parcacik_komsusuz() -> None:
    assert komsu_say(np.zeros((1, 3)), 1.0)[0] == 0


def test_kafeste_komsu_sayisi_ELDEN_hesapla() -> None:
    """`1` aralıklı `3x3x3` kafes; merkezin `r < 1,5` içinde `18` komşusu.

    Merkez `(1,1,1)`: mesafe `1` olan `6`, `sqrt(2)=1,414` olan `12`
    -> `18`. `sqrt(3)=1,732` olan `8` köşe **dışarıda**.
    """
    g = np.array([(i, j, k) for i in range(3) for j in range(3)
                  for k in range(3)], dtype=float)
    n = komsu_say(g, 1.5)
    merkez = int(np.argmin(np.linalg.norm(g - 1.0, axis=1)))
    assert n[merkez] == 18, n[merkez]


def test_UZAK_parcacik_YETIM_sayiliyor() -> None:
    x = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [1000.0, 0.0, 0.0]])
    n = komsu_say(x, 5.0)
    assert n.tolist() == [1, 1, 0]


def test_KUTU_SINIRINDA_komsu_kacirilmiyor() -> None:
    """Izgara kutulamasında sınırı geçen komşu düşerse sayım bozulur."""
    # yaricap 1.0 -> kutu boyu 1.0; iki nokta ayri kutularda ama yakin
    x = np.array([[0.999, 0.0, 0.0], [1.001, 0.0, 0.0]])
    assert komsu_say(x, 1.0).tolist() == [1, 1]


def test_yetim_tanisi_DONMUS_enerjiyi_dogru_topluyor() -> None:
    x = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0],
                  [500.0, 0.0, 0.0]])          # sonuncusu yetim
    m = np.array([10.0, 10.0, 2.0])
    u = np.array([100.0, 100.0, 1.0e6])
    v = np.zeros((3, 3))
    v[2, 0] = 100.0
    r = yetim_tanisi(x, m, u, v, yaricap=5.0)
    assert r["n_yetim"] == 1
    assert r["kutle_kg"] == pytest.approx(2.0)
    assert r["ic_enerji_J"] == pytest.approx(2.0e6)
    assert r["kinetik_J"] == pytest.approx(0.5 * 2.0 * 100.0 ** 2)
    assert r["ic_enerji_pay"] == pytest.approx(2.0e6 / KE_GELEN)


def test_NEGATIF_u_donmus_enerjiye_KATILMIYOR() -> None:
    """`u < 0` fizikte sıfır sayılıyor (A21); tanı da öyle saymalı."""
    x = np.array([[0.0, 0.0, 0.0], [500.0, 0.0, 0.0]])
    r = yetim_tanisi(x, np.array([1.0, 1.0]), np.array([0.0, -1.0e6]),
                     np.zeros((2, 3)), yaricap=5.0)
    assert r["ic_enerji_J"] == 0.0


def test_bozuk_girdi_REDDEDILIYOR() -> None:
    with pytest.raises(ValueError, match="pozitif"):
        komsu_say(np.zeros((3, 3)), 0.0)
    with pytest.raises(ValueError, match=r"\(N,3\)"):
        komsu_say(np.zeros((3, 2)), 1.0)
