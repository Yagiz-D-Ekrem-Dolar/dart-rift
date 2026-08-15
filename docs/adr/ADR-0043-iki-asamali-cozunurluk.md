# ADR-0043 — Mermiyi çözmek için **iki aşamalı** çözünürlük

- **Durum:** **ÖNERİLDİ** (kilitli değil — karar proje sahibinin)
- **Tarih:** 2026-08-08
- **Tetikleyen:** G4-A1 **düştü** —
  [KAYIT-041](../defter/KAYIT-041_2026-08-08_yerel-gpu-ve-mermi-cozulmemis.md)
- **İlgili:** [ADR-0026](ADR-0026-mermi-cozunurlugu.md) (mermi çözünürlüğü),
  [ADR-0041](ADR-0041-yerel-incelme-yaklasimi.md) (A′)

---

## 1. Sorun — ölçülmüş

G4-A1 (`mermi çapı / yerel aralık ≥ 2`) **üç kurulumda da düştü**:

| kurulum | yerel aralık | `A1` |
|---|---|---|
| `s7_λ2` | 3,500 m | **0,215** |
| `s7_λ3` | 2,333 m | **0,322** |
| `s5_λ2` | 2,500 m | **0,300** |

`A1 ≥ 2` için `λ = 18,6` (kütle oranı **6478:1**) gerekiyor. Bedeli
ayrıştırıldı:

