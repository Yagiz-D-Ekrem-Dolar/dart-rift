# KAYIT-028 — D-1: kaynak teriminin model-form hatası (2026-08-04)

**Kapsam:** FAZ 4.2 karar verisi · **Durum:** ölçüldü — **D için iyi haber**,
ama sınırlı bir aralıkta
**Öncül:** ADR-0011, ADR-0026, [KAYIT-023](KAYIT-023_2026-08-04_cozunurlugu-h-belirliyor.md)

---

## 0. Soru ve neden dolaylı sorulmak zorunda

**D**, mermiyi hiç çözmez: momentumunu ve enerjisini bir **kaynak terimi**
olarak hedefe koyar. Getirdiği hata bir ayrıklaştırma hatası değil,
**model-form** hatasıdır.

Doğrudan kıyas **imkânsız**: DART mermisini çözmek `1,72e9` parçacık ister
(ADR-0026), fizibil sınır `1,12e7`.

### Dolaylı kıyasın mantığı

Kaynak terimi *"aynı enerji, **yapısız**"* demektir. Öyleyse:

> **Gözlenebilir, enerjinin biriktirildiği bölgenin yarıçapına ne kadar
> duyarlı?**

Sedov'un **tam analitik** çözümü (nokta patlaması) `r_dep → 0` limitidir —
yani doğrudan referans. Başka bir koşuya gerek yok.

---

## 1. Ölçüm (TRUBA, iş 1451137, `n_side = 64`, 87 s)

| `h_enj` | `r_dep` | **`r_dep/r_şok`** | `n_enj` | `r_ölçülen` | **işaretli hata** | adım |
|---|---|---|---|---|---|---|
| 0,015 | 0,030 | 0,1200 | **32** | 0,23212 | **−0,07112** | 654 |
| 0,020 | 0,040 | 0,1601 | **56** | 0,22588 | **−0,09611** | 575 |
| 0,025 | 0,050 | 0,2001 | 136 | 0,23983 | −0,04028 | 484 |
| 0,030 | 0,060 | 0,2401 | 208 | 0,23881 | −0,04435 | 408 |
| 0,040 | 0,080 | 0,3201 | 552 | 0,23874 | −0,04464 | 287 |
| 0,060 | 0,120 | 0,4802 | 1904 | 0,24176 | −0,03255 | 175 |

Boşluk kontrolü geçti (tarama ayırt ediyor).

---

## 2. Ham uydurma **kirlenmiş** — ve rakamlar bunu söylüyor

Betiğin ilk çıktısı `p = −0,647` idi: *"biriktirme yarıçapı küçüldükçe hata
**büyüyor**"*. Bu, naif beklentinin (küçük `r_dep` → nokta patlamasına
yaklaşma) **tersi**.

**Sebep ayrıklaştırma kirlenmesi.** `h_enj` küçülürken kafes **sabit**
kalıyor; enjeksiyon bölgesindeki parçacık sayısı `1904 → 32`'ye düşüyor.
Enerji birkaç parçacığa yığılınca başlangıç koşulu **kötü örneklenmiş** olur.

İki ayrı imza doğruluyor:

1. **Adım sayısı** `175 → 654`: küçük biriktirme → yüksek enerji yoğunluğu →
   yüksek ses hızı → küçük `dt`.
2. **Trend kırılıyor**: `n_enj = 136` noktası (hata %4,03), kendinden daha
   *geniş* olan `n_enj = 208` (%4,44) ve `552` (%4,46) ile aynı bantta —
   ama daha *dar* olan 56 ve 32 birden %9,6 ve %7,1'e sıçrıyor.

### İki rejim

| rejim | noktalar | hata aralığı |
|---|---|---|
| **az örneklenen** (`n_enj < 100`) | 2 | %7,11 – %9,61 |
| **iyi örneklenen** (`n_enj ≥ 100`) | 4 | **%3,26 – %4,46** |

| uydurma | üs |
|---|---|
| tüm noktalar | `+0,647` — **kirlenmiş, raporlanmaz** |
| yalnız iyi örneklenenler | `+0,264` |

> **Eşiğim çok gevşekti.** `injection_well_sampled` için `n ≥ 20` koymuştum;
> `32` ve `56` parçacıklı noktalar onu geçiyordu ama hâlâ örnekleme hatası
> taşıyorlardı. Eşik **100**'e çıkarıldı ve iki rejim ayrı raporlanıyor.

---

## 3. Asıl bulgu: **hata biriktirme yarıçapına duyarsız**

İyi örneklenen rejimde `r_dep/r_şok` **0,20 → 0,48** (2,4 kat) değişiyor ve
hata **%3,26 – %4,46** arasında kalıyor — **1,21 puanlık** bir yayılım.

### Peki bu ~%4 nereden geliyor?

