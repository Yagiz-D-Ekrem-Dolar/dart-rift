# ADR-0059 — Çok doğruluklu vekilin **geri alınması**: çözünürlük farkı σ mı, yanlılık mı?

**Tarih:** 2026-10-09 · **Durum:** kabul (öneri, kilitli)
**Veri durumu:** havuz (`1592569`) **koşuyor**, TRUBA erişimi kapalı,
**hiçbir nokta görülmedi.** Kural 6 sağlanıyor.
**Öncül:** PROTOKOL-UY2-KESISIM, KAYIT-071 (satır 22),
[ADR-0058](ADR-0058-uretim-posteriorunun-tarifi.md),
[PROTOKOL-HAVUZ](../truba/PROTOKOL-HAVUZ-URETIM.md), PROTOKOL-M-YAKINSAMA
**Kod:** `inference/cok_dogruluk.py` (yazılmış, sınavlanmış, **çağrılmıyor** — A116)

---

## 1. Ne oldu

UY2 ve KAYIT-071 satır 22 üretim yolunu **"kaba merdiven + çok doğruluklu
vekil"** olarak kilitlemişti. ADR-0058 üretim posteriorunun tarifini
yazarken bu maddeyi **düşürdüm.** ADR-0058'in beş kararında ve reddedilen
seçeneklerinde çok doğruluklu vekil **hiç geçmiyor** — reddedilmiş bile
değil, **unutulmuş**.

`src/dartrift/inference/cok_dogruluk.py` yazılmış, Kennedy–O'Hagan AR(1)
belgelenmiş, sınavları geçiyor ve **hiçbir yerden çağrılmıyor.**

Bu ADR o maddeyi geri alıyor. ADR-0058'in hiçbir satırı silinmiyor
(kural 5); oraya bu ADR'ye işaret eden bir not düşüldü.

## 2. Mesele: **σ** ile **yanlılık** aynı şey değil

ADR-0058 ve PROTOKOL-HAVUZ, çözünürlük farkını `σ_model` içinde
**varyans terimi** olarak taşıyor:

| terim | değer | kaynak |
|---|---|---|
| `cozunurluk_uzak` | `0,004` | UA: Δ(3,5 m; 7 m), KAYIT-067 |
| `cozunurluk_yakin` | `0,053` | PROTOKOL-UY |

Çok doğruluklu vekil ise farkı **düzeltme** olarak taşır:

    y_orta(x) = ρ · f_kaba(x) + δ(x)

Fark şu: `σ` yaklaşımı posterioru **genişletir** ama **kaba öngörünün
merkezinde** bırakır. Fark sistematik bir kaymaysa, `θ` o kaymayı
**emmek zorunda kalır** — yani yanlış bir iç yapıya, doğru bir `β`
ürettiği için inanırız.

### Çözülmemiş uyuşmazlık

