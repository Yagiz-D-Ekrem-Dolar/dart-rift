# ADR-0054 — **C1:** gözlenen `β` olarak hangi sayı kilitlenecek

**Durum:** **KABUL EDİLDİ** (2026-10-05) · **Karar:** kullanıcı kararı Claude'a devretti (*"kararları sen ver ve düzgün ver"*, 2026-10-05); gerekçe ve geri alma koşulu KAYIT-075'te · **C1'in cevabı** · **Tarih:** 2026-10-04
**Öncül:** PROTOKOL-U §1 (kilitli `3,12 ± 0,34`),
`observables/period_interface.dart_beta_budget`,
`observables/dart_gozlemleri.cheng_beta`, KAYIT-070 §3 (**A108** kütle
tutarlılığı), KAYIT-072 (DY2), [ADR-0053](ADR-0053-y0-onseli-ve-tanimlayici-gozlemli.md)
**Kod:** ikisi de **zaten var**; eksik olan karar.

---

## 1. Bağlam — projede gözlenen `β` için **iki** ayrı yol var

| yol | nasıl | `M = 4,30e9 kg` için |
|---|---|---|
| **(a)** `period_interface.dart_beta_budget` | **bizim** türetmemiz: ölçülen `ΔT = −33,0 ± 1,0 dk`, **dairesel iki cisim** yaklaşımı | `β = 3,2225`, `ΔT` bandı `[3,125 ; 3,320]` |
| **(b)** `dart_gozlemleri.cheng_beta` | **yayınlanan** bağıntı: `β = 3,61 · ρ/2400 − 0,03` (tam yörünge çözümü) | `β = 3,5434` `(+0,188 / −0,247)` |

Yayınlanan künye **birincil kaynaktan teyit edildi** (Cheng ve diğ. 2023,
*Nature* 616, 457; arXiv:2303.03464 özeti):
**`β = 3,61 (+0,19 / −0,25)` (1σ)**, Dimorphos ile Didymos'un
**eşit yoğunlukta (`2400 kg/m³`)** olduğu varsayımıyla;
`ρ ∈ [1500, 3300] kg/m³` için `β ∈ [2,2 ; 4,9]`;
yörünge hızı azalması `Δv = 2,70 ± 0,10 mm/s`.

İki yol arasındaki `%10,5` fark bir hesap hatası değil: `period_interface`
kendi gövdesinde bunu yazıyor ve kaynağını **girdi varsayımları** (kütle ve
dairesel yörünge) olarak gösteriyor.

## 2. Asıl sorun: kilitli `3,12` **artık var olmayan bir sahneye** ait

PROTOKOL-U §1 şöyle yazıyor: *"Sahnenin kendi hedef kütlesiyle
(`≈ 4,16e9 kg`) depo arayüzü gözlenen `β ≈ 3,12 ± 0,34` veriyor."*
Doğrulandı:

| `M` | yol (a) `β` |
|---|---|
| `4,160e9` (eski **küre** sahnesi) | **`3,1172`** ← kilitli `3,12` buradan |
| `4,298e9` (**DY2**, üretim sahnesi) | `3,2210` |
| `4,300e9` (gözlemin varsayımı) | `3,2225` |

