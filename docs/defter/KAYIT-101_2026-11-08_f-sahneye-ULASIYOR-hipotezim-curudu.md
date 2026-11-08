# KAYIT-101 — `f` kazı bölgesine **ULAŞIYOR**: §11.5'in açıklaması da benim hipotezim de çürüdü

**Tarih:** 2026-11-08 (ölçüm 2026-11-06) · **Sıfır GPU** (yalnız sahne kurucusu)
**Betik:** `scripts/tani_f_sahne_tohum.py` (kapıları koşudan önce yazılı)
**Veri:** `docs/sonuclar/tani_f_sahne_tohum.json`
**Öncül:** [KAYIT-097](KAYIT-097_2026-11-05_esdogrusallik-96-noktada-olculdu.md),
`LITERATUR-DART-SIMULASYONLARI.md` §11.5, A74, A109

---

## 1. Niçin

KAYIT-097 blok kesri `f`'in öğrenilen yöndeki payını `q90`'da bile
`0,045` ölçtü: `β`, `f`'i **görmüyor**. §11.5 bunun sebebini
*"yerleşim gürültüsü + tek tohum"* diye yazdı.

**Ama bu ölçülmemişti.** Bir hipotezdi ve raporun en zayıf iddiası oldu.
Üstelik iki birbirini dışlayan açıklama vardı:

- **H1 (gürültü):** `f` kazı bölgesine ulaşıyor ama tek tohumla etkisi
  yerleşim saçılmasından ayrılamıyor. §11.5'in yazdığı şey.
- **H2 (yapılandırma):** `f` kazı bölgesine **hiç** ulaşmıyor; eklenen
  hacim çekirdeğe gidiyor. O zaman körlük fizik değil **bizim sahne
  kurulumumuzun kusuru**dur.

Koşudan önce ikisi de kapıya bağlandı. Benim beklentim **H2**'ydi.

## 2. Tasarım

Üretim sahnesi birebir (`88,5×87,0×58,0 m` elipsoit, `r ∈ [14, 56] m`,
`q = 3`, `blok_uretici = v1`, çarpma `17°`, `aim = (0,0,1)`).
`8` adet `f` değeri × `16` tohum = **128 sahne**, yalnız blok alanı
üretildi; çözücü koşmadı. Küre–küre kesişim hacmi **kapalı formdur**,
pay Monte Carlo gürültüsü taşımaz.

## 3. YARGI — ikisi de değil

| kapı | ölçülen | sonuç |
|---|---|---|
| G1 akıl sağlığı: `ρ(f, f_gerçek) ≥ 0,90` | `+1,000` | GEÇTİ |
| G2 `f` kazı bölgesine ulaşıyor mu (`R = 28 m`) | `ρ = +1,000`, `D = 1,598` | **ULAŞIYOR ve tek tohumda AYIRT EDİLEBİLİR** |

`D ≥ 1,0` eşiği aşıldı. Yani:

> **H1 de H2 de doğrulanmadı.** `f` kazı bölgesine ulaşıyor **ve** tek
> tohumda ayırt edilebiliyor. §11.5'in *"yerleşim gürültüsü"*
> açıklaması **desteklenmedi**; benim H2 beklentim de tutmadı.
> Körlüğün sebebi sahnede değil — **çözücüde ya da gözlenebilirde**
> aranmalı.

Eşik sonucu görmeden yazılmıştı ve değiştirilmedi. `D = 1,598` eşiği
geçiyor ama **rahat geçmiyor**: `D = 3` için `θ` başına `4` tohum
gerekirdi (`M*`).

## 4. Ama sahnede İKİ gerçek kusur ölçüldü

Yargı sahneyi aklamıyor. Aynı koşu iki şeyi daha ölçtü:

### 4.1 Bloklar çekirdeğe sürülmüş — G3 DÜŞTÜ

| | değer |
|---|---|
| kabuk (`s ≥ 0,75`) hacim payı | `0,578` |
| blokların kabuktaki payı / beklenen | **`0,064`** |
| kapı | `< 0,50` → **DÜŞTÜ** |

Bloklar, yansız dağılımda olmaları gerekenin **%6,4'ü** kadar kabukta.
Sebebi v1'in kabul şartı: *"blok TAMAMEN mesh içinde olmalı."* Büyük
bloklar yapı gereği merkeze sürülüyor.

### 4.2 Çarpma noktası hiçbir sahnede blokla kaplı değil

`carpmada_blok`: **`0/128`**. Bu bir istatistik değil, analitik bir
sonuç: çarpma noktası **yüzeydedir** ve v1 bloğun tamamen içeride
olmasını ister; bir blok yüzey noktasını ancak **tam teğetlikle**
içine alabilir, olasılığı sıfırdır.

Sonuç: Protokol L'nin ölçtüğü *"bloğa çarpma"* dalı (`β−1 ≈ 0,03`,
matriste `≈ 0,5`) üretim havuzunda **yapı gereği hiç gerçekleşmiyor**.

## 5. Ve `f` düğmesi doyuyor — A74 üretim yapılandırmasında doğrulandı

| `f` istenen | `0,050` | `0,114` | `0,179` | `0,243` | `0,307` | `0,371` | `0,436` | `0,500` |
|---|---|---|---|---|---|---|---|---|
| **gerçekleşen** | `0,151` | `0,157` | `0,204` | `0,258` | `0,312` | `0,360` | `0,369` | `0,369` |

Tasarım `0,05 – 0,50` istiyor; sahnede yalnız **`0,151 – 0,369`**
gerçekleşiyor. `f ≥ 0,436`'da sahneler **bit-aynı** (`yaricap_maks`
sinyali tam sıfır, `D = 0`).

A74 bunu `r ≤ 42` ile **48 noktalık** tasarımda ölçmüştü; bu kayıt
üretim yapılandırmasında (`r ≤ 56`, `96` nokta) doğruluyor.

## 6. Ne değişti, ne değişmedi

- **§11.5'in açıklaması düzeltilmeli.** *"Yerleşim gürültüsü"* cümlesi
  ölçümle desteklenmedi. Oraya bu kayda işaret eden bir NOT düşülecek;
  §11.5'in metni **silinmeyecek** (kural 4).
- **KAYIT-097'nin ölçümü değişmedi.** `f`'in payı hâlâ `q90`'da
  `0,045`. Değişen, *sebebi* hakkındaki açıklama.
- **A74 ve A109 açık kalır.** Bu kayıt onları kapatmaz, üretim
  yapılandırmasındaki sonuçlarını ölçer.
- **Yeni açık soru:** `f` sahneye ulaşıyorsa ve `β` onu görmüyorsa,
  kayıp nerede? Çözücüde mi (blok–matris etkileşimi), gözlenebilirde
  mi (`β`'nın tanımı)? Ölçülmedi.

## 7. Dürüstlük notu

Bu ölçümü **H2'yi doğrulamak için** kurdum ve H2 çıkmadı. Kapı koşudan
önce yazıldığı için beklentimi sonuca uyduramadım; eşik de
değiştirilmedi. Kayıt, yanıldığım hâliyle duruyor.

## 8. Yeniden üretme

```
python scripts/tani_f_sahne_tohum.py --cikti docs/sonuclar/tani_f_sahne_tohum.json
```
