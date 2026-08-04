# KAYIT-025 — C (iki alan eşlemesi) bedelini nereden ödüyor? (2026-08-04)

**Kapsam:** FAZ 4.2 karar verisi · **Durum:** ara değerleme bedeli ölçüldü,
**korunum ölçülmedi**
**Öncül:** [KAYIT-024](KAYIT-024_2026-08-04_degisken-h-arayuzu-kotulestiriyor.md) §6

---

## 0. Kapatılan boşluk

KAYIT-024 §6 açıkça bıraktı:

> C'nin arayüzü de iki farklı `h`'nin buluştuğu yerdir. Eşleme, sınır boyunca
> **doğrudan SPH toplamıyla** yapılırsa **C yerel olarak A′'ya eşittir**.
> Örtüşme bölgesi + ara değerleme yapılırsa farklı olabilir — **ama bu
> ölçülmedi.**

Bu kayıt o ölçümü yapar.

---

## 1. C'nin mekanizması neden farklı

Örtüşmeli eşlemede **hiçbir çözücü kütle süreksizliği görmez**:

- **İnce alan** yalnızca **ince** parçacıklar görür; örtüşme bandındaki
  hayaletler de incedir ve kaba çözümden **ara değerlenerek** üretilir.
- **Kaba alan** yalnızca **kaba** parçacıklar görür.

Yani sıfırıncı mertebe tutarlılık her iki alanda **tam** kalır — her biri
kendi düzgün kafesindedir. A′'nın 3,2–6,5 katlık cezası **hiç doğmaz**.

Bedel başka yerden gelir: **hayaletleri üretirken yapılan ara değerlemeden.**

---

## 2. Ölçüm

SPH ara değerlemesi `f_i = Σ_j (m_j/ρ_j) W_ij f_j`, üç alan üzerinde:

| sınav | doğru cevap | ne ölçer |
|---|---|---|
| sabit (`f = 1`) | tam `1` | sıfırıncı mertebe |
| doğrusal (`f = x`) | tam `x` | birinci mertebe |
| karesel (`f = x²`) | `x² + c·h²` | çekirdeğin doğal yumuşatması |

`h` **kaynağın** çözünürlüğüne bağlıdır: hayaleti üreten alan kendi
çekirdeğiyle ara değerler.

### Ham toplam — taban görünüyor

| durum | yön | sabit | doğrusal | birim bölünmesi sapması |
|---|---|---|---|---|
| λ=1 | her ikisi | 9,501e-03 | 9,501e-03 | 9,501e-03 |
| λ=2 | ince→kaba | 9,501e-03 | 9,501e-03 | — |
| λ=4 | kaba→ince | 9,501e-03 | 9,048e-03 | — |

**Boşluk kontrolü düştü — ve bilgi verdi.** λ=1'de (aynı kafes) bile hata
`9,5e-03`. Bu bir *eşleme* hatası değil: `h/dx = 1,3`'te SPH toplamının
**birim bölünmesi açığı** (%0,95). Ve çözünürlük sıçraması buna **hiçbir şey
eklemiyor** — dört basamağa kadar aynı sayı.

### Shepard normalize — gerçek uygulamanın hâli

Gerçek bir uyarlamada `f/Σw` kullanılır ve açık **tanım gereği** kapanır:

| durum | yön | sabit | doğrusal | **karesel** |
|---|---|---|---|---|
| **λ=1 (taban)** | her ikisi | 1,332e-15 | 1,599e-15 | **1,774e-02** |
| λ=2 (8:1) | **ince→kaba** | 1,332e-15 | 8,882e-16 | **3,080e-03** |
| λ=2 (8:1) | kaba→ince | 1,332e-15 | 1,599e-15 | 1,822e-02 |
| λ=4 (64:1) | **ince→kaba** | 4,441e-16 | 8,882e-16 | **5,657e-04** |
| λ=4 (64:1) | kaba→ince | 1,332e-15 | **8,868e-04** | 1,792e-02 |

---

## 3. Okuma

### (a) Sabit ve doğrusal alanlar **makine hassasiyetinde**

Shepard + simetrik komşuluk ⇒ `Σ w·(x_j − x_i) = 0` ⇒ birinci mertebe tam.
Ara değerleme **hiç hata katmıyor** — hata ancak **eğrilikten** başlıyor.

### (b) Karesel hata **kaynağın `h²`'siyle** ölçekleniyor

| yön | h_kaynak / h_taban | karesel hata / taban | `(h/h₀)²` |
|---|---|---|---|
| λ=2 ince→kaba | 1/2 | 0,174 | 0,25 |
| λ=4 ince→kaba | 1/4 | 0,032 | 0,0625 |

Ölçülen oranlar `h²`'den **daha iyi**. Yani **ince→kaba yönünde ara değerleme
bedeli çözünürlük oranıyla küçülüyor**: kütle oranı büyüdükçe bu yöndeki
eşleme **daha ucuz** oluyor.

### (c) Kaba→ince yönünde kaba `h`'nin hatası **kalıyor** (1,79e-02)

