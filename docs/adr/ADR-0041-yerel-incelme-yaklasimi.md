# ADR-0041 — Yerel incelme yaklaşımı: **her seçeneğin ölçülmüş bir bedeli var**

- **Durum:** **ÖNERİLDİ — kilitlenmedi.** Kilitleme kararı proje sahibinindir.
- **Tarih:** 2026-08-04
- **Bağlam:** ADR-0026 (mermi çözünürlüğü tekdüze ağda imkânsız), FAZ 4.1/4.2
- **Kanıt:** KAYIT-019 … KAYIT-032 (on dört kayıt, on üç TRUBA koşusu + üç CPU ölçümü)
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

### 3.8 D'nin serbest parametresi **bağlanamadı** (KAYIT-030)

KAYIT-029, `r_dep`'in **kalibre edilmesi gereken serbest bir parametre**
olduğunu söylemişti. **KAYIT-030** (iş 1451309) o kalibrasyonu denedi:
enerjiyi *ısı* yerine **toplu hareket** olarak taşıyan bir **piston**
kuruldu (gerçek merminin yaptığı) ve eşleşen `r_dep` arandı.

**Sonuç: eşleme tek parametreyle yapılamıyor.**

| `R` | `r_dep` eşdeğer | `KE/E` piston | `KE/E` biriktirme | uyuşmazlık |
|---|---|---|---|---|
| 0,0250 | 0,04435 | 0,17313 | 0,15121 | **%14,5** |
| 0,0350 | 0,05235 | 0,18814 | 0,15939 | **%18,0** |

Şok yarıçapı eşleşirken kinetik enerji kesri **%14,5–18,0** ayrışıyor.
Piston enerjiyi hareket olarak taşıyıp şokta ısıya çevirir; biriktirme onu
baştan ısı koyar — geç zamandaki kinetik/termal bölüşüm yapısal olarak
farklı kalıyor. **Bir tek sayı iki bağımsız büyüklüğü ayarlayamaz.**

β momentum-türevidir ve bu bölüşüme **doğrudan** bağlıdır.

> Betiğin ilk çıktısı `TASINABILIR: True` idi ve **yanlıştı**: dört
> pistonun ikisi aralık dışındaydı ve `np.interp` onları uç değere
> **kelepçeleyip** uydurma oranlar üretmişti. Düzeltildi; aralık dışında
> oran `NaN`, ve eşik `≥ 3` nokta oldu.

### 3.9 A′'nın mimari bedeli: **çok seviyeli komşu arama zorunlu** (KAYIT-031)

Kalan tek ölçülmemiş kefe dolduruldu — ve **terazi devrildi**.

`hash_grid.build(x, support)` **tek bir** destek yarıçapı alır
(`hash_grid.py:42,47`; `density.py:26`; `forces.py:54`). Parçacık başına
`h` ile ızgara **en büyük** desteğe göre kurulmak zorundadır; ince
parçacıklar gereğinden çok aday tarar.

**Ölçüldü** (boşluk kontrolü: `λ=1` → israf **tam 1,000**):

| λ | kütle oranı | tasarruf | israf | **NET** |
|---|---|---|---|---|
| 1,26 | 2:1 | 1,90× | 1,32× | 0,694 |
| 1,59 | 4:1 | 3,54× | 2,30× | 0,650 |
| 2,00 | 8:1 | 5,99× | 5,13× | 0,857 |
| **2,52** | **16:1** | 9,45× | **10,06×** | **1,065** |

**Tasarruf doğrusal, israf küpsel.** 8:1'de kazanç yalnızca %14;
**16:1'de A′ her yeri inceltmekten %6,5 daha pahalı.** ADR-0026 ise DART
için **153×** istiyor.

> **Tek ızgarayla A′, DART'ın ihtiyaç duyduğu oranlarda kazandırmıyor;
> kaybettiriyor.** A′'nın bedeli, parçacık başına `h` (68 site) ve `Ω`'nın
> yanında **çok seviyeli komşu aramayı** da içerir — bu bir iyileştirme
> değil, **ön koşuldur**.

### 3.10 Çok seviyeli ızgara israfı **tam** kaldırıyor (KAYIT-032)

§3.9 çok seviyeli aramayı **ön koşul** ilan etti — ama işe yarayıp
yaramadığı ölçülmemişti. *"Ön koşul"* demek onun çalıştığını **varsaymaktır**.

Doğru sorgu: simetrik biçimde `(i,j)` çiftinin yarıçapı `h_i + h_j`'dir;
parçacık `i` **her seviye** `L`'yi `h_i + h_L` ile sorgular.

