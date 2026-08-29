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

## 7. Ne ölçmüyor

`β`, krater. `t = 6e-3 s`'de kazı akışı yok.
