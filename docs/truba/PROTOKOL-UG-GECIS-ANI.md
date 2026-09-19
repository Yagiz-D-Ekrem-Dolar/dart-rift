# Protokol UG — geç evreye geçiş anı yakınsıyor mu?

**Yazıldı:** 2026-09-19, **UG koşularından ÖNCE**. W2'nin kilitli sonucu
biliniyor (KAYIT-067). **Öncül:** PROTOKOL-W2, LITERATUR L1/L3/L8, ADR-0051.
**Rapor:** `scripts/ug_gecis_raporu.py` → `S_UG.json` (kilitli).

---

## 1. Neden

W2 geçiş anını iki değerde koştu. Kilitli sağlamlık ölçütü (`≤ 0,20`) geçti,
ama fark **tek yönlü ve büyük**:

| `Y₀` | `β` (0,2 s) | `β` (1,0 s) | `Δ(β−1)` |
|---|---|---|---|
| 50 Pa | 3,295 | 3,494 | +%8,7 |
| 10 Pa | 3,667 | 4,070 | +%15,1 |
| 1 Pa | 3,992 | 4,389 | +%13,3 |

Yani `t_geçiş = 0,2 s` **yakınsamış değil**. Literatür daha geç geçiyor:
L3 ölçütü `t_geçiş ≈ 10 L / c_s` (bizim sahnede `~0,5–1 s`), L8 `5 / 50 / 500 s`
ile sonuçları aynı buldu. W2'de geçişte kinetik enerji 0,2 s ile 1,0 s arasında
hemen hiç azalmamış (`3,757e8 → 3,746e8 J`): 0,2 s'de hedef hâlâ akıyor ve
`A_geç = 1e5 Pa` ile ses hızı `~8 m/s`'ye iniyor.

> Soru: geçiş anı büyüdükçe `β` bir değere yaklaşıyor mu, hangi `t_geçiş`
> yeterli?

## 2. Tasarım

`W2_Y10_*` ile **aynı** her şey (L1 küresi, kaba merdiven, `Y₀ = 10 Pa`,
`A_geç = 1e5 Pa`, 600 s), yalnız `t_geçiş` değişir:

| kol | `t_geçiş` | kaynak |
|---|---|---|
| 0,2 s | 0,2 | W2_Y10_g0p2 (yeniden koşulmaz) |
| 1,0 s | 1,0 | W2_Y10_g1p0 (yeniden koşulmaz) |
| **2,5 s** | 2,5 | UG görev 0 |
| **5,0 s** | 5,0 | UG görev 1 |

Maliyet: erken evrede adım `4,2e-6 s` sabit (mermi parçacıklarıyla sınırlı,
W2'de ölçüldü: 0,2 s = 47 712 adım, 1,0 s = 238 236 adım). 2,5 s `~7,7 sa`,
5,0 s `~14 sa`. Toplam `~22 GPU-sa`.

## 3. Geçerlilik

Dört kolun dördü `gecerli = True`; biri değilse **OKUNMAZ**.

## 4. Kilitli yargı

`b_g = β_g − 1` (600 s), `Δ(a; b) = |b_a − b_b| / b_b`.

| yargı | koşul |
|---|---|
| **GEÇİŞ YAKINSAMIŞ** | `Δ(5,0; 2,5) ≤ 0,05` |
| **YAKINSIYOR** | değil, ama `Δ(5,0; 2,5) < Δ(2,5; 1,0)` |
| **YAKINSAMA YOK** | aksi |

**Üretim geçiş anı (kilitli):** `{0,2; 1,0; 2,5}` içinden `Δ(t; 5,0) ≤ 0,05`
olan **en küçük** `t`. Hiçbiri değilse: YAKINSIYOR'da `5,0 s`, YAKINSAMA
YOK'ta **belirlenemedi**.

## 5. Yorum tablosu (koşudan önce)

| yargı | anlamı |
|---|---|
| YAKINSAMIŞ | üretim kilitli `t_geçiş` ile; `0,2 s` koşuları çok doğruluklu vekilde **düşük doğruluk** olarak kullanılabilir (KOH AR(1), `cok_dogruluk.py`) |
| YAKINSIYOR | üretim `5,0 s`; kalan fark `σ_geçiş = Δ(5,0; 2,5)` model eksikliğine girer |
| YAKINSAMA YOK | geç evre şeması (`A_geç`, geçiş biçimi) kendi başına sorunlu; `A_geç` taraması gerekir, üretim durur |

**Kapı olmayan tanı:** her kolda L1 oranı (`β / 4,18`), `β_km`, `M_ejekta`,
geçişte kinetik enerji, duvar süresi.
