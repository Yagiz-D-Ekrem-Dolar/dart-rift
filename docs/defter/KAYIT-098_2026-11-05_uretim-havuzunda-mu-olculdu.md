# KAYIT-098 — Üretim havuzunda ejekta üssü `μ` **ölçüldü**

**Tarih:** 2026-11-05 · **Sıfır GPU** (TRUBA `debug`, iş `6917201`, `16 s`)
**Betik:** `scripts/tani_mu_havuz.py` — kapıları koşudan önce yazılı
**Öncül:** `docs/SONUC-E-F-MEKANIZMA.md`, `LITERATUR...` §11.4

---

## 1. Niçin

`README.md` S6 *"`μ = 0,463 ± 0,016`"* diyor. Literatür
karşılaştırması yazılırken (§11.4) bu sayı L1'in `0,36 – 0,39`'uyla yan
yana konuldu ve *"bizim değer üstünde, fark açıklanmadı"* yazıldı.
**Karşılaştırma yanıltıcıydı:** `0,463` **mekanizma çalışmasından**
geliyor, üretim havuzundan değil.

Ayrıca `SONUC-E-F` o dönemin üretim kolu için *"dağılım **yok** — `12`
eşikte `3` farklı kütle değeri (basamak fonksiyonu)"* diyordu. Bugünkü
üretim `--matris-cekme-yok` kullanıyor, yani o uyarı geçerli
olmayabilirdi — **ama kimse bakmadı.**

## 2. Kapılar — koşudan önce

Bir bant ancak **`≥ 8` farklı kütle değeri** ve **`R² ≥ 0,99`** ile
uydurulmuş sayılır. Havuzun yarısından azında hiçbir bant
uydurulamazsa *"üretim havuzunda `μ` ölçülemez"* yazılacaktı.

## 3. Ölçüm — `SONUC-E-F`'in aynı sekiz bandında

| | değer |
|---|---|
| uydurulabilen nokta | **`95/96`** (oran `0,990`) |
| bant başına farklı kütle değeri (ortanca) | **`2 581`** (`750 – 3 183`) |
| **`μ` ortanca** | **`0,4347`** |
| `μ` aralığı | `0,2899 – 0,4567` |

**Yargı: ÜRETİM HAVUZUNDA `μ` ÖLÇÜLEBİLİR.**

## 4. İki düzeltme

**(a) "Basamak fonksiyonu" uyarısı bugünkü üretime uymuyor.** Bant
başına ortanca `2 581` farklı kütle değeri var; `3` değil. O uyarı
`--matris-cekme-yok` öncesi kola aittir.

**(b) S6'nın sayısı üretimi biraz yukarı gösteriyor.**

| | `μ` |
|---|---|
| **üretim havuzu** | **`0,4347`** |
| S6 / mekanizma kolu | `0,463 ± 0,016` |
| L1 (Raducan & Jutzi 2022) | `0,36 – 0,39` |
| Housen–Holsapple | `0,40 – 0,55` |

Üretim değeri H&H aralığının **içinde**, yani S6'nın *"GEÇTİ"*
yargısı **ayakta**. Ama L1'in aralığının hâlâ **üstünde**: fark
`0,463`'e göre daralıyor, **kapanmıyor**, ve sebebi **açıklanmamıştır**.

`μ` havuz boyunca `0,290 – 0,457` arasında geziyor — yani `θ`'ya
bağlı, ki H&H'de de `μ` malzemeye bağlıdır.

## 4.1 Fark niçin kapanmıyor — ve beklenmedik bir bağlantı

`μ`'yü `θ`'ya karşı çözdüm (`95` nokta):

| | |
|---|---:|
| `r(log₁₀ Y₀, μ)` | **`−0,895`** |
| `r(f, μ)` | **`−0,035`** |
| `r(α_b, μ)` | `+0,006` |

Uydurma: **`μ = 0,4914 − 0,0314·log₁₀(Y₀) − 0,0221·f`**, `R² = 0,805`.

Yani bizim `μ`'müzü **`Y₀` yönetiyor**; `α_b` ve `f` neredeyse hiç
etkilemiyor.

### Eşleşmiş parametrede fark BÜYÜYOR

L1'in kendi koşuları `Y₀ = 50 / 10 / 1 / 0` Pa'da, yani **zayıf uçta**.
Bizim o rejimdeki değerimiz:

| kesit | n | `μ` ortanca |
|---|---:|---:|
| `Y₀ ≤ 50` Pa | 32 | **`0,4521`** |
| `Y₀ ≤ 50` Pa **ve** `f ≥ 0,40` (L1'in `f` bandıyla örtüşen) | 7 | **`0,4368`** |
| L1'in ölçtüğü | — | `0,36 – 0,39` |

Fark `%12 – 25` ve **kapanmıyor**. Bizim `μ`'müz L1'in bandına ancak
`Y₀ = 2 116 – 14 248` Pa'da düşüyor — L1'in `Y₀`'ının **`40 – 300`
katı**.

### Ve asıl bulgu: `f` körlüğü `β`'ya özgü DEĞİL

L1 açıkça *"`μ = 0,36 – 0,39` (**`f` arttıkça küçülür**)"* diyor. Bizde
`r(f, μ) = −0,035`, yani **hiç**. Bu önemli, çünkü:

> `β`'nın `f`'i görmemesi (KAYIT-097: payı `q90`'da `0,045`) bir
> **çıkarım** sorunu sanılabilirdi. Ama `μ` bambaşka bir nicelik —
> momentum değil, kütle–hız dağılımının **eğimi** — ve o da `f`'i
> görmüyor. **İki bağımsız gözlenebilir aynı körlüğü paylaşıyor.**
>
> Bu, körlüğün çıkarım makinesinde değil **ileri modelde** olduğunu
> söyler: blok modeli ya da çözünürlüğü. Doğrudan **A109**'u (hangi
> blok modeli üretim — kilitli değil) ve A89'u (blok çözünürlüğü)
> işaret ediyor.

**Hipotez, sonuç değil.** `μ` farkının başka sebepleri de olabilir ve
sınanmadı: bitiş zamanı (`600 s` ile L1'in `30 dk – 2 sa`'i), hedef ve
mermi farkı, ejekta tanımı (bizde radyal `v_r > 0`). Bunlar ayrılmadan
*"blok modeli yüzünden"* denemez.

## 5. Kilitli yargılara etkisi — YOK

S6'nın kilitli tablosuna **dokunulmadı** (kural 5: düzeltme NOT olarak
eklendi). `SONUC-E-F`'in mekanizma ölçümü de olduğu gibi duruyor;
ölçülen şey **başka bir yapılandırmadır**, onun yanlış olduğu değil.
`n_yön = 1`, tarih eşlemesi, SBC, iki mühürlü ön kayıt **etkilenmez**.
