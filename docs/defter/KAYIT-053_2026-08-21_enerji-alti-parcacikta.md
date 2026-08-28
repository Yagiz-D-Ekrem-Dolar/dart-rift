# KAYIT-053 — Çarpma enerjisinin `%78`'i altı parçacıkta; iki gözlenebilir kırık çıktı (2026-08-21)

**Kapsam:** A17 · A19 · A20 · A21 · ADR-0048
**Öncül:** [KAYIT-052](KAYIT-052_2026-08-21_truba-moloz-yigini.md)
**Koşular:** TRUBA `1515233`, `1515252`, `1515317`, `1515337`, `1515364`,
`1515367` · yerel RTX 3050

---

## 1. Nereden başladım: `μ = 80`

Önceki kayıt *"blok `Y0` hiç taranmadı"* ile kapanmıştı. Bu turda
önce şunu ölçtüm: mermi neye çarpıyor?

| | |
|---|---|
| merminin kütlesi | `579,4 kg` |
| çarptığı hedef parçacığı (`λ₂ = 2`) | `4,66e4 kg` |
| **oran `μ`** | **`80,4`** |

Ve şok hedefe **girmiyordu**: `u_hedef/u_mermi = 0,0016`.

`λ₂` `6` ve `8`'e çıkarılınca (`μ = 2,98` ve `1,26`) oran `0,73` oldu
— hedefin en sıcak parçacığı `8 993 -> 3,36e6 J/kg`, **`370` kat**.
Eşleşme düzeldi. `A1` üç kolda da tam `2,039` kaldı, yani tarama
gerçekten tek değişkenliydi.

**Ama `β` yükselmedi** (`1,411 -> 1,290`). Ve *"ilk kez hedef
ejektası"* diye görünen `108,71 kg`, iki koşuda **bit düzeyinde
aynı** çıkınca ayrıştırdım: iki parçacık, `54,357 kg` × 2, ve
kütleleri ne `λ₂ = 6` ne `λ₂ = 8` ızgarasına ait — **aşama-1'in
kabalaştırılmış siteleri**. Krater ejektası değil.

---

## 2. Bütün elemelerin geçersiz olabileceğini fark ettim

`μ = 80`'de şok hedefe girmiyorsa, **hedefe ait hiçbir şeyin etkisi
ölçülemez**. Bu projedeki bütün elemeler — hasar, matris `Y0`, blok
`Y0`, gözeneklilik, yerçekimi, süre — o rejimde yapılmıştı.

> Bir şeyin etkisiz olduğunu, etki edeceği fiziğin hiç oluşmadığı bir
> koşuda ölçmek: bu deponun **üç kez** kaydettiği hata. Bu sefer
> kendi elemelerimin tamamına uyguladım.

`λ₂ = 8`'de dört kol koşuldu (üretim / hasarlı / zayıf / ikisi).
Sonuç §5'te — ama önce ölçmeye çalıştığım şeyin kendisi kırık çıktı.

---

## 3. A19: krater çıkarıcısı **yokken var, varken yok** diyor

Şekil ölçütünü uygulayacaktım; önce çıkarıcıya **boş sınav** verdim.

| sınav | olması gereken | ölçülen |
|---|---|---|
| pürüzlü yüzey, çarpma **yok** | `0` | `0,26 m` |
| ensemble yolu, çarpma **yok** (40 nokta) | `0` | **`10,85 m`** |
| gerçek `12 m` çukur, `508` parçacık kazılmış | `~12 m` | **`-0,03 m`** |

Raporlanan derinliğin **`%67,7`**'si tabandı. Ve vekil hangi kısmın
parametrelerle açıklandığını söyledi:

| | `q2` |
|---|---|
| SON (raporlanan) | `0,2769` |
| REF (çarpmasız taban) | `0,1287` |
| **fark (gerçek krater)** | **`-0,3283`** |

`G4-C`'nin `q2 = 0,907`'lik güzel korelasyonu **tabandan** geliyordu:
`boulder_alpha0` ve `f_boulder` yüzeyin pürüzünü belirliyor, çıkarıcı
pürüzü derinlik sanıyordu.

### Çare

`krater_yerdegistirme`: **aynı parçacıkların yer değiştirmesi**,
mutlak yarıçap değil. Pürüz `x` ve `x_reference`'ta aynı olduğu için
**farkta çıkar gider** — yaklaşım değil, cebirsel özdeşlik.

| sınav | eski | **yeni** |
|---|---|---|
| kimildamamış, pürüzlü | `0,26 m` | **`0`** |
| gerçek `12 m` çukur | `-0,03 m` | **`9,29 m`** |
| krater yokken çap | `0,0` | **`nan`** |

### Ve gerçek krater ortaya çıktı: **`9 cm`**

| kol | derinlik |
|---|---|
| üretim (`λ₂ = 2`) | `0,0849 m` |
| `λ₂ = 8` | `0,0923 m` |
| ensemble (40 nokta) | medyan **`0,0099 m`** |

Bu depoda `15,28 m` diye taşınan sayı baştan sona **çıkarıcı
artığıydı**.

---

## 4. A20: uzun koşu **sessizce** kesilmişti