`β = Δv·M/p` olduğundan **gözlenen `β` hedef kütlesiyle doğru orantılıdır**
(bunu `GOZLEM_KUTLESI`/`KUTLE_TOLERANSI` ile A108'de kendimiz yazdık). Üretim
sahnesi A108/A111 düzeltmeleriyle `4,2980e9 kg`'a kalibre edildi. Yani:

> **Kilitli hedef `3,12`, kütlesi `%3,2` küçük olan eski bir sahneden geliyor.
> Model `β`'sı ile gözlem `β`'sı aynı kütleyle konuşmuyor.**

Bu, A108'in uyardığı hatanın **gözlem tarafındaki** yüzü: kütleyi sahnede
düzelttik, ama hedefi güncellemedik.

## 3. Karar (öneri)

**C1 = `cheng_beta(hedef_kutlesi = sahnenin kendi kütlesi)`.**

Yani gözlenen `β` sabit bir sayı olarak değil, **sahnenin kütlesinin
fonksiyonu** olarak kilitlenir. Üretim sahnesi (`M = 4,2980e9 kg`,
şekil modeli hacmi `1,81e6 m³` → `ρ = 2374,6`):

**`β_gözlem = 3,5418  (+0,188 / −0,247)`**

Dört gerekçe:

1. **Yayınlanan sayı.** Topluluğun referansı ve tam yörünge çözümünden
   geliyor; bizim dairesel iki cisim yaklaşımımız onu yenemez. Kendi
   basitleştirmemizi "gözlem" diye sunmak savunulamaz.
2. **Kendi kendine tutarlı.** Sahnenin kütlesi değişirse hedef de
   `β ∝ M` kuralıyla birlikte kayar. Bir daha "eski sahnenin hedefi"
   sorunu çıkmaz; A108'in denetimi gözlem tarafına da uygulanmış olur.
3. **Teyit düzeyi yüksek.** `cheng_beta`'nın künyesi `teyit = "tam_metin"`;
   `3,12`'nin arkasındaki `ΔT` ve dairesel yaklaşım bizim kodumuz.
4. **Sınavı ZORLAŞTIRIYOR, kolaylaştırmıyor.** Gözlem sd'si
   `0,34` → `+0,188 / −0,247`'ye **daralıyor**. Yani bu değişiklik modelin
   işini kolaylaştırmak için seçilmiş olamaz.

## 4. Sonuçları (ölçülmüş)

| | kilitli `3,12 ± 0,34` | **önerilen `3,5418 (+0,188)`** |
|---|---|---|
| `σ_gözlem` | `0,340` | **`0,188`** (daha sıkı) |
| `σ_model` (aynı dört terim) | `0,226` | `0,271` |
| payda | `0,408` | `0,330` |
| **DY2 (`β = 3,7480`) → `I`** | `1,54` | **`0,63`** |
| ima edilen `Y₀` (W2 serisi) | `644 Pa` | **`59 Pa`** |

Üç okuma:

1. **Uyum iyileşiyor:** `I` `1,5` → `0,63`. Model, yayınlanan gözlemle
   `0,63σ` içinde. Daha dar bir bantla **daha iyi** tutuyor.
2. **ADR-0053 güçleniyor:** ima edilen `Y₀` `644 → 59 Pa`, yani üretim
   önselinin alt kenarından `1,2` dekad daha uzağa gidiyor. ADR-0053'ün
   önerdiği `[1e0, 1e5] Pa` bunu da içeriyor (§2c tablosu).
3. **Yoğunluk diliyle söylemek:** DY2'nin `β = 3,748`'i, Cheng bağıntısında
   `ρ = 2511,7 kg/m³`'e karşılık geliyor — yayınlanan makul aralığın
   (`1500–3300`) **içinde** ve eşit yoğunluk varsayımının (`2400`) yalnız
   `%4,7` üstünde. Yani "modelimiz gözlemi `%20` aşıyor" demek yerine
   **"modelimiz, Dimorphos'un yığın yoğunluğu `2512` ise gözlemi tam
   verir"** demek daha doğru ve daha bilgilendirici.

## 5. Ne **değişmiyor** (kural 6)

- **PROTOKOL-U §1'in `3,12 ± 0,34`'ü yerinde kalır.** Onunla hesaplanmış
  bütün yargılar (W, W2, U/V, DY, **DY2**) **olduğu gibi** durur ve
  yeniden hesaplanmaz. DY2'nin kilitli yargısı `MODEL GÖZLEME ULAŞIYOR`'dur
  ve `I = 1,40`'tır; bu ADR onu değiştirmez, **yanına** `I = 0,63`'ü
  koyar.
- `period_interface` yolu **silinmez**: bağımsız çapraz denetim olarak
  kalır ve `%10,5` farkı **yöntem** farkı olarak raporlar (dairesel iki
  cisim vs tam yörünge). Bu fark, bir sonraki ölçülmüş bütçe terimi
  adayıdır (`gozlem_yontemi`).
- Yeni hedef **bundan sonraki** protokollerde (üretim havuzu, posterior,
  PROTOKOL-HT) kullanılır.

## 6. Reddedilen seçenekler

- **`3,12`'yi olduğu gibi tutmak.** Üretim sahnesinin kütlesiyle tutarsız;
  A108'in kendi kuralını gözlem tarafında çiğner.
- **`3,2210`'a güncellemek** (yol (a), yeni kütleyle). Tutarlılığı düzeltir
  ama yine **bizim** dairesel yaklaşımımız; yayınlanan tam yörünge
  çözümünü göz ardı etmenin gerekçesi yok.
- **Sabit `3,61`'i almak.** Kütle eşleşmesini atlar: Cheng'in `ρ = 2400`
  varsayımı bizim sahnemizin kütlesine karşılık gelmiyor
  (`2400 · 1,81e6 = 4,344e9` vs `4,298e9`). `β ∝ M` olduğu için bu
  `%1,1` sistematik kayma demek — küçük, ama bedava düzeltilebilir.
- **Yeniden şekillenme (L16) düzeltmesini hedefe katmak.** `β`'yı `3,02`
  ya da `2,82`'ye indirir ve eski önseli "kurtarır" — ama o künyenin kendi
  notu *"arama özeti, tam metin teyidi bekliyor"*. Teyit edilmemiş bir
  düzeltmeyi, sonucu kurtardığı için almak **tam olarak** yapmamamız
  gereken şey. Tam metin teyit edilirse ayrı ADR ile açılır.
- **İki hedefi birlikte kullanmak** (çok gözlemli uygunsuzluk). Cazip ama
  yanlış: ikisi **aynı** `ΔT` ölçümünden türüyor, bağımsız gözlemli
  değiller; `I_M = max I_k` onları bağımsız sayar ve belirsizliği
  olduğundan küçük gösterir.
