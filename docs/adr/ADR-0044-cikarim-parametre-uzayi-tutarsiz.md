# ADR-0044 — Çıkarım parametre uzayı `ρ_yığın` ile **tutarsız**

- **Durum:** **ÖNERİLDİ** (kilitli değil — karar proje sahibinin)
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

> Bu bir **öneri**; ölçülmedi. Kilitlenmeden önce §6'daki iki şey
> ölçülmelidir.

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

1. **Seçenek 3'ün tasarım kutusu gerçekten uygulanabilir mi** —
   `boulder_alpha0 × f_boulder` kutusunun her köşesinde
   `matrix_alpha0_for_bulk_density` çözülebiliyor mu, yoksa orada da
   yasak bölgeler mi var?
2. **Üç gözlenebilir yeni parametreleri ayırt edebiliyor mu** — `C2`
   (bant/önsel) ve `C3` (gürültü tepkisi) yeni uzayda **yeniden**
   ölçülmeli. `boulder_alpha0`, `β`'yı `f_boulder` kadar etkilemiyorsa
   uzay dejenere olur ve `C2` düşer.

> Bu ikisi ölçülmeden FAZ 4.6 koşulmamalıdır: yanlış bir uzayda
> `~9` saat GPU harcamak, bu ADR'nin **tam olarak** önlediği şey.
