# KAYIT-072 — DY2: **MODEL GÖZLEME ULAŞIYOR** · `σ_şekil` ödünç `0,20`'den **ölçülmüş `0,009`**'a · A110 ölçüldü (2026-10-04)

**Kapsam:** DART sahnesinin geç evre modeliyle **gerçekleşmiş** ilk koşusu +
şekil kontrol kolu · **Durum:** iki kilitli yargı okundu, bir kilitli ölçüm
yapıldı, iki bütçe terimi ödünçten ölçülmüşe geçti, bir kusur (A110) ölçüldü ·
**Kaynak:** `docs/olcumler/DY2_DK_2026-09-30/`,
[PROTOKOL-DY](../truba/PROTOKOL-DY-DART-GEC-EVRE.md) ·
**Öncül:** [KAYIT-071](KAYIT-071_2026-09-29_UY2-azaliyor-DY-okunmaz-A112.md)
(DY **OKUNMAZ**, A112)

---

## 1. Kilitli yargı: **MODEL GÖZLEME ULAŞIYOR**

| | DY2 (elipsoit, gerçek sahne) | DK (hacim-eşdeğer küre) |
|---|---|---|
| `β` (600 s) | **3,748** | 3,772 |
| `β_km` | 3,822 | 3,855 |
| `I` | **1,40** | 1,45 |
| `M_ejekta` | **1,96e7 kg** | 3,07e7 kg |
| parçacık | 15 623 | 15 049 |
| kütle tutarlılığı | `−%0,05` | `−%0,11` |
| momentum artığı | `5,6e-15` | `9,6e-15` |
| enerji sapması | `−%0,78` | `−%0,78` |

Gözlem `3,12 ± 0,34`; `σ_model = 0,291`; payda `0,447`; kesme `3,0`.
`I = 1,40 < 3` **ve** `β ≥ 3,12 − 0,34` → **MODEL GÖZLEME ULAŞIYOR**.

**Bu, projenin merkezî sorusunun ilk olumlu cevabıdır.** U/V havuzu
`β ≈ 2,05` ile `HİÇBİR VARYANT ULAŞMIYOR` demişti (KAYIT-064); o koşular
`0,2 s`'de kesilmişti. Geç evre modeli, **gerçek DART sahnesinde**,
gözlemin bandına giriyor. Üretim havuzu anlamlı.

### Ama ne demediğini de yazalım

- `β = 3,748` gözlemin **üstünde** (`3,12`). `I < 3` olmasının nedeni
  paydanın büyük olması (`0,447`): "bant içinde", **"tutturdu" değil**.
- Bu tek nokta `Y₀ = 10 Pa`'da. Posterior `Y₀`'yu **yukarı** itecek
  (daha yüksek dayanım → daha düşük `β`). Yani bu koşu `θ`'yı çıkarmıyor;
  **havuzun gözlemi içine alabileceğini** gösteriyor. PROTOKOL-DY §4'ün
  kendi uyarısı: "Bu tek koşu `θ`'yı çıkarmaz."
- `M_ejekta = 1,96e7` gözlemin (`1,6 ± 0,3e7`, L17 Lolachi) `1,2σ` üstünde:
  **ikinci gözlemli de tutuyor.** Bu, `β`'nın doğru sebeple tutup tutmadığı
  sınavının ilk geçişi.

## 2. Kilitli ölçüm: `σ_şekil = 0,0086`

PROTOKOL-DY §6.3 (koşudan önce kilitli):
`σ_şekil = |b_elipsoit − b_küre| / b_elipsoit`, `b = β − 1`.

    |2,7480 − 2,7716| / 2,7480 = 0,0086

Kilitli yorum eşiği `< 0,05` → **"şekil terimi KÜÇÜK"**.
`MODEL_EKSIKLIGI_KAYNAKLI`'ya `hedef_sekli_olculen = 0,009` olarak girdi;
literatürden ödünç `hedef_sekli = 0,20` satırı **yerinde kaldı** (kural 6).

**Literatür bizim sahnemizde doğrulanmadı.** L1 (Raducan & Jutzi 2022)
basık elipsoidin küreden `%15–21` **yüksek** `β` verdiğini bildiriyor.
Bizde fark `%0,86` ve **ters yönde** (küre `%0,86` yüksek). Bu bir
uyuşmazlıktır ve öyle kaydedilir; olası nedenler:

- L1'in kıyasladığı elipsoit/küre çifti **aynı kütlede değil**; bizimki
  kalibrasyonla aynı kütlede (`4,30e9 kg`, A108/A111).
- Çarpma noktası: bizde her iki kolda da **merkeze doğru `17°`**; basıklığın
  `β`'ya etkisi çarpma yerine ve açısına güçlü bağlı olabilir (A95).
