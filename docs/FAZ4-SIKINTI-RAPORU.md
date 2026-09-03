# FAZ 4 — sıkıntı raporu (canlı)

> **Bu belge her turda güncellenir.** Amaç tek bir yerde şunu görebilmek:
> *ne bozuldu, neden bozuldu, nasıl bulundu, ne yapıldı.*
>
> Kural: **hiçbir satır silinmez.** Düzeltilen bir sıkıntı `KAPANDI`
> işaretlenir; nedeni yerinde kalır. Yanlış çıkan bir yargı da öyle.

**Son güncelleme:** 2026-08-21 · **Kapanan:** 37 (bölüm 2: 23 tablo satırı + 14 `###` başlığı) + 14 (bölüm 1) · **Açık:** 20 — A11, A12, A17, A18, A19, A20, A21, A22, A23, A24, A25, A26, A27, A28, A29, A30, A31, A32, A33, A34 · A22'nin **bulgusu** ayakta (üretim ayarında şok yok); **maliyet çıkarımı** A23'te düzeltildi

> ### ⚠ Bu sayaç bir kez **yanlış düzeltildi**
>
> Başlık `37` diyordu; ben `23` sanıp *"düzelttim"*. **Yanlıştı.**
> Bölüm 2 maddeleri **iki biçimde** yazılı — `| N |` tablo satırı
> (`23` tane) ve `### N` başlığı (`14` tane) — ve ben yalnızca
> tablo satırlarını saymıştım. Numaralar `1..37` kesintisiz.
>
> `test_KAPANAN_ve_ACIK_sayilari_TABLOLARLA_tutuyor` iki biçimi de
> sayıyor ve tam bu yüzden düştü. Test haklıydı, ben değildim.

> ### Sayaç `4 → 3` (2026-08-21) — **neden**
>
> A3'ün gövdesi `2026-08-17`'de *"Bu yarısı da KAPANDI (iş `1506785`)"*
> yazıyordu ve [KAYIT-049](defter/KAYIT-049_2026-08-18_CI-yesil-A3-kapandi.md)
> de A3'ü kapanmış sayıyordu; **başlık** ise onu hâlâ açık listeliyordu.
> Yani rapor kendi özetiyle çelişiyordu — testin yakalayamadığı bir
> çelişki, çünkü test `Açık:` sayısını **başlıklarla** karşılaştırıyor
> ve iki taraf da A3'ü açık sayıyordu.
>
> Değişen tek şey **etiket**: A3 başlığına `KAPANDI` eklendi, sayaç
> `4 → 3` ve bölüm 1'in kapananı `13 → 14` oldu. Ölçüm yok, gerekçe
> yerinde duruyor.

---

## 1. AÇIK sıkıntılar

> ### Sayaç düzeltmesi (2026-08-11)
>
> Başlık `Kapanan: 37` diyordu. Saydım: bölüm 2'de **`1`–`23`** arası
> `23` giriş var, `37` değil — ve bölüm 1'de `11` kapanmış başlık.
> Eski sayı ya bayatmış ya da başka bir şeyi sayıyordu; **kaynağını
> bulamadım**, o yüzden sessizce değiştirmek yerine buraya yazıyorum.
>
> Başlık artık iki bölümü **ayrı** veriyor ve açıkların **adını**
> listeliyor; böylece bir sonraki sefer sayının nereden geldiği
> tartışılmaz.


Bunlar bugün çözülemez ve **nedeni dışsal** ya da **ölçüm gerektiriyor**.

### A1 — TRUBA kotası dolu → **KAPANDI** (2026-08-11)

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

> **KAPANDI (2026-08-11): kota açıldı.**
>
> | | önce | sonra |
> |---|---|---|
> | limit | `7 200 000` | **`37 200 000`** |
> | kullanılan | `7 200 096` (**aşılmış**) | `7 235 503` |
>
> Kuyruktaki işler artık `AssocGrpCPUMinutesLimit` değil `(Priority)`
> ile bekliyor — yani **sıra**, engel değil. Aynı gün dört iş gönderildi
> ve üçü koştu (`0/40` düşen ensemble dahil).
>
> Yan bulgu: `kolyoz-cuda` çekirdek sayısının **16'nın katı** olmasını
> istiyor; `-n 4` ile `CPU count specification invalid` alınır.

> Bu bir kod sorunu değil. Etrafından **dolaşılmadı**.

### A2 — G4 kapısı geçilemedi → **KAPANDI** (2026-08-11)

On ölçütün **onu da** `koşulmadı`. Kapı raporu üretildi ve
`GEÇİLEMEDİ` diyor (çıkış kodu 1). A1 çözülmeden değişmez.


> ### Kapı **tam olarak** değerlendirildi (2026-08-11)
>
> Artık *"koşulmadı"* kalan ölçüt **yok**. `10` ölçütün `9`'u geçti:
>
> | grup | sonuç |
> |---|---|
> | G4-A (A1, A2, A3) | **GEÇTİ** — `A1 = 2,039` |
> | G4-B (B1, B2, B3, B4) | **GEÇTİ** — `B1 = 8,4e-4` |
> | G4-C (C1, C3) | GEÇTİ |
> | **C2** | **`0,907` DÜŞTÜ** (eşik `< 0,50`) |
>
> Bunu mümkün kılan iki ölçüm bu turda tamamlandı: FAZ 4.4 **eşit
> `t_sim`** ile yeniden koştu (`B1`/`B3` o yüzden boştu) ve `A1` iki
> aşamalı üretim modelinden okunmaya başlandı.
>
> **A2 açık kalıyor** çünkü kapı hâlâ geçmedi. Ama sebebi artık tek ve
> ölçülmüş: koşul sayısı `79,5`, `Y0` gözlenemeyen alt uzayda. Çare bir
> ölçüm değil **kapsam kararıdır** (ADR-0046).

> ### KAPANDI: **G4 GEÇİLDİ** — `10/10`
>
> `C2` `0,907 → 0,221`. Geçmesini sağlayan şey bir eşik gevşetmesi ya
> da yeni bir gözlenebilir **değil**: ADR-0046 kararı S1 ile çıkarım
> uzayı üç parametreden **bire** indirildi (`matrix_alpha0`).
>
> `C2` her parametrenin **marjinal** bandına bakar; dejenere bir
> posterior'da iyi kısıtlanan yön bir *birleşim* olduğu için
> marjinallerin hepsi geniş kalır. Tek parametrede dejenerasyon yok.
>
> | | üç parametre | **bir parametre** |
> |---|---|---|
> | `C2` | `0,907` DÜŞTÜ | **`0,221` GEÇTİ** |
> | posterior bandı | `Y0`: önselin `%70`'i | `%15` |
>
> **Bedel kaydedildi:** bilimsel iddia *"iç yapıyı çıkardık"*tan
> **"matris gözenekliliğini çıkardık"**a daraldı. `f_boulder` artık
> serbest değil ve Hera onu görüntüleyecek.
### A3 — ADR-0041 ve ADR-0042 **koşullu** → **KAPANDI** (2026-08-17)

Ölçümler **küp geometrisinde** yapıldı, DART geometrisinde değil.
Boşluk 3 `λ = 2` (8:1) oranında kapandı; ADR-0026 daha yükseğini
istiyor. Koşul kapı raporunda **listeleniyor** ve kapı geçse bile
kalacak.

