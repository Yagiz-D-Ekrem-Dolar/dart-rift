# ADR-0045 — Krater gözlenebiliri: **çap mı derinlik mi?**

**Tarih:** 2026-08-09
**Durum:** **ÖNERİ** — karar verilmedi
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

Geriye **S2** (derinlik, `±%18` sıçramalı) ve **S3** (iki gözlenebilir)
kalıyor. Eğilimim hâlâ **S3**; S2'nin `±%18`'i ölçülmüş bir gürültü ve
`β`'nın bit düzeyinde kararlılığıyla kıyaslanınca zayıf kalıyor.

**1 olmadan ADR yine de kapatılmamalı** — ama artık kapanışa bir ölçüm
daha yakın.
