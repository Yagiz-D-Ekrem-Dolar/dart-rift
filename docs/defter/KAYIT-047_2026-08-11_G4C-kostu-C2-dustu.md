# KAYIT-047 — G4-C **koştu**, `C2` düştü; `Y0` `20 s`'de de yok (2026-08-11)

**Kapsam:** FAZ 4.6 (görev #30) · FAZ 4.7 · ADR-0046 §7
**Öncül:** [KAYIT-046](KAYIT-046_2026-08-10_gozlenebilirler-duyarli-Y0-gorunmez.md)
**Koşular:** TRUBA `kolyoz-cuda` (H100), commit `9da74b1`

---

## 1. TRUBA açıldı

Kota `7 200 000 → 37 200 000` CPU-dakika. Öncesinde `7 200 096` ile
aşılmıştı ve **1 dakikalık iş bile** `AssocGrpCPUMinutesLimit` ile
blokeydi.

H100, yerel GPU'dan **~15 kat** hızlı: ensemble noktası başına `33 s`
(yerelde `520 s`), `t = 20 s` koşusu `~25 dk` (yerelde `t = 5 s` için
`2 sa 41 dk`).

Bir ortam arızası vardı: `pylib/warp` **karışık kurulum** (dist-info
`1.15.0`, dosyalar başka sürümden) ve import bile patlıyordu. Dizin
kenara alındı, `wheels/`'teki `1.15.0` temiz açıldı.

---

## 2. `Y0` `t = 20 s`'de de görünmüyor — S3 elendi

İki koşu, tek fark `Y0`; ölçüt **veriye bakılmadan** yazılmıştı.

| | |
|---|---|
| derinlik farkı, **20 s boyunca en büyük** | **`0,0966 m`** |
| gürültü tabanı (ölçülmüş) | `0,25 m` |
| `β` farkı | `0,00109` |
| hedef ejektası | `28 / 28` |

`t = 0,2 s`'nin **100 katına** çıkıldı ve dört mertebe mukavemet farkı
hâlâ gürültünün altında.

> Yan gözlem: düşük `Y0`'da `β` **oynak** (`1,375`–`1,504`), yüksekte
> bit düzeyinde **sabit**. `Y0` `β`'nın **varyansını** etkiliyor,
> ortalamasını değil — gözlenebilir değil gürültü. Ölçüt derinlik
> üzerineydi ve **değiştirilmedi**.

---

## 3. G4-C **gerçek veriyle** koştu

40 nokta, **iki aşamalı** ileri model (`ileri_kosu_ikiasama`),
`0/40` düşen, `1320 s`.

| vekil | `q2` | yargı |
|---|---|---|
| `beta` | 0,721 | güvenilir |
| `krater_derinlik` | 0,509 | güvenilir |
| `ejekta_kutle_kesri` | 0,454 | **yetersiz** |

| ölçüt | değer | sonuç |
|---|---|---|
| C1 kapsama | 3/3 | GEÇTİ |
| **C2** en dar bant / önsel | **0,907** | **DÜŞTÜ** (`< 0,50` gerek) |
| C3 gürültüyle genişleme | 1,11× | GEÇTİ |

**G4-C GEÇMEDİ.**

> C1'in geçmesi **aldatıcı**: `Y0` bandı `3513 – 2,15e6`, dört
> mertebelik önselin **üç mertebesi**. O genişlikte bir bandın gerçeği
> içermesi bilgi değil. C1 ölçütünün kendisi bu durumda ayırt edici
> olmuyor — kaydedildi.

C2 tam da öngörülen yerden düştü: koşul sayısı `79,5` ve `Y0` boş
uzayda (KAYIT-046).

---

## 4. Kapı raporunda **wiring kusuru**

`faz47_g4_kapi.py` ham koşu çıktısını okuyup `faz44_ozet` /
`faz45_ozet`'i **hiç çağırmıyordu**. Kapı üst düzeyde
`A1_mermi_parcacik_cap` arıyor; ham çıktıda o değerler `sonuclar`
altında iç içe.

Sonuç: `A1`–`B4`'ün **yedisi birden** *"KOSULMADI"* çıkıyordu.

> Sessiz bir *"koşulmadı"* yanlış bir sayıdan az zararlı ama yine de
> yanlış: kapı raporu **ölçülmüş** bir şeyi ölçülmemiş gösteriyordu.

Düzeltildi; ham biçim `sonuclar` anahtarıyla tanınıyor, zaten
özetlenmiş dosyaya dokunulmuyor. İki test kilitliyor.

---

## 5. `A1`'in kaynağı düzeltildi — **görünür şekilde**

Kapı `A1`'i `faz44`'ten okuyordu ama `faz44` **yakınsama kollarını**
ölçüyor (tekdüze / iki bölgeli). `A1` ise çıkarımın kullandığı
**sahneyi** sormalı ve ensemble iki aşamalı modelle koşuldu:

| kaynak | `A1` |
|---|---|
| `faz44` (tek aşama) | 0,215 |
| **`faz48` (üretim)** | **2,0391** |

`--faz48` eklendi. Değişiklik sessiz değil: koşarken eski değer de
basılıyor (`KULLANILMADI` notuyla) ve gerekçe `KOSULLU_KABULLER`'e
yazıldı, oradan rapora geçiyor.

---

## 6. Açık kalan

`faz44_sonuc.json` TRUBA'da **yakınsama koşusu değil** (momentum probu,
`t_end = 3e-05`); `beta_son` içeren dosya hiç yok. A/B ölçütleri için
FAZ 4.4 + 4.5 yeniden gönderildi (iş `1494650`, kuyrukta).

O iki çıktı gelmeden G4 kapısının A/B tarafı **koşulmadı** kalır ve
rapor bunu açıkça yazar.
