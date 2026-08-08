# FAZ 4 — sıkıntı raporu (canlı)

> **Bu belge her turda güncellenir.** Amaç tek bir yerde şunu görebilmek:
> *ne bozuldu, neden bozuldu, nasıl bulundu, ne yapıldı.*
>
> Kural: **hiçbir satır silinmez.** Düzeltilen bir sıkıntı `KAPANDI`
> işaretlenir; nedeni yerinde kalır. Yanlış çıkan bir yargı da öyle.

**Son güncelleme:** 2026-08-08 · **Kapanan:** 24 · **Açık:** 6

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

**Durum:** `t₁`'i bulmak için `t_end = 5e-2 s` koşusu sürüyor (25 kat
uzun). ADR-0043 `ÖNERİLDİ` kalıyor — zaten §7 bunu **kilit şartı**
olarak yazmıştı, şart **işe yaradı**.

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
| bir eşiği **ölçmeden** yazmak | **5** | eşik yazılmadan önce ölçülüyor |
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

---

## 6. Sayılar

| büyüklük | değer |
|---|---|
| hata ayıklama turu | **15** |
| kapanan sıkıntı | **24** |
| açık sıkıntı | **6** (A5 + A7 karar, kalanı kota; A6 kapandı) |
| **testlerin kör olduğu kusur** | **4** |
| **tahminimi çürüten ölçüm** | **5** |
| eklenen gerileme testi | **67** |
| yerel test takımı | **954 geçti, 96 atlandı** (öncesi 912, ondan önce 898) |
