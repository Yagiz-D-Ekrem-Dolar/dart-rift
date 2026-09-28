# Çözünürlükler arası standartlaştırma — bütün ölçümler ve kural (2026-09-28)

> **Ne için:** aynı `θ`, farklı sayısal ayar → farklı `β`. Havuzu ucuz ayarla
> koşup sonucu "standart" ayara taşımak istiyoruz. Bu **mühendisliktir**;
> savunulabilir olması için düzeltmenin **ölçülmüş**, **hata paylı** ve
> **kötüye kullanılamaz** olması gerekir.
>
> **Kod:** `src/dartrift/inference/cozunurluk_standardi.py` (+ 8 sınav).
> **Kilitli koşu sonuçları:** `S_UY.json`, `S_UG.json`, `S_A98.json`,
> `S_A98K.json`, `S_A103.json`, `S_A104.json`, `S_A105.json`.
> **Defter:** KAYIT-069. **Karar:** ADR-0052.

---

## 1. Sorunun büyüklüğü: bütün ölçümler alt alta

Hepsi **aynı sahne** (L1 kıyası: küre `a = 75 m`, `ρ = 1600`, 500 kg alüminyum
mermi 6 km/s), **aynı `θ`** (`Y₀ = 10 Pa`, `f = 0,6`), aynı geç evre şeması.

### 1a. Yumuşatma boyu `h` ekseni (`t_geçiş = 0,2 s`, `β(300 s)`)

| kol | aralık `s` | `h/s` | **`h` bağıl** | parçacık | `β` | kaynak |
|---|---|---|---|---|---|---|
| kaba | 1,0 | 2,0 | **1,000** | 14 616 | **3,686** | W2_Y10_g0p2 |
| A104 k15 | 1,0 | 1,5 | **0,750** | 14 616 | **4,023** | A104_k15 |
| UY orta | 0,5 | 2,0 | **0,500** | 66 601 | **3,978** | UY_orta |
| A104 o15 | 0,5 | 1,5 | **0,375** | 66 601 | **4,006** | A104_o15 |
| UY iç | kısmi (≤ 12 m) | 2,0 | — | 48 233 | 3,823 | UY_ic |
| A103 dış | kısmi (dış kuşak) | 2,0 | — | — | 3,762 | A103_dis2 |

**İki okuma:**

1. **`β`, parçacık sayısına değil `h`'ye bağlı.** `k15` kabayla **aynı**
   parçacık sayısına sahip; yalnız çekirdek daraltıldı ve `β` `3,686 → 4,023`
   oldu — orta çözünürlüğün verdiği değerin ta kendisi. 4,5 kat parçacık
   koymakla aynı parçacıkları daha keskin çekirdekle kullanmak aynı şeyi
   yapıyor (A104 kilitli yargısı: "KARIŞIK", eğim `0,58 → 0,22`: yakınsama
   başlıyor).
2. **Eğri doyuyor.** `h ≤ 0,75`'te üç kol `4,023 / 3,978 / 4,006` —
   **`4,00 ± 0,02` (`%0,6`)**. Dışarıda kalan tek nokta en kaba kol.

### 1b. Geçiş anı ekseni (kaba merdiven, `β(600 s)`)

| `t_geçiş` | `β` | L1'e oran |
|---|---|---|
| 0,2 s | 3,667 | 0,88 |
| 1,0 s | 4,070 | 0,97 |
| **2,5 s** | **4,167** | **0,997** |
| **5,0 s** | **4,165** | **0,996** |

`Δ(5,0; 2,5) = 0,0007`. Kilitli yargı (PROTOKOL-UG): **GEÇİŞ YAKINSAMIŞ**,
üretim geçiş anı **1,0 s** (`Δ(1,0; 5,0) = 0,030 ≤ 0,05`).

### 1c. Uzak alan (taban aralık, `β(600 s)`)

| taban | 7 m | 5 m | 3,5 m |
|---|---|---|---|
| `β` | 3,667 | 3,675 | 3,677 |

