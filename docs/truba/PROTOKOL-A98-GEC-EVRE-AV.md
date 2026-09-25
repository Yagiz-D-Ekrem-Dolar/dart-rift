# Protokol A98 — geç evrede yapay viskozite `β`'yı ve çözünürlük farkını belirliyor mu?

**Yazıldı:** 2026-09-25, **A98 koşularından ÖNCE**. UY ve UG'nin kilitli
sonuçları biliniyor (bu protokolle aynı gün üretildi, aşağıda §1).
**Öncül:** PROTOKOL-UY, PROTOKOL-UG, PROTOKOL-W2, rapor **A98**
(`docs/FAZ4-SIKINTI-RAPORU.md`), KAYIT-068.
**Rapor:** `scripts/a98_gec_av_raporu.py` → `S_A98.json` (kilitli).

---

## 1. Neden

Kilitli UY yargısı (2026-09-25): **ÇÖZÜNÜRLÜK TERİMİ GEREKLİ** —
48 m içi 2× incelince `β(300 s)` `3,686 → 3,978` (`Δ_orta = 0,098`).
Keşif (yargı değil): üç kolun `β(t)` eğrisi **0,2 s'ye kadar aynı**
(`1,966 / 1,963 / 1,975`); fark **geç evrede** (0,2 s → 100 s) doğuyor.

Kod incelemesi (A98): geç evrede Monaghan yapay viskozitesi (`α = 1`,
`β = 2`, Balsara açık) değişmeden kalıyor. Yapay gerilme `q ~ ρ α c h |∇v|`;
geç evrede `c ≈ 6–8 m/s`, akış hızları `~0,1–1 m/s`, `|∇v| ~ 0,01–0,05 1/s`.
Kaba merdivende `h = 2,8–11,2 m` (12–48 m kuşağı) için `q ~ 50–300 Pa` —
modelin kohezyonu (`Y₀ = 10 Pa`) ve litostatik basıncı (`< 1 Pa`) bunun
çok altında. Ölçüldü (CPU, `tests/test_a98_gec_evre_av.py`): aynı akış
alanında `h` yarıya inince AV gücü `1,95–1,97` kat azalıyor (doğrusal).
Fiziksel bir sürtünme çözünürlükten bağımsız olurdu.

> Hipotez: geç evre akışını yapay viskozite frenliyor; `h` küçüldükçe fren
> zayıflıyor ve `β` büyüyor. UY'deki farkın sebebi bu ise, geç evrede AV
> küçültülünce (1) `β` belirgin değişir, (2) kaba–orta farkı küçülür.

Yapay viskozite **şok yakalama** aracıdır; geç evrede (Mach `~0,05`) şok
yoktur ve fiziksel yitim zaten kurucu modelde (sürtünme `μ_f`, kohezyon `Y₀`,
plastik iş). AV'yi geçişte küçültmek yeni bir fizik değil, sayısal bir
aracın uygulama alanını daraltmaktır.

## 2. Tasarım

`UY` ile **aynı** her şey (L1 küresi, `Y₀ = 10 Pa`, `t_geçiş = 0,2 s`,
`A_geç = 1e5 Pa`, dondurma, yerçekimi, `β` iki yöntem, kod `0721629` fiziği);
yalnız **geçişten sonraki** AV katsayıları ve merdiven değişir. Hepsi 300 s.

| görev | ad | merdiven | geç AV `(α, β)` | amaç |
|---|---|---|---|---|
| 0 | `A98_k_av1` | kaba | `(1, 2)` (varsayılan) | AV tanısı + gerileme (W2 ile aynı fizik) |
| 1 | `A98_k_av01` | kaba | `(0,1 ; 0,2)` | AV duyarlılığı |
| 2 | `A98_o_av01` | orta (`48:2.8 … 3:0.175`) | `(0,1 ; 0,2)` | AV küçükken çözünürlük farkı |
| 3 | `A98_k_av0` | kaba | `(0 ; 0)` | AV sınırı |
| 4 | `A98_k_p6400` | kaba, **mermi 6400 parçacık** | `(1, 2)` | mermi çözünürlüğü geç `β`'ya yansıyor mu (M5) |

Karşılaştırma kolları (yeniden koşulmaz): `W2_Y10_g0p2` (kaba, AV 1/2) ve
`UY_orta` (orta, AV 1/2). Hepsinde `--av-tanisi-her 50` (görev 0–4).

**Görev 4 neden:** 20–21 Eylül P1 deneyleri (TRUBA `p1-2026092*`, depoya
girmemişti; KAYIT-068) 24 ms'de mermi 803 → 6401 parçacıkla `β`'nın
`1,407 → 1,600` değiştiğini ölçtü. UY'de hedef inceltmesinin 24 ms farkı
0,2 s'de kayboldu; mermininki kayboluyor mu bilinmiyor.

