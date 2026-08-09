# FAZ 4 — sıkıntı raporu (canlı)

> **Bu belge her turda güncellenir.** Amaç tek bir yerde şunu görebilmek:
> *ne bozuldu, neden bozuldu, nasıl bulundu, ne yapıldı.*
>
> Kural: **hiçbir satır silinmez.** Düzeltilen bir sıkıntı `KAPANDI`
> işaretlenir; nedeni yerinde kalır. Yanlış çıkan bir yargı da öyle.

**Son güncelleme:** 2026-08-09 · **Kapanan:** 37 · **Açık:** 7

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

### A5 — **G4-A1 düştü: mermi çözülmemiş** (2026-08-08, en önemli teknik bulgu)

| | |
|---|---|
| **ölçülen** | `A1 = 0,215` parçacık/çap (`s7_λ2`), en iyi kolda `0,322` |
| **eşik** | `2,0` — **6,2 ila 9,3 kat** eksik |
| **gereken `λ`** | **18,6** (kütle oranı **6478:1**) |
| **ölçülmüş `λ`** | boşluk 3: `2` (8:1); KAYIT-033: `≤ 3` |
| **bedel** | `r_iç = 3 m` ile `96` GPU-günü — bütçenin **3,2 katı** |
| **bedelin kaynağı** | parçacık `1,13×`, **`dt` cezası `9,3×`** |

> **Tek global zaman adımlı şemada bu bedel küçültülemez.** Çözümü
> bireysel/blok zaman adımı — bu kod tabanında **yok**.

#### ÖLÇÜLDÜ: mermiyi çözmek **rejimi değiştiriyor** (2026-08-09)

Üç kol, aynı `t_end = 0,2 s`:

| kol | `A1` | `β` | **`n_ejekta`** | mom. kapanışı |
|---|---|---|---|---|
| tek aşama (`λ=2`) | 0,2146 | 1,617583 | **803** | 1,36e-14 |
| iki seviyeli *(geçersiz)* | 2,0391 | 1,412659 | 32 | **6,90e-01** |
| **üç seviyeli** | **2,0391** | **1,411216** | **28** | **1,31e-14** |

**`803`, merminin parçacık sayısının tamamı.** Çözülmemiş mermide
**bütün mermi sekip kaçıyor**; çözülmüşte yalnızca `28` parçacık —
mermi **gömülüyor**.

> `%12,8`'lik bir `β` farkı değil, **rejim değişikliği**: *"tamamen
> seken top"* → *"gömülen mermi"*. `A1 ≥ 2` eşiği **haklı çıktı**:
> altında ve üstünde **farklı fizik** var.

#### `A1`'in daha keskin hâli: **`h` merminin `9,3` katı** (2026-08-09)

*"`0,215` parçacık/çap"* soyut kalıyor. Aynı şey yumuşatma uzunluğuyla:

| | `λ = 2` | `λ = 19` |
|---|---|---|
| mermi çapı | 0,7512 m | 0,7512 m |
| mermi `h` | **7,0000 m** | 0,7368 m |
| **`h` / çap** | **`9,32`** | **`0,98`** |
| `h` / mermi iç aralığı | 96,7 | 10,2 |

> `λ = 2`'de **bütün mermi tek bir yumuşatma uzunluğunun içinde**.
> SPH onu katı bir mermi gibi değil, çapının `9` katına yayılmış
> **seyrek bir bulut** gibi görüyor. Temas basıncı `~10³` kat düşük
> kalır.

**Bu, A9/A11/A12'nin hepsini açıklıyor:**

| gözlem | açıklaması |
|---|---|
| `β` = merminin *"sekmesi"* | yayılmış bulut gömülmüyor, **sekiyor** |
| krater derinliği = aralığın `%1`'i | basınç krater açmaya yetmiyor |
| hedef ejektası **sıfır** | fırlatacak itki yok |

> Yani `A1` **kapının bir ölçütü değil, diğer her şeyin ön koşulu**.
> `λ = 2`'de ölçülen `β`, krater ve ejekta sayıları *"yanlış"* değil —
> **başka bir problemin doğru cevapları**.

Bu yüzden FAZ 4.10 (fırlatma süresi) `λ = 2`'de ölçmek **anlamsızdı** ve
durduruldu; önce `λ = 19` ile çözülmüş mermide bakılıyor (FAZ 4.8).

Karar gerektiriyor: A1 eşiği mi gözden geçirilecek, mimari mi
değişecek? İkisi de bir ADR ister. Detay:
[KAYIT-041](defter/KAYIT-041_2026-08-08_yerel-gpu-ve-mermi-cozulmemis.md).

### A6 — FAZ 4.4 `--t-end` almıyor, `--steps` alıyor → **KAPANDI**

*(Kural gereği yerinde bırakıldı; bkz. §2 sıkıntı 24.)*

Kollar **farklı `t_sim`**'e ulaşıyor (`dt` farklı olduğu için). Farklı
`t`'deki `β`'ları kıyaslamak yakınsama ölçmez, dolayısıyla **B1 ve B3
hesaplanamadı**. Kusur değil, ölçüm tasarımının bilinen sınırı; sonraki
koşuda düzeltilmeli.

### A7 — ADR-0043'ün `t₁ ≈ 1e-3 s` tahmini ölçümle çürüdü → **KAPANDI**

ADR-0043 iki aşamalı çözünürlüğü *"mermiyi çözmek `%1`'e mal oluyor"*
diye önerdi. O `%1`, `t₁ ≈ 1e-3 s` **varsayımına** dayanıyordu ve
varsayım şuydu: mermi kendi çapını `1,22e-4 s`'de geçiyor, `1e-3 s`'de
şok `4` mermi çapı yol alıyor, öyleyse bağlanma bitmiştir.

Ölçüldü (`scripts/faz43c_baglanma_suresi.py`, `λ=19`, `A1 = 2,04`,
`N = 11 871`, yerel RTX 3050):

| büyüklük | değer |
|---|---|
| ölçüt | `u = \|⟨v⟩_mermi − ⟨v⟩_yakın hedef\| / v_çarpma` |
| `u` (`t → 0`) | `0,791` |
| `u` (`t = 2e-3 s`) | **`0,337`** |
| durulma sınavı | **DÜŞTÜ** — eğilim `%8,56`, yarım-pencere `%4,79` (tol `%2`) |
| `t₁` (ölçülen) | **`nan`** — pencerede durulma **yok** |

> `1e-3 s`'de mermi hâlâ hedefe göre çarpma hızının **üçte biriyle**
> gidiyor ve `u` **düşmeye devam ediyor**. Bağlanma bitmemiştir.

**Sonucu doğrudan bedele vuruyor.** ADR-0043 §3'ün duyarlılık tablosu
`t₁` ile **doğrusal**: `1e-2 s` → `+%9,9`, `1e-1 s` → `+%99`. `t₁`
ölçülmeden §4'ün önerisi **savunulamaz**.