`Δ ≤ 0,004`. **UZAK ALAN YAKINSAMIŞ** (PROTOKOL-UA). 48 m ötesi `β`'yı
değiştirmiyor.

### 1d. Diğer sayısal eksenler (aynı sahne, kaba kol)

| eksen | değişiklik | `β` | fark |
|---|---|---|---|
| mermi çözünürlüğü | 800 → 6400 parçacık | 3,686 → **3,901** | **+%7,4** (A98 M5) |
| geç evre yapay viskozitesi | `α = 1` → `0,1` | 3,686 → **3,476** | **−%7,8** (A98 M2) |
| matris çekme dayanımı | yok → `T_m = Y₀/μ_f` | 3,686 → **2,854** | **−%23** (A105) |

Yani "çözünürlük" tek bir düğme değil: en az dört sayısal eksen `β`'yı
`%7`'den fazla oynatıyor, biri (**çekme**) modelleme seçimi olarak `%23`.

### 1e. Yapay viskozite kontrollü deneyde (A98K, Maxwell Z kazı akışı)

| geç AV | `Q(s=1)` | `Q(s=0,5)` | `Q(s=0,25)` | çözünürlük bağımlılığı `D` |
|---|---|---|---|---|
| `(1; 2)` varsayılan | 39 069 | 45 283 | 50 233 | **0,222** |
| `(0,1; 0,2)` | 41 617 | 46 965 | 50 116 | 0,170 |
| `(0; 0)` | 45 415 | 47 255 | 51 538 | **0,119** |

Kilitli yargılar: K1 **varsayılan AV'de çözünürlük bağımlılığı var**,
K3 **geç AV küçültmek bağımlılığı kısmen kaldırıyor**, K4 `p = 0,33` →
**birinci mertebe değil**. Ama tam sahnede (A98) AV küçültülünce kaba–orta
farkı **büyüdü** (`0,098 → 0,147`) → A98'in kilitli yargısı: **AV SEBEP
DEĞİL**. Mekanizma tek başına AV değil.

---

## 2. Formül aranıyor: ne çıktı, ne çıkmadı

### 2a. Güç yasası uyar mı

`β(h) = β_∞ − C·h^p` dört ölçülmüş noktaya uyduruldu
(`cozunurluk_standardi.guc_yasasi_uydur`):

    beta_inf = 4,06   C = 0,33   p = 3,0   artik RMS = 0,062

`p ≈ 3` demek hata `h` ile **çok hızlı** ölüyor: bu bir "her çözünürlükte
biraz düzelt" eğrisi değil, **eşik** davranışı. Doyma eşiği `h_bağıl ≈ 0,75`.

### 2b. Tek çarpan

`β − 1` üzerinden **kaba → yakınsak** düzeltmesi:

| eksen | çarpan (`β − 1`) | `β` üzerinden | σ |
|---|---|---|---|
| çözünürlük (`h`) | **1,118** | 1,087 | 0,008 (üç kolun saçılması) |
| geçiş anı | **1,187** | 1,136 | 0,03 (`Y₀`'a göre kayma) |

### 2c. **Tuzak 1 — varsayılan `p` ile iki noktalı ekstrapolasyon**

Elimizde yalnız kaba ve orta olsaydı ve Richardson uygulasaydık:

| varsayılan `p` | formülün dediği `β_∞` |
|---|---|
| 0,33 (A98K'da ölçülen mertebe) | **5,11** |
| 0,5 | 4,68 |
| 1,0 | 4,27 |
| 2,0 | 4,08 |
| **ölçülen** | **4,01** |

`p = 0,33` varsayımı `%27` fazla verirdi. **İki nokta bir formül için
yetmiyor**; üçüncü ve dördüncü kol koşulduğu için bu görüldü.
`richardson_iki_nokta` bu yüzden her çağrıda uyarı döndürür.

### 2d. **Tuzak 2 — iki eksenin çarpanları çarpılmaz**

`1,118 × 1,187 = 1,327` → `β = 4,57`. Oysa:

- **birlikte ölçülen** nokta (kaba merdiven + `t_geçiş = 2,5 s`): **4,167**
- literatür (L1, aynı sahne, aynı `θ`): **4,18**

Çarpım ikisini de `%9`'dan fazla aşıyor. İki hata bağımsız değil; ikisi de
"geç evre akışının ne kadarını koruyabiliyoruz" sorusunu ölçüyor. Aynı şeyi
A103 merdivenin bölgeleri için ölçtü: **katkılar toplamsal değil**
(`Δ_toplam = 0,292`, dış kuşak payı `%26`).

Bu yüzden kodda `carpan_carp(...)` **her zaman hata verir** ve
`standartla(kaynak="kaba@tg0.2", hedef="yakinsak_h@tg_yakinsak")`
**reddedilir**: o dönüşüm ölçülmedi.

---

## 3. Kural (ADR-0052)

1. Standartlaştırma **yalnız ölçülmüş** durum çiftleri arasında yapılır
   (`OLCUMLER` kaydı; her satırda kanıt dosyası ve tarih var).
2. Her düzeltme **hata payı taşır**; `standartla` `beta_sigma` döndürür ve bu
   pay posteriorda model eksikliğine girer (`tarih_esleme`).
3. Çarpanlar `β − 1` üzerinden tanımlıdır (`β = 1` mermi katkısıdır, sayısal
   ayardan etkilenmez).
4. **Ayrı ölçülmüş iki eksenin çarpanı çarpılamaz.** Ortak etki birlikte
   ölçülmelidir.
5. Düzeltme **gözlemi tutturmak için seçilemez**. Kayıttaki sayılar
   koşulardan gelir; değiştirmek yeni koşu ister.

> **Dürüst sınır:** standartlaştırma hatayı **yok etmez**, sadece bilinen bir
> ayara taşır ve belirsizliğini yazar. "Yakınsadı" demek için ölçülmüş
> noktalar gerekir; bizde `h` ekseninde dört, geçiş ekseninde dört nokta var,
> ama **ikisinin kesişiminde bir tane** (kaba + 2,5 s).

---

## 4. Şu an ne biliyoruz, ne bilmiyoruz

| soru | durum |
|---|---|
| uzak alan (≥ 48 m) `β`'yı değiştiriyor mu | **hayır** (`≤ %0,4`), kapandı |
| geçiş anı yakınsıyor mu | **evet**, `t_geçiş ≥ 2,5 s`; üretim `1,0 s` |
| `h` inceltmek `β`'yı ne yapıyor | `+%11,8` (`β − 1`), `h ≤ 0,75`'te doyuyor |
| `β` `N`'ye mi `h`'ye mi bağlı | **`h`'ye** (A104) |
| kaba + doğru geçiş anı literatürü tutuyor mu | **evet**, `4,167` vs `4,18` (`%0,3`) |
| ince + doğru geçiş anı ne verir | **BİLİNMİYOR** — tek eksik koşu |
| mermi parçacık sayısı | `800 → 6400`: `+%7,4`, yakınsamadı |
| matris çekme dayanımı | `β`'yı `%23` düşürüyor; modelleme kararı bekliyor |

**Sıradaki tek belirleyici koşu:** orta merdiven × `t_geçiş = 2,5 s`
(~10–15 GPU-saat). Sonucu:

- `≈ 4,2` → iki eksen birbirini götürmüyor, kaba merdiven + doğru geçiş anı
  üretim için yeterli; çözünürlük düzeltmesi gereksiz.
- `≈ 4,6` → kaba koldaki uyum **tesadüf**; iki hatanın birbirini götürdüğü
  ortaya çıkar ve üretim ayarı yeniden seçilir.

Bu koşu yapılmadan hiçbir üretim havuzu başlatılmamalıdır.
