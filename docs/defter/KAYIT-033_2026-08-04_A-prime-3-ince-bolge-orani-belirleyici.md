# KAYIT-033 — A′-3: belirleyici olan **ince bölgenin oranı** (2026-08-04)

**Kapsam:** FAZ 4.2 · **Durum:** ölçüldü — **KAYIT-031'in "ön koşul" yargısı
düzeltildi**
**Öncül:** [KAYIT-031](KAYIT-031_2026-08-04_A-prime-tek-izgara-ise-yaramiyor.md),
[KAYIT-032](KAYIT-032_2026-08-04_A-prime-2-cok-seviyeli-izgara.md)

---

## 0. Ne düzeltiliyor

KAYIT-031 şunu yazdı:

> Tek ızgarayla A′, DART'ın ihtiyaç duyduğu oranlarda hiçbir şey
> kazandırmıyor. **Çok seviyeli komşu arama bir iyileştirme değil, ön
> koşuldur.**

**Bu yargı geçersizdir.** Silinmiyor; nedeni yazılıyor.

KAYIT-031 ve 032 **tek bir geometride** ölçtü: `r_iç/r_dış = 0,357`. Orada
ince parçacıklar toplamın **%63'ü**. Ama israf **yalnızca ince parçacıklara**
uygulanır — genel israf, ince kesirle ağırlıklı bir ortalamadır.

> **DART'ın ince bölgesi hedefe göre küçüktür**: ~1,3 m'lik mermi ~160 m'lik
> bir cisimde. `r_iç/r_dış` ~ 0,02–0,1 mertebesindedir, `0,36` değil.

---

## 1. Ölçüm — ince bölge oranı taranıyor

`λ = 2` (8:1), `r_dış = 70`, `s = 8`:

| `r_iç/r_dış` | ince kesir | tasarruf | tek ızgara israf | **net (tek)** | net (çok) | tek yeter mi |
|---|---|---|---|---|---|---|
| **0,114** | 0,039 | 7,86× | 1,070 | **0,136** | 0,127 | **✔** |
| 0,171 | 0,120 | 7,71× | 1,313 | **0,170** | 0,130 | **✔** |
| 0,229 | 0,267 | 7,34× | 2,025 | **0,276** | 0,136 | **✔** |
| 0,357 | 0,628 | 5,99× | 4,494 | 0,750 | 0,167 | ✘ |
| 0,500 | 0,884 | 4,25× | 6,768 | 1,591 | 0,235 | ✘ |

**İnce kesir küçüldükçe tek ızgara israfı `1,0`'a yaklaşıyor** — çünkü israf
yalnızca ince parçacıkları vuruyor.

---

## 2. Yüksek oran + küçük bölge — DART'ın gerçek rejimi

| λ | oran | `r_iç/r_dış` | ince kesir | tasarruf | **net (tek)** | **net (çok)** | tek/çok |
|---|---|---|---|---|---|---|---|
| 2,00 | 8:1 | 0,114 | 0,039 | 7,86× | **0,136** | 0,127 | **%93** |
| 2,52 | 16:1 | 0,114 | 0,077 | 15,60× | **0,077** | 0,064 | **%83** |
| 3,00 | 27:1 | 0,114 | 0,126 | 25,75× | **0,051** | 0,039 | **%76** |
| 2,00 | 8:1 | 0,357 | 0,628 | 5,99× | 0,750 | 0,167 | %22 |
| 3,00 | 27:1 | 0,357 | 0,848 | 12,29× | 1,307 | 0,081 | %6 |

> **Küçük ince bölgede tek ızgara, çok seviyelinin `%76–93`'ünü veriyor.**
> Çok seviyeli ızgara bir **ön koşul değil, bir iyileştirmedir**.

Ve tasarruf **büyüyor**: 27:1'de tek ızgarayla bile `net = 0,051`, yani
**19,6 kat** daha ucuz.

---

## 3. KAYIT-031 neden yanıldı

Tek bir geometride ölçüp **tüm geometrilere** genelledim. Oysa israf,
tanımı gereği **ince kesirle ağırlıklı**:

