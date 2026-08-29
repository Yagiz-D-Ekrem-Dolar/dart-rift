# KAYIT-054 — Şok **doğuyor**; aktarım onu siliyor (2026-08-29)

**Kapsam:** A22 (düzeltildi) · A23 · A24 · ADR-0049
**Öncül:** [KAYIT-053](KAYIT-053_2026-08-21_enerji-alti-parcacikta.md)
**Koşular:** yerel RTX 3050 — `sok_lam{2,8,20,40}`, `h2_r{3,12}`, `a24_{A,B}`

---

## 1. Nereden başladım: A22'ye inanmamak

Önceki tur *"model şok üretmiyor"* diye kapanmıştı ve çareyi
`A1 ≈ 64` / `~55 gün`'e bağlamıştı. O çıkarım **iki noktadan** üs
yasası uyduruyordu ve noktalardan biri (tek aşama `λ = 2`)
ötekinden (iki aşama `λ₁ = 38`) bambaşka bir düzenekti.

Karışık noktadan ölçekleme çıkarmak bu deponun tekrarlayan hatası.
Bu yüzden **kendi bulguma** tek düzenekli, tek değişkenli bir sınav
kurdum — ve ölçütü koşudan **önce** yazıp commit ettim.

### Sınavı ucuzlatan fikir

Şok **mikro-saniyede** kurulur; kraterin `0,2 s`'sine gerek yok.
`t_end = 1e-3 s` + `r_ince2 = 3 m` ile dört kol **dakikalar** sürdü.
`55 günlük` bir tahmini çürütecek deney `20 dakikaya` indi.

---

## 2. A23: şok `λ₂ = 20 – 40`'ta doğuyor

| `λ₂` | `s` | `r_mermi/h` | sıkışma max | artış (üs) |
|---|---|---|---|---|
| `2` | `3,500` | `0,053` | `%0,0057` | — |
| `8` | `0,875` | `0,212` | `%1,683` | `296×` (`4,10`) |
| `20` | `0,350` | `0,531` | `%22,024` | `13,1×` (`2,81`) |
| **`40`** | `0,175` | `1,061` | **`%40,521`** | `1,8×` (`0,88`) |

`λ₂ = 40`'ta sıkışma Hugoniot alt ucunun (`%45,6`) **`%89`**'u ve üs
`4,10 -> 0,88` ile **doyuma** gidiyor: fiziksel tavana yakınsamanın
imzası. **Ekstrapolasyona artık gerek yok — cevap ölçüldü.**

A22'nin `A1^0,92` yasası `λ₂ = 20` için `%0,047` derdi. Ölçülen
`%22,02`: **`470` kat**.

### Cephe gerçek — ve hızı da tutuyor

`λ₂ = 20`, `t = 1e-3 s`: `1 306` parçacık `>%1` (`60 865 kg`),
temastan `0,67 – 3,41 m`, sıkışma uzaklıkla **düzgün azalıyor**.
`λ₂ = 8`'de aynı ölçü **tek** parçacık — cephe `h = 1,75 m`'nin
içine sığıyor.

> Tepe sıkışma `%22,02` -> Rankine-Hugoniot `Us = 3 565 m/s`.
> Cephe `1e-3 s`'de `3,41 m` gitmiş -> **`3 410 m/s`**. Sapma
> **`%4,3`**. Biri yoğunluktan, öteki konumdan; aralarındaki bağıntı
> literatürden. **Uydurulmadılar.**

---

## 3. A24: A22 **cesedi** ölçmüş

Üretim aşama-1 `λ₁ = 19` (`s = 0,368 m`) — yani `%22` üreten
`λ₂ = 20` (`s = 0,350`) ile neredeyse **aynı**. Öyleyse aşama-1 şok
üretiyor olmalı. `t = 4,767e-3 s`'de ölçtüm:

| | |
|---|---|
| sıkışma max | `%26,08` |
| şoklanan kütle | `72 936 kg` |
| **kütle kesri** | **`1,750e-5`** |

KAYIT-053'te `t₁` için yazılı olan: *"`%1`'den fazla sapan `2 181`
parçacık, **kütlece `1,81e-5`**"*.

> **Aynı sayı.** Aşama-1 şok üretiyor. Ben o kaydı *"şok yok"* diye
> okumuştum; oysa şokun **kendisiydi**.

### Kök sebep — kodda, ölçüme gerek yok

| durum değişkeni | aşama-2'ye taşınıyor mu |
|---|---|
| `x`, `v`, `m`, `u` (ısı), `D` (hasar) | **evet** |
| **`ρ` (sıkışma)** | **hayır** |

`solver_solid.py` `ρ`'yu **her zaman** `ρ₀/α₀` ile kuruyordu ve
`_cozucu`'nun `rho` parametresi **yoktu**. Aktarım sıkışmayı
kaybetmiyor — **kurulumda siliyor**.