**Durum: KAPANDI (2026-08-09).** `t_end = 5e-2 s` koşusu bitti,
`t₁ = 4,767e-3 s` **ölçüldü** — tahminin `4,8` katı, bedel `+%0,9`
yerine `+%4,7`. Öneri o kalemde ayakta.

**Ama ölçüt tanımım da yanlıştı** ve bunu ancak iz eğrisine bakınca
gördüm: `u` **sıfıra inmiyor**, `0,409`'da düzleşiyor — ve oraya
*aşağıdan*, `0,118`'den **yükselerek** geliyor (92 adımın 16'sı artış).
*"Mermi hedefle aynı hıza gelince bağlanma biter"* yanlış; doğrusu
*"momentum alışverişi bitince fark **sabitlenir**"*. Düzeltme
ADR-0043 §4a ve `faz43c` başlığında; yanlış cümle **silinmedi**.

### A8 — `t₁`'in iki şartı çelişiyor (ADR-0043'ü durduran bulgu) → **KAPANDI**

Kabalaştırma ölçüldü (§2 sıkıntı 27). Korunum **geçti**, aktarım
**düştü**:

| `t₁` [s] | kütle/mom./enerji | ısıya dönen | **atama mesafesi** |
|---|---|---|---|
| `1e-3` | `≤ 3,4e-15` | `%93,2` | `0,97` hücre |
| **`4,77e-3`** (ölçülen `t₁`) | `≤ 1,0e-15` | **`%99,3`** | **`4,35` hücre** |
| `1e-2` | `≤ 6,1e-15` | **`%99,9`** | **`10,16` hücre = 35,6 m** |

- Bağlanmanın bitmesi için `t₁` **büyük** olmalı → `4,77e-3 s`.
- Aktarımın maddeyi ışınlamaması için **küçük** olmalı → `≤ 1e-3 s`.
- **Aralık boş.**

`r_iç`'i büyütmek çözmüyor: sıkıştırma `(λ₁/λ₂)³ = 857`'de **sabit**,
yalnızca bedel artıyor (`12 m` → `+%42`).

> Kusur tanımlanabilir: hedef siteler aşama-2'nin **başlangıç**
> kafesinden alınıyor, yani **Euler**'ci — maddenin peşinden gitmiyor.

**KAPANDI (2026-08-09).** Lagrange'cı sürüm yazıldı (`sites_from_cloud`)
ve ölçüldü — **çelişki Euler'ci aktarımın çelişkisiymiş**:

| `t₁` [s] | euler ısıya | **lagrange ısıya** | euler mes. | **lagrange mes.** |
|---|---|---|---|---|
| `1e-4` | %98,2 | %97,1 | 0,97 | 0,73 |
| `1e-3` | %93,2 | %85,9 | 0,97 | 0,73 |
| **`4,77e-3`** | **%99,3** | **%2,88** | **4,35** | **0,73** |
| `1e-2` | %99,9 | **%0,46** | **10,16** | **0,73** |

> İki kip **zıt yönlere** gidiyor: Euler'ci kötüleşiyor, Lagrange'cı
> **iyileşiyor**. Aynı olayın iki yüzü — madde genişliyor; sabit hedef
> ondan uzaklaşıyor, bulutu izleyen hedef ise giderek daha **düzgün**
> bir akış görüyor.

**Kalan (ölçülmedi):** ek parçacıkların (40 / 210) aşama-2 kafesiyle
**dikişi**, ve site sayısına **üst sınır** yok.

### A9 — **`β` bir BASAMAK: `B2` geçiyor ama zayıf kanıt** (2026-08-09)

> ### ⚠ Bu maddeyi önce **fazla güçlü** yazdım
>
> *"`B2` ölçülemez"* demiştim. **Yanlış.** FAZ 4.5 bitti ve `β` baştan
> sona sabit **değil**: ilk üç örnekte `1,000000` (ejekta **yok**), sonra
> `t = 4,056e-2 s`'de `1,583620`'ye **atlıyor**. `yayilim_rel = 0,369`,
> yani `sabit` bayrağı **kalkmıyor** ve `B2` meşru biçimde yazılıyor:
> **`B2 = 1,0` GEÇTİ.**
>
> Maddenin **özü** doğru kaldı; aşağısı ölçümle düzeltilmiş hâlidir.

FAZ 4.5 bitti (`40 000` adım, `t = 4,63 s`, `17 757 s` duvar). `β`
bir **basamak fonksiyonu**:

| örnek | `t` | `β` |
|---|---|---|
| 1–3 | `0,0088 → 0,0290 s` | **`1,000000`** (ejekta **yok**) |
| 4 | **`0,040558 s`** | **`1,583620`** ← geçiş |
| 5–400 | `0,052 → 4,632 s` | `1,583620` |

**Geçişten sonraki yayılım: `2,18e-13`** — 397 örnek, `4,6` saniyelik
simüle süre, **bit düzeyinde** düz. FAZ 4.4 aynı sahnede `0,052 → 0,200 s`
için bağımsız olarak aynı değeri vermişti (`5,6e-16`).

Yani `β` **relakse olmuyor**; bir kez **atlıyor** ve donuyor.

**Sebebi kurulumda ve meşru:** `_malzeme()` `GravityParams(enabled=False)`
kullanıyor (ADR-0024 ölçeklendirmesi). Yerçekimi yokken:

1. Ejekta bir kez serbest kalınca **balistik**tir → momentumu **tam**
   korunur.
2. Ejekta kümesi (`d > r_ctrl` **ve** `v_r > v_kaçış`) donuyor — hızlılar
   çoktan geçti, yavaşlar `0,9 s`'de `r_ctrl`'e ulaşamıyor.

`β = 1 − p_ejekta·ê / |p_mermi|` bu yüzden şoktan sonra **değişemez**.

> **Sonuç: `B2` geçiyor ama ölçtüğü şey dar.** `t_durulma = 4,06e-2 s`
> aslında *"ejektanın kontrol yüzeyini ilk geçtiği an"*; ondan sonra
> değişecek bir şey **yok**. Yani `B2`, *"şok bitti mi"*yi ölçüyor —
> *"gereken simüle süre ne kadar"*ı **değil**.
>
> `B2`'nin ölçmek istediği geç-zaman davranışı (yeniden birikme, geri
> düşen ejekta) **yerçekimi gerektiriyor** ve o kapalı.

**Ne yapıldı:** sıkıntı 33'ün düzeltmesi doğru davrandı — seri sabit
**olmadığı** için bayrak kalkmadı ve `B2` yazıldı. Koruma yanlış
pozitif üretmiyor.

> Koşu **eski kodla** bittiği için `sabit` alanı `None` gelmişti; özet
> **güncel kodla yeniden hesaplandı** (ham seri değişmedi, dosyaya
> `yeniden_ozetlendi` notu düşüldü).

