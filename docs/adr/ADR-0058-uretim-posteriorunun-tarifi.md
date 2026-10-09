# ADR-0058 — Üretim posteriorunun tarifi: GP + heteroskedastik olabilirlik + **ölçülmüş** korelasyon + SBC kapısı

**Durum:** **KABUL EDİLDİ** (2026-10-05) · **Karar:** kullanıcı kararı Claude'a devretti (*"kararları sen ver ve düzgün ver"*, 2026-10-05); gerekçe ve geri alma koşulu KAYIT-075'te · **Tarih:** 2026-10-05
**Öncül:** **A115** (teşhis 2026-10-05'te düzeltildi), ADR-0051 §2b/§2c,
ADR-0053 (`M_ejekta` ikinci gözlemli), ADR-0054 (hedef `β`),
KAYIT-073 (`β = K·M·v·kos/p`), KAYIT-074 (ölçülmüş gerçeklem terimleri)
**Kod:** `inference/gp_vekil.py`, `inference/posterior.grid_posterior_hetero`,
`inference/kalibrasyon.py` — **hepsi var, birlikte hiç kullanılmadı**
**Sınav:** `scripts/prova_cikarim.py`, `tests/test_prova_cikarim.py` (10)

> **NOT (2026-10-09) — EKSİK MADDE, [ADR-0059](ADR-0059-cok-dogruluklu-vekilin-geri-alinmasi.md) ile tamamlandı.**
> Bu ADR yazılırken **çok doğruluklu vekil** (UY2 + KAYIT-071 satır 22
> ile kilitli) düşürüldü — aşağıda ne kararlarda ne de reddedilen
> seçeneklerde geçiyor, yani reddedilmiş değil **unutulmuş**.
> Çözünürlük farkı burada yalnız `σ_model` **varyans** terimi olarak
> taşınıyor (`cozunurluk_yakin = 0,053`); oysa PROTOKOL-M/U0 kaba→orta
> geçişinde `β` için `−%13` ölçmüştü. Varyans bir **kaymayı** yutmaz.
> ADR-0059 iç içe `12` ince nokta ekliyor ve posterioru **iki yolla**
> (`SIGMA` = bu ADR, değişmeden · `CD` = düzeltilmiş) hesaplatıp yan
> yana raporlatıyor. **Aşağıdaki hiçbir satır geçersiz değildir**;
> `SIGMA` yolu olduğu gibi durur.

---

## 1. Niçin havuzdan önce

Posteriorun tarifi havuz **koştuktan sonra** seçilirse, seçim sonuca göre
yapılmış olur. Prova (`prova_cikarim.py`) hattı sentetik veriyle uçtan uca
koşturdu ve üç şey ölçtü. Bu ADR o ölçümleri **tarif** haline getiriyor.

## 2. Ölçülen (A115 düzeltmesi, `n_sbc = 200`)

| senaryo | vekil | `α_b` | `Y₀` | `f` |
|---|---|---|---|---|
| `ayrik` | ikinci derece | KALİBRE | **AŞIRI TEMKİNLİ** | KALİBRE |
| `ayrik` | **GP + Bachoc** | KALİBRE | **KALİBRE** | KALİBRE |
| `ayrik` | tam model (vekil yok) | KALİBRE | KALİBRE | KALİBRE |
| `dejenere` | ikinci derece | KALİBRE | **AŞIRI TEMKİNLİ + YANLI** | DÜZGÜN DEĞİL |
| `dejenere` | GP + Bachoc | KALİBRE | **YANLI** | YANLI |
| `dejenere` | tam model | KALİBRE | KALİBRE | KALİBRE |

Üç okuma: **(i)** posterior makinesi doğru (tam modelle kusursuz kalibre),
**(ii)** GP ikinci derece vekilden iyi, **(iii)** dejenere yönde kalan
**yanlılık** varyans kalibrasyonuyla çözülmez (ızgara da değil:
`n_grid` `24/40/60` → `D = 0,111/0,109/0,110`).

## 3. Yeni ölçüm — **gözlemliler bağımsız değil ve `R = I` almak pahalı**

KAYIT-073 kanıtladı: `β − 1 = K · M_kaçan · v_ort · kos_ort / p`. Yani `β`
ile `M_ejekta` **aynı ejekta alanından** türüyor; artıkları korelasyonlu
olmak **zorunda**. `grid_posterior_hetero` korelasyon matrisi `R` alıyor;
provada `R = I` kullanıldı. Bedeli ölçüldü (`ayrik`, tam model, `n_grid = 30`):

| `ρ(β, M_ejekta)` | daralma `α_b` | daralma `Y₀` | daralma `f` | `Y₀` %68 genişliği |
|---|---|---|---|---|
| `0,00` | **`+0,372`** | `+0,899` | `−0,060` | `0,1974` |
| `0,50` | **`+0,547`** | `+0,896` | `−0,064` | `0,1989` |
| `0,80` | **`+0,708`** | `+0,893` | `−0,068` | `0,2010` |
| `0,95` | **`+0,805`** | `+0,892` | `−0,069` | `0,2021` |

**Beklediğimin tersi çıktı ve ölçüm kazandı.** "Korelasyonlu gözlemlileri
bağımsız saymak bilgiyi şişirir" diye bekliyordum; `Y₀` için öyle
(`0,899 → 0,892`, ihmal edilebilir), ama `α_b` için **tam tersi**:
`ρ` arttıkça `α_b`'nin daralması **iki kattan fazla** artıyor
(`0,372 → 0,805`).

Sebebi anlaşılır: korelasyon arttıkça iki gözemlinin **farkı** keskin
kısıtlanan bir birleşim olur (ortak kısım çıkar gider) ve `α_b` tam o
fark yönüne biniyor. Yani `R = I` almak bilgiyi **şişirmiyor, yanlış yere
dağıtıyor**: fark yönünü hafife alıyor.

> Sonucu: **`α_b`'nin çıkarılabilir olup olmaması `R`'ye bağlı.** `R = I`
> ile "zayıf" (`0,37`), ölçülmüş `ρ ≈ 0,8` ile "öğrenildi" (`0,71`).
> `R`'yi varsaymak, projenin ikinci parametresi hakkındaki sonucu
> varsaymak olur.

## 4. Karar (öneri) — üretim posteriorunun **kilitli** tarifi

1. **Vekil: GP** (`gp_uydur`) + **Bachoc grup-CV varyans kalibrasyonu**
   (`gp_varyans_kalibre`, `yalniz_buyut=True`), gözlemli başına ayrı.
   Gruplar: tasarım noktalarının `θ`-grupları (4 kat).
   Gerekçe: §2(ii). İkinci derece vekil `Y₀`'yu aşırı temkinli yapıyor.
2. **Olabilirlik: `grid_posterior_hetero`**, `θ`'ya bağlı varyans
   (`GP öngörü varyansı + σ_gözlem² + σ_model²`) ve **ölçülmüş** `R`.
   Gerekçe: GP'nin varyansı veriden uzak köşelerde büyür; sabit varyans
   bunu gizler. `log det S(θ)` terimi atılmaz (fonksiyonun kendi notu).
3. **`R` ÖLÇÜLÜR, varsayılmaz.** Kaynağı: havuzun kendi vekil artıkları
   (`β` ve `M_ejekta` artıklarının örnek korelasyonu, `θ`-gruplu CV ile).
   Ölçülemezse — ki ölçülebilir — posterior **iki ayrı `ρ` ile** koşulur
   (`0` ve ölçülen üst sınır) ve ikisi **yan yana** raporlanır.
4. **Gözlemliler:** `β` ve `M_ejekta` (ADR-0053). Hedefler: ADR-0054
   (`β = 3,5418 (+0,188/−0,247)`) ve L17 (`1,6 ± 0,3e7`).
   `σ_model` terimleri **ölçülmüş** olanlardan (KAYIT-072/073/074).
   `krater_derinlik` posteriora **girmez** (DART onu görmedi; ADR-0055).
5. **SBC KAPISI (en önemli madde).** Posterior, **gerçek vekille** koşulan
   SBC'de her eksende `KALİBRE` ya da `DÜZGÜN` vermeden **yayımlanmaz.**

   | SBC sonucu | yapılacak |
   |---|---|
   | hepsi `KALİBRE`/`DÜZGÜN` | posterior yayımlanır |
   | bir eksen `AŞIRI TEMKİNLİ` | yayımlanır, **"muhafazakâr"** etiketiyle (iddia küçülür, yanlış olmaz) |
   | bir eksen **`YANLI`** | **yayımlanmaz.** Tasarım sıkılaştırılır (sırt boyunca nokta) ya da tek posterior yerine `tarih_esleme` (Vernon) ile eleme yapılır |

   Sınav hazır: `scripts/prova_cikarim.py --vekil gp`. Havuz verisiyle
   aynı betik koşar.
6. **Tanımlanabilirlik raporu zorunlu ek** (ADR-0051): daralma, profil,
   Fisher yönleri. İki gözemliyle en çok iki yön öğrenilir; **`f_boulder`'ın
   önsel-baskın çıkması beklenen sonuçtur**, kusur değil — ve öyle yazılır.

## 5. Ne **iddia edilmeyecek**

- "Üç parametreyi çözdük." İki gözemliyle en çok iki yön (ADR-0051 §2c,
  prova doğruladı: üçüncü Fisher özdeğeri **tam sıfır**).
- "`α_b` şu değerdir." `α_b`'nin daralması `R`'ye güçlü bağlı (§3);
  `R` ölçülmeden `α_b` hakkında sayı verilmez.
- "Posterior kalibre." SBC geçmeden bu cümle kurulmaz.

## 6. Reddedilen seçenekler

- **İkinci derece vekille devam etmek.** Ölçüldü: `Y₀` aşırı temkinli
  çıkıyor. GP aynı veriyle daha iyi ve maliyeti ihmal edilebilir
  (`96` nokta).
- **`grid_posterior` (sabit varyans) kullanmak.** GP'nin `θ`'ya bağlı
  varyansını atar; veriden uzak köşelerde yapay kesinlik üretir.
- **`R = I` ile yetinmek.** §3'te ölçüldü: `α_b` sonucunu belirliyor.
- **SBC'yi havuzdan sonra "kontrol" olarak koşmak.** Kapı olmayan bir
  denetim, sonucu değiştirmediği için denetim değildir. Kapı olmalı ve
  **koşudan önce** yazılmalı — bu ADR onu yapıyor.
- **`YANLI` çıkarsa paydayı büyütüp geçmek.** Yanlılık bir kaymadır;
  paydayı büyütmek kaymayı gizler, düzeltmez (A115 (c)3).
