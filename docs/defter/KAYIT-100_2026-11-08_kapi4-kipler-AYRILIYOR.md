# KAYIT-100 — ADR-0059 **dördüncü kapı**: kipler AYRILIYOR; çözünürlük seçimi `Y₀` kestirimini **8,6 kat** kaydırıyor

**Tarih:** 2026-11-08 · **Sıfır GPU** (yalnız depodaki iki CSV)
**Betik:** `scripts/cd_posterior.py`
**Kapı:** [ADR-0059](../adr/ADR-0059-cok-dogruluklu-vekilin-geri-alinmasi.md) §3.4–§3.5 — **burada seçilmedi**
**Öncül:** [KAYIT-099](KAYIT-099_2026-11-08_cok-dogruluklu-duzeltme-baglandi.md)

---

## 1. Niçin

KAYIT-099 ADR-0059 §3.4'ün ilk üç maddesini geçti ve dördüncüyü
**ÖLÇÜLMEDİ** diye bıraktı: o madde tam posterioru **iki yolla**
koşmayı gerektiriyordu. Bu kayıt onu ölçer.

## 2. Tek değişken ilkesi

İki yol **tek koşuda** hesaplandı. Tasarım, ADR-0060 gözlenebilir
dönüşümü, `R`, `σ_model`, ızgara ve olabilirlik **aynı nesnelerdir**;
değişen tek şey vekilin ortalamasıdır.

`CD` yolunun kaba katmanı, `SIGMA`'nın kullandığı **Bachoc kalibreli
GP'nin kendisiyle** değiştirildi. Sebebi: `gp_varyans_kalibre` yalnız
varyansı ölçekler, ortalamayı değiştirmez — dolayısıyla `ρ` ve `δ`
geçerli kalır ve iki yol **yalnız düzeltmede** ayrışır. Aksi hâlde
kipler arasındaki farkın düzeltmeden mi kalibrasyondan mı geldiği
bilinemezdi.

| | `ρ` | uyarı |
|---|---:|---|
| `β` kolu | `0,7000` | yok |
| `log M_ejekta` kolu | `1,1800` | yok |

İkisi de `0 – 2` ızgarasının **içinde**.

## 3. Ölçüm

Kip, ızgara posteriorunun en olası düğümü; `σ`, `SIGMA` posteriorunun
birim küpteki kendi `std_u`'sudur.

| eksen | `SIGMA` | `CD` | `\|Δkip\| / σ_SIGMA` |
|---|---:|---:|---:|
| `α_b` blok gözenekliliği | `1,2695` | `1,0356` | **`2,743`** |
| **`Y₀` matris dayanımı** | **`18,67` Pa** | **`159,73` Pa** | **`1,881`** |
| `f` blok kesri | `0,0500` | `0,0500` | `0,000` |

> **KAPI 4: KİPLER AYRILIYOR.** Eşik `1σ`; iki eksende aşıldı.

## 4. Yargı

ADR-0059 §3.4: *"iki yolun kipleri — ayrılıyorsa **ikisi de**
manşette."* §3.5: *"`≥ 1σ` ayrılırsa bu bir **bulgu**dur, gizlenmez."*

> **Dört maddenin dördü de değerlendirildi. Kipler ayrıldığı için
> `SIGMA` ve `CD` yollarının İKİSİ DE manşettedir**, ve §3.5'in
> istediği cümle şudur:
>
> **Çözünürlük seçimi, matris dayanımı kestirimini `18,7 Pa`'dan
> `159,7 Pa`'ya — yaklaşık `8,6` kat — kaydırıyor.**

Eşik değiştirilmedi, madde atlanmadı.

## 5. Bu, ADR-0059'un ÖNGÖRDÜĞÜ şeyin gerçekleşmesidir

ADR-0059 §2 veriyi görmeden şunu yazmıştı:

> *"`σ` yaklaşımı posterioru genişletir ama kaba öngörünün merkezinde
> bırakır. Fark sistematik bir kaymaysa, `θ` o kaymayı emmek zorunda
> kalır — yani yanlış bir iç yapıya, doğru bir `β` ürettiği için
> inanırız."*

Ölçülen tam olarak budur. KAYIT-099 farkın sistematik olduğunu
gösterdi (`9/9`, `p = 0,00195`); bu kayıt o kaymanın `θ`'ya **nereye**
gittiğini gösteriyor: `Y₀`'a.

Ve dikkat: `Y₀`, tasarımın **tek öğrenilebilir yönü**dür (KAYIT-097,
payı `0,999`). Yani çözünürlük kayması, posteriorun **tek bilgi taşıyan
ekseninde** birikiyor. Öğrenilemeyen eksende kayma olsaydı önemsizdi;
öğrenilen eksende olması bu bulguyu ciddi kılıyor.

## 6. Bu ne demek DEĞİL

- **`Y₀ = 159,7 Pa` doğru cevap değildir.** Orta katman da yakınsamış
  değildir (PROTOKOL-M: **YAKINSAMIYOR**, farklar inceldikçe büyüyor).
  `CD` *"bir kademe daha ince koşulsaydı ne çıkardı"* der. Bir sonraki
  kademe `Y₀`'ı yine kaydırabilir ve bugünkü veri hangi yöne diyemez.
- **İki sayıdan biri seçilemez.** ADR-0059 ikisini de manşete
  koyuyor; aralarından birini seçmek, kuralın yasakladığı şeydir.
- **`α_b` ve `f` kipleri okunmamalıdır.** İkisi de önsel kenarına
  yapışık (`α_b → 1,0`; `f = 0,05`, aralığın alt ucu) ve `n_yön = 1`
  yargısıyla tutarlı olarak önsel baskın. `α_b`'deki `2,74σ` kayma,
  kenara yapışmış bir kipin kayması olduğu için **büyüklüğü
  abartmalıdır**; yargı `Y₀` üzerinden okunmalıdır.
- **Tasarım tam değil.** `12` nokta planlanmış, `9`'u koşulmuştur
  (`78, 87, 92` iptal); kenarlarda `δ(x)` ölçülmedi.

## 7. VARSAYIM — açıkça

ADR-0060 gereği vekil `(β−1)/cos²`'ye uyduruluyor. İnce koşuların `kos`
sütunu **kaydedilmedi**; ince noktaların dönüşümünde **kaba koşunun
`kos`'u** kullanıldı.

İki yol da aynı `kos`'u kullandığı için karşılaştırmayı bozmaz, ama
`CD`'nin **mutlak** değerine girer. `kos` çözünürlükle değişiyorsa
`159,7 Pa` da kayar. Bunu kapatmak için ince koşuların `kos`'u
kaydedilmeli — ileriye dönük bir düzeltme, geçmişe dönük
hesaplanmaz.

## 8. Yeniden üretme

```
python scripts/cd_posterior.py docs/sonuclar/havuz_posterior_girdi.csv \
    --ince docs/sonuclar/ince/ince_96.csv \
    --json docs/sonuclar/cd_posterior.json
```
