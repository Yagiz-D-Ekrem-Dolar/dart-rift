# KAYIT-036 — Boşluk 3: mukavemette ölçüldü, gözeneklilikte **ölçülemedi** (2026-08-08)

**Kapsam:** FAZ 4.4 · **Durum:** **kısmen** kapandı
**Öncül:** [ADR-0041](../adr/ADR-0041-yerel-incelme-yaklasimi.md) §5 boşluk 3,
[KAYIT-026](KAYIT-026_2026-08-04_E3-sok-arayuzden-gecerken.md),
[KAYIT-035](KAYIT-035_2026-08-08_omega-celiskisi-olculerek-cozuldu.md)

---

## 0. Kapatılmaya çalışılan boşluk

> **§5 boşluk 3** — Sedov gerilmesiz ve tek malzemeli; mukavemet,
> gözeneklilik ve hasarla etkileşim ölçülmedi.

A′ hakkında bilinen her şey **ideal gaz** Sedov'unda ölçülmüştü. Ve
KAYIT-026 aslında A′'yı değil, A′'nın *arayüz geometrisini* ölçmüştü —
o zaman `h` skalerdi. Bu ölçüm iki şeyi birden değiştiriyor: malzeme
basalt (Tillotson + mukavemet + gözeneklilik + hasar) ve iki bölgeli kol
**gerçek A′** (ince bölgede `h/λ`).

---

## 1. Sonuç — önce yargı

| kol | yargı | taşma (`0,02`) | `t` |
|---|---|---|---|
| **yalnız EOS** | eşiğe bağımlı | **%0,0000** | 3e-5 |
| **+ mukavemet** | eşiğe bağımlı | **%0,0000** | 3e-5 |
| + gözeneklilik | ölçülemedi (aşağıda) | — | 1,5e-5 |
| tam (EOS+muk+göz+hasar), A′ | ölçülemedi | — | 1,5e-5 |

> **Mukavemet açıkken A′'nın arayüzü şok cephesine hiçbir şey
> eklemiyor** — taşma tam `%0,0000`, KAYIT-026'nın ideal gaz sonucuyla
> **aynı**.
>
> **Gözeneklilik açıkken ölçüm kurulamadı.** Bu bir sonuç değil, bir
> **başarısızlıktır** ve öyle yazılıyor.

---

## 2. Mukavemet kolu — ölçülen tablo (job 1460698, H200)

`t = 3e-5 s`, `n_kaba = 32`, `λ = 2` (8:1), `r_iç = 0,15`:

| kol | `r@0,01` | `r@0,02` | `r@0,05` | N |
|---|---|---|---|---|
| tekdüze kaba | 0,28773 | 0,25921 | 0,21397 | 32 768 |
| **iki bölgeli (A′)** | **0,28086** | **0,25540** | **0,20933** | 35 936 |
| tekdüze ince | 0,27369 | 0,25334 | 0,22270 | 262 144 |
| **parantez içinde mi** | ✔ | ✔ | ✘ | |

Ön koşulların hepsi geçti: kollar ayırt edilebilir, enjekte enerji eşit,
kütle sapması `%0,073`, enjeksiyon bölgesi eşit.

### `0,05` eşiği neden ayrı düşüyor

| | `0,01` | `0,02` | `0,05` |
|---|---|---|---|
| parantez genişliği | %5,13 | %2,31 | **%2,00** |
| taşma | %0,00 | %0,00 | **%2,17** |
| taşma / parantez | 0 | 0 | **1,09** |
| kaba > ince mi | ✔ | ✔ | **✘ (ters)** |

İki şey birden oluyor:

1. **Ölçütün orada gücü yok.** Taşma parantezle **aynı mertebede**
   (`oran 1,09`). Bir ölçüt kendi çözünürlüğü kadar bir farkı "dışarıda"
   ilan ediyorsa, doğru yanıt *"geçti"* değil, *"bu eşikte ayırt
   edemiyorum"*dur.
2. **Sıralama ters dönüyor.** Düşük eşikte kaba > ince, yüksek eşikte
   ince > kaba. Yani iki eşik **farklı fiziksel özelliği** ölçüyor:
   düşük eşik elastik öncü dalgayı, yüksek eşik şiddetli çekirdeği.

> **Bu bilgi yargıyı kurtaracak biçimde ayarlanmadı.** `esige_bagimli`
> verdikti duruyor; `judge` yalnızca her eşiğin **gücünü** yanına
> yazıyor. Yorum okuyanın, ayar benim olmamalı.

---

## 3. Gözeneklilik kolu neden ölçülemedi

P-α gözenekliliği enerjiyi **gözenek çöktürerek** yutuyor. Ölçüldü:

| büyüklük | gözeneksiz | gözenekli |
|---|---|---|
| `ρ_maks` (`t = 3e-5`) | **2730–2804** | **1803–1805** |
| başlangıç `ρ` | 2700 | **1800** (`= ρ₀/α₀`) |
| sıkışma | `~%2` | **`~%0,3`** |

