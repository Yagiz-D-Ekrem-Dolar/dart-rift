# ADR-0041 — Yerel incelme yaklaşımı: **D önerilir, kalibrasyon şartıyla**

- **Durum:** **ÖNERİLDİ — kilitlenmedi.** Kilitleme kararı proje sahibinindir.
- **Tarih:** 2026-08-04
- **Bağlam:** ADR-0026 (mermi çözünürlüğü tekdüze ağda imkânsız), FAZ 4.1/4.2
- **Kanıt:** KAYIT-019 … KAYIT-029 (on bir kayıt, on iki TRUBA koşusu)
- **İlgili:** ADR-0011, ADR-0013, ADR-0022, ADR-0028, ADR-0030, ADR-0040

---

## 1. Karara zorlayan olgu

ADR-0026 ölçtü:

| büyüklük | değer |
|---|---|
| DART mermisini çapı boyunca 6 parçacıkla çözmek | **1,72e9** parçacık |
| ölçülmüş fizibil üst sınır | **1,12e7** |
| oran | **153×** |

Ve *"yerel incelmenin nasıl yapılacağı FAZ 4'te **ölçümle** seçilecek"* dedi.
Bu ADR o ölçümlerin sonucudur.

---

## 2. Ölçülen seçenekler

| # | yaklaşım |
|---|---|
| **A** | değişken kütle bölgeleri, **tek global `h`** |
| **A′** | değişken kütle **+ parçacık başına `h`** |
| **B** | parçacık bölme (adaptif) |
| **C** | iki alan eşlemesi (örtüşme + hayalet) |
| **D** | mermiyi hiç çözme — momentum/enerji **kaynak terimi** |

---

## 3. Ölçümler ve elemeler

### 3.1 A elendi — çözünürlüğü artırmıyor

`h` **tüm kod tabanında skalerdir** (`solver.py:179`, `solver_solid.py:299`,
`solid_ref.py:46`). Bu bir ayar değil, mimari bir olgu.

Sedov'un tam çözümüne karşı üç kol koşturuldu (**KAYIT-023**, iş 1450829):

| kol | plato | `h → 0` limitinden |
|---|---|---|
| `h/dx = 2` sabit (yani `h → 0`) | **0,24008** | — |
| `h = 0,06250` sabit | **0,25650** | **%6,84** |
| `h = 0,03125` sabit | **0,24303** | **%1,23** |

Üç kol da oturdu. Sabit `h`'de `h/dx` 2,00'den 4,00'e çıkıyor (komşu sayısı
~8 kat) ve sonuç bir platoya oturuyor — ama `h → 0` limitine **gitmiyor**.
`h` yarıya inince plato taşınıyor.

> **Sabit `h`'de ne kadar parçacık eklenirse eklensin, çözülen ölçek
> değişmiyor.**

Ters yol da kapalı: `h`'yi ince bölgeye göre seçmek kaba bölgede `h/dx < 1`
yapar; **ADR-0013** zaten ölçmüş ki `h/dx = 1,25` (65 komşu) **%15,8** hata
verir. `λ = 2` için kaba bölgede `h/dx = 1,0` → 34 komşu → daha kötü.

### 3.2 B bağımsız bir seçenek değil

Bölme `dx`'i küçültür. `h` skaler kaldıkça (3.1) bu **faydasızdır**; anlamlı
olması için parçacık başına `h` gerekir — yani B, A′'nın alt kümesidir.

### 3.3 A′ çözer, ama arayüzü **kötüleştirir**

Dört simetrileştirme biçimi ölçüldü (**KAYIT-024**, iş 1450836), hepsi
momentumu tam koruyor (`< 1e-12`):

| oran | `global_h` | `average_h` | `symmetric_kernel` | `gradh` (Ω) |
|---|---|---|---|---|
| 8:1 | **0,1684** | 1,0998 | 1,6806 | 1,5978 |

Ham ivme de aynı: `1,06e3` vs `6,16e3` (5,8 kat). Kademeli geçiş
(smoothstep, 6·`h` genişliğe kadar) `0,545`'te **doyuyor** — hâlâ 3,2 kat.

`Ω` (grad-h) düzeltmesi **kurtarmıyor**: `Ω`, *düzgün değişen* `h` için
türetilmiştir; **süreksiz** bir sıçramada sıfırıncı mertebe tutarlılığı geri
getirmez.

### 3.4 C momentumu **korumuyor** — ve kayma birikiyor

C'nin çekiciliği ölçümle doğrulandı (**KAYIT-025**): örtüşmeli eşlemede
hiçbir çözücü kütle süreksizliği görmez; ara değerleme bedeli Shepard ile
sabit ve doğrusal alanlarda **makine sıfırı**, karesel `O(h_kaynak²)`.

Ama asıl risk de ölçüldü (**KAYIT-027**):

| λ | kütle oranı | boşluk kontrolü | **momentum kayması** |
|---|---|---|---|
| 1,0 | 1:1 | 2,670e-15 | **2,6696e-15** |
| 2,0 | 8:1 | 2,670e-15 | **7,4599e-03** |
| 3,0 | 27:1 | 2,670e-15 | **5,8491e-03** |

