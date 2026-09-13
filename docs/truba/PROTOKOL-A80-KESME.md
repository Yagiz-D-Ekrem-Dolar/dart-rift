# Protokol A80 — dayanım kesmesinin doğrulanması

**Yazıldı:** 2026-09-13, **doğrulama koşularından ÖNCE**. Kural
`scripts/a80_kesme_raporu.py`'de kilitli, sınavı
`tests/test_a80_kesme_raporu.py`.

## 1. Kusur ve düzeltme

M kaba t5 (`α_b = 1,15`, `Y₀ = 1e4`, `f = 0,45`, sahne `20260906`),
T matris (iki tohum, 0,2 s) ve N'nin bir noktası `nan`'a gitti.
`PatlamaGozlemcisi` ile yeniden üretildi (adım `14 775`): `u = 6e6 J/kg`
(`u_iv = 4,72e6`) bir parçacık `ρ 77 → 0,001 kg/m³` genleşirken
`|S| = √(2/3) Y₀`'da kaldı; `√(4G/3ρ)` ve `S/ρ` ivmesi tekilleşti, `dt → 0`.

Düzeltme (`--dayanim-kesme`, varsayılan kapalı): `u ≥ u_iv` ya da
`ρα/ρ₀ < 0,5` olan parçacıkta `S = 0` ve `dt` hesabında `G/ρ` yok. Birim
sınavda (`P` kırpılı, `ρ = 1e-3`): `dt 1,6e-8 → 1,8e-5 s`.

## 2. Doğrulama

- **V1 kararlılık:** M'nin kaba 6 θ × 2 tohum tasarımı kesmeyle
  (`K80_kaba_t*`, `truba/is_K80_kesme.slurm`). **12/12** tamam → KARARLI.
- **V2 nötrlük:** kesmesiz M kaba ile çiftler; 5 gözlenebilir
  (`d_merkez, R_krater, V_krater, β−1, M_ejekta`), ölçek L2 matris merkez
  gerçekleme sapması. `|Δ| ≤ 2σ` kesri:

| kesir | yargı |
|---|---|
| `≥ 0,90` | **NÖTR** |
| `≥ 0,70` | **KÜÇÜK ETKİ** |
| `< 0,70` | **FİZİĞİ DEĞİŞTİRİYOR** |

  25'ten az karşılaştırma → OKUNMAZ.
- **V3:** T matris kolu kesmeyle (`Tk_matris`, 0,2 s, iki tohum) tamamlanır
  ve Protokol T'nin kilitli plato kuralıyla okunur.

## 3. Karar tablosu (koşudan önce)

| V1 | V2 | karar |
|---|---|---|
| KARARLI | NÖTR | üretim `--dayanim-kesme`; kesmesiz tamamlanmış sonuçlar (L2, N, M) **geçerli kalır**; patlayan noktalar kesmeyle doldurulur |
| KARARLI | KÜÇÜK ETKİ / DEĞİŞTİRİYOR | üretim `--dayanim-kesme`; kesmesiz kampanyalar yalnız betimleyici; üretim kampanyaları kesmeyle yeniden |
| KARARSIZ | — | A80 kapanmaz; `PatlamaGozlemcisi` ile yeni tanı |

Gerekçe: kesmesiz model hem kararsız hem fiziksel olarak yanlış
(buharlaşmış madde kayma gerilmesi taşıyor); V2 yalnız eski sonuçların
ayakta kalıp kalmadığını söyler, üretim seçimini değil.
