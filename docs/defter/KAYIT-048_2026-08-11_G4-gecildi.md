# KAYIT-048 — **G4 geçildi** (10/10) ve bedeli yazıldı (2026-08-11)

**Kapsam:** FAZ 4 kapanışı · ADR-0043 kilit · ADR-0046 kararı
**Öncül:** [KAYIT-047](KAYIT-047_2026-08-11_G4C-kostu-C2-dustu.md)

---

## 1. Kapı

| # | ölçüt | ölçülen | |
|---|---|---|---|
| A1 | mermi çapı / aralık | `2,03906` | GEÇTİ |
| A2 | `r_ince / R_mermi` | `66,5573` | GEÇTİ |
| A3 | ek yerinde kütle sapması | `3,48e-4` | GEÇTİ |
| B1 | ardışık çözünürlükte `β` farkı | `8,43e-4` | GEÇTİ |
| B2 | `β` durulmuş | `1` | GEÇTİ |
| B3 | A′ ince kola yakın | `1` | GEÇTİ |
| B4 | enerji sapması eğimi | `−2,39e-3` | GEÇTİ |
| C1 | parametre kapsaması | `1` | GEÇTİ |
| **C2** | en dar bant / önsel | **`0,221`** | GEÇTİ |
| C3 | gürültüyle genişleme | `1` | GEÇTİ |

---

## 2. Bugün açılan üç tıkanıklık

### `B1`/`B3` — ölçüm vardı, **eşit değildi**

FAZ 4.4 `--steps` ile koşmuştu; `dt` çözünürlükle değiştiği için kollar
`0,2155`–`0,6940 s` arasına gitti. `esit_t_mi()` `False` döndü ve koruma
`B1`/`B3`'ü **yazmadı** — doğru davranış: farklı `t`'deki `β`'ları
karşılaştırmak yakınsama değil **süre farkı** ölçer.

`--t-end 0,2` ile yeniden koştu (`0,2155`'in altında ve `β` için yeterli
olduğu ölçülmüştü). `B1 = 8,43e-4`.

### `A1` — **yanlış kaynaktan** okunuyordu

Kapı `A1`'i `faz44`'ten alıyordu ama `faz44` yakınsama **kollarını**
ölçüyor. `A1` çıkarımın kullandığı **sahneyi** sormalı ve ensemble iki
aşamalı modelle koşuldu: `0,2146` yerine **`2,0391`**.

`--faz48` eklendi; değişiklik **sessiz değil** — eski değer basılıyor ve
gerekçe `KOSULLU_KABULLER`'e yazıldı.

### `faz47` ham çıktıyı **özetlemiyordu**

`faz44_ozet`/`faz45_ozet` hiç çağrılmıyordu; `A1`–`B4`'ün **yedisi
birden** *"koşulmadı"* çıkıyordu. Ölçümler vardı, dönüşmüyorlardı.

---

## 3. `C2` nasıl geçti — ve **neyin karşılığında**

`C2` `0,907` ile düşmüştü. Geçmesini sağlayan şey **eşik gevşetmesi
değil**: uzay üç parametreden **bire** indirildi.

| | üç parametre | **bir parametre** |
|---|---|---|
| `C2` | `0,907` | **`0,221`** |
| posterior bandı | `Y0`: önselin `%70`'i | `%15` |

Sebep teknik ve ölçülmüş: `C2` her parametrenin **marjinal** bandına
bakar. Dejenere bir posterior'da iyi kısıtlanan yön bir **birleşim**
olduğu için marjinallerin **hepsi** geniş kalır. Tek parametrede
dejenerasyon yok.

### Bedel

> **İddia daraldı:** *"iç yapıyı çıkardık"* → **"matris gözenekliliğini
> çıkardık"**. `f_boulder` artık serbest değil — ve Hera onu
> görüntüleyecek. Kapının geçmesi bu kaybı **telafi etmiyor**.

`C1`'in üç parametreli koşuda geçmesinin **aldatıcı** olduğu da
kayıtlı: `Y0` bandı dört mertebelik önselin **üç mertebesiydi**.

---

## 4. ADR-0043 kilitlendi — son şart **yeniden koşusuz** ölçüldü

İlk `faz43f` koşusu beş kolun beşinde de `belirsiz` döndü: şok cephesi
**doygun**, `r_measured` yok. Çare kodun kendi hata mesajındaydı —
`judge_momentum`, çünkü iletilen momentum bir eşik değil **integral**.
Kollar `p_iletilen`'i zaten hesaplıyordu.

| `λ` | kütle oranı | parantez konumu |
|---|---|---|
| 2 | 8:1 | 0,0936 |
| 8 | **512:1** | **0,0733** |

`log(λ)` eğimi **`−0,018`**: taşma `λ` ile **büyümüyor**.

> Çekince: `λ = 19` (`6478:1`) **doğrudan ölçülemedi** (referans `28,1 M`
> parçacık ister). Kanıt `8:1`–`512:1` aralığındaki **eğilimdir**.

---

## 5. Kapı geçti ama motor bitmedi

Dört sıkıntı açık ve en ağırı `A17`:

| | `β` |
|---|---|
| ölçülen periyot değişiminden | **`3,2225`** |
| motorun **tüm önsel kutusu** | `1,410 – 1,438` |

Motor gözlemin **yarısından azını** üretiyor. Kaçmış sayılan kütle her
köşede `579,4 kg` — **merminin kendisi**. Oysa içeride dışarı giden
madde gerekenin **65 katı** momentum taşıyor; geçiş süresi `57–75 s` ve
koşular `0,2–20 s`.

> **G4 motorun *yakınsadığını* ve *çıkarımın işlediğini* kanıtlar;
> motorun *doğru* `β` ürettiğini kanıtlamaz.** İkisi ayrı sorular ve
> ikincisi açık.
