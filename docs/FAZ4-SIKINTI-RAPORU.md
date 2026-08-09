# FAZ 4 — sıkıntı raporu (canlı)

> **Bu belge her turda güncellenir.** Amaç tek bir yerde şunu görebilmek:
> *ne bozuldu, neden bozuldu, nasıl bulundu, ne yapıldı.*
>
> Kural: **hiçbir satır silinmez.** Düzeltilen bir sıkıntı `KAPANDI`
> işaretlenir; nedeni yerinde kalır. Yanlış çıkan bir yargı da öyle.

**Son güncelleme:** 2026-08-09 · **Kapanan:** 31 · **Açık:** 4

---

## 1. AÇIK sıkıntılar

Bunlar bugün çözülemez ve **nedeni dışsal** ya da **ölçüm gerektiriyor**.

### A1 — TRUBA kotası dolu (**en önemli engel**)

| | |
|---|---|
| **belirti** | her iş `PENDING (AssocGrpCPUMinutesLimit)` |
| **kanıt** | hesap `cpu = 7 200 096 / 7 200 000` (96 dk **aşılmış**) |
| **benim payım** | `cpu = 133 053` (%1,8) — kalanını grup harcamış |
| **alternatif var mı** | **yok**: tek erişilebilir hesap `egitimg16`, tek küme `cuda` |
| **donanım** | **boş** (21 idle düğüm) — ama tahsis yok |
| **karar sınaması** | 1 dk, 16 çekirdek, 1 GPU, sadece `echo` → **bloke** |
| **etkilenen** | FAZ 4.4, 4.5, 4.6, 4.7 (**dört ölçüm**) |
| **durum** | iş **1460742** kuyrukta; kota yenilenince kendiliğinden koşacak |

> Bu bir kod sorunu değil. Etrafından **dolaşılmadı**.

### A2 — G4 kapısı geçilemedi

On ölçütün **onu da** `koşulmadı`. Kapı raporu üretildi ve
`GEÇİLEMEDİ` diyor (çıkış kodu 1). A1 çözülmeden değişmez.

### A3 — ADR-0041 ve ADR-0042 **koşullu**

Ölçümler **küp geometrisinde** yapıldı, DART geometrisinde değil.
Boşluk 3 `λ = 2` (8:1) oranında kapandı; ADR-0026 daha yükseğini
istiyor. Koşul kapı raporunda **listeleniyor** ve kapı geçse bile
kalacak.

### A5 — **G4-A1 düştü: mermi çözülmemiş** (2026-08-08, en önemli teknik bulgu)

| | |
|---|---|
| **ölçülen** | `A1 = 0,215` parçacık/çap (`s7_λ2`), en iyi kolda `0,322` |
| **eşik** | `2,0` — **6,2 ila 9,3 kat** eksik |
| **gereken `λ`** | **18,6** (kütle oranı **6478:1**) |
| **ölçülmüş `λ`** | boşluk 3: `2` (8:1); KAYIT-033: `≤ 3` |
| **bedel** | `r_iç = 3 m` ile `96` GPU-günü — bütçenin **3,2 katı** |
| **bedelin kaynağı** | parçacık `1,13×`, **`dt` cezası `9,3×`** |

> **Tek global zaman adımlı şemada bu bedel küçültülemez.** Çözümü
> bireysel/blok zaman adımı — bu kod tabanında **yok**.

Karar gerektiriyor: A1 eşiği mi gözden geçirilecek, mimari mi
değişecek? İkisi de bir ADR ister. Detay:
[KAYIT-041](defter/KAYIT-041_2026-08-08_yerel-gpu-ve-mermi-cozulmemis.md).

### A6 — FAZ 4.4 `--t-end` almıyor, `--steps` alıyor → **KAPANDI**

*(Kural gereği yerinde bırakıldı; bkz. §2 sıkıntı 24.)*

Kollar **farklı `t_sim`**'e ulaşıyor (`dt` farklı olduğu için). Farklı
`t`'deki `β`'ları kıyaslamak yakınsama ölçmez, dolayısıyla **B1 ve B3
hesaplanamadı**. Kusur değil, ölçüm tasarımının bilinen sınırı; sonraki
koşuda düzeltilmeli.

### A7 — **ADR-0043'ün `t₁ ≈ 1e-3 s` tahmini ölçümle çürüdü** (2026-08-08)