**Ne yapılmadı:** `B2`'nin anlamlı ölçülebilmesi için ya yerçekimi açık
bir koşu ya da başka bir gözlenebilir gerekiyor. İkisi de **karar**
ister; `docs/G4-OLCUTLERI.md` `B2`'yi bu varsayımla yazmamıştı.

> `β`'nın donması **kusur değil**; kusur, onu *"durulma"* diye
> raporlayacak bir ölçüt tanımlamış olmak. `B2` geçti ama **`B4` ile
> aynı ağırlıkta okunmamalı**: `B4 = −0,0037` gerçek bir sayısal hijyen
> ölçümü, `B2 = 1,0` ise neredeyse tanım gereği.

### A10 — Çıkarım parametre uzayı `ρ_yığın` ile tutarsız → **KAPANDI**

**KAPANDI (2026-08-09):** [ADR-0044](adr/ADR-0044-cikarim-parametre-uzayi-tutarsiz.md)
**KABUL EDİLDİ** ve uygulandı — çıkarımın uzayı artık **Seçenek 3**
(`boulder_alpha0, Y0, f_boulder`). FAZ 4.6 o uzayla **koşuyor**.
ADR-0044 §6 madde 2, G4-C `C2`'nin içine taşındı: `C2` düşerse uzay
dejenere demektir ve ADR yeniden açılır.

FAZ 4.6'nın GPU ileri modeli ilk kez koşuldu (duman testi, 2 tasarım
noktası, 40 adım) ve **29/29 nokta düştü**.

| | |
|---|---|
| **çatışma 1** | `ρ_yığın = 1800` sabitken `matrix_alpha0`, `f_boulder`'ın **fonksiyonu** |
| | `f=0,0 → α₀=1,500` · `f=0,3 → α₀=1,838` · `f=0,5 → α₀=2,625` |
| | İlan edilen 3B kutunun uygulanabilir oranı **tam olarak `0`** |
| **çatışma 2** | `f_boulder = 0` `M1` sınıfında **yasak**, ama kutunun alt sınırı `0` ve `factorial_design` köşeleri alıyor |
| **kod kusuru mu** | **Hayır** — `build_rubble_pile`'ın reddi ADR-0030'u koruyor. Kusur **uzayın tanımında** |
| **durum** | [ADR-0044](adr/ADR-0044-cikarim-parametre-uzayi-tutarsiz.md) **ÖNERİLDİ**; FAZ 4.6 karar verilmeden koşulamaz |

> **Duman testi `~2` dakika sürdü ve `~9` saatlik bir GPU koşusunu
> kurtardı.** Bu, A4'ün (*"GPU yolu hiç koşulmadı"*) neden bir risk
> olarak yazıldığının kanıtı — risk **gerçekleşti**.

### A11 — **`krater_capi` ölçülemiyor: üç gözlenebilirin ikisi ölü** (2026-08-09)

FAZ 4.6'nın **ilk 3 noktası** çıkınca JSONL okundu:

| `i` | `beta` | `krater_capi` | `ejekta_kutle_kesri` |
|---|---|---|---|
| 0 | 1,62077 | **0** | 1,3905e-07 |
| 1 | 1,56893 | **0** | 1,39056e-07 |
| 2 | 1,54954 | **0** | 1,39059e-07 |

**Kök neden:** `crater_profile` çapı ancak sapma
`depth_threshold × R = 0,05 × 82 = 4,1 m`'yi **aşarsa** ölçüyor.
`t = 0,174 s`'de krater o kadar derin değil.

> **Koşu `~7` saat sonra ölecekti:** sabit gözlenebilirde
> `Surrogate.sabit` kalkar ve `faz46` *"çıkarım koşturmak boşuna
> olurdu"* diyerek **durur**.

Bundan **kuşkulanmıştım** ve *"tüm noktalar aynı `t`'de olduğu için
`C1/C2/C3` yine anlamlı"* diye **geçmiştim**. Yanlış: sabit bir
gözlenebilir anlamlı değil, **yok**.

**Durum:** koşu `3/60`'ta **durduruldu**.

#### Krater **derinliği** de kurtarmıyor — ölçüldü

Çap eşik istiyor, **derinlik istemiyor**. O yüzden derinlik ölçüldü
(`boulder_α₀ = 1,00`, `f_boulder = 0,05`, `1500` adım, `593,7 s`):

| büyüklük | değer |
|---|---|
| krater **derinliği** | **`0,03486 m`** |
| çap eşiği (`0,05 × R`) | `4,1 m` — **118 kat** uzak |
| **parçacık aralığı** (`s_ince`) | **`3,5 m`** |
| derinlik / aralık | **`0,0100`** |

> Ölçülen *"krater"* bir parçacık aralığının **yüzde biri**. Bu bir
> krater değil, **sayısal gürültü**. Derinliği gözlenebilir yapmak
> gürültüyü çıkarıma sokmak olurdu.

`t = 0,174 s`'de krater **yok** — ne çap ne derinlik olarak.

### A12 — **`β` ejektayı değil MERMİNİN SEKMESİNİ ölçüyor** (2026-08-09)

> ### ⚠ Bunu *"en ağır yeni bulgu"* diye yazdım — **yeni değil**
>
> [ADR-0028](adr/ADR-0028-uzun-kosu-kararliligi.md) bunu **zaten**
> kaydetmiş: *"kontrol yüzeyini geçen malzeme, hedeften kopan ejekta
> değil, **merminin geri sıçramasıdır**; hedeften hiçbir parçacık
> `2R`'yi geçmedi."* `100+` saniye kestirimi de orada yazılı.
>
> Ben bunu **yeniden keşfettim**. Kendi deposunun ADR'lerini okumadan
> *"en ağır bulgu"* demek, bu turda düştüğüm kalıpların bir başkası.
>
> Aşağısı düzeltilmiş hâlidir: **ne biliniyordu**, **ne yeni**.

#### Zaten biliniyordu (ADR-0028)

- Kontrol yüzeyini geçen şey merminin sekmesi.
- Ejekta `β`'sı `m/s` mertebesindeki ejekta için `100+` saniye ister.
- ADR-0028 soruyu FAZ 4'e **erteledi**: *"β ne zaman durulur sorusu
  FAZ 4'ün yerel incelme tasarımına bağlıdır ve orada ölçülecektir."*

**FAZ 4 onu ölçmedi — belirti aynen sürüyor.** Bu maddenin işlevi:
ertelenen sorunun **hâlâ açık** olduğunu kapı raporuna taşımak.

#### YENİ olan iki şey

**1. ADR-0028'in gösterdiği sebep artık geçerli değil, belirti sürüyor.**

| | ADR-0028 | FAZ 4 (şimdi) |
|---|---|---|
| mermi yoğunluğu | `20 kg/m³` (**135 kat** düşürülmüş, *"köpük top"*) | **`2610 kg/m³`** — gerçekçi |
| belirti | ejekta = mermi | **aynı** |

