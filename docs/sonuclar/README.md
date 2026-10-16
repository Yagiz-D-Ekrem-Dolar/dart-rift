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

## 6. Model gözleme ulaşıyor mu — **evet**, ve geriye %7,37 kalıyor

PROTOKOL-UP §6 (tarih eşleme, Vernon) 2026-10-16'da koşuldu
([`UP_s5_s6.json`](UP_s5_s6.json),
[KAYIT-080](../defter/KAYIT-080_2026-10-16_UP-onsel-duyarliligi-ve-tarih-eslemesi.md)):

| ölçü | değer |
|---|---|
| `I_min` | **0,504** (kesme `I > 3`) |
| bağdaşır hacim | **%7,37** — 15 916 / 216 000 düğüm |
| posterior %68 hacmi | %0,50 |
| oran | **14,78** (eşik 10) |
| post68 kütlesinin bağdaşır oranı | **1,0000** (eşik 0,90) |
| **yargı** | **POSTERIOR DAR** |

`I_min = 0,504` önemsiz değil: **model DART'ın gözlemine ulaşabiliyor.**
Hiçbir `θ` bağdaşmasaydı `I_min > 3` çıkar, ileri model reddedilirdi.

Çelişki yok — posteriorun %68 kütlesinin **tamamı** bağdaşır bölgenin
içinde. Ama hacmi o bölgenin 1/14,8'i: Gauss olabilirliği + köşegen
kovaryans varsayımının aşırı-güven imzası. Protokolün karşılığı:
**ana sonuç tarih eşleme bölgesidir**, posterior "olabilirlik
varsayımına koşullu" etiketiyle verilir.

## 7. Sonuç veriden mi önselden mi — **arada**

| önsel | kip `log10 Y₀` | kip `Y₀` (Pa) |
|---|---:|---:|
| `KILITLI` | +0,2542 | 1,796 |
| `DUZ_LOG` | +0,2542 | 1,796 |
| `KAYDIRILMIS` (×3) | +0,5085 | 3,225 |

`σ_onsel = 0,2542 dex` → **ÖNSEL ETKİLİ** (eşikler 0,15 / 0,50).
Posterior yayımlanır ama üç önselin tablosu **zorunlu ek**.

İki yan bulgu kayda geçti:

- **`KILITLI` ile `DUZ_LOG` aynı dağılım.** ADR-0053 kilitli önseli
  `Y₀ ∈ [1e0, 1e5]` (log, 5 dekad), yani protokolün "bilgisiz uç"
  dediği şeyin ta kendisi. Protokol yazılırken fark edilmemiş;
  düzeltilmiyor, kaydediliyor.
- **Kip önsel kenarına yapışık.** `u = (0,661 ; 0,051 ; 0,949)`:
  `Y₀` alt kenarda, `f` üst kenarda. Veri önsel kutusunun dışını
  istiyor — ADR-0053'ün `ÖNSEL GÖZLEMİ İÇERMİYOR` yargısıyla aynı yön.

## 8. Vekilin durumu

| vekil | `q²` | Bachoc çarpanı | kalibre %68 kapsama |
|---|---:|---:|---:|
| `β` (fırlatı geleneğinde) | **0,9310** | 1,2896 | 0,7083 |
| `ln M_ejekta` | **0,9882** | 1,0953 | 0,7188 |

θ-gruplu 4-kat ÇD; Bachoc ikisini de büyüttü, kapsama `0,68` hedefinin
biraz üstünde (muhafazakâr taraf). Ölçülen artık korelasyonu
`ρ = 0,2047` (ham `0,2924`, λ = 0,3).

## 9. Hâlâ ölçülmeyen

| | durum |
|---|---|
| üretim posterioru (yayımlanabilir hâli) | **koşmadı** — koştuğunda §5 ve §6'nın etiketleriyle çıkacak |
| ince koşu (12 nokta, σ mı yanlılık mı) | **koşmadı** — ~224 GPU-saat |
| Hera ön kaydı | **üretilmedi** |

## 10. Bugünkü hâliyle savunulabilir cümle

> DART'ın `β`'sı `(α_b, Y₀, f)` uzayında **bir** yön kısıtlıyor
> (`n_yön = 1`). Ölçülmüş model hatası bütçesiyle yapılan elemede önsel
> hacminin **%7,37'si** gözlemle bağdaşır kalıyor ve model gözleme
> **ulaşıyor** (`I_min = 0,504`). Gauss olabilirliğine dayanan posterior
> bu bölgeden 14,8 kat dar olduğu için ana sonuç **eleme bölgesidir**;
> posterior varsayıma koşullu bir ek olarak verilir. Sonuç önselden
> bağımsız değildir (`0,254 dex`), bu yüzden üç önselin tablosu
> sonuçla birlikte yayımlanır.
