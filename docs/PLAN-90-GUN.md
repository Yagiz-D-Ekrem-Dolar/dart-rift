# 90 günlük plan — havuzdan teslime (2026-10-08 → 2027-01-06)

**Yazıldı:** 2026-10-08 · **Durum:** havuz koşuyor (`1592569`), TRUBA erişimi
kapalı · **Bütçe:** harcanan `418`, havuz `480`, **kalan `602 GPU-saat`** ·
**Öncül:** [KAYIT-077](defter/KAYIT-077_2026-10-07_havuz-gonderildi-ve-uc-parametre-acildi.md),
[PROTOKOL-HAVUZ](truba/PROTOKOL-HAVUZ-URETIM.md),
[KAYIT-075](defter/KAYIT-075_2026-10-05_bes-karar-verildi.md) (beş karar)

---

## 0. Planın mantığı

Üç ilke:

1. **Kritik yol kısa tutulur.** Posterior → Hera mührü → rapor. Bu üçü
   aksarsa proje biter; geri kalan her şey aksarsa yalnız kapsam küçülür.
2. **Sıfır GPU işleri öne alınır.** Kaydedilmiş durum `npz`'leri
   (`x, v, m, rho, alpha, P, S, D, h, cs, strain`) bir **maden**: oradan
   çıkan her ölçüm GPU istemiyor ve TRUBA kapalıyken de yapılabiliyor.
3. **Her yargı kuralı veriden önce yazılır** (kural 6). Bu planın kendisi
   bir yargı değil; yargılar protokollerde.

## 1. Dört kuşak

### 1. kuşak — **sıfır GPU**, kaydedilmiş durumlardan (~1 hafta)

| # | iş | süre | Hera sınar mı | protokol |
|---|---|---|---|---|
| 1 | İki kaçış ölçütüyle `β` (`0,08` vs `0,24 m/s`) + geri düşme | ½ gün | — | PROTOKOL-SI §2 |
| 2 | `β`'yı **yörünge hızı yönüne** projekte et | ½ gün | — | PROTOKOL-SI §3 |
| 3 | **Balistik son işleme** (Didymos çekimi, `11 saat`) | 2-3 gün | — | PROTOKOL-SI §4 |
| 4 | **Spin / açısal momentum değişimi** | 1 gün | **EVET** | PROTOKOL-SI §5 |
| 5 | **Yoğunluk / sıkışma değişimi** | 1 gün | **EVET** | PROTOKOL-SI §6 |
| 6 | **Şekil değişimi** (yarı eksenler) | ½ gün | **EVET** | PROTOKOL-SI §7 |
| 7 | **Önsel duyarlılık analizi** | 1 gün | — | PROTOKOL-UP §5 |
| 8 | **Tarih eşleme (Vernon)** posteriorun yanında | 1-2 gün | — | PROTOKOL-UP §6 |

**4, 5, 6 üç ayrı mühürlü Hera öngörüsü demek** — ödül kartı birden üçe
çıkıyor ve maliyeti sıfır.

### 2. kuşak — ucuz GPU (~25 saat, ~2 gün)

| # | iş | GPU | niçin |
|---|---|---|---|
| 9 | **Çarpma açısı duyarlılığı** (`17° ± 7°`) | `~10` | bütçedeki **SON ödünç terimi** kapatır |
| 10 | Blok modeli karşılaştırması (`14–56` vs `1,7–6,5 m`) | `~10` | A109'un cevabını ölçer |
| 11 | Mermi yoğunluğu duyarlılığı (`1000 kg/m³`) | `~5` | ödünç uygulama |

9'dan sonra: **"model eksikliğinin her terimi kendi kodumuzda ölçüldü."**

### 3. kuşak — planda zaten olanlar (~280 saat)

| # | iş | GPU |
|---|---|---|
| 12 | **Çok doğruluklu vekil** (12 ince nokta, `3,5 m`) | `224` |
| 13 | Hera mührü koşuları (HK + HT) | `60` |
| 14 | **A95 koni düzeltmesi** — ara an kaydıyla neredeyse bedava | `~20` |
| 15 | X→Y yama çalışması | `37` |

