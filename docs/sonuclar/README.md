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

## 5. Kaç yön öğreniliyor — **ölçüldü: bir**

PROTOKOL-UP §3/§4, 2026-10-16'da tam havuzda koşuldu
([`UP_secim_96.json`](UP_secim_96.json), gerekçe
[KAYIT-079](../defter/KAYIT-079_2026-10-16_UP-gozlemli-secimi-ve-n-yon.md)):

> **1 YÖN ÖĞRENİLİYOR (3 parametre için YETMİYOR)**
> Yan yargı: **YÖN SAYISI NOKTAYA VE KOVARYANSA BAĞLI** → §4 gereği en
> küçük `n_yön` alındı.

Kapı A ve B'den geçen aday tam üç tane ve her biri ayrı grupta
(`beta` · `M_kacan` · `e_hiz`), yani seçimde tercih yoktu. Sebep σ'dan
bağımsız: üç gradyan **neredeyse paralel** — `β` ile `e_hız` arası açı
merkezde `4,64°`, bir köşede `0,62°`.

σ(`e_hız`) bin kat küçültülse ikinci öz değer yalnız `2,35 → 4,17`
oluyor; eşik **36**. Öz değer σ ile doyuyor, çünkü σ bir satırın
*ağırlığını* artırır, *yönünü* döndürmez.

Kafeste (3 ρ × 5 θ) ikinci öz değer `1,67 – 140,53` aralığında, yani
eşiğin iki yanında; kararsız olduğu için kural en küçüğü aldırıyor.
`FISHER_ESIGI` **değiştirilmedi** — indirmek protokolde yasak ve
indirilirse yargı geçersiz sayılır.

## 6. Hâlâ ölçülmeyen

| | durum |
|---|---|
| önsel duyarlılığı (UP §5) | **koşmadı** — sıfır GPU |
| tarih eşleme (UP §6) | **koşmadı** — sıfır GPU |
| üretim posterioru | **koşmadı**; başlığı `n_yön` parametreli olacak |
| Hera ön kaydı | **üretilmedi** |

`n_yön = 1` olduğu için posterior yalnız o tek birleşim için
yayımlanacak; `α_b` ve `f` için **sayı verilmeyecek**, "önselden ayırt
edilemez" yazılacak.
