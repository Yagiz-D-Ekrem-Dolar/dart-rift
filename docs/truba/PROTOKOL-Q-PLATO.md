# Protokol Q — β platosu anında yakınsama ve çıkarım

**Yazıldı:** 2026-09-14, **koşulardan ÖNCE**. Yeni eşik yok: M, M2 ve
P'nin kilitli kuralları aynen, yalnız veri farklı.

## 1. Neden

T (orta, kesme + taban) ve Tkt (kaba) kilitli: **`β` platosu GEÇTİ**
(`β−1`: `0,65` @ 24 ms → `0,82–0,85` @ 0,1–0,2 s; kaba `0,75 → 0,92–0,97`).
Bütün önceki çıkarım (N, P, M, M2) **24 ms**'deydi — plato değerinin
yalnız `%80`'i. Gerçek DART `β`'sı plato değeridir. Ayrıca M'nin
yakınsamaması **erken anın** özelliği olabilir: krater hâlâ büyürken
çözünürlük farkı en büyüktür.

## 2. Kampanyalar (üretim fiziği: `--dayanim-kesme --yogunluk-tabani`)

| kod | tasarım | merdiven | `t_end` | koşu |
|---|---|---|---|---:|
| **Q1 `Mt`** | M'nin 6 θ × 2 tohum | kaba/orta/ince | 0,1 s | 36 |
| **Q2 `Ntk`** | N + N2 (LHS `20260906`, `20260914`) × 2 tohum | kaba | 0,1 s | 96 |
| **Q3 `Nto`** | aynı | orta | 0,1 s | 96 |
| **Q4 `N3i`** | N3 (LHS `20260921`) × 2 tohum | ince | 24 ms | 48 |

## 3. Yargılar (kilitli kurallar, yeniden kullanılır)

- **Q1:** `scripts/m_yakinsama_raporu.py --onek Mt` — Protokol M'nin
  toleransları ve Richardson kapısı aynen. Ayrıca M2 kontrastları (t2−t0:
  `Y₀`; t3/t4−t0: `α_b`, `f`) M'deki keşif tablosuyla aynı biçimde
  **betimleyici** yazılır.
- **Q2, Q3:** PROTOKOL-P §4d (P-v4) ve §4e (P-v4b) aynen, havuz başına
  (`is_Pgen_rapor.slurm`). Zaman örnekleri (8/16 ms) aynı eğriden gelir.
- **Q4:** ince-72 havuzu (`Ni + N2i + N3i`), §4f.

## 4. Hangisi esas (kilitli)

1. **Q1 plato anında YAKINSIYOR (≥ 4/5 gözlenebilir) derse**: Bitiş 3'ün
   esas posterioru **Q3 (orta, 0,1 s)**; Q2 kaba karşılaştırma.
2. **Q1 YAKINSAMIYOR derse**: esas sonuç 24 ms'deki en yüksek
   çözünürlüklü tam havuz (ince-72) olarak kalır; plato sonuçları
   betimleyicidir; M2 kontrast dayanıklılığı (`Y₀`) yorumu belirler.
3. **KISMİ**: iki sonuç birlikte yazılır, hangisinin esas olduğu
   gözlenebilir bazında (yakınsayanlar plato, diğerleri 24 ms) belirtilir.

## 5. Bilinen sınırlar

- `M_ejekta` platosu hiçbir T koşusunda geçmedi; plato anında `M_ejekta`
  hâlâ büyüyen bir niceliktir.
- 0,1 s tek bir an; `β` platosunun `%2–4` salınımı gürültüye eklenir.
- İnce merdivende 0,1 s nokta başına `~3–4 saat` (tahmin).

## 6. Ek kampanyalar (2026-09-14, koşulardan ÖNCE)

| kod | tasarım | merdiven | `t_end` | koşu | soru |
|---|---|---|---|---:|---|
| **Q5 `Nbtk`** | N + N2 × 2 tohum, **blok sahası** (`4 m` gömülü blok) | kaba | 0,1 s | 96 | Matris sahasında çözülen eksenler blok sahasında da çözülüyor mu? |
| **Q6 `M2t`** | M2'nin 4 θ × 2 tohum | kaba/orta/ince | 0,1 s | 24 | `Y₀` kontrastı plato anında da çözünürlüğe dayanıklı mı? |

- **Q5 yargısı:** PROTOKOL-P §4d/§4e aynen. **Esas sonuç değildir**; Q §4'e
  göre seçilen esas sonucun **saha duyarlılığı** satırıdır. Aynı eksenler
  çözülüyorsa sonuç çarpma sahası türüne dayanıklı; çözülmüyorsa Bitiş 3
  sonucu "matris sahası koşullu" diye yazılır.
- **Q6 yargısı:** `m2_kontrast_raporu.py --onek M2t`, PROTOKOL-M2 kuralları
  aynen. Q §4 madde 2 (Q1 YAKINSAMIYOR) durumunda yorum Q6'ya dayanır.

## 7. Rapor denetimi (A84'ten sonra, zorunlu)

Her havuz raporu `BEKLENEN_DESEN` (desen sayısı) ve `BEKLENEN_KOSU_EN_AZ`
(npz alt sınırı) ile gönderilir. Rapor başında npz sayılır; P-v4 sonrası
okunan koşu sayısı `≥ alt sınır − 8` denetlenir. Tutmazsa iş hata koduyla
durur (`exit 4/5/6`). Değerler:

| rapor | desen | npz (ölçülen / beklenen) | alt sınır |
|---|---:|---|---:|
| ince-48 | 2 | 96 | 90 |
| kaba-72 | 4 | 145 | 136 |
| orta-72 | 4 | 144 | 136 |
| kaba-48 figür | 3 | 97 | 90 |
| orta-48 figür | 3 | 96 | 90 |
| ince-72 | 3 | 96 + 48 | 130 |
| Q2 / Q3 / Q5 | 2 | 96 | 86 |
