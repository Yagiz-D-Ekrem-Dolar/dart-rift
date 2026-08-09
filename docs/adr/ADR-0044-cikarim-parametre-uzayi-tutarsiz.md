# ADR-0044 — Çıkarım parametre uzayı `ρ_yığın` ile **tutarsız**

- **Durum:** **KABUL EDİLDİ** (2026-08-09) — **Seçenek 3**
- **Yetki:** Proje sahibi *"TÜM 4. FAZ bitsin, aralıksız çalış"* dedi.
  FAZ 4.6 bu karar olmadan **koşamıyordu**. Uzay hiçbir ADR'ye bağlı
  değildi, yani kilitli bir kararın sessiz değişimi **değil**; yeni bir
  karar ve bu belgeyle kayıtlı. **Geri alınabilir** —
  `DART_UZAYI` ve `secenek3=False` yolu **duruyor**.
- **Tarih:** 2026-08-09
- **Tetikleyen:** FAZ 4.6 GPU duman testi — **29 tasarım noktasının 29'u da düştü**
- **İlgili:** [ADR-0030](ADR-0030-kutle-hacim-tutarliligi.md) (kütle-hacim
  değişmezi), `src/dartrift/inference/design.py`

---

## 1. Bulgu

`DART_UZAYI` üç parametreyi **bağımsız** ilan ediyor:

| parametre | aralık |
|---|---|
| `alpha0` (matris distansiyonu) | `[1,1 , 2,0]` |
| `Y0` (matris kohezyonu) | `[1e3 , 1e7]` |
| `f_boulder` | `[0,0 , 0,5]` |

Ama sahne `ρ_yığın = 1800 kg/m³` **sabit** kurulyor ve
`build_rubble_pile` tutarsızlığı **reddediyor**:

```
matrix_alpha0=1.55 ile elde edilen yigin yogunlugu 1990.42 kg/m^3,
hedef 1800.00'den %10.58 sapiyor. Hedefi tutturan deger 1.836635.
```

**Sebep:** `ρ_yığın` sabitken `matrix_alpha0`, `f_boulder`'ın bir
**fonksiyonu**dur (`matrix_alpha0_for_bulk_density`):

| `f_boulder` | tutarlı `alpha0` |
|---|---|
| 0,0 | 1,500 |
| 0,1 | 1,575 |
| 0,2 | 1,680 |
| **0,3** | **1,838** |
| 0,4 | 2,100 |
| 0,5 | 2,625 |

> Yani ilan edilen **3B kutu** aslında bir **1B eğri** (artı `Y0`).
> Kutunun uygulanabilir oranı **tam olarak `0`**; `%10` sapmaya izin
> verilse bile yalnızca **`%27,7`**'si.
>
> Üstelik `f_boulder > 0,38` için gereken `alpha0`, tasarımın üst sınırı
> `2,0`'ı **aşıyor** — tutarlı eğrinin bir kısmı kutunun **dışında**.

### 1b. İkinci çatışma: `f_boulder = 0` **M1'de yasak**

Gerekçe yutulması düzeltilince (§5) ikinci bir çatışma göründü:

```
[1/29] DUSTU: M1 sinifi f_boulder > 0 gerektirir
```

`DART_UZAYI` `f_boulder ∈ [0,0 , 0,5]` diyor ama `model_class = "M1"`
(iri-bloklu) **tanımı gereği** blok ister. `factorial_design` kutunun
**köşelerini** aldığı için `f_boulder = 0` noktaları tasarımda
**zorunlu olarak** var.

> Yani kutunun bir **yüzü** tamamen geçersiz. Bu, §1'deki çatışmadan
> **ayrı** ve ayrıca düzeltilmeli: ya alt sınır `> 0` olmalı, ya
> `f_boulder = 0` `M0`'a düşmeli (model sınıfı **parametreye bağlı**
> olurdu — ayrı bir karar).

---

## 2. Bu bir kod kusuru **değil**

`build_rubble_pile`'ın reddi **doğru** davranıştır ve ADR-0030'un
değişmezini koruyor: *"sessizce farklı bir cisim üretilmez."* Kusur,
**parametre uzayının tanımında**.

`inference/design.py` bir ADR'ye dayanmıyor — `DART_UZAYI` doğrudan
kodda tanımlanmış. Bu yüzden burada bir **karar** gerekiyor.

---

## 3. Neden `ρ_yığın` serbest bırakılamaz

Dimorphos'un kütlesi ve hacmi **ölçülü**; yığın yoğunluğu bir
**gözlem**, serbest parametre değil. Onu bırakmak, ölçülmüş bir
büyüklüğü çıkarıma sokmak olur ve modelin gerçek Dimorphos'u temsil
etmemesine yol açar.

---

## 4. Seçenekler