- Geç evre: L1'in `β`'sı farklı `t`'de okunmuş olabilir; `t = 1 s` civarında
  bizim iki kolun farkı **daha büyük** (aşağıya bak).

Bu, "ödünç terimler sorgulanmalı" tezinin somut kanıtı: NUSAP soy kütüğünde
(KAYIT-070 §2) doğrulaması **sıfır** olan terim, ölçülünce **22 kat** küçüldü.

## 3. `β` aynı — **ama sahne aynı değil**

Kaydın en önemli bulgusu bu. İki kol `β`'da `%0,6` ayrılıyor; geri kalan
her şeyde ayrılıyor:

| büyüklük | DY2 elipsoit | DK küre | bağıl fark |
|---|---|---|---|
| `β` (600 s) | 3,748 | 3,772 | **`%0,6`** |
| `M_ejekta` | 1,96e7 | 3,07e7 | **`%56`** |
| koni tam açısı | `85,2°` | `124,8°` | **`%46`** |
| `t50` (impulsun yarısı) | **`0,54 s`** | **`1,43 s`** | **2,6 kat** |
| `s(1 s) = β(1s)/β(600s)` | 0,554 | 0,476 | `%16` |
| dondurulan parçacık | 4103 | 3728 | `%10` |

**Sonuç 1 — şekil betimleyicileri iddiası doğrulandı.** KAYIT-070 §2'de
"`β` tek başına mekanizmayı ayırt etmiyor, `t50`/`s(1s)` ekleyelim" demiştik.
İşte aynı `β`'yı veren **iki farklı mekanizma**: `t50` onları **2,6 kat**
ayırıyor. `rank(F) ≤ gözlemli sayısı` argümanı (tanımlanabilirlik) artık
teorik değil, **ölçülmüş**.

**Sonuç 2 — `M_ejekta` ayırt edici, `β` değil.** Gözleme uzaklık:

| | `M_ejekta` | gözlemden sapma (`1,6 ± 0,3e7`) |
|---|---|---|
| DY2 elipsoit | 1,96e7 | **`1,2σ`** |
| DK küre | 3,07e7 | **`4,9σ`** |

Yani gerçek şekli kullanmak **zorunlu** — ama `β` yüzünden değil,
**ejekta kütlesi** yüzünden.

> **Protokolün koşudan önce yazdığı yoruma düşülen not** (kural 6: kural
> değişmez, not yan yana eklenir). PROTOKOL-DY §6.3'ün kilitli yorumu
> "`σ_şekil < 0,05` ise küresel sahneler de savunulabilir" diyordu. Ölçüm
> `0,0086` çıktı ve bu yorum **`β` için geçerli**. Ama aynı iki kol
> `M_ejekta`'da `%56`, koni açısında `%46`, `t50`'de `2,6 kat` ayrılıyor.
> **`β` dışındaki hiçbir gözlemli için küresel sahne savunulamaz.** Üretim
> havuzu elipsoit sahnede koşar (zaten öyle planlıydı); DK'nın işi bu
> terimi ölçmekti ve ölçtü.

## 4. Aşırı kolay okumaya karşı: `β`'nın şekle duyarsızlığı neden anlamlı

`β` bir **oran**: aktarılan momentum / mermi momentumu. Mermi, hedef
yüzeyinin `~2 m` ölçeğindeki bir bölgesini görüyor; `88,5 × 87 × 58 m`
elipsoit ile `R = 76,4 m` küre o ölçekte **ayırt edilemez**. Hedefin
bütün şekli ancak ejektanın **nereye kaçtığını** (koni, kütle, zamanlama)
değiştiriyor. Yani ölçtüğümüz `%0,86`, bir sayı hatası değil, **beklenen
fizik**: `β` yerel, `M_ejekta` küresel.

Bu okuma bir öngörü de üretiyor: `α_b`/`f` gibi **yerel** parametreler
`β`'da görünür, `Y₀` gibi **geç evreyi** yöneten parametreler `t50`'de
daha güçlü görünür. Posterior bunu sınayacak.

## 5. A110 **ölçüldü**: plato terimi sahneye bağlı

KAYIT-071 A110'u "açık" bırakmıştı: `t_end = 600 s` yetiyor mu? O sayı
(`−%2,7/dekad`, `β∞ ≈ 4,55`) **bozuk DY koşusundandı** (A112). Düzeltilmiş
sahnede yeniden ölçüldü — `β = β∞ + C/t` uydurması, `t ≥ 100 s`, 7 nokta:

| kol | tepe | `b` 60→600 s | `β∞` | 600 s'den sonra **kalan yol** |
|---|---|---|---|---|
| **DY2** (DART, elipsoit) | `4,050 @ 62,9 s` | `−%9,7` | **3,703** | **`−%1,64`** |
| DK (hacim-eşdeğer küre) | `3,867 @ 83,4 s` | `−%2,9` | 3,766 | `−%0,22` |
| W2 (kıyas küre) | `4,199 @ 83,4 s` | `−%3,3` | 4,042 | `−%0,92` |

Üç okuma:

1. **Plato terimi sahneye bağlı.** Bütçedeki `plato = 0,01` **kıyas**
   sahnesinin eğrisinden geliyordu (KAYIT-067 §2b) ve DART sahnesinin
   kalan yolunu karşılamıyor. `plato_olculen_DART = 0,016` olarak
   ölçülmüş terim eklendi; eski satır yerinde kaldı.
2. **Yargı sağlam.** Kilitli `I`, `plato = 0,01` ile `1,4034`;
   `0,016` ile `1,4003`. İkisi de `< 3`. Yargı **değişmiyor** — bu bir
   duyarlılık sınavı, kural değişikliği değil (sınav:
   `test_DY2_yargisi_olculen_plato_terimine_SAGLAM`).
3. **`t_end = 600 s` savunulabilir, ama ucu ucuna.** Kalan `%1,64`
   bütçeye **ölçülmüş terim olarak** girdi. `t_end`'i uzatmak `β`'yı
   `3,748 → ~3,703` indirir, yani gözleme **yaklaştırır**; bu yönde
   olduğu için havuzu bekletmeye gerek yok. A110 **kapandı**
   (ölçülerek, uzatılarak değil).

> Elipsoidin kıyas küresinden `3` kat yavaş oturması da §3'ün resmine
> uyuyor: basık cisimde ejekta uzun süre **bağlı** yörüngelerde kalıyor
> (koni `85°` vs `125°`), geri düşenler `β`'yı yavaşça aşağı çekiyor.

## 6. Bütçenin durumu (ödünç → ölçülmüş)

| terim | ödünç | **ölçülmüş** | nerede |
|---|---|---|---|
| `cozunurluk_uzak` | `0,15` | **`0,004`** | KAYIT-067 (UA) |
| `gerceklem_beta` | — | **`0,033`** | KAYIT-070 (U/V, iki tohum) |
| `gerceklem_M_ejekta` | — | **`0,15`** | KAYIT-070 |
| `hedef_sekli` | `0,20` | **`0,009`** | **bu kayıt** (DY2/DK) |
| `plato` | `0,01` (kıyas) | **`0,016`** (DART) | **bu kayıt** (A110) |
| `gecis_ani` | — | **`0,187`** → üretim `1,0 s` ile düştü | KAYIT-071 (UG) |
| `cozunurluk_yakin` | — | **`0,053`** | KAYIT-071 (UY2) |
| `mermi_geometrisi` | `0,15` | **DM koşuyor** | PROTOKOL-DY §7 |
| `gerceklem_beta` (DART sahnesi) | `0,033` (eski model) | **DT koşuyor** | PROTOKOL-DY §7 |
| `carpma_yeri` | `0,10` (L12) | ölçülmedi | A109/C1 kararı bekliyor |
| `carpma_acisi` | `0,05` | ölçülmedi | kapsam dışı (§2) |

İki terim kaldı (`carpma_yeri`, `carpma_acisi`) ve ikisi de **kullanıcı
kararı** bekliyor, GPU değil.

## 7. Maliyet ve dürüst değerlendirme

`1583605_0/1`: `4:50:53` + `4:48:52` → **`~9,7 GPU-saat`**.

- **İyi:** projenin merkezî sorusu ilk kez olumlu cevap verdi ve ikinci
  gözlemli (`M_ejekta`) de `1,2σ` içinde. İki ödünç bütçe terimi ölçülmüşe
  döndü. Şekil betimleyicileri iddiası **ölçümle** doğrulandı.
- **Dikkat:** `β` gözlemin üstünde; "ulaşıyor" dar bir bant kararı değil,
  büyük paydalı bir bant kararı. Posteriorun işi bundan sonra başlıyor.
- **Dürüstlük:** literatürün şekil iddiasını **doğrulayamadık** ve bunu
  kaydettik. Kilitli yorum "küre savunulabilir" diyordu; `β` için öyle,
  başka hiçbir gözlemli için değil — kuralı değiştirmeyip **not** düştük.
- **Kalan risk:** `carpma_yeri = 0,10` bütçenin **en büyük** terimi ve
  hâlâ ödünç (L12). `25 m` kaçıklık `--nisan` ile ölçülebilir; ölçülmezse
  posteriorun paydası literatürün sayısına dayanır.