`t_end = 20 s` istenen koşu `azami_adim = 200 000`'de durdu:
`t_sim = 7,72 s` (istenenin `%39`'u), **çıkış kodu `0`**, dosya adı
hâlâ `_t20`. Kısa kalmış bir koşu tam koşmuş gibi kaydedilmişti.
Okuduğum için yakalandı. `_kos` artık `RuntimeError` atıyor.

Uzun koşunun kendisi de bir şey söyledi: `bekleyen` (içeride dışarı
giden madde) `0 -> 5 000–14 000`, yani **kazı akışı doğuyor** — ama
yüzey profili eksene yakın **pozitif**: yüzey çökmüyor, **kabarıyor**.
Model kazmıyor, **çınlıyor**.

---

## 5. A21: enerji nereye gitti — **altı parçacığa**

Farklı bir açıdan baktım. Gelen `1,0939e10 J`:

| | enerji | pay |
|---|---|---|
| hedefte iç enerji | `9,2822e9 J` | `%84,9` |
| **bunun `6` parçacıkta olanı** | **`8,5548e9 J`** | **`%78,2`** |
| hedefte kinetik | `1,0339e8 J` | `%0,9` |
| mermide | `1,4312e9 J` | `%13,1` |

O `6` parçacık hedef kütlesinin **`%0,002`**'si. Çarpma bölgesinde
medyan `u = 0,49 J/kg` ve **medyan yoğunluk `1537,2`** — yani
`ρ₀/α₀`'ın tam kendisi, hiç değişmemiş.

> **Şok yayılmıyor.** Kraterin olmaması, ejektanın olmaması ve
> `β`'nın hedeften beslenmemesi üç ayrı sorun değil; üçü de bunun
> sonucu.

### İki mekanizma bulundu

**(a) `u < 0` sızıntısı.** `tillotson_p` basıncı hesaplarken
`u = max(u_in, 0)` diyor ama durum değişkeni kırpılmıyor. Hedef
parçacıklarının **`%44,5`**'i negatife düşmüş (tek aşamalı kolda
gelen enerjinin `%2,76`'sı). Defter (`Σ m u`) korunuyor ama dinamiğin
gördüğü enerji farklı. Çare: `kick_u_3d_tabanli` — taban **ve**
kırpılanın defteri; **varsayılan kapalı**, çünkü açmak bütün kayıtlı
sayıları değiştirir ve bu bir karar.

**(b) Yetim parçacıklar.** `40` parçacığın `2h = 14 m` içinde hiç
komşusu yok; `409,6 kg` (merminin `%71`'i) ve gelen enerjinin
**`%17,7`**'sini taşıyorlar. Komşusuz bir parçacığın `P dV`'si
yoktur: iç enerjisi **işe dönüşemez**.

Kaynağı bulundu: `h` **zamanla güncellenmiyor** — ADR-0042'nin
kilitlediği karar. O ADR'nin kanıtı komşu sayısının *çalışma
noktasındaki* salınımını ölçmüştü; **genleşen** maddede ne olduğunu
ölçmemişti. Kararı çürütmüyor, kapsamını düzeltiyor.

---

## 6. Yakınsama denetimi: **iki düğme düşüyor**

Sekiz ayrıklaştırma düğmesi tek tek tarandı (yeni araç,
`yakinsama_denetimi.py`):

| düğme | bağıl fark | yargı | mertebe |
|---|---|---|---|
| **`lam1`** | `2,35e-01` | **DÜŞTÜ** | `2,07` |
| **`spacing`** | `1,46e-01` | **DÜŞTÜ** | — |
| `r_ince1` | `9,17e-02` | geçti (kıl payı) | — |
| diğer beşi | — | geçti | — |

`spacing` bugüne kadar **hiç taranmamıştı**. Ve en önemli ders:

> `lam2` `β`'yı `%5` oynatıp *"geçti"* dedi. **Aynı** düğme, aynı
> taramada, hedefin iç enerjisini **`450` kat** değiştirdi. Bir
> gözlenebilirin yakınsama testini geçmesi, **fiziğin yakınsadığı
> anlamına gelmiyor.**

---

## 7. Dış kıyas (ilk kez)

π-grubu ölçeklemesi (Holsapple 1993; Housen & Holsapple 2011), dört
malzeme ailesi taranarak: çap **`13,3 – 85,6 m`** beklenirken model
`7,49 m` (eski ölçüyle) — en sert kaya ailesinin bile altında.
Malzemeden bağımsız şekil kıyası: `d/D = 2,04` vs literatür
`0,15 – 0,30`.

---

## 8. Bu turda **kendi hatalarım**

- `β` için `1,3 ≤ β < 2,0 -> kısmi` bandı: taban değerin kendisi o
  bandın içindeydi. **Kötü eşik.**
- A11'de *"benzersiz değer = 40 -> CANLI"*: `np.unique` **kayan nokta
  gürültüsünü** sayıyordu; gerçek seviye sayısı `2`.
- `d/D ≤ 0,50 -> mekanizma bulundu`: ölçülen `0,005` ve dal teknik
  olarak ateşledi, ama sebebi çanak değil çukurun `9 cm` olmasıydı.
  **Başarı diye okumadım.**
- Krater bölgesini bir kez **çarpma noktasının antipodundan** ölçtüm.
- A11 ensemble'ında `λ₂` **ve** `n_bins` birlikte değişti — kendi
  tek-değişkenli kuralımı çiğnedim ve sonucun yanına yazdım.

---

## 9. Ne **yapılmadı**

- `β` hâlâ `3,2225` üretilmiyor ve bu turda üretilmedi.
- A21'in çaresi (`--u-tabani`) **açık/kapalı karşılaştırması
  koşulmadı**.
- Gözeneklilik kolu `μ ≈ 3`'te koşuyor; sonucu bu kayıtta yok.
- ADR-0046, ADR-0047 ve ADR-0048 kararları kullanıcıda.
