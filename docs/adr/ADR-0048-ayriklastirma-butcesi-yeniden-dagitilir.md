# ADR-0048 — Ayrıklaştırma bütçesi **yeniden dağıtılır**: eksenel simetri + hareketli inceltme + fırlatma-anı gözlenebiliri

**Tarih:** 2026-08-21
**Durum:** **ÖNERİ** — kısıt ölçüldü (§2), mimari kararı **kullanıcının**
**İlgili:** [ADR-0043](ADR-0043-iki-asamali-cozunurluk.md) ·
[ADR-0047](ADR-0047-beta-ileri-modelin-ciktisi-degil.md) ·
[ADR-0028](ADR-0028-uzun-kosu-kararliligi.md) ·
[KAYIT-053](../defter/KAYIT-053_2026-08-21_kutle-orani-ve-denetim.md)

---

## 1. Neden yeni bir mimari kararı

Bugüne kadar A17 **düğme çevirerek** kovalandı: süre, yerçekimi, matris
`Y0`, blok `Y0`, hasar, gözeneklilik, `λ₂`, `λ₁`. Hepsi ölçüldü, hepsi
elendi ya da `β`'yı gözlemden **uzağa** itti.

Kök neden bulundu ve bir parametre değil: **şok hedefe girmiyordu**
(`u_hedef/u_mermi = 0,0016`), çünkü mermi kendisinden `80` kat ağır
tek bir parçacığa çarpıyordu (`μ = 80,4`). `λ₂ = 6–8` ile `μ ≈ 1–3`'e
inildi ve oran `0,73`'e çıktı — **eşleşme düzeldi**.

Ama `β` yükselmedi ve yakın alanda (`r > 1,05R`) hedeften kaçan madde
hâlâ **yok**. Sebep artık belli: `t = 0,2 s`'de ejekta perdesi henüz
**doğmamış**. Kazı akışı `15 m`'lik bir kraterde `~10–100 s` sürer.

> Yani mesele *"hangi parametre"* değil, **bütçenin nereye
> harcandığı**.

---

## 2. Ölçülen kısıt: **parçacık değil, zaman**

`λ₂ = 8` (`μ = 1,26`, `N = 70 839`, `s = 0,875 m`) koşusundan:

| | ölçülen |
|---|---|
| adım başına | `523 ms` |
| `dt` (CFL `0,25`) | `3,65e-5 s` |
| `t_end = 0,2 s` | `5 486` adım, **`48 dk`** |

Aynı çözünürlükte daha uzun koşmak:

| `t_end` | adım | **duvar (tam 3B)** |
|---|---|---|
| `5 s` | `1,37e5` | `19,9 saat` |
| `20 s` | `5,49e5` | `79,7 saat` |
| **`100 s`** | `2,74e6` | **`399 saat`** |

> Parçacık sayısı sorun **değil** (`71k` rahat). Duvar **zaman
> integrasyonu**: ejektanın oluştuğu süreye, ejektayı üretebilecek
> çözünürlükte gitmek `~400 saat`.
>
> Bugüne kadarki bütün *"uzun koş"* denemeleri bu yüzden ya kaba
> çözünürlükte (`μ = 80`, mekanizma yok) ya da kısa (`t = 0,2–5 s`,
> ejekta yok) kaldı. **İkisi bir arada hiç denenmedi ve mevcut
> mimaride denenemez.**

---

## 3. Üç çarpan — hiçbiri denenmedi, üçü **bağımsız**

### Ç1 — Eksenel simetri: **`36×`**

`configs/p3_scene.yaml`: `angle_deg: 0.0`, `aim: [0, 0, 1]`. Çarpma
**tam dik** ve hedef bir küre. Bloklar dışarıda bırakıldığında problem
**eksenel simetriktir**; tam 3B küre simüle etmek simetriyi
ayrıklaştırmaya harcamaktır.

Eksen etrafında `θ` açılı bir **kama**, yansıtıcı yan duvarlarla,
parçacık sayısını `360/θ` kat düşürür:

| kama | çarpan | `t_end = 100 s` duvarı |
|---|---|---|
| `30°` | `12×` | `33,7 saat` |
| **`10°`** | **`36×`** | **`11,2 saat`** |
| `5°` | `72×` | `5,6 saat` |

**Bedeli:** SPH çekirdeğine **yansıtıcı yan sınır** eklemek (iki düzlem,
ayna hayalet parçacıkları). Yeni fizik değil, yeni **sınır koşulu** —
ve kendi doğrulamasını ister (küresel simetrik Sedov kamada tam
çözümü vermeli).

