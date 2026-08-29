# ÖLÇÜT — Şokun **yayılması** hangi bağıl çözünürlüğü istiyor? (koşudan önce)

**Tarih:** 2026-08-29 · **Öncül:** A23 (doğma), A25 (arayüz)
**Araç:** `kademe_sinavi.py` + `sok_cephesi.py`

---

## 1. Neden bu, A23'ten **farklı** bir soru

A23 şokun **doğması** için gereken çözünürlüğü ölçtü: `r_mermi/h ≈ 1`,
yani `s ≤ 0,175 m`. Bu bir **kaynak** koşulu — merminin kendisi
çözülmeli.

Şokun `10 m`'ye **yayılması** için gereken çözünürlük başka bir sayı
ve **hiç ölçülmedi**. Orada ilgili uzunluk mermi değil, şokun kendi
yarıçapı; ölçü de mutlak `s` değil **bağıl** `s/r`.

## 2. Neden bu sayı her şeyi belirliyor

Öz-benzer merdivende (`r` ve `s` birlikte katlanır) bir oktavlık
kabuk:

    V = (14/3) π r³        N = V / (0,707 s³) = 20,7 (r/s)³

`r`'ye **bağlı değil**: her oktav **aynı** maliyette. Yani kraterin
yarıçapına ulaşmak geometrik olarak ucuz — bütün maliyet tek bir
sayıda.

| `r/s` | `N` / oktav | `3 -> 48 m` (dört oktav) | üretim bütçesine göre |
|---|---|---|---|
| `4,3` | `1 646` | `6 583` | `0,1×` |
| `8,6` | `13 166` | `52 665` | `0,7×` |
| `17,1` | `103 504` | `414 017` | `5,8×` |
| `20,0` | `165 600` | `662 400` | `9,3×` |

Benim `r/s ≥ 20` tahminim bir **varsayım**; maliyet ona **küpten**
bağlı. `8,6` ile `20` arasındaki fark **`12,6` kat**.

## 3. Karıştırıcı — ve nasıl kaldırıldı

En kolay tasarım *"`s/r`'yi baştan sona değiştir"* olurdu. **Hatalı
olurdu:** kaba merdivenlerde çekirdek de kabalaşır ve A23'e göre şok
**doğmaz** bile. Ölçülen şey yayılma değil, doğma olurdu.

> Bu, bu deponun **dört kez** düştüğü tuzağın aynısı: bir şeyin
> etkisini, o şeyin olamayacağı bir rejimde ölçmek.

Çare: **iç bölge her kolda birebir aynı**; yalnızca `r > 6 m`
değişiyor.

## 4. Düzenek — tek değişken

Ortak çekirdek (üç kolda da **aynı**): `r < 3` -> `s = 0,175`;
`3 – 6 m` -> `s = 0,350`.

| kol | `6 – 12 m` | `12 – 24 m` | dış `s/r` |
|---|---|---|---|
| **A (ince)** | `0,7` | `1,4` | `0,058` |
| **B (orta)** | `1,4` | `2,8` | `0,117` |
| **C (kaba)** | `2,8` | `2,8` | `0,233` |

`t_end = 6e-3 s` — cephenin `6 m`'yi geçmesine yetecek süre
(`3 400 m/s` ile `~20 m`).

## 5. Yargı (kilitli)