Malzeme neredeyse hiç sıkışmıyor; tepe hız düşük kalıyor ve bozulma
zayıf ama **geniş** yayılıyor. Sonuç: cephe kutu kenarına varıyor.

`t = 1,5e-5`'e inince cephe kutuya sığıyor ama bu kez çok erken:

| kol | `r` (`t=1,5e-5`) |
|---|---|
| tekdüze kaba | 0,128113 |
| iki bölgeli | **0,034527** |
| tekdüze ince | 0,034525 |

`r = 0,0345` **arayüzün (`0,15`) içinde** — yani bozulma arayüze
**varmamış**. Arayüzü sınamayan bir koşu arayüz hakkında bir şey söylemez.
Yargı `arayuz_zararsiz` çıktı ama **anlamsız**: parantez `%271` geniş
çünkü kaba kol dört kat ötede.

> **Kutu aynı anda iki şartı sağlayamıyor:** cephe arayüzü geçecek kadar
> ilerlemeli **ve** kutu kenarına varmamalı. Gözenekli malzemede bu
> pencere bu kutu boyutunda **yok**.

### Gereken

Daha büyük kutu (ya da soğurucu sınır) + daha uzun `t`. Bu bir kurulum
işidir, bir belirsizlik değil — ama **bu kayıtta yapılmadı**.

---

## 4. Bu ölçümde yakalanan dört kusur

Hepsi benim kurduğum ölçümdeydi, hiçbiri çözücüde değil:

| # | kusur | nasıl yakalandı | ders |
|---|---|---|---|
| 1 | `E = 5e9 J` → özgül `6,6e7 J/kg`, buharlaşmanın **3 katı** | koşu patladı (`overflow in reduce`) | mertebe **hesaplanır** (`3,4e6 J` çıktı) |
| 2 | eşik `1,05·ρ₀` hiç tetiklenmedi | sonda tanılayıcı yapılınca | gözeneklilikte `ρ` başlangıcı `ρ₀/α₀`; **yığın ≠ katı** |
| 3 | enjeksiyon yarıçapı kolun **kendi** `dx`'ine bağlıydı | ince kol patladı (262144/262144 NaN) | aynı enerji **aynı bölgeye** girmeli; `enerji_esit` bunu yakalayamaz |
| 4 | eşik `kesir·max\|v\|` → kollarda **farklı** eşik | `r = 0,838970` = kutu köşesi | referans **kola bağlı olmamalı**: `v_ref = √(2E/m_enj)` |

3 numaralı kusur ön koşul listesinde bir **boşluk** açığa çıkardı:
üç kolun enerjisi `3,8e-16` içinde aynıydı ama **dağıldığı bölge**
farklıydı. Yeni ön koşul: enjekte edilen **kütle** de eşit olmalı.

4 numaralı kusurdan sonra **doygunluk koruması** eklendi:
`r > 0,45·KUTU` ise ölçüm geçersiz. Onsuz `muk+gözenek` kolu parantezi
`%278,95` genişletip iki bölgeli kolu "içine" alıyor ve **yanlış bir
`arayuz_zararsiz`** üretiyordu.

### Bir de süreç hatası

Metin değiştiren betiğim eşleşmeyi **doğrulamadan** `"ok"` yazdı; çağrı
kaldırılmamıştı ve iş `NameError` ile düştü. Artık her değiştirmede
`assert` var — ya da `Edit` kullanılıyor (o eşleşmezse patlar).

---

## 5. Boşluk 3'ün durumu

| bileşen | durum |
|---|---|
| Tillotson (gerilmesiz) | **ölçüldü** — taşma %0,0000 |
| **mukavemet** | **ölçüldü** — taşma %0,0000 |
| gözeneklilik | **ölçülemedi** — kutu penceresi yok |
| hasar | **ölçülemedi** — gözeneklilikle birlikte koşuluyordu |

> Boşluk 3 **kısmen** kapandı. ADR-0042'nin ve ADR-0041'in bu boşluğa
> bağlı olan kısımları **hâlâ koşulludur**.

---

## 6. Sırada

| # | iş | neden |
|---|---|---|
| 4.4b | gözenekli kol için **büyük kutu** kurulumu | pencere yok; kurulum işi |
| 4.5 | gereken benzetim süresi (ADR-0028'in açık maddesi) | |
| — | ADR-0042'nin DART geometrisinde sınanması | kararı koşullu yazdım |

---

## 7. Bu kayıtta uygulanan kurallar

| kural | nerede |
|---|---|
| ölçülemeyen şey "ölçüldü" diye yazılmaz | §1, §3, §5 |
| bir ölçüt kendi çözünürlüğünün altını yargılıyorsa **gücü yazılır** | §2 |
| yargı, sonucu kurtarmak için **ayarlanmaz** | §2 |
| bir mertebe **hesaplanır**, tahmin edilmez | §4-1 |
| bir ön koşul bir hatayı yakalayamıyorsa **yeni ön koşul** eklenir | §4-3 |
| bir referans **kola bağlı** olamaz | §4-4 |
| eşleşmeyi doğrulamayan metin değiştirme yapılmaz | §4 (süreç) |