**Sinerji:** 13 için yazılacak **ara an durum kaydı** kodu, 14'ün de
çaresi (koniyi `~170 s`'de **konumdan** ölçmek). 14 kapanırsa `θ` için
**dördüncü gözemli** gelir.

### 4. kuşak — kapsam dışı, gerekçesi yazılı

| ne | niçin hayır |
|---|---|
| `μ(I)` granüler reoloji | 2-3 aylık iş |
| Ejekta anizotropisi / filamentler | çözünürlük altı yapı |
| Tam N-cisim + parçacık çarpışmaları | balistik yaklaşım yeterli; literatür de öyle |
| `1 cm` çözünürlük | `54 milyon GPU-saat` (eşleştirme şartı) |

## 2. Takvim

| hafta | iş | bağımlılık |
|---|---|---|
| **1-2** | **1. kuşak** (sıfır GPU) · PROTOKOL-UP, SI, XY · `R` kestiricisi · ADR-0058 düzeltmesi · A116 · havuz okuma raporu | havuz koşuyor |
| **3** | Havuz biter → aday gözlemliler + tutarlılık · `R` ölç · GP vekili · **gözemli seçimi (2 mi 3 mü)** | havuz |
| **4** | **Posterior + SBC kapısı** · tanımlanabilirlik · 2. kuşak (9/10/11) | 3. hafta |
| **5** | Ara an kaydı kodu · PROTOKOL-HK · HK koşuları · A95 | — |
| **6** | **PROTOKOL-HT yeniden yazımı → üç öngörüyü MÜHÜRLE → Zenodo DOI** | 4-5. hafta |
| **7-9** | Çok doğruluklu vekil + Richardson · TÜBİTAK raporu · makale gövdesi | paralel |
| **10-11** | X→Y yama (kutu sahnesi → analitik kapı → eşleşmiş koşu) | aksarsa atılır |
| **12-13** | **Savunma provası** · poster · son okuma | — |

**Kritik yol:** havuz (2 hafta) → posterior (2 hafta) → Hera mührü (2 hafta)
→ rapor/prova (4 hafta) = **10 hafta**. `~3 hafta` pay.

## 3. Bütçe

| kalem | saat |
|---|---|
| kalan | `602` |
| çok doğruluklu vekil | `−224` |
| SBC kapısı düşerse `+24` nokta | `−120` |
| Hera (HK + HT) | `−60` |
| X→Y yama | `−37` |
| 2. kuşak (açı + blok + mermi) | `−25` |
| A95 koni | `−20` |
| **pay** | **`116`** |

Pay, SBC ikinci kez düşerse ya da ince nokta sayısını `12 → 18` çıkarmak
istersek kullanılır.

## 4. Kapılar — bunlar geçilmezse ilerlenmez

| kapı | nerede | geçmezse |
|---|---|---|
| Havuz kaybı `≤ %20` | PROTOKOL-HAVUZ §4 | havuz tekrarı |
| **SBC: her eksende KALİBRE/DÜZGÜN** | PROTOKOL-HAVUZ §6 | posterior **yayımlanmaz**; `+24` nokta ya da tarih eşlemeyle eleme |
| Balistik entegratör `t=0`'da `β`'yı yeniden üretiyor | PROTOKOL-SI §4 | 3. ölçüm okunmaz |
| Kutu sahnesi analitik plaka çözümünü veriyor | PROTOKOL-XY §2 | yama hiç koşulmaz |
| X→Y düzeltmesi: `E_düzeltmeli < E_düzeltmesiz/3` | PROTOKOL-XY §4 | araç olarak kullanılmaz |

## 5. Teslim edilecekler

| ürün | ne zaman |
|---|---|
| **Mühürlü üç Hera öngörüsü + Zenodo DOI** | 6. hafta |
| Kalibre posterior + SBC raporu + tanımlanabilirlik | 4. hafta |
| TÜBİTAK 2204-B raporu + poster | 9. hafta |
| Makale gövdesi (JOSS + PSJ/MNRAS için) | 9. hafta |
| Savunma provası tamam | 13. hafta |

## 6. Riskler

| risk | olasılık | karşılık |
|---|---|---|
| **TRUBA kesintisi** (şu an yaşanıyor) | yüksek | 1. kuşak sıfır GPU — kesintide de çalışılır |
| SBC kapısı `YANLI` | ~%25 | `+24` nokta (`120 sa`) ya da tarih eşleme |
| Krater hiçbir anda okunamaz | ~%25 | spin + yoğunluk + şekil öngörüleri **yine durur** |
| Ortak kuyruk gecikmesi | orta | havuz dilimli, kesintiye dayanıklı |
| **Savunma hazırlığı yetmez** | ? | 12-13. hafta buna ayrıldı; **en büyük risk** |

Son satır: bilimsel riskleri ölçtüm, **savunma riski ölçülemez** ve
kullanıcıdadır. Plan ona 2 hafta ayırıyor.

## 6.1 Planın dayandığı kilitli protokoller (2026-10-08'de yazıldı)

| protokol | neyi kilitler | veri görüldü mü |
|---|---|---|
| [PROTOKOL-SI](truba/PROTOKOL-SI-SON-ISLEME.md) | 1. kuşağın 6 sıfır-GPU ölçümü (§2 kaçış, §3 yörünge yönü, §4 balistik, §5 spin, §6 yoğunluk, §7 şekil) | **hayır** — TRUBA kapalıydı |
| [PROTOKOL-UP](truba/PROTOKOL-UP-POSTERIOR.md) | gözemli seçimi yargısı, çok noktalı + 3 kovaryanslı denetim, önsel duyarlılığı (§5), tarih eşleme (§6) | **hayır** — havuz koşuyordu |
| [PROTOKOL-XY](truba/PROTOKOL-XY-YAMA.md) | analitik plaka kapısı (§2), üç çözünürlük, düzeltme kapısı `E_düz < E_ham/3` (§4), yazılı yasaklar (§5) | **hayır** — yama hiç koşulmadı |

Üçü de kural 6'ya uyuyor: **yargı kuralı veriden önce.** Her birinin
"bu protokolün yapmadığı şey" bölümü var; ödül sunumunda ilk okunacak
yerler oralar.

## 7. Bu planın değiştirmediği şeyler

- Beş kilitli karar (KAYIT-075): `Y₀` önseli, hedef `β`, çekme kapalı,
  blok modeli, posterior tarifi
- `~0` çekme dayanımı bulgusu (ölçüldü, DC)
- Kapsam sınırı: `(α_b, f)` `≳14 m` **iç** bloklara ait
- Kural 6: yargı kuralları veriden önce
