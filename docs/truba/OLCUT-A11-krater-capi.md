# A11 — `krater_capi` `λ₂ = 4`'te canlanıyor mu? (2026-08-21, koşudan **önce**)

## Nereye geldik

`krater_capi` **ölü**: `40` kaydedilmiş durumun hepsinde `6,69 m`,
sıfır yayılım. Kök neden ölçülmüştü — **nicemleme**:

| `λ₂` | çalışan `n_bins` | kutu genişliği | çapta belirsizlik |
|---|---|---|---|
| **2** (üretim) | yalnızca `8` | `1,5°` | **`±4,3 m`** |
| 4 | `16` açılıyor | `0,75°` | `±2,1 m` |

Parametrelerin çapta yarattığı oynama derinliğin `%20,7` yayılımından
**`~1,4 m`** diye kestirilmişti — yani `λ₂ = 2`'de nicemlemenin
**altında** kalıyor ve kenar hiç kutu değiştirmiyor.

Bu ölçüm **bugüne kadar koşulmadı**; `λ₂` ensemble betiğinde sabitti.

## Neden şimdi

ADR-0047 kabul edilirse (`β` gözlenebilir olmaktan çıkar) çıkarım
**tek** gözlenebilire iner: `krater_derinlik`. Çap canlanırsa ikinci
gözlenebilir geri gelir ve S3 çok daha savunulabilir olur.

## Koşu

Kol **D**: `40` nokta, `DART_UZAYI_S3`, `t_end = 0,2 s`,
`--lam2 4 --n-bins 16`. Gerisi üretimle aynı (`λ₁ = 19`, `r₁ = 3`,
`r₂ = 25`, `spacing = 7`, tohum aynı).

Taban (üretim ensemble'ı, `λ₂ = 2`, `n_bins = 8`):

| | |
|---|---|
| çap | `6,69 m`, **40/40 aynı** |
| benzersiz değer | **`1`** |
| derinlik yayılımı | `%20,7` |

## Ölçüt — **veriye bakılmadan**

### 0. Koruyucu — karşılaştırma geçerli mi

- Düşen koşu `0` olmalı (üretimde `0/40`).
- Derinliğin bağıl yayılımı `%10` ile `%40` arasında kalmalı. Dışına
  çıkarsa `λ₂` değişikliği derinliği de kaydırmıştır ve iki ensemble
  **karşılaştırılamaz**; o zaman çap yargısı okunmaz.

### 1. Birincil — çap **canlı mı**

- benzersiz çap değeri **`>= 5`** ve yayılım **`>= 2,1 m`**
  (`n_bins = 16` nicemlemesi) -> çap **CANLI**; A11 çözülür ve
  çıkarım ikinci gözlenebiliri kazanır.
- benzersiz **`<= 2`** ya da yayılım **`< 2,1 m`** -> çap hâlâ
  nicemlemenin altında; `λ₂ = 4` **yetmiyor** ve gereken çözünürlük
  daha yüksek (ya da çıkarıcı değişmeli).
- arası -> kısmi; `n_bins = 12` ile ara nokta gerekir.

### 2. Bu koşunun karar **veremeyeceği** şey

Bu ensemble üretim çözünürlüğünde **değil** (`λ₂ = 4`). Çap canlansa
bile üretim ensemble'ının `λ₂ = 4`'e taşınması ayrı bir karardır:
ADR-0043 `λ₂ = 2`'yi seçmişti ve maliyet `~3,3×`.

Ayrıca `β` ve derinlik bu kolda **üretim değerleri değildir**;
buradan `β` hakkında sonuç çıkarılmaz.
