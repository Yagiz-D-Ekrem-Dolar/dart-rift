# ADR-0045 — Krater gözlenebiliri: **çap mı derinlik mi?**

**Tarih:** 2026-08-09
**Durum:** **YENİDEN AÇILDI** (§8) — S2'yi eleyen ölçüm **bozuk bir çıkarıcıyla** yapılmıştı; düzeltilince derinlik yakınsıyor.
**İlgili:** [ADR-0039](ADR-0039-krater-olcutu-yanliliktan-ayristirilir.md) ·
FAZ 4.6 · [rapor A11/A13](../FAZ4-SIKINTI-RAPORU.md)

---

## 1. Karar gerektiren şey

`GOZLENEBILIRLER = ("beta", "krater_capi", "ejekta_kutle_kesri")`.

Ortadaki **çap**. Ölçüldü ki üretim sahnesinde **özdeş `0`** okuyor.

Bunun sonucu **öngörülebilir**: `fit_surrogate` sabit sütunu `sabit=True`
ile işaretler, `guvenilir=False` döner ve `faz46_sentetik_kurtarma.py`
**DURDURULDU** diyerek durur. Yani FAZ 4.6 bugün başlatılsa, GPU saatleri
harcandıktan sonra **bilinen** bir sebeple duracak.

> Bu ADR o durmayı önlemek için değil — durmak **doğru** davranış.
> Karar, gözlenebilirin **ne olacağı**.

---

## 2. Ölçümler

### 2a. Çap neden `0`

`depth_threshold = 0,05`, `R`'nin kesri: `0,05 × 82 = 4,10 m` sapma
istiyor. DART kraterinin **kendi derinliği** kadar.

| eşik | `D = 20` gerçek | `D = 40` gerçek | kratersiz sahnede **hayalî** |
|---|---|---|---|
| 0,05 (`4,10 m`) | `0` — kaçırıyor | 14,83 | yok |
| 0,005 (`0,41 m`) | 19,13 | 28,32 | 6,93 *(0,5 m gürültüde)* |
| 0,002 (`0,16 m`) | 19,13 | 28,32 | 11,99 |

### 2b. Derinlik ölçülebiliyor (A13'ten sonra)

`n_theta = 1024` + `ejekta_yaricap_carpani = 1.05` ile, gerçek aşama-2
sahnesinde:

| gerçek | ölçülen |
|---|---|
| 2 m | 2,46 |
| 5 m | 4,93 |
| 10 m | 7,48 |

Gürültü tabanı **`0,43 m`**; `2 m` kraterde pay **`5,7×`**.

---

## 3. Seçenekler

### S1 — `krater_capi` kalsın, eşik `0,005`'e çekilsin

**Artı:** Hera'nın gerçekten ölçeceği büyüklük **çap**. FAZ 5'te gerçek
veriye bağlanacak gözlenebilir bu.

**Eksi:** Çıktı **kaba nicemli** (`D = 20 → 19,13`, `D = 40 → 28,32`:
iki ayrık düzey). `D = 40`'ta **`%29` düşük** yanlı. Ve `0,5 m` yüzey
gürültüsünde **hayalî `6,93 m` çap** üretiyor; üretim koşusunun yüzey
gürültüsü **ölçülmedi**.

### S2 — `krater_derinlik`e geçilsin

**Artı:** Ölçülebiliyor, doğrusal, gürültü payı `5,7×`.

**Eksi:** **Hera derinliği bu kesinlikte vermeyecek.** G4-C bu
gözlenebilirle geçerse, geçtiği şey FAZ 5'te **kullanılamayan** bir
kurtarma olur — kapının içi boşalır. ADR-0040'ın *"kriter
düşebilmelidir"* ilkesinin tersi: ölçülemeyen bir kriterle geçmek.

### S3 — İki gözlenebilirle yürünsün (`beta`, `ejekta_kutle_kesri`)

**Artı:** İkisi de ölçülüyor ve ikisi de gerçek veriye bağlanabilir
(`β` periyot değişiminden; ejekta kütlesi gözlemlerden).

**Eksi:** Üç parametre (`boulder_alpha0`, `Y0`, `f_boulder`) iki
gözlenebilirle **eksik belirlenmiş**. C1 (*"parametre kapsaması 3/3"*)
büyük olasılıkla **düşer** — ama düşmesi *dürüst* bir düşüş olur.

---

## 4. Eğilimim: **S3**, S1'i ölçüme bağlı olarak açmak üzere

Gerekçe: **hangi seçenek yanlış bir şeyi doğru göstermez** sorusu.