Ölçü: `>%1` sıkışan parçacıkların **en uzak** referans yarıçapı
(`sok_cephesi.py`) **ve** kaba seviyelerde şoklanan parçacık sayısı
(A25'in kütle parmak izi ölçüsü).

| sonuç | anlamı |
|---|---|
| üç kol da `> 6 m`'ye ulaşır | `r/s = 0,233` **yetiyor** -> maliyet `0,1×` |
| A ve B ulaşır, C ulaşmaz | eşik `0,117` ile `0,233` arasında -> `~0,7×` |
| yalnızca A ulaşır | eşik `≤ 0,058` -> `5,8×`, ensemble zorlaşır |
| hiçbiri ulaşmaz | sebep bağıl çözünürlük **değil**; başka bir yerde |

Son satır önemli: bu ölçüt kendi öncülünü de **çürütebilir**.

## 6. `r_dış` neden `24 m` — `β` hedefinden geliyor

`β = 3,2225` bir sayı değil, bir **kütle bütçesi**:

| | |
|---|---|
| `p_mermi` | `3 560 355 kg m/s` |
| gereken ejekta momentumu | **`7 912 889 kg m/s`** |

Bu momentumu taşıyacak madde:

| ort. ejekta hızı | gereken kütle | eşdeğer yarıçap |
|---|---|---|
| `20 m/s` | `395 644 kg` | `4,97 m` |
| `8 m/s` | `989 111 kg` | **`6,75 m`** |
| `3 m/s` | `2 637 630 kg` | `9,36 m` |
| `1 m/s` | `7 912 889 kg` | **`13,50 m`** |

Bugün şoklanan kütle `72 936 kg` ve **kaçan `0 kg`**. Yani gereken
`13,6 – 108` kat daha fazla madde.

> **Kazı bölgesi en az `~7 – 14 m` yarıçapa ulaşmalı.** Bu, literatür
> krater yarıçapıyla (`6,5 – 43 m`) tutarlı ve merdivenin şoku
> taşıması gereken mesafeyi **sayıyla** veriyor.

`r_dış = 24 m` bu bandın üstünü kapsıyor. Ve maliyet:

| `r/s` | `3 -> 24 m` (üç oktav) | üretim bütçesine göre |
|---|---|---|
| `8,6` | `39 500` | **`0,6×`** |
| `17,1` | `310 500` | `4,4×` |

Yani *"`β`'ya ulaşmak için gereken çözünürlük ne kadara mal olur"*
sorusu, bu ölçütün ölçtüğü **tek sayıya** indirgenmiş durumda.

## 7. Malzeme mi sayısal mı — **üç bağımsız hesap** aynı bandı veriyor

Bütün bu iş, sıkıntının **ayrıklaştırmada** olduğu varsayımına
dayanıyor. O varsayım sınanabilir: malzeme parametreleri doğruysa
kraterin boyutunu **açıklamalılar**.

Şok basıncı `P(r) = P₀ (r₀/r)ⁿ` ile sönüyor; krater `P > Y₀` olan
bölgeye kadar. `P₀ = 20,3 – 59,8 GPa` (A22'nin Hugoniot bandı),
`r₀ = 0,371 m`, `Y₀ = 10 MPa` (üretim matrisi):

| `n` | `P₀ = 20,3 GPa` | `P₀ = 59,8 GPa` |
|---|---|---|
| `2,0` | `16,7 m` | `28,7 m` |
| `2,5` | `7,8 m` | `12,0 m` |
| `3,0` | `4,7 m` | `6,7 m` |

Üç **bağımsız** yoldan gelen bant:

| kaynak | yarıçap |
|---|---|
| `β = 3,22`'nin kütle bütçesi | `6,8 – 13,5 m` |
| Housen-Holsapple ölçeklemesi | `6,7 – 42,8 m` |
| malzemenin **kendi** `Y₀`'ı + şok sönümü | `4,7 – 16,5 m` |

> Üçü de `~5 – 17 m`. **Malzeme parametreleri kraterin boyutunu
> açıklıyor.** Kusur malzemede değil; şokun oraya **taşınamamasında**.

Bu, çıkarım probleminin (iç yapıyı `β`'dan çıkarmak) yanlış malzeme
modeliyle çökmediğini söylüyor — sayısalı düzeltmek gerçekten
hedefe götürebilir. Ama bir tutarlılık kontrolü, kanıt değil: `n`
literatürden alınmış bir bant ve model onu kendisi üretmiyor.

## 8. Üretim reçetesi — ölçüm hangi kararı verecek

Merdiven ile iki aşamalı yol **birleşmiyor**: aktarım `r < r₁`'i
kabalaştırdığı için merdivenin iç seviyelerini öğütür. Yani merdiven
**tek aşamalı** koşulmalı ve `dt` en ince aralıktan gelir.

`t_end = 0,2 s`, öz-benzer merdiven, üretim bütçesine göre:

| `s_min` | `r_iç` | `r_dış` | `r/s` | `N` | adım | maliyet | H100/nokta | A23 sıkışma |
|---|---|---|---|---|---|---|---|---|
| `0,175` | `3` | `24` | `17,1` | `337 778` | `27 429` | `23,7×` | `19,0 sa` | `%40,5` |
| `0,175` | `3` | `12` | `17,1` | `233 493` | `27 429` | `16,4×` | `13,1 sa` | `%40,5` |
| **`0,350`** | **`3`** | **`24`** | **`8,6`** | **`50 972`** | **`13 714`** | **`1,8×`** | **`1,4 sa`** | `%22,0` |
| `0,350` | `6` | `24` | `17,1` | `233 493` | `13 714` | `8,2×` | `6,6 sa` | `%22,0` |
| `0,700` | `3` | `24` | `4,3` | `15 122` | `6 857` | `0,3×` | `0,2 sa` | `%1,7` |

Takas doğrudan: **şokun gücü** (`s_min`, A23) ile **maliyet**
arasında. `s_min = 0,175` Hugoniot'un `%89`'una çıkıyor ama
`13 – 19 saat`; `0,350` yarısını veriyor ve **`1,4 saat`**.

> Kırk noktalık bir ensemble: `s_min = 0,350` ile **`56 saat`**,
> `0,175` ile `520 – 760 saat`.

Bu ölçütün ölçtüğü `r/s` eşiği kararı **doğrudan** veriyor: `8,6`
yetiyorsa üçüncü satır seçilir ve ensemble mümkün olur; `17`
gerekiyorsa mekanizma koşuları tek tek yapılır ve ensemble başka bir
yolla (vekil model, daha az nokta) kurulur.

## 9. Ne ölçmüyor

`β`, krater. `t = 6e-3 s`'de kazı akışı yok.