ADR-0028 sebebi *"mermi köpük top gibi sıçrıyor"* diye açıklamıştı.
Mermi artık gerçekçi yoğunlukta ve **yine** aynı şey oluyor. Yani
sebep yoğunluk **değil** — geçiş süresi geometrinin kendisinden
geliyor (`82 m` yol, `m/s` hız).

**2. ADR-0028'in azaltıcı önlemi hiçbir şey kazandırmıyor.**

ADR-0028 *"plato araması **bağlı kütle** momentumundan türetilen `β`
ile yapılır, ejektadan türetilenle değil"* diyor. Ama momentum
korunumundan (`p_bağlı + p_ejekta = p_mermi`):

```
β_bound = p_bağlı·ê/|p_mermi| = 1 − p_ejekta·ê/|p_mermi| = β
```

**İkisi aynı büyüklük.** `β_bound` kullanmak ejekta bekleme sorununu
**çözmüyor**; FAZ 4.5 tam da bu yüzden `t = 0,0406 s`'de donmuş bir
sayı ölçtü.

#### Ölçülen (bu turda)

| | |
|---|---|
| kaçan kütle (`t = 0,174 s`) | **`579,44 kg`** |
| **mermi kütlesi** | **`579,40 kg`** |
| fark | `%0,007` |

**Kaçan madde merminin kendisi.** Hedeften ejekta **yok**. FAZ 4.5'te
`β`, `t = 0,0406 s`'de atlayıp `4,63 s`'ye kadar `2,18e-13` düzlükte
kaldı — o süre boyunca kontrol yüzeyini geçen **yeni hiçbir şey yok**.

#### Neden — tanımdan

Ejekta ölçütü: `d > 2R = 164 m` **ve** `v_r > v_kaçış`. Hedef maddesi
`R = 82 m`'den başlıyor, yani **en az `82 m` yol almalı**:

| ejekta hızı | `164 m`'ye varış |
|---|---|
| `100 m/s` | 0,82 s |
| `10 m/s` | **8,2 s** |
| `5 m/s` | **16,4 s** |
| `1 m/s` | **82 s** |

Mermi kırıntısı `km/s` — **anında** geçiyor. Krater ejektası `m/s`.

#### Etkisi: ADR-0043'ün bedel modeli eksik varsayıma dayanıyor

ADR-0043 §2 *"ensemble koşu süresi `~1 s`"* diyor ve `9,73` GPU-günlük
bedel tablosu buna dayanıyor. `1 s`'de yüzeyi geçmek için ejekta
`≥ 82 m/s` olmalı.

> Gereken süre `4,63 s`'den **büyük**, üst sınırı **bilinmiyor**.
> Bedeli **`10–20×`** büyütebilir.

#### `B1`, `B2`, `B3` bu ışıkta yeniden okunmalı

| | ne sanılıyordu | ne ölçtüğü |
|---|---|---|
| `B1` | ejekta `β`'sı yakınsıyor mu | **mermi sekmesi** yakınsıyor mu |
| `B2` | `β` yerleşti mi | mermi kırıntısı yüzeyi geçti mi |
| `B3` | ejekta `β`'sında A′ üstünlüğü | mermi sekmesinde |

Sayılar **doğru**; **iddia ettikleri daha dar**.

#### Gereken sürenin **bedeli** — ölçülmüş `dt` ve hızla

