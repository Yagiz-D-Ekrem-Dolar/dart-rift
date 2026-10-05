# KAYIT-074 — Bütçenin son iki ödünç terimi ölçüldü; `β`'nın gerçeklem saçılması **2,5 kat küçüldü** (2026-10-05)

**Kapsam:** PROTOKOL-DY §7 (DM = tek küre mermi, DT = ikinci sahne tohumu) ·
**Durum:** iki kilitli ölçüm okundu, bir yan ölçüm, **A114 canlı doğrulandı** ·
**Kaynak:** `docs/olcumler/DM_DT_2026-10-05/`,
[PROTOKOL-DY §7](../truba/PROTOKOL-DY-DART-GEC-EVRE.md) ·
**Öncül:** [KAYIT-072](KAYIT-072_2026-10-04_DY2-model-gozleme-ulasiyor.md),
[KAYIT-073](KAYIT-073_2026-10-04_beta-nin-uc-carpani-goturme.md)

---

## 1. Üç kol yan yana

| | DY2 (üç küre, tohum 1) | **DM** (tek küre) | **DT** (tohum 2) |
|---|---|---|---|
| `β` (600 s) | **3,7480** | **4,1153** | **3,7999** |
| `β_km` | 3,8216 | 4,2128 | 3,8337 |
| `M_ejekta` | 1,964e7 | 2,346e7 | **2,357e7** |
| koni tam açısı | 85,2° | 91,2° | 90,7° |
| `t50` | 0,541 s | 0,625 s | **0,702 s** |
| `β∞` (`1/t`) | 3,703 | 4,067 | 3,780 |
| parçacık | 15 623 | 15 652 | 15 623 |
| kütle tutarlılığı | `−%0,05` | `−%0,05` | `−%0,04` |
| enerji sapması | `−%0,78` | `−%0,74` | `−%0,79` |

Her iki koşu da `COMPLETED`, `~5 GPU-saat`/kol, bütün denetimler geçti.

## 2. Kilitli ölçüm 1: `σ_mermi = 0,134`

PROTOKOL-DY §7.3: `σ_mermi = |b_DY2 − b_DM| / b_DY2`.

    |2,7480 − 3,1153| / 2,7480 = 0,1337

**Tek küre mermi, `β`'yı `%9,8` YÜKSELTİYOR** (3,748 → 4,115). Yani
mermiyi tek bir yoğun topa indirmek momentum aktarımını artırıyor —
kütlesi aynı olmasına rağmen. Fizik okuması: tek küre daha derin ve daha
yoğun bir bağlaşım bölgesi açıyor; üç küre (`%88 + 2 × %6`, `2,215 m`
aralıklı) enerjiyi daha geniş bir alana yayıyor.

**L9'un ödünç `0,15`'i iyi bir üst sınırdı** (ölçülen `0,134`, `%11`
yakın). Bu, önceki üç ölçümün (`hedef_sekli` 22 kat küçüldü, `plato`
büyüdü, `cozunurluk_uzak` 37 kat küçüldü) aksine, literatürden alınan
sayının **tutmasına** bir örnek — ve bunu da yazmak gerekiyor.

### Bu terim paydaya **GİRMİYOR** ve niçin

ADR-0056'nın A105 için kurduğu mantık burada da geçerli:
**tek küre, gerçeğin bir alternatifi değil, DAHA KABA bir yaklaşımdır.**
Gerçek DART uzay aracı dağıtılmış kütleli bir yapı; üç küre onu tek
küreden **daha iyi** temsil ediyor. Dolayısıyla kalan belirsizlik "üç küre
ile gerçek uzay aracı arasındaki fark"tır ve bu, ölçtüğümüz "üç küre ile
tek küre arasındaki fark"tan **küçüktür**.

`0,134` bir **üst sınır** olarak kaydedildi
(`mermi_geometrisi_olculen`), PROTOKOL-DY'nin `TERIMLER` listesine
**eklenmedi** ve sınavla kilitlendi
(`test_mermi_olculen_terimi_PROTOKOL_DY_paydasina_GIRMEZ`).

> Eklenirse ne olurdu: payda `0,447 → 0,574`, `I` `1,40 → 1,09`. Yani
> sınavı **kolaylaştırırdı**. Kendi sınavını kolaylaştıran bir terim,
> dürüstlük değil. Yan yana sayı olarak kayıtta duruyor.

## 3. Kilitli ölçüm 2: `σ_gerçeklem(β, DART) = 0,013`

PROTOKOL-DY §7.3: `|b₁ − b₂| / ortalama(b) / √2`.

    |2,7480 − 2,7999| / 2,7740 / √2 = 0,0132

**Eski değer `0,033` idi** (U/V havuzu, **eski model**, `0,1–0,2 s`).
Geç evre modelinde ve DART sahnesinde **2,5 kat küçüldü**.

Bu iyi bir haber ve sebebi anlaşılır: `0,1 s`'de `β` hâlâ hızla
değişiyor ve blok diziliminin yerel ayrıntısına duyarlı; `600 s`'de
ejekta bütünleşmiş ve tek tek blokların yeri önemini yitirmiş.
**Tek gözleme aşırı uyma (overfit) tabanı düştü** — posterior `β`'dan
daha fazlasını çıkarabilir.

## 4. Yan ölçüm: `M_ejekta`'nın saçılması **küçülmedi**

