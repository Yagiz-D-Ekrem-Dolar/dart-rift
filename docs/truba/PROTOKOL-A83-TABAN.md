# Protokol A83 — süreklilik yoğunluğu tabanının doğrulanması

**Yazıldı:** 2026-09-13, **doğrulama koşularından ÖNCE**. Rapor
`scripts/a80_kesme_raporu.py --eski-onek K80 --yeni-onek K83` (A80 ile
aynı kilitli V1/V2 kuralı).

## 1. Kusur

`--dayanim-kesme` açıkken 48 kaba N/N2 noktasının 5'i ve T matris
(`99991111`, 0,2 s) patladı. Patlayanlar: N θ#10 `(1,018 ; 1,39e6 ; 0,484)`,
N2 θ#6 `(1,025 ; 2,43e4 ; 0,465)` iki tohumda, N2 θ#18 `(1,077 ; 8,85e3 ;
0,453)` bir tohumda — hepsi yüksek `f`, neredeyse katı blok. Tanı (N2 θ#6,
adım 8 425): kesilmiş (`S = 0`), kırpılmış (`P = 0`), `α = 2,2` bir matris
parçacığının süreklilik yoğunluğu `0`'a iniyor; `divv ∝ 1/ρ` → `dt → 0`.

Düzeltme `--yogunluk-tabani`: `ρ ≥ 0,01 ρ₀/α`.

## 2. Doğrulama (kilitli)

- **V1 kararlılık:** kesme + taban ile (a) M kaba 6 θ × 2 tohum (`K83`),
  (b) patlayan üç θ × iki tohum (`Nkd`), (c) T matris `99991111` (`Tkt`).
  (a) **12/12** ve (b) **6/6** ve (c) tamam → KARARLI.
- **V2 nötrlük:** `K83` ile `K80` (yalnız kesme) çiftleri, A80 kuralı:
  `|Δ| ≤ 2σ` kesri `≥ 0,90` NÖTR · `≥ 0,70` KÜÇÜK ETKİ · `< 0,70`
  FİZİĞİ DEĞİŞTİRİYOR.

## 3. Karar tablosu

| V1 | V2 | karar |
|---|---|---|
| KARARLI | NÖTR | üretim = kesme + taban; kesmeli kampanyalar (Nk, M2, Tk) **geçerli**; patlayan noktalar tabanla doldurulur (`Nkd`, havuz deseni) |
| KARARLI | KÜÇÜK ETKİ / DEĞİŞTİRİYOR | üretim = kesme + taban; kesmeli kampanyalar yalnız betimleyici, yeniden koşulur |
| KARARSIZ | — | A83 kapanmaz; yeni tanı |