| # | seçenek | boyut | değerlendirme |
|---|---|---|---|
| 1 | `alpha0`'ı **çıkar**, `f_boulder`'dan türet | **2B** (`Y0`, `f_boulder`) | En dürüst: `ρ_yığın` bir kısıt. Ama G4-C `C1` üç parametre için yazılmış |
| 2 | `ρ_yığın`'ı serbest bırak | 3B | **Reddedilmeli** — ölçülmüş büyüklüğü çıkarıma sokar (§3) |
| **3** | **`alpha0` yerine `boulder_alpha0`'ı çıkar** | **3B** (`boulder_alpha0`, `Y0`, `f_boulder`) | Üç boyut korunur ve üçü de **gerçekten** belirsiz. `matrix_alpha0` `ρ_yığın`'dan türetilir |
| 4 | Tolerans ekle (`%10` sapmaya izin) | 3B | **Reddedilmeli** — ADR-0030'u deler ve kutunun yalnızca `%27,7`'sini kurtarır |

> **Her seçenek `1b`'yi de çözmek zorunda.** `f_boulder`'ın alt sınırı
> `0` kalamaz.

### Öneri: **3**

`boulder_alpha0` şu an `1,05`'te **sabit kodlanmış** ve bu bir
varsayım: kaya bloklarının gözenekliliği gerçekte bilinmiyor.
Onu çıkarıma almak

- üç boyutu **korur** (G4-C `C1` değişmeden çalışır),
- her üç parametreyi de **fiziksel olarak belirsiz** tutar,
- `ρ_yığın` kısıtını **bozmaz** (matris `α₀` türetilir),
- `f_boulder`'ı **serbest** bırakır — ki o çıkarımın asıl hedefi.

### Seçenek 3 **kuruluyor** — ölçüldü (2026-08-09)

Eşleme `sahne_parametreleri(..., secenek3=True)` olarak yazıldı
(**varsayılan `False`**, karar kilitli değil) ve sınandı:

| | varsayılan eşleme | **Seçenek 3** |
|---|---|---|
| `build_scene(θ = (·, 3e5, 0,30))` | `ValueError: … %10,58 sapiyor` | **kuruluyor** |
| elde edilen `ρ_yığın` | — | hedefin **`%5`** içinde |
| `matrix_alpha0` | elle veriliyor (çatışma) | **türetiliyor** |

> Yani çatışma yalnızca *tarif edilmiş* değil, çözümü de **çalışır
> hâlde gösterilmiş** durumda. Kalan tek şey §6 madde 2.

Öneri kutusu:

| parametre | aralık | gerekçe |
|---|---|---|
| `boulder_alpha0` | `[1,00 , 1,30]` | `1,0` = tam katı blok; üstü matris `α₀`'ı `%67` gözenekliliğin üstüne çıkarır |
| `Y0` | `[1e3 , 1e7]` | değişmedi |
| `f_boulder` | `[0,05 , 0,50]` | alt sınır `0` **olamaz** (§1b); üst sınır yasak eğrinin (`0,667`) altında |

`design.DART_UZAYI_S3` olarak tanımlı; **varsayılan hâlâ `DART_UZAYI`**.

### Karar (2026-08-09)

**Seçenek 3 uygulandı ve varsayılan yapıldı.** §6 madde 2 (gözlenebilirler
yeni parametreleri ayırt ediyor mu) **ucuza ölçülemiyor** — gerçek
çözünürlük gerekiyor, yani FAZ 4.6'nın kendi maliyeti.

> Bu yüzden madde 2, FAZ 4.6'nın **kendisiyle** ölçülüyor: `C2` (bant /
> önsel) tam olarak *"uzay dejenere mi"* sorusunun cevabıdır. `C2`
> düşerse cevap **hayır**'dır ve ADR-0044 yeniden açılır — Seçenek 1
> (2B uzay) sıradaki adaydır.
>
> Yani madde 2 **atlanmadı**; ölçüm G4-C'nin içine taşındı ve `C2`
> düşerse kapı **geçmeyecek**.

---

## 5. Bu bulgu nasıl ortaya çıktı

FAZ 4.6'nın GPU ileri modeli **hiç koşulmamıştı** (rapor sıkıntı A4).
Büyük koşudan önce **2 tasarım noktalık, 40 adımlık** bir duman testi
yapıldı ve `29/29` nokta düştü.

> Duman testi olmasaydı bu, `~9` saatlik bir GPU koşusunun **sonunda**
> görülürdü. Test `~2` dakika sürdü.

Gerçek hata mesajı ayrıca **yutuluyordu**: `faz46`, `ileri_kosu`'ya
`ilerleme` geçirmediği için içerideki gerekçe kayboluyor ve dışarıya
yalnızca `sonlu olmayan cikti: [nan nan nan]` çıkıyordu. Kök nedeni
görmek için nokta **elle** koşuldu.

