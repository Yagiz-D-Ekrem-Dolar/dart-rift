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

## 5. Kilitli yargılara etkisi — YOK

S6'nın kilitli tablosuna **dokunulmadı** (kural 5: düzeltme NOT olarak
eklendi). `SONUC-E-F`'in mekanizma ölçümü de olduğu gibi duruyor;
ölçülen şey **başka bir yapılandırmadır**, onun yanlış olduğu değil.
`n_yön = 1`, tarih eşlemesi, SBC, iki mühürlü ön kayıt **etkilenmez**.