Beklenen ve kaçınılmaz: kaba veriden ince çözünürlükte bilgi **üretilemez**.
C'nin ince alanı, sınırından `h_kaba` ölçeğinde yumuşatılmış bir bilgi alır.

### (d) λ=4'te kaba→ince **doğrusal** hata belirdi: `8,868e-04`

Diğer tüm doğrusal hatalar `~1e-15`. Sebebi simetri: Shepard'ın birinci
mertebeyi tam vermesi, hedefin donör kafesinin bir **simetri noktasında**
olmasını gerektirir. λ=2'de ince noktalar kaba noktalara ya da tam ortalarına
düşer (simetri korunur); **λ=4'te çeyrek noktalar simetriyi kırar.**

Bu, standart SPH ara değerlemesinin bilinen eksikliğidir ve **doğrusal
tutarlı** bir ara değerleyici (MLS / CSPM) ile kapatılır. Yani C'yi seçmek
bu ek bileşeni de gerektirir.

---

## 4. C ile A′'nın kıyası — ve kıyasın sınırı

| | A′ | C |
|---|---|---|
| **yapay kuvvet** (arayüzde) | `0,55–1,10` (global `h`'nin 3,2–6,5 katı) | **hiç doğmuyor** — her alan kendi düzgün kafesinde |
| **ek hata mekanizması** | yok | ara değerleme: sabit/doğrusal **makine sıfırı**, karesel `O(h_kaynak²)` |
| **çözünürlük oranıyla** | **kötüleşiyor** | ince→kaba yönünde **iyileşiyor** |
| **mimari** | çekirdek + hash-grid + CFL + `Ω` | iki çözücü + örtüşme + ara değerleme (+ MLS) |

> **Uyarı:** iki sütun **aynı büyüklüğü ölçmüyor.** A′'nınki bir *ivme*,
> C'ninki bir *alan* hatasıdır. Doğrudan sayısal kıyas yapılamaz. Kurulan
> şey niteliksel ama sağlam: **C'de arayüz kaynaklı yapay kuvvet mekanizması
> yoktur.**

---

## 5. C'nin ölçülmemiş — ve muhtemelen asıl — riski: **korunum**

A ve A′ momentumu **tam** korur (ölçülen `< 1e-12`, KAYIT-020 §1 ve
KAYIT-024 §1), çünkü kuvvet biçimi antisimetriktir: `f_ij = −f_ji`.

**Örtüşmeli eşlemede bu güvence yoktur.** Hayaletler *dayatılır*, dinamik
olarak eşleşmez; bir alanın hayalete uyguladığı kuvvetin karşılığı diğer
alanda görünmez. Örtüşen alan yöntemlerinin bilinen zayıf noktası tam
budur.

> **C'yi seçmeden önce ölçülmesi gereken:** eşlenmiş sistemde toplam
> momentum ve enerji ne kadar kayıyor, ve bu kayma **birikiyor mu**?

Bu, bu kayıtta **ölçülmedi**. Ölçülmeden C "temiz" sayılamaz — KAYIT-024
§6'daki kuralın kendisi budur.

---

## 6. Karar tablosu — üçüncü güncelleme

| # | yaklaşım | mermiyi çözer | yapay kuvvet | ek hata | mimari bedel |
|---|---|---|---|---|---|
| ~~A~~ | global `h` | **hayır** | 0,168 | — | yok |
| **A′** | parçacık başına `h` | evet | **0,55–1,10** | — | çekirdek+grid+CFL+Ω |
| **B** | bölme | A′ ile | = A′ | — | = A′ |
| **C** | iki alan eşlemesi | evet | **yok** | ara değerleme `O(h²)`; **korunum ölçülmedi** | iki çözücü + örtüşme + MLS |
| **D** | kaynak terimi | **atlar** | yok | model-form **ölçülmedi** | ılımlı |

**Karar hâlâ verilmedi.** Kalan iki ölçüm belirli:

| # | ölçüm | neden belirleyici |
|---|---|---|
| **C-2** | eşlenmiş sistemde momentum/enerji kayması | C'nin *asıl* riski |
| **D-1** | kaynak teriminin model-form hatası | çözülmüş referans 1,72e9 parçacık ister → **dolaylı** kıyas tasarlanmalı |

---

## 7. Bu kayıtta uygulanan kurallar

| kural | nerede |
|---|---|
| normalize etmemek **bilinçli**: Shepard sıfırıncı mertebeyi tanım gereği düzeltir ve sınavı boşaltırdı | §2 |
| boşluk kontrolü düşerse **bilgi verir** | §2 — λ=1'de `9,5e-03` taban ortaya çıktı |
| ölçüm = **taban + sinyal** (K18) | §2 — sıçrama tabana hiçbir şey eklemiyor |
| beklenmedik sayı **açıklanır**, susulmaz | §3(d) — λ=4 simetri kırılması |
| iki farklı büyüklük **kıyaslanamaz**, sınırı yazılır | §4 uyarı |
| ölçülmemiş bir seçenek **temiz** sayılmaz | §5 — korunum |