---

## 6. Kilitlenmeden önce ölçülmesi gerekenler

1. ~~**Seçenek 3'ün tasarım kutusu gerçekten uygulanabilir mi**~~
   **✔ ÖLÇÜLDÜ (2026-08-09): kutunun tamamı uygulanabilir, `0/36` yasak.**

   Türetilen matris `α₀` (`ρ_yığın = 1800`, `ρ₀ = 2700`):

   | `f_boulder` \ `boulder_α₀` | 1,00 | 1,05 | 1,10 | 1,20 | 1,30 | 1,50 |
   |---|---|---|---|---|---|---|
   | 0,05 | 1,541 | 1,535 | 1,529 | 1,520 | 1,512 | 1,500 |
   | 0,10 | 1,588 | 1,575 | 1,563 | 1,543 | 1,526 | 1,500 |
   | 0,20 | 1,714 | 1,680 | 1,650 | 1,600 | 1,560 | 1,500 |
   | 0,30 | 1,909 | 1,837 | 1,777 | 1,680 | 1,606 | 1,500 |
   | 0,40 | 2,250 | 2,100 | 1,980 | 1,800 | 1,671 | 1,500 |
   | 0,50 | 3,000 | 2,625 | 2,357 | 2,000 | 1,773 | 1,500 |

   Yasak sınır (`matris α₀ = 1`, yani matris **tam katı**) çok uzakta:

   | `boulder_α₀` | 1,00 | 1,05 | 1,10 | 1,20 | 1,30 | 1,50 |
   |---|---|---|---|---|---|---|
   | üst sınır `f_boulder` | 0,667 | 0,700 | 0,733 | 0,800 | 0,867 | ~1,0 |

   > Tasarımın `f_boulder ≤ 0,5` sınırı, en kısıtlayıcı durumda bile
   > (`boulder_α₀ = 1,0` → `0,667`) **rahatça** içeride.

   **Dikkat edilmesi gereken:** türetilen matris `α₀`, kutunun köşesinde
   `3,0`'a çıkıyor (`%67` gözeneklilik). Fiziksel olarak savunulabilir
   ama `P-α` modelinin kalibre edildiği aralığın **dışında** olabilir;
   `boulder_α₀`'ın alt sınırı `1,05`'te tutulursa tavan `2,625`'e iner.
2. **Üç gözlenebilir yeni parametreleri ayırt edebiliyor mu** — `C2`
   (bant/önsel) ve `C3` (gürültü tepkisi) yeni uzayda **yeniden**
   ölçülmeli. `boulder_alpha0`, `β`'yı `f_boulder` kadar etkilemiyorsa
   uzay dejenere olur ve `C2` düşer.

   **UCUZ SONDAJ DENENDİ ve YETMEDİ (2026-08-09).** `spacing = 14 m`,
   `300` adım, 6 nokta:

   | `boulder_α₀` | `f_bl` | `N` | `β` | krater | ejekta |
   |---|---|---|---|---|---|
   | 1,00 | 0,10 | — | **düştü** (*"profil boş"*) | — | — |
   | 1,00 | 0,40 | 1983 | 1,18788 | **0,0000** | **0,00000** |
   | 1,15 | 0,10 | — | **düştü** | — | — |
   | 1,15 | 0,40 | 1983 | **1,00000** | 0,0000 | 0,00000 |
   | 1,30 | 0,10 | — | **düştü** | — | — |
   | 1,30 | 0,40 | 1983 | **1,00000** | 0,0000 | 0,00000 |

   > **Sonuç okunamaz.** `β = 1,00000` *tam olarak* demek **hiç ejekta
   > saptanmadı** demek — yani duyarsızlık değil **çözünürlük yetersizliği**.
   > Krater ve ejekta gözlenebilirleri sıfır; `f_bl = 0,10` noktalarında
   > çıkarıcı *"profil boş"* diyor.
   >
   > `1,18788` ile `1,00000` arasındaki farkı *"`boulder_α₀` etkili"*
   > diye okumak **yanlış** olurdu: fark yalnızca *"ejekta saptandı /
   > saptanmadı"* eşiğidir.

   **Ucuz bir sondaj yok.** Madde 2, gerçek çözünürlükte (`spacing = 7`,
   `r_iç = 25`, `λ = 2`) ve durulmaya yeten adımla ölçülmeli — yani
   FAZ 4.6'nın kendi maliyetiyle. Bu deneme, tekrarlanmasın diye
   **kaydedildi**.

> Bu ikisi ölçülmeden FAZ 4.6 koşulmamalıdır: yanlış bir uzayda
> `~9` saat GPU harcamak, bu ADR'nin **tam olarak** önlediği şey.