| λ | oran | tek ızgara (genel) | **çok seviye (genel)** | kazanç |
|---|---|---|---|---|
| 1,00 | 1,0 | 1,000 | **1,000** | 1,00× |
| 1,26 | 2,0 | 1,282 | **1,000** | 1,28× |
| 1,59 | 4,0 | 2,120 | **1,000** | 2,12× |
| 2,00 | 8,0 | 4,494 | **1,000** | 4,49× |
| 2,52 | 16,0 | 9,005 | **1,000** | 9,01× |

İsraf `1e-12` içinde **tam 1,000** — her satırda. Boşluk kontrolü de geçti
(`λ=1`'de tek seviye, iki yöntem aynı).

### A′'nın net maliyeti

| λ | oran | tasarruf | tek ızgara net | **çok seviye net** |
|---|---|---|---|---|
| 1,26 | 2:1 | 1,90× | 0,677 | **0,528** |
| 2,00 | 8:1 | 5,99× | 0,750 | **0,167** |
| 2,52 | 16:1 | 9,45× | 0,953 | **0,106** |

> **Çok seviyeli ızgarayla A′ parçacık tasarrufunun tamamını gerçekleştiriyor:
> 16:1'de `9,45×` daha ucuz.** §3.9'un *"tek ızgarada kazanç yok"* yargısı
> duruyor; eksik olan, doğru mimariyle kazancın **tam** olduğuydu.

> **Not (KAYIT-031 §3b):** §3.9'un israf sayıları "gereken"i `2·h_i` ile
> tanımlıyordu; A′'nın kullanacağı simetrik biçim `h_i + h_j`'dir ve israfı
> bir miktar **düşürür** (16:1'de net `1,065 → 0,953`). Yargı nitelik
> olarak aynı, nicelik olarak yumuşadı.

---

## 4. Karar tablosu

| # | mermiyi çözer | yapay kuvvet | şok geçişi | **momentum** | model-form | mimari bedel |
|---|---|---|---|---|---|---|
| ~~A~~ | **hayır** | 0,168 | zararsız ✔ | 1e-16 ✔ | — | yok |
| **A′** | evet | **0,55–1,10** | (A'da zararsız) | 1e-16 ✔ | **yok** | çekirdek + CFL + Ω + çok seviyeli ızgara → **16:1'de 9,45× ucuz** (§3.10) |
| ~~B~~ | A′ ile | = A′ | = A′ | = A′ | = A′ | = A′ |
| **C** | evet | yok | ölçülmedi | **7,5e-03 ✘ sistematik** | ara değerleme `O(h²)` | iki çözücü + örtüşme + MLS + korunum düzeltmesi |
| **D** | **atlar** | yok | — | ✔ (tek çözücü) | **%5–7**, **kalibre edilemiyor** (§3.7, §3.8) | ılımlı |

---

## 5. Öneri: ~~**D**, A′ yedekte~~ → **A′ öne geçti** (bkz. §3.8 ve aşağıdaki not)

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

> **KAYIT-029 + KAYIT-030 sonrası denge: A′ ÖNE GEÇTİ.**
>
> D'nin son savunması *"biriktirme yarıçapı kalibre edilebilir"* idi.
> **D-2 onu ölçtü ve yapılamadı** (§3.8): şok yarıçapı eşlenirken kinetik
> enerji kesri %14,5–18,0 ayrışıyor; tek parametre iki gözlenebiliri aynı
> anda eşlemiyor.
>
> A′'nın model-form hatası **yoktur** — mermiyi gerçekten çözer. Bedeli
> **yalnızca mimaridir**, ve arayüz gürültüsü şok geçişinde **ölçülemez**
> (§3.5: taşma %0,000).
>
> **KAYIT-031 sonrası: her seçeneğin ölçülmüş bir bedeli var.**
>
> | # | ölçülmüş bedel |
> |---|---|
> | **A′** | arayüz 3,2–6,5× gürültü + çok seviyeli ızgara (68+24 site) — **karşılığı ölçüldü: 16:1'de 9,45× ucuz**, ve model-form hatası **yok** |
> | **C** | momentum **7,5e-03 sistematik** + MLS + korunum düzeltmesi |
> | **D** | model-form **%5–7**, tek parametreyle **kalibre edilemiyor** (`KE/E` %14,5–18,0) |
>
> **Hiçbir seçenek ucuz değil.** Karar artık *"hangisi doğru"* değil,
> *"hangi hatayı kabul ediyoruz ve neyi ödemeye razıyız"* sorusudur.
> Bu **proje sahibinin** kararıdır; ADR bu yüzden **ÖNERİLDİ** durumunda
> kalır.

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