ADR-0043 iki aşamalı çözünürlüğü *"mermiyi çözmek `%1`'e mal oluyor"*
diye önerdi. O `%1`, `t₁ ≈ 1e-3 s` **varsayımına** dayanıyordu ve
varsayım şuydu: mermi kendi çapını `1,22e-4 s`'de geçiyor, `1e-3 s`'de
şok `4` mermi çapı yol alıyor, öyleyse bağlanma bitmiştir.

Ölçüldü (`scripts/faz43c_baglanma_suresi.py`, `λ=19`, `A1 = 2,04`,
`N = 11 871`, yerel RTX 3050):

| büyüklük | değer |
|---|---|
| ölçüt | `u = \|⟨v⟩_mermi − ⟨v⟩_yakın hedef\| / v_çarpma` |
| `u` (`t → 0`) | `0,791` |
| `u` (`t = 2e-3 s`) | **`0,337`** |
| durulma sınavı | **DÜŞTÜ** — eğilim `%8,56`, yarım-pencere `%4,79` (tol `%2`) |
| `t₁` (ölçülen) | **`nan`** — pencerede durulma **yok** |

> `1e-3 s`'de mermi hâlâ hedefe göre çarpma hızının **üçte biriyle**
> gidiyor ve `u` **düşmeye devam ediyor**. Bağlanma bitmemiştir.

**Sonucu doğrudan bedele vuruyor.** ADR-0043 §3'ün duyarlılık tablosu
`t₁` ile **doğrusal**: `1e-2 s` → `+%9,9`, `1e-1 s` → `+%99`. `t₁`
ölçülmeden §4'ün önerisi **savunulamaz**.

**Durum: KAPANDI (2026-08-09).** `t_end = 5e-2 s` koşusu bitti,
`t₁ = 4,767e-3 s` **ölçüldü** — tahminin `4,8` katı, bedel `+%0,9`
yerine `+%4,7`. Öneri o kalemde ayakta.

**Ama ölçüt tanımım da yanlıştı** ve bunu ancak iz eğrisine bakınca
gördüm: `u` **sıfıra inmiyor**, `0,409`'da düzleşiyor — ve oraya
*aşağıdan*, `0,118`'den **yükselerek** geliyor (92 adımın 16'sı artış).
*"Mermi hedefle aynı hıza gelince bağlanma biter"* yanlış; doğrusu
*"momentum alışverişi bitince fark **sabitlenir**"*. Düzeltme
ADR-0043 §4a ve `faz43c` başlığında; yanlış cümle **silinmedi**.

### A8 — **`t₁`'in sağlaması gereken iki şart çelişiyor** (2026-08-09, ADR-0043'ü durduran bulgu)

Kabalaştırma ölçüldü (§2 sıkıntı 27). Korunum **geçti**, aktarım
**düştü**:

| `t₁` [s] | kütle/mom./enerji | ısıya dönen | **atama mesafesi** |
|---|---|---|---|
| `1e-3` | `≤ 3,4e-15` | `%93,2` | `0,97` hücre |
| **`4,77e-3`** (ölçülen `t₁`) | `≤ 1,0e-15` | **`%99,3`** | **`4,35` hücre** |
| `1e-2` | `≤ 6,1e-15` | **`%99,9`** | **`10,16` hücre = 35,6 m** |

- Bağlanmanın bitmesi için `t₁` **büyük** olmalı → `4,77e-3 s`.
- Aktarımın maddeyi ışınlamaması için **küçük** olmalı → `≤ 1e-3 s`.
- **Aralık boş.**

`r_iç`'i büyütmek çözmüyor: sıkıştırma `(λ₁/λ₂)³ = 857`'de **sabit**,
yalnızca bedel artıyor (`12 m` → `+%42`).

> Kusur tanımlanabilir: hedef siteler aşama-2'nin **başlangıç**
> kafesinden alınıyor, yani **Euler**'ci — maddenin peşinden gitmiyor.

**KAPANDI (2026-08-09).** Lagrange'cı sürüm yazıldı (`sites_from_cloud`)
ve ölçüldü — **çelişki Euler'ci aktarımın çelişkisiymiş**:

| `t₁` [s] | euler ısıya | **lagrange ısıya** | euler mes. | **lagrange mes.** |
|---|---|---|---|---|
| `1e-4` | %98,2 | %97,1 | 0,97 | 0,73 |
| `1e-3` | %93,2 | %85,9 | 0,97 | 0,73 |
| **`4,77e-3`** | **%99,3** | **%2,88** | **4,35** | **0,73** |
| `1e-2` | %99,9 | **%0,46** | **10,16** | **0,73** |

> İki kip **zıt yönlere** gidiyor: Euler'ci kötüleşiyor, Lagrange'cı
> **iyileşiyor**. Aynı olayın iki yüzü — madde genişliyor; sabit hedef
> ondan uzaklaşıyor, bulutu izleyen hedef ise giderek daha **düzgün**
> bir akış görüyor.

**Kalan (ölçülmedi):** ek parçacıkların (40 / 210) aşama-2 kafesiyle
**dikişi**, ve site sayısına **üst sınır** yok.

### A4 — `ileri_kosu`'nun GPU kısmı hiç koşulmadı

Yapısı doğrulanmış `faz44` döngüsüyle aynı tutuldu ama bu bir kanıt
değil. Doğrulanamayan kod yolu **küçültüldü** (üçe bölündü, ikisi
GPU'suz sınanıyor) ama sıfırlanamadı.

---

## 2. KAPANAN sıkıntılar — kronolojik

### Ölçüm tasarımı (1–4)

| # | sıkıntı | nasıl bulundu | ne yapıldı |
|---|---|---|---|
| 1 | *"yayılım varsa suçlu komşu sayısıdır"* — **ayrıştırma yok** | ölçülen eğri hâlâ düşüyordu | iddia **düzeltildi**: sonuç bir **üst sınır** |
| 2 | tarama salınımı **kapsamadı** (523,6 < 551,5) | `judge` kapsam koruması | `n_sides_for_swing()` — aritmetik **koda** taşındı |
| 3 | kapsadı ama çalışma aralığında **tek nokta** | `judge` iç-nokta koruması | aynı fonksiyon; iki şart birlikte çözülüyor |
| 4 | `rho_ilk = 0,0` raporlandı | değer sıfırdı | `_eval()` eklendi + sıfırsa `RuntimeError` |

### Fizik kurulumu (5–8)

| # | sıkıntı | kanıt | ne yapıldı |
|---|---|---|---|
| 5 | `E = 5e9 J` → özgül `6,6e7 J/kg` | koşu **patladı** (`overflow in reduce`) | mertebe **hesaplandı** (`3,4e6 J`), `1,0e7` seçildi |
| 6 | eşik `1,05·ρ₀` **hiç** tetiklenmedi | `ρ_başlangıç = 1800`, `1,05·ρ₀ = 2835` | gözeneklilikte `ρ = ρ₀/α₀`; ölçüt **hıza** çevrildi |
| 7 | enjeksiyon yarıçapı kolun **kendi** `dx`'ine bağlı | ince kol patladı (**262144/262144** NaN) | mutlak `h_inject`; **yeni ön koşul**: enjekte kütle eşit |
| 8 | eşik `kesir·max\|v\|` → kollarda **farklı** eşik | `r = 0,838970` = kutu köşesi | `v_ref = √(2E/m_enj)` + **doygunluk koruması** |

> **7 numaralı** sıkıntı ön koşul listesinde bir **boşluk** açığa
> çıkardı: üç kolun enerjisi `3,8e-16` içinde aynıydı ama **dağıldığı
> bölge** farklıydı. `enerji_esit` bunu yakalayamazdı.

### Süreç (9–10)

| # | sıkıntı | sonuç | ne yapıldı |
|---|---|---|---|
| 9 | GPU testleri `PYTHONPATH=src` ile **atlandı** | 4 test "skipped" göründü | tekerlek yolu korundu; **atlanan test geçmiş değildir** |
| 10 | metin değiştirme **eşleşmeyi doğrulamadan** `"ok"` yazdı | iş `NameError` ile düştü | her değiştirmede `assert`, ya da `Edit` |

### Çıkarım katmanı (11–14) — **üçü testleri geçiyordu**

| # | sıkıntı | testler | ne yapıldı |
|---|---|---|---|
| 11 | eski plato ölçütü **"durulmadı" diyemiyordu** | — | `settling_time` çıkarıldı; durulmadıysa `nan` |
| 12 | *"yarım-pencere sınavı bağımsız"* — **değil** | — | altı şekilde ölçüldü; oran **tam 2**, cebirsel |
| 13 | `prior_width()` **yanlış payda** (`1,0` vs `0,68`) | **kör** | ölçüt **belgede yazandan zayıftı**; sıkılaştı |
| 14 | kenara çakılma "bilgilendirici" sayılıyordu | **kör** | `pinned()`; çakılı eksen C2'yi geçemez |

### Sözleşme ve tip (15–18)

| # | sıkıntı | belirti | ne yapıldı |
|---|---|---|---|
| 15 | `escape_speed_value` diye **parametre yok** | üç betikte birden | doğru imza; kota olsaydı üçü de düşerdi |
| 16 | `judge` doygun cephede **çöküyordu** | `TypeError: '<' NoneType` | `None` kolları `belirsiz`; tek eşik atlanıyor |
| 17 | aynı çökme `faz44_bosluk3`'te **iki yerde daha** | tüketici taraması | `None` → `"DOYGUN"` yazılıyor |
| 18 | kapı **numpy** değerleri `koşulmadı` sanıyordu | **kör** | `_sayi()` ile `float()`; np.bool_ dahil |

> **18 numaralı** sıkıntı kapının var olma sebebinin **tersiydi**:
> *"koşulmayan ölçüt geçmiş sayılmaz"* kuralı vardı, ama **ölçülen ölçüt
> koşulmamış sayılıyordu.** Ve tamamen sessizdi — kapı zaten geçmiyor,
> yani fazla iki kalem kimsenin dikkatini çekmezdi.

### Değişmez boşluğu (21) — kusur **değil**, sınanmamış varsayım

| # | sıkıntı | bulgu | ne yapıldı |
|---|---|---|---|
| 21 | `dt` **en küçük** `h` ile mi belirleniyor — **sınanmıyordu** | kod **doğru** (`_h_np` dizi, global `min`) | CPU'da 4 test; ölçüldü |

Bu bir kusur değil ama **sessiz bir risk**: biri `_h_np`'yi `self.h`'ye
(skaler `max`) çevirse A′'da ince parçacıklar CFL'yi **ihlal ederdi** ve
kararsızlık **birikerek** gelirdi — hemen patlamaz.

Ölçülen (CPU referansı, `n = 216`):

| kurulum | `dt` |
|---|---|
| `h = 2,6` tekdüze | `5,132e-05` |
| `h = 1,3` tekdüze | `2,566e-05` (oran **tam 2,000**) |
| karışık (yarısı ince) | **`2,566e-05`** — **ince** değere oturuyor |
| **tek** parçacık `h = 0,65` | **`1,284e-05`** — dörtte bir |

> Son satır `min`'in gerçekten **global** olduğunu gösteriyor: ortalama
> alınıyor olsaydı tek parçacık `dt`'yi kayda değer düşürmezdi.

`ensemble_cost`'un `dt_kaba/λ` varsayımı **bu** ölçümden geliyor;
değişmez düşerse maliyet tablosu da yanlış olur.

### Dayanıklılık (19–20, 22)

| # | sıkıntı | risk | ne yapıldı |
|---|---|---|---|
| 19 | beş koşucuda **sabit TRUBA yolu** | iş nihayet koşarken yol hatası → 12 saat yanar | `REPO = Path(__file__)...` |
| 20 | UTF-8 koruması **dört koşucuda yoktu** | `faz47` **gerçekten çöktü** ve raporu yok etti | altı koşucuya eklendi |
| 22 | ensemble **kesintide her şeyi kaybediyordu** | iş 1460700 zaman aşımından kesildi (**yaşandı**) | JSONL, satır satır, devam edebilir |
| 23 | **TRUBA'ya bağımlılık** — kota dolunca hiç ölçüm yok | GPU ölçümleri tamamen durmuştu | **yerel RTX 3050** kullanıldı; `2,85×` yavaş, yeterli |

> **22 numaralı** sıkıntı bir kod hatası değil, bir **eksiklik**ti.
> `~300` koşu `~10` GPU-günü (KAYIT-040) ve bir SLURM işi `12` saat —
> yani kesinti **kaçınılmaz**, olası değil. Tek seferlik bir çağrı her
> kesintide baştan başlardı.

---

### 24 — kollar **farklı `t_sim`**'e ulaşıyordu (A6'nın kapanışı)

| | |
|---|---|
| **belirti** | `s7_λ2`: A′ `t = 0,342 s`, tek-`h` `t = 0,694 s` |
| **kök neden** | koşucu yalnızca `--steps` alıyordu; `dt ∝ h`, `h` kola göre değişiyor |
| **etkisi** | `B1` ve `B3` **anlamsız** — farklı `t`'deki `β`'lar kıyaslanıyordu |
| **düzeltme** | `--t-end`; son adım `dt = t_end − t_sim` ile **kırpılıyor** |
| **ikinci savunma** | `esit_t_mi()`; kollar aynı `t`'de değilse `B1`/`B3` anahtarları **hiç yazılmıyor** |
| **doğrulama** | ilk kol tam `t_sim = 2,0000e-01`'e oturdu; fikstür güncellenince 7 test düştü → koruma **çalışıyor** |

> Yanlış bir sayı yazmaktansa *"koşulmadı"* demek doğrudur. İkinci
> savunma tam bunun için: `--t-end` unutulursa kapı sessizce yanlış bir
> `B1` üretmiyor.

---

### 25 — `refine.py`'de **iki** gizli bellek bombası (aynı kalıbın 2. ve 3. kez)

| | |
|---|---|
| **belirti** | `r_ince = 9 m, λ = 19` → `Unable to allocate 36.8 GiB` |
| **kök neden** | `N×M×3` dizi **tek seferde** kuruluyordu, iki ayrı yerde |
| **yer 1** | `refine_scene_local` α₀/Y₀ komşu araması: `r=6 m`'de `2,8 GB`, `r=9 m`'de `9,4 GB` |
| **yer 2** | `_dikis_kalitesi`: kuşakta `40 597` parçacık → `36,8 GiB` |
| **niye görülmedi** | `_dikis_kalitesi`'nin yorumu *"kuşak küçük (yüzlerce)"* diyordu — `λ=2`'de **doğruydu** |
| **düzeltme** | ikisi de parçalı; blok belleğe göre seçiliyor |
| **doğrulama** | parçalı sonuç tam matrisle **birebir** aynı (yeni test) |

> Bu, `412 TiB` kusurunun **aynısı**. Üçüncü kez. Karşı önlem artık bir
> kural: `x[:, None, :] - y[None, :, :]` **asla** parçasız yazılmıyor.
> `coarsen.py` bu kuralla yazıldığı için oraya sızmadı.

### 26 — kabalaştırmanın hedef kafesi **yanlıştı**

| | |
|---|---|
| **belirti** | `r_iç=6 m` içinde yalnızca **2 site** |
| **kök neden** | çıkarılan `7 m`'lik **kaba** parçacıklar hedef alınıyordu |
| **doğrusu** | aşama-2 `λ=2` kullanıyor → o bölgede aralık `3,5 m` |
| **nasıl bulundu** | CPU ön uçuşu (GPU'ya gitmeden) |
| **düzeltme** | hedef artık aşama-2'nin **kendi** ince kafesi (2 → 14 site) |

### 27 — açısal momentum **anlamsız** bir paydayla ölçülüyordu

| | |
|---|---|
| **belirti** | `%72 870` kayıp — okunamaz |
| **kök neden** | `\|L₀\|`'a bölünüyordu; **merkezi çarpmada `L₀ ≈ 0`** |
| **düzeltme** | ulaşılabilir ölçeğe göre: `Σ mᵢ\|xᵢ\|\|vᵢ\|` → `%1,71` |
| **ikinci kusur** | ilk test fikstürüm bunu **gösteremiyordu** (`L₀ = 4` çıkmıştı) |
| **doğrulama** | fikstür `L₀ = 0` olacak biçimde yeniden kuruldu; testin kendi iddiası artık ölçülüyor |

---

### 28 — dejenere ölçüm **`%0` diye raporlanıyordu** (kendi betiğimde)

| | |
|---|---|
| **belirti** | `r_iç = 6 m`'de bütün satırlar `%0,000` — bir an *"hata yok"* diye okudum |
| **kök neden** | ince bölgede **hiç blok yoktu**; `f_kes = f_kul = 0`, sapma `0/1e-300 = 0` |
| **niye tehlikeli** | ölçülemeyen şeye `0` demek `nan` demekten **kötü**: `nan` görünür, `0` **başarı** gibi okunur |
| **düzeltme** | `validation/boulder_boundary.py`; dejenere kol `belirsiz`, `judge` onları **atıyor**, hepsi dejenereyse `gecti = None` (`False` değil) |
| **doğrulama** | 14 test; koşucu artık çıkış kodu `1` ve *"kayıt bulunamadı"* |

### 29 — kendi **test fikstürüm** eşiği yuvarlıyordu

| | |
|---|---|
| **belirti** | `test_esik_kenarlari[0.099-True]` düştü |
| **kök neden** | fikstür `n=1000` parçacık **sayarak** kesir kuruyordu; `int(round(0,3297·1000)) = 330` → `%9,9` **`%10,0`** oldu |
| **düzeltme** | kütle doğrudan veriliyor, yuvarlama yok |

> Sınav kodun değil **fikstürün** kusuruydu ve fikstür kusuru testi
> *"kod yanlış"* diye bağırtıyordu. §2 sıkıntı 27'deki `L₀ = 4`
> fikstürüyle aynı sınıf — bu turda **iki kez**.

### 30 — bayat süreçler kaynağı yiyordu

| | |
|---|---|
| **belirti** | test takımı `%30`'da, `faz45` bir saatte 2000 adıma varamadı |
| **kök neden** | **iki** `pytest` (biri unutulmuş) + kullanıcının kestiği `faz43e`'nin süreci **hâlâ koşuyordu** (`λ=19, r=25 m` → 1,85 M parçacık) |
| **ders** | bir aracın çağrısını kesmek **süreci öldürmüyor** |

---

### 31 — çıkarım hattının **uçtan uca** sınavı yoktu

| | |
|---|---|
| **belirti** | 42 çıkarım testi var ama **hiçbiri** uçtan uca değil |
| **kök neden** | posterior testleri veriyi **vekilin kendisinden** üretiyordu (`veri = s.predict(gerçek)`) — döngüsel |
| **niye önemli** | gerçekte veri **simülatörden** gelir; vekil onu yalnızca yaklaşık temsil eder. Asıl risk **dar ama yanlış** posterior |
| **düzeltme** | `tests/test_inference_uctan_uca.py` — veri, vekilin öğrenemeyeceği bir modelden geliyor |
| **sonuç** | `C1`, gerçeğin posteriorda olup olmadığını **doğru** izliyor (üç doğrusalsızlık düzeyinde de) |
| **ek** | `ensemble_kos` ilk kez **kuru olmayan** kipte sınandı: sürdürme, düşen nokta, kesinti→aynı vekil |

> **Ölçüm bir tahminimi daha çürüttü (7.):** *"`dogrusalsizlik = 3` vekili
> bozar"* dedim; `q2 = 0,944…0,996` çıktı. Hangi biçimin **gerçekten**
> bozduğu ölçüldü:
>
> | tepki yüzeyi | `q2` | geçiyor mu |
> |---|---|---|
> | `a³` | 0,9944 | ✔ |
> | basamak `a > ½` | 0,6706 | ✔ |
> | `1/(0,05+a)` | 0,7812 | ✔ |
> | **`sin(4πa)`** | **−0,0262** | **✘** |
>
> **Bunun kendisi bir bulgu:** `q2 > 0,5` **zayıf** bir koruma. Yalnızca
> **salınımlı** tepki yüzeyinde uyarı veriyor ve `β(θ)` fizik gereği
> salınımlı değil — yani pratikte **neredeyse her zaman geçecek**.
> G4-C bu bayrağa tek başına yaslanmamalı. Sınır artık **testle**
> belgeli (`test_q2_esigi_ZAYIF_bir_koruma_bu_yazili_olsun`).

---

## 3. Kusurların **sınıflandırması**

| sınıf | sayı | örnek |
|---|---|---|
| ölçüm tasarımı (kendi düzeneğim) | 8 | dar tarama, yanlış eşik, yanlış payda |
| sözleşme / tip | 4 | `None` çökmesi, numpy tipleri |
| dayanıklılık / portabilite | 5 | sabit yol, UTF-8, JSON |
| fizik kurulumu | 3 | enerji mertebesi, yığın yoğunluğu |
| süreç | 2 | doğrulanmayan değiştirme, atlanan test |
| sınanmamış değişmez | 1 | `dt` en küçük `h` ile mi |

> **Yirmi üç kusurun tamamı benim ölçüm düzeneğimde ya da yeni yazdığım
> kodda.** Hiçbiri SPH çözücüsünde değil.

---

## 4. Tekrarlanan hata **kalıpları**

Bunlar bir kez değil, **birden çok** kez oldu:

| kalıp | kaç kez | karşı önlem |
|---|---|---|
| bir eşiği **ölçmeden** yazmak | **6** | eşik yazılmadan önce ölçülüyor |
| `N×M×3` diziyi **parçasız** kurmak | **3** | kural: asla parçasız yazılmaz |
| çalışma noktasını **içermeyen** aralıkta yargı | 2 (+2 önceki tur) | `judge` kapsam koruması |
| aynı büyüklüğü **iki yerde** tanımlamak | 2 | tek kaynağa indirildi |
| dönüş sözleşmesi değişince **tüketicileri denetlemem** | 2 | sistematik tarama |
| **tutarsız** kurulum (yol, kodlama) | 2 | parametrize testler |

> En sık kalıp: **ölçmeden yazmak.** **Beş** kez oldu ve beşinde de
> ölçüm tahminimi çürüttü. Son iki örnek: *"RTX 3050 ~400× yavaş olur"*
> dedim, ölçüm **2,85×** dedi; *"`t₁ ≈ 1e-3 s` yeter"* dedim, ölçüm
> `u = 0,337` ve **hâlâ düşüyor** dedi (A7).
>
> Bu ikisinin ortak yanı: ikisi de bir **fizik argümanından** türetildi
> (mermi çapı / şok hızı, bellek bant genişliği) ve ikisi de makul
> görünüyordu. Kalıp *"dikkatsizlik"* değil — **argümanın kendisi
> ölçümün yerine geçemiyor.**
>
> Altıncısı (2026-08-09) aynı kalıbın **ölçüt** hâli: *"`u → 0`
> bağlanmanın bittiğini gösterir"* yazdım; `u` sıfıra inmedi,
> `0,409`'da düzleşti. Eşik değil **tanım** yanlıştı, ki bu daha sinsi:
> yanlış tanım ölçüm yapılsa bile yanlış sonucu *doğru* gösterirdi.

---

## 5. Bu turda **doğru** yapılanlar

Dengeli olmak için — çünkü rapor yalnızca hataları listelerse ne işe
yaradığı görünmez:

| ne | kanıt |
|---|---|
| kapsam koruması **kendi** hatamı yakaladı | sıkıntı 2 ve 3 |
| doğrulanamayan kod yolu **küçültüldü** | `ileri_kosu` üçe bölündü |
| eşikler ölçümden **önce** yazıldı | `G4-OLCUTLERI.md` + 13 test |
| kuru kip bir **kanıt sayılmıyor** | `g4_gate` `kuru: true` → `koşulmadı` |
| sonradan ölçülen büyüklük **ölçüt yapılmadı** | `TANILAR` bölümü |
| R4 riski **kapandı** | `x_reference` zorunlu |
| reddedilen alternatif **ölçüldü** | naif ortalama `%38` momentum kaybı |
| CPU ön uçuşu GPU'dan **önce** koştu | sıkıntı 26 ve 27 GPU'ya gitmeden bulundu |
| korunumun **görmediği** şey ayrıca ölçüldü | atama mesafesi → A8'i o buldu |
| kendi testimin fikstürü **sınandı** | `L₀ = 4` ve `%9,9→%10,0`, ikisi de düzeltildi |
| reddedilen yol **ölçülerek** çürütüldü | Euler'ci aktarım: `%99,3` vs `%2,88` |
| dejenere ölçüm **`belirsiz`** oldu | `%0` diye raporlanması engellendi |

---

## 6. Sayılar

| büyüklük | değer |
|---|---|
| hata ayıklama turu | **16** |
| kapanan sıkıntı | **31** |
| açık sıkıntı | **4** (A5 karar, kalanı kota; A6/A7/A8 kapandı) |
| **testlerin kör olduğu kusur** | **6** |
| **tahminimi çürüten ölçüm** | **7** |
| eklenen gerileme testi | **123** |
| yerel test takımı | **954 geçti, 96 atlandı** (öncesi 912, ondan önce 898) |