Aynı tohum çifti, `M_ejekta` için:

    |1,964e7 − 2,357e7| / 2,160e7 / √2 = 0,129      (eski model: 0,15)

| gözlemli | eski model | **DART, geç evre** | değişim |
|---|---|---|---|
| `β` | `0,033` | **`0,013`** | `2,5` kat **küçüldü** |
| `M_ejekta` | `0,15` | **`0,129`** | neredeyse aynı |
| `t50` (tanı) | — | **`0,183`** | — |

**Okuma:** geç evre modeli `β`'yı tohumdan tohuma kararlı kılıyor, ama
**kaçan kütleyi** kılmıyor. KAYIT-073'ün ayrıştırmasıyla birlikte bu
tutarlı: `β = K·M·v·kos/p` ve tohum değişince `M` ile `v` ters yönde
oynuyor, çarpımı sabit kalıyor. Yani `β`'nın kararlılığı bir **götürme**
daha — bu kez gerçeklem ekseninde.

> ADR-0053'ün `M_ejekta` kazancı etkilenmiyor: oradaki
> `σ_M = hypot(0,1875 ; 0,15) = 0,240` yerine ölçülen
> `hypot(0,1875 ; 0,129) = 0,228` gelir; çarpan `×1,96 → ×1,91`,
> `β`'ya göre kazanç `6,3 → 6,5` kat. Sonuç **güçleniyor**.

**Ama `t50`'nin saçılması `0,183`** — yani KAYIT-072 §3'ün "iki kol
`t50`'de `2,6` kat ayrışıyor" bulgusu sağlam (2,6 kat ≫ %18), ama
`t50`'yi tek koşudan okumak `%18` gürültü taşıyor. Mekanizma tanısı
olarak kullanılırken bu yazılmalı.

## 5. A114 **canlı doğrulandı**

DM'nin ensemble kaydı:

```
{"i": 0, "y": null, "hata": "carpma ekseni kutusunda 3 parcacik var
 (en az 5 gerekir) ... Yuzey parcacigi 8538, n_bins=8."}
```

DT'nin kaydı tam. Yani DART sahnesinin **üç** koşusundan **ikisi**
(`DY2`, `DM`) vekile girecek `y` vektörünü üretmedi — A114'ün "kabaca
yarısı" kestirimi **iyimserdi**.

Ölçümler etkilenmedi çünkü `dy_dart_raporu` sayıları `npz`'nin
`fizik_tani`'sından okuyor. Ama **havuz `jsonl`'in `y`'sini kullanacaktı.**
ADR-0055 (1) olmadan bu tur `~650 GPU-saat`'in `%60`'ını götürürdü.

## 6. Bütçenin durumu — **ödünç terim kalmadı** (ikisi hariç)

| terim | ödünç | **ölçülmüş** | nerede |
|---|---|---|---|
| `cozunurluk_uzak` | `0,15` | **`0,004`** | KAYIT-067 |
| `cozunurluk_yakin` | — | **`0,053`** | KAYIT-071 (UY2) |
| `gecis_ani` | — | **`0,187`** → üretim `1,0 s` ile düştü | KAYIT-071 (UG) |
| `hedef_sekli` | `0,20` | **`0,009`** | KAYIT-072 |
| `plato` | `0,01` (kıyas) | **`0,016`** (DART) | KAYIT-072 (A110) |
| **`mermi_geometrisi`** | `0,15` | **`0,134`** (üst sınır) | **bu kayıt** |
| **`gerceklem_beta`** | `0,033` (eski model) | **`0,013`** | **bu kayıt** |
| **`gerceklem_M_ejekta`** | `0,15` | **`0,129`** | **bu kayıt** |
| `carpma_yeri` | `0,10` (L12) | ölçülmedi | A109/C1 kararı bekliyor |
| `carpma_acisi` | `0,05` | ölçülmedi | kapsam dışı (PROTOKOL-DY §2) |

**Kalan iki terim de GPU değil, karar bekliyor.** Model eksikliği
bütçesinin ölçülmüş kısmı artık **sekiz terim**.

## 7. Maliyet ve dürüst değerlendirme

`1588084_0/1`: `05:02:10` + `05:00:57` → **`~10,1 GPU-saat`**.

- **İyi:** iki ödünç terim ölçülmüşe döndü ve biri (`gerceklem_beta`)
  `2,5` kat küçüldü. Literatürün `0,15`'i bu kez **tuttu** — ödünç
  terimlerin hepsi kötü değil, bunu da kaydettik.
- **Dikkat:** tek küre `β`'yı `%9,8` yükseltiyor. Mermi geometrisi
  `carpma_yeri`'nden (`0,10`) **büyük** bir etki ve üç küre seçimi
  L9'dan ödünç. Gerçek uzay aracının kütle dağılımına geçmek (paneller
  ayrı) bir sonraki iyileştirme adayı.
- **Kötü:** A114 tahmin ettiğimden sık çıkıyor (3'te 2). Düzeltme
  uygulandı ama **varsayılan kapalı** — üretim planı `istege_bagli` /
  `nan_izinli`'yi açıkça istemek zorunda, yoksa havuz yine ölür.
- **Açık kalan:** `t50`'nin `%18` gerçeklem gürültüsü, mekanizma
  tanılarının tek koşudan okunmasını zayıflatıyor.
