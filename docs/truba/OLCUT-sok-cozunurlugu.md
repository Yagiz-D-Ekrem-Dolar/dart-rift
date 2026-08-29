# ÖLÇÜT — Şok hangi çözünürlükte doğuyor? (koşudan **önce** yazıldı)

**Tarih:** 2026-08-28 · **Öncül:** rapor A22 · **Araç:** `scripts/sok_sinavi.py`

---

## 1. Soru

A22 *"model şok üretmiyor"* dedi ve çareyi `A1 ≈ 64`'e (`~55` gün)
bağladı. O çıkarım **iki noktadan** üs yasası uydurdu ve noktalardan
biri (tek aşama `λ = 2`) ötekinden (iki aşama `λ₁ = 38`) bambaşka bir
düzenekti. **Karışık iki noktadan ölçekleme çıkarmak bu deponun
tekrarlayan hatası.** Yerine: tek düzenek, tek değişken.

## 2. Hipotez — ve neden bu

SPH bir özelliği ancak **yumuşatma boyundan büyükse** taşır. Şoku
doğuran özellik merminin **ön yüzü**: yarıçapı `0,3714 m`.

| kol | `s` | `h = 2s` | **`r_mermi/h`** |
|---|---|---|---|
| üretim `λ₂ = 2` | `3,50` | `7,00` | **`0,053`** |
| `λ₂ = 8` | `0,875` | `1,75` | `0,212` |
| `λ₂ = 20` | `0,350` | `0,700` | `0,531` |
| `λ₂ = 40` | `0,175` | `0,350` | **`1,061`** |

> **H1:** Sıkışma düz bir `A1` üs yasası değil; `r_mermi/h ≈ 1`
> civarında **eşik** gösterir — şok, çözünürlük merminin **kendisini**
> çözdüğü anda doğar.
>
> **H0 (A22'nin dediği):** düz `~ A1^0,92`; `λ₂ = 40`'ta sıkışma
> `%10`'u geçmez.

İkisi `λ₂ = 40`'ta **ayrışıyor**: H1 `≳ %20`, H0 `≲ %10`.

## 3. Düzenek — ve neden **ucuz**

Şok mikro-saniyede kurulur; kraterin `0,2 s`'sine gerek yok.
`t_end = 1e-3 s` ile `λ₂ = 40` yalnızca `137` adım; `r_ince2 = 3 m`
ile parçacık `~15 000`'de kalıyor.

**Tek aşama** koşuluyor: aktarım (`ρ`'yu `ρ₀/α₀`'a sıfırlıyor)
denklemin dışında kalsın diye.

| değişken | değer |
|---|---|
| **taranan** | `λ₂ ∈ {2, 8, 20, 40}` |
| sabit | `--tek-asama --r-ince2 3 --t-end 1e-3`, üretim malzemesi |

## 4. Yargı kuralı (**kilitli**)

`sok_sinavi.py`, her parçacığın **kendi `α₀`**'ı ile.
Hugoniot bandı `%45,6 – 74,3`.

| en yüksek sıkışma | yargı |
|---|---|
| `≥ %45,6` | **`SOK_VAR`** — fizik kuruldu |
| `%4,6 – 45,6` | **`KISMI`** |
| `< %4,6` | **`SOK_YOK`** |

**H1 geçer** ⟺ `λ₂ = 40`'ta sıkışma `> %20` **ve** `20 -> 40` artışı
`8 -> 20` artışından **büyük** (eşik = hızlanan artış).

**H1 düşer** eğer artış düz kalırsa; o zaman A22'nin `~55 gün`
tahmini ayakta kalır ve tek çare ADR-0048'in kamasıdır.

## 5. Ne **ölçmüyor**

`β`, krater, ejekta — hiçbiri. `t = 1e-3 s`'de kazı akışı başlamamıştır.
Bu ölçüt yalnızca **şokun doğup doğmadığını** sorar.

## 6. Maliyet

Dört kol, yerel RTX 3050, `< 20` dakika beklenir. Bu, `55` günlük
tahmini **çürütebilecek** en ucuz deney.

---

# EK ÖLÇÜT — Şok **doğduktan sonra** ne oluyor? (koşudan **önce**)

**Tarih:** 2026-08-29 · **Öncül:** A23'ün dört noktası

## 7. Çelişki

Üretim **aşama-1**'i `λ₁ = 19` ile koşuyor: `s = 0,368 m`. Bu,
`%22` sıkışma üreten `λ₂ = 20` (`s = 0,350`) ile **neredeyse aynı**.
Öyleyse aşama-1 şok üretiyor olmalı. Ama `t₁ = 4,767e-3 s`'de
ölçülen: kütlenin yalnızca `1,8e-5`'i `%1`'den fazla sapmış.

**Şok doğuyor ama `t₁`'e kalmıyor.**

## 8. Hipotez

Cephe `~3 400 m/s`. İnce bölge `r_ince = 3 m`. Cephe orayı
`3/3400 = 0,88e-3 s`'de terk ediyor — ölçtüğüm `t = 1e-3` **tam o
an**. Ötesinde `h = 7 m` ve A23'e göre orada şok taşınamıyor.

> **H2:** Şok, ince bölgenin **sınırında** ölüyor. Yani sıkıntı
> çözünürlüğün derecesi değil, ince bölgenin **kapsamı**.

## 9. Sınav — iki kol, tek değişken

| kol | `r_ince2` | `t_end` |
|---|---|---|
| **dar** | `3 m` | `4,767e-3 s` |
| **geniş** | `12 m` | `4,767e-3 s` |

`λ₂ = 20` sabit. Karşılaştırma noktası: A23'ün `t = 1e-3`'teki
`%22,02`'si.

## 10. Yargı (kilitli)

**H2 geçer** ⟺ dar kolda `t_end`'de sıkışma `%22,02`'nin **yarısının
altına** düşer **ve** geniş kolda `%11`'in **üstünde** kalır.

**H2 düşer** eğer iki kol da benzer sonuç verirse (o zaman sönüm
çözünürlükten değil, fizikten/AV'den gelir) ya da dar kol da
sıkışmayı korursa (o zaman `t₁`'deki `1,8e-5` başka bir sebepten —
aktarımdan — gelir ve **aktarım** suçlanır).

## 11. Neden önemli

H2 doğruysa çare **çözünürlüğü artırmak değil**, ince bölgeyi
cepheyle birlikte **taşımak** — ADR-0048'in hareketli inceltmesi.
Ve maliyet ince bölgenin **hacmiyle** değil **kabuğuyla** ölçeklenir.
