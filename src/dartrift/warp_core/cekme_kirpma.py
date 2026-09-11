"""Çekme kırpma — **yalnızca tanı kolu**, üretim modeli değil.

## Neden var

Uzman incelemesi (2026-09-05) kazı akışının durmasının **birinci
adayı** olarak şunu koydu: *"düşük basınç evresinde matrisin çekmede
bağlı kalması."*

Ölçüm bunu destekliyor. Kodun CPU EOS'unda `u = 0`, `α = 1,7564`,
`ρ_s = 0,999 ρ_s0` verildiğinde:

| `Y₀`      | EOS basıncı |
|-----------|------------:|
| `1 Pa`    | `−15,19 MPa` |
| `10 MPa`  | `−15,19 MPa` |
| `100 MPa` | `−15,19 MPa` |

`Y₀` **yalnız deviatorik gerilmenin** sınırını değiştiriyor;
Tillotson'dan gelen **negatif hidrostatik basıncı** sınırlamıyor.
Yani *"1 Pa'lık matris"* hâlâ `−15 MPa` çekme taşıyabiliyor —
sağlam kayanın çekme dalı granüler matrise uygulanıyor. Bu,
`Y₀`'ın sekiz mertebede etkisiz kalmasını da açıklıyor
(rapor A17/A45).

## Ne yapar

EOS'tan **hemen sonra**, maskeli parçacıklarda `P < 0` ise `P = 0`.
Kırpılan `P`, kuvvet teriminde (`t = (S − P I)/ρ²`) ve enerji
işinde (`du`) **aynı** değer olarak kullanılır — uzmanın şartı:
*"Kuvvet ve enerji işinde aynı etkin basıncı kullanın; AV, basma
basıncı, kayma dayanımı ve kompaksiyon değişmesin."*

## Ne YAPMAZ

- Üretime önerilen bir basınç kırpması **değildir**.
- Granüler malzemenin basınca bağlı sürtünmesini **modellemez**.
- Yapay gerilme (`ast_*`, ADR-0014) ile aynı şey **değildir**: o
  kümelenmeyi önlemek için çift kuvvetine ek terim koyar, bu ise
  `P`'nin kendisini kırpar.

Amacı tek: **hangi kuvvetin kazıyı durdurduğunu ayırmak.**
"""

from __future__ import annotations

import warp as wp

F = wp.float64


@wp.kernel
def cekme_kirp(
    maske: wp.array(dtype=wp.uint8),
    P: wp.array(dtype=F),
):
    """Maskeli parçacıklarda negatif basıncı sıfıra kırp."""
    i = wp.tid()
    if maske[i] != wp.uint8(0):
        if P[i] < F(0.0):
            P[i] = F(0.0)


@wp.kernel
def cekme_sinirla(
    maske: wp.array(dtype=wp.uint8),
    T: wp.array(dtype=F),
    P: wp.array(dtype=F),
):
    """Granüler matris dalı: `P_eff = max(P, −T_m)` (uzman Soru 1).

    `T_m` parçacık başına ÇEKME DAYANIMI [Pa] (`≥ 0`). Uzman: *"Matrisin
    çekme sınırı T_m ile blokların çekme/kırılma davranışı ayrı olmalı.
    P_eff = max(P, −T_m) biçimindeki sınır, seçilen granüler kurucu
    modelin parçası olabilir."* `T_m = 0` durumu için eski `cekme_kirp`
    kullanılır (bit-aynı; işaretli sıfır farkı bile yok).
    """
    i = wp.tid()
    if maske[i] != wp.uint8(0):
        t = T[i]
        if P[i] < -t:
            P[i] = -t
