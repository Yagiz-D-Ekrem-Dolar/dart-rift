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

## 6. Model gözleme ulaşıyor mu — **evet**, ve geriye %34 kalıyor

PROTOKOL-UP §6 (tarih eşleme, Vernon), düzeltilmiş girdiyle
([`UP_s5_s6.json`](UP_s5_s6.json), KAYIT-080 + düzeltmesi
[KAYIT-082](../defter/KAYIT-082_2026-10-16_kos-hatasi-ve-duzeltilmis-sonuclar.md)):

| ölçü | değer |
|---|---|
| `I_min` | **0,325** (kesme `I > 3`) |
| bağdaşır hacim | **%34,04** — 73 537 / 216 000 düğüm |
| posterior %68 hacmi | %10,27 |
| oran | **3,31** (eşik 10) |
| post68 kütlesinin bağdaşır oranı | **1,0000** (eşik 0,90) |
| **yargı** | **İKİ YÖNTEM UYUŞUYOR** |

`I_min = 0,325`: **model DART'ın gözlemine ulaşıyor.** Hiçbir `θ`
bağdaşmasaydı `I_min > 3` çıkar, ileri model reddedilirdi.

Ve iki yöntem **birbirini doğruluyor**: posteriorun %68 kütlesinin
tamamı bağdaşır bölgede, hacim oranı 3,31 ile eşiğin (10) altında.
Protokolün karşılığı: posterior yayımlanır, tarih eşleme
**doğrulayıcı ek** olur.

## 7. Sonuç veriden mi önselden mi — **veriden**, ama sınav dişsiz

| önsel | kip `log10 Y₀` |
|---|---:|
| `KILITLI` | +1,2712 |
| `DUZ_LOG` | +1,2712 |
| `KAYDIRILMIS` (×3) | +1,2712 |

`σ_onsel = 0,0000 dex` → **SONUÇ VERİDEN GELİYOR**.

**Ama bu göründüğünden zayıf bir kanıt** ve öyle yazılıyor:
`KAYDIRILMIS` önsel `Y₀ < 3 Pa`'yı kesiyor, posterior kipi ise
`18,7 Pa`. Kesilen bölge posteriorun zaten umursamadığı yer, yani
perturbasyon hiçbir şeye dokunmuyor. Kilitli yargı uygulandı; sınavın
ayırt edici gücü düşük.

Yan bulgu: **`KILITLI` ile `DUZ_LOG` aynı dağılım.** ADR-0053 kilitli
önseli `Y₀ ∈ [1e0, 1e5]` (log, 5 dekad), yani protokolün "bilgisiz uç"
dediği şeyin ta kendisi. Protokol yazılırken fark edilmemiş.

## 8. Posterior — `n_yön = 1`'in somut hâli

| eksen | büzülme | sd oranı | sınıf |
|---|---:|---:|---|
| `α_b` | 0,031 | 0,984 | **ÖNSEL BASKIN** |
| `Y₀` | **0,882** | 0,343 | **ÖĞRENİLDİ** |
| `f` | −0,305 | 1,143 | **ÖNSEL BASKIN** |

Kip: `Y₀ ≈ 18,7 Pa`, önsel kutusunun içinde (kenarda değil).
Fisher: `[499,73 · 0,82 · 0,00]`, eşik 36 → **`n_yön = 1`**.

Büzülme sınıfları Fisher yargısıyla **tutarlı**: bir eksen öğrenildi,
ikisi önselden ayırt edilemiyor.

## 9. Vekil ve bilgi bütçesi

| vekil | `q²` | ÇD-RMSE | Bachoc | kalibre %68 kapsama |
|---|---:|---:|---:|---:|
| `β` (fırlatı geleneğinde) | **0,9765** | 0,1509 | 1,367 | 0,792 |
| `ln M_ejekta` | **0,9882** | 0,1806 | 1,095 | 0,719 |

`β` belirsizliğinin kaynakları (toplam sd `0,3126`):

| kaynak | pay |
|---|---:|
| gözlem | **%48,4** |
| model hatası bütçesi | %28,3 |
| vekil (GP) | %23,3 |

Baskın kalem **gözlem** — ve onu biz iyileştiremeyiz. Daha çok tasarım
noktası vekil payını (%23,3) küçültür, toplamı çok değiştirmez.

## 10. SBC kapısı — **GEÇTİ**

PROTOKOL-HAVUZ §6, `n_sbc = 200`, tohum `20261016`, düzeltilmiş girdi
([`UP_sbc.json`](UP_sbc.json),
[KAYIT-081](../defter/KAYIT-081_2026-10-16_SBC-kapisi-gecti.md)):

| eksen | tanı | PIT ort. (se 0,0204) | KS `p` | kapsama68 |
|---|---|---:|---:|---:|
| `α_b` | **KALİBRE** | 0,4998 | 0,8680 | 0,645 |
| `Y₀` | **KALİBRE** | 0,4751 | 0,0741 | 0,650 |
| `f` | **KALİBRE** | 0,5326 | 0,2994 | 0,680 |

**GENEL: KALİBRE → posterior yayımlanabilir.** PLAN-90-GÜN'de `~%25`
yazılı "SBC düşer" riski gerçekleşmedi. En zayıf eksen `Y₀`
(`p = 0,0741`, eşik `0,05`) ve saklanmıyor.

SBC'nin kanıtladığı dar: çıkarım makinesi **kendi varsayımları
altında** kalibre. Modelin gerçeğe uyması §6'nın sorusu.

## 11. Hâlâ ölçülmeyen

| | durum |
|---|---|
| ince koşu (12 nokta, σ mı yanlılık mı) | **koşuyor** — iş `1601448`, 4 GPU, ADR-0059 |
| Hera spin ön kaydı | **üretilmedi** — [PROTOKOL-HS](../truba/PROTOKOL-HS-HERA-SPIN.md) kilitli |
| Hera krater ön kaydı | **üretilmedi** — [PROTOKOL-HT](../truba/PROTOKOL-HT-HERA-TAHMIN.md) |
| `μ_f` sürtünme duyarlılığı | **koşmadı** — ~10 GPU-saat |

## 12. Bugünkü hâliyle savunulabilir cümle

> DART'ın `β`'sı `(α_b, Y₀, f)` uzayında **bir** yön kısıtlıyor
> (`n_yön = 1`): `Y₀` öğreniliyor (büzülme 0,882, kip ≈ 18,7 Pa),
> `α_b` ve `f` önselden ayırt edilemiyor. Ölçülmüş model hatası
> bütçesiyle yapılan elemede önsel hacminin **%34'ü** bağdaşır kalıyor
> ve model gözleme **ulaşıyor** (`I_min = 0,325`). Posterior ile eleme
> **birbirini doğruluyor** (oran 3,31 < 10) ve çıkarım makinesi SBC'de
> kalibre çıkıyor. Sonuç önsele duyarsız görünüyor, ama o sınavın
> ayırt edici gücü düşüktür ve öyle raporlanıyor.

## 13. Bu klasörün dışında duran uyarı

**`β` gelenek düzeltmesi özgün bir katkı DEĞİL.** 2026-10-16 literatür
kontrolü: DART ekibi `β_n`, `β_p` ve Cheng'in fırlatı doğrultusu
`β`'sını açıkça tanımlıyor. ADR-0060 bizim kendi hatamızı yakaladı;
sunumda keşif olarak geçmeyecek.