PROTOKOL-M / U0, kaba → orta geçişinde `β` için **`−%13`** ölçtü
(`cok_dogruluk.py`'nin kendi gerekçe metninde yazılı).
`cozunurluk_yakin` ise **`%5,3`**.

İkisi arasında `~2,5×` fark var. Bu uyuşmazlık **çözülmedi** ve bu ADR
onu çözdüğünü iddia **etmiyor**. İki sayının farklı şeyler ölçüyor
olması mümkün (farklı `θ`, farklı sahne, biri saçılma biri kayma).
Ama şu kesin: **hangisinin doğru olduğunu bilmeden**, yalnız `σ` yolunu
tek cevap olarak yayımlamak savunulamaz.

> Not: `−%13` tek bir `θ` noktasında (U0) ölçüldü. Üretim sahnesinin
> yanlılığı olduğunu **iddia etmiyorum**; ölçülmedi. İddia yalnız şu:
> bu büyüklükte bir kaymanın **mümkün** olduğunu kendi ölçümümüz
> gösteriyor ve `%5,3`'lük bir σ onu yutmaz.

## 3. Karar

1. **İç içe (nested) ince tasarım.** `96` kaba noktanın **12**'si
   `3,5 m`'de tekrar koşulur. `~224 GPU-saat` (PLAN-90-GUN 3. kuşak, 12).
   İç içe olması şart: `δ`'nın özyinelemeli kestirimi iç içe tasarımda
   **kesin**, değilse yaklaşık.

2. **12 nokta ŞİMDİ, veriye bakmadan seçilir.** Ölçüt: `96` nokta
   içinden **maximin** alt küme (`DART_UZAYI_S4`'te ölçeklenmiş
   uzaklıkla), deterministik ve tohumsuz. Seçim betiği havuz
   okunmadan koşar ve çıktısı commit edilir.

   **KİLİTLİ SEÇİM — 2026-10-09, havuz okunmadan koşuldu:**

   ```
   [11, 20, 33, 44, 45, 57, 58, 62, 74, 78, 87, 92]
   ```

   Kod: `inference/ic_ice_tasarim.maximin_alt_kume`, girdi
   `lhs_design(DART_UZAYI_S4, 96, root_seed=20260906)` (PROTOKOL-HAVUZ §3
   ile **aynı** tasarım). Ölçülen kapsama:

   | ölçü | değer | anlamı |
   |---|---|---|
   | `min_ikili` | `0,4632` | seçilenler arası en küçük uzaklık |
   | `rastgele_ortalama_min_ikili` | `0,1559` | aynı `k` için rastgele alt küme kıyası |
   | `en_uzak_ortulmemis` | `0,4487` | seçilmeyen bir noktanın en büyük uzaklığı |

   Maximin rastgeleden **`2,97×`** daha iyi yayılıyor. Bu liste
   `tests/test_ic_ice_tasarim.py::test_KILITLI_12_nokta_kaydi` ile
   **sınava bağlandı**: havuz görüldükten sonra "daha iyi" diye
   değiştirilirse sınav düşer.

3. **Posterior İKİ YOLLA hesaplanır ve YAN YANA raporlanır:**

   | yol | tarif |
   |---|---|
   | `SIGMA` | ADR-0058'in kilitli tarifi, **değişmeden** |
   | `CD` | aynı tarif, ama vekil `cok_dogruluk` ile orta çözünürlüğe düzeltilmiş |

   ADR-0058 geçersiz **değil**; `SIGMA` yolu olduğu gibi duruyor.

4. **Manşet hangisi: `CD` KAPISI'na bağlı.**

   | kapı | eşik |
   |---|---|
   | tasarım iç içe | `12` ince nokta `96`'nın **alt kümesi** |
   | `ρ` ızgara kenarında değil | `cok_dogruluk`'un uyarı alanı **boş** |
   | ince noktalarda dışarıda-bırak-bir | `E_CD < E_SIGMA` |
   | iki yolun kipleri | ayrılıyorsa **ikisi de** manşette |

   **Dördü de geçerse** manşet `CD`, `SIGMA` zorunlu ek.
   **Biri bile düşerse** manşet `SIGMA`, `CD` "keşif" etiketiyle ek —
   ve kapının hangi maddesinin düştüğü yazılır.

5. **İki yolun kipleri `≥ 1σ` ayrılırsa** bu bir **bulgu**dur, gizlenmez:
   "çözünürlük seçimi `θ` kestirimini `X` kadar kaydırıyor" cümlesi
   rapora **girer** ve PLAN-90-GUN'daki 4. kuşak gerekçesine eklenir.

## 4. Ne **iddia edilmeyecek**

- "Çözünürlük sorununu çözdük." `3,5 m` de yakınsamış değil
  (PROTOKOL-M); `CD` yalnız `7 m → 3,5 m` farkını düzeltir.
- "`CD` doğru cevap." Kapı geçse bile bu bir **model**; `δ`'nın
  `12` noktadan öğrenilmiş GP'si.
- "`−%13` üretim sahnesinin yanlılığıdır." Ölçülmedi (§2 notu).

## 5. Reddedilen seçenekler

- **Olduğu gibi bırakmak (yalnız `SIGMA`).** UY2'nin kilitli kararını
  sessizce düşürmek olur ve §2'deki `2,5×` uyuşmazlık cevapsız kalır.
- **ADR-0058'i değiştirmek.** Kural 5: satır silinmez. Yeni ADR + not.
- **12 ince noktayı posterior sırtına göre seçmek.** İstatistiksel
  olarak daha verimli olurdu, ama düzeltmeyi **veriye bakarak**
  konumlandırmak olur; seçim etkisi `CD`'nin kendi kapısını zayıflatır.
  Maximin daha az verimli, **daha savunulabilir**.
- **İnce noktaları `96`'nın dışından almak.** İç içe olmaz; `δ`
  yaklaşık kalır ve kapının birinci maddesi anlamını yitirir.
- **Havuz sonucunu görüp hangi yolu yayımlayacağımıza karar vermek.**
  Tam olarak kural 6'nın yasakladığı şey. Kapı yukarıda, **önce** yazıldı.