`λ = 1`'de (hayaletler birebir kopya) kayma **makine sıfırı** — ölçümün
doğru kurulduğunun kanıtı. `λ > 1`'de kayma gerçek ve **tamamen sistematik**:

```
vektor [5,0780e+09 ; 4,1788e-07 ; -4,8630e-06]     |x|/|v| = 1,000000
```

Tümüyle basınç gradyanı ekseninde. **Rastgele olsaydı `√N` ile büyürdü; bu
`N` ile büyür.**

A ve A′ momentumu **cebirsel olarak** korur (antisimetri, `1e-16`). C onu
**hiç korumaz** — yalnızca küçük tutar. **On üç mertebe** fark.

C'yi kullanmak ayrıca **doğrusal tutarlı** bir ara değerleyici (MLS/CSPM,
KAYIT-025 §3d) **ve** bir korunum düzeltmesi gerektirir; ikisinin de işe
yarayıp yaramadığı **ayrıca ölçülmelidir**.

### 3.5 Arayüz, şok geçişi açısından **zararsız**

**KAYIT-026** (işler 1450842, 1450837): üç kol aynı global `h` ile.

| oran | kaba | **iki bölgeli** | ince | **taşma** |
|---|---|---|---|---|
| 8:1 (n=48) | 0,24336 | 0,24732 | 0,24701 | %0,125 |
| 8:1 (n=64) | 0,23874 | **0,24337** | 0,24404 | **%0,000** |
| 27:1 (n=64) | 0,23874 | **0,24346** | 0,24435 | **%0,000** |

Üç ön koşul da geçti. Çözünürlük arttıkça taşma **küçüldü**.

> Bu, karar eksenini **arayüz kalitesinden** çıkarıp **çözünürlük** ve
> **korunum** eksenlerine taşır.

### 3.6 D'nin model-form duyarlılığı ~~düşük~~ — **DÜZELTİLDİ, bkz. §3.7**

**KAYIT-028** (iş 1451137): kaynak terimi *"aynı enerji, yapısız"* demektir;
sorusu **gözlenebilirin biriktirme yarıçapına duyarlılığıdır**. Sedov'un tam
çözümü `r_dep → 0` limitidir, yani doğrudan referans.

İyi örneklenen rejimde (`n_enj ≥ 100`):

| `r_dep/r_şok` | hata |
|---|---|
| 0,2001 | %4,03 |
| 0,2401 | %4,44 |
| 0,3201 | %4,46 |
| 0,4802 | %3,26 |

Yarıçap **2,4 kat** değişiyor, hata **1,21 puan** oynuyor.

Ve ~%4'lük taban **biriktirme yarıçapından gelmiyor**: KAYIT-023'ün `n = 64`
ayrıklaştırma platosu (`0,23874`) ile **birebir aynı**.

### 3.7 DÜZELTME — §3.6'nın aralığı **DART bandını içermiyordu**

**KAYIT-029** (işler 1451183, 1451261): `n_side = 128` ile DART bandına
inildi ve **altı noktanın hepsi** iyi örneklendi (`n_enj ≥ 136`).

| `r_dep/r_şok` | `n_enj` | hata | **taban üstü fazlalık** |
|---|---|---|---|
| 0,3201 | 4632 | %3,87 | ~0 *(taban)* |
| 0,2401 | 1904 | %4,94 | %1,1 |
| 0,2001 | 1088 | %5,97 | %2,1 |
| 0,1601 | 552 | %7,75 | %3,9 |
| 0,1200 | 208 | %9,62 | %5,7 |
| **0,1000** | 136 | **%10,41** | **%6,5** |

Hata **monoton**; yarıçap 3,2 kat küçülünce hata **2,7 kat** büyüyor.
**DART bandında (`0,065–0,13`) model-form hatası ~%5–7.**