| bileşen | çarpan (`λ=2`'ye göre, `r_iç = 3 m`) |
|---|---|
| parçacık sayısı | **1,13** |
| **`dt` cezası (CFL)** | **9,3** |

> İnce bölge ne kadar küçültülürse küçültülsün `dt` yine `λ` kat iner ve
> **bütün** parçacıklar o adımla ilerler. Tek global adımlı bir şemada
> bu bedel **küçültülemez**.

---

## 2. Belirleyici gözlem: **bağlanma fazı çok kısa**

| büyüklük | değer |
|---|---|
| mermi çapı | 0,751 m |
| çarpma hızı | 6144,9 m/s |
| **mermi kendi çapını geçme süresi** | **`1,22e-4 s`** |
| `1e-3 s`'de şokun aldığı yol (`c ≈ 3000`) | 3,0 m = **4 mermi çapı** |
| ensemble koşu süresi | `~1 s` |

> **Mermiyi çözmenin gerektiği süre, koşu süresinin `~10⁴`'te biri.**

Yani pahalı çözünürlük **sürekli** taşınmak zorunda değil.

### ⚠ `~1 s` **ölçülmüş değil** — bütün §3 buna dayanıyor (2026-08-09)

Tablodaki *"ensemble koşu süresi `~1 s`"* satırı bir **varsayım**.
§3'ün bütün bedel tablosu (`9,73` GPU-günü) ve §4'ün *"`%4,7`'ye mal
oluyor"* sonucu **o sayıdan** türüyor.

Ölçülenler onu **desteklemiyor** (rapor A11/A12):

| ölçüm | `t = 0,174 s`'de |
|---|---|
| kaçan kütle | `579,44 kg` = **merminin kendisi** (`579,40 kg`) |
| krater derinliği | `0,035 m` = parçacık aralığının **`%1`**'i |
| kaçış hızını aşan hedef parçacığı | **18 / 10 380** |

Yani `1 s`'lik bir koşu **kraterin oluşmasına bile yetmiyor**;
ejektanın `β`'ya katkısı `+0,08` (`%5`).

> **Gereken süre ölçülüyor** (`scripts/faz410_firlatma_suresi.py`,
> balistik `β`'nın durulması). Sonuç `1 s`'ten büyük çıkarsa §3'ün
> bedel tablosu **orantılı olarak** büyür ve §4'ün önerisi yeniden
> değerlendirilmelidir.
>
> `100 s` çıkarsa `9,73` GPU-günü `~970` olur — bütçenin `32` katı.

---

## 3. Üç seçenek — ölçülen bedeller (300 koşu, GPU-günü)

| # | seçenek | aşama-1 | aşama-2 | **toplam** | `A1` |
|---|---|---|---|---|---|
| 1 | tek aşama, `λ=2` | — | 9,73 | **9,73** | **0,21 ✘** |
| 2 | tek aşama, `λ=19`, `r_iç=3 m` | — | 96,13 | **96,13** | 2,04 ✔ |
| **3** | **iki aşama**, `t₁ = 1e-3 s` | **0,096** | 9,73 | **9,82** | **2,04 ✔** |

`t₁` duyarlılığı:

| `t₁` | aşama-1 | **toplam** | `λ=2`'ye göre |
|---|---|---|---|
| `1e-4 s` | 0,010 | 9,74 | **+%0,1** |
| **`1e-3 s`** | 0,096 | **9,82** | **+%0,9** |
| `1e-2 s` | 0,961 | 10,69 | +%9,9 |

> **Mermiyi çözmek `%1`'e mal oluyor** — `10×`'a değil.

---

## 4. Öneri

> **Seçenek 3.** `t₁ ≈ 1e-3 s`'ye kadar `λ ≈ 19` ve `r_iç ≈ 3 m` ile
> koş; sonra **kabalaştır** ve `λ = 2` ile devam et.

`t₁` bir tahmin **değil**, ölçülecek: aşama-1 ancak **bağlanma bittikten**
sonra kesilebilir. Ölçütü FAZ 4.5'in durulma ölçütüyle aynı
(`settling_time`), ama `β` yerine **mermi parçacıklarının hızı**: mermi
hedefle aynı hıza geldiğinde bağlanma bitmiştir.

### 4a. ⚠ `t₁ = 1e-3 s` **ölçüldü ve düştü** (2026-08-08)

> Yukarıdaki `t₁ ≈ 1e-3 s` **yanlış çıktı.** Silinmiyor (RULES.txt);
> düzeltme burada.

`scripts/faz43c_baglanma_suresi.py` ile `λ=19`, `r_iç=3 m`,
`N = 11 871`, `A1 = 2,04` sahnesinde ölçüldü:

```
u = |<v>_mermi − <v>_yakın hedef| / v_çarpma

u(t→0)     = 0,791
u(2e-3 s)  = 0,337     <-- ADR'nin önerdiği t1'in İKİ KATINDA
durulma    = DÜŞTÜ (eğilim %8,56, yarım-pencere %4,79; tol %2)
t1         = nan  (pencerede durulma yok)
```

`1e-3 s`'de mermi hedefe göre hâlâ çarpma hızının **üçte biriyle**
gidiyor ve `u` **düşmeye devam ediyor**. §2'nin *"bağlanma fazı çok
kısa"* akıl yürütmesi — mermi çapını `1,22e-4 s`'de geçiyor, `1e-3
s`'de şok `4` çap yol alıyor — **bağlanmanın bittiğini göstermiyor.**
Şokun mermiyi geçmesi ayrı şey, momentumun aktarılıp hızların
eşitlenmesi ayrı şey.

**Bunun §3'e etkisi doğrudan:** aşama-1 bedeli `t₁` ile doğrusal.

| `t₁` | aşama-1 | toplam | `λ=2`'ye göre | durum |
|---|---|---|---|---|
| `1e-3 s` | 0,096 | 9,82 | +%0,9 | ✘ **yetersiz (ölçüldü)** |
| `1e-2 s` | 0,961 | 10,69 | +%9,9 | ? ölçülüyor |
| `1e-1 s` | 9,61 | 19,34 | **+%99** | ? önerinin sınırı |

> `t₁ ≳ 1e-1 s` çıkarsa **iki aşama seçeneği çöker** ve §6'nın
> *"bireysel/blok zaman adımı"* alternatifi tek yol kalır.

### 4b-öncesi ek: uzun koşu bitti — **`t₁ = 4,77e-3 s`**

`t_end = 5e-2 s` (25 kat uzun, 93 örnek) koştu ve `u` **duruldu**:

| | |
|---|---|
| `u` en düşük | `0,1177` (`t = 3,7e-4 s`) |
| `u` **plato** | `0,4093` |
| durulma penceresi | `[0,0353 , 0,0500] s`, 28 nokta |
| eğim kayması | `%0,067` (tol `%2`) ✔ |
| yarım-pencere farkı | `%0,035` ✔ |
| plato pencereden geniş | **evet** — uç-nokta yakınlığı değil, gerçek plato |
| **`t₁` (ölçülen)** | **`4,767e-3 s`** |

> **`u` sıfıra inmiyor, `0,409`'da düzleşiyor** — ve oraya *aşağıdan*
> yükselerek geliyor (92 adımın 16'sı artış). §4'ün *"mermi hedefle
> aynı hıza geldiğinde"* cümlesi bu yüzden **yanlıştı**. Doğrusu:
> momentum alışverişi bitince iki topluluk balistikleşir ve fark
> **sabitlenir**; sabitlendiği değerin sıfır olması gerekmez.

**Bedele etkisi — öneri ayakta kalıyor:**

| `t₁` | aşama-1 | toplam | `λ=2`'ye göre |
|---|---|---|---|
| `1e-3 s` (ADR'nin tahmini) | 0,096 | 9,83 | +%0,99 |
| **`4,767e-3 s` (ölçülen)** | **0,458** | **10,19** | **+%4,70** |
| `1e-2 s` | 0,961 | 10,69 | +%9,87 |

> Tahmin **4,8 kat** şaşmıştı ama sonuç niteliksel olarak değişmedi:
> mermiyi çözmek `%1` değil **`%4,7`**'ye mal oluyor. Bütçenin
> (`~30` GPU-günü) hâlâ **çok altında**.

---

## 4b. Kurulum engeli **kaldırıldı** (2026-08-08)

`refine_scene` iki **tam** sahne kurup birleştiriyordu ve `λ = 19`'da bu
**imkânsızdı**:

| `λ` | tam ince sahne `N` | bellek |
|---|---|---|
| 2 | 76 180 | 0,02 GB |
| 6 | 2 056 860 | 0,62 GB |
| **19** | **65 314 837** | **19,6 GB** |

Oysa gereken `r_iç = 3 m` içinde `~1500` parçacık — yani `%99,998`
kurulup atılıyordu.

`refine_scene_local` yazıldı: ince kafes yalnızca çarpma noktası
çevresindeki **kutuda** kuruluyor. Ölçüldü:

| `λ` | `s_ince` | `A1` | `r_iç` | `n_ince` | `N` | kütle sapması | süre |
|---|---|---|---|---|---|---|---|
| 2 | 3,5000 | 0,21 | 25 m | 952 | 11 183 | 1,3e-04 | 0,3 s |
| 6 | 1,1667 | 0,64 | 6 m | 389 | 10 734 | 1,8e-05 | 0,1 s |
| **19** | **0,3684** | **2,04 ✔** | **3 m** | **1524** | **11 871** | **2,0e-05** | **0,5 s** |

> **`λ = 19` artık kurulabiliyor** — `0,5` saniyede, `11 871` parçacıkla.
> Aşama-1'in kurulumu bir engel değil.

`α₀`/`Y₀` en yakın kaba parçacıktan örnekleniyor ki **kaya blokları
silinmesin** (`f_boulder` çıkarımın üç parametresinden biri). Bu bir
yaklaşımdır: blok sınırları ince kafeste kaba çözünürlükte kalır;
`diagnostics`'e yazılı, **ölçülmedi**.

---

## 4c. Kabalaştırma **ölçüldü** — korunum geçti, **aktarım düştü** (2026-08-09)

`src/dartrift/setup/coarsen.py` yazıldı, `scripts/faz43d_kabalastirma.py`
ile `λ=19`, `r_iç=3 m` gerçek sahnesinde ölçüldü. Hedef siteler
**aşama-2'nin kendi ince kafesi** (`λ=2` → `3,5 m`).

| `t₁` [s] | kütle | momentum | enerji | ısıya dönen | **atama mesafesi** |
|---|---|---|---|---|---|
| `1e-4` | `3,9e-14` | `2,8e-16` | `1,8e-16` | `%98,2` | `0,97 s₂` |
| `1e-3` | `3,9e-14` | `3,4e-15` | `5,7e-16` | `%93,2` | `0,97 s₂` |
| **`4,77e-3`** (ölçülen `t₁`) | `3,9e-14` | `1,0e-15` | `7,4e-16` | **`%99,3`** | **`4,35 s₂`** |
| `1e-2` | `3,9e-14` | `6,1e-15` | `1,5e-15` | **`%99,9`** | **`10,16 s₂` = 35,6 m** |

### §5'in istediği **karşılandı**

Kütle, momentum ve enerji **üçü de** `≤ 6e-15` — makine hassasiyeti.
Naif yolun `%38` momentum kaybettiği ayrıca ölçüldü
(`tests/test_coarsen.py`). Yani §5'in korunum şartı **sorun değil**.

### Ama aktarımın kendisi **çalışmıyor**

Ölçmeyi ADR'nin istemediği, sonradan eklenen iki tanı düşürüyor:

1. **Atama mesafesi `t₁`'de `4,35` hücre, `1e-2 s`'de `10,2` hücre
   (`35,6 m`).** Hedef siteler `r_iç = 3 m` içinde **sabit** duruyor,
   oysa madde `t₁`'e kadar oradan **çıkmış** oluyor. Aktarım `35 m`
   öteden kütleyi `3 m`'lik bir topa **ışınlıyor**. Korunum bunu
   göremiyor — toplamlar tutuyor.
2. **Isıya dönen kinetik `t₁`'de `%99,3`.** Ve `t₁` büyüdükçe
   **kötüleşiyor** (`%93,2 → %99,3 → %99,9`), çünkü akış hızla genişleyen
   bir radyal akışa dönüşüyor ve onu ortalamak yok ediyor.

> **`t₁` iki şartı aynı anda sağlayamıyor.** Bağlanmanın bitmesi için
> `t₁` **büyük** olmalı (`4,77e-3 s`); aktarımın maddeyi ışınlamaması
> için **küçük** olmalı (`≤ 1e-3 s`). Aralık **boş**.

### Sıkıştırma oranı `r_iç` ile **değişmiyor**

`r_iç`'i büyütmek akla geliyor (daha çok site). Ölçüldü — işe yaramıyor:

| `r_iç` | aşama-1 `N` | site | **ince/site** | aşama-1 | toplam | `λ=2`'ye göre |
|---|---|---|---|---|---|---|
| 3 m | 11 871 | 2 | 1164 | 0,46 | 10,19 | +%4,7 |
| 6 m | 22 555 | 14 | 930 | 0,87 | 10,60 | +%8,9 |
| 9 m | 51 359 | 51 | 820 | 1,98 | 11,71 | +%20,4 |
| 12 m | 106 275 | 120 | 806 | 4,10 | 13,83 | +%42,1 |

Sıkıştırma `~857`'de sabit — çünkü **tanım gereği** `(λ₁/λ₂)³ = 9,5³`.
`r_iç` yalnızca **bedeli** büyütüyor.

### Bu ADR'yi öldürmüyor, ama **§4'ün önerisini** öldürüyor

Ölçülen şey *"iki aşama olmaz"* değil; **bu aktarım olmaz**. Kusur
tanımlanabilir: hedef siteler aşama-2'nin **başlangıç** kafesinden
alınıyor, yani **Euler**'ci. Maddenin peşinden gitmiyor.

> Çalışabilecek sürüm **Lagrange**'cı olmalı: hedef siteler `t₁`
> anındaki **mevcut** ince parçacık dağılımından üretilmeli (örneğin
> `s₂` aralıklı bir kafes, o anki bulutun sınırlayıcı kutusuna
> oturtulmuş), aşama-2'nin `t=0` kafesinden değil.

Bu **ölçülmedi** ve ayrı bir iş. §7'ye madde 5 olarak eklendi.

---

## 4d. Lagrange'cı aktarım **yazıldı ve ölçüldü** — engel **kalktı** (2026-08-09)

`sites_from_cloud`: `t₁` anındaki bulut, kenarı `a = s₂/2^{1/6}` olan
kübik ızgaraya bölünüyor; **dolu** hücrelerin merkezleri site oluyor.
Her parçacık kendi hücresinin merkezine `≤ a√3/2` uzaklıkta —
atama mesafesi **yapı gereği** sınırlı.

> `a = s₂/2^{1/6} ≈ 0,8909·s₂`, çünkü aşama-2 FCC ve parçacık hacmi
> `s₂³/√2`; kübik hücrede hacim `a³`. Eşitlenmezse aktarılan parçacıklar
> `%41` daha büyük hacim temsil ederdi.

**İki kip, aynı durumda** (`λ=19`, `r_iç=3 m`, yerel RTX 3050):

| `t₁` [s] | kip | site | kütle | momentum | enerji | **ısıya dönen** | **atama mes.** |
|---|---|---|---|---|---|---|---|
| `1e-4` | euler | 2 | 3,9e-14 | 2,8e-16 | 1,8e-16 | `%98,2` | `0,97` |
| `1e-4` | **lagrange** | 4 | 8,0e-15 | 8,2e-16 | 3,7e-16 | `%97,1` | `0,73` |
| `1e-3` | euler | 2 | 3,9e-14 | 3,4e-15 | 5,7e-16 | `%93,2` | `0,97` |
| `1e-3` | **lagrange** | 7 | 7,9e-15 | 2,7e-15 | 3,8e-16 | `%85,9` | `0,73` |
| **`4,77e-3`** | euler | 2 | 3,9e-14 | 1,0e-15 | 7,4e-16 | **`%99,3`** | **`4,35`** |
| **`4,77e-3`** | **lagrange** | **40** | 2,1e-15 | 4,3e-16 | 3,7e-16 | **`%2,88`** | **`0,73`** |
| `1e-2` | euler | 2 | 3,9e-14 | 6,1e-15 | 1,5e-15 | **`%99,9`** | **`10,16`** |
| `1e-2` | **lagrange** | **210** | 1,6e-15 | 3,6e-15 | 1,8e-16 | **`%0,46`** | **`0,73`** |

### İki kip **zıt yönlere** gidiyor

| `t₁` | euler ısıya | lagrange ısıya |
|---|---|---|
| `1e-4` | 98,2 | 97,1 |
| `1e-3` | 93,2 | 85,9 |
| `4,77e-3` | **99,3** | **2,88** |
| `1e-2` | **99,9** | **0,46** |

> Euler'ci **kötüleşiyor**, Lagrange'cı **iyileşiyor**. Sebebi aynı olay:
> madde genişliyor. Sabit hedef ondan uzaklaşıyor; bulutu izleyen hedef
> ise giderek daha **düzgün** bir akış görüyor ve `s₂` ölçeğinde
> temsil edilebilir hâle geliyor.

### §4c'nin *"aralık boş"* sonucu **düzeldi**

Ölçülen `t₁ = 4,767e-3 s`'de Lagrange'cı aktarım:

| | euler | **lagrange** |
|---|---|---|
| ısıya dönen | `%99,3` | **`%2,88`** — `34×` iyi |
| atama mesafesi | `4,35` hücre | **`0,73` hücre` |
| korunum (üçü) | `≤ 1,0e-15` | `≤ 2,1e-15` |
| açısal kayıp (ölçekli) | `%0,007` | `%0,012` |

**`t₁`'in iki şartı artık çelişmiyor.** §4c'de kaydedilen engel,
Euler'ci aktarımın engeliydi — **yaklaşımın değil**.

### Karşılığı: aktarım parçacık sayısını **artırıyor**

Aşama-2'nin o bölgede `2` parçacığı olurdu; Lagrange'cı aktarım
`t₁ = 4,77e-3 s`'de **40**, `1e-2 s`'de **210** üretiyor. Mutlak sayı
küçük (toplam `~11 000`'in `%0,4`'ü ve `%1,9`'u), yani bedel ihmal
edilebilir. Ama **nötr değil** ve iki şey **ölçülmedi**:

1. Bu ek parçacıkların aşama-2'nin mevcut kafesiyle **dikişi**
   (`_dikis_kalitesi` bu duruma uygulanmadı).
2. `t₁` büyüdükçe site sayısı da büyüyor (`4 → 7 → 40 → 210`); bir üst
   sınır **konmadı**.

---

## 4e. Şema **uçtan uca kuruldu** (2026-08-09)

`setup/two_stage.py` + `scripts/faz48_iki_asama.py`. CPU ön uçuşu
(`λ₁=6`, `r_iç=6 m`, kısa `t`) hattı **baştan sona** koşturdu.

### Çözülen asıl sorun: **çifte sayım**

Kabalaştırılmış parçacıklar aşama-1'in ince bölgesinden geliyor;
aşama-2'nin **kendi** parçacıkları da orada. İkisi de kalırsa o
bölgenin kütlesi **iki katına** çıkar ve ADR-0030 delinir.

> Çıkarma ölçütü **Lagrange'cı**: aşama-2'nin `r_iç_aşama1` içinde
> **başlamış** parçacıkları atılır — *"bu madde aşama-1'de mi vardı"*.
> Naif yol (*"kabalaştırılmışa yakın olanı at"*) keyfî bir mesafe
> eşiği isterdi.

### Ön uçuş ölçümleri

| büyüklük | değer |
|---|---|
| korunum (kütle / momentum / enerji) | `2,8e-15` / `2,6e-16` / `1,8e-16` |
| atama mesafesi | `0,672` hücre |
| komşu medyanı (birleşik sahnede) | **229** (`<30` oranı `0,000`) |
| **bölge kütle uyuşmazlığı** | **`%2,82`** |

### Yeni bulgu: bölge kütle uyuşmazlığı `%2,82`

Aşama-1'in ince bölgesi ile aşama-2'nin **atılan** bölgesi aynı
fiziksel hacmi temsil ediyor ama **iki farklı kafesle** örneklenmiş.
Aktarım korunumu bunu **görmüyor** — o yalnızca aşama-1'in kütlesini
koruyor.

> Küçük ama **sistematik** ve tam da **krater bölgesinde** — `β` oradan
> geliyor. Mermi kütlesi (`579 kg`) hesaptan doğru şekilde çıkarılmış
> durumda; `%2,82` saf ayrıklaştırma farkı. Tanı olarak raporlanıyor,
> **düzeltilmedi**.

### Ön uçuş **iki kendi kusurumu** buldu

| kusur | önce | sonra |
|---|---|---|
| komşu tanısı yalnızca aktarılanlar arasında sayıyordu | medyan **27**, `<30` oranı **1,000** | medyan **229**, `<30` oranı **0,000** |
| `is_impactor` `state_numpy()`'dan okunmaya çalışılıyordu (o anahtar **yok**) | mermi kütlesi **hiç** çıkarılmıyordu | zorunlu parametre |

> Birincisi *"her aktarılan parçacık komşusuz"* diyordu ve paniğe
> değecek bir sayıydı — **ölçüm aracının kendisi bozuktu**.

---

## 4f. ⚠ ŞEMANIN KENDİSİ KUSURLU: `r_iç` ile `t₁` **çelişiyor** (2026-08-09)

FAZ 4.8 gerçek sahnede koştu ve **momentum kapanışı `0,690`** verdi —
yani momentumun `%69`'u kayıp. Kök neden ölçüldü:

| `t₁ = 4,767e-3 s`'de momentum | oran |
|---|---|
| **tüm sahne** | `1,000 × p_mermi` ✔ korunuyor |
| **ince bölge** (`r < 3 m`) — *aktarılan* | **`0,310`** |
| **kaba bölge** — *atılan* | **`0,690`** |

Bozulmanın yayılımı (`v > 1e-3 m/s` olan parçacıklar):

| | çarpma noktasına uzaklık |
|---|---|
| medyan | 3,04 m |
| p90 | **34,5 m** |
| en uzak | **48,6 m** |
| şok yolu `c·t₁` | 14,3 m |

> `t₁`'de bozulma `~35–48 m`'ye yayılmış; `r_iç = 3 m` bunun **onda
> biri**. Aşama-1'in ince bölgesi momentumun yalnızca `%31`'ini
> taşıyor.

### İki gereksinim **birbiriyle çelişiyor**

| gereksinim | istediği |
|---|---|
| aşama-1 **ucuz** olsun | `r_iç` **küçük** (§3: `3 m`) |
| bağlanma **bitsin** | `t₁` **büyük** (`4,767e-3 s`) |

Ama `t₁` büyüdükçe bozulma `r_iç`'in dışına taşıyor. **İki seviyeli**
bir sahnede bu ikisi aynı anda sağlanamaz.

### Bu bir uygulama kusuru **değil**, tasarım kusuru

Aktarım aşama-1'in ince bölgesini alıp aşama-2'nin **dinlenmedeki**
kaba bölgesine ekliyor. Aşama-1'in kaba bölgesi (`%69` momentum)
**atılıyor**, çünkü aşama-2'nin `3 < r < 25 m` bölgesi `3,5 m`
aralıklı — aşama-1'in orada `7 m` aralığı var, yani **daha kaba**.
Kabadan inceye geçiş **iyi tanımlı değil**.

### Çözüm: aşama-1 **üç seviyeli** olmalı

```
asama-1:  r < 3 m      lam=19   (mermi cozulmus)
          3 < r < 25 m lam=2    (asama-2 ile AYNI)
          r > 25 m     lam=1
```

O zaman aktarım yalnızca `r < 3 m`'yi kabalaştırır; gerisi **birebir**
kopyalanır ve hiçbir momentum atılmaz.

> Bedeli küçük: `dt` zaten `λ=19` çekirdeğinden geliyor; eklenen
> parçacıklar aşama-2'nin zaten sahip olduğu parçacıklar.

**`β = 1,412659` sayısı (FAZ 4.8, iki seviyeli) GEÇERSİZDİR** —
momentumun `%69`'u eksikken hesaplandı.

### Düzeltme **uygulandı ve ölçüldü** (2026-08-09)

`refine_scene_ucseviye` + `asama2_sahnesi_ucseviye`:

| | iki seviyeli | **üç seviyeli** |
|---|---|---|
| aşama-2'den atılan | 805 parçacık | **0** |
| birebir kopyalanan | — | **10 366** |
| sahne momentum hatası | — | **`1,177e-15`** |
| **momentum kapanışı** | **`6,901e-01`** | **`5,101e-15`** |

**On beş büyüklük mertebesi.** Aktarım artık yalnızca `r < r₁`'i
kabalaştırıyor; `r₁ < r < r₂` aşama-2 ile **aynı aralıkta** olduğu
için evrimleşmiş hâliyle **birebir** kopyalanıyor.

Bedeli ölçüldü:

| | değer |
|---|---|
| üç seviyeli `N` | **12 705** |
| aşama-2 `N` | 11 183 |
| oran | **`1,136×`** |
| `A1` | **2,0391** ✔ |
| `h_mermi / çap` | **0,981** ✔ |
| kurulum süresi | 0,7 s |

> `dt` zaten `λ₁` çekirdeğinden geliyor; orta seviye zaman adımını
> **değiştirmiyor**. Yani `%13,6` parçacık artışı **tek** ek bedel.

İki seviyeli sürüm **silinmedi** ama `asama2_sahnesi_ucseviye`
`ucseviye` bayrağı olmayan sahneyi **reddediyor**: sessizce `%69`
momentum atmaktansa hata vermek doğrudur.

---

## 4g. ÖLÇÜLDÜ: mermiyi çözmek **niteliksel** fark yaratıyor (2026-08-09)

Üç kol, aynı `t_end = 0,2 s`, aynı sahne tohumu:

| kol | `A1` | `β` | **`n_ejekta`** | momentum kapanışı |
|---|---|---|---|---|
| tek aşama (`λ=2`) | 0,2146 | **1,617583** | **803** | 1,36e-14 |
| iki seviyeli *(geçersiz)* | 2,0391 | 1,412659 | 32 | **6,90e-01** |
| **üç seviyeli** | **2,0391** | **1,411216** | **28** | **1,31e-14** |

### Asıl bulgu `β` değil, **`n_ejekta`**

`803` — merminin **parçacık sayısının tamamı**. Çözülmemiş mermide
**bütün mermi sekip kaçıyor**. ADR-0028'in *"köpük top gibi
sıçrıyor"* dediği davranış, mermi gerçekçi yoğunlukta (`2610 kg/m³`)
olsa **bile** sürüyor — çünkü `h` çapının `9,3` katı.

Çözülmüş mermide yalnızca **28** parçacık kaçıyor: mermi ağırlıklı
olarak **gömülüyor** — yoğun bir merminin gözenekli hedefe yapması
gereken şey.

> Bu `%12,8`'lik bir `β` farkı değil, **niteliksel bir rejim
> değişikliği**: *"tamamen seken top"* → *"gömülen mermi"*.
> ADR-0026'nın *"çözülmemiş mermi erken bağlanmayı sayısal yapay
> yapar"* uyarısı **ölçümle doğrulandı**.

### `A1 ≥ 2` eşiği **haklı çıktı**

§6'da *"A1 eşiğini düşürmek"* alternatifi *"eşiği boşaltmak"* diye
reddedilmişti. Artık ölçümle destekli: eşiğin altında ve üstünde
**farklı fizik** var.

### İki seviyelinin `β`'sı neden yakın çıktı

`1,412659` ile `1,411216` neredeyse aynı — ama iki seviyelinin
momentum kapanışı `0,690`, yani **sahne bozuktu**. `β` ejekta
momentumundan hesaplanıyor; atılan `%69` ise **bağlı** kütlenin
momentumuydu ve `β`'ya yansımadı.

> **Yakınlık tesadüf.** `β`'nın makul çıkması sahnenin doğru olduğu
> anlamına **gelmiyor**. Momentum kapanışı tanısı olmasaydı bozuk
> sahne *"doğrulanmış"* sayılırdı.

---

## 5. Uygulanması gereken — ~~**mevcut değil**~~ **YAZILDI**

Bu seçenek bir **kabalaştırma** adımı istiyor: aşama-1'in ince
parçacıkları aşama-2'nin kaba kafesine aktarılmalı.

| gereksinim | neden |
|---|---|
| **kütle** korunmalı | ADR-0030'un değişmezi |
| **momentum** korunmalı | ana ürün `β`; kayıp doğrudan onu bozar |
| **enerji** korunmalı | krater ve ejekta ondan geliyor |
| aktarım hatası **ölçülmeli** | yeni bir model-form hatası kaynağı |

> **2026-08-09 güncellemesi:** kod yolu **yazıldı** (`coarsen.py`) ve
> korunum şartlarının üçünü de `~1e-15` ile geçiyor (§4c). Bu paragrafın
> korktuğu şey **gerçekleşmedi**; düşen başka bir şey oldu (atama
> mesafesi).

> Bu **yeni bir kod yolu** ve KAYIT-025'in ölçtüğü şeyle aynı sınıfta:
> C yaklaşımının ara değerleme hatası. Orada momentum `7,5e-03`
> **sistematik** kaybediliyordu (KAYIT-027). Kabalaştırma aynı tuzağa
> düşebilir ve **ölçülmeden** kabul edilemez.

### Reddedilmesi gereken kolay yol

Kabalaştırmayı *"ince parçacıkları grupla, ortalamasını al"* diye yapmak
momentumu **korumaz** (ağırlıksız ortalama). Kütle-ağırlıklı toplama
şart ve o bile enerjiyi korumaz (iç enerji ile kinetik arasında transfer
olur). Bu, ADR ile ayrıca karara bağlanmalı.

---

## 6. Değerlendirilen alternatifler

| seçenek | neden önerilmedi |
|---|---|
| **A1 eşiğini düşürmek** | Eşik ölçümden **önce** yazıldı (ADR-0040) ve düştü. Ölçüme uydurmak, ölçütü boşaltmaktır. Ayrıca ADR-0026 zaten *"çözülmemiş mermi erken bağlanmayı sayısal yapay yapar"* diyor. |
| **Tek aşama `λ=19`** | Ölçüldü: `96` GPU-günü, bütçenin **3,2 katı**. |
| **Bireysel / blok zaman adımı** | CFL cezasını **kökünden** çözer ve iki aşamadan daha genel. Ama çok daha büyük bir mimari değişiklik ve determinizm kilidini (ADR-0004) yeniden düşünmeyi gerektirir. **İki aşama bunun ucuz özel hâlidir**; blok adımı ileride yine düşünülebilir. |
| **Mermiyi kaynak terimi yapmak (D)** | Zaten elendi: model-form `%5–7`, kalibre **edilemiyor** (KAYIT-029, KAYIT-030). |

---

## 7. Bu ADR **kilitlenmeden** önce ölçülmesi gerekenler

1. ~~**`t₁` gerçekte ne kadar** — mermi hızının hedefle eşitlendiği an.~~
   **✔ ÖLÇÜLDÜ: `t₁ = 4,767e-3 s`** (§4a). ADR'nin tahmininin **4,8
   katı**; bedel `+%0,9` değil **`+%4,7`**. Öneri ayakta.
   *Uyarı:* ölçüt *"aynı hıza gelme"* değil *"farkın durulması"*
   olarak **düzeltildi** — ilk formülasyon yanlıştı.
2. ~~**Kabalaştırmanın kütle/momentum/enerji hatası** — üçü de ayrı ayrı.~~
   **✔ ÖLÇÜLDÜ: üçü de `≤ 6e-15`** (§4c). Ama aynı ölçüm **yeni bir
   engel** buldu: atama mesafesi `t₁`'de `4,35` hücre. Bkz. madde 5.
3. **`λ = 19`'da arayüz ne yapıyor** — boşluk 3 yalnızca `λ = 2`'de
   kapandı; `6478:1` oranı ölçülmüş her şeyin ötesinde.

   > **`λ = 19` bu sınavda DOĞRUDAN ÖLÇÜLEMEZ** (2026-08-09).
   > `run_solid_interface`'in üçüncü kolu **tekdüze ince** referanstır ve
   > kenarı `n_coarse·λ`:
   >
   > | `n_coarse` | `λ` | referans `N` | |
   > |---|---|---|---|
   > | 32 | 2 | `64³` = 262 144 | koştu (KAYIT-037) |
   > | 32 | 6 | `192³` = 7,1 M | 4 GiB'a sığmaz |
   > | 32 | **19** | **`608³` = 225 M** | **imkânsız** |
   > | 16 | 6 | `96³` = 884 736 | koşabilir |
   >
   > Referans kolu olmadan **taşma** ölçülemez — parantezin üst ucu odur.
   > Bu bir **sonuç değil, ölçümün sınırı**.

   `scripts/faz43f_arayuz_lam_taramasi.py` yazıldı: `n_coarse` sabit,
   `λ` taranıyor ve soru **eğilime** çevriliyor — taşma `λ` ile büyüyor
   mu? Büyümüyorsa `λ = 19` için **dolaylı kanıt** (ispat **değil**);
   büyüyorsa bu madde **düşer**. Sonuç ne olursa olsun `λ = 19`
   **ölçülmemiş** kalır ve betik bunu her koşuda basıyor.
4. ~~**Blok sınırlarının kaba çözünürlükte kalmasının etkisi** (§4b)~~
   **◐ GEOMETRİK YARISI ÖLÇÜLDÜ** (`scripts/faz43e_blok_sinirlari.py`,
   `r_iç = 25 m`, 7 blok):

   | `λ` | `s_ince` | yanlış sınıflanan | kütlece | `f_blok` sapması |
   |---|---|---|---|---|
   | 2 | 3,500 m | `%4,73` | `%4,96` | **`%3,02`** |
   | 6 | 1,167 m | `%5,48` | `%6,44` | **`%6,45`** |

   > **`λ` arttıkça kötüleşiyor** — ince kafes inceldikçe daha çok
   > parçacık blok sınırına düşüyor ve `7 m`'lik komşudan örnekleme
   > onları çözemiyor. `f_boulder` çıkarımın **üç parametresinden biri**.

   **✔ DİNAMİK ETKİSİ HESAPLANDI (2026-08-11)** — ayrı koşu gerekmedi.
   FAZ 4.12 `f_boulder` duyarlılığını ölçtü (40 nokta, iki aşamalı
   model): tam aralık üzerinden `Δβ = −0,01575`, `Δ`derinlik `= −1,499 m`,
   yani birim `f_boulder` başına `dβ/df = −0,0350` ve
   `d(derinlik)/df = −3,330 m`.

   Yukarıdaki geometrik sapmalar buna çarpılınca (`f = 0,25` nominali):

   | `λ` | `f_blok` sapması | `Δf` | **`Δβ`** | **`Δ`derinlik** |
   |---|---|---|---|---|
   | 2 | `%3,02` | 0,00755 | `2,64e-4` (β'nın `%0,019`'u) | `0,025 m` |
   | 6 | `%6,45` | 0,01613 | `5,64e-4` (`%0,040`) | `0,054 m` |

   İkisi de ölçülmüş gürültü tabanının (`0,25 m`) **onda biri**;
   DART'ın `β` belirsizliğinin (`~%5 = 0,0705`) `%0,4`'ü.

   > **Blok sınırı sapması dinamik olarak ihmal edilebilir.** Bu madde
   > kilit için engel değil.

   *İki çekince, gizlenmiyor:*
   1. Bu bir **doğrusal kestirim**, doğrudan koşu değil. Duyarlılık
      köşe ortalamalarından geldi ve aradaki eğrilik ölçülmedi.
   2. Duyarlılık `λ = 2`'de ölçüldü; `λ = 6` satırı onun **aynı**
      kaldığını varsayıyor. `λ = 6`'da ayrı ölçülmedi.
5. ~~**(YENİ, §4c)** **Lagrange'cı hedef site üretimi.**~~
   **✔ ÖLÇÜLDÜ (§4d):** yazıldı (`sites_from_cloud`) ve ölçülen `t₁`'de
   ısıya dönen oran `%99,3 → %2,88`, atama mesafesi `4,35 → 0,73`
   hücre. §4c'nin engeli **kalktı**.
   *Kalan:* ek parçacıkların aşama-2 kafesiyle **dikişi** ölçülmedi ve
   site sayısına **üst sınır konmadı** (`t₁=1e-2 s` → 210).

> **Durum (2026-08-11):** 1, 2, 4 ve 5 **ölçüldü**; 4'ün dinamik yarısı
> duyarlılıktan hesaplandı ve **ihmal edilebilir** çıktı. **3 hâlâ
> ölçülmedi** ama artık kuyrukta (`faz43f`, iş `1494651`); kilit için
> tek kalan şart odur. Özellikle 3: A′'nın
> arayüz davranışı yüksek oranda **bilinmiyor** ve KAYIT-024 gürültünün
> oranla **büyüdüğünü** ölçtü.
