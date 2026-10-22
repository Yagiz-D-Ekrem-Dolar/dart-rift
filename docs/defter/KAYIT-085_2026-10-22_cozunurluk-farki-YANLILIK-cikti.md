# KAYIT-085 — Çözünürlük farkı **yanlılık** çıktı: `σ` yaklaşımı yetersiz

**Tarih:** 2026-10-22 · **Sıfır GPU** (analiz)
**Öncül:** [ADR-0059](../adr/ADR-0059-cok-dogruluklu-vekilin-geri-alinmasi.md),
PROTOKOL-M, KAYIT-083 (yükselteç), KAYIT-082
**Veri:** iç içe ince koşu, **7/12** nokta

---

## 1. Tek cümle

İnce koşunun tamamlanan 7 noktasında `b_ince > b_kaba` — **7'sinde de,
istisnasız**. Yani kaba ile orta çözünürlük arasındaki fark saçılma
değil **sistematik kayma**; ADR-0058'in paydaya varyans terimi koyan
yaklaşımı bu farkı doğru temsil **etmiyor**.

## 2. Ölçüm

| nokta | `b_kaba` | `b_ince` | oran | `β_kaba` | `β_ince` | oran |
|---|---:|---:|---:|---:|---:|---:|
| 11 | 0,7081 | 0,9350 | 1,3204 | 1,5828 | 1,7428 | 1,1011 |
| 33 | 3,3646 | 4,0835 | 1,2137 | 3,8795 | 4,8406 | 1,2477 |
| 45 | 1,9075 | 2,3515 | 1,2328 | 2,6438 | 2,9761 | 1,1257 |
| 57 | 2,9410 | 4,4246 | 1,5045 | 3,5235 | 4,6705 | 1,3255 |
| 58 | 2,0154 | 2,5882 | 1,2842 | 2,7578 | 3,2405 | 1,1750 |
| 62 | 1,7987 | 2,0565 | 1,1433 | 2,5577 | 2,7312 | 1,0678 |
| 74 | 4,5043 | 4,9490 | 1,0987 | 5,0156 | 5,7754 | 1,1515 |

| | `b` | `β` |
|---|---:|---:|
| ortanca oran | **1,2328** (**%+23,3**) | 1,1515 (%+15,1) |
| ortalama | 1,2568 | — |
| sd | 0,1332 | — |
| aralık | 1,099 – 1,505 | 1,068 – 1,326 |
| **aynı yön** | **7/7** | **7/7** |

**İşaret sınavı:** saf saçılma olsaydı 7/7 aynı işaret olasılığı
`1/64`; iki yönlü **`p = 0,0156`**.
**Tek örnek `t`** (`H₀`: oran = 1): **`t = 5,10`**, sd = 6.

Yedi noktayla bile sonuç şansa bağlanamaz.

## 3. Niçin bu ciddi — KAYIT-083'ün yükselteci

`β−1 ∝ Y₀^(−0,1791)`, yani `1/|p| = 5,58`. `b`'deki her kayma `Y₀`'ya
5,58. kuvvetle geçiyor:

| `b`'de kayma | `Y₀`'da |
|---|---:|
| **ölçülen %+23,3** | **×3,22** |
| paydanın öngördüğü %5,3 | ×1,33 |

Yani:

- Posteriorun kipi `Y₀ ≈ 18,7 Pa`; orta çözünürlükte aynı gözlemi
  karşılayan değer **~60 Pa**.
- Paydadaki `cozunurluk_yakin = 0,053` terimi bu kaymanın yalnız
  **~%23'ünü** (çarpan olarak `1,33 / 3,22`) hesaba katıyor.

ADR-0059'un uyarısı birebir gerçekleşti:

> *"`σ` yaklaşımı posterioru genişletir ama kaba öngörünün merkezinde
> bırakır. Fark sistematik bir kaymaysa, `θ` o kaymayı emmek zorunda
> kalır — yani yanlış bir iç yapıya, doğru bir `β` ürettiği için
> inanırız."*

## 4. M/U0 ile **işaret çelişkisi** — çözülmedi

ADR-0059 §2, PROTOKOL-M/U0'ın kaba→orta geçişinde `β` için **`−%13`**
ölçtüğünü kaydediyor. Biz aynı geçişte **`+%15,1`** ölçtük.

