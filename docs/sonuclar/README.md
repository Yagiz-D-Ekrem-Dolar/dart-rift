# Üretim havuzu — sonuçlar

> **96/96 nokta · kayıp koşu yok · kod `d96c4ee` · tohum `20260906`**
> TRUBA/H100, `kolyoz-cuda`, iş `1592569`, 2026-10-06 → 2026-10-15.

Bu klasör üretim havuzunun **ham ve özet** sonuçlarını taşır. Hiçbir sayı
elle yazılmadı: tablolar [`havuz_96.csv`](havuz_96.csv)'den, tasarım
koordinatları `lhs_design(DART_UZAYI_S4, 96, root_seed=20260906)`'dan üretildi.

---

## 1. Havuzun durumu

| | |
|---|---|
| tamamlanan nokta | **96 / 96** |
| kayıp koşu | **0** — Kapı 1 ölçütü %20, ölçülen **%0,00** |
| kod sürümü | `d96c4ee6f29cd76eb327d360bba34334d0a20837` (tek) |
| tasarım tohumu | `20260906` (tek) |
| merdiven | kaba: 48:5,6 → 3:0,35 m, N ≈ 17 000 |
| `t_end` | 600 s, yerçekimi açık, `mu_f = 0,6` |

## 2. Gözlenebilirler

| gözlenebilir | n | nan | min | medyan | maks |
|---|---:|---:|---:|---:|---:|
| `β` | 96 | 0 | 1.5310 | 2.7187 | 5.0402 |
| ejekta kütle kesri | 96 | 0 | 0.0000 | 0.0009 | 0.0091 |
| krater derinliği (m) | 66 | **30** | -8.1916 | -2.9679 | 4.6738 |

**Gözlem aralığın içinde mi.** DART'ın ölçülen `β`'sı **3,5418** ve havuz
`[1,5310 ; 5,0402]`'yi kapsıyor — çıkarım bir *iç değerleme*, dışdeğerleme
değil. Ejekta kütlesi için gözlem `1,6e7 kg / 4,2980e9 kg = 0,0037`; havuzun
medyanı `0,0009`, maksimumu `0,0091` — aralığın **içinde ama üst çeyrekte**.

**Krater okunmaz.** 96 noktanın **30**'unda `nan`, kalanların medyanı
**negatif**. Negatif krater derinliği fiziksel değil; operatör bu `t_end`'de
anlamlı bir yüzey bulamıyor. ADR-0055 bu gözlenebiliri *isteğe bağlı* ilan
ettiği için kayıt düşmez, ama pratikte bu eksen **kullanılamaz**.

## 3. Hangi gözlenebilir hangi ekseni görüyor

Spearman sıra korelasyonu, **96 noktanın tamamında** ölçüldü:

| gözlenebilir | n | `α_b` | `log Y₀` | `f` |
|---|---:|---:|---:|---:|
| **`β`** | 96 | -0.019 | -0.986 | +0.026 |
| ejekta kütle kesri | 96 | -0.019 | -0.972 | -0.036 |
| krater derinliği | 66 | +0.137 | -0.470 | +0.200 |

**Tam havuzun getirdiği yeni bilgi — ve iyi değil.** Ejekta kütle kesri de
`log Y₀` ile neredeyse tam tekdüze (`−0,972`), diğer iki eksenle ≈ 0. Yani
`β` ile **aynı yönü** taşıyor; bağımsız bir kısıt değil, ikinci bir
ölçümü. PROTOKOL-UP'ın üç açık gözlenebilir grubundan ikisi
(`periyot_degisimi` ve `ejekta_kutlesi`) böylece **tek bir yöne**
çöküyor. İkinci bir yön kalmışsa yalnız üçüncü grupta —
`ejekta_hiz_dagilimi` — olabilir ve o grup henüz **hiç ölçülmedi**.

`ω` (kazanılan spin) bu tabloda yok: havuz `jsonl`'inde değil, durum
dosyalarından PROTOKOL-SI §5 yöntemiyle çıkarılıyor. 88 noktada ölçülen
değerleri `../rapor2204/veri/eksen_duyarliligi.dat` taşıyor:
`ρ(ω,f) = +0,459`, `ρ(ω,α_b) = −0,316`, `ρ(ω,log Y₀) = −0,111`, `r(β,ω) = +0,131`.

## 4. Bu tablodan çıkan tek cümle

> `β` pratikte **tek bir koordinat** taşıyor. `log Y₀` ile neredeyse tam
> tekdüze; diğer iki eksenle korelasyonu sıfıra yakın. Tek skaler gözlem,
> üç boyutlu iç yapı uzayında **bir yön** görüyor.

## 5. Henüz ölçülmeyen — ve neden

Bu klasörde **yok**, çünkü kilitli ölçüm henüz koşmadı:

| | durum |
|---|---|
| öğrenilen yön sayısı `n_yön` | **ölçülmedi** — PROTOKOL-UP §3, Fisher eşiği 36 |
| gözlenebilir seçimi (3 grup) | **ölçülmedi** — hız dağılımı grubunun katkısı açık |
| posterior | **koşmadı** |
| Hera ön kaydı | **üretilmedi** |

`FISHER_ESIGI`'ni `n_yön` büyüsün diye indirmek protokolde **yasak**;
indirilirse yargı geçersiz sayılır. Bu klasör yargıdan **önceki** durumu
dondurur.