İkinci gözlenebilir de duyarlı: kinetik enerji kesri `0,210 → 0,127`
(nokta patlaması değeri `0,28`'den **%25–55** uzak).

> §3.6 silinmiyor: ölçümü ve iki rejim ayrımı doğruydu; **aralığı**
> DART çalışma noktasını içermiyordu ve yargısı o yüzden yanlıştı.

---

## 4. Karar tablosu

| # | mermiyi çözer | yapay kuvvet | şok geçişi | **momentum** | model-form | mimari bedel |
|---|---|---|---|---|---|---|
| ~~A~~ | **hayır** | 0,168 | zararsız ✔ | 1e-16 ✔ | — | yok |
| **A′** | evet | **0,55–1,10** | (A'da zararsız) | 1e-16 ✔ | yok | çekirdek + hash-grid + CFL + Ω |
| ~~B~~ | A′ ile | = A′ | = A′ | = A′ | = A′ | = A′ |
| **C** | evet | yok | ölçülmedi | **7,5e-03 ✘ sistematik** | ara değerleme `O(h²)` | iki çözücü + örtüşme + MLS + korunum düzeltmesi |
| **D** | **atlar** | yok | — | ✔ (tek çözücü) | **%5–7** (DART bandı, §3.7) | ılımlı + **kalibrasyon** |

---

## 5. Öneri: **D**, A′ yedekte

### Gerekçe

1. **C elenmeli.** Momentumu sistematik olarak kaybediyor ve kayıp `N` ile
   birikiyor. Bu, β gibi **momentum-türevi** bir gözlenebilirin ana
   ürününü doğrudan zehirler. Düzeltilebilir ama düzeltme de ölçüm ister —
   ve bedel zaten en büyüğüydü.

2. **D, ADR-0028'in bilinen kusurunu ortadan kaldırıyor.** Uzun koşu
   kararlılığında ejekta sayısı **tam 1009**'da donmuştu; bu, merminin kendi
   parçacık sayısıdır — yani ölçülen şey **merminin geri sıçramasıydı**,
   ejekta değil. D'de mermi parçacığı **yoktur**; geri sıçrayacak bir şey de
   yoktur.

3. ~~**D'nin ölçülen model-form duyarlılığı düşük** (§3.6)~~ —
   **BU MADDE GEÇERSİZ** ([KAYIT-029](../defter/KAYIT-029_2026-08-04_D1b-duzeltme-kaynak-terimi-duyarli.md)).
   §3.6'nın dayandığı tarama DART çalışma noktasının **üstündeydi**.
   `n_side = 128` ile banda inildiğinde hata **monoton ve güçlü**:
   `%3,87 → %10,41`; taban üstü fazlalık DART bandında **%5–7**. Kinetik
   enerji kesri de duyarlı (`0,210 → 0,127`, nokta değerinden %25–55 uzak).
   **Doğrusu:** D korunumu bozmuyor, ama **model-form duyarlılığı düşük
   değil** ve biriktirme yarıçapı **kalibre edilmesi gereken serbest bir
   parametredir**.

4. **A′ yedek olarak durmalı**, elenmemeli: çözer ve momentumu korur.
   Bedeli mimari; arayüz gürültüsü ise (§3.5) şok geçişinde ölçülebilir
   etki yaratmıyor.

> **KAYIT-029 sonrası denge:** A′ ile D arasındaki fark **D'nin aleyhine
> kaydı.** A′'nın model-form hatası **yoktur** (mermiyi gerçekten çözer);
> D'ninki DART bandında %5–7. D hâlâ savunulabilir — ama ancak biriktirme
> yarıçapı **çözülmüş bir referansla kalibre edilirse** (D-2, ölçülmedi).
> Öneri bu yüzden **kilitlenmemiştir**.

### Bu öneriyi **kilitlemeden önce** kapatılması gereken üç boşluk

| # | boşluk | neden |
|---|---|---|
| ~~1~~ | ~~D'nin DART çalışma noktası taranan aralığın dışında~~ | **KAPATILDI (KAYIT-029):** `n_side=128` ile inildi; hata %5–7 çıktı ve §5 öneri gerekçesi düzeltildi |
| ~~2~~ | ~~ölçülen gözlenebilir yalnızca şok yarıçapı~~ | **KISMEN KAPATILDI (KAYIT-029 §2):** kinetik enerji kesri de ölçüldü ve **duyarlı** (`0,210 → 0,127`). Gerçek β hâlâ ölçülmedi. |
| **3** | Sedov **gerilmesiz ve tek malzemeli** | mukavemet, gözeneklilik ve hasarla etkileşim ölçülmedi |

> **Bu üçü kapanmadan ADR kilitlenmemelidir.** Kanıtsız kilitlenmiş bir
> mimari karar, bu projenin kurallarına aykırıdır.

---

## 6. Sonuçlar

- (+) Karar uzayı **ölçümle** beşten ikiye indi; elemelerin her biri bir
  ölçüme dayanıyor, tercihe değil.
- (+) `h`'nin skaler olması artık **yazılı** bir kısıt (§3.1); daha önce
  örtük bir varsayımdı.
- (+) C'nin korunum kusuru **erken** bulundu — uygulanmadan önce.
- (−) D seçilirse mermi **hiçbir zaman çözülmeyecek**; merminin iç yapısına
  bağlı hiçbir soru sorulamaz. Bu bir **kapsam daraltmasıdır** ve açıkça
  kabul edilmelidir.
- (−) §5'teki üç boşluk kapanana kadar karar **askıdadır** ve FAZ 4.3
  (uygulama) başlayamaz.

---

## İlgili testler ve modüller

`src/dartrift/validation/`: `mass_ratio`, `resolution_scaling`, `variable_h`,
`shock_interface`, `domain_coupling`, `coupling_conservation`,
`deposit_radius`
`tests/`: `test_mass_ratio_probe`, `test_variable_h`,
`test_shock_interface_ic`, `test_domain_coupling`,
`test_coupling_conservation`, `test_faz4_gpu_paths`