**Ne kaybedilir:** bloklar. Moloz yığını yapısı eksenel simetrik
değil. Yani kama kolu **mekanizma** çalışmasıdır; iç yapı çıkarımı
tam 3B kalır. Bu bir daralma ve açıkça yazılmalı.

### Ç2 — Hareketli inceltme: **`3–10×`**

Bugün ince bölge `r < 25 m`'de **sabit** ve `t = 0`'dan itibaren
oradadır. Oysa:

- `t < 5 ms`: iş çarpma noktasında (`r < 3 m`)
- `t ~ 0,1–100 s`: iş **genişleyen krater kenarında**

Yani ince parçacıkların büyük kısmı, işin olmadığı yerde ve olmadığı
zamanda duruyor. Kazı cephesini **izleyen** bir inceltme (parçacık
bölme/birleştirme) aynı bütçeyle kazı bölgesinde `3–10×` daha ince
olur.

**Bedeli:** bölme/birleştirme korunumlu olmalı (kütle, momentum,
enerji) — depo bunun altyapısına **zaten sahip**
(`coarsen_to_sites`, `Sum m D` defteri, `refine_scene_local`).

### Ç3 — Fırlatma-anı gözlenebiliri: **`5–20×`**

`β` bugün *"madde `2R`'yi geçti mi"* diye ölçülüyor ve bu, `~550 s`
beklemek demek. Çarpma literatürü böyle ölçmez: **ejekta kütle–hız
dağılımı** `M(>v)` fırlatma anında ölçülür ve balistik olarak
integre edilir.

`M(>v)` kazı akışı kurulur kurulmaz (`t ~ 5–20 s`) ölçülebilir; `2R`
beklenmez. Bu, gereken `t_end`'i `100 s`'den `~20 s`'ye indirir.

**Bedeli:** yeni bir gözlenebilir ve onun doğrulaması. `2R` ölçütü
**silinmez** — ikisi birlikte raporlanır ve tutarlılıkları ölçülür.

### Ç4 — `A1` eşiği: `>= 2` **yetersiz olduğu ölçüldü**

`A1 = mermi çapı / yerel aralık` ölçütünün eşiği `>= 2`. Yani mermi
**iki parçacık** eninde. Şok literatüründe mermi tipik olarak
`10 – 20` parçacıkla çözülür; `2` ile şok merminin **içinde** bile
ayrıklaştırılamaz.

Ve ölçüldü: `A1` `2,04 -> 4,08` olunca `β` **`%16`** değişiyor. Yani
`A1 = 2` yakınsamış değil, **uzağında**.

