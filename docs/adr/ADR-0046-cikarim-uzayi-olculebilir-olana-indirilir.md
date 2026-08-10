# ADR-0046 — Çıkarım uzayı **ölçülebilir olana** indirilir

**Tarih:** 2026-08-10
**Durum:** **ÖNERİ** — karar verilmedi
**İlgili:** [ADR-0030](ADR-0030-kutle-gozeneklilikten-turer.md) ·
[ADR-0044](ADR-0044-cikarim-parametre-uzayi-tutarsiz.md) ·
[ADR-0040](ADR-0040-kriter-dusebilmelidir.md) ·
[KAYIT-046](../defter/KAYIT-046_2026-08-10_gozlenebilirler-duyarli-Y0-gorunmez.md)

---

## 1. Karar gerektiren şey

`DART_UZAYI_S3 = (boulder_alpha0, Y0, f_boulder)` — üç parametre.
G4-C ölçütü: **3/3 parametre kurtarılmalı**.

Ölçüldü (FAZ 4.11 + 4.12, 9 köşe, `t_end = 0,2 s`, `0/9` düşen):
**bu ölçüt bu ileri modelle karşılanamaz.** Sebep çözünürlük ya da koşu
süresi değil, **parametre uzayının kendi yapısı**.

---

## 2. Ölçümler

### 2a. Gözlenebilirlerin durumu

| gözlenebilir | bağıl yayılım | yargı |
|---|---|---|
| `krater_derinlik` | **%20,7** | en güçlü |
| `beta` | %2,0 | kullanılabilir |
| `ejekta_kutle_kesri` | eşik göstergesi | zayıf (2 seviye) |
| `krater_capi` | `0` | ölü |

### 2b. `Y0` **görünmez** — iki bağımsız ölçüm

| parametre | `β` etkisi | derinlik etkisi |
|---|---|---|
| `boulder_alpha0` | +0,01131 | **+1,4124 m** |
| `f_boulder` | −0,01575 | **−1,4987 m** |
| **`Y0`** | **+0,00115** | **−0,0768 m** |

`Y0` **dört mertebe** değişiyor (`10³ → 10⁷ Pa`) ve etkisi diğerlerinin
`%5`–`%8`'i. Daha keskin: nokta 4 ile 6 **yalnızca** `Y0`'da farklı ve
hedef ejektası `0,1 kg` bile değişmiyor (`670,7` / `670,7`).

Sebebi makul: `t = 0,2 s`'de basınçlar `GPa` mertebesinde; `Y0 = 10⁷ Pa`
bile **üç mertebe** küçük, akış mukavemeti hissetmiyor. Mukavemet
kraterin **geç** evresinde belirleyici olur ve o evre `0,2 s`'de yok.

### 2c. Kalan iki parametre **ayrışmıyor**

`Y0`'yı tamamen dışarıda bırakıp `(boulder_alpha0, f_boulder)` için
`2 × 2` Jacobian (birimlenmiş kutu, gözlenebilirler kendi ölçeklerine
bölünmüş):

```
d(beta)/d(a0, fb)     = +0,01131   -0,01575
d(derinlik)/d(a0, fb) = +1,41236   -1,49868

olceklenmis tekil degerler = 0,14287 ,  0,00180
KOSUL SAYISI              = 79,5
```

Bir parametre yönü iyi kısıtlanıyor; **dik yönü `~80` kat zayıf.**
`β` ile derinlik arasında `r = +0,836` (`r² = 0,70`) — yani bağımsız
bileşen **var** ama az.

### 2d. Kök neden: iki parametre **tek** türetilmiş büyüklüğe çöküyor

Yığın yoğunluğu ADR-0030 gereği **sabit** (`1800 kg/m³`, ölçülmüş
değer). Dolayısıyla üretici `matrix_alpha0`'ı
`(boulder_alpha0, f_boulder)`'dan **türetmek zorunda**:

| # | `a0_blok` | `f_blok` | **matris `α₀`** | derinlik |
|---|---|---|---|---|
| 1,3 | 1,30 | 0,05 | 1,5122 | 15,35 / 15,28 |
| 0,2 | 1,00 | 0,05 | 1,5405 | 15,09 / 15,01 |
| 5,7 | 1,30 | 0,50 | 1,7727 | 15,00 / 14,93 |
| 4,6 | 1,00 | 0,50 | **3,0000** | **12,45 / 12,36** |

Derinlik ile matris `α₀` arasında **`r = −0,9932`** (`R² = 0,986`).

