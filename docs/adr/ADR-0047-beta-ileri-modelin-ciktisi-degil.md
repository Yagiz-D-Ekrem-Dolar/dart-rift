# ADR-0047 — `β` bu ileri modelin **çıktısı değil**: ne yapılacak

**Tarih:** 2026-08-21
**Durum:** **ÖNERİ** — ölçüm tarafı kapandı (§2), **kapsam kararı kullanıcının**
**İlgili:** [ADR-0028](ADR-0028-uzun-kosu-kararliligi.md) ·
[ADR-0027](ADR-0027-grady-kipp-hasar-modeli.md) ·
[ADR-0040](ADR-0040-kriter-dusebilmelidir.md) ·
[ADR-0046](ADR-0046-cikarim-uzayi-olculebilir-olana-indirilir.md) ·
[KAYIT-051](../defter/KAYIT-051_2026-08-21_beta-cozunurluk-artigi.md)

---

## 1. Karar gerektiren şey

Motor `β = 1,4112` üretiyor; gözlem `3,2225` (yayımlanan `3,6`).
A17 bu farkı üç turdur kovalıyordu. Bu turda fark **açıklandı** ve
açıklama bir parametre değil:

> `β`'nın **tamamı** merminin geri sekmesi. Hedef ejektasının katkısı
> **tam sıfır** — ve sekme çözünürlük arttıkça **kayboluyor**.

Yani model `β`'yı *"küçük üretmiyor"*; **hiç üretmiyor**, ve şu anki
değeri bir ayrıklaştırma artığı.

---

## 2. Ölçümler — parametre tarafı **kapandı**

| aday | nasıl elendi | kanıt |
|---|---|---|
| koşu süresi | `t_end` `0,2 -> 600 s` (`3000×`), `β` **bit düzeyinde aynı** | iş `1506765` |
| yerçekimi | `t = 100 s`'de `%0,14`; zayıf cisimde `%0,001` | iş `1501241/2`, `1515196` |
| matris `Y0` | `1 -> 2,15e6 Pa` (6 mertebe) | iş `1506779`, FAZ 4.12 |
| **blok `Y0`** | `1e7 -> 1 Pa`, yerçekimi açık | **iş `1515196`** |
| hasar (ADR-0027) | `Δβ = 5,9e-6`; `11 183` parçacığın `3`'ü kırılıyor | yerel, 21.08 |
| gözeneklilik | katı sahnede `+%7,5` — gereken `2,3×` | rapor A17 |
| `λ₂` (hedef ızgarası) | `Δβ = 0,000843` | G4-B1 |

Ve **yakınsamamış tek yön** `β`'yı gözlemden **uzaklaştırıyor**:

| `λ₁` | `A1` | `β` |
|---|---|---|
| — | `0,215` | `1,617583` |
| `19` | `2,039` | `1,411216` |
| `38` | `4,078` | `1,185066` |

Ardışık farklar `-0,206`, `-0,226`: azalma yavaşlamıyor, limit
**`β -> 1`**.

Eşlik eden ölçüm, mekanizmanın neden yok olduğunu gösteriyor:

| | |
|---|---|
| merminin özgül `KE`'si | `1,888e7 J/kg` |
| iç enerjiye dönen | **`%29,7`** |
| sahnedeki **en yüksek** `u` | `5,644e6` — ve o **merminin** üstünde |

**Hedef güçlü bir şok hiç görmüyor.** Kazı akışı başlamıyor.

---

## 3. Bunun kapı sonucu: `G4-B1` **düşüyor**

`B1` *"ardışık çözünürlükte `β` farkı `< 0,1`"* diyor ve `0,000843`
ile geçmişti. O tarama `λ₂`'yi değiştiriyordu — oysa `β`'yı üreten
tek şey **mermi**:

| yön | `Δβ` | eşik `0,1` |
|---|---|---|
| `λ₂` (hedef) | `0,000843` | geçti |
| **`λ₁` (mermi)** | **`0,226150`** | **düştü**, `268` kat |