`β(300 s)`: kendi 300 s koşularında son değer; `W2_Y10_g0p2` için UY
raporunun **aynı** log-zaman aradeğeri (`beta_aninda`).

## 3. Geçerlilik

- Her kol `gecerli = True` ve `t = 300 s`'ye ulaşmış olmalı; değilse o kolun
  girdiği her ölçüt **OKUNMAZ**.
- **Gerileme R0:** `|β_{A98_k_av1}(300) − β_{W2}(300)| ≤ 0,01`. Tanı fiziğe
  dokunmuyorsa bu sağlanır. Sağlanmazsa **bütün protokol OKUNMAZ** (kod yolu
  W2 ile aynı değil demektir).
- `A98_k_av0` (AV sıfır) kararsızlaşırsa (geçersiz ya da süre aşımı) yalnız
  M4 OKUNMAZ; diğerleri etkilenmez.

## 4. Kilitli yargı

`b = β(300 s) − 1`.

**M1 — AV payı (tanı, `A98_k_av1`):**
`pay = E_AV,geç / (E_AV,geç + W_plastik,geç)` (geç evrede AV'nin ısıya
çevirdiği enerji ile plastik iş).
`pay ≥ 0,5` → **AV GEÇ EVREDE BASKIN**; değilse **AV GEÇ EVREDE İKİNCİL**.

**M2 — duyarlılık:** `Δ_AV = |b_k01 − b_k1| / |b_k1|` (`b_k1` = `A98_k_av1`).
`Δ_AV > 0,05` → **β GEÇ EVRE AV'SİNE DUYARLI**; değilse **DUYARSIZ**.

**M3 — çözünürlük (ana yargı):**
`Δ_1 = |b_UYorta − b_W2| / |b_UYorta|` (AV 1/2; UY'de `0,098`),
`Δ_01 = |b_o01 − b_k01| / |b_o01|` (AV 0,1/0,2).

| yargı | koşul |
|---|---|
| **AV ÇÖZÜNÜRLÜK FARKININ ANA SEBEBİ** | `Δ_01 ≤ 0,05` **ve** `Δ_01 ≤ Δ_1 / 2` |
| **AV KISMİ SEBEP** | yukarıdaki değil ama `Δ_01 < Δ_1` |
| **AV SEBEP DEĞİL** | `Δ_01 ≥ Δ_1` |

**M4 — AV sınırı:** `Δ_0 = |b_k0 − b_k01| / |b_k0|`. `Δ_0 ≤ 0,02` →
**AV 0,1'DE İHMAL EDİLEBİLİR**; değilse **AV 0,1 HÂLÂ ETKİLİ**.

**M5 — mermi çözünürlüğü (ayrı soru):**
`Δ_p = |b_p6400 − b_k1| / |b_p6400|` (`b_k1` = `A98_k_av1`).
`Δ_p ≤ 0,05` → **MERMİ ÇÖZÜNÜRLÜĞÜ GEÇ β'YA YANSIMIYOR**; değilse
**MERMİ ÇÖZÜNÜRLÜĞÜ GEÇ β'YA YANSIYOR**. `genel` yargı M3'tür; M5 ayrı yazılır.

> **Dürüst sınır:** iki merdiven yakınsamayı kanıtlamaz. M3 "ana sebep"
> derse bile üretim çözünürlüğü için üçüncü bir seviye gerekir. `Δt`
> AV ile değişir (AV küçülünce adım büyür); J1 `ara` kipinde `Δt`
> bağımlılığının kalktığını gösterdi, ama burada ayrıca sınanmadı.
> Sonuç ne çıkarsa çıksın, gözlenen DART `β`'sına göre ayar yapılmaz.

## 5. Kapı olmayan tanılar

`β(t)` eğrileri (0,2 s'de dört kol aynı olmalı: geçişe kadar fizik aynı),
`M_ejekta`, `β_km`, koni açıları, AV ivme payının zamanla seyri, duvar
süresi, adım sayısı.

## 6. Maliyet

W2 kaba 600 s `7,2 GPU-sa`, UY orta 300 s `6,4 sa`. AV küçülünce geç evre
adımı `~2×` büyür; mermi 6400'de en küçük `h` yarıya iner, adım `~2×` küçülür.
Beklenen: görev 0 `~3,6`, 1 ve 3 `~2`, 2 `~3,5`, 4 `~8` → toplam `~20 GPU-sa`,
**5 GPU aynı anda** (20 GPU sınırının içinde), süre sınırı 16 sa. Otomatik
yeniden gönderim yok.