Sonuç: aşama-2 **sıcak ama sıkışmamış** maddeyle başlıyor. Şoklanmış
madde için fiziksel olarak **olanaksız** bir durum. A22'nin

> *"en sıcak parçacıklar `u = 1,03e5 J/kg`'a çıkmış ama sıkışmaları
> `%0,4 – 0,5`"*

belirtisi bir ayrıklaştırma artığı değil, **aktarımın parmak izi**.

### Zincir

| adım | ne oluyor |
|---|---|
| aşama-1 | gerçek şok: `%26` sıkışma **+** ısı, `73 t` |
| **aktarım** | ısı geçer, **sıkışma sıfırlanır** |
| aşama-2 | sıcak-ama-sıkışmamış madde; genleşir, **kazmaz** |
| `t = 0,2 s` | sıkışma `%0,25`, krater `9 cm`, `β` hedeften beslenmez |

Dört ayrı sıkıntı değil, **tek** sıkıntının dört yüzü — ve A22'nin
söylediği yerde değil, **bir aşama sonrasında**.

### Çare: hacim korunumlu aktarım

`ρ` artık taşınıyor. Ama kütle-ağırlıklı ortalama **değil**:
yoğunluk `m/V`'dir, birleşen parçacıklar hem kütleyi hem **hacmi**
korumalı.

    V_k = Σ_i m_i/ρ_i        ρ_k = m_k / V_k        (harmonik)

Düz ortalama yanlış olurdu: kütlenin yarısı `2ρ`, yarısı `ρ` iken
hacim korunumu `1,333ρ` verir, düz ortalama `1,5ρ` — **boşluk yok
ederdi**. Korunan defter: **toplam hacim**.

Ve toplam yönteminde `rho_durum` artık **hata veriyor** (orada `ρ`
her adımda yeniden hesaplanır; sessizce yoksaymak çağıranın
sıkışmayı taşıdığını **sandırırdı** — A24'ün ta kendisi).

---

## 4. İkinci sınır: şok `3,4 m`'de duruyor

`t = 1e-3 -> 4,767e-3 s` (`4,8×` süre) cephe `3,41 m`'de **kaldı**;
`3 400 m/s` ile `16 m` gitmeliydi. İnce bölge `r_ince = 3 m`.

Şoklanan hacim `82 m³`. En küçük literatür krateri (`D = 13,3 m`)
bile `~6,5 m` yarıçap ister — **`2` kat büyük**. Bunun inceltmeden
mi doğal sönümden mi geldiği `r_ince = 12 m` koluyla sınanıyor
(ölçüt yazılı, koşu sürüyor).

---

## 5. ADR-0049: elemelerin ön koşulu

A23 bir **eşik** verdi ve o eşik geçmişi vuruyor. Bütün elemeler
şokun olmadığı rejimde yapılmış:

| eleme | `λ₂` | o `s`'de sıkışma |
|---|---|---|
| hasar, matris `Y0`, blok `Y0`, yerçekimi | `2` | `%0,006` |
| gözeneklilik | `6 – 8` | `≤ %1,68` |

KAYIT-053 bunu bir kez fark edip hasarı `μ ≈ 1`'de yeniden koşmuştu.
Ama `μ` **yanlış ölçüydü**: `μ ≈ 1` = `λ₂ = 8` ve orada sıkışma hâlâ
`%1,68`. Doğru ölçü `μ` değil, **sıkışma**.

> **Öneri:** hiçbir fizik elemesi, **aynı koşuda** şok sınavı `KISMI`
> ya da `SOK_VAR` vermedikçe geçerli sayılmaz.

---

## 6. Bu turda **kendi hatalarım**

- **A22'nin kendisi.** *"Model şok üretmiyor"* yanlıştı; model
  üretiyor, aktarım siliyor. Bir aşama önce bakmadım.
- **A22'nin `55 gün`'ü.** İki karışık noktadan üs yasası; `470` kat
  yanlış çıktı.
- **H1'i kendi kuralımla düşürdüm.** *"Artış hızlanmalı"* dedim; ama
  Hugoniot tavanı yüzünden o kural tek yönde **sınanamazdı**. Eşik
  yazmıştım, ölçüm **doyum** gösterdi.
- **Krater bölgesini yine `ehat`'ın ters ucundan ölçtüm** (ikinci
  kez); `-ehat` ile düzeltildi.
- Gözeneklilik/AV işi çıktısız düştü — ama A23'e göre `λ₂ = 6/8`'de
  koşuyordu, yani zaten **geçersizdi**.

---

## 7. Ne **yapılmadı**

- `β` hâlâ `3,2225` üretilmiyor; bu turda `β` **hiç ölçülmedi**
  (bilerek: `t = 1e-3 – 6e-3 s`'de kazı akışı yok).
- A24 çaresinin **koşudaki** A/B'si sıraya alındı, sonucu bu kayıtta
  yok.
- `r_ince = 12 m` kolu sürüyor.
- ADR-0046, 0047, 0048, 0049 kararları kullanıcıda.