Maliyet (ölçülen `n_ince ~ λ₁^2,48` ölçeklemesiyle; aşama-1 `λ₁ = 19`
H100'de `~30 s`):

| `A1` | `λ₁` | `s_ince` | `n_ince` | aşama-1 maliyeti | H100 |
|---|---|---|---|---|---|
| **2,0** (bugün) | `19` | `0,368 m` | `2 327` | `1×` | `30 s` |
| 4,1 | `38` | `0,184 m` | `13 011` | `11×` | `6 dk` |
| **8,0** | `75` | `0,094 m` | `69 355` | `117×` | **`1 saat`** |
| 12,0 | `112` | `0,063 m` | `189 838` | `480×` | `4 saat` |
| 20,0 | `186` | `0,038 m` | `675 033` | `2 845×` | `24 saat` |

> `A1 = 8` **bugün karşılanabilir** (aşama-1 için `~1 saat`) ve
> `λ₁` yakınsama eğrisine üçüncü noktayı koyar. `A1 = 20` tek nokta
> için `24 saat` — ensemble için değil, **mekanizma** için.

Ama dikkat: aşama-2 aktarımı bu inceliği `t₁`'de **kabalaştırıp
atıyor**. Yani Ç4 tek başına yetmez; Ç2 (hareketli inceltme) ile
birlikte anlamlı.

#### SONRADAN ÖLÇÜLDÜ (2026-08-29, A23 · A24)

Yukarıdaki tablo `β`'nın `A1` ile değişimine dayanıyordu — yani
modelin **kendi** çıktısına. Şok sınavı dışarıdan bir hedef verdi ve
sayılar **değişti**:

| | tabloda | **ölçülen** |
|---|---|---|
| şok için gereken `s` | ima: `≤ 0,094 m` (`A1 = 8`) | **`0,175 m`** (`λ₂ = 40`) |
| o noktada sıkışma | bilinmiyordu | `%40,5` — Hugoniot'un `%89`'u |
| `s = 0,350 m` | *"yetersiz"* | `%22,0` — **şok var** |

Ve *"aktarım inceliği kabalaştırıp atıyor"* sezgisi **eksik**
çıktı: aktarım kabalaştırmıyor, **sıfırlıyor**. `ρ` hiç
taşınmıyordu; çözücü onu her zaman `ρ₀/α₀` ile kuruyordu (A24).
Çare yazıldı (hacim korunumlu aktarım) ve Ç2'nin gerekçesi
**güçlendi**: hareketli inceltme olmadan şok, ince bölgenin
sınırında (`3,4 m`) duruyor.

Maliyet de düzeldi. Üretim bütçesine göre, `t_end = 0,2 s`:

| şema | `N` | H100 / nokta | `40` nokta |
|---|---|---|---|
| `λ₂ = 20`'yi `r = 25 m`'ye yaymak | `1 089 581` | `30,6 saat` | `1 225 saat` |
| **üç seviyeli** (`0,35`/`0,875`/`3,5`) | **`33 008`** | **`56 dk`** | **`37 saat`** |

Yani şoku kurmak için gereken şey **daha çok parçacık değil**,
parçacıkları **doğru yere koymak** — ki bu ADR'nin tezi zaten buydu.
Artık dışarıdan ölçülmüş bir hedefle destekli.

### Birleşik etki

`Ç1 × Ç3` tek başına: `399 saat -> ~2 saat`. Üçü birlikte, `μ ≪ 1`
çözünürlüğünde tam kazı süresi **bir gecelik koşu** olur.

---

## 4. Dördüncü iş: **dış kıyas** (mimari değil, ama şart)

Model bugün yalnızca **kendi** ölçütlerine karşı doğrulanıyor
(Sedov, Hugoniot, korunum). Kraterin **büyüklüğü** hiçbir dış
standarda karşı sınanmadı.

π-grubu ölçeklemesi (Holsapple 1993; Housen & Holsapple 2011) verilen
çarpma ve hedef için krater hacmini **kapalı formda** verir. Bu bir
uydurma değil, literatür sabitleriyle bir kıyastır ve **koşu
gerektirmez**.

Bu olmadan *"modelim doğru mu"* sorusunun cevabı yok — ve bu, dışarıdan
gelecek ilk sorudur.

---

## 5. Seçenekler

| # | ne | maliyet | kazanç |
|---|---|---|---|
| **M1** | Yalnızca Ç3 (fırlatma gözlenebiliri) + π kıyası | **günler** | `t_end` `100 -> 20 s`; dış doğrulama |
| **M2** | Ç1 + Ç3 (kama + yeni gözlenebilir) | **haftalar** | `μ ≪ 1`'de tam kazı, bir gecede |
| **M3** | Ç1 + Ç2 + Ç3 (tam yeniden dağıtım) | **aylar** | üretim ensemble'ı da bu bütçede |
| **M4** | Hiçbiri — ADR-0047 S3 ile `β`'yı gözlenebilir olmaktan çıkar | **sıfır** | dürüst ama iddia daralır |

---

## 6. Eğilimim: **M1 şimdi, M2 hemen sonra**

Gerekçe: Ç3 ve π kıyası **çözücüye dokunmadan** yapılır, ikisi de
bugünkü kayıtlı durumlarla başlar ve ikisi de M2'nin ölçütünü
hazırlar. Kama (Ç1) en büyük çarpan ama yeni bir sınır koşulu ve o
kendi doğrulamasını ister — ölçütü M1'in sonucuyla yazılmalı.

M4 her zaman elde: M1/M2 sonuç vermezse `β` dürüstçe düşer.

---

## 7. Karar için gereken **eksik ölçüm**

| # | ölçüm | durum |
|---|---|---|
| 1 | π-ölçeklemesinin öngördüğü krater vs modelin krateri | **yapılabilir, koşu gerekmez** |
| 2 | `M(>v)` kayıtlı durumlardan çıkarılabiliyor mu | kısmen (`t = 0,2 s` erken) |
| 3 | Kamada Sedov tam çözümü — yansıtıcı sınırın doğrulaması | Ç1 seçilirse |

**1 olmadan hiçbir mimari kararı verilmemeli:** modelin krateri
literatürle uyumluysa sorun yalnızca ejekta muhasebesidir ve M1
yeter; uyumsuzsa mesele daha derindir ve M2/M3 bile yetmeyebilir.
