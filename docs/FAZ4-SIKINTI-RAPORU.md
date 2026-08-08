# FAZ 4 — sıkıntı raporu (canlı)

> **Bu belge her turda güncellenir.** Amaç tek bir yerde şunu görebilmek:
> *ne bozuldu, neden bozuldu, nasıl bulundu, ne yapıldı.*
>
> Kural: **hiçbir satır silinmez.** Düzeltilen bir sıkıntı `KAPANDI`
> işaretlenir; nedeni yerinde kalır. Yanlış çıkan bir yargı da öyle.

**Son güncelleme:** 2026-08-08 · **Kapanan:** 20 · **Açık:** 4

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

### Dayanıklılık (19–20)

| # | sıkıntı | risk | ne yapıldı |
|---|---|---|---|
| 19 | beş koşucuda **sabit TRUBA yolu** | iş nihayet koşarken yol hatası → 12 saat yanar | `REPO = Path(__file__)...` |
| 20 | UTF-8 koruması **dört koşucuda yoktu** | `faz47` **gerçekten çöktü** ve raporu yok etti | altı koşucuya eklendi |

---

## 3. Kusurların **sınıflandırması**

| sınıf | sayı | örnek |
|---|---|---|
| ölçüm tasarımı (kendi düzeneğim) | 8 | dar tarama, yanlış eşik, yanlış payda |
| sözleşme / tip | 4 | `None` çökmesi, numpy tipleri |
| dayanıklılık / portabilite | 3 | sabit yol, UTF-8, JSON |
| fizik kurulumu | 3 | enerji mertebesi, yığın yoğunluğu |
| süreç | 2 | doğrulanmayan değiştirme, atlanan test |

> **Yirmi kusurun tamamı benim ölçüm düzeneğimde ya da yeni yazdığım
> kodda.** Hiçbiri SPH çözücüsünde değil.

---

## 4. Tekrarlanan hata **kalıpları**

Bunlar bir kez değil, **birden çok** kez oldu:

| kalıp | kaç kez | karşı önlem |
|---|---|---|
| bir eşiği **ölçmeden** yazmak | 3 | eşik yazılmadan önce ölçülüyor |
| çalışma noktasını **içermeyen** aralıkta yargı | 2 (+2 önceki tur) | `judge` kapsam koruması |
| aynı büyüklüğü **iki yerde** tanımlamak | 2 | tek kaynağa indirildi |
| dönüş sözleşmesi değişince **tüketicileri denetlemem** | 2 | sistematik tarama |
| **tutarsız** kurulum (yol, kodlama) | 2 | parametrize testler |

> En sık kalıp: **ölçmeden yazmak.** Üç kez oldu ve üçünde de ölçüm
> tahminimi çürüttü.

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
| hata ayıklama turu | **12** |
| kapanan sıkıntı | **20** |
| açık sıkıntı | **4** (üçü kotaya bağlı) |
| **testlerin kör olduğu kusur** | **4** |
| eklenen gerileme testi | **42** |
| yerel test takımı | **954 geçti, 96 atlandı** (öncesi 912, ondan önce 898) |
