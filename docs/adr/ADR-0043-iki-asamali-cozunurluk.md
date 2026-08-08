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

## 5. Uygulanması gereken — **mevcut değil**

Bu seçenek bir **kabalaştırma** adımı istiyor: aşama-1'in ince
parçacıkları aşama-2'nin kaba kafesine aktarılmalı.

| gereksinim | neden |
|---|---|
| **kütle** korunmalı | ADR-0030'un değişmezi |
| **momentum** korunmalı | ana ürün `β`; kayıp doğrudan onu bozar |
| **enerji** korunmalı | krater ve ejekta ondan geliyor |
| aktarım hatası **ölçülmeli** | yeni bir model-form hatası kaynağı |

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
2. **Kabalaştırmanın kütle/momentum/enerji hatası** — üçü de ayrı ayrı.
3. **`λ = 19`'da arayüz ne yapıyor** — boşluk 3 yalnızca `λ = 2`'de
   kapandı; `6478:1` oranı ölçülmüş her şeyin ötesinde.
4. **Blok sınırlarının kaba çözünürlükte kalmasının etkisi** (§4b) —
   ince bölgede kaya blokları kaba kafesin çözünürlüğünde temsil
   ediliyor ve bu **ölçülmedi**.

> **Dördü de** ölçülmeden bu ADR **kilitlenmemelidir**. Özellikle 3: A′'nın
> arayüz davranışı yüksek oranda **bilinmiyor** ve KAYIT-024 gürültünün
> oranla **büyüdüğünü** ölçtü.