> Kapı raporu **GEÇİLDİ** diyor. Bu ADR kabul edilirse `B1` yeniden
> değerlendirilmeli ve rapor **yeniden üretilmelidir**; ADR-0040
> gereği bir ölçütün düşmesi bastırılmaz.

---

## 4. Seçenekler

### S1 — Krater bölgesini **inceltmek**

Ejekta perdesi kraterin üst birkaç metresinden fırlar; `λ₂ = 2` ile
orada fırlatma tabakası `1–2` parçacık kalınlığında.

**Artı:** Ölçülebilir ve **şu anda ölçülüyor** (iş `1515233`,
`λ₂ = 4`). Doğruysa yol açık.
**Eksi:** Ensemble maliyeti. `λ₂ = 2 -> 4` parçacık sayısını `~8×`,
`dt`'yi `1/2` yapar: tek nokta `~16×`. `40` noktalık ensemble
`λ₂ = 4`'te bugünkü bütçeyi aşar.

### S2 — **Model-form** değişikliği

Eksik olan mekanizmayı eklemek: merminin parçalanması/aşınması,
serbest yüzeyde kazı akışının doğru temsili, ya da yüzeye yakın
parçacık bölme.

**Artı:** Bilimsel iddia korunur — model gerçekten `β` üretir.
**Eksi:** Bu bir **araştırma programı**, bir düzeltme değil. Her
adayın kendi doğrulaması gerekir (ADR-0027 hasar için 32 test
istemişti).

### S3 — `β`'yı **gözlenebilir olmaktan çıkar**

Çıkarım `krater_derinlik` üzerine kurulur (`%20,7` yayılım, en güçlü
gözlenebilir); `β` **rapor edilir ama ölçüt değildir**.

**Artı:** Bugünkü ölçümlerle **tutarlı** ve dürüst. G4-B'nin `β`
ölçütleri ADR-0040'ın istediği gibi **düşer**, gizlenmez.
**Eksi:** Bilimsel iddia daralır: *"momentum aktarımını çıkardık"*
değil **"krater morfolojisini çıkardık"**. DART'ın asıl ölçtüğü
büyüklük `β` ve onu bırakmak ağır bir kayıp.

### S4 — `β` için **dış ölçekleme** kullan

`β`'yı simülasyondan değil, krater/ejekta ölçeklemesinden (pi-grubu)
türet; simülasyon krater ve iç yapıyı verir.

**Artı:** İki taraf da yapabildiği işi yapar.
**Eksi:** *"Uçtan uca ileri model"* iddiası biter; zincirin ortasına
kalibre edilmiş bir ilişki girer ve belirsizliği ayrıca taşınmalıdır.

---

## 5. Eğilimim: **S3**, S1'in sonucunu bekleyerek

Gerekçe: S3 bugün ölçülmüş olanla çelişmeyen tek konum. S1 hâlâ
açık ve **ucuz** biçimde sınanıyor; sonucu S3'ü geri alabilir.
S2 doğru hedef ama bu fazın işi değil. S4 kapsam kararını
bugünden vermek zorunda bırakır.

S3'ü seçmek S1/S2'yi kapatmıyor: `β` ölçüt olmaktan çıkınca da
**raporlanmaya** devam eder, ve mekanizma eklendiğinde geri gelir.

---

## 6. Karar için gereken **eksik ölçüm**

| # | ölçüm | durum |
|---|---|---|
| 1 | `λ₂ = 4` krater inceltmesi hedef ejektasını açıyor mu | **koşuyor** (iş `1515233`) |
| 2 | `λ₁ = 55` dördüncü yakınsama noktası | koşuyor (yerel) |
| 3 | `λ₂ = 6` üçüncü nokta — yalnızca 1 "kısmi" çıkarsa | gerekmeyebilir |

**1 olmadan S3 kapatılmamalı:** eksik olanın çözünürlük mü mekanizma
mı olduğu ölçülebilir ve ölçülüyor.