> ### İkinci yarısı **kapandı**: oran artık `512:1`'e kadar ölçülü
>
> *"`λ = 2` yetersiz"* şikâyeti 2026-08-11'de karşılandı
> (ADR-0043 §7 madde 3): `λ` `2 → 8` tarandı, yani kütle oranı
> **`8:1 → 512:1`** (`64` kat).
>
> | `λ` | oran | parantez konumu | yargı |
> |---|---|---|---|
> | 2 | 8:1 | 0,0936 | `arayuz_zararsiz` |
> | 8 | **512:1** | **0,0733** | `arayuz_zararsiz` |
>
> `log(λ)` eğimi **`−0,018`**: taşma oranla **büyümüyor**.
>
> `λ = 19` (`6478:1`) hâlâ **ölçülemez** (tekdüze ince referans
> `28,1 M` parçacık ister) ve bu çekince duruyor.
>
> ### İlk yarısı için **DART geometrisinde kanıt var** — ama dolaylı
>
> Üretim koşularının aktarım tanıları (DART geometrisi, `λ₁ = 19`
> çekirdek + `λ₂ = 2`):
>
> | | ölçülen |
> |---|---|
> | sahne momentum hatası | `8,76e-15` |
> | sahne kütle hatası | `1,14e-16` |
> | kabalaştırma kütle / momentum / enerji | `2,27e-15` / `1,02e-14` / `1,89e-16` |
> | dikişte en yakın komşu / ince aralık | `0,652` (eşik `0,5`) |
> | komşu medyanı | `74,5` (min `27`, çok yalnız oran **`0`**) |
> | ısıya dönen kinetik | `%2,50` |
>
> Yani DART geometrisinde **korunum ve komşu sağlığı** ölçülü ve iyi.
>
> **Ama bu, ADR-0041/0042'nin kendi iddialarını doğrulamaz.** O ADR'ler
> `h` ilkesi ve `Ω` birimi hakkında; korunumun iyi olması onları
> sınamaz.
>
> ### Bu yarısı da **KAPANDI** (2026-08-17, iş `1506785`)
>
> ADR-0042 kendi içine şu yükümlülüğü yazmıştı ve yerine
> getirilmemişti: *"Ölçüm FAZ 4.4'te DART geometrisinde
> **tekrarlanacaktır**."*
>
> Ölçüldü (`scripts/faz49_komsu_salinimi_dart.py`, iki aşamada `101`
> örnek):
>
> | | küp (KAYIT-035) | **DART** |
> |---|---|---|
> | `N_komşu` aralığı | `268,2 – 551,5` | **`379,1 – 403,5`** |
> | salınım | `2,06×` | **`1,064×`** |
> | taramanın kapsadığı aralık | `56,1 – 650,5` | — |
>
> DART salınımı küp taramasının kapsadığı aralığın **içinde** ve küpün
> kendi salınımından **daha dar**. Yargı `kanit_gecerli`: ADR-0042'nin
> kanıtı çalışma noktasını kapsıyor, **yeniden açılmasına gerek yok**.
>
> Ölçüt veriye bakılmadan yazıldı ve ADR'nin *kendi* kapsama mantığını
> kullanıyor (`judge`'ın aralık koruması). ADR *"belirgin biçimde"*
> eşiğini tanımsız bırakmıştı; keyfî bir çarpan uydurmak yerine
> deponun başka yerde kullandığı ölçüt alındı ve bunun bir **yorum**
> olduğu çıktının `yorum` alanında taşınıyor.
>
> #### İlk ölçüm **yanlıştı** ve düzeltildi
>
> İlk koşuda salınım `1,000×` çıktı — `101` örnek, `207 252` değer,
> hepsi `379,1`. Sonuç değil **maske hatasıydı**: küpün `r ≤ 0,6R`
> tarifi aynen kullanılmıştı, oysa
>
> | | küp (Sedov) | DART |
> |---|---|---|
> | enerji nerede | **merkez** | **yüzey** |
> | `r ≤ 0,6R` neyi kapsar | şok bölgesini | **hiç şok görmeyen çekirdeği** |
>
> Maske parçacık başına destek ölçütüne çevrildi (`r_i + 2h_i ≤ R`):
> ince bölgede `h` küçük olduğu için krater çevresi **dahil**, kaba
> bölgede `h = 14 m` olduğu için yüzeyden uzak. İki test bu hatanın
> geri gelmesini engelliyor.
>
> #### Çapraz kontrol
>
> Analitik `neighbour_count` tekdüze paketleme varsayıyor; fiilen
> sayılan komşu `303` (başta) ve `266` (sonda), analitik `379,1` —
> oran `1,25×` ve `1,43×`. Küp kanıtı da **aynı** formülle kurulduğu
> için karşılaştırma eşdeğer.
>
> Kalan çekince `Ω`'nın kendisinde değil: `Ω ≡ 1` cebirsel
> (`∂h/∂ρ = 0` çarpanı terimi kapatır), ölçüme tabi değil. Ölçülen
> şey sabit `h`'nin **yeterliliğiydi** ve DART'ta küpten daha rahat.

### A5 — **G4-A1 düştü: mermi çözülmemiş** → **KAPANDI** (2026-08-09)

| | |
|---|---|
| **ölçülen** | `A1 = 0,215` parçacık/çap (`s7_λ2`), en iyi kolda `0,322` |
| **eşik** | `2,0` — **6,2 ila 9,3 kat** eksik |
| **gereken `λ`** | **18,6** (kütle oranı **6478:1**) |
| **ölçülmüş `λ`** | boşluk 3: `2` (8:1); KAYIT-033: `≤ 3` |
| **bedel** | `r_iç = 3 m` ile `96` GPU-günü — bütçenin **3,2 katı** |
| **bedelin kaynağı** | parçacık `1,13×`, **`dt` cezası `9,3×`** |

> **KAPANDI: iki aşamalı şema `A1`'i geçiriyor.**
>
> | kurulum | `A1` | |
> |---|---|---|
> | tek aşama (`λ=2`) | `0,215` | düşük |
> | **iki aşama** (`λ1=19` çekirdek → kabalaştırma → `λ2=2`) | **`2,0391`** | **geçti** |
>
> Ve geçmenin **fark yarattığı** ölçüldü (KAYIT-045): `n_ejekta`
> `803 → 28`. Çözülmemiş mermide **tamamı sekiyor**, çözülmüşte
> gömülüyor — `%12`'lik bir fark değil **rejim değişikliği**.
>
> Maliyet de tahminin altında kaldı: `96` GPU-günü değil, iki aşamalı
> nokta H100'de **`33 s`** (`t_end = 0,2 s`).

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

### A9 — `β` bir BASAMAK, `B2` zayıf kanıt → **KAPANDI** (2026-08-11)

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

> ### KAPANDI: ölçüt ikinci şart kazandı (2026-08-11)
>
> Zayıflığın kaynağı şuydu: `β`'nın düz olmasının **iki** sebebi var ve
> seriden ayırt edilemiyorlar.
>
> | sebep | `β` düz mü | gerçekten durdu mu |
> |---|---|---|
> | kazı bitti, kaçan kaçtı | evet | **evet** |
> | madde **yolda**, `r > R`'yi geçmedi | evet | **hayır** |
>
> Ayıran ölçüm bulundu ve kodlandı: içeride dışarı doğru giden madde
> (`kacis_bekleyenler`). `durulma_yolda_madde_ile()` her ikisini
> **birlikte** istiyor:
>
> ```
> durulmus_gercek = durulmus  VE  yolda madde yok
> ```
>
> Ve DART koşusunda bu ölçüt **düşüyor**: `t = 20 s`'de `2786` parçacık
> hâlâ yolda, geçiş süresi medyan `57–75 s`. Yani `β`'nın düzlüğü
> *"bitti"* değil **"daha başlamadı"** demekmiş — A9'un sezgisi
> doğruymuş, kanıtı şimdi var.
>
> **Üçüncü hâl korundu:** eski koşular `n_bekleyen` taşımıyor; o zaman
> `durulmus_gercek = None` döner — `True` de `False` de değil.
> Bilinmeyeni *"geçti"* saymak tam da A9'un şikâyet ettiği şeydi.
>
> Dört test kilitliyor, `bekleyen_esigi` varsayılanı `0`: tek parçacık
> bile yoldaysa durulmuş sayılmaz; gevşetmek **bilinçli** bir karar.

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

> ### Kök neden bulundu, düzeltildi — ama **yetmedi** (2026-08-11)
>
> Kenar eşiği cismin yarıçapının kesriydi (`thr = depth_threshold × R`
> `= 4,10 m`), yani DART kraterinin **kendi derinliği** kadar. Ölçek
> bağımsız hâle getirildi (`esik_kipi = "derinlik"`).
>
> **Sentetik kraterde işe yaradı:**
>
> | `D` / `d` | yarıçap kipi | derinlik kipi |
> |---|---|---|
> | 20 / 8 | 10,78 | **19,12** (`%96`) |
> | 20 / 3 | **0,00** | 14,95 |
> | 10 / 3 | **0,00** | 2,99 |
>
> **Gerçek ensemble'da işe YARAMADI.** 40 kaydedilmiş durumun
> hepsinde çap **`6,69 m`** — tek değer, sıfır yayılım. İki kipte de.
>
> Sebep: kenar açısal kutu kenarına çakılı ve `n_bins = 8` × `12°`
> `= 1,5°`'lik kutular çapta **`±4,3 m`** belirsizlik demek.
> Parametrelerin yarattığı oynama bundan **küçük**, yani kenar hiç
> kutu değiştirmiyor.
>
> `n_bins > 8` **reddediyor** (eksen kutusunda parçacık bitiyor), yani
> bu çözünürlükte daha ince kutulanamaz.
>
> **Nicel gereksinim:** çapın gözlenebilir olması için kraterin açısal
> yarıçapı önsel kutu boyunca `> 1,5°` oynamalı. Bu, koni içinde
> `~3×` daha çok yüzey parçacığı ister → çarpma bölgesinde
> `λ ≈ 3,5` (şu an `2`).
>
> **A11 AÇIK kalıyor.** Düzeltme gerçek ama yetersiz; kalan engel
> çözünürlük.

> ### Çözünürlük gereksinimi **ölçüldü** (2026-08-11)
>
> #### Önce bir ölçümümü geri alıyorum
>
> İlk taramada *"`λ` artınca koni **boşalıyor**"* diye bir tablo
> çıkardım (`207 → 55 → 66 → 79`). **Yanlıştı.** Aynı çağrıyı iki
> yazımla, tek betikte tekrarlayınca sayılar tutarlı çıktı ve
> ince/kaba ayrışmasıyla da doğrulandı:
>
> | `λ` | koni içi | ince + kaba |
> |---|---|---|
> | 2,0 | **207** | 195 + 12 |
> | 3,0 | 653 | 641 + 12 |
> | 4,0 | **1518** | 1506 + 12 |
>
> Koni `λ` ile **doluyor**, boşalmıyor. Yanlış tablonun kaynağını
> bulamadım; `refine_scene_local`'in girdisini değiştirmediğini ayrıca
> sınadım (üst üste çağrılar birebir aynı). Sonuç: o tablo ve ona
> dayanan *"boşalıyor"* yorumu **geçersiz**.
>
> #### Doğru sonuç: `λ` **daha ince kutulamayı açıyor**
>
> Sentetik `D = 20 m`, derinlik `5 m` krater; ölçülen çap / gerçek:
>
> | `λ` | `nb = 8` | `nb = 12` | `nb = 16` |
> |---|---|---|---|
> | 2,0 | 0,75 | **RED** | **RED** |
> | 3,0 | **0,96** | 0,78 | RED |
> | 4,0 | 0,75 | 0,92 | **0,90** |
>
> Kazanç kurtarma oranında değil **nicemlemede**: `λ = 2`'de yalnızca
> `nb = 8` çalışıyor (`±1,5°` → çapta **`±4,3 m`**); `λ = 4`'te
> `nb = 16` açılıyor (`±0,75°` → **`±2,1 m`**).
>
> #### Yine de yeterli olduğu **gösterilmedi**
>
> Nicemleme yarıya iniyor ama parametrelerin çapta yarattığı oynama
> `~1,4 m` mertebesinde kestiriliyor (derinliğin `%20` yayılımından),
> yani **hâlâ nicemlemenin altında** olabilir. Kesin cevap `λ = 4`'te
> gerçek bir ensemble ister.
>
> **Maliyet ölçüldü:** `λ = 4` → `N` `10 380 → 17 072` (`1,64×`) ve
> `dt` cezasıyla birlikte `~3,3×`. 40 noktalık ensemble `~73 dk`.
>
> Bu bir **üretim çözünürlüğü değişikliği** olur ve ADR-0043 `λ₂ = 2`'yi
> kilitledi; tek taraflı değiştirmiyorum.

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

#### ⚠⚠ GERİ ALINDI: *"çıkarıcı krateri göremiyor"* **YANLIŞTI** (2026-08-09)

Bu bölümde *"`crater_profile` `80 m`'lik krateri bile göremiyor"* diye
bir **kusur bildirdim**. **Yanlıştı ve geri alıyorum.**

**Hata bendeydi:** sınav küresine krateri `+x`'e oyup
`impact_direction = +x` verdim. Oysa o parametre merminin **gidiş
yönü**dür — krater `−impact_direction` tarafındadır. Yanlış işaretle
çıkarıcı **karşı kutba** bakıyor ve doğal olarak `0` buluyordu.

> Bu, bugün **beşinci** kez: kendi ölçüm düzeneğimin kusurunu koda
> yıkmak. Üstelik bu kez sonucu *"ciddi kusur"* diye **raporladım**.

#### Doğru yönelimle ÖLÇÜLEN gerçek sınırlar

`R = 82 m` küre, parabolik krater, `impact_direction = −merkez_yönü`:

| `D` | derinlik | `s = 3,5 m` | `s = 2,0 m` | `s = 1,2 m` |
|---|---|---|---|---|
| 40 m | 8 m | *ölçülemedi* (koruma çalıştı) | **3,51** | **3,80** |
| 20 m | 4 m | 0 | 0 | 0 |

**İki gerçek sınır, ikisi de kusur değil:**

1. **`0.` kutu genişliği.** Kutu `0–12,84°` (yüzeyde `18,4 m`) ve
   **medyan** alınıyor. Parabolik kraterin medyanı tepe derinliğinin
   ~yarısı → `8 m` yerine `3,5–3,8 m`. Çözünürlük artırmak bunu
   düzeltmiyor (`3,51 → 3,80`).
2. **Çap eşiği.** `depth_threshold × R = 4,1 m`; ölçülen `dev` altında
   kaldığı için **çap `0`**.

`D = 20 m` krater `0.` kutudan **küçük** (yarı açı `7° < 12,84°`);
medyan kımıldamıyor.

> Yani `krater_capi = 0`, `t = 0,174 s`'de **gerçekten krater yok**
> demek — ilk okuyuşum doğruymuş. A11'in özü değişmiyor: gözlenebilir
> ölü, çünkü **krater oluşmamış**.

**Kalan kazanç:** çarpma ekseni kutusu seyrekse `crater_profile` artık
`0` yerine **hata veriyor** (`s = 3,5 m` satırında çalıştı). *"Ölçemedim"*
ile *"sıfır"* artık ayrı.

4 test bu sınırları kilitliyor; yanlış yönelimin `0` verdiği de
**kayıtlı** ki bir daha kusur sanılmasın.

#### Üretim çağrısı **doğru** — denetlendi

Geri almadan sonra *"belki çağıran taraf ters işaret veriyordur"* diye
şüphelendim. **Vermiyor:**

| | |
|---|---|
| `crater_shape.py:154` | `axis = -d_imp / dn  # krater ekseni: DISA dogru` |
| yani | `crater_profile` işareti **kendi içinde** çeviriyor |
| sahne | `impact_point = [0,0,82]`, `impact_direction = [0,0,-1]` |
| sonuç eksen | `[0,0,+1]` — **kratere doğru** ✔ |
| gerçek DART sahnesinde `0.` kutu | **13** yüzey parçacığı (`min_per_bin = 5`) |

> Yani ölçüm **yapılıyor** ve `≈ 0,035 m` çıkıyor çünkü **krater yok**.
> Bu kez iddia etmeden **önce** denetledim.

#### Gözlenebilir **kurtarılabilir** — ayarlı kutulamayla ölçüldü

Beklenen krater çapı mertebe kestirimiyle **10–25 m** (Holsapple
mukavemet rejimi, `Y = 1e4…1e5 Pa`), varsayılan algılama tabanı ise
`D ≳ 20 m`. Yani gözlenebilir **tam tabanın üstünde** duruyor.

Bilinen `D = 16 m`, derinlik `3 m` kraterle ayarlar tarandı:

| `s` | `outer` | `n_bins` | `n_theta` | ölçülen derinlik |
|---|---|---|---|---|
| 3,5 | 60° | 20 | vars. | **0,000** |
| 3,5 | 20° | 10 | 48 | 0,724 |
| 2,0 | 20° | 10 | 48 | 0,991 |
| **2,0** | **12°** | **8** | **64** | **2,082** (gerçek `3,0`) |

> **Varsayılan ayarlar kraterin ölçeğine göre çok kaba.** Kutulama
> kratere uydurulunca derinliğin `%69`'u geri geliyor.

**Üç ayar birlikte değişmeli:** `outer_angle_deg` beklenen kratere
(`~12°`), `n_theta` daha ince (`~64`), ve `depth_threshold` — `%5 × R
= 4,1 m` üç metrelik bir krater için **çok yüksek**, çap bu yüzden hâlâ
`0`.

`s = 3,5 m` (ensemble çözünürlüğü) en iyi hâlde `%24` veriyor; güvenilir
bir krater gözlenebiliri **daha ince yüzey** istiyor. Bu, FAZ 4.6'nın
tasarımına giren **ölçülmüş** bir kısıt.

#### Yanlış pozitif sınavı **geçildi**

`n_theta = 64`, `s = 3,5 m`'de **`0,84` parçacık/kutu** demek — tam da
`surface_particles`'ın *"kutuda `~1` parçacık kalınca hayalî `41 m`
krater üretir"* diye uyardığı bölge. Sınandı:

| `s` | gürültü | küresel kayma | ölçülen derinlik | çap |
|---|---|---|---|---|
| 3,5 | 0,00 | 0,0 | 0,0000 | 0 |
| 3,5 | 0,20 | 0,0 | 0,0854 | 0 |
| 3,5 | 0,20 | −0,5 | 0,1694 | 0 |
| 2,0 | 0,20 | −0,5 | 0,1313 | 0 |

**Hayalî krater yok.** Yanlılığı `x_reference` çıkarması götürüyor —
R4'ün onu **zorunlu** yapmasının sebebi tam bu.

> **Gürültü tabanı `0,02–0,17 m`.** Gerçek koşunun ölçtüğü
> `0,033–0,037 m` bu bandın **içinde** — yani o sayı bir krater değil,
> gürültü. Bağımsız bir doğrulama daha.

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

### A13 — `KRATER_AYARLARI_DART` krateri ölçemiyordu → **KAPANDI** (A16/eksen kipi)

> ### ⚠ Bu benim **kendi** düzeltmemin kusuru
>
> A11'i kapatırken `outer_angle_deg` ve `n_bins`'i ölçerek ayarladım
> ve *"ayarlı ayarlar derinliğin `%69`'unu geri kazanıyor"* dedim.
> `n_theta = 64`'ü **hiç sorgulamadım** — oysa bağlayıcı kısıt oydu.

#### Ölçüm

`surface_particles` `cos θ`'da **eşit** kutular kullanıyor, yani
kutuptaki kutu açısal olarak en geniş olanı. Krater tam kutupta:

| `n_theta` | kutup kutusu | `D = 20 m` kraterin yarı-açısı |
|---|---|---|
| **64** | **14,36°** | 7,00° |
| 256 | 7,17° | 7,00° |
| **1024** | **3,58°** | 7,00° |

`64`'te krater **tek bir kutunun içine sığıyor** ve görünmez oluyor.
Gerçek derinlik `2 → 12 m` (**6 kat**) değişirken ölçülen:

| gerçek | `n_theta = 64` | `n_theta = 1024` |
|---|---|---|
| 2 m | **1,1975** | 2,46 |
| 5 m | **1,1975** | 4,93 |
| 10 m | **1,1975** | 7,48 |
| 12 m | **1,1975** | — |

**Sabit bir çıktı gözlenebilir değildir.** Bir parametre hakkında sıfır
bilgi taşır; çıkarıma girseydi `krater_derinlik` sütunu gürültü olurdu.

#### İkinci kusur: uçuştaki ejekta krateri kapatıyor

`surface_particles` kutudaki **en uzak** parçacığı alıyor ve yarıçap üst
sınırı **yok**. Kraterin üstünde uçan madde hâlâ aynı açısal kutuda, yani
"yüzey" o oluyor. `ejekta_yaricap_carpani = 1.05` eklendi.

> Süzgeç **yalnızca ölçülen yüzeye** uygulanmalı. İkisine birden
> uygulayınca hayatta kalan parçacıklar zaten taban altında olduğu için
> referans = ölçüm oluyor ve sonuç **özdeş sıfır** — bunu da ölçerek
> öğrendim (ilk denemem buydu).

#### Doğrulama ve yanlış-pozitif denetimi

Gerçek aşama-2 sahnesinde (`N = 10 380`) `2/5/10 m` → `2,46/4,93/7,48`,
tek düze artan. Kabuk sınavında oran üçünde de **`0,823`** — doğrusal.

Kratersiz sahnede, yüzey gürültüsü `0 → 0,5 m`, 3 tohum:
**gürültü tabanı en kötü `0,43 m`**. `2 m` krater `2,46` okunduğu için
pay **`5,7×`**.

#### Durum

`n_theta = 1024`, `n_phi = 128`, `ejekta_yaricap_carpani = 1.05`
işlendi. Beş test kilitliyor; biri `n_theta`'yı düşüreni yakalıyor.

#### Çap: kurtarılabiliyor ama **kullanmıyorum**

Çapın `0` okumasının sebebi ölçüldü: `depth_threshold = 0,05`, `R`'nin
kesri olduğu için `0,05 × 82 = 4,1 m` sapma istiyor — DART kraterinin
**kendisi kadar**. Eşik düşürülünce çap geri geliyor:

| eşik | `D = 20` gerçek | `D = 40` gerçek | kratersiz sahnede **hayalî** |
|---|---|---|---|
| 0,05 (`4,10 m`) | `0` — kaçırıyor | 14,83 | yok |
| **0,005** (`0,41 m`) | **19,13** | 28,32 | 6,93 *(yalnız `0,5 m` gürültüde)* |
| 0,002 (`0,16 m`) | 19,13 | 28,32 | **11,99** |

`0,005` gerçek kraterde çalışıyor ve yüzey gürültüsü `≤ 0,2 m` iken
hayalî çap üretmiyor. Yine de **gözlenebilir vektörüne koymuyorum**:

1. Çıktı **kaba nicemli** — `D = 20` ve `40` için yalnızca iki ayrık
   düzey (`19,13` / `28,32`); taşıdığı bilgi az.
2. `D = 40`'ta **`%29` düşük** yanlı.
3. Üretim koşusunun yüzey gürültüsü **ölçülmedi**; `0,2 m` sınırının
   hangi tarafında olduğunu bilmiyorum. Bilmeden açmak, hayalî bir
   kraterin çıkarıma girmesi demek.

> Bu bir *"çalışmıyor"* değil, **koşulu doğrulanmamış** kaydıdır. Koşul
> (yüzey gürültüsü `< 0,2 m`) ölçülürse eşik `0,005`'e çekilebilir.

**Sonuç:** FAZ 4.6 **iki** gözlenebilirle yürüyor (`β`, `krater_derinlik`),
üç değil — ve sebebi ölçülmüş bir sayı.

**Hâlâ açık:** `4096`'da 2 m krater kayboluyor; tatlı nokta **dar** ve
farklı bir sahne çözünürlüğünde yeniden ölçülmeli.

---

### A14 — `--gozeneksiz` kolu cismi patlatacaktı → **KAPANDI** (katı sahne)

Hazırladığım ayırt edici kol şuydu: gözeneklilik şok enerjisini gözenek
çökmesine yutuyorsa krater kazılmaz; **P-α'yı kapat**, krater oluşursa
hipotez doğrulanır.

Kol koşulmadan önce denetlendi. **Bozuk çıktı.**

#### Ölçüm

Süreklilik yönteminde başlangıç yoğunluğu `rho0 / alpha0`'dır
(`solver_solid.py:133`) — ve bu, gözeneklilik **kapalıyken de** öyle
kalır. Yani P-α'yı kapatmak cismi genişlemiş halde bırakıyor:

| `alpha0` | `ρ` başlangıç | `P` gözenekli | `P` **gözeneksiz** |
|---|---|---|---|
| 1,00 | 2700,0 | `0` | `0` |
| 1,15 | 2347,8 | `0` | **`−3,03e9` Pa** |
| 1,30 | 2076,9 | `0` | **`−4,74e9` Pa** |

`−4,7 GPa` gerilme cismi daha `t = 0`'da parçalar.

> Kol ejekta üretseydi *"gözeneklilik enerjiyi yutuyormuş"* diye
> okuyacaktım. Oysa cisim yalnızca **kendi başlangıç gerilmesinden**
> patlamış olacaktı. Hipotezi doğrulayan sahte bir kanıt.

#### İlk düzeltmem de kusurluydu — bir tuzağı başkasıyla değiştirdim

Önce yalnızca `alpha0 = 1` yaptım. Gerilme gitti ama **yeni** bir
tutarsızlık geldi: parçacık kütlesi yığın yoğunluğundan gelir
(`m = ρ_yığın · V`), oysa `ρ` bağımsız bir durum değişkeni ve
`rho0/alpha0` ile kurulur. İkisini ayrı ayrı ayarlayınca uyuşmuyorlar:

| kol | `m/V` | `ρ` başlangıç | uyum |
|---|---|---|---|
| gözenekli | 1537,2 | 1537,2 | ✔ |
| *yalnızca* `alpha0 = 1` | **1537,2** | **2700** | ✘ **`%76`** |
| **katı sahne** (son hâl) | 2700 | 2700 | ✔ |

SPH'de hacim elemanı `m/ρ`'dur; `%76`'lık uyuşmazlık parçacıkların
uzayı doldurmamasına ve basınç gradyanının yanlış ölçeklenmesine yol
açardı.

#### Son hâl

`--gozeneksiz` artık **sahneyi** katı kuruyor:
`bulk_density = 2700`, `boulder_alpha0 = 1,0`. İkincisi zorunlu —
`matrix_alpha0_for_bulk_density(2700, 2700, 1,05, 0,25)` **çözülmüyor**
(matris distansiyonu `0,9844 < 1`): gözenekli bloklarla katı yığın
yoğunluğuna ulaşılamıyor.

Ölçülen son durum: iki kolda da `m/V = ρ` ve `P(t=0) = 0`.
`_alpha0_denetle` sahne katı kurulmamışsa **hata veriyor**.

#### Kalan kusur — kapatılamaz

Kol **tek değişkenli değil ve olamaz**: gözeneklilik başlangıç durumuna
gömülü. Katı hedef aynı hacimde **`%76` daha ağır**.

**Kusursuz kontrol yok.** Var olanların en iyisi *"katı, gerilmesiz,
tutarlı hedef"* ve karşılaştırma bu farkı **belirterek** okunmalı —
`faz48_gozeneklilik_karsilastir.py` bunu belgesinde söylüyor.

---

### A15 — Uzun koşunun krater sütunu ejektayı ölçüyordu → **KAPANDI**

`faz48 --t-end 5.0` bitti (`9805,5 s` duvar). Krater sütunu:

| `t` | derinlik | çap |
|---|---|---|
| 3,92 | 0,0950 | 0,000 |
| 4,16 | 0,1098 | 0,000 |
| 4,28 | 0,1201 | 0,000 |
| **4,40** | **5,3278** | **25,476** |
| 4,65 | 5,3206 | 25,475 |
| 5,00 | 5,3145 | 25,476 |

Tek örnekte `44×` sıçrama, sonra dört hane kararlı.

> **Fizik böyle davranmaz.** `4,3` saniye boyunca hiçbir şey olmayan bir
> yerde krater bir adımda açılmaz; çapın `0`'dan `25,476`'ya atlayıp
> orada donması bir **kutunun geçerli hâle gelmesinin** imzası.

#### Mekanizma — ölçüldü

Aynı sahnede, **kratersiz** ve varsayılan kutulamayla `crater_profile`
çağırınca:

```
ValueError: carpma ekseni kutusunda 0 parcacik var (en az 5 gerekir).
            Yuzey parcacigi 800, n_bins=20.
```

**Kratersiz sahne ölçülemiyor.** Ama koşu sayı üretti. Aradaki tek fark
uçuştaki maddedir: mermi kırıntısı çarpma ekseni boyunca dışarı gidiyor
ve `surface_particles` yarıçap üst sınırı olmadığı için (A13) onu
*"yüzey"* sayıyor.

Yani `0,033 → 0,12 m` **kraterin büyümesi değil, ejektanın
sürüklenmesiydi**. `t = 4,40`'ta o maskeleme kalktı ve altındaki kutu
okunur oldu.

#### Ne söylenebilir, ne söylenemez

| | |
|---|---|
| `5,31 m` / `25,48 m`'nin **başlangıç zamanı** | **anlamsız** |
| büyüklüğün kendisi | **belirsiz** — ayrı ölçüm gerekiyor |
| `d/D = 0,21` tipik krater oranı | **teşvik edici ama kanıt değil** |

#### Yapılan

`_iz_ornegi` artık `KRATER_AYARLARI_DART` kullanıyor (A13 düzeltmesi;
`n_theta = 1024` + ejekta süzgeci). Koşu **yeniden başlatıldı**
(`faz48_v2`). Beklenti: düzeltilmiş ayarlarla krater erkenden ve
**sürekli** görünmeli. Sıçrama tekrarlarsa açıklama yanlıştır.

> Bu bir tahmin, sonuç değil. Sıçramanın tekrar edip etmediği
> `faz48_v2`'nin cevaplayacağı **ayırt edici** soru.

#### `faz48_v2` koştu — tahminim **yarı** doğru çıktı

| tahmin | sonuç |
|---|---|
| krater **erken** görünür | ✔ `t = 0,066 s`'de `6,61 m` |
| `t = 4,4` sıçraması **tekrarlamaz** | ✔ tekrarlamadı |
| değer **sürekli** büyür | ✘ **YANLIŞ** — nicemli |

Düzeltme *görünürlüğü* kurtardı, *niceliği* kurtarmadı. 82 örnekte:

| büyüklük | davranış |
|---|---|
| **çap** | yalnızca **iki değer**: `6,93` (21 örnek), `12,00` (61) |
| derinlik | 74 farklı değer ama `19` adet `> 0,5 m` sıçrama, en büyüğü **`2,43 m`** |

Çap `~1 bit` bilgi taşıyor. Derinlik `~13 m` sinyalde `±%18` sıçrıyor.

> `GOZLENEBILIRLER`'in kullandığı alan **`krater_capi`** — yani tam da
> iki seviyeli olan. Bu, ADR-0045'in eksik ölçümlerinden birini
> kapatıyor: çap bu çözünürlükte **çıkarım gözlenebiliri olamaz**.

---

### A16 — A13'ün `n_theta = 1024` düzeltmesi de yanlış → **KAPANDI** (eksen kipi)

`surface_particles` `N/PER_BUCKET` kadar kutu seçer (`~867`, yani
`n_theta ≈ 20`) çünkü kutu başına `~12` parçacık gerekir. A13'te
krateri görebilmek için `n_theta`'yı **1024**'e çıkardım. Ölçtüm:

| `n_theta` | kutu | "yüzey" sayısı | oran | medyan `r` |
|---|---|---|---|---|
| 16 | 512 | 512 | 0,05 | **81,26** |
| 64 | 8 192 | 6 038 | 0,58 | 72,18 |
| **1024** | 131 072 | **9 970** | **0,96** | **66,91** |
| 4096 | 524 288 | 10 306 | 0,99 | 66,64 |

Gerçek yüzey `R = 81,94 m`. `n_theta = 1024`'te "yüzey" kümesi cismin
**%96'sı** ve medyanı `66,91` — 10. yüzdelik `39,34`, yani merkeze
yakın.

> `surface_particles` kutu sayısı parçacık sayısını geçince
> **dejenere** oluyor: her parçacık kendi kutusunun en dışı olur ve
> "yüzey" = **bütün cisim**. `1024` krateri *"görüyor"* ama ölçtüğü şey
> yüzey değil.

#### Doğrulamam neden geçti

İki sınavda da:

* **Kabuk testleri** — kabukta *her parçacık zaten yüzeydedir*, aşırı
  kutulama zararsız. Bu yüzden `2/5/10 m → 1,65/4,11/8,23` doğrusal
  çıktı.
* **Dolu sahne testi** — parçacıkları `3R`'ye taşıyıp süzünce krater
  sinyali yine göründü, ama **yanlış sebeple**: yüzey/iç karışımının
  kayması yüzünden.

Kabuk, dolu cismin vekili değilmiş. Aradaki fark tam da ölçülmek
isteneni yok ediyor.

#### İki gereksinim **çelişiyor**

| gereksinim | gerekli `n_theta` |
|---|---|
| kutup kutusu `<` krater yarı-açısı (`7°`) | `> 256` |
| kutu başına `≳ 12` parçacık | `≈ 20` |

`10 410` parçacıkla ikisi **aynı anda sağlanamaz**. Bu bir ayar
seçimiyle çözülmez.

#### Kök neden ve doğru çare

`surface_particles` **küresel `cos θ`**'da kutuluyor. Krater kutupta,
yani tam da kutuların en geniş olduğu yerde. Doğru kutulama **çarpma
ekseninden açıya** göre olmalı: o zaman kutup bölgesi `131k` küresel
kutu gerektirmeden ince örneklenir.

**Durum:** A13'ün `n_theta = 1024` seçimi **geri alındı**.
`KRATER_AYARLARI_DART` artık `kutulama = "eksen"` kullanıyor;
`n_theta`/`n_phi` **hiç verilmiyor** (o kipte kullanılmıyorlar ve
bırakmak *"ayarlanmış"* izlenimi verirdi).

#### Çare: `kutulama = "eksen"`

Küresel ızgara hiç kullanılmıyor; parçacıklar çarpma ekseninden açıya
göre eşit açılı halkalara bölünüyor ve her halkanın yüzeyi `p95` ile
kestiriliyor. Üretim sahnesinde, **ek maliyet olmadan**:

| gerçek | `nb = 4` | `nb = 6` | `nb = 8` |
|---|---|---|---|
| 2 m | 1,844 | 1,977 | **2,015** |
| 5 m | 4,340 | 4,793 | **4,882** |
| 10 m | 8,499 | 9,486 | **9,660** |

Küresel kip aynı sahnede **dokuz ayarın hepsinde** reddediyordu.

#### İlk güvenilir DART krateri ölçümü

`faz48_v2`'nin kaydedilmiş son durumunda (`t = 5 s`), yeni kiple:

| `n_bins` | `p90` | `p95` | `p99` |
|---|---|---|---|
| 4 | 12,283 | 14,346 | 14,488 |
| 6 | 12,557 | **14,780** | 14,916 |
| 8 | 14,103 | **14,782** | 14,931 |

`p95`'te `nb = 6` ve `8` **dört hanede uyuşuyor**. Eski bozuk kip aynı
duruma `7,30`–`16,62` arası veriyordu.

> **DART krateri `t = 5 s`'de `≈ 14,8 m` derin.** Sentetik kalibrasyonun
> `−%4` yanlılığıyla gerçek değer `≈ 15,4 m`.

Üç çekince, hiçbiri gizlenmiyor:

1. Ölçülen şey `t₁ = 4,77e-3 s`'ten `t = 5 s`'e olan **değişim**
   (aktarım parçacık kimliklerini değiştirdiği için `t = 0` referansı
   kullanılamıyor).
2. **Tek koşu, nominal parametreler** — belirsizlik bandı yok.
3. Yerçekimi **kapalı**; krater büyümesini durduran örtü yükü yok, yani
   bu sayı üst sınıra yakın olmalı.

`kuresel` bileşen `p99`'da `−0,160 m` — cisim küresel olarak neredeyse
hiç değişmemiş, yani ölçülen şey **yerel** krater (ADR-0039'un amacı).

---

### A17 — Motor `β`'yı gözlemin **2,3 katı altında** üretiyor (2026-08-11)

Bu bir faz meselesi değil, **motorun kendi kusuru**: ürettiği momentum
aktarımı gerçek ölçümün çok altında.

| kaynak | `β` |
|---|---|
| ölçülen periyot değişimi `−33,0 ± 1,0` dk → türetilen | **`3,2225`** |
| yayımlanan (Cheng ve diğerleri 2023) | `3,6` |
| **motorun ürettiği**, 40 nokta, **tüm önsel kutusu** | **`1,410 – 1,438`** |

Hiçbir parametre birleşimi gözlemi üretmiyor. Kutunun tamamı gözlemin
`2,2`–`2,5` katı **altında**.

#### Eksik olan ne kadar

`β = 1 + |p_ejekta · ê| / p_mermi`:

| | `p_ejekta` |
|---|---|
| gözlem | `7,913e6 kg m/s` |
| motor | `1,464e6` |
| **eksik** | **`6,449e6`** = merminin **`1,81` katı** |

`1 m/s`'lik ejekta için bu, hedefin **`%0,15`**'i (`6,45e6 kg`).

#### Sebep: fizik var, **sayamıyoruz**

| | |
|---|---|
| motorun "kaçtı" saydığı kütle | `579,4 kg` = **merminin kendisi** |
| hedeften kaçan | `0 – 91,3 kg` (dokuz köşe) |
| içeride dışarı giden ("bekleyen") | `2786` parçacık `≈ %26` |
| bekleyenin kaba momentumu | `4,2e8` = **gerekenin `65` katı** |

Ejekta ölçütü maddenin `r > R`'yi geçmesini istiyor; geçiş süresi medyan
**`57–75 s`**. Koşular `0,2`–`20 s`. Yani ölçüt, motorun **ürettiği**
maddeyi görmüyor.

> **Bekleyeni doğrudan saymak savunulamaz:** `bekleyen_profili` o
> maddenin çarpma noktasında **seyrek**, uzakta **yoğun** olduğunu
> ölçtü — kazı değil cismin **çınlaması**.

#### Bu neden motor kusuru sayılıyor

Motorun ana ürünü `β`. Ürettiği `β` gözlemin yarısından azsa, motor
**henüz bitmemiştir** — çözünürlük, gözlenebilir seçimi ve çıkarım
uzayı düzeltilse bile.

#### Kök neden bulundu: **`β` yerçekimsiz cisimde iyi tanımlı değil**

`y0lo`'nun son durumunda (`t = 20 s`) ölçüldü:

| | |
|---|---|
| momentum korunumu | `1,000000` ✔ |
| **iç dolaşım / net** | **`250` kat** (`±8,9e8` vs `3,56e6`) |
| kütle merkezinin KE'si | `1521 J` |
| **iç hareketin KE'si** | toplamın **`%100,00`**'ü |

Bekleyen madde ayrıştırılınca: `+4,14e8` ileri (mermi yönü),
`−3,53e8` geri (ejekta yönü). Geri akış tek başına gerekenin **`55`
katı** — hepsi kaçsaydı `β ≈ 100` olurdu.

> `β` *"cisimden ne kadar momentum ayrıldı"* diye soruyor. Model net
> momentumun **250 katını** içeride dolaştırıyor ve bir parçacığın
> ayrılıp ayrılmadığı onu **tutan** şeye bağlı — o da **yerçekimi**, ve
> **kapalı**. `v_kaçış = 0,082 m/s` simüle **edilmeyen** bir fiziğin
> eşiği.

Bu, `beta_bal_bandi`'nin neden `−43,8` verdiğini de açıklıyor ve o
geri almanın doğru olduğunu doğruluyor.

#### ADR-0028 yerçekimini **fizik yüzünden kapatmamış**

| | s/adım | enerji hatası |
|---|---|---|
| yerçekimsiz | 0,150 | `1,4558e-02` |
| yerçekimli | 2,36 | **`1,4558e-02`** |

Enerji hatası **birebir aynı** — yerçekimi kararlılığı bozmuyor.
Gerekçe `15,7` katlık **maliyet**ti. H100 yerel GPU'dan `~15` kat hızlı,
yani o ceza artık donanımla karşılanıyor.

#### Yerçekimi sınandı — `t = 0,2 s`'de **fark yok**

Ölçüt veriye bakılmadan yazılmıştı; sonuç:

| kol | `β` | `n_ejekta` | duvar |
|---|---|---|---|
| yerçekimi **kapalı** | `1,411216` | 28 | `41,9 s` |
| yerçekimi **açık** | `1,411216` | 28 | `67,9 s` |

**Bit düzeyinde aynı.** Ölçüt *"fark `< %10` → yerçekimi sebep değil"*
diyordu ve uygulanıyor.

Geriye dönünce makul: `t = 0,2 s`'de yerçekiminin verebileceği hız
`g·t ≈ 5e-5 m/s`, ejektanınki `m/s` mertebesinde. **`0,2` saniyede
yerçekimi hiçbir şeyi geri çekemez.**

> Yan ölçüm: maliyet cezası ADR-0028'in ölçtüğü `15,7×` değil,
> burada **`1,6×`**. Donanım ve iki aşamalı şema farkı.

#### Ama bu, uzun sürede de fark olmadığını göstermez

`t = 100 s`'de `g·t ≈ 0,025 m/s`, yani `v_kaçış`ın (`0,082`) **aynı
mertebesi**; geçiş süresi medyanı da `57–75 s`. Ayrım ancak orada
görünebilir.

İki kol gönderildi (`1501241` yerçekimli, `1501242` kontrol),
`t_end = 100 s`. Ölçüt yine önden:

| gözlenen | sonuç |
|---|---|
| iki kolun `β` farkı `> %10` | yerçekimi uzun sürede **belirleyici** |
| fark `< %10` | yerçekimi sebep **değil** — başka yerde ara |

#### Sonuç: `t = 100 s`'de de yerçekimi sebep **değil**

| | yerçekimli | yerçekimsiz |
|---|---|---|
| `β` | `1,40921` | `1,41122` |
| `n_ejekta` | 30 | 28 |
| bekleyen | 2269 | 2312 |
| krater derinliği | **`13,45 m`** | **`15,28 m`** |

`β` farkı **`%0,14`** — ölçütün `%10`'unun çok altında. **Yerçekimi
elendi.**

> Yerçekimi **derinliği** etkiliyor (`%12` daha sığ — sıkıştırıyor) ama
> `β`'yı etkilemiyor. İkisi ayrı büyüklükler ve ayrı davranıyorlar.

#### ⚠ *"Koşu süresi de elendi"* dedim — **YANLIŞTI**

`t_end` `0,2 → 100 s` (`500` kat) ve `β` `1,41`'de kaldı; bundan
*"süre sebep değil"* diye çıkardım. **Erken karardı.**

`t = 100 s`'deki durumu ölçtüm:

| | |
|---|---|
| `r > R` geçen | **187** parçacık (`t = 0,2 s`'de `28`'di) |
| `r > 2R` geçen | `28` (= merminin kendisi) |
| dışarı giden iç madde | `2847`, medyan `r = 57,7 m`, `v_r = 0,193 m/s` |
| **`2R`'ye varış süresi** | **`~550 s`** |

**Üretim ölçütü `2R`'ye bakıyor** (`momentum_transfer`'in
`control_radius = 2R`'si) ve hedef maddesi oraya **henüz varmamış** —
`5,5` kat eksik.

> Hedef maddesi `R`'yi **geçiyor** (`28 → 187`) ama `2R`'yi geçmiyor.
> Yani `β`'nın sabit kalması *"ejekta yok"* değil **"ejekta sayılmıyor"**
> demek olabilir ve ben ikisini ayırmadan karar verdim.

`t_end = 600 s` gönderildi (iş `1506765`), ölçüt yine önden yazıldı:

| gözlenen | sonuç |
|---|---|
| `β > 2,5` | süre **yetersizdi**, model gözlemi üretiyor |
| `β < 1,8` ve durulmuş | süre değil, **model-form** kesinleşir |
| arası | kısmi; `t_end` daha da büyütülmeli |

#### Elenenler ve elenmeyenler — güncel

| aday | durum |
|---|---|
| yerçekimi | **elendi** (`%0,14` fark, `t = 100 s`) |
| gözeneklilik | **zayıf** — katı sahnede `β` `1,411 → 1,517` (`+%7,5`), gereken `2,3×` |
| çözünürlük | **elendi** — `λ₂` `2 → 4`: parçacık `28 → 150` ama momentum `1,46e6 → 1,21e6` (`−%17`), yani **yakınsamış** |
| **koşu süresi** | **AÇIK** — `2R` varış süresi `~550 s`, koşulan `100 s` |

Ejekta yönlülüğü de ölçüldü: kaçan maddenin **tamamı** geri gidiyor
(`p_ileri = 0`, iptal `%0`). Yani ejekta kusursuz yönlü; sorun yön
değil **miktar**.

#### Momentum anatomisi — **gereken momentum motorda var**

`scripts/a17_momentum_anatomisi.py` tek bir `β` sayısının karıştırdığı
üç soruyu ayırıyor. `t = 100 s` durumunda:

| soru | ölçüm |
|---|---|
| **momentum var mı?** | dışa giden `4790` parçacık, `2,02e9 kg`, eksenel net **`−1,1813e7`** — gerekenin (`7,91e6`) **`1,49` katı** |
| **yönlü mü?** | genel yönlülük `0,0206` → ezici çoğunluk **eş yönlü çınlama** |
| **çıkıyor mu?** | `r > 2R`: `28` (= mermi). **Hayır.** |

Korunum sağlam: `|p_toplam| = 3,5604e6` = merminin momentumu.

> Yani A17 **ters yönde** okunmuş: motor az momentum üretmiyor,
> ürettiği yönlü momentum **gövdeden çıkmıyor**.

Yönlülük kabuk kabuk bakınca nerede olduğunu söylüyor:

| `r/R` | `n` | yönlülük |
|---|---|---|
| `0,00 – 0,25` | 81 | **`0,3150`** |
| `0,25 – 0,50` | 494 | `0,0063` |
| `0,50 – 0,75` | 1415 | `0,0440` |
| `0,75 – 1,00` | 2732 | `0,0692` |

Yönlü kısım **iç** kabukta; dış kabuk neredeyse tamamen eş yönlü. Kazı
akışı hâlâ gövdenin içinde.

#### Ama bir **çınlama imzası** var — ve kestirimi zayıflatıyor

Hız bantlarında eksenel momentumun **işareti dönüyor**:

| `v_r` (m/s) | `n` | kütle (kg) | `p_eksen` |
|---|---|---|---|
| `0 – 0,1` | 2660 | `1,06e9` | **`+9,28e6`** |
| `0,1 – 0,5` | 1559 | `6,85e8` | **`−1,74e7`** |
| `0,5 – 2` | 473 | `2,28e8` | `+2,52e6` |
| **`2 – 10`** | **68** | `4,04e7` | **`−1,14e7`** |
| `10 – 100` | 2 | `1,25e6` | `+3,65e6` |
| `> 100` | 28 | `579 kg` | `+1,46e6` (mermi) |

`v_kaçış = 0,0824 m/s`. `2–10 m/s` bandı kaçıştan `25–120` kat hızlı ve
tek başına gerekenin `1,44` katını taşıyor.

> **Çekince — kendi kestirimime karşı:** dört işaret dönüşü var. Madde
> tutarlı bir tabaka halinde değil **salınım** halinde. O yüzden anlık
> `−1,1813e7`, kaçacak momentumun **üst sınırı değil**; salınımın o
> fazdaki değeri. `1,49 kat` bir *imkân*, bir *garanti* değil.

Bu yüzden `600 s` koşusunun ölçütü **`β` üzerine** yazıldı, momentum
anatomisi üzerine değil: anatomi imkânı gösteriyor, `β` gerçekleşmeyi
ölçüyor.

| `600 s`'de gözlenen | çıkarım |
|---|---|
| `β > 2,5` | salınım **değil** akış; süre yetersizdi |
| `β < 1,8` ve durulmuş | salınım; anlık momentum aldatıcıydı, **model-form** |
| arası | kısmi boşalma; `t_end` daha da büyütülmeli |

#### ⚠ *"Yerçekimi elendi"* de **YANLIŞTI** — aynı hata, ikinci kez

Yerçekimi sınavı `t = 100 s`'de yapıldı ve `%0,14` fark çıktı. Ama:

| | |
|---|---|
| yığın yoğunluğu | `1808,2 kg/m³` |
| **serbest düşme zamanı** `t_ff` | **`1562,2 s`** |
| `R / v_kaçış` | `994,5 s` |
| sınav yapıldığı an | `t/t_ff = ` **`0,064`** |

> `t/t_ff = 0,064`'te yerçekimi **etkisiz olmak zorundadır**. `%0,14`
> ölçüp *"yerçekimi elendi"* demek, sınavı etkisiz olduğu yerde
> yapmaktı. `600 s`'de `t/t_ff = 0,384` — yerçekimi orada
> **belirleyici**.

Yerçekimli kol `6:19:12`, yerçekimsiz `3:39:22` (`1,73×`). `600 s` için
yerçekimli koşu `~36 sa` eder ve `24 sa` sınırına **sığmaz**. Bu yüzden
koşu yerine **enerji ölçütü** hesaplandı (küresel potansiyel,
`Φ_i = −G[M(<r_i)/r_i + Σ_{r_j>r_i} m_j/r_j]`):

| kol (`t = 100 s`) | `E > 0` kütle | eksenel momentum | `β_enerji` |
|---|---|---|---|
| yerçekimli | `%93,06` | `−3,4645e6` | `1,9731` |
| yerçekimsiz | `%93,78` | `−2,5517e6` | `1,7167` |

`%93` **bağsız** çıkıyor. Bu tek başına gövdenin dağıldığı anlamına
gelmiyor — ve nedeni A17'nin kilidi.

#### Kök neden adayı: **cismi tutan şey yerçekimi değil mukavemet**

| | enerji (J/kg) | `GM/R`'ye oran |
|---|---|---|
| yerçekimsel bağlanma `GM/R` | `3,394e-3` | 1 |
| `Y0 = 1 Pa` | `5,53e-4` | `0,163` |
| `Y0 = 100 Pa` | `5,53e-2` | `16,3` |
| **`Y0 = 3513 Pa`** (en düşük sınanan) | `1,943` | **`572`** |
| `Y0 = 2,15e6 Pa` | `1189` | `3,50e5` |

Rejim geçişi `Y0/ρ ≈ GM/R`'de, yani **`Y0 ≈ 6,14 Pa`**.

> **FAZ 4.12 yanlış aralıkta ölçtü.** `Y0`'ı `3513 → 2,15e6 Pa` taradı;
> o aralıkta mukavemet/yerçekimi oranı `572` ile `350 000` arasında —
> **baştan sona aynı rejimde**. *"β `Y0`'a duyarsız"* bulgusu
> *"`Y0` önemsiz"* demiyor, **"aralık tek rejimde"** diyor.

Gerçek Dimorphos kohezyonu **~Pa** mertebesinde kestiriliyor: fiziksel
çalışma noktası geçişin tam üzerinde ve orası **hiç sınanmadı** —
geçişin `572` katı üstünden başladık.

> Bu, KAYIT-029'un dersinin **üçüncü** kez tekrarı: *"bir büyüklüğün
> nasıl davrandığını, ilgilenilen çalışma noktasını içermeyen bir
> aralıkta ölçerek söyleyemezsin."* Daha önce `r_dep/r_şok` ve
> `r_iç/r_dış`'ta oldu; şimdi `Y0`'da.

İş `1506779` üç kolu (`Y0 = 1 / 10 / 100 Pa`) geçişin iki yanına
yerleştiriyor. Ölçüt önden yazıldı:

| gözlenen | çıkarım |
|---|---|
| `Y0 = 1 Pa`'da `\|p_eksen\|` temelin `1,5` katını geçerse veya `β > 2,0` | **mukavemet rejimi** sebeptir |
| üç kolun üçü de temele bit düzeyinde yakınsa | `Y0` da değil |

#### Üç ölçüt de koştu — **üçü de hipotezlerimin aleyhine**

**1. Süre (iş `1506765`, `t_end = 600 s`, `22:50` duvar):**

| | |
|---|---|
| `t_sim` | `600,000 s` (tam) |
| `β` | **`1,411216`** |
| `t = 0,2 s`'deki `β` | `1,411216` |
| `n_ejekta` | `28` |
| momentum kapanışı | `2,86e-12` |

`3000` kat uzun koşu, `β`'yı **bit düzeyinde** değiştirmedi. Ölçüt
`β < 1,8` idi → **süre sebep değil.**

`2R`'ye varış kestirimim `~550 s`'ti ve tutmadı: madde yavaşlıyor.
`t = 100 s`'de `r = 57,7 m`, `v_r = 0,193 m/s`; sabit hızla `600 s`'de
`r ≈ 154 m` eder — `2R = 164 m`'nin **altında**, üstelik çınlama
yavaşlatıyor.

**2. Mukavemet rejimi (iş `1506779`):**

| `Y0` (Pa) | `β` | `n_ejekta` |
|---|---|---|
| 1 | `1,411215` | 28 |
| 10 | `1,411215` | 28 |
| 100 | `1,411215` | 28 |

Üçü de **bit düzeyinde aynı**. Ölçüt gereği: **`Y0` da değil.**
Tesisat ayrıca doğrulandı — `Y0` dizileri gerçekten farklı
(`1` / `100` / `3513`; blok `1e7` sabit), yani çözücüye ulaşıyor.

**3. Yerçekimi (enerji ölçütü, `t = 100 s`):** `β_enerji` `1,7167`
(yerçekimsiz) → `1,9731` (yerçekimli). Yön doğru ama `3,2225`'e uzak.

#### Sonuç: A12 baştan haklıydı ve bu **üçüncü** doğrulaması

Bütün bu elemeler tek bir şeye yakınsıyor ve o şey **zaten yazılıydı**:

> [ADR-0028](adr/ADR-0028-uzun-kosu-kararliligi.md): *"kontrol yüzeyini
> geçen malzeme, hedeften kopan ejekta değil, **merminin geri
> sıçramasıdır**."*

A12 bunu bir kez yeniden keşfettiğimi zaten kaydetmiş. Bu turda
**üçüncü** kez aynı yere geldim. Fark: bu kez ölçtüm.

`n_ejekta = 28` ve kaçan kütle `579,40 kg` **her koşuda**, `t_end`
`0,2 → 600 s` (`3000×`), `Y0` `1 → 2,15e6 Pa` (`6` mertebe),
yerçekimi açık/kapalı, gözenekli/katı fark etmeksizin. `579,4 kg`
DART'ın kütlesidir.

> **Hedef parametreleri `β`'yı değiştiremez, çünkü `β` hedefi
> ölçmüyor.** Gözeneklilik (`+%7,5`) ve çözünürlük (`−%17`) etki
> ediyor — ikisi de merminin ayrıklaştırmasını veya çarptığı yüzeyin
> sertliğini değiştirdiği için.

#### Yapılan: kimlik artık **taşınıyor**

Kusur ölçülebilir değildi çünkü kabalaştırmadan sonra `is_impactor`
hiçbir parçacıkta korunmuyordu ve `hedef = ~is_impactor` **her yerde
`True`** oluyordu. Kaçan `28` parçacık *"hedef ejektası"* etiketiyle
sayılıyordu.

`coarsen_to_sites` artık `mermi_kesri` taşıyor — bayrak değil **kesir**,
çünkü kabalaştırma mermi ve hedefi aynı siteye karıştırabiliyor. Kütle
ağırlıklı taşındığı için toplam mermi kütlesi **tam** korunuyor
(`Σ m_k f_k = Σ m_i f_i`, ölçülen hata `< 1e-14`).

Böylece `β`'nın payı ilk kez **ayrıştırılabilir**: `p_eksen_mermi` ve
`p_eksen_hedef` ayrı ayrı ölçülüyor
(`scripts/a17_momentum_anatomisi.py`, `[3b]` bölümü).

#### Ve ölçüldü (iş `1512733`) — **hedef payı tam sıfır**

Beklenti koşudan **önce** yazıldı (*"`hedef_payi ~ 0` çıkmalı; belirgin
şekilde `> 0` çıkarsa A17 hakkındaki bütün teşhis yanlıştır"*).

| | ölçülen |
|---|---|
| taşınan mermi kütlesi | `579,4000 kg` (DART'ın kütlesi) |
| `mermi_kesri > 0,5` olan | `28` parçacık — kaçan sayıyla **birebir** |
| taşıma hatası | **`0,000e+00`** (`< 1e-14` değil, **tam**) |

Ayrıştırma:

| | |
|---|---|
| kaçan **mermi** kütlesi | `579,40 kg` — sahnedeki merminin **tamamı** |
| kaçan **hedef** kütlesi | **`0,0000e+00 kg`** |
| `p_eksen` mermi | `+1,4641e6` |
| `p_eksen` hedef | **`+0,0000e+00`** |
| **hedef payı** | **`0,0000`** |
| `β` (yalnız mermiden) | `1,4112` |
| `β` katkısı (hedeften) | **`0,0000`** |

> `β = 1,4112`'nin **tamamı** merminin geri sekmesi. Hedef ejektasının
> katkısı **tam olarak sıfır** — yuvarlama düzeyinde küçük değil,
> **hiç**. Mermi gelen momentumunun `%41`'ini geri taşıyor.

Bu, kütleden **çıkarılan** sonucun artık **doğrudan ölçülmesi**. Aynı
zamanda bütün elemelerin neden aynı sonucu verdiğinin açıklaması:
`Y0`, yerçekimi ve koşu süresi hedefe ait; `β`'nın payında hedeften
hiçbir şey yok.

> Bu A17'yi **kapatmıyor**. Kapattığı şey şu: *"ejekta mı, sekme mi"*
> sorusu artık tahminle değil **ölçümle** yanıtlanıyor — ve cevap
> `0,0000`.
>
> Açık kalan asıl soru: gözlemi (`β = 3,2225`) üretecek hedef ejektası
> için ne gerekiyor. Daha uzun koşu değil (`3000×` ölçüldü), daha zayıf
> malzeme değil (altı mertebe ölçüldü). Ya gözlenebilirin tanımı
> (`d > 2R` kontrol yüzeyi) ya da modelin ejekta üretimi değişmeli —
> ve bu bir **ADR** kararı.

#### Üçüncü aday: ejekta **parçacık kütlesiyle nicemli**

| | |
|---|---|
| hedef parçacık kütlesi (medyan) | `3,73e5 kg` |
| gereken ejekta (`1 m/s` için) | `6,45e6 kg` = **`17` parçacık** |
| `2R` ölçütüyle ölçülen hedef ejektası | `0` – `91 kg` |
| `r > R` ölçütüyle (nokta 6) | **`3,98e4 kg`** — bir parçacık `3,91e4` |

Yani gerçek bir hedef parçacığı **yüzeyi geçmiş ama `2R`'yi
geçmemiş**. Üretim ölçütü onu saymıyor.

`3,98e4 kg` bile gerekenin **`%0,6`**'sı — hâlâ `170` kat eksik. Yani
nicemleme bir **taban** koyuyor ama açığın tamamını açıklamıyor.

> ### `91,3 kg` iddiam **şüpheli** — düzeltme
>
> ADR-0045 §9'da bunu *"gerçek hedef ejektası"* diye yazdım. Kaçan
> parçacıkların kütleleri incelenince `579,400` (nokta 0) ile
> `670,697` (nokta 4) arasındaki fark, kabalaştırmanın karıştırdığı
> mermi+çekirdek parçacıklarından geliyor olabilir — `2R` ölçütünde
> hangi parçacığın ne olduğu artık ayırt **edilemiyor** (aktarımdan
> sonra `is_impactor` boş).
>
> **Ayrıştırılmadı.** O yüzden `91,3 kg`'ı *"gerçek hedef ejektası"*
> diye okumayı geri alıyorum; kesin olan tek şey `r > R` ölçütünde
> nokta 6'da `3,91e4 kg`'lık **bir parçacığın** yüzeyi geçtiği.

#### `boulder_Y0` **hiçbir taramada değişmedi** (2026-08-21, yerel CPU)

A17'nin bütün elemeleri `β = 1,411216`'yı bit düzeyinde bırakınca şunu
sordum: *`Y0` taramaları çarpmanın gerçekten gördüğü malzemeyi
değiştirdi mi?* Koda bakınca eleme koşullarının `Y0` kolu

```
faz48_iki_asama.py:156   return {**kw, "matrix_Y0": float(Y0)}
inference/forward.py:99  kw.update(boulder_alpha0=a0, matrix_Y0=y0, ...)
inference/forward.py:103 kw.update(matrix_alpha0=a0, matrix_Y0=y0, ...)
```

**yalnızca matrisi** eziyor. `build_scene`'in `boulder_Y0` varsayılanı
`1,0e7 Pa` ve `SAHNE` onu hiç vermiyor: yani FAZ 4'ün **hiçbir**
taramasında (`Y0` `1 Pa`–`2,15e6 Pa`, çıkarım uzayının `Y0` ekseni
dahil) blokların mukavemeti değişmedi. Bloklar hedefin kütlece
**%36,3**'ü.

Ölçüm **kanıt koşusu değil, sahne kurulumu** — yerel CPU'da koştu
(`scripts/a17_carpma_bolgesi_malzemesi.py`, üretim tohumu `20260801`).
Ölçütler veriye bakılmadan yazıldı (betiğin kendi belgesinde).

##### İki kuşkum da **çürüdü**

| kuşku | ölçüt | ölçülen | yargı |
|---|---|---|---|
| *"çarpma bir bloğun içine düşüyor"* | blok kütle payı `>= %50` | `r <= 8 m`: **`0,0000`**, `r <= 15 m`: `0,0738` | **çürüdü** |
| *"ejekta ayrıklaştırma tabanının altında"* | krater içinde `< 20` parçacık | üretim inceltmesinde (`λ₂ = 2`) `r <= 15 m`'de **`223`** hedef parçacığı | **çürüdü** |

Gereken ejekta (`6,449e6 kg m/s`) ince bölge parçacığı (`4,66e4 kg`)
cinsinden: `1 m/s`'de `138` parçacık, `10 m/s`'de **`13,8`**,
`100 m/s`'de `1,4`. Yani nicemleme kaba ama **engel değil**.

##### Ayakta kalan: bölgenin **ortalama mukavemetini blok belirliyor**

| bölge | `n` (kaba / ince) | blok kütle payı | kütle ağırlıklı `Y0` |
|---|---|---|---|
| `r <= 8 m` | `4` / `37` | `0,0000` | `1,00e4 Pa` |
| `r <= 15 m` (krater) | `22` / `223` | `0,0738` | **`7,47e5 Pa`** |
| `r <= 25 m` | `116` / `952` | `0,3366` | `3,37e6 Pa` |

Krater bölgesinin kütlesi `%92,6` matris ama **ortalama mukavemeti
matrisin `75` katı**, çünkü `%7,4`'lük blok `1e7 Pa`'da duruyor.
Bunun aritmetik sonucu:

| `matrix_Y0` | bölgenin `<Y0>`'ı |
|---|---|
| `1 Pa` | `7,3779e5` |
| `10 Pa` | `7,3780e5` |
| `100 Pa` | `7,3788e5` |
| `1e4 Pa` | `7,4705e5` |
| `2,15e6 Pa` | `2,7292e6` |

> İş `1506779`'un üç kolu (`1 / 10 / 100 Pa`) krater bölgesinin kütle
> ağırlıklı mukavemetini **`1,0001` kat** oynatıyor. *"Üçü de bit
> düzeyinde aynı çıktı"* bulgusu bu yüzden `Y0`'ın etkisiz olduğunu
> göstermiyor olabilir: **taranan şey bölgede neredeyse hiç
> değişmiyordu.**

Bu bir **aritmetik**, sınav değil: ölçülen tek şey blok kütle payı,
gerisi ondan çıkıyor. Ve kütle ağırlıklı ortalama bir **vekil** —
matris `%92,6` ile sürekli faz ve kazıyı o yönetiyor olabilir. Bunu
ancak bir koşu söyler.

##### Çarpma noktasının malzemesi bir **kura** — sekiz tohum

| tohum | `r <= 15 m` blok kütle payı |
|---|---|
| **`20260801`** (üretim) | **`0,0738`** |
| `20260802` | `0,4373` |
| `20260803` – `20260808` | `0,0000` (altı tohumun altısı) |

Sekiz tohumun altısında krater bölgesi **saf matris**. Yani `Y0`
taramasının anlamlı olup olmaması tohuma bağlı ve **bütün A17
koşuları tek tohumla** (`20260801`) yapıldı. Bu, ensemble'ın
istatistiksel yakınsaması için de ayrı bir uyarı.

##### Bunu kapatacak koşu — ölçüt **önden**

İki kol, ikisi de ucuz (`t_end = 0,2 s`, tek nokta):

| kol | değişen | beklenti |
|---|---|---|
| **B1** | üretim tohumu, `boulder_Y0` `1e7 -> 1e2 Pa` | `β` oynarsa mukavemet **elenmemiştir** |
| **B2** | tohum `20260803` (saf matris), `matrix_Y0` `1e4 -> 1 Pa` | `β` oynarsa mukavemet **elenmemiştir** |

- İki kolun herhangi birinde `β` farkı `> %10` -> *"`Y0` da değil"*
  yargısı **geri alınır**; mukavemet A17'nin adayı olarak geri döner.
- İkisinde de fark `< %1` -> mukavemet, öncekinden **daha sağlam**
  bir zeminde elenmiş olur (bu kez taranan şey bölgede gerçekten
  değişmişti).
- Arası -> kısmi; blok geometrisi ayrıştırılmalı.

> **Bu koşu bu oturumda gönderilemedi:** TRUBA MCP bağlantısı
> `egitimg16u1` olarak açılıyor ve `/arf/scratch/egitimg16u4`
> `Permission denied` veriyor; `driftclaude` çalışma alanı erişilebilir
> değil. Bu bir kod sorunu değil, **erişim** sorunu.

#### Hasar sınandı ve **elendi** — yolda iki kusur çıktı (2026-08-21)

Bütün bu tur **yerel RTX 3050**'de koştu; TRUBA çalışma alanına
erişilemiyor (MCP `egitimg16u1` olarak bağlanıyor). Bu bir engel
değil çıktı: makine referansı **birebir** tutturuyor.

| kol | TRUBA/kayıtlı | **yerel** |
|---|---|---|
| iki aşamalı `β` | `1,411216` | **`1,411216`** |
| `A1` | `2,0391` | `2,0391` |
| aktarım momentum hatası | `8,76e-15` | `8,76e-15` |
| tek aşamalı `β` | `1,6175832076207557` | **`1,617583208`** |

> `t_end = 0,2 s`'lik iki aşamalı koşu bu dizüstünde **`14` dakika**.
> Yani A17'nin bundan sonraki elemeleri TRUBA **olmadan** yapılabilir.

##### Kök neden adayı: `damage` FAZ 4 boyunca **kapalıydı**

| kaynak | ne diyor |
|---|---|
| `configs/p3_dimorphos.yaml` | `damage: enabled: true` |
| `faz44_dart_yakinsama.py::_malzeme()` | `damage=DamageParams(enabled=False)` |

İkincisi FAZ 4'ün **bütün** koşularının malzemesi — G4 kapısı,
ensemble ve çıkarım dahil. ADR-0027 (kabul edilmiş, `2026-08-01`)
bu durumun sonucunu önceden yazmıştı:

> *"`D = 0` bırakmak, malzemenin çekmede sınırsız dayanıklı olduğunu
> varsaymak demekti — krater hacmini ve dolayısıyla ejekta kütlesini,
> yani **β'yı** sistematik olarak küçültürdü."*

##### İlk çift **geçersiz**: tesisat sınavı düştü

Ölçüt (`docs/A17-HASAR-OLCUTU.md`) koşudan **önce** yazılıp
commit'lendi (`ba04d36`). İlk maddesi tesisattı ve düştü:
`--hasarli` kolunda `D_max = 0,0000`.

Tanı ölçüldü — hasar **oluşuyor**, aktarım **taşımıyordu**:

| aşama-1 (üretim sahnesi) | |
|---|---|
| `t = 4,6e-4 s`'de `P_min` | `-1,37e9 Pa` (kusur eşiğinin `~80` katı) |
| `t = t₁ = 4,767e-3 s`'de `D_max` | **`0,562`** |
| aktarımdan **sonra** | **`0`** |

`coarsen_to_sites` `D`'yi taşımıyordu, `IkiAsamaSahne`'nin alanı
yoktu ve aşama-2 çözücüsü `D = 0` ile başlıyordu. Yani şokun ürettiği
bütün hasar `t₁`'de siliniyor ve cisim çekmede yeniden *"sınırsız
dayanıklı"* oluyordu. **Kusur sessizdi:** `--hasarli` kolu hasarsız
kolla aynı `β`'yı veriyor ve hiçbir defter tutulmuyordu.

Taşıma eklendi (`hasar=` kütle ağırlıklı, `Sum m D` hatası
`0,000e+00`; `WarpSolid3D(D0=...)`; hasar kapalıyken `D0` vermek artık
`ValueError`). Altı gerileme testi: `tests/test_hasar_aktarimi.py`.

##### Aktarımın **durum sıfırlaması** ölçüldü — iddiamı geri alıyorum

Aktarım yalnızca `x, v, m, u, h` taşıyor; aşama-2 `rho`'yu
`rho0/alpha0`'a, `alpha`'yı `alpha0`'a, `S`'yi sıfıra kuruyor. Bunun
hasar kolunu *"kirlettiğini"* yazmıştım (`934fcd3`). **Ölçtüm ve
küçük çıktı:**

| sıfırlanan | etkilenen kütle payı |
|---|---|
| ezilme (`alpha < alpha0`) | `1,33e-3` |
| `rho` (`> %1` sapan) | `1,81e-5` |
| `S`, ince bölge **dışında** | medyan `1,79 Pa` (`Y0 = 1e4`) |

Sıfırlama gerçek ama **ince bölgeyle sınırlı** (`r < 3 m`), yani
kütlenin binde biri. *"Hasar kolunu kirletiyor"* demem fazlaydı.

##### Karar: tek aşamalı çift — hasar **elendi**

Aktarım hiç olmadığı için durum da sıfırlanmıyor. Ölçüt EK'te,
koşudan önce (`934fcd3`).

| | **K** (hasar kapalı) | **H** (hasar açık) |
|---|---|---|
| `β` | `1,617583208` | `1,617592767` |
| `n_ejekta` | `803` | `803` |
| `D_max` | `0` | **`1,0000`** |
| tam kırık parçacık | `0` | **`3`** |
| `D` ortalama | `0` | `2,757e-4` |
| krater derinliği | `0,047697` | `0,048595` |

- **[0] tesisat:** `D_max = 1,0`, `3` tam kırık -> hasar **koşuyor**.
- **[0b] referans:** `K` kayıtlı değerden `%0,000` sapıyor -> tuttu.
- **[1] birincil:** `|Δβ| / β = 5,9e-6` -> ölçütün *"`< %1` ise sebep
  değil"* dalı. **Hasar A17'nin sebebi değil.**

> ADR-0027 haklıydı ama **ölçekte değil**: hasar `β`'yı
> küçültebilecek bir mekanizma, ancak üretim çözünürlüğünde
> **neredeyse hiç oluşmuyor** — `11 183` parçacığın **`3`'ü** tam
> kırılıyor, ortalama `D = 2,8e-4`. Doğrulanmış (32 testli) bir
> modül, `3,5 m`'lik parçacıkta fiilen **etkisiz**.

Krater derinliği `%1,9` arttı: yön ADR-0027'nin dediği yönde ama
büyüklük gerekenin (`2,3` kat) yanından geçmiyor.

##### Kaçan madde **şoklanmış** — ama hedef şok görmüyor

Üçüncü hipotezim de çürüdü. Ölçüt EK-2'de, koşudan önce (`9e9dad8`):

| | ölçülen |
|---|---|
| kaçan parçacık | `803` = `579,40 kg` = merminin **tamamı** |
| kaçan **hedef** kütlesi | **`0`** |
| `u_kaçan` (kütle ağırlıklı) | `5,613e6 J/kg` = **`1,19 x u_iv`** |
| gelen özgül `KE` | `1,888e7 J/kg` |
| iç enerjiye dönen | **`%29,7`** |
| sahnedeki **en yüksek** `u` | `5,644e6` — ve o **merminin** üstünde |

Geri sekme soğuk bir elastik yapay **değil**: kaçan madde erime
eşiğini geçmiş. Ama merminin enerjisinin `%70`'i kinetik kalıp geri
çıkıyor ve **sahnedeki en sıcak parçacık merminin kendisi** — yani
hedef güçlü bir şok hiç görmüyor.

##### **`β` mermi çözünürlüğünde yakınsamamış** — ve `1`'e doğru düşüyor

Ölçüt EK-3'te, koşudan **önce** (`8ed77fc`). Tek değişen `λ₁`;
`t_end`, sahne, tohum, `λ₂` aynı.

| `λ₁` | `A1` = mermi çapı / aralık | `N` (aşama-1) | **`β`** | `n_ejekta` |
|---|---|---|---|---|
| — (tek aşamalı, `λ = 2`) | `0,215` | `11 183` | `1,617583` | `803` |
| `19` | `2,039` | `12 705` | `1,411216` | `28` |
| **`38`** | **`4,078`** | `23 391` | **`1,185066`** | `40` |

`Δβ = -0,226150`, bağıl **`%16,0`** — ölçütün `%10` dalı. Yargı:
**`β` mermi çözünürlüğünde yakınsamamış.**

> Yön **gözlemden uzağa**. Mermi daha iyi çözüldükçe geri sekme
> zayıflıyor; sekme `β`'nın **tamamı** olduğu için `β` de düşüyor.
> Üç nokta tekdüze azalıyor ve azalma **hızlanmıyor da yavaşlamıyor**
> (`-0,206`, `-0,226`). Yakınsama limiti gözlemin `3,2225`'i değil,
> **`β -> 1`** yönü: yani *"momentum artışı yok"*.

##### Bu `G4-B1`'i **düşürüyor**

`B1` ölçütü *"ardışık çözünürlükte `β` farkı `< 0,1`"* diyor ve
kapı raporunda `0,000843` ile **geçti**. Ama o tarama `λ₂`'yi
(**hedef** inceltmesi) değiştiriyordu. `λ₁` (**mermi** inceltmesi)
yönünde aynı ölçüt:

| tarama yönü | `Δβ` | bağıl | yargı |
|---|---|---|---|
| `λ₂` `2 -> 4` (hedef) | `0,000843` | `%0,06` | **geçti** |
| `λ₁` `19 -> 38` (mermi) | **`0,226150`** | **`%16,0`** | **düştü** |

> ### Eşik hangisi — kayda geçiyor (2026-08-21 düzeltmesi)
>
> İki yerde iki biçimde yazılı: kapı **üreticisi** mutlak `0,1`
> kullanıyor (`faz47_g4_kapi.py`; raporda `< 0.1`), ölçüt belgesi ise
> **`%10` bağıl** diyor (`G4-OLCUTLERI.md` B1). `β ≈ 1,41` için ikisi
> aynı sayı **değil** (`0,1` vs `0,141`).
>
> `λ₁` ölçümü **ikisini de** aşıyor: mutlak eşiğin `2,26`, bağıl
> eşiğin `1,60` katı. Yargı hangi okumayla bakıldığından bağımsız.
>
> **Önceki sürümde burada *"268 kat"* yazıyordu.** O sayı eşikle
> değil `λ₂` ölçümüyle oran (`0,226150 / 0,000843`), yani iki **tarama
> yönü** arasındaki fark. Eşik aşımı diye okunacak biçimde yazmıştım;
> düzeltiyorum.

> `B1`'in *"gözlenebilirler yakınsıyor"* yargısı, `β`'yı **üreten**
> yönde hiç sınanmamıştı. `β`'nın payındaki tek şey merminin
> sekmesiyken yakınsamayı hedef ızgarasında aramak, ölçmek istenen
> şeyin yanında ölçmekti.

##### A17'nin cevabı: `β` **hedeften hiç beslenmiyor** ve sekme bir ayrıklaştırma yapayı

Bu turda ölçülenler tek bir tabloya çıkıyor:

| ölçüm | sonuç |
|---|---|
| kaçan kütle (her çözünürlükte) | merminin **tamamı**; hedef payı **tam `0`** |
| kaçan madde şoklanmış mı | evet (`u = 1,19 x u_iv`) |
| merminin enerjisinin ne kadarı iç enerjiye döndü | **`%29,7`** |
| sahnedeki en sıcak parçacık | **mermi** — hedef güçlü şok görmüyor |
| hasar açık/kapalı | `Δβ = 5,9e-6` — **eleme** |
| mermi çözünürlüğü `2` kat | `Δβ = -%16` — **yakınsamamış**, `1`'e doğru |

> Yani `β = 1,41` bir fizik sonucu değil, **çözülmemiş bir çarpışmanın
> artığı**. Çözünürlük arttıkça artık küçülüyor ve altından
> **hedef ejektası çıkmıyor** — çünkü hiç yok.
>
> Gözlemin `3,2225`'ini bu ileri modelden çıkarmak için eksik olan
> şey bir parametre değil: hedef maddesini fırlatan **mekanizmanın
> kendisi**. Bu bir **ADR kararı** ve ölçüm tarafı artık kapalı.

##### Son deneme: **gerçek moloz yığını** rejimi — TRUBA, iş `1515196`

Geriye tek bir fiziksel açıklama kalmıştı: modelin hedefi bir moloz
yığını değil **kaya**. Rejim geçişi `Y0 ≈ 6,14 Pa`'da; model matrisi
`1e4 Pa` (geçişin `1 636` katı), **blokları `1e7 Pa`** (`1,6e6` katı)
ve blok mukavemeti FAZ 4 boyunca **hiç taranmamıştı** (KAYIT-050).
Üstelik yerçekimi kapalı olduğu için *"kaçış"* tanımsızdı.

TRUBA çalışma alanı `egitimg16u4` altında erişilemez olduğu için
`egitimg16u1` altında **sıfırdan** kuruldu (klon + `pip --target`
ile warp `1.15.0`). `--boulder-Y0` bayrağı eklendi — daha önce
`_sahne_Y0` yalnızca matrisi eziyordu.

**Ortam sınavı geçti** (ölçüt gereği, B kolu ondan önce koşmadı):

| | beklenen | ölçülen |
|---|---|---|
| `β` | `1,4112162721355217` | **birebir aynı** |
| `A1` | `2,0390593305845943` | **birebir aynı** |

Kol B — `matrix_Y0 = 1 Pa`, `boulder_Y0 = 1 Pa`, **yerçekimi açık**,
`t_end = 5 s`:

| | üretim | **B (moloz yığını)** |
|---|---|---|
| `β` | `1,411216272` | `1,411231044` |
| bağıl fark | — | **`1,05e-5`** |
| `n_ejekta` | `28` | `28` (mermi) |
| **kaçan hedef kütlesi** | `0` | **`0`** |
| `bekleyen` (içeride dışarı giden) | `17` | **`0`** |
| momentum kapanışı | `1,31e-14` | `3,10e-13` |

Koruyucu ölçüt de geçti: `bekleyen = 0` ve kapanış `3e-13`, yani
cisim **dağılmadı** — sonuç *"ejekta çıktı"* ile *"cisim patladı"*
karışması değil.

> **Ölçütün birincil dalı:** *"kaçan hedef kütlesi `= 0` -> zayıf
> hedef de yetmiyor; sebep parametre değil **mekanizma** (model-form)
> ve bu bir ADR kararıdır."* Bu dal **düştü**.

Hedefi gerçek Dimorphos'un mukavemet rejimine indirmek ve yerçekimini
açmak `β`'yı `%0,001` oynattı ve hedef ejektası **yine tam sıfır**.
Yerçekimi açıkken `bekleyen` de `17 -> 0` oldu: zayıf cisimde dışarı
giden madde **daha da az**.

> ### Kendi ölçütümde bir kusur — kayda geçiyor
>
> `β` için *"`1,3 <= β < 2,0` -> kısmi"* bandını yazmıştım. **Kötü
> eşikti:** taban değerin (`1,4112`) kendisi o bandın içinde, yani
> hiç oynamayan bir sonuç *"kısmi"* okunurdu. Bandı sonradan
> değiştirmiyorum; sonucu **oynamadı** diye okuyorum
> (`Δβ/β = 1,05e-5`) ve karar zaten birincil ölçütte veriliyor.

##### Böylece parametre tarafı **kapandı**

| aday | nasıl elendi |
|---|---|
| koşu süresi | `3000×` — bit düzeyinde aynı |
| yerçekimi | `t = 100 s`'de `%0,14`; **`t = 5 s`'de zayıf cisimle `%0,001`** |
| matris `Y0` | 6 mertebe |
| **blok `Y0`** | **`1e7 -> 1 Pa`, bu koşu** |
| çözünürlük (`λ₂`) | yakınsamış |
| hasar | `Δβ = 5,9e-6` |
| gözeneklilik | zayıf (`+%7,5`) |
| **mermi çözünürlüğü (`λ₁`)** | **yakınsamamış — ama `β`'yı `1`'e itiyor** |

Geriye tek bir ifade kalıyor ve artık ölçülü:

> Bu ileri model **hedef ejektası üretmiyor** — mukavemet rejiminden,
> yerçekiminden, süreden ve hasardan bağımsız olarak. `β`'nın tamamı
> merminin sekmesi ve o sekme çözünürlükle **kayboluyor**. Gözlemin
> `3,2225`'i için eksik olan bir parametre değil, ejektayı üreten
> **mekanizmanın kendisi**.

##### **Kök neden bulundu: kütle oranı** — şok hedefe girmiyordu (TRUBA `1515337`)

Kaçan maddenin enerjisine bakarken hedefinkine de bakıldı ve ölçü
şuydu (tek aşamalı kontrol kolu, `t = 0,2 s`):

| | |
|---|---|
| merminin en sıcak parçacığı | `5,6445e6 J/kg` |
| **hedefin** en sıcak parçacığı | **`8 993 J/kg`** |
| oran | **`0,0016`** |

`6,1 km/s`'lik bir çarpmada hedefin çarpma noktası `1e6 – 1e7 J/kg`'a
çıkmalı. `9e3` çıkıyor — **üç mertebe** eksik. Şok hedefe **girmiyor**;
`β`'nın hedeften beslenmemesi bunun **sonucu**.

Hipotez: bugüne kadarki bütün çözünürlük ölçütleri **uzunluk**
ölçütüydü. `A1 = mermi çapı / yerel aralık ≥ 2` geçiyor (`2,039`) ama
o ölçüt merminin **aşama-1** ızgarasında çözülüp çözülmediğini
soruyor. Aktarımdan sonra mermi aşama-2 ızgarasında ilerliyor ve orada
ölçülmesi gereken **kütle** (`scripts/a17_kutle_orani.py`):

| `λ₂` | `s_ince` | hedef parçacığı | **`μ = m_hedef/m_mermi`** | `N` |
|---|---|---|---|---|
| **2** (üretim) | `3,50 m` | `4,66e4 kg` | **`80,4`** | `10 413` |
| 4 | `1,75 m` | `5,83e3 kg` | `10,1` | `10 880` |
| 6 | `1,17 m` | `1,73e3 kg` | `2,98` | `35 959` |
| 8 | `0,875 m` | `7,28e2 kg` | `1,26` | `71 134` |

> Mermi (`579,4 kg`), üretimde kendisinden **`80` kat ağır tek bir
> parçacığa** çarpıyor. Momentumun büyük kısmının geri sekmesi böyle
> bir çarpışmada **beklenen** davranıştır.

Ölçüt `docs/truba/OLCUT-kutle-orani.md`'de, koşudan **önce** yazıldı
ve birincil gösterge bilerek `β` **değil** iç enerji seçildi.

| `λ₂` | `μ` | `u_hedef_max` | `u_mermi_max` | **oran** | `β` | `n_ejekta` | `A1` |
|---|---|---|---|---|---|---|---|
| 2 | `80,4` | — | — | `0,0016` | `1,411216` | `28` | `2,039` |
| **6** | `2,98` | `3,3635e6` | `4,4085e6` | **`0,7630`** | `1,307686` | `334` | `2,039` |
| **8** | `1,26` | `3,3573e6` | `4,6243e6` | **`0,7260`** | `1,289949` | `436` | `2,039` |

**Birincil ölçüt (`≥ 0,50`) geçti.** Hedefin en sıcak parçacığı
`8 993 → 3,36e6 J/kg`: **`370` kat**. Şok artık hedefe giriyor.

`A1` üç kolda da **tam olarak `2,039`** — yani korktuğum karışma
olmadı, tarama gerçekten tek değişkenli.

###### Ama `β` **yükselmedi** — ve "hedef ejektası" çıkan şey o değil

`β` `1,411 → 1,308 → 1,290` ile **düştü**. Sebep ayrıştırıldı:

| | `λ₂ = 6` | `λ₂ = 8` |
|---|---|---|
| kaçan parçacık | `334` | `436` |
| kaçanlarda taşınan **mermi** kütlesi | `576,5 kg` | `578,7 kg` |
| kaçanlarda taşınan **hedef** kütlesi | `108,71 kg` | `108,71 kg` |
| hedef-çoğunluklu kaçan parçacık | **`2`** | **`2`** |

> `108,713880 kg` iki koşuda **bit düzeyinde aynı** ve iki
> parçacıktan geliyor (`54,35694018 kg` × 2). Bu parçacıkların
> kütlesi ne `λ₂ = 6` (`1 726 kg`) ne `λ₂ = 8` (`728 kg`) ızgarasına
> ait; **aşama-1'in kabalaştırılmış siteleri** (`0,72 – 55,75 kg`).
>
> Yani bu **krater ejektası değil**, çarpma noktasındaki çekirdek
> maddesi. *"İlk kez hedef ejektası çıktı"* diye okumak yanlış olurdu.

Eşleşme düzeldi, `β`'nın payına giren hedef maddesi hâlâ yok.

##### Süre elemesi **yeniden açılıyor**

*"Koşu süresi elendi"* yargısı (`t_end` `0,2 → 600 s`, `β` bit
düzeyinde aynı) `μ = 80`'de ölçüldü — yani hedefin **hiç şoklanmadığı**
rejimde. Eşleşme düzeldiğine göre eleme, **mekanizmanın yok olduğu
yerde** yapılmış olabilir; bu deponun üç kez kaydettiği hatanın
(`ölçütü etkisiz olduğu yerde sınamak`) aynısı olurdu.

İş `1515364` gönderildi: `λ₂ = 6`, `t_end = 20 s`, ölçüt koşudan önce
(`n_hedef_ejekta` zamanla **artıyor mu**).

---

#### Yakınsama denetimi — **iki düğme düşüyor** (TRUBA `1515317`)

`scripts/yakinsama_denetimi.py` sekiz ayrıklaştırma düğmesini tek tek
taradı (`t_end = 0,2 s`, taban `β = 1,4112162721355217`):

| düğme | bağıl fark | yargı | mertebe | yeterli ayar |
|---|---|---|---|---|
| **`lam1`** | `2,349e-01` | **DÜŞTÜ** | **`2,07`** | — |
| `lam2` | `5,001e-02` | geçti | — | `2` |
| **`spacing`** | `1,455e-01` | **DÜŞTÜ** | — | — |
| `r_ince1` | `9,168e-02` | geçti | — | `3` |
| `r_ince2` | `4,843e-03` | geçti | — | `25` |
| `cfl` | `1,585e-03` | geçti | — | `0,25` |
| `n_mermi` | `1,090e-03` | geçti | — | `800` |
| `t1` | `4,820e-03` | geçti | — | `4,767e-3` |

**Yeni bulgu: `spacing` (kaba ızgara) de düşüyor** — `%14,6`. Bu
düğme bugüne kadar **hiç taranmamıştı**.

`lam1`'in gözlenen mertebesi **`2,07`**: hata `h²` ile küçülüyor, yani
bu bir **gerçek ayrıklaştırma hatası**, bir kusur değil. Ve `r_ince1`
`%9,17` ile eşiğin hemen altında — geçti ama **kıl payı**.

> ### En önemli ders bu tabloda
>
> `lam2` `β`'yı yalnızca `%5` oynattı ve **"geçti"** dedi. Aynı
> düğme, aynı taramada, hedefin iç enerjisini **`450` kat**
> değiştirdi (`0,0016 → 0,73`).
>
> **Bir gözlenebilirin yakınsama testini geçmesi, fiziğin
> yakınsadığı anlamına gelmiyor.** Gözlenebilir duyarsız olabilir —
> ve `β` tam olarak öyleydi.

---

#### A11 — çap **hâlâ ölü**, ve "canlı" diyen gösterge **benim hatamdı**

Ensemble `λ₂ = 4`, `n_bins = 16` ile koştu (iş `1515252`, `40` nokta,
`0/40` düşen). Koruyucu ölçüt geçti: derinliğin bağıl yayılımı
`%18,2` (`%10 – %40` bandında).

Koşunun kendi çıktısı *"benzersiz değer sayısı = 40 -> CANLI"* dedi.
**Yanlıştı.** Değerler `0,01 m` toleransla kümelenince:

| seviye | nokta |
|---|---|
| `5,4032 m` | `3` |
| `7,4916 m` | `37` |
| **ayrı seviye sayısı** | **`2`** |

`np.unique` kayan nokta gürültüsünü (`< 1e-4 m`, bağıl `1,3e-5`)
ayrı değer sayıyordu. Gösterge **canlı derken gürültü sayıyordu** ve
göstergeyi yazan bendim. Düzeltildi: artık toleransla kümeleme
yapılıyor (`faz412_Y0_duyarliligi.py`).

Yayılım `2,0884 m` ve bu **tam olarak bir kutu adımı**
(`n_bins = 16` → `±2,1 m`). Yani çap iki nicemleme seviyesi arasında
`3/40` noktada atlıyor, başka bir şey yapmıyor.

Bağımsız doğrulama — vekil (`fit_surrogate`, aşağıda): `krater_capi`
`q2 = 0,0111` (`S1`) / `0,2127` (`S3`). **Kullanılamaz.**

> **Önceden yazılmış ölçütün ikinci dalı geçerli:** *"benzersiz `≤ 2`
> **ya da** yayılım `< 2,1 m` -> `λ₂ = 4` yetmiyor."* İki koşul da
> sağlandı. **A11 açık kalıyor.**
>
> Ölçütün ilk dalı (`benzersiz ≥ 5` **ve** yayılım `≥ 2,1`) eşiği tam
> nicemleme değerine koyduğu için kötü kurulmuştu; bugün ikinci kez
> yaptığım eşik hatası. Dalı sonradan değiştirmiyorum.

#### Vekil **eğitildi** — ve `krater_derinlik` düştü

`40` nokta, `docs/olcumler/ensemble_1515252.csv`:

| gözlenebilir | `q2` (`S1`) | `q2` (`S3`) | güvenilir (`q2 > 0,5`) |
|---|---|---|---|
| `beta` | **`0,8725`** | **`0,9260`** | **evet** |
| `krater_derinlik` | `0,2351` | `0,2769` | hayır |
| `krater_capi` | `0,0111` | `0,2127` | hayır |

G4-C'de (`λ₂ = 2`, `S1`) kayıtlı değerler `krater_derinlik 0,907`,
`beta 0,749` idi. Yani `λ₂ = 2 → 4` ile **sıralama tersine döndü**.

> **Çekince — bu kol tek değişkenli DEĞİL.** `λ₂` ile birlikte
> `n_bins` de `8 → 16` değişti. Derinliğin `q2`'sindeki düşüşün
> çözünürlükten mi kutulamadan mı geldiği **ayrıştırılmadı**. Kendi
> kuralımı bu koşuda çiğnedim ve bunu sonucun yanına yazıyorum.

---

#### **DIŞ KIYAS** — model çanak değil **delik** açıyor (2026-08-21)

Bu deponun ilk **dış** doğrulaması. Bugüne kadarki bütün ölçütler
modelin kendi iç tutarlılığınaydı (Sedov, Hugoniot, korunum,
determinizm) — çarpma **sonucunun büyüklüğü** hiçbir dış standarda
karşı sınanmamıştı.

π-grubu krater ölçeklemesi (Holsapple 1993; Housen & Holsapple 2011)
verilen çarpma için krater hacmini kapalı formda verir. Sabitler
literatürden; **hiçbiri uydurulmadı**. Dimorphos'un hangi malzeme
ailesine düştüğü bilinmediği için bir **kuşak** tarandı
(`scripts/pi_olcekleme.py`, koşu gerektirmez):

| malzeme ailesi | rejim | `V (m³)` | çap (m) |
|---|---|---|---|
| kuru kum | yerçekimi | `4,93e4` | **`85,6`** |
| zayıf gözenekli | mukavemet | `6,12e3` | `42,7` |
| kohezyonlu toprak | mukavemet | `2,07e4` | `64,1` |
| sert kaya | mukavemet | `1,85e2` | **`13,3`** |

| | |
|---|---|
| π-ölçekleme aralığı | çap **`13,3 – 85,6 m`** |
| **modelin ölçtüğü** | çap **`7,49 m`** |

Model, **en sert kaya** ailesinin öngördüğünün bile altında — oysa
Dimorphos bir moloz yığını, yani zayıf uçta (`43 – 86 m`) olmalı.

##### Ve malzemeden **bağımsız** olan kıyas

Ölçekleme sabitleri tartışılabilir; şu tartışılamaz: çarpma
kraterleri **çanak**tır ve geçici kraterde derinlik/çap oranı
literatürde `0,15 – 0,30`'dur (Melosh 1989). Bu oran **boyutsuz** ve
hiçbir malzeme sabitine bağlı değil.

| | ölçülen |
|---|---|
| modelin derinliği | `15,28 m` |
| modelin çapı | `7,49 m` |
| **derinlik / çap** | **`2,040`** |
| literatür bandı | `0,15 – 0,30` |
| bandın üst sınırının | **`6,8` katı** |

> **Model çanak açmıyor, `delik` açıyor.** Mermi içeri giriyor ve
> madde yanlara **akmıyor** — kazı akışı yok. Ejektanın olmaması,
> `β`'nın hedeften beslenmemesi ve şokun hedefe girmemesi
> (`u_hedef/u_mermi = 0,0016`) bunun **aynı olgunun** üç yüzü.

Bu bulgu `tests/test_pi_olcekleme.py` ile kilitlendi: düzelirse test
düşer ve rapor güncellenmek zorunda kalır.

---

### A19 — **`krater_derinlik` krateri ölçmüyor: yokken var, varken yok** (2026-08-21)

`krater_derinlik` bu projenin **en güçlü** gözlenebiliriydi
(`G4-C`'de `q2 = 0,907`) ve çıkarım ona dayanıyor. İki yönlü sınandı;
ikisi de kötü çıktı.

#### Boş sınav — çarpmamış sahneye ne diyor

Ensemble yolunun `40` noktasının **çarpmamış** (referans)
konfigürasyonu çıkarıcıya verildi:

| | ölçülen |
|---|---|
| REF (çarpma **yok**) derinlik | `7,94 – 12,23 m`, medyan **`10,85 m`** |
| SON (raporlanan) derinlik | `13,65 – 16,46 m` |
| fark (çarpmaya ait olan) | `3,61 – 6,12 m` |
| **raporlanan değerin taban payı** | **`%67,7`** |

Ve vekil, hangisinin parametrelerle açıklandığını söylüyor:

| büyüklük | `q2` |
|---|---|
| SON (raporlanan) | `0,2769` |
| REF (çarpmasız taban) | `0,1287` |
| **fark (gerçek krater)** | **`-0,3283`** |

> Raporlanan derinliğin üçte ikisi çarpmayla ilgisi olmayan **yüzey
> yapısı**; ve çarpmaya ait olan kısım parametrelerle **ortalamadan
> bile kötü** açıklanıyor (`q2 < 0`).
>
> Bir gözlenebilirin parametrelerle güzel korele olması, ölçmek
> istediğin şeyi ölçtüğü anlamına gelmiyor. **Taban da parametrelere
> bağlıysa korelasyon tabandan gelir** — `boulder_alpha0` ve
> `f_boulder` yüzeyin pürüzünü belirliyor.

#### Dolu sınav — gerçek çukura ne diyor

Sentetik, denetimli fikstür (dolu küre, eksende `12 m` derin, `15°`
yarı-açılı düz tabanlı çukur, `508` parçacık kazılmış; çukurun
gerçekten orada olduğu ayrıca doğrulanıyor):

| | ölçülen |
|---|---|
| gerçek derinlik | `12 m` |
| çıkarıcının dediği | **`-0,03 m`**, çap `0` |

#### İkisi birlikte

| sınav | olması gereken | ölçülen |
|---|---|---|
| pürüzlü yüzey, çarpma yok | `0` | **`0,26 m`** |
| ensemble yolu, çarpma yok | `0` | **`10,85 m`** |
| gerçek `12 m` çukur | `~12 m` | **`-0,03 m`** |

> **Çıkarıcı yokken var, varken yok diyor.**

Düzgün (pürüzsüz) yüzeyde `x == x_referans` verildiğinde tam `0`
dönüyor — yani tek tuttuğu değişmez bu. Pürüz girer girmez bozuluyor.

#### Sonucu nereye kadar gidiyor

- `G4-C`'nin `C1`/`C2`/`C3` yargıları `krater_derinlik`'e dayanıyor.
- ADR-0046 `Y0`'ı *"derinlikte görünmüyor"* diye uzaydan çıkardı —
  o ölçüm de bu gözlenebilirle yapıldı.
- ADR-0045 (çap mı derinlik mi) yeniden okunmalı.

**Bu A19 kapanmadan çıkarım tarafında hiçbir sayı güvenilir değil.**

Kilit: `tests/test_krater_bos_sinav.py` — iki kusur
`xfail(strict=True)` ile sabitlendi; düzeltildikleri gün testler
**düşer** ve bu bölüm güncellenmek zorunda kalır.

---

### A21 — **Enerji yayılmıyor: gelen enerjinin `%78`'i `6` parçacıkta** (2026-08-21)

> ### Tek tabloda bütün zincir (`λ₁ = 38`, `t = 0,2 s`)
>
> | | enerji | pay |
> |---|---|---|
> | **gelen** | `1,0939e10 J` | `%100,0` |
> | hedefte iç enerji | `9,2822e9 J` | `%84,9` |
> | **bunun `6` parçacıkta olanı** | **`8,5548e9 J`** | **`%78,2`** |
> | hedefte kinetik | `1,0339e8 J` | `%0,9` |
> | mermide (sekme + ısı) | `1,4312e9 J` | `%13,1` |
>
> O `6` parçacık hedef kütlesinin **`%0,002`**'si.
>
> | | model | olması gereken |
> |---|---|---|
> | krater (yeni ölçü) | **`0,09 m`** | π-ölçekleme: çap `13 – 86 m` |
> | hedef ejektası | **`0 kg`** | gözlem için `6,45e6 kg` |
>
> **Çarpma enerjisinin `%78`'i altı parçacığa hapsolmuş durumda.**
> Kraterin olmaması, ejektanın olmaması ve `β`'nın hedeften
> beslenmemesi — üçü de bunun sonucu, üç ayrı sorun değil.


Farklı bir açıdan bakıldı: gelen enerji (`½ m v² = 1,0939e10 J`)
nereye gitti?

| kol | `KE` | `U` (ısı) | hedefte `KE` | hedefte `U` |
|---|---|---|---|---|
| tek aşama (`A1 = 0,215`) | `%38,2` | `%59,7` | `%0,004` | `%30,0` |
| iki aşama (`λ₁ = 38`, `A1 = 4,08`) | **`%5,6`** | **`%93,2`** | `%0,95` | **`%84,8`** |

İlk okuma `β`'yı **bağımsız olarak** doğruluyor: mermideki kinetik
enerji `%38,2 -> %4,7`, yani geri sekme çözünürlükle ölüyor —
`β`'nın `1,618 -> 1,185` düşüşünün ikinci ölçümü.

İkinci okuma asıl bulguyu veriyor: **enerji hedefe geçiyor
(`%84,8`) ama akış olmuyor (`KE = %0,95`).** Madde ısınıyor, hareket
etmiyor.

#### Isı nerede: **altı parçacıkta**

Hedefin iç enerjisi parçacık başına sıralandı (`λ₁ = 38`,
`10 387` hedef parçacığı):

| en sıcak | `U`'nun payı | kütlece payı |
|---|---|---|
| `1` parçacık | **`%26,7`** | `%0,0006` |
| `5` parçacık | **`%89,5`** | `%0,0020` |
| `10` parçacık | `%96,5` | `%0,0076` |
| `50` parçacık | `%100,0` | `%0,048` |

> `U`'nun **`%50`'si `2` parçacıkta, `%90`'ı `6` parçacıkta** —
> hedef parçacıklarının `%0,058`'i, hedef kütlesinin `%0,002`'si.

Çarpma bölgesinde (`r ≤ 15 m`, `230` parçacık) **medyan** `u` yalnızca
`0,49 J/kg` ve **medyan yoğunluk `1537,2 kg/m³`** — yani
`ρ₀/α₀`'ın tam kendisi, hiç değişmemiş. `ρ > 1600` olan `10` parçacık
(`%4,3`).

> **Şok yayılmıyor.** Enerji temas noktasındaki birkaç parçacığa
> dökülüyor ve orada kalıyor. Gerçek bir şok, mermi çapının birkaç
> katı yarıçapında bir yarıküreyi karşılaştırılabilir `u`'ya
> çıkarırdı.
>
> Ejektanın olmaması, kraterin `9 cm` kalması, `β`'nın hedeften
> beslenmemesi — hepsi **bunun** sonucu.

#### Ve bir sızıntı: `u < 0`

Aynı durumlarda hedef parçacıklarının **`%44,5`'inde iç enerji
negatif**:

| koşu | `u < 0` | en negatif | tutulan enerji |
|---|---|---|---|
| `λ₁ = 38` | `4 641 / 10 424` | `-12,06 J/kg` | `-7,0e6 J` (`%0,06`) |
| tek aşama | `4 942 / 11 183` | `-694 J/kg` | `-3,0e8 J` (**`%2,76`**) |

Sebep bulundu: `eos_tillotson.py` basıncı hesaplarken

```
u = wp.max(u_in, F(0.0))
```

diyor — **negatif `u`'yu sıfır sayıyor**. Ama durum değişkeni hiçbir
yerde kırpılmıyor (`integrator.py`: `u[i] += half_dt * dudt[i]`).

İki sonucu var:

1. **Defter ile fizik ayrışıyor.** `Σ m u` korunuyor ve
   `test_conservation` bunu doğruluyor; ama dinamiğin gördüğü enerji
   defterdekinden farklı.
2. **Negatif `u` bir borç.** O parçacık sonradan ısıtıldığında önce
   borcunu kapatıyor; EOS ısınmayı ancak `u > 0` olunca görüyor. Şok
   cephesinin arkasındaki madde **olması gerekenden uzun soğuk
   kalıyor** — ve bu, ısının yayılmamasının bir parçası.

Büyüklük ADR-0028'in kaydettiği `%1,5`'lik enerji hatasıyla aynı
mertebede; ikisinin aynı şey olup olmadığı **ölçülmedi**.

Kilit: `tests/test_ic_enerji_tabani.py` — kırpmanın kendisi ve
defter/fizik ayrışması geçiyor; integratörde taban olmadığı
`xfail(strict=True)` ile sabit.

**Çare yazıldı** (`integrator.kick_u_3d_tabanli`): `u` sıfırın altına
inmiyor **ve kırpılan miktar parçacık başına biriktiriliyor** —
sessizce kırpmak, bir kaçak kaynağını başkasıyla değiştirmek olurdu.
`WarpSolid3D(u_tabani=False)` **varsayılan kapalı**: açmak bütün
kayıtlı sayıları değiştirir ve bu bir **karar**, sessiz düzeltme
değil. Altı çekirdek testi (`tests/test_u_tabani_cekirdegi.py`).

#### İkinci mekanizma: **yetim parçacıklar** enerjiyi donduruyor

SPH'de komşusu olmayan bir parçacık hiçbir şeyle etkileşemez:
basınç gradyanı yok, `P dV` yok, **iş yapamaz**. İç enerjisi varsa o
enerji **donar**.

Ölçüldü (`λ₁ = 38`, `t = 0,2 s`, komşuluk yarıçapı `14 m = 2h`):

| | |
|---|---|
| komşusuz parçacık | **`40`** |
| toplam kütleleri | `409,6 kg` — merminin **`%71`**'i |
| taşıdıkları iç enerji | `1,323e9 J` = **`%12,1`** gelen enerjinin |
| kinetik | `6,14e8 J` = `%5,6` |
| **donmuş toplam** | **`%17,7`** |

Tek aşamalı kolda yetim **yok** (`0`): mermi `803` parçacıkla birlikte
kalıyor. Yetimler, iki aşamalı aktarımın mermiyi `46` siteye
kabalaştırmasıyla ortaya çıkıyor.

> Momentum ve kütle **korunuyor** — yetimler sahnede duruyor.
> Kaybolan şey enerjinin **işe dönüşebilirliği**. Gerçekte o sıcak
> madde genleşir ve momentuma dönerdi; burada gelen enerjinin
> **altıda biri** etkileşemez halde donuyor.
>
> Ve bu doğrudan `β`'nın payına ait: genleşemeyen ejekta itmez.

Tanı aracı `scripts/yetim_parcacik.py`, yedi test
(`tests/test_yetim_parcacik.py`) — komşu sayımı `3x3x3` kafeste elle
hesapla kilitlendi (`18` komşu), kutu sınırında komşu kaçırılmıyor,
negatif `u` donmuş enerjiye katılmıyor.

##### Kaynağı: **`h` zamanla güncellenmiyor** (ADR-0042'nin ölçülmemiş sonucu)

`WarpSolid3D` `h`'yi kurulumda bir kez alıyor ve **bir daha
dokunmuyor**; `support = 2h` sabit. Bu bir kaza değil,
[ADR-0042](adr/ADR-0042-h-sabittir-omega-birimdir.md)'nin kilitlediği
bir karar (*"`h` sabittir, dolayısıyla `Ω ≡ 1`"*).

Sonucu şimdi ölçüldü: **genleşen madde bağlantısını kaybediyor.**

| | |
|---|---|
| kabalaştırılmış parçacığın `h`'si | `2 s₂ = 7 m` |
| komşuluk yarıçapı | `2h = 14 m` |
| yetim olan parçacığın en yakın komşusu | `72,9 m` |

Mermi kırıntıları `~km/s` ile ayrışıyor; `14 m`'yi geçtikleri anda
komşusuz kalıyorlar ve iç enerjileri donuyor. Uyarlanabilir `h`
(`h ∝ (m/ρ)^(1/3)`) olsaydı `h` genleşmeyle büyür ve bağlantı
sürerdi — bu, SPH'nin standart davranışı.

> ADR-0042'nin kanıtı (KAYIT-035) **komşu sayısının çalışma
> noktasındaki salınımını** ölçtü; **genleşen** maddede ne olduğunu
> ölçmedi. Karar o kanıtla doğru verilmişti ama kapsamı bu değildi.
>
> Bu ADR-0042'yi **çürütmüyor**: sabit `h`, arayüz hatası ve
> determinizm için seçilmişti ve o gerekçeler duruyor. Çürüttüğü şey,
> kararın **sonuçlarının tamamının ölçüldüğü** varsayımı.

---

### A22 — ~~**Model şok üretmiyor**~~ · **BAŞLIK YANLIŞ** — bkz. A23, A24 (2026-08-21)

> **DÜZELTME (2026-08-29).** Bu bölümün *ölçümleri* doğru ama
> *başlığı* yanlış. Model şok **üretiyor**; A22 aktarımdan **sonraki**
> durumu ölçtü, yani cesedi.
>
> | A22 diyordu | gerçek |
> |---|---|
> | model şok üretmiyor | aşama-1 `%26` sıkışma üretiyor (**A24**) |
> | çare `A1 ≈ 64`, `~55 gün` | şok `λ₂ = 20`'de doğuyor; `470` kat yanlış (**A23**) |
> | ısı ayrıklaştırmadan geliyor | ısı **gerçek**; kaybolan şey **sıkışma** (**A24**) |
>
> Aşağıdaki tablo ve sayılar **silinmedi** (depo kuralı) — o durum
> gerçekten ölçüldü, yalnızca sebebi başka.

A21 *"enerji altı parçacıkta"* diyordu. Bir adım daha sorulunca en dip
katman çıktı: **o parçacıklar sıkışmadan ısınmış.**

Gerçek bir şok maddeyi **sıkıştırarak** ısıtır; Rankine-Hugoniot
sıçrama koşulları ikisini birbirine bağlar. Referans **dışarıdan**
geliyor — modelin kendi önceki koşusundan değil.

Bazalt için `Us = C0 + S·up` (`C0 = 2,6 km/s`, `S = 1,5`; Melosh 1989),
DART hızında (`6 144,9 m/s`, `up ≈ v/4 – v/2`):

| `up` | `Us` | **sıkışma** | `P` | `du` |
|---|---|---|---|---|
| `1 536 m/s` | `4 904` | **`%45,6`** | `20,3 GPa` | `1,18e6 J/kg` |
| `3 072 m/s` | `7 209` | **`%74,3`** | `59,8 GPa` | `4,72e6 J/kg` |

Ölçülen (her parçacığın **kendi** `α₀`'ına göre):

| kol | `A1` | sıkışma medyan | **sıkışma max** | `>%5` sıkışan |
|---|---|---|---|---|
| tek aşama | `0,215` | `%-0,0008` | **`%0,250`** | **`0`** |
| iki aşama `λ₁ = 38` | `4,078` | `%-0,0008` | **`%3,693`** | **`0`** |

> **Hedefte tek bir parçacık bile `%5` sıkışmıyor.** Hugoniot `%46`
> istiyor. Model bandın `%0,5` – `%8`'inde.
>
> En sıcak parçacıklar `u = 1,03e5 J/kg`'a çıkmış ama sıkışmaları
> `%0,4 – 0,5`. **Sıkışmadan ısınma şok değildir** — ısı,
> ayrıklaştırmanın dağıtıcı teriminden geliyor.

#### Bu, geri kalan her şeyi açıklıyor

| belirti | sebebi |
|---|---|
| `β` hedeften beslenmiyor | şok yok -> kazı akışı yok -> ejekta yok |
| krater `9 cm` | kazılacak madde şoklanmadı |
| enerji `6` parçacıkta | şok yayılmadı, temas noktasında dağıldı |
| `%78` iç enerji, `%0,9` kinetik | ısı üretildi ama akışa dönüşmedi |

Dört ayrı sıkıntı değil; **tek** sıkıntının dört yüzü.

#### Yakınsama yönü **var** ve hedefi dışarıdan belli

`A1` `0,215 -> 4,078` (`19×`) ile sıkışma `%0,25 -> %3,69` (`15×`).
Ölçülen ölçekleme: **sıkışma `~ A1^0,92`**.

Hugoniot bandının **alt** ucuna (`%45,6`) ulaşmak için:

| | |
|---|---|
| gereken `A1` | **`≈ 64`** (bugünkü eşik `2`) |
| gereken `λ₁` | `≈ 592` |
| aşama-1 maliyeti | `159 727×` |
| H100'de tek nokta | **`≈ 55 gün`** |

Ara noktalar: `A1 = 8` -> `1 saat` (sıkışma `~%7` beklenir),
`A1 = 20` -> `24 saat` (`~%16`).

> `A1 ≥ 2` eşiği yalnızca *gevşek* değil; **şok üretemeyecek kadar**
> gevşek. Ve şoku üretmek bu mimaride tek nokta için `~55 gün`.
> ADR-0048'in kama önerisi (`36×`) bunu `~1,5 güne` indirir — kararın
> asıl gerekçesi budur.

Ölçüt aracı `scripts/sok_sinavi.py`, on dört test
(`tests/test_sok_sinavi.py`): Hugoniot bağıntıları elden hesapla
kilitli, blok/matris tabanı `α₀` ile **kesin** (koşular artık `α₀`'ı
da kaydediyor), ve tahmin yolunun sınırı (`%30` üstü sıkışmada
yanılır) testle yazılı.

---

### A23 — **Şok `λ₂ = 20`'de doğuyor; A22'nin `55 gün`'ü `470` kat yanlış** (2026-08-28)

A22 iki noktadan `sıkışma ~ A1^0,92` çıkarıp *"Hugoniot için
`A1 ≈ 64`, `~55 gün`"* dedi. O iki nokta **farklı düzeneklerdendi**
(tek aşama `λ = 2` ve iki aşama `λ₁ = 38`). Tek düzenekte, tek
değişkenli tarama koşuldu (ölçüt: `docs/truba/OLCUT-sok-cozunurlugu.md`,
**koşudan önce** kilitli).

Düzenek ucuz çünkü **şok mikro-saniyede kurulur**: `t_end = 1e-3 s`,
`r_ince2 = 3 m`, tek aşama (aktarım denklem dışında).

| `λ₂` | `s` | `r_mermi/h` | **sıkışma max** | `u_max` | yargı |
|---|---|---|---|---|---|
| `2` | `3,500` | `0,053` | `%0,0057` | `2,3e3` | `SOK_YOK` |
| `8` | `0,875` | `0,212` | `%1,683` | `9,0e5` | `SOK_YOK` |
| `20` | `0,350` | `0,531` | `%22,024` | `3,5e6` | `KISMI` |
| **`40`** | `0,175` | **`1,061`** | **`%40,521`** | `5,6e6` | **`KISMI`** |

> `λ₂ = 40`'ta sıkışma Hugoniot alt ucunun (`%45,6`) **`%89`**'u.
> **Model şok üretebiliyor.** Yalnızca `s ≤ 0,175 m` istiyor.

Ve yükseliş **doyuma gidiyor** — fiziksel tavana yaklaşan bir
yakınsamanın imzası:

| geçiş | artış | üs |
|---|---|---|
| `2 -> 8` | `296×` | `4,10` |
| `8 -> 20` | `13,1×` | `2,81` |
| `20 -> 40` | `1,8×` | **`0,88`** |

Doyum noktası `r_mermi/h = 1,06`'da: **mermi bir yumuşatma boyuna
sığdığı anda** sıkışma Hugoniot değerine oturuyor. Artık
**ekstrapolasyona gerek yok** — cevap ölçüldü.

A22'nin yasası `λ₂ = 20` için `%0,047` derdi. Ölçülen `%22,02` —
**`470` kat**. `A1^0,92` **yanlış**.

#### Bu bir sayı artığı değil: **cephe var, hızı da tutuyor**

`λ₂ = 20`, `t = 1e-3 s`, temas noktasına göre (Lagrange'cı):

| sıkışma | parçacık | kütle | temastan uzaklık |
|---|---|---|---|
| `> %1` | `1 306` | `60 865 kg` | `0,67 – 3,41 m` |
| `> %5` | `580` | `27 031 kg` | `0,67 – 2,83 m` |
| `> %10` | `184` | `8 575 kg` | `0,67 – 2,54 m` |
| `> %20` | `2` | `93 kg` | `0,68 m` |

Sıkışma uzaklıkla **düzgün azalıyor** — sönümlenen bir şok cephesinin
tam profili. `λ₂ = 8`'de aynı ölçü **tek** parçacık veriyor: cephe
`h = 1,75 m`'nin içine sığıyor, yani yok.

> **Bağımsız sınav.** Ölçülen tepe sıkışma `%22,02`'yi
> Rankine-Hugoniot'a sokarsak `Us = 3 565 m/s`. Cephe `1e-3 s`'de
> `3,41 m` gitmiş → **`3 410 m/s`**. Sapma **`%4,3`**.
>
> Bu iki sayı birbirine **uydurulmadı**: biri yoğunluktan, öteki
> konumdan geliyor ve aralarındaki bağıntı literatürden. Şok
> **gerçek**.

#### Maliyet: sorun çözünürlük değil, **dağılım**

| seçenek | `N` | H100 / nokta | `40` nokta |
|---|---|---|---|
| A22'nin ima ettiği (`A1 ≈ 64`) | — | **`5 324` gün** | — |
| `λ₂ = 20`'yi `r = 25 m`'ye yaymak | `1 089 581` | `30,6 saat` | `1 225 saat` |
| **üç seviyeli** (`0,35` / `0,875` / `3,5`) | **`33 008`** | **`56 dakika`** | **`37 saat`** |

Üçüncü satır **bugünkü üretim bütçesinin `1,16` katı**. Bugün o bütçe
`25 m`'lik bir küreye `s = 3,5 m` ile harcanıyor — şokun olmadığı
yere. Şok `5 m` içinde ve `s ≤ 0,35 m` istiyor.

> Sıkıntı çözünürlüğün **yetmemesi** değil, **yanlış yere
> konması**. Ve gereken düzenek depoda zaten var:
> `refine_scene_ucseviye` / `asama2_sahnesi_ucseviye`.

#### Kendi ölçütümün kusuru

Kilitlediğim kural *"`20 -> 40` artışı `8 -> 20`'den büyük olmalı"*
diyordu. `8 -> 20` artışı `13,1×`; bunu aşmak `λ₂ = 40`'ta `%288`
sıkışma isterdi — Hugoniot tavanı `%74`. **Kural tek yönde
sınanamazdı ve H1 kendi kuralımla düştü** (`1,8× < 13,1×`).

H1'in *eşik* dediği yerde ölçüm **doyum** gösterdi; ikisi aynı şey
değil ve ben eşik yazmıştım. Ama `r/h ≈ 1`'in özel olduğu — doyumun
tam orada gelmesi — ayakta. Asıl soruya gelince: **H0 çöktü** ve
yerine ekstrapolasyon değil **ölçüm** geçti.

---

### A24 — **Aşama-1 şoku üretiyor; aktarım ısıyı taşıyıp sıkışmayı atıyor** (2026-08-29)

A22 *"model şok üretmiyor"* dedi. **Yanlıştı.** A22 doğumu değil,
**cesedi** ölçmüştü: aktarımdan sonraki `t = 0,2 s`'yi.

#### Uzlaştırma: `1,750e-5` = `1,81e-5`

`λ₂ = 20` (`s = 0,350 m`), `t = 4,767e-3 s` — yani üretim aşama-1'in
(`λ₁ = 19`, `s = 0,368 m`) neredeyse aynısı:

| | |
|---|---|
| sıkışma max | **`%26,08`** |
| şoklanan kütle (`>%1`) | `72 936 kg` |
| **kütle kesri** | **`1,750e-5`** |

Deftere `t₁`'de yazılan (KAYIT-053): *"`ρ`: `%1`'den fazla sapan
`2 181` parçacık, **kütlece `1,81e-5`**"*.

> **Aynı sayı.** Üretim aşama-1 şok **üretiyor** — `%26` sıkışma,
> `73` ton. Ben o kaydı *"şok yok"* diye okumuştum; oysa şokun
> **kendisiydi**.

#### Aktarım sıkışmayı **taşıyamıyor** — kod düzeyinde kesin

| durum değişkeni | aşama-2'ye taşınıyor mu |
|---|---|
| `x`, `v`, `m` | evet |
| `u` (ısı) | evet (`sahne.e`) |
| `D` (hasar) | evet (bu turda eklendi) |
| **`ρ` (sıkışma)** | **hayır** |

`solver_solid.py:139` `ρ`'yu **her zaman** `ρ₀/α₀` ile kuruyor ve
`_cozucu`'nun `rho` parametresi **yok**
(`faz48_iki_asama.py:218`, `:531`). Yani aktarım sıkışmayı
kaybetmiyor — **kurulumda siliyor**. Ölçüme gerek yok, imzada yazılı.

#### Bu, A22'nin belirtisinin **tam kendisi**

Aşama-2, **sıcak ama sıkışmamış** maddeyle başlıyor. Şoklanmış madde
için bu fiziksel olarak **olanaksız** bir durum. A22 aynen bunu
ölçmüştü:

> *"En sıcak parçacıklar `u = 1,03e5 J/kg`'a çıkmış ama sıkışmaları
> `%0,4 – 0,5`."*

O bir ayrıklaştırma artığı değil, **aktarımın parmak izi**.

#### Zincir, baştan sona

| adım | ne oluyor |
|---|---|
| aşama-1 | gerçek şok: `%26` sıkışma **+** ısı, `73 t` |
| **aktarım** | ısı geçer, **sıkışma sıfırlanır** |
| aşama-2 | sıcak-ama-sıkışmamış madde; genleşir, kazmaz |
| `t = 0,2 s` | sıkışma `%0,25`, krater `9 cm`, `β` hedeften beslenmez |

#### **ÖLÇÜLDÜ: çare işliyor** (TRUBA `J3`, 2026-08-30)

İki aşamalı koşu, `λ₁ = 19`, `λ₂ = 8`, `t_end = 6e-3 s`, tek değişken:

| kol | `t₁` | `t_end` | yargı |
|---|---|---|---|
| **A** — `ρ` taşınıyor | `%27,593` | **`%10,435`** | `KISMI` |
| **B** — `--rho-tasima-yok` | `%27,593` | **`%0,219`** | **`SOK_YOK`** |

`t₁` değerleri **bit düzeyinde aynı** — yani tarama gerçekten tek
değişkenli. `t_end`'de fark **`47,6` kat**.

Ve `B` kolu, bu turda yazdığım uyarıyı kendiliğinden bastı:

> `UYARI: sok t1'de VARDI, t_end'de YOK -- aktarim ya da asama-2
> cozunurlugu onu yutuyor (rapor A24).`

Kalan `%10,4 < %27,6`: sıkışma hâlâ **sönüyor**, çünkü aşama-2
`λ₂ = 8` (`s = 0,875 m`) ve A23'e göre o çözünürlük `%1,68`'den
fazlasını taşıyamaz. Aktarım artık **silmiyor**; aşama-2'nin
çözünürlüğü **eritiyor**. İkisi ayrı sıkıntı ve ayrı çareleri var.

#### İkinci sınır: şok `3,4 m`'de duruyor

`t = 1e-3 -> 4,767e-3 s` (`4,8×` süre) cephe `3,41 m`'de **kalıyor**;
`3 400 m/s` ile `16 m` gitmeliydi. İnce bölge `r_ince = 3 m`.
Şoklanan hacim `82 m³`; en küçük literatür krateri (`D = 13,3 m`)
bile `~6,5 m` yarıçap ister — **`2` kat büyük**.

Yani iki ayrı sınır var: **(a)** aktarım sıkışmayı siliyor,
**(b)** ince bölge şokun taşınabileceği yeri sınırlıyor. `(b)`'nin
inceltmeden mi yoksa doğal sönümden mi geldiği `r_ince = 12 m` kolu
ile sınanıyor (ölçüt yazılı).

---

### A25 — **Şok, inceltmenin kendi ördüğü duvara çarpıyor**: arayüz oranı `8 000` (2026-08-29)

A24 cephenin `3,41 m`'de durduğunu buldu. **Neden** durduğu ölçüldü.

`λ₂ = 20`, `r_ince = 3 m`, `t = 4,767e-3 s`, çarpma noktasından
kabuk kabuk parçacık kütlesi:

| kabuk | `n` | kütle medyan |
|---|---|---|
| `0 – 3,0 m` | `1 420` | `46,6 kg` |
| `3,0 – 3,5 m` | `409` | `46,6 kg` (ve bir tane `372 834`) |
| **`3,5 – 4,0 m`** | `1` | **`372 834 kg`** |

> **Arayüz oranı `8 000`.** Şok, kendisinden `8 000` kat ağır bir
> duvara çarpıyor ve geçemiyor.

Bu, KAYIT-053'ün *"mermi hedefe giremiyor"* dediği `μ = 80`'in
**`100` katı**. Aynı patoloji, aynı büyüklük — bu kez duvar
**ayrıklaştırmanın kendi ürünü**.

#### Ve inceltme arttıkça **kötüleşiyor**

| `λ` | ince kütle | en dik basamak | aralık sıçraması | yargı |
|---|---|---|---|---|
| `2` | `46 604 kg` | `8` | `2,0×` | OLAĞAN |
| `8` | `728 kg` | `512` | `8,0×` | TEHLİKELİ |
| `20` | `46,6 kg` | **`8 000`** | `20,0×` | TEHLİKELİ |
| `40` | `5,8 kg` | **`64 000`** | `40,0×` | TEHLİKELİ |

> Şoku **doğurmak** için inceltiyoruz; aynı inceltme şoku
> **hapsedecek duvarı** örüyor. `λ = 2` bu ölçüde *"olağan"* çıkıyor
> — çünkü orada taşınacak şok zaten yok.

Kütle `s³` ile gittiği için `8 000` kat = **`20` kat aralık**
sıçraması, hem de **tek** basamakta. AMR uygulamasında olağan
basamak `2` katı (kütlede `8`).

#### Gereken kademe **sayıyla** belli

`8^k ≥ oran` en küçük `k`, eksi bir:

| `λ` | oran | **gereken ara seviye** |
|---|---|---|
| `8` | `512` | `2` |
| `20` | `8 000` | **`4`** |
| `40` | `64 000` | **`5`** |

Bugünkü şema **tek** basamak kullanıyor. Üç seviyeli yol (`refine_scene_ucseviye`)
bir ara seviye ekliyor — `λ₂ = 20` için gereken **dördün biri**.

#### İkinci açıklama sınandı ve **düştü**

*"Belki arayüzde komşu çölü vardır"* — kaba parçacıklar `7 m`
aralıklı, ince bölge `3 m`'de bitiyor; sınırdaki ince parçacıkların
`2h = 1,4 m` içinde dışa doğru komşusu olmayabilirdi (A21'in yetim
parçacıklarıyla aynı kusur). Ölçüldü:

| kabuk | `n` | komşu ortalama | komşu min | `<30` komşulu |
|---|---|---|---|---|
| `2,8 – 3,0 m` | `267` | `202,5` | `93` | `%0,0` |
| `3,0 – 3,2 m` | `278` | `177,3` | `96` | `%0,0` |

Ve en dıştaki ince parçacık `3,41 m`, en yakın kaba parçacık
`3,43 m` — **boşluk `0,02 m`**, destek yarıçapının (`1,40 m`)
yetmiş'te biri.

> **Komşu çölü yok.** Sınırdaki parçacıkların bol komşusu var; onlar
> yalnızca **çok ağır**. Açıklama kütle oranında kalıyor.

#### Ve örtüşme **tam**

| | |
|---|---|
| cephe konumu | `3,41 m` |
| ince bölgenin dış ucu | `3,41 m` |

Sönen bir şok cephesi değil: **şok ince bölgeyi doldurup durmuş.**
Ölçtüğüm *"cephe"*, fiziğin değil **ızgaranın** sınırı.

#### Şok **engellenmiyor** — yavaş bir itmeye dönüşüyor

Momentum arayüzü **geçiyor**, ama şok olarak değil:

| bölge | `n` | hız medyan | `u` medyan |
|---|---|---|---|
| ince `2,8 – 3,41 m` | `675` | **`25,3 m/s`** | `1 755` |
| kaba `3,43 – 6 m` | `2` | `1,56 m/s` | `-68` |
| kaba `6 – 12 m` | `10` | `0,27 m/s` | `36` |
| kaba `12 – 25 m` | `100` | `0,019 m/s` | `0,001` |

Arayüzde hız **`15` kat** düşüyor. Ve gereken hız `1,56` değil:

| | |
|---|---|
| şoklanan bölgenin **toplam** momentumu | `2 246 474 kg m/s` |
| `%22` sıkışma için gereken `up` | `643 m/s` |
| **tek** kaba parçacığı `up`'a çıkarmak | `239 864 135 kg m/s` |
| **oran** | **`107` kat eksik** |

> Şoklanan `73` tonun **tamamının** momentumu, **tek bir** kaba
> parçacığı şok hızına çıkarmaya yetmiyor. Bu yüzden şok
> engellenmiyor — `1,56 m/s`'lik **yavaş bir itmeye** dönüşüyor ve
> şok olmaktan çıkıyor.

Ayrım önemli: *"engelleniyor"* deseydik çare bir sınır koşulu
olurdu. Ölçülen şey başka — **momentum yeterli değil**, çünkü alıcı
parçacık çok ağır. Çare kütle basamağını küçültmek.

#### Bu, üç bulguyu tek sebebe bağlıyor

| bulgu | bu ışıkta |
|---|---|
| `μ = 80` (KAYIT-053) | aynı kusurun **mermi** ucundaki hâli |
| cephe `0,0 m/s` (A24) | aynı kusurun **arayüz** ucundaki hâli |
| şoklanan hacim `82 m³` | duvarın içinde kalan hacmin ta kendisi |

#### Kütle parmak izi: **hiçbir kaba parçacık şoklanmamış**

Bağımsız bir teşhis (kullanıcı, 2026-08-29) daha keskin bir sınav
önerdi ve doğrulandı — **her iki zamanda da**:

| `t` | şoklanan | **ince** | **kaba** | `n × 46,6043 kg` | ölçülen |
|---|---|---|---|---|---|
| `1e-3` | `1 306` | `1 306` | **`0`** | `60 865,2` | `60 865,2` |
| `4,767e-3` | `1 565` | `1 565` | **`0`** | `72 935,7` | `72 935,7` |

Şoklanan kütle, ince parçacık kütlesinin **tam katı**. Yani `>%1`
sıkışan parçacıkların **tamamı ince**; kaba bölgeye şok **hiç
girmemiş**.

> Bu, benim *"cephe `3,41 m`'de duruyor"* ifademi düzeltiyor.
> `3,41 m` bir şok cephesi **değil** — başlangıçta `r < 3 m`'de olan
> ince parçacıkların dışarı taşınmış **kenarı**. Kaba bölgede
> ölçülecek bir cephe hiç oluşmadı.

#### Ve `h_ij` mekanizması

SPH eşleşmesi `h_ij = (h_i + h_j)/2` kullanıyor. Arayüzde:

| | |
|---|---|
| `h` ince (`s = 0,35`) | `0,70 m` |
| `h` kaba (`s = 7,0`) | `14,00 m` |
| **`h_ij`** | **`7,35 m`** |
| **destek `2h_ij`** | **`14,70 m`** |

Şoklanan bölgenin **yarıçapı** `3,41 m`. Yani etkileşim desteği,
şokun tamamından **`4,3` kat geniş**. Aynı `h_ij` yapay viskozitede
de kullanılıyor (`solid_stress.py`), dolayısıyla dar şok darbesi
`14,7 m`'lik bir hacme yayılıp **sayısal olarak siliniyor**.

İki mekanizma birbirini tamamlıyor: alıcı parçacık `8 000` kat
**ağır** (momentum `107` kat yetmiyor) **ve** etkileşim şoktan `4,3`
kat **geniş** bir desteğe yayılıyor.

#### Uyarı: `λ`'yı tek başına artırmak **kötüleştirir**

Kütle duvarı `λ³` ile büyüyor. Keskin sınır korunarak `λ` artırılırsa:

| `λ` | duvar |
|---|---|
| `8` | `512` |
| `20` | `8 000` |
| `40` | `64 000` |

Çözünürlüğü artırmak, aynı maskeyle, **duvarı `λ³` oranında
yükseltir**.

#### A24 bu kilidin sebebi **değil**

Yoğunluk aktarımı kusuru (A24) gerçek ve ayrı bir kusur. Ama
buradaki koşu **tek aşamalı** — aktarım hiç yok. `3,4 m` kilidinin
sebebi yalnızca **arayüz**.

#### Çare kuruldu ve **ölçüldü**: `%13` parçacığa `1 000` kat iyileşme

`refine_scene_kademeli` — `(r, λ)` çiftleri **dıştan içe**, her adım
bir öncekinin çekirdeğini oyup daha ince kafesle dolduruyor.

Aynı sahne, aynı en ince aralık (`s = 0,175 m`), `r_iç = 3 m`:

| şema | `N` | **en dik basamak** | `h` | yargı |
|---|---|---|---|---|
| tek basamak | `90 950` | **`8 000×`** | `0,35 – 7,0` | TEHLİKELİ |
| **merdiven** (`20,10,5,2.5,1.25`) | `102 367` | **`8×`** | `0,35 – 7,0` | **OLAĞAN** |

Basamaklar: `8,0× -> 8,0× -> 8,0×` (kalan `1,2 – 4,8×` oranları
inceltme değil, **blok/matris** yoğunluk farkı).

> Arayüz oranı **`1 000` kat** iyileşiyor; bedeli **`%13`** parçacık.
> Ve `h_min` değişmediği için **`dt` aynı** — yani maliyet gerçekten
> yalnızca `%13`.

Sıra doğrulaması zorunlu: yarıçaplar dıştan içe **azalmalı**, `λ`
**artmalı**. Ters sıra sessizce daha kötü bir sahne üretirdi; ikisi
de `ValueError`.

#### **ÖLÇÜLDÜ: çare işliyor** (2026-08-29)

Merdiven koşuldu (`24:2.5`'e gerek kalmadan,
`12:1.25 8:2.5 6:5 4.5:10 3:20`, `t = 4,767e-3 s`, `N = 96 483`):

| ölçü | tek basamak | **merdiven** |
|---|---|---|
| şoklanan **seviye** sayısı | **`1`** | **`3`** |
| kaba seviyelerde şoklu parçacık | **`0`** | **`2 983`** |
| şoklanan kütle | `72 936 kg` | **`240 905 kg`** |
| sıkışma max | `%26,08` | **`%45,18`** |
| cephe | `3,41 m` (= ızgara sınırı) | **`5,41 m`** |

Seviye dağılımı — A25'in kütle parmak izi ölçüsü, artık **geçiyor**:

| seviye | şoklu / toplam | oran |
|---|---|---|
| `5,8 kg` (`s = 0,175`) | `14 129 / 14 233` | `%99,3` |
| `46,5 kg` (`s = 0,350`) | `2 922 / 4 134` | `%70,7` |
| `372,3 kg` (`s = 0,700`) | `61 / 1 039` | `%5,9` |

> Şok **iki arayüzü geçti** ve üçüncüsüne giriyor. Tek basamaklı
> şemada üç ölçümde de kaba seviyede **sıfır** parçacık şoklanmıştı.

Ve sıkışma `%45,18`: Hugoniot bandının alt ucu **`%45,6`**. Model
şoku artık **doğru değerde** üretiyor *ve* ızgarada taşıyor.
(Yargı hâlâ `KISMI` — bandın `%99,1`'inde, kıl payı altında.)

Kalan `%13` parçacık maliyetiyle: şoklanan kütle `3,3` kat,
sıkışma `1,7` kat.

#### Asıl sınır kütle oranı **değil**: **kabuk kalınlığı**

Bir kaba parçacığın şoku alabilmesi için desteğinde yeterli ince
madde bulunmalı. Destekteki ince parçacık sayısı `(2h_kaba)³`, gereken
kütle de `s_kaba³` ile gittiği için **pay basamak boyutundan
bağımsız** — her basamakta `189,6×`:

| basamak | destekteki ince | gereken | pay |
|---|---|---|---|
| `8×` | `1 517` | `8` | `189,6×` |
| `8 000×` | `1 516 733` | `8 000` | `189,6×` |

Yani kütle oranı **tek başına** hiçbir basamağı düşürmez. Düşüren
şey **geometri**: destek yarıçapı `2h_kaba = 4 s_kaba`, ve o kadar
ince madde **var olmalı**.

| | |
|---|---|
| tek basamakta kaba desteği | `4 × 7,0 = 28 m` |
| ince bölge | `3 m` |
| **oran** | **`9` kat büyük -> düşer** |

Destekte `1,5` milyon ince parçacık gerekiyordu; ince bölgede
**`1 828`** var.

> **Ölçüt:** her seviyenin kabuğu en az `~4 s` kalın olmalı. Kütle
> oranı bunun bir **vekili**; asıl koşul bu.

Bu, koşmakta olduğum merdivenin bir kusurunu **koşu sırasında**
ortaya çıkardı:

| kabuk | `s` | kalınlık | `kalınlık/s` | |
|---|---|---|---|---|
| `0 – 3` | `0,175` | `3,0 m` | `17,1` | geçer |
| `3 – 4,5` | `0,350` | `1,5 m` | `4,3` | geçer |
| `4,5 – 6` | `0,700` | `1,5 m` | **`2,1`** | **çok ince** |
| `6 – 8` | `1,400` | `2,0 m` | **`1,4`** | **çok ince** |
| `8 – 12` | `2,800` | `4,0 m` | **`1,4`** | **çok ince** |

Öz-benzer merdivende (`r` ve `s` **birlikte** katlanır) bu
kendiliğinden çözülüyor: `kalınlık/s = r/s` sabit.

| kabuk | `s` | kalınlık | `kalınlık/s` |
|---|---|---|---|
| `0 – 3` | `0,175` | `3,0` | `17,1` |
| `3 – 6` | `0,350` | `3,0` | `8,6` |
| `6 – 12` | `0,700` | `6,0` | `8,6` |
| `12 – 24` | `1,400` | `12,0` | `8,6` |

Yani `ozbenzer_kademeler` yalnızca zarif değil — **gerekli**.

#### Merdiven yetmezse: **yedek çare** `h_ij`'nin kendisi

`solid_stress.py:178` `hij = 0,5 (h_i + h_j)` kullanıyor ve bu
**hem** çekirdek gradyanına **hem** yapay viskoziteye giriyor.
Arayüzde ikisi birden `7,35 m`'ye şişiyor: etkileşim `14,7 m`'ye
yayılıyor **ve** AV'nin dağıtımı aynı oranda büyüyor.

Merdiven bu oranı `8×`'e indirerek sorunu **dolaylı** çözüyor
(`h_ij` `0,5(2s + 4s) = 3s`, yani ince `h`'nin `1,5` katı — kabul
edilebilir). Doğrudan çare ise değişken-`h` SPH'nin standart yolu:

| yaklaşım | çekirdek | durum |
|---|---|---|
| bugün (ADR-0041) | `W(r, (h_i+h_j)/2)` | çok çözünürlükte **şişiyor** |
| simetrikleştirilmiş | `½[∇W(r,h_i) + ∇W(r,h_j)]` | her parçacık **kendi** `h`'siyle |

İkincisi korunumu bozmuyor (Hernquist & Katz 1989) ve tam olarak
değişken çözünürlük için tasarlanmış. Ama çekirdeğin kendisine
dokunuyor — ADR-0041'in *"tüm `h` eşitken tam olarak `h` verir, bit
uyumu korunur"* güvencesini yeniden kurmak gerekir.

**Sıra:** önce merdiven ölçülür. Yetiyorsa çekirdeğe dokunulmaz.

Ölçüt aracı `scripts/arayuz_orani.py`, dokuz test: kayan nokta
gürültüsü seviye sayılmıyor (A11'de sayılmıştı), eşikler ayrı,
kademe önerisi elden hesapla kilitli, ve *"inceltme arttıkça
kötüleşiyor"* monotonluğu testte yazılı.

---

### A26 — **`--kademeler` iki betikte farklı şey demek**: TRUBA `J4` iki kat kaba koştu (2026-08-30)

Merdiven `(r, λ)` çiftleriyle veriliyordu ve `λ` **tabana bağlı**:

| betik | taban `spacing` | `"3:20"` ne demek |
|---|---|---|
| `kademe_sinavi.py` | `3,5` (gömülü) | `s = 0,175 m` |
| `faz48_iki_asama.py` | `7,0` (varsayılan) | **`s = 0,350 m`** |

TRUBA `J4` `faz48` ile koştu. Sonuç:

| | beklenen | **ölçülen** |
|---|---|---|
| `N` | `131 057` | **`17 201`** |
| `s_min` | `0,175 m` | `0,350 m` |
| `β` | — | `1,216` |

> Koşu **iki kat kaba** gitti ve **hiçbir şey hata vermedi**. Sayı
> sessizce yanlıştı; `β = 1,216` üretimin `1,411`'inin bile altında.

Aynı sınıf: A14 (bayrağın varsayılanı sessizce kaydırması), A20
(adım sınırının koşuyu sessizce kesmesi). Ortak yanı: **çıkış kodu
sıfır**.

#### Çare: `λ` değil **metre**

`--kademeler 48:2.8 24:1.4 12:0.7 6:0.35 3:0.175` — ikisi de metre.
`kademe_ayristir(ciftler, spacing)` tek yerde çeviriyor ve
tabandan **büyük** bir aralığı reddediyor (o da sessizce sahneyi
bozardı).

Dört test: taban `3,5 / 7,0 / 14,0` için **aynı** aralık;
tabandan büyük reddediliyor; bozuk biçim reddediliyor; **her iki
betiğin de** ayrıştırıcıyı kullandığı kilitli.

#### `J1` bundan etkilenmedi

`kademe_sinavi.py` kendi tabanını (`3,5`) kullandığı için `J1`'in
merdivenleri **istendiği gibi** kuruldu (`N = 104 – 126 bin`,
`s_min = 0,175`). `J1`'in sonucu geçerli — ama başka bir sebeple
eksik (§A27).

---

### A27 — **Şok tüpü düzeneği geçersiz**: denetim kolu kendi kuralımla düştü (2026-08-30)

A25'in sorusunu sahnesiz sormak için düzlemsel bir şok tüpü kuruldu
(`arayuz_sok_tupu.py`). Ölçüt, **koşudan önce**, şunu yazmıştı:

> `κ = 1` **denetim**: aynı çözünürlük, şok `x > 0`'a ulaşmalı.
> Ulaşmazsa düzenek geçersizdir ve öteki kollar **okunmaz**.

TRUBA `J2` (`400` ve `1 200` adım):

| `κ` | kütle oranı | `N` | ince sıkışma | kaba şoklu |
|---|---|---|---|---|
| **`1`** | `1×` | `864` | **`%0,294`** | `0` |
| `2` | `8×` | `2 160` | `%-0,144` | `0` |
| `4` | `64×` | `7 344` | `%0,128` | `0` |
| `8` | `512×` | `28 080` | `%0,122` | `0` |
| `20` | `8 000×` | `173 232` | `%0,406` | `4` |

**Denetim kolunda bile şok yok** (`%0,294`, Hugoniot `%45,6`).
Düzenek geçersiz; tablodaki hiçbir satır okunmaz.

#### Sebep: **yanal boşalma**

Tüpün enine boyutu `6 s_kaba`; `κ = 1` için `1,05 m`. Şokun kat
etmesi gereken yol `2,1 m`. Serbest yan yüzeylerden gelen boşalma
dalgaları eksene, şok ucundan **önce** varıyor ve sıkışmayı
öldürüyor. SPH'de periyodik sınır olmadığı için çare tüpü **çok**
genişletmek — ki o zaman ucuzluk avantajı gider.

#### `κ = 20`'nin `4` parçacığı **yanlış pozitif**

Kısa koşuda `κ = 20` *"GEÇTİ"* dedi (`4` parçacık); uzun koşuda
`0`. Denetim kolu geçersiz olduğu için o satır zaten okunmuyordu —
**kural, kendi yazdığım yanlış pozitifi engelledi.**

#### Ne yapıldı

Araç ve `8` testi **duruyor** (depo kuralı: hiçbir satır silinmez),
ama bu belgeyle *"geçerli düzenek değil"* damgası taşıyor. A25'in
kanıtı **küresel sahne** ölçümünden geliyor ve o ölçüm geçerli.

---

### A28 — **Elemeler ilk kez şok varken ölçüldü**; beşi etkisiz, gözeneklilik şoku çökertiyor (2026-08-31)

ADR-0049 *"hiçbir eleme, aynı koşuda şok sınavı geçmedikçe geçerli
değil"* diyordu. TRUBA `J5` ilk kez o koşulu sağladı — **ama iki kat
kaba merdivenle** (A26), yani `s_min = 0,350` yerine `0,175`.
Sonuçlar geçici; düzeltilmiş koşu kuyrukta.

| kol | sıkışma max | yargı | `β` |
|---|---|---|---|
| taban | `%28,615` | `KISMI` | `1,000000` |
| hasarlı | `%28,616` | `KISMI` | `1,000000` |
| yerçekimli | `%28,615` | `KISMI` | `1,000000` |
| zayıf blok (`Y0 = 1 Pa`) | `%28,615` | `KISMI` | `1,000000` |
| zayıf matris (`Y0 = 1 Pa`) | `%28,615` | `KISMI` | `1,000000` |
| **gözeneksiz** | **`%0,518`** | **`SOK_YOK`** | `1,000000` |

#### Beş kolun aynı çıkması bir **eleme değil, doğrulama**

Mukavemeti dört mertebe düşürmek (`10 MPa -> 1 Pa`) sıkışmayı
beşinci ondalıkta bile oynatmıyor. Beklenen:

| | |
|---|---|
| şok basıncı (`up = v/4`) | `20,3 GPa` |
| matris `Y0` | `10 MPa` |
| **oran** | **`2 034` kat** |

Mukavemetin şok evresinde etkisiz olması **fiziğin gereği**.
`Y0` geç evrede (kazı akışı) belirleyicidir ve `t = 6e-3 s` orayı
görmüyor.

> Yani bu koşu *"`Y0` `β`'yı etkilemiyor"* **demiyor**. Yalnızca
> *"`Y0` şoku etkilemiyor"* diyor — ki zaten öyle olmalıydı.
> ADR-0049'un istediği eleme hâlâ **yapılmadı**: `t_end = 0,2 s`
> gerekiyor (`K4`).

Bu ayrımı yazmak önemli, çünkü bu depo **dört kez** bir sonucu
kapsamının dışında okudu.

#### Gözeneksiz kolun çökmesi: **açıklanmadı**

`%28,6 -> %0,518`. Olası sebep: `α₀ = 1` ile parçacık kütlesi
`1,7564` kat büyüyor, mermi/hedef kütle oranı o oranda kötüleşiyor
ve iki kat kaba merdivenle birleşince eşiğin altına düşüyor.

**Ama bu bir tahmin.** Düzeltilmiş koşu (`s_min = 0,175`) bunu
ayıracak. Eğer orada da çökerse sebep çözünürlük değil,
gözenekliliğin şok yakalamadaki rolüdür — ve bu, `P-α`'nın bu
modelde ne yaptığına dair ayrı bir soru açar.

---

### A29 — **Momentum defteri kuruldu**: eski `β`'nın `%100`'ü mermi geri tepmesiymiş (2026-08-31)

Bir dış geri bildirim şunu istedi: *"`β`'yı provenance ile ayır ve
momentum defterini kapat; kapanmıyorsa `β` raporlama."* Defter kuruldu
ve **makine hassasiyetinde kapandı** (`artık/p = 1,15e-14`).

`p_mermi = 3 560 355 kg m/s`, `t = 0,2 s`:

| | **kıyas** (tek basamak) | **merdiven** |
|---|---|---|
| `P_bağlı_hedef` | `4 909 756` | `3 863 797` |
| `P_kaçan_hedef` | **`0,0`** | **`-117 854`** |
| `P_bağlı_mermi` | `0,0` | `-21,8` |
| `P_kaçan_mermi` | `-1 349 401` | `-185 566` |
| **artık** | `1,15e-14` | `1,15e-14` |
| **`β_hedef`** (gerçek) | **`1,000000`** | **`1,033102`** |
| **`β_mermi`** (geri tepme) | **`0,379007`** | `0,052120` |
| kaçan mermi kütlesi | **`579,4 kg`** = merminin **tamamı** | `233,8 kg` |
| kaçan hedef kütlesi | **`0,0 kg`** | **`93,2 kg`** |

#### Önceki `β` **başka bir şeyi** ölçüyormuş

`β = 1,379`'un hedef katkısı **tam sıfır**. `803` parçacık kaçıyor ve
kütleleri toplamı `579,4 kg` — yani **merminin kendisi**, olduğu gibi
sekiyor.

> **Doğru ifade:** önceki `β` tahmini hedef-ejekta momentumunu değil,
> **baskın olarak mermi geri tepme momentumunu** ölçüyordu.
> *"Sahteydi"* demek savunması zayıf bir cümle; ölçülen şey gerçekti,
> yalnızca **başka bir büyüklüktü**.

Bu daha önce *"β hedeften beslenmiyor"* diye tahmin edilmişti; artık
**kapanan bir defterle** ayrıştırılmış durumda.

> Ve `β` **defterden türetiliyor**, ayrıca hesaplanmıyor. Defter
> kapanmazsa `defter_satiri` *"`β` RAPORLANMAZ"* basıyor.

#### Merdivenin iki gerçek kazanımı

| | |
|---|---|
| **hedef ejektası ilk kez sıfırdan farklı** | `β_hedef = 1,0331`; `93,2 kg` hedef maddesi kaçıyor |
| **mermi gömülüyor** | geri tepme `0,379 -> 0,052` (**`7,3` kat**); kaçan mermi kütlesi `579,4 -> 233,8 kg` |

#### Kalan açık — ve büyüklüğü belli

| | |
|---|---|
| ölçülen `P_kaçan_hedef` | `117 854 kg m/s` |
| `β = 3,2225` için gereken | `7 912 889 kg m/s` |
| **oran** | **`67` kat** |

Yani hedef ejekta momentumu `67` kat büyümeli. Kütle olarak: `93,2 kg`
-> `~10⁶ kg` mertebesi (ejekta hızına bağlı).

#### Bu, ölçütü de değiştiriyor

Bundan sonra `β` tek sayı olarak raporlanmaz. Her koşu **defteri**
taşır ve `β_hedef` ile `β_mermi` **ayrı** yazılır. `β_mermi` bir
sonuç değil, bir **tanı**: büyükse mermi hedefe bağlanamamış demektir.

---

### A30 — **Hedef ejektası gürültü tabanında**: `16` parçacık, ve hiçbir parametre onu oynatmıyor (2026-09-01)

`K6`: altı kol, `t_end = 0,2 s`, merdiven, tek değişken. Defter her
kolda `~1e-14` ile kapandı.

| kol | `β_hedef` | `β_mermi` | kaçan hedef | `n` |
|---|---|---|---|---|
| güçlü matris (`Y0 = 1e8`) | `1,033146` | `0,055805` | **`262,1 kg`** | `45` |
| hasarlı | `1,033097` | `0,052155` | `93,2 kg` | `16` |
| **taban** | `1,033102` | `0,052120` | `93,2 kg` | `16` |
| yerçekimli | `1,033102` | `0,052120` | `93,2 kg` | `16` |
| zayıf blok (`1 Pa`) | `1,033116` | `0,052225` | `93,2 kg` | `16` |
| zayıf matris (`1 Pa`) | `1,033098` | `0,052122` | `93,2 kg` | `16` |

#### Duyarlılık **yok**

`Y0`'ı **sekiz mertebe** değiştirmek (`1 Pa -> 1e8 Pa`) `β_hedef`'i
`5e-5` oynatıyor. Sinyalin kendisi `0,0331`; yani değişim sinyalin
**`%0,15`**'i. Hasar, yerçekimi ve blok mukavemeti daha da az.

#### Ve **sebebi** duyarlılık değil, **ölçülemezlik**

| | |
|---|---|
| kaçan hedef kütlesi | `93,2 kg` |
| kaçan parçacık | `16` |
| **`93,2 / 16`** | **`5,83 kg`** = en ince parçacık kütlesi |

> Ejekta **tam olarak `16` parçacık**. Bu bir fizik sayısı değil,
> bir **ayrıklaştırma sayısı**. `16` parçacıkla ejekta kütlesi
> ölçülemez; bir parçacık eksik ya da fazla `%6` oynatır.

Yani *"parametreler `β`'yı etkilemiyor"* demek **yanlış** olur.
Doğrusu: **`β_hedef` bu çözünürlükte ölçülebilir bir gözlenebilir
değil.** Beş kolda bit düzeyinde aynı çıkması da bunun kanıtı —
aynı `16` parçacık kaçıyor.

#### Tek anlamlı fark: **güçlü matris**

`Y0 = 1e8` kolu `262,1 kg` (`45` parçacık) veriyor — `2,8` kat.
Yönü **fiziksel olarak doğru**: daha mukavim hedef enerjiyi plastik
işe yutmuyor, daha çok madde fırlatıyor. Ama `45` parçacık da
gürültü tabanının hemen üstünde.

#### Gözlenebilir niteleme kuralı (yeni)

| gözlenebilir | durum |
|---|---|
| `β_mermi` | ölçülüyor ama **fizik değil** — tanı |
| `β_hedef` | **`< 50` parçacık** -> ölçülemez |
| krater derinliği | `1,03 m`, ölçülüyor |
| krater çapı | A11'den beri iki nicemleme seviyesi — **diskalifiye** |
| ejekta kütle kesri | `6,26e-8`, kollar arası **bit düzeyinde aynı** -> ölçülemez |

> **Mühendislik güvenlik kapısı:** ejekta gözlenebilirleri
> `n_kaçan ≥ 50` olmadıkça çıkarıma girmez.

Ama bu **nihai bilimsel ölçüt değil**. `51` parçacığa çıkmak tek
başına hiçbir şey kanıtlamaz. Gerçek ölçüt **yakınsama**:

| gereken | |
|---|---|
| `β_hedef` | `N` iki katına çıkınca değişmiyor mu |
| kaçan hedef kütlesi | aynı |
| ejekta hız dağılımı | aynı |

Yani `~50`, `~100`, `~500` kaçan parçacıkta **aynı fiziksel sonuç**
çıkmalı. `n ≥ 50` yalnızca *"ölçmeye başlanabilir"* eşiği; yakınsama
*"ölçüm geçerli"* ölçütü. İkisi karıştırılırsa bu depo yine
gürültüyü sonuç sanar.

---

### A31 — **Paralel ensemble görevleri aynı noktaları koştu**: `6` kat israf (2026-09-01)

`K5` altı görevle koştu ve `30` satır yazdı — ama yalnızca **`5`
benzersiz nokta**. Her görev `i = 0 … 4`'ü **yeniden** koştu.

`ensemble_kos` tamamlananları **başlangıçta bir kez** okuyor; altı
görev aynı anda başlayıp **boş** dosya gördü ve hepsi `i = 0`'dan
başladı. Kaldığı yerden devam tasarımı **sıralı** kesinti için
doğru, **eşzamanlı** görevler için değil.

| | |
|---|---|
| harcanan | `6 × 5 × 3,6 saat` = **`108` GPU-saat** |
| elde edilen | `5` nokta (`18` GPU-saatlik iş) |
| israf | **`%83`** |

Çare seçenekleri: (a) her göreve **ayrık** nokta aralığı ver
(`--dilim i/n`), (b) dosya kilidi, (c) her adımda yeniden oku.
En basit ve en sağlamı **(a)**: paylaşım yerine **bölüşüm**.

---

### A32 — **`pytest | tail` düşen testi yuttu**: aynı kusurun araç sürümü (2026-09-01)

Bir test düşük kaldı ve **yine de push edildi**. Sebep bir boru hattı:

```
pytest ... | tail -2 && git commit && git push
```

`pipefail` olmadan bir boru hattının çıkış kodu **son** komutundan
gelir. `pytest` düştü (`1`), `tail` başarılı oldu (`0`) — dışarıya
`0` çıktı ve zincir devam etti.

#### Bu, deponun **kendi** kusur sınıfının araç sürümü

| | |
|---|---|
| fizik sürümü | `β = 1,4112` — hedef ejektası değil, **mermi geri tepmesi** ölçülüyordu |
| araç sürümü | `pytest \| tail` — test düştü, **çıkış kodu `0`** |

İkisinde de aynı: **program "başarılı" diyor, ölçüm başka bir şeyi
temsil ediyor.** Ve çözüm de aynı: başarı bayrağına değil,
**başarının nasıl üretildiğine** güvenmek.

#### Çare: kural + test

Bütün kabuk/SLURM betiklerinde `set -euo pipefail`.
`tests/test_kabuk_pipefail.py` bunu her koşuda denetliyor —
ve **yazıldığı anda beş betikte eksik olduğunu buldu**.

Düşen testin eşiği de uydurmaydı (`> 30`); gerçek oran `26,0` ve
artık ölçülen değere kilitli.

---

### A33 — **Testim geçti, kusur duruyordu**: varlık sınandı, yokluk sınanmadı (2026-09-03)

`L1` ensemble'ı TRUBA'da `~15` saat koştu, veriyi yazdı ve **özet
satırında** çöktü:

```
AttributeError: 'EnsembleDurum' object has no attribute 'n_tamam'
```

Bu kusur *"düzeltilmişti"* ve **testi vardı**. Test şöyleydi:

```python
assert f"durum.{ad}" in k, ad        # tamamlanan, toplam, dusen, ...
```

Yani `durum.tamamlanan`'ın **var olduğunu** sınıyordu. Ama
`durum.n_tamam` de kaynakta **duruyordu** — ve varlık sınavı onu
görmüyordu.

#### Aslında **iki** kusur vardı

Yokluk sınavı eklenince ikisi birden çıktı:

| satır | yanlış alan | doğrusu |
|---|---|---|
| `155` | `durum.n_tamam` | `durum.tamamlanan` |
| `156` | `durum.n_dusen` | `durum.dusen` |

İkisi de aynı düzenlemede kaçmıştı (heredoc içinde satır sonu
kaçışının üçüncü kez bozulması).

#### Çare: **yokluk** sınavı

```python
kullanilan = set(re.findall(r"durum\.(\w+)", k))
assert not (kullanilan - alanlar)
```

Artık `EnsembleDurum`'da olmayan **hiçbir** alan kullanılamıyor.

#### Aynı sınıf, üçüncü kez

| | |
|---|---|
| A29 | `β` doğru sayıydı, **yanlış büyüklüğün** |
| A32 | `pytest \| tail` — test düştü, **çıkış kodu `0`** |
| **A33** | **test geçti, kusur duruyordu** |

Üçünde de: *doğrulama olumlu, ama doğruladığı şey amaçlanan şey
değil.* Varlık sınamak yetmiyor; **yokluk** da sınanmalı.

#### Veri kurtuldu

`ensemble_kos` JSONL'i **satır satır** yazdığı için `24` noktanın
tamamı diskteydi. Çöküş yalnızca özet satırındaydı. Tasarım kararı
işe yaradı.

---

### A34 — **TRUBA iki gün geride kaldı**: koşular eski kodla koştu (2026-09-03)

`L1`/`L2` gönderilirken `git pull` yapılmıştı, ama sonraki iki günün
işi (`A32`'nin `pipefail`'i, `Δβ`, `θ_ejekta`, `plato_gecti`, alan
adı düzeltmeleri) TRUBA'ya **çekilmedi**. Koşular `3bbc722`'de kaldı.

| sonuç | |
|---|---|
| `L1` | alan adı kusuruyla koştu -> özet satırında çöktü |
| `L2` | sonuç dosyaları **momentum defterini taşımıyor** (o kod sonradan geldi) |

Defter sonradan kayıtlı durumlara uygulanabildi (`son_durum.npz`
`mermi_kesri`'yi taşıyor), yani veri kaybı yok — ama koşu **kendi
yargısını taşımıyor** ve ADR-0049'un istediği bu.

**Çare:** SLURM betikleri işin **içinde** `git pull` yapmalı; gönderim
anındaki sürüm değil, **koşum anındaki** sürüm kullanılmalı.

---

### A18 — **`G4-C`'nin ensemble verisi depoda yok ve geri alınamıyor** (2026-08-21)

Kapı raporu `G4-C`'yi üç ölçütle geçiriyor (`C1 = 1`, `C2 = 0,221142`,
`C3 = 1`) ve vekil kalitelerini yazıyor (`krater_derinlik`
`q2 = 0,907`, `beta` `0,749`, `ejekta_kutle_kesri` `0,308`). Bu
sayıların **hepsi** `40` noktalık bir `X, Y` matrisinden geliyor.

**O matris depoda yok.**

| aranan | nerede olması gerekirdi | durum |
|---|---|---|
| `g4c_ensemble.json` | `docs/olcumler/` | **yok** |
| `faz46_g4c_s1.json` | `docs/olcumler/` | **yok** |
| `faz412` çıktısı (`X`, `Y`) | `docs/olcumler/` | **yok** |

Depoda yalnızca **betikler** var (`faz46_g4c_s1.py`,
`faz46_g4c_hazir_ensemble.py`). Veri eski TRUBA çalışma alanında
(`egitimg16u4`) kalmış ve orası artık erişilemez. `2026-08-21`'de
erişilebilen her yerde arandı:

```
find /arf/scratch/egitimg16 /arf/scratch/egitimg16u1      /arf/home/egitimg16u1 -name "*g4c*" -o -name "faz46*" -o -name "faz412*"
-> hicbir sonuc
```

`.gitignore` *"koşu çıktıları; kanıtlar `docs/evidence` altına
**seçilerek** kopyalanır"* diyor. Kural doğru ama **uygulanmamış**:
seçilerek kopyalanan şey `G0`–`G3` kapı raporlarıydı, `G4`'ün
ensemble'ı değil.

> **Sonuç:** `G4-C`'nin sayıları **yeniden üretilemez**. Kapı raporu
> onları hâlâ gösteriyor ve gösterdiği şey yanlış değil — ama
> arkasındaki veri kaybolduğu için bir okuyucu **doğrulayamaz**.
> Bu, deponun kendi *"kanıtla geçilir"* kuralının delindiği yer.

#### Ne yapılıyor

`2026-08-21`'de koşan A11 ensemble'ı (iş `1515252`, `40` nokta,
`λ₂ = 4`) `X`, `Y`, `derinlik` ve **çap**ı tek JSON'a yazıyor. O
çıktı bittiğinde `docs/olcumler/` altına **kopyalanacak** ve vekil
o veriden yeniden eğitilebilecek.

Bu A18'i kapatmıyor: kaybolan `λ₂ = 2` ensemble'ı geri gelmiyor ve
yeni ensemble **üretim çözünürlüğünde değil**.

> ### Kısmen yapıldı (2026-08-21)
>
> İş `1515252`'nin `40` noktası `docs/olcumler/ensemble_1515252.csv`
> olarak depoya girdi (`X`, `β`, derinlik, ejekta kesri, **çap**) ve
> vekil o dosyadan **yeniden eğitilebiliyor** — depo kopyası TRUBA
> kopyasının verdiği `q2`'leri birebir veriyor.
>
> A18 yine de **açık**: kaybolan `λ₂ = 2` ensemble'ı geri gelmedi ve
> `G4-C`'nin kapı raporundaki sayılar hâlâ yeniden üretilemiyor.

---

#### A19'un **çaresi** ve onunla gelen gerçek tablo (2026-08-21)

Kırık çıkarıcıyı değiştirmek yerine yanına doğru ölçü yazıldı
(`krater_yerdegistirme`): **aynı parçacıkların yer değiştirmesine**
bakıyor, mutlak yarıçapa değil.

| | |
|---|---|
| yüzey kabuğu | **referans** konfigürasyondan seçilir |
| kutulama | **referans** kutup açısına göre — kutu üyeliği çarpmadan etkilenmez |
| ölçülen | kutu başına `⟨r − r₀⟩` |
| kaçan madde | `r > 1,05 R` **dışlanır** |

**Değişmez:** `x is x_reference` ise her kutuda yer değiştirme tam
`0`'dır, yüzey ne kadar pürüzlü olursa olsun. Pürüz iki tarafta da
aynı olduğu için **farkta çıkar gider** — yaklaşım değil, cebirsel
özdeşlik. A19'un kök nedeni tam buydu.

| sentetik sınav | eski ölçü | **yeni ölçü** |
|---|---|---|
| kimildamamış, düzgün | `0` | `0` |
| kimildamamış, **pürüzlü** | `0,26 m` | **`0,000000`** |
| gerçek `12 m` çukur (`15°`) | `-0,03 m` | **`9,29 m`** |
| pürüzlü + `12 m` çukur | — | `10,50 m` |
| krater **yokken** çap | `0,0` | **`nan`** (uydurmuyor) |

##### Ve gerçek koşularda krater **yok**

Yeni ölçü bütün kayıtlı durumlara uygulandı (`t = 0,2 s`):

| kol | `μ` | **derinlik** | çap | `d/D` |
|---|---|---|---|---|
| `λ₂ = 2` (üretim) | `80,4` | **`0,0849 m`** | `17,84` | `0,005` |
| `λ₁ = 38` | `80,4` | `0,0531` | `17,84` | `0,003` |
| `λ₂ = 6` | `2,98` | `0,0728` | `17,84` | `0,004` |
| `λ₂ = 8` | `1,26` | `0,0923` | `17,84` | `0,005` |
| `λ₂ = 8` **hasarlı** | `1,26` | `0,0926` | `17,84` | `0,005` |
| `λ₂ = 8` **zayıf** | `1,26` | **`0,1109`** | `24,93` | `0,004` |
| `λ₂ = 8` hasar+zayıf | `1,26` | `0,1105` | `24,93` | `0,004` |

Ensemble'ın `40` noktası (`λ₂ = 4`): derinlik **`0,0002 – 0,0379 m`**,
medyan `0,0099 m`.

> Yani `t = 0,2 s`'de krater **`1 – 11 santimetre**. Bu depoda
> `15,28 m` diye taşınan sayı baştan sona **çıkarıcı artığıydı**.

##### Elemelerin `μ ≈ 1`'de yeniden sınavı

| kol | derinlik | tabana göre |
|---|---|---|
| üretim malzemesi | `0,0923 m` | — |
| **hasar açık** | `0,0926 m` | **`+%0,3`** — etkisiz |
| **zayıf** (`Y0 = 1 Pa`) | `0,1109 m` | **`+%20`** |

Hasarın elenmesi `μ ≈ 1`'de **doğrulandı**. Mukavemet ise ilk kez
ölçülebilir bir iz bıraktı (`+%20`) — küçük ama gerçek.

> Kendi ölçütümde üçüncü eşik hatası: *"`d/D ≤ 0,50` -> mekanizma
> bulundu"* yazmıştım. Ölçülen `0,004 – 0,005`, yani dal **teknik
> olarak** ateşliyor — ama sebebi çanak açılması değil, çukurun
> `9 cm` olması ve *"çap"*ın kutu genişliğiyle belirlenmesi.
> **Bunu başarı diye okumuyorum.**

---

#### Uzun koşu: model **kazmıyor, çınlıyor** (iş `1515364`)

`λ₂ = 6` (`μ = 2,98`, şok hedefe giriyor), `t_end = 20 s` istendi.

| `t` | `beta_bal` | `hedef_ej` | **`bekleyen`** | `t_geçiş` |
|---|---|---|---|---|
| `0,2 s` (kısa koşular) | `1,41` | `0` | **`0`** | — |
| `2,51 s` | `1,259` | `3` | `6 342` | `54,3 s` |
| `4,83 s` | `1,302` | `3` | `7 088` | `59,6 s` |
| `6,56 s` | `1,210` | `3` | `7 874` | `62,4 s` |
| `7,72 s` | `1,283` | `4` | `5 368` | `63,0 s` |

**Kazı akışı gerçekten doğuyor**: içeride dışarı giden madde
`0 → 5 000–14 000` parçacık. Ama:

- `β` `1,31`'de kalıyor, `beta_bal` `1,18 – 1,31` arasında
  **salınıyor**, eğilim yok.
- `2R`'yi geçen hedef maddesi tek haneli (`3 – 46`, gürültülü).
- Yeni ölçüyle yüzey profili (`t = 7,72 s`):

```
aci:  1     4     6     9    11    14    16    19    21    24
Dr : +0,034 +0,098 +0,103 +0,066 +0,089 +0,075 +0,059 +0,019 -0,022 -0,039
```

Eksene yakın yer değiştirme **pozitif** — yüzey içeri çökmüyor,
**dışarı kabarıyor**. `t = 0,2 s`'de `-0,073 m` olan eksen değeri
`t = 7,7 s`'de `+0,034 m` olmuş.

> **Model kazmıyor, çınlıyor.** Madde dışarı gidiyor ama bir kazı
> akışı olarak değil, cismin salınımı olarak; yüzey aşağı değil
> **yukarı** hareket ediyor. Bu, A17'nin *"iç dolaşım net momentumun
> 250 katı"* ölçümüyle ve *"dört işaret dönüşü"* bulgusuyla tam
> tutarlı.

---

### A20 — **adım sınırı koşuyu sessizce kesiyordu** (2026-08-21)

İş `1515364` `t_end = 20 s` istedi, `azami_adim = 200 000`'de durdu ve

| | |
|---|---|
| `t_sim` | **`7,72 s`** (istenenin `%39`'u) |
| çıkış kodu | **`0`** |
| çıktı dosyası | `lam2_6_t20.json` — adında hâlâ `t20` |
| duvar | `5:08:58` |

Yani **kısa kalmış bir koşu, tam koşmuş gibi kaydedildi**. Bu koşunun
sonuçları yukarıda `t = 7,72 s` diye okundu; eğer okunmasaydı
`20 s`'lik sonuç sanılacaktı.

Düzeltildi: `_kos` artık `t < t_end` ile dönerse **`RuntimeError`**
atıyor ve kaç adımda nerede kaldığını yazıyor.

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
| **ölçüm aracının kendisi bozuk** | **5** | aracı önce bilinen bir durumda sına |
| kendi düzeneğimin hatasını **koda yıkmak** | **1** | *(en pahalısı — yanlış bir kusur raporladım)* |
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

#### En pahalısı: düzeneğimin hatasını **koda yıktım**

Krater çıkarıcısının *"`80 m`'lik krateri bile göremediğini"* bildirdim,
yeniden üretim betiği yazdım, `xfail` ekledim ve **rapora geçirdim**.
Sonra ortaya çıktı ki `impact_direction`'ı ters vermişim — çıkarıcı
karşı kutba bakıyordu.

> Diğer dört olayda bozuk araç **kendi yazdığım tanıydı**; bu kez
> **çalışan bir modülü suçladım**. Karşı önlem aynı: yeni bir düzenek
> **bilinen doğru cevabı** vermeden sonuç bildirilmez. `+x`'e krater
> oyup `-x` vererek sınasaydım ilk denemede görürdüm.

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