- S1 hayalî krater riski taşıyor ve o riskin büyüklüğü **ölçülmedi**.
- S2 geçen bir kapı üretir ama kapının ölçtüğü şey FAZ 5'te yok.
- S3 muhtemelen **düşer** ve düşmesi bilgi taşır: *"üç parametre iki
  gözlenebilirle ayrılamıyor"* sonucu, sahte bir geçişten değerlidir.

S1'i açmanın **ölçülebilir** şartı var: üretim koşusunun yüzey
gürültüsü `< 0,2 m` ise `0,005` eşiği hayalî çap üretmiyor. O sayı
ölçülünce bu ADR yeniden açılmalı.

---

## 5. Karar için gereken **eksik ölçüm**

| # | ölçüm | durum |
|---|---|---|
| 1 | üretim koşusunun **yüzey gürültüsü** | **ölçülmedi** |
| 2 | gerçek koşuda çapın **çözünürlüğü** | **ÖLÇÜLDÜ** (aşağıda) |
| 3 | Hera'nın çap belirsizliği (dış kaynak) | girilmedi |

### 2 kapandı: çap **iki seviyeli**

`faz48_v2` (`t = 5 s`, düzeltilmiş ayarlar, 82 örnek):

| büyüklük | benzersiz değer |
|---|---|
| **çap** | **2** — `6,93` (21 kez), `12,00` (61 kez) |
| derinlik | 74, ama `19` sıçrama `> 0,5 m`, en büyüğü `2,43 m` |

Çap `~1 bit` bilgi taşıyor. Üç parametreyi bir bitle ayırmak mümkün
değil; **S1 bu çözünürlükte elenmiştir** — hayalî krater riski yüzünden
değil, taşıdığı bilgi yetersiz olduğu için.

### S2 de elendi: derinlik **yakınsamıyor**

`faz48_v2`'nin kaydedilmiş son durumunda (`t = 5 s`) aynı duruma 18
farklı ayar uygulandı:

| `n_theta` | `n_bins = 6` | `8` | `12` |
|---|---|---|---|
| 256 | 11,84 | 14,19 | 11,96 |
| 1024 | 8,73 | **13,92** | 16,54 |
| 4096 | 7,32 | 7,45 | 13,94 |

Derinlik **`7,30` – `16,62 m`** (2,3 kat), çap `5,62` – `13,85` (2,5 kat).

**Hiçbir yönde yakınsama yok:**

* `n_bins` 6 → 8 → 12 (`n_theta = 1024` sabit): `8,73 → 13,92 → 16,54`
* `n_theta` 256 → 1024 → 4096 (`n_bins = 8` sabit): `14,19 → 13,92 → 7,45`

> Yakınsamayan bir sayı **ölçüm değildir**. Kutulamayı sıklaştırınca
> değişmeye devam ediyorsa, ölçülen şey kraterin derinliği değil
> **kutulamanın kendisidir**.

Ejekta süzgeci `t = 5 s`'de artık fark yaratmıyor (`< %1`) — beklendiği
gibi, ejekta çoktan uzaklaşmış. Süzgeç erken zamanların ilacıydı.

---

## 6. Karar: **S3**

Üç seçenekten ikisi **ölçümle** elendi:

| | eleme gerekçesi |
|---|---|
| S1 (çap) | 82 örnekte **2 değer** → `~1 bit` |
| S2 (derinlik) | ayarlara göre **2,3 kat** değişiyor, yakınsamıyor |
| **S3** (iki gözlenebilir) | ayakta |

FAZ 4.6 **`β` + `ejekta_kutle_kesri`** ile yürüyecek. Üç parametre iki
gözlenebilirle eksik belirlenmiş; **C1 (3/3 kapsama) düşecek** ve bu
düşüş **dürüst**: sahte bir üçüncü gözlenebilirle geçmekten iyidir
(ADR-0040, *"kriter düşebilmelidir"*).

> Kalan eksik ölçüm (yüzey gürültüsü, Hera belirsizliği) artık kararı
> **değiştirmiyor**: iki seçenek de eşiğe bakmadan elendi. O yüzden ADR
> kapatılabilir.

**Yeniden açma şartı:** çarpma bölgesinde yüzey çözünürlüğü
`s ≲ 1 m`'ye inerse (şu an `3,5 m`) her iki eleme de yeniden ölçülmeli.


---

## 7. DÜZELTME — S3'ü **ölçmeden** seçmişim (aynı gün)

§6'da S1 ve S2'yi ölçümle eledim ve geriye kalanı seçtim. **S3'ün
kendisini denetlemedim.** Yirmi dakika sonra denetledim:

```
kacan kutle          = 579.4000000000001 kg
mermi kutlesi        = 579.4000          kg
oran                 = 1.000000
```

`ejekta_kutle_kesri` **merminin kendisidir**. Hedeften kaçan madde
`t = 5 s`'de tam olarak **sıfır**. Mermi kütlesi DART görevinin sabiti;
`θ`'nın hiçbir bileşeni onu değiştirmez.

> Eleme yöntemim kusurluydu: *"ikisi elendi, üçüncü ayakta"* dedim ama
> ayakta olduğunu **varsaydım**. Elemek ile seçmek aynı kanıt standardını
> ister.

### Geriye kalan

| gözlenebilir | durum | gerekçe |
|---|---|---|
| `krater_capi` | **ölü** | 82 örnekte 2 değer |
| `krater_derinlik` | **ölü** | ayarlara göre 2,3 kat, yakınsamıyor |
| `ejekta_kutle_kesri` | **ölü** | tam olarak mermi kütlesi |
| `beta` | **ölçülüyor** | FAZ 4.11 sürüyor |

**Üç parametre, en iyi ihtimalle bir gözlenebilir.** G4-C'nin
*"3/3 parametre kurtarıldı"* ölçütü bu ileri modelle **karşılanamaz** —
`β` duyarlı çıksa bile bir sayı üç bilinmeyeni belirlemez.

Bu, FAZ 4.6'nın neden bitmediğinin cevabıdır: eksik olan koşu süresi ya
da çözünürlük değil, **gözlenebilir sayısı**.

### Karar bu ADR'nin kapsamını aşıyor

Gözlenebilir vektörünün yeniden tasarlanması ayrı bir ADR gerektirir.
Bu ADR **krater** gözlenebilirini karara bağladı (ikisi de ölü) ve o
kısmı geçerlidir.


---

## 8. YENİDEN AÇILDI — S2'yi eleyen ölçüm **bozuk çıkarıcıyla** yapıldı

§5'te derinliği *"ayarlara göre 2,3 kat, yakınsamıyor"* diye eledim.
O tablo `kutulama = "kuresel"` ile alındı ve rapor A16 gösterdi ki o kip
dolu cisimde **hiçbir ayarda** çalışmıyor:

* küçük `n_theta` → koniye `5-14` parçacık düşer,
* büyük `n_theta` → ızgara parçacık sayısını geçer, *"yüzey = bütün
  cisim"* olur (`n_theta = 1024`'te `9970/10410`, medyan `r = 66,9`).

Yani elediğim şey **derinlik değil, bozuk bir ölçüm**di.

### `kutulama = "eksen"` ile aynı sahne

Küresel ızgara hiç kullanılmıyor; parçacıklar çarpma ekseninden açıya
göre eşit açılı halkalara bölünüyor. Aynı sahne, aynı çözünürlük
(`λ = 2`), hiçbir ek maliyet yok:

| gerçek | `nb = 4` | `nb = 6` | `nb = 8` |
|---|---|---|---|
| 2 m | 1,844 | 1,977 | **2,015** |
| 5 m | 4,340 | 4,793 | **4,882** |
| 10 m | 8,499 | 9,486 | **9,660** |

Kutu sayısı arttıkça gerçeğe **tek düze** yaklaşıyor. Gürültü tabanı
`0,25 m` (yüzey gürültüsü `0,2 m` iken). Hayalî çap üretmiyor.

### Güncel durum

| gözlenebilir | durum |
|---|---|
| `krater_capi` | **ölü** — 2 değer; yeni kipte de çap = eşik geçişi, çap değil |
| **`krater_derinlik`** | **YAŞIYOR** — yakınsıyor, `%±3` yanlı, tabanı `0,25 m` |
| `ejekta_kutle_kesri` | **ölü** — tam olarak mermi kütlesi (§7) |
| `beta` | FAZ 4.11 ölçüyor |

Yani gözlenebilir sayısı `1`'den **`2`'ye** çıktı (`β` + derinlik).
Üç parametre için hâlâ eksik ama G4-C artık *"hiç ölçülemez"*
durumunda değil.

### Ön koşul — kayıt altında

`"eksen"` kipi **yüzeye yığılmış** örnek istiyor. Tekdüze dolu bir
cisimde eksik okuyor (`5 m → 3,48`), çünkü dar konide yüzeye yakın
parçacık yok. Üretim sahnesi yerel incelme kullandığı için koşul
**sağlanıyor**; sağlanmadığı yerde kip kullanılmamalı. Test bunu
kilitliyor.