**İşaretler ters.** Büyüklükler benzer, yön zıt.

Olası sebepler — hiçbiri ölçülmedi, bu yüzden hiçbiri iddia edilmiyor:

- U0 tek bir `θ` noktasıydı; burada 7 farklı `θ` var
- Sahne ve yapılandırma farklı olabilir (U0 üretim sahnesi değil)
- İki ölçümden biri hatalı olabilir

Bu çelişki **açık kalıyor** ve raporda böyle yazılacak. Kapatmadan
"çözünürlük düzeltmesi şudur" denemez.

## 5. ADR-0059 kapısı: **DÜŞTÜ** (1. madde)

Kilitli kapı dört maddeydi; ilki:

> | tasarım iç içe | `12` ince nokta `96`'nın alt kümesi |

Elimizde **7** var, 12 değil. Kayıp sebepleri:

| nokta | sebep |
|---|---|
| 20, 44 | zaman sınırı (48 sa gönderilmiş; bölüm 72 sa'e izin veriyormuş) |
| 78, 87, 92 | `TESISAT SINAVI DUSTU: nvidia-smi GPU gormuyor (kolyoz11)` |

Son üçü donanım arızası ve `ortak_bas.sh`'ın bekçisi **çöp üretmek
yerine durdurdu** — tasarlandığı gibi çalıştı.

Kapının kuralı açık: *"Biri bile düşerse manşet `SIGMA`, `CD` 'keşif'
etiketiyle ek — ve kapının hangi maddesinin düştüğü yazılır."*

**Uygulanan:** manşet `SIGMA` (ADR-0058'in kilitli tarifi, değişmeden).
Çok doğruluklu düzeltme (`CD`) **yapılmadı** — 7 noktayla `δ`'nın GP'si
kurulmaz ve kapı zaten düştü.

> Dikkat: kapının düşmesi **tanıyı** geçersiz kılmaz. Kapı "`CD`
> düzeltmesi manşet olabilir mi" sorusunun kapısıydı. §2'deki ölçüm
> ayrı bir şeydir ve geçerlidir.

## 6. Sonuçlara etkisi

**Etkilenmeyen:** `n_yön = 1`. İkinci Fisher öz değeri eşiğin 44 katı
altındaydı; noktadan noktaya 1,10–1,50 arasında değişen bir çarpan
bunu kapatmaz. Dejenerasyon bulgusu ayakta.

**Etkilenen:** `Y₀`'nın **mutlak değeri**. `18,7 Pa` sayısı artık
şu şerhle verilmeli: *çözünürlüğe sistematik olarak bağlı; orta
çözünürlükte ~60 Pa, ve 3,5 m de yakınsamış değil (PROTOKOL-M).*

**Yeni cümle — eskisinin yerine:**

> `Y₀`'nın mutlak değeri bu veriyle **belirlenemiyor**: kaba→orta
> çözünürlük adımı `b`'yi sistematik olarak `%+23` kaydırıyor (7/7,
> `p = 0,016`) ve bu, `Y₀`'da `×3,2`'ye karşılık geliyor. Belirlenen
> şey `β`'nın **bir** yön taşıdığıdır (`n_yön = 1`), o yönün sayısal
> konumu değil.

Bu, raporun iddiasını **daraltıyor** — ve daralma doğru yönde:
ölçmediğimiz bir şeyi ölçtük demiyoruz.

## 7. Bundan sonra

1. **Mühürlü spin ön kaydı** (`ONKAYIT_HERA_SPIN_uretim96`) kendi §7(4)
   uyarısında *"ince koşu yanlılık gösterirse bu kayıt yeniden
   üretilmeli"* diyordu. **Gösterdi.** Kayıt duruyor (silinmez), ama
   yanına bu kaydın notu düşülecek.
2. Kalan 5 nokta **72 saatlik** sınırla ve `kolyoz11` dışlanarak
   yeniden gönderilmeli; 12'ye tamamlanırsa ADR-0059 kapısı yeniden
   değerlendirilebilir.
3. `truba/is_HAVUZ_INCE.slurm`: `--time` 48 → **72**, `--exclude`
   listesine `kolyoz11` eklenmeli.