`dt = 1,158e-4 s` ve `0,4439 s/adım` (ikisi de FAZ 4.5'ten **ölçüldü**):

| gereken `t` | adım | nokta başı | **60 nokta** |
|---|---|---|---|
| `0,174 s` (şimdiki) | 1 503 | 0,2 sa | **0,5 gün** |
| `1 s` (ADR-0043'ün varsayımı) | 8 636 | 1,1 sa | **2,7 gün** |
| `10 s` | 86 363 | 10,6 sa | **26,6 gün** |
| `100 s` (ADR-0028'in kestirimi) | 863 634 | 106,5 sa | **266 gün** |

> H200 `2,85×` hızlı olsa bile `100 s` için `93` gün. **FAZ 4.6 bu
> tanımla koşulamaz.**

#### Ölçülmedi

Hedef maddesi kaçış hızını **aşıyor mu** (yüzeyi geçmemiş olsa da)?
`v_kaçış = 0,082 m/s` çok küçük. Aşıyorsa sorun **koşu süresi**;
aşmıyorsa `β ≈ mermi sekmesi` **fiziksel olarak doğru cevap**.

#### Balistik kestirim **ölçüldü** — sorunu **ikiye böldü**

Yerçekimi kapalı olduğu için serbest parçacık doğru çizgide gider;
`|x + vt| = 2R` her parçacık için **tam** çözülür.
`t = 0,168 s` durumundan (`scripts/faz49_balistik_beta.py`):

| büyüklük | değer |
|---|---|
| kaçış hızını aşan **hedef** parçacığı | **18 / 10 380** (`%0,2`) |
| kütlece | `%0,056` |
| `v_r` medyanı | **`0,111 m/s`** (`v_kaçış = 0,082`) |
| balistik geçiş süresi (medyan) | **`795 s`** (min `363`, p90 `1038`) |
| `β` (şimdi) | `1,61758` |
| **`β(t→∞)`** (durum donmuş varsayımı) | **`1,69842`** |

**İki ayrı sorun olduğu ortaya çıktı:**

**(1) Geçiş beklemesi — ÇÖZÜLEBİLİR.** `795 s`'lik yolculuğu simüle
etmeye gerek **yok**; balistik olarak hesaplanıyor. `100 s / 266 gün`
rakamı bu yüzden **geçersiz**.

> **Çapraz kontrol geçti:** balistik betik `t ≈ 0,168 s`'de
> `β = 1,61758` verdi; FAZ 4.8'in **bağımsız** tek-aşama kontrol kolu
> `t = 0,2 s`'de `β = 1,617583` ölçtü. İki ayrı kod yolu, aynı sayı —
> yani balistik hesap `β`'yı doğru çıkarıyor.

**(2) Fırlatma — ÇÖZÜLMEDİ, asıl sorun bu.** Balistik kestirim
*"durum şu an dondurulursa"* `β = 1,698` diyor. Ama `t = 0,174 s`'de
krater **oluşmamış** (derinlik = aralığın `%1`'i), yani fırlatılacak
madde henüz **yok**. Ejektanın `β`'ya toplam katkısı `+0,08` (`%5`).

#### Düzeltme: o `18` parçacık **ejekta değilmiş**

`faz49_balistik_beta.py` ölçütü yalnızca `v_r > v_kaçış` idi — **konum
şartı yoktu**. FAZ 4.10 `r > R` şartını ekleyince:

| ölçüt | `t ≈ 0,2 s`'de hedef ejektası |
|---|---|
| `v_r > v_kaçış` (konum şartsız) | **18** parçacık → `β(∞) = 1,698` |
| `v_r > v_kaçış` **ve** `r > R` | **0** parçacık → `β = 1,61758` |

O `18` parçacık cismin **içinde** (`r ≤ R`), basınç dalgasıyla dışarı
salınan maddeydi — **iç titreşim**, ejekta değil.

> Yani `+0,08`'lik *"ejekta katkısı"* da **yokmuş**. `t = 0,225 s`'de
> hedeften ayrılmış **tek bir parçacık bile yok**; `β` tamamen mermi.

> Gereken simüle süreyi belirleyen şey **geçiş değil, krater kazısı**.
> O süre **ölçülmedi**.
>
> FAZ 4.5 tam bunu ölçecekti ama `β_bound`'a baktı; o mermi sekmesine
> kilitlendiği için `t = 0,0406 s` gibi **yanıltıcı** bir sayı verdi.

### A4 — `ileri_kosu`'nun GPU kısmı hiç koşulmadı → **KAPANDI**

**KAPANDI (2026-08-09):** yol **koşuldu**. İlk koşuda `29/29` nokta
düştü ve kök neden bulundu (A10 / ADR-0044). Düzeltmeden sonra FAZ 4.6
gerçek GPU koşusuna **başladı**.

> Risk *"kod yolu doğrulanmadı"* diye yazılmıştı ve **gerçekleşti**.
> Onu `2` dakikalık bir duman testiyle yakalamak, `~11` saatlik koşunun
> sonunda görmekten ucuzdu.

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

### Değişmez boşluğu (21) — kusur **değil**, sınanmamış varsayım

| # | sıkıntı | bulgu | ne yapıldı |
|---|---|---|---|
| 21 | `dt` **en küçük** `h` ile mi belirleniyor — **sınanmıyordu** | kod **doğru** (`_h_np` dizi, global `min`) | CPU'da 4 test; ölçüldü |

Bu bir kusur değil ama **sessiz bir risk**: biri `_h_np`'yi `self.h`'ye
(skaler `max`) çevirse A′'da ince parçacıklar CFL'yi **ihlal ederdi** ve
kararsızlık **birikerek** gelirdi — hemen patlamaz.

Ölçülen (CPU referansı, `n = 216`):

| kurulum | `dt` |
|---|---|
| `h = 2,6` tekdüze | `5,132e-05` |
| `h = 1,3` tekdüze | `2,566e-05` (oran **tam 2,000**) |
| karışık (yarısı ince) | **`2,566e-05`** — **ince** değere oturuyor |
| **tek** parçacık `h = 0,65` | **`1,284e-05`** — dörtte bir |

> Son satır `min`'in gerçekten **global** olduğunu gösteriyor: ortalama
> alınıyor olsaydı tek parçacık `dt`'yi kayda değer düşürmezdi.

`ensemble_cost`'un `dt_kaba/λ` varsayımı **bu** ölçümden geliyor;
değişmez düşerse maliyet tablosu da yanlış olur.

### Dayanıklılık (19–20, 22)

| # | sıkıntı | risk | ne yapıldı |
|---|---|---|---|
| 19 | beş koşucuda **sabit TRUBA yolu** | iş nihayet koşarken yol hatası → 12 saat yanar | `REPO = Path(__file__)...` |
| 20 | UTF-8 koruması **dört koşucuda yoktu** | `faz47` **gerçekten çöktü** ve raporu yok etti | altı koşucuya eklendi |
| 22 | ensemble **kesintide her şeyi kaybediyordu** | iş 1460700 zaman aşımından kesildi (**yaşandı**) | JSONL, satır satır, devam edebilir |
| 23 | **TRUBA'ya bağımlılık** — kota dolunca hiç ölçüm yok | GPU ölçümleri tamamen durmuştu | **yerel RTX 3050** kullanıldı; `2,85×` yavaş, yeterli |

> **22 numaralı** sıkıntı bir kod hatası değil, bir **eksiklik**ti.
> `~300` koşu `~10` GPU-günü (KAYIT-040) ve bir SLURM işi `12` saat —
> yani kesinti **kaçınılmaz**, olası değil. Tek seferlik bir çağrı her
> kesintide baştan başlardı.

---

### 24 — kollar **farklı `t_sim`**'e ulaşıyordu (A6'nın kapanışı)

| | |
|---|---|
| **belirti** | `s7_λ2`: A′ `t = 0,342 s`, tek-`h` `t = 0,694 s` |
| **kök neden** | koşucu yalnızca `--steps` alıyordu; `dt ∝ h`, `h` kola göre değişiyor |
| **etkisi** | `B1` ve `B3` **anlamsız** — farklı `t`'deki `β`'lar kıyaslanıyordu |
| **düzeltme** | `--t-end`; son adım `dt = t_end − t_sim` ile **kırpılıyor** |
| **ikinci savunma** | `esit_t_mi()`; kollar aynı `t`'de değilse `B1`/`B3` anahtarları **hiç yazılmıyor** |
| **doğrulama** | ilk kol tam `t_sim = 2,0000e-01`'e oturdu; fikstür güncellenince 7 test düştü → koruma **çalışıyor** |

> Yanlış bir sayı yazmaktansa *"koşulmadı"* demek doğrudur. İkinci
> savunma tam bunun için: `--t-end` unutulursa kapı sessizce yanlış bir
> `B1` üretmiyor.

---

### 25 — `refine.py`'de **iki** gizli bellek bombası (aynı kalıbın 2. ve 3. kez)

| | |
|---|---|
| **belirti** | `r_ince = 9 m, λ = 19` → `Unable to allocate 36.8 GiB` |
| **kök neden** | `N×M×3` dizi **tek seferde** kuruluyordu, iki ayrı yerde |
| **yer 1** | `refine_scene_local` α₀/Y₀ komşu araması: `r=6 m`'de `2,8 GB`, `r=9 m`'de `9,4 GB` |
| **yer 2** | `_dikis_kalitesi`: kuşakta `40 597` parçacık → `36,8 GiB` |
| **niye görülmedi** | `_dikis_kalitesi`'nin yorumu *"kuşak küçük (yüzlerce)"* diyordu — `λ=2`'de **doğruydu** |
| **düzeltme** | ikisi de parçalı; blok belleğe göre seçiliyor |
| **doğrulama** | parçalı sonuç tam matrisle **birebir** aynı (yeni test) |

> Bu, `412 TiB` kusurunun **aynısı**. Üçüncü kez. Karşı önlem artık bir
> kural: `x[:, None, :] - y[None, :, :]` **asla** parçasız yazılmıyor.
> `coarsen.py` bu kuralla yazıldığı için oraya sızmadı.

### 26 — kabalaştırmanın hedef kafesi **yanlıştı**

| | |
|---|---|
| **belirti** | `r_iç=6 m` içinde yalnızca **2 site** |
| **kök neden** | çıkarılan `7 m`'lik **kaba** parçacıklar hedef alınıyordu |
| **doğrusu** | aşama-2 `λ=2` kullanıyor → o bölgede aralık `3,5 m` |
| **nasıl bulundu** | CPU ön uçuşu (GPU'ya gitmeden) |
| **düzeltme** | hedef artık aşama-2'nin **kendi** ince kafesi (2 → 14 site) |

### 27 — açısal momentum **anlamsız** bir paydayla ölçülüyordu

| | |
|---|---|
| **belirti** | `%72 870` kayıp — okunamaz |
| **kök neden** | `\|L₀\|`'a bölünüyordu; **merkezi çarpmada `L₀ ≈ 0`** |
| **düzeltme** | ulaşılabilir ölçeğe göre: `Σ mᵢ\|xᵢ\|\|vᵢ\|` → `%1,71` |
| **ikinci kusur** | ilk test fikstürüm bunu **gösteremiyordu** (`L₀ = 4` çıkmıştı) |
| **doğrulama** | fikstür `L₀ = 0` olacak biçimde yeniden kuruldu; testin kendi iddiası artık ölçülüyor |

---

### 28 — dejenere ölçüm **`%0` diye raporlanıyordu** (kendi betiğimde)

| | |
|---|---|
| **belirti** | `r_iç = 6 m`'de bütün satırlar `%0,000` — bir an *"hata yok"* diye okudum |
| **kök neden** | ince bölgede **hiç blok yoktu**; `f_kes = f_kul = 0`, sapma `0/1e-300 = 0` |
| **niye tehlikeli** | ölçülemeyen şeye `0` demek `nan` demekten **kötü**: `nan` görünür, `0` **başarı** gibi okunur |
| **düzeltme** | `validation/boulder_boundary.py`; dejenere kol `belirsiz`, `judge` onları **atıyor**, hepsi dejenereyse `gecti = None` (`False` değil) |
| **doğrulama** | 14 test; koşucu artık çıkış kodu `1` ve *"kayıt bulunamadı"* |

### 29 — kendi **test fikstürüm** eşiği yuvarlıyordu

| | |
|---|---|
| **belirti** | `test_esik_kenarlari[0.099-True]` düştü |
| **kök neden** | fikstür `n=1000` parçacık **sayarak** kesir kuruyordu; `int(round(0,3297·1000)) = 330` → `%9,9` **`%10,0`** oldu |
| **düzeltme** | kütle doğrudan veriliyor, yuvarlama yok |

> Sınav kodun değil **fikstürün** kusuruydu ve fikstür kusuru testi
> *"kod yanlış"* diye bağırtıyordu. §2 sıkıntı 27'deki `L₀ = 4`
> fikstürüyle aynı sınıf — bu turda **iki kez**.

### 30 — bayat süreçler kaynağı yiyordu

| | |
|---|---|
| **belirti** | test takımı `%30`'da, `faz45` bir saatte 2000 adıma varamadı |
| **kök neden** | **iki** `pytest` (biri unutulmuş) + kullanıcının kestiği `faz43e`'nin süreci **hâlâ koşuyordu** (`λ=19, r=25 m` → 1,85 M parçacık) |
| **ders** | bir aracın çağrısını kesmek **süreci öldürmüyor** |

**ÜÇÜNCÜ KEZ (2026-08-09).** `10` dakikalık araç zaman aşımına uğrayan
bir ölçüm betiği (`python -`) **koşmaya devam etti** ve `16,5` CPU-dakika
yiyerek krater sondasını yavaşlattı. Sonda `11` dakikada bitmesi
gerekirken `17` dakikada tek satır bile üretemedi.

> Kural: uzun bir işi başlatmadan **önce** süreç listesine bak. Araç
> zaman aşımı, `Ctrl-C` **değildir**.

### 32 — yavaşlığın nedenini **ölçmeden** aradım

`faz45` 3,5 saatte 40 000 adımın 2 000'ine varmıştı. Sırayla iki şey
**varsaydım**, ikisi de yanlıştı:

| varsayım | ölçüm |
|---|---|
| *"`beta_from_bound` `O(N²)`, örnekleme boğuyor"* | `1,18 ms` |
| *"`budgets()` yerçekimi potansiyeli hesaplıyor"* | `2,40 ms` (yerçekimi zaten **kapalı**) |

Profil çıkarınca sebep göründü:

| | |
|---|---|
| adım | **1467,86 ms** |
| `state_numpy` | 6,20 ms |
| `budgets` | 2,40 ms |
| `momentum_transfer` | 1,18 ms |

Aynı sahne FAZ 4.4'te **`52 ms/adım`** koşmuştu. Yani örnekleme değil,
**adımın kendisi** `28×` yavaşlamıştı — sebebi tek: **4 GiB'lik tek
kartta aynı anda 3–4 iş** koşturuyordum (`faz45` + iki `pytest` +
profil betiğinin kendisi).

> Kendi ölçüm betiğim de yükün **parçasıydı** — yani ölçtüğüm yavaşlığa
> ölçüm işlemi de katkı veriyordu. Rakamlar bu yüzden yalnızca *"adım
> baskın"* sonucunu destekler, mutlak değer olarak **geçersizdir**.

**Ders:** paralel koşu ücretsiz değil. Tek GPU'da **tek** ağır iş;
gerisi sıraya. Yalnız kaldığında `40 000` adım `~35 dk` sürecek —
`3,5` saat değil.

---

### 31 — çıkarım hattının **uçtan uca** sınavı yoktu

| | |
|---|---|
| **belirti** | 42 çıkarım testi var ama **hiçbiri** uçtan uca değil |
| **kök neden** | posterior testleri veriyi **vekilin kendisinden** üretiyordu (`veri = s.predict(gerçek)`) — döngüsel |
| **niye önemli** | gerçekte veri **simülatörden** gelir; vekil onu yalnızca yaklaşık temsil eder. Asıl risk **dar ama yanlış** posterior |
| **düzeltme** | `tests/test_inference_uctan_uca.py` — veri, vekilin öğrenemeyeceği bir modelden geliyor |
| **sonuç** | `C1`, gerçeğin posteriorda olup olmadığını **doğru** izliyor (üç doğrusalsızlık düzeyinde de) |
| **ek** | `ensemble_kos` ilk kez **kuru olmayan** kipte sınandı: sürdürme, düşen nokta, kesinti→aynı vekil |

> **Ölçüm bir tahminimi daha çürüttü (7.):** *"`dogrusalsizlik = 3` vekili
> bozar"* dedim; `q2 = 0,944…0,996` çıktı. Hangi biçimin **gerçekten**
> bozduğu ölçüldü:
>
> | tepki yüzeyi | `q2` | geçiyor mu |
> |---|---|---|
> | `a³` | 0,9944 | ✔ |
> | basamak `a > ½` | 0,6706 | ✔ |
> | `1/(0,05+a)` | 0,7812 | ✔ |
> | **`sin(4πa)`** | **−0,0262** | **✘** |
>
> **Bunun kendisi bir bulgu:** `q2 > 0,5` **zayıf** bir koruma. Yalnızca
> **salınımlı** tepki yüzeyinde uyarı veriyor ve `β(θ)` fizik gereği
> salınımlı değil — yani pratikte **neredeyse her zaman geçecek**.
> G4-C bu bayrağa tek başına yaslanmamalı. Sınır artık **testle**
> belgeli (`test_q2_esigi_ZAYIF_bir_koruma_bu_yazili_olsun`).

---

### 33 — `B2` **sabit** bir seriyle kapıyı geçebilirdi (koşu sürerken yakalandı)

FAZ 4.5 koşarken `β_bound` üç ölçümde de **birebir aynı** çıktı
(`1,583620` @ `t = 0,226` ve `t = 0,458`). Sebebi meşru: `β_bound` bağlı
parçacıkların momentumu ve hiçbir parçacık kaçış eşiğini geçmemişse
değişmez. Ama bunun kapıya yansıması **meşru değildi**:

| | |
|---|---|
| **belirti** | sabit seride `is_settled` → `durulmus = True` |
| **sonucu** | `faz45_ozet` `B2_durulmus = 1,0` yazardı |
| **niye yanlış** | yerleşen bir şey yok; ölçüm **duyarsız**. Kapı **boş bir kanıtla** geçerdi |
| **düzeltme 1** | `is_settled` artık `sabit` ve `yayilim_rel` döndürüyor (`Surrogate.sabit` kalıbı) |
| **düzeltme 2** | `settling_time` sabit seride `t_durulma_anlamli = False` diyor — sayı silinmiyor, **yorumu** yazılıyor |
| **düzeltme 3** | `faz45_ozet` sabit seride `B2`'yi **hiç yazmıyor** → kapı `koşulmadı` diyor |
| **doğrulama** | 7 yeni test; gerçek platoda bayrak **kalkmıyor** (ayrım korunuyor) |

> `esit_t_mi`'nin `B1`/`B3` için yaptığının aynısı (sıkıntı A6). Aynı
> ilke üçüncü kez: **yanlış bir sayı yazmaktansa *"koşulmadı"* demek.**
>
> Bu kusur bir **koşu sürerken** bulundu — çıktıya bakıp *"bu sayı üç
> kez aynı, kapı buna ne diyecek?"* diye sormakla. Test takımı onu
> bulamazdı; hiçbir fikstürde sabit seri yoktu.

---

### 34 — `faz45` **hiçbir şeyi** koşu bitene kadar yazmıyordu

| | |
|---|---|
| **belirti** | 3,5 saatlik koşu; kesilirse **tamamı** kaybolur |
| **kök neden** | bütün izler bellekte tutulup sonda tek seferde yazılıyordu |
| **niye önemli** | `ensemble_kos` bu dersi **zaten** öğrenmişti (*"her nokta hemen yazılır, kesinti en fazla son noktayı kaybeder"*) — aynı depoda aynı ders iki yerde tutarsızdı |
| **düzeltme** | her örnek `.izler.jsonl`'e hemen yazılıyor; ana çıktı yalnızca **bitince** (yarım JSON *"sonuç"* sanılmasın) |
| **ek koruma** | eski iz dosyası baştan siliniyor — iki koşunun izi karışırsa `settling_time` iki seriyi **tek** seri sanardı |

> Diğer koşucular (`faz43c/d/f`, `faz47`) da sonda tek seferde yazıyor
> ama koşuları `15–40` dk. Riski **düşük**, kusuru **aynı**;
> düzeltilmedi ve bu **bilerek** yazıldı.

### 35 — süre denetimi **yoktu**: kısa koşu sessizce geçerdi

| | |
|---|---|
| **belirti** | FAZ 4.6 varsayılanı `--steps 3000` → `t ≈ 0,075 s`; FAZ 4.4 aynı sahnede `0,2 s`'ye `8000` adımda gitti |
| **niye tehlikeli** | erken kesilen koşu `β`'yı **sistematik** küçük verir ve **bütün** tasarım noktalarını aynı yönde kaydırır. Vekil bunu göremez (`q2` yüksek, yüzey düzgün) → posterior **dar ama yanlış** |
| **düzeltme** | `--faz45` verilince koşu süresi FAZ 4.5'in ölçtüğü durulma zamanıyla karşılaştırılıyor; yetmiyorsa **duruyor** |
| **oran nereden** | adım→zaman FAZ 4.5'in **kendi çıktısından** (`t_sim_end/steps_done`), tahmin edilmiyor |
| **dört dal da sınandı** | kısa → durdu (`--steps 6000` önerdi) · yeterli → geçti · sabit seri → *"denetim yapılamıyor"* · `--faz45` yok → *"DENETLENMEDİ"* |

> Denetim sonucu çıktıya **yazılıyor**: denetlenmeden koşulmuş bir
> ensemble ile durulmaya kadar koşulmuş olan aynı sayılmamalı —
> `kuru: true`nun yaptığı ayrımın aynısı.

---

### 36 — posterior tek bir `nan`'la **sessizce** çökerdi (FAZ 4.6 koşmadan bulundu)

FAZ 4.6 koşmak üzereyken `grid_posterior` denetlendi:

| | |
|---|---|
| **belirti (potansiyel)** | herhangi bir vekil ızgarada `nan` üretirse `logp.max()` `nan` olur, `p` **tamamen** `nan` olur |
| **sonucu** | `contains()` her yerde `False` → G4-C *"`C1` düştü"* der |
| **niye tehlikeli** | **doğru sonuç, tamamen yanıltıcı sebep**. Kimse vekilin bozuk olduğunu anlamaz; herkes çıkarımın gerçeği kaçırdığını sanar |
| **düzeltme** | tahmin, veri ve vekil `sigma`sı **açıkça** denetleniyor; kaç noktada `nan` olduğu mesaja yazılıyor |
| **doğrulama** | 4 yeni test — tek bir `nan` bile yakalanıyor; sağlam vekiller etkilenmiyor |

> Kusur **gerçekleşmemişti**; koşulmadan önce arandı ve bulundu. Bu turda
> ikinci kez CPU denetimi GPU harcamasını önledi (ilki sıkıntı 26).

---

### 37 — düşme gerekçesi **yutuluyordu**

| | |
|---|---|
| **belirti** | `29/29` nokta düştü, tek mesaj: `sonlu olmayan cikti: [nan nan nan]` |
| **kök neden** | `faz46`, `ileri_kosu`'ya `ilerleme` geri çağrısı **geçirmiyordu**; içerideki gerekçe kayboluyordu |
| **etkisi** | kök neden ancak nokta **elle** koşularak görüldü |
| **düzeltme** | gerekçe yakalanıp `RuntimeError` olarak yeniden atılıyor → `ensemble_kos` gerçek sebebi yazıyor |
| **hemen kazanç** | düzeltme, **ikinci** çatışmayı (`f_boulder = 0` M1'de yasak) anında gösterdi — ilk mesajda görünmüyordu |

> Bir hata yolunun **kendisi** de sınanmalı: *"düşen nokta `nan` kalır
> ve çağıran taraf görür"* doğruydu, ama çağıran taraf **nedeni**
> görmüyordu.

---

## 3. Kusurların **sınıflandırması**

| sınıf | sayı | örnek |
|---|---|---|
| ölçüm tasarımı (kendi düzeneğim) | 8 | dar tarama, yanlış eşik, yanlış payda |
| sözleşme / tip | 4 | `None` çökmesi, numpy tipleri |
| dayanıklılık / portabilite | 5 | sabit yol, UTF-8, JSON |
| fizik kurulumu | 3 | enerji mertebesi, yığın yoğunluğu |
| süreç | 2 | doğrulanmayan değiştirme, atlanan test |
| sınanmamış değişmez | 1 | `dt` en küçük `h` ile mi |

> **Yirmi üç kusurun tamamı benim ölçüm düzeneğimde ya da yeni yazdığım
> kodda.** Hiçbiri SPH çözücüsünde değil.

---

## 4. Tekrarlanan hata **kalıpları**

Bunlar bir kez değil, **birden çok** kez oldu:

| kalıp | kaç kez | karşı önlem |
|---|---|---|
| bir eşiği **ölçmeden** yazmak | **6** | eşik yazılmadan önce ölçülüyor |
| `N×M×3` diziyi **parçasız** kurmak | **3** | kural: asla parçasız yazılmaz |
| çalışma noktasını **içermeyen** aralıkta yargı | 2 (+2 önceki tur) | `judge` kapsam koruması |
| aynı büyüklüğü **iki yerde** tanımlamak | 2 | tek kaynağa indirildi |
| dönüş sözleşmesi değişince **tüketicileri denetlemem** | 2 | sistematik tarama |
| **tutarsız** kurulum (yol, kodlama) | 2 | parametrize testler |
| **ölçüm aracının kendisi bozuk** | **3** | aracı önce bilinen bir durumda sına |
| **kuşkulandım ama ölçmeden geçtim** | **2** | kuşku = ölçüm emri |
| düzenleme **sessizce düşerken** commit mesajı yazıldı | **3** | `grep` ile doğrula, sonra commit |
| bayat süreç kaynağı yiyor | **3** | uzun iş öncesi süreç listesine bak |

> En sık kalıp: **ölçmeden yazmak.** **Beş** kez oldu ve beşinde de
> ölçüm tahminimi çürüttü. Son iki örnek: *"RTX 3050 ~400× yavaş olur"*
> dedim, ölçüm **2,85×** dedi; *"`t₁ ≈ 1e-3 s` yeter"* dedim, ölçüm
> `u = 0,337` ve **hâlâ düşüyor** dedi (A7).
>
> Bu ikisinin ortak yanı: ikisi de bir **fizik argümanından** türetildi
> (mermi çapı / şok hızı, bellek bant genişliği) ve ikisi de makul
> görünüyordu. Kalıp *"dikkatsizlik"* değil — **argümanın kendisi
> ölçümün yerine geçemiyor.**
>
> Altıncısı (2026-08-09) aynı kalıbın **ölçüt** hâli: *"`u → 0`
> bağlanmanın bittiğini gösterir"* yazdım; `u` sıfıra inmedi,
> `0,409`'da düzleşti. Eşik değil **tanım** yanlıştı, ki bu daha sinsi:
> yanlış tanım ölçüm yapılsa bile yanlış sonucu *doğru* gösterirdi.

### En pahalı yeni kalıp: **ölçüm aracının kendisi bozuk**

Üç kez oldu ve üçünde de **sayı inandırıcıydı**:

| araç | verdiği | gerçek |
|---|---|---|
| komşu tanısı (çevre sayılmıyordu) | medyan **27**, *"hepsi komşusuz"* | medyan **229** |
| `is_impactor` (`state_numpy()`'da o anahtar yok) | mermi kütlesi hiç çıkarılmıyordu | zorunlu parametre |
| balistik `β` (konum şartı yoktu) | `18` ejekta, `β(∞) = 1,698` | **`0`** ejekta, `1,618` |

> Yanlış bir **sonuç** tartışılır; yanlış bir **araç** tartışmayı da
> bozar. Karşı önlem: yeni bir tanıyı **bilinen** bir durumda
> (analitik ya da dejenere) sınamadan gerçek veriye uygulamamak.

### İkinci yeni kalıp: **kuşkulandım ama ölçmeden geçtim**

| kuşku | ne dedim | ölçüm |
|---|---|---|
| krater `β`'dan yavaş olabilir | *"hepsi aynı `t`'de, `C1/C2/C3` yine anlamlı"* | krater **yok**, gözlenebilir ölü (A11) |
| `β` donuyor, `B2` boş olabilir | *"`B2` ölçülemez"* (fazla güçlü) | `B2` **geçti**, ama iddiası dar (A9) |

> İkisi de **doğru kuşkulardı** ve ikisi de ölçülmeden geçildi.
> Kuşku bir **ölçüm emri**dir; *"muhtemelen sorun olmaz"* diye
> kapatılmaz.

### Üçüncü yeni kalıp: **düzenleme düştü, commit mesajı yazıldı**

`python - <<'PY'` blokları birden çok `replace` yapıp **sonda tek
seferde** yazıyor. Biri patlarsa öncekiler de kaybolur — ama commit
mesajı zaten yazılmış olur. `A11` tam böyle **hiç yazılmadan**
*"A11: …"* başlıklı bir commit'e konu oldu.

> Karşı önlem: dosya değişikliğinden sonra `grep` ile **doğrula**,
> sonra commit et. Ayrıca `;` yerine `&&` — *"pushed"* yazısı git
> başarısızken de basılıyordu.

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
| reddedilen alternatif **ölçüldü** | naif ortalama `%38` momentum kaybı |
| CPU ön uçuşu GPU'dan **önce** koştu | sıkıntı 26 ve 27 GPU'ya gitmeden bulundu |
| korunumun **görmediği** şey ayrıca ölçüldü | atama mesafesi → A8'i o buldu |
| kendi testimin fikstürü **sınandı** | `L₀ = 4` ve `%9,9→%10,0`, ikisi de düzeltildi |
| reddedilen yol **ölçülerek** çürütüldü | Euler'ci aktarım: `%99,3` vs `%2,88` |
| dejenere ölçüm **`belirsiz`** oldu | `%0` diye raporlanması engellendi |

---

## 6. Sayılar

| büyüklük | değer |
|---|---|
| hata ayıklama turu | **16** |
| kapanan sıkıntı | **37** |
| açık sıkıntı | **7** (A5 + A9 + A11 + A12 karar, kalanı kota) |
| **testlerin kör olduğu kusur** | **7** |
| **tahminimi çürüten ölçüm** | **9** |
| eklenen gerileme testi | **133** |
| yerel test takımı | **954 geçti, 96 atlandı** (öncesi 912, ondan önce 898) |
