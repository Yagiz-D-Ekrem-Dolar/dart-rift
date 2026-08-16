# G4 kapı raporu

> **Üretildi:** 2026-08-11, TRUBA `kolyoz-cuda` (H100).
> **Kaynaklar:** `faz44_esit.json` (eşit `t_sim`), `faz45_durulma.json`,
> `faz46_g4c.json` (iki aşamalı ensemble, 40 nokta), `y0lo.json` (`A1`).
> Bu dosya `scripts/faz47_g4_kapi.py` tarafından **üretilir**; elle
> düzenlenmez.

**Sonuç:** **GEÇİLEMEDİ**

- **düşen ölçütler:** C2

> Kısmi geçiş yoktur. Bir ölçüt koşulmadıysa **geçmemiş** sayılır.
> Bu koşuda **koşulmayan ölçüt kalmadı** — onu da yazmak gerekiyor:
> `10` ölçütün `9`'u geçti, `1`'i düştü.

## G4-A — mermi çözülüyor — GEÇTİ

| # | ölçüt | eşik | ölçülen | durum |
|---|---|---|---|---|
| A1 | mermi çapı / yerel aralık | `>= 2` | `2.03906` | **GECTI** |
| A2 | `r_ince / R_mermi` | `>= 3` | `66.5573` | **GECTI** |
| A3 | kaba/ince ek yerinde kütle sapması | `< 0.005` | `0.000348021` | **GECTI** |

## G4-B — gözlenebilirler yakınsıyor — GEÇTİ

| # | ölçüt | eşik | ölçülen | durum |
|---|---|---|---|---|
| B1 | ardışık çözünürlükte `β` farkı | `< 0.1` | `0.000842672` | **GECTI** |
| B2 | `β` durulmuş (1 = evet) | `>= 1` | `1` | **GECTI** |
| B3 | A′, ince kola tek `h`'den yakın (1 = evet) | `>= 1` | `1` | **GECTI** |
| B4 | enerji sapması log-log eğim | `< 1` | `-0.00238537` | **GECTI** |

## G4-C — parametreler geri bulunuyor — GEÇMEDİ

| # | ölçüt | eşik | ölçülen | durum |
|---|---|---|---|---|
| C1 | parametre kapsaması (3/3) | `>= 1` | `1` | **GECTI** |
| C2 | en dar bant / önsel | `< 0.5` | `0.906948` | **DUSTU** |
| C3 | gürültüyle genişleme (1 = evet) | `>= 1` | `1` | **GECTI** |

### `C2` neden düştü — **ölçülmüş yapısal sebep**

Bu bir aksaklık değil. Ölçüldü (FAZ 4.11/4.12, KAYIT-046):

| | |
|---|---|
| `2 × 2` Jacobian'ın **koşul sayısı** | **`79,5`** |
| 2. yönü kurtarmak için gereken gözlem kesinliği | `%0,067` |
| DART'ın `β` ölçüm belirsizliği | `~%5` |
| boş uzay yönünün en büyük bileşeni | **`Y0` (`0,81`)** |

Yığın yoğunluğu ADR-0030 gereği sabit olduğu için üretici
`matrix_alpha0`'ı `(boulder_alpha0, f_boulder)`'dan **türetiyor**;
derinlik ile matris `α₀` korelasyonu `r = −0,9932`. Üç parametreli uzay
**yapısı gereği** tek boyutlu.

> **`C1`'in geçmesi aldatıcıdır ve öyle okunmamalıdır.** `Y0` bandı
> `3513 – 2,15e6`, yani dört mertebelik önselin **üç mertebesi**. O
> genişlikte bir bandın gerçeği içermesi bilgi değildir.

Çare bir ölçüm değil **kapsam kararıdır** (ADR-0046) ve bu belge onu
vermez.

## Tanılar — **ölçüt değil**

> Bunlar ölçüldü ama G4'ün geçme koşulu **değil**. Ölçütler ölçümden
> önce yazıldı ve sonradan eklenmiyor (ADR-0040); bilgi ise gizlenmiyor.

| büyüklük | ölçülen | yorum |
|---|---|---|
| `β_bound` baştan sona sabit mi kaldı | `0` | `1` ise B2 **yazılmaz** — sabit seride `durulmuş` boş bir kanıttır (sıkıntı 33) |
| A′ dikişinde en yakın komşu / ince aralık | `0.652114` | 0,5'in altı gözden geçirme gerektirir |
| FAZ 4.4 kolları aynı `t_sim`'e ulaştı mı | `1` | `0` ise B1 ve B3 **yazılmaz** (sıkıntı A6) |
| A′'nın parçacık tasarrufu | `6.87227` | ölçülen `6,87×` (`s = 7,0/3,5`, `r_iç = 25`) |

## Koşullu kabuller

> Kapı geçse **bile** bunlar açık kalır.

1. ADR-0041 ve ADR-0042 küp geometrisinde ölçüldü, DART geometrisinde değil (KAYIT-035, KAYIT-037).
2. Boşluk 3 `λ = 2` (8:1) oranında kapandı; ADR-0026 DART için çok daha yüksek oran istiyor. *(2026-08-11: eğilim `8:1`–`512:1` aralığında ölçüldü ve bozulmuyor — ADR-0043 §7 madde 3.)*
3. B1 eşiği (`%10`) bilinçli olarak gevşek; ana ürün henüz `±0,1` doğrulukta değil.
4. `B1`/`B2`/`B3` `β` üzerinden ölçüldü ve `λ=2`'de `β` **merminin sekmesidir**: kaçan kütle `579,44 kg` = merminin kendisi. Sayılar doğru, **iddiaları dar** (rapor A12).
5. `λ=2`'de mermi `h`'si çapının `9,32` katı. Çözülmüş mermide `n_ejekta` `803 → 28`: **rejim** değişiyor (ADR-0043 §4g).
6. Krater ve ejekta gözlenebilirleri `t = 0,2 s`'de zayıf. *(2026-08-11: derinlik `kutulama="eksen"` ile canlandı, `%20,7` yayılım; çap hâlâ ölü — rapor A11/A13/A16.)*
7. `A1` **`faz44`'ten değil** iki aşamalı üretim modelinden (`faz48`) okunuyor. `faz44` yakınsama **kollarını** ölçüyor; `A1` çıkarımın kullandığı **sahneyi** sormalı. `faz44`'ün kendi `A1`'i `0,215`, üretimde `2,0391`.
8. **Motor `β`'yı gözlemin `2,3` katı altında üretiyor** (rapor A17): ölçülen periyot değişiminden `β = 3,2225`, modelin tüm önsel kutusu `1,410–1,438`. Bu kapının ölçütü değil ama kapının geçmesi bu kusuru **kapatmaz**.