**KAYIT-023'ten.** Olağan yakınsama kolu `n = 64`'te `r = 0,23874` ölçmüştü,
hata **%4,46**. D-1'in varsayılan noktası (`h_enj = 0,040`) **birebir aynı**
değeri veriyor: `0,23874`.

> **~%4'lük taban, `h` ile sınırlı ayrıklaştırma tabanıdır — biriktirme
> yarıçapının model-form hatası değil.**

Bu, ADR-0011'in *"%3,9 model-form tabanıdır"* atfını **kısmen** düzeltir:
o taban `n ≥ 96`'da bile sürüyordu, ama bu tarama gösteriyor ki taban
biriktirme yarıçapıyla **oynamıyor**. İki etki karışıktı; burada ayrıştılar.

> Not düşülüyor, silinmiyor: ADR-0011'in ölçümü doğruydu; **atfı** eksikti.

---

## 4. D için ne anlama geliyor

> **İyi örneklenen aralıkta gözlenebilir, enerjinin biriktirildiği bölgenin
> yarıçapına neredeyse duyarsız.** Yarıçapı 2,4 kat değiştirmek şok
> yarıçapını yalnızca **1,2 puan** oynatıyor.

Kaynak terimi tam olarak *"enerjiyi belirli bir bölgeye yapısız koy"*
demektir. Ölçüm, bu bölgenin **boyutunun** sonucu güçlü biçimde
belirlemediğini söylüyor — **D'nin lehine**.

### Ama üç sınır var

| # | sınır |
|---|---|
| **1** | Taranan aralık `0,20 – 0,48`. **DART çalışma noktası `0,065 – 0,13`** — yani **altında**. Oraya inmek için daha ince kafes gerekir (`n_side ≥ 128`), yoksa az örneklenen rejime düşülür. |
| **2** | Ölçülen gözlenebilir **şok yarıçapıdır**. β ve krater şekli daha duyarlı olabilir; ölçülmedi. |
| **3** | Sedov **tek malzemeli ve gerilmesizdir**. Gerçek çarpmada mukavemet, gözeneklilik ve hasar var; biriktirme yarıçapının onlarla etkileşimi ölçülmedi. |

**Yani D "temiz" ilan edilemez** — ama karşısına konulacak somut bir kusur
da çıkmadı.

---

## 5. Karar tablosu — altıncı ve son güncelleme

| # | yaklaşım | mermiyi çözer | yapay kuvvet | şok geçişi | **momentum** | **model-form** | mimari bedel |
|---|---|---|---|---|---|---|---|
| ~~A~~ | global `h` | **hayır** | 0,168 | zararsız ✔ | 1e-16 ✔ | — | yok |
| **A′** | parçacık başına `h` | evet | 0,55–1,10 | (A'da zararsız) | 1e-16 ✔ | yok | çekirdek+grid+CFL+Ω |
| **B** | bölme | A′ ile | = A′ | = A′ | = A′ | = A′ | = A′ |
| **C** | iki alan eşlemesi | evet | yok | ölçülmedi | **7,5e-03 ✘ sistematik** | ara değerleme `O(h²)` | iki çözücü + örtüşme + MLS + korunum düzeltmesi |
| **D** | kaynak terimi | **atlar** | yok | — | ✔ | **≤1,2 puan** (dar aralıkta) | ılımlı |

### Ölçümlerin söylediği

- **A elendi** — çözemez.
- **B, A′'nın alt kümesi** — bağımsız seçenek değil.
- **A′**: çözer, momentumu korur, ama **arayüzü 3,2–6,5 kat gürültülendirir**
  ve mimari bedeli en büyüğü.
- **C**: arayüz kaynaklı yapay kuvvet yok, ama **momentumu korumuyor** ve
  kayma **sistematik olarak birikiyor** — üstelik bedeli en karmaşığı.
- **D**: mermiyi atlar, korunumu bozmaz, ve model-form duyarlılığı
  **ölçülen aralıkta düşük**.

**Karar hâlâ yazılmadı** — ama üç ölçülmemiş nokta artık **belirli** ve
küçük: D'nin DART çalışma noktasındaki davranışı, β duyarlılığı ve
mukavemetli malzemedeki etkileşim.

---

## 6. Bu kayıtta uygulanan kurallar

| kural | nerede |
|---|---|
| beklenmedik **işaret** açıklanır, susulmaz | §2 — `p = −0,647` |
| iki rejim varsa **ayrılır**, tek yasa uydurulmaz | §2 |
| kendi eşiğim gevşek çıktıysa **sıkılaştırılır** | §2 — `20 → 100` |
| bir taban başka bir ölçümle **eşleşiyorsa** aynı şeydir | §3 — `0,23874` birebir |
| başka bir belgenin **atfı** düzeltilir, ölçümü değil | §3 — ADR-0011 |
| ekstrapolasyon **açıkça** işaretlenir | §4(1) |