> **Çarpma matris gözenekliliğini hissediyor; ona nasıl varıldığını
> hissetmiyor.** İki serbest parametre tek bir türetilmiş sayıya
> çöküyor — üçüncüsü (`Y0`) hiç hissedilmiyor. Üç parametreli uzay
> **yapısı gereği** tek boyutlu.

`β` matris yoğunluğuyla `R² = 0,767` uyuyor, yani `β`'da matris
gözenekliliğinin **ötesinde** bir bileşen var (`%23`). Bu, dik yöndeki
zayıf kısıtın kaynağı.

---

## 3. Bu neden bir **kusur değil**

Üç ölçüm de doğru; ileri model de doğru. Sorun **soru sorma
biçiminde**: üç serbest sayı seçtim ama ileri model onların yalnızca
bir birleşimini gözlenebilirlere yazıyor.

> G4-C'nin *"3/3 kurtarıldı"* ölçütü **karşılanamaz** ve düşmesi
> ADR-0040'ın istediği türden bir düşüş: *"bir kriter düşebilmelidir."*
> Kurtarılamayan şeyi kurtarılmış göstermek için gözlenebilir uydurmak
> ya da eşik gevşetmek — asıl kusur o olurdu.

---

## 4. Seçenekler

### S1 — Uzayı **tek parametreye** indir: `matrix_alpha0`

Doğrudan ölçülebilen büyüklük. `boulder_alpha0` ve `f_boulder` sabit
tutulur (FAZ 3 değerleri), `matrix_alpha0` serbest bırakılır ve
`ρ_yığın` kısıtı **ters yönde** kullanılır.

**Artı:** Belirlenmiş sistem (1 parametre, 2 gözlenebilir). G4-C
anlamlı biçimde geçebilir. Derinlik `R² = 0,986` ile bu büyüklüğü
zaten okuyor.

**Eksi:** Bilimsel iddia daralır — *"iç yapıyı çıkardık"* yerine
*"matris gözenekliliğini çıkardık"*. `f_boulder` (blok oranı) Hera'nın
görüntüleyeceği bir şey ve onu bırakmak bilgi kaybı.

### S2 — İki parametre (`matrix_alpha0`, `f_boulder`), `Y0` **çıkarılır**

**Artı:** `f_boulder` kalır. Koşul sayısı yeniden ölçülmeli ama bu
eşleme `matrix_alpha0`'ı türetilmiş değil **serbest** yaptığı için
çökme kalkar.

**Eksi:** `ρ_yığın` sabitken `matrix_alpha0` ve `f_boulder` bağımsız
seçilemez — ADR-0030 kısıtı yeniden ihlal edilir (ADR-0044'ün
düzelttiği hatanın aynısı). **Ölçülmeden seçilemez.**

### S3 — `Y0`'yı görünür kılmak için **daha uzun koş**

Mukavemet geç evrede belirleyici. `t = 5 s`'de krater hâlâ büyüyordu,
yani arrest süresi çok daha uzun.

**Artı:** Bilimsel iddia korunur.
**Eksi:** ADR-0043'ün maliyet hesabı yeniden açılır. `t = 5 s` tek
nokta için `2h 41dk`; ensemble için `9 × 2,7 h ≈ 24 saat`, ve arrest
süresinin `5 s` olduğu **ölçülmedi** — daha büyük olabilir.

---

## 5. Eğilimim: **S1**, S3'ü ayrı bir ölçümle sınamak üzere

Gerekçe: S1 **bugün ölçülmüş** kanıta dayanıyor (`R² = 0,986`), S2
ADR-0030 ile çelişebilir ve **ölçülmedi**, S3 bilinmeyen bir süreye
bahis.

S1'i seçmek S3'ü kapatmıyor: `Y0`'nın hangi `t`'de görünür olduğu
**ayrı ve ucuz** bir ölçüm (tek parametre çifti, uzun koşu, `Y0`'nın
iki ucu). O ölçüm gelince uzay genişletilebilir.

---

## 6. Karar için gereken **eksik ölçüm**

| # | ölçüm | durum |
|---|---|---|
| 1 | `matrix_alpha0` serbest bırakılınca koşul sayısı | **ölçülmedi** |
| 2 | `Y0`'nın görünür olduğu `t` (iki uçlu uzun koşu) | **ölçülmedi** |
| 3 | Hera'nın `f_boulder` belirsizliği (dış kaynak) | girilmedi |

**1 olmadan S1 kapatılmamalı:** tek parametreye indirmek koşullanmayı
düzeltiyor mu, yoksa yalnızca soruyu küçültüyor mu — bu ölçülebilir ve
ölçülmelidir.
