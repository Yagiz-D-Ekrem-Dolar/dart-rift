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