```
israf_genel ≈ f_ince · λ³  +  (1 − f_ince) · 1
```

`f_ince = 0,63` iken (KAYIT-031) `λ = 2` için `≈ 0,63·8 + 0,37 = 5,4` —
ölçülen `4,49` ile uyumlu.
`f_ince = 0,039` iken `≈ 0,039·8 + 0,96 = 1,27` — ölçülen `1,07` ile uyumlu.

**Formül baştan yazılabilirdi.** Yazmadım; tek bir sayı ölçüp genelledim.

> **Ders:** bir maliyet oranı **geometriye bağlıysa**, o geometri
> **taranmadan** yargı kurulmaz. KAYIT-031 tek bir `r_iç/r_dış` değerinde
> ölçtü ve "her oranda" diye yazdı.

Bu, KAYIT-029'un dersinin tekrarıdır: *"bir büyüklüğün nasıl davrandığını,
ilgilenilen çalışma noktasını içermeyen bir aralıkta ölçerek
söyleyemezsin."* Orada aralık `r_dep/r_şok` idi; burada `r_iç/r_dış`.

**İki kez aynı hata.** Kalıcı kural olarak yazılıyor.

---

## 4. A′'nın bedeli — üçüncü ve son hâli

| bileşen | durum |
|---|---|
| parçacık başına `h` (68 site + 24 CPU) | **zorunlu**, mekanik |
| `Ω` (grad-h) düzeltmesi | **zorunlu**, bilinen formül |
| parçacık başına CFL | **zorunlu**, mekanik |
| ~~seviye başına ızgara~~ | **İSTEĞE BAĞLI** — DART geometrisinde kazancın %76–93'ü tek ızgarayla zaten alınıyor |
| arayüz gürültüsü 3,2–6,5× | **kaçınılmaz** (KAYIT-024); şok geçişine etkisi **ölçülemez** (KAYIT-026) |

> **A′'nın mimari bedeli, KAYIT-031'in söylediğinden belirgin biçimde
> küçük.** Yeni bir komşu arama mimarisi **gerekmiyor**; parçacık başına `h`
> ve `Ω` yeterli.

---

## 5. Karar tablosu

| # | mermiyi çözer | **ölçülmüş bedel** | **ölçülmüş kazanç** |
|---|---|---|---|
| ~~A~~ | **hayır** | — | — |
| **A′** | evet | 92 site + `Ω`; arayüz 3,2–6,5× gürültü (şoka etkisi yok) | DART rejiminde **19,6× ucuz** (27:1, tek ızgara), model-form hatası **yok** |
| ~~B~~ | A′ ile | = A′ | = A′ |
| **C** | evet | momentum **7,5e-03 sistematik** + MLS + korunum düzeltmesi | arayüzde yapay kuvvet yok |
| **D** | **atlar** | model-form **%5–7**, kalibre **edilemiyor** | en ucuzu |

**A′ belirgin biçimde öne geçti.** Tek *"model-form hatası yok"* diyebilen
seçenek, ve mimari bedeli ölçüldükçe **küçüldü**.

---

## 6. Sırada

| # | iş | neden |
|---|---|---|
| — | **ADR-0041'in kilitlenmesi** | tüm kefeler ölçüldü; karar proje sahibinin |
| — | ADR-0041 §5 boşluk 3 (mukavemetli malzeme) | hangisi seçilirse seçilsin açık |

---

## 7. Bu kayıtta uygulanan kurallar

| kural | nerede |
|---|---|
| bir oran **geometriye bağlıysa** geometri **taranır** | §3 — yeni kalıcı kural |
| ölçülen sayı bir **formülle** açıklanabiliyorsa yazılır | §3 — `f·λ³ + (1−f)` |
| yanlış çıkan yargı **silinmez**, nedeni yazılır | §0, §3 |
| aynı hatanın **tekrarı** işaretlenir | §3 — KAYIT-029'un dersi |
| bedel ölçüldükçe **küçülebilir**; karar buna göre güncellenir | §4 |
