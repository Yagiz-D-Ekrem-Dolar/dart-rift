# KAYIT-041 — Yerel GPU açıldı; **mermi çözülmemiş** (2026-08-08)

**Kapsam:** FAZ 4.4 · **Durum:** kısmen ölçüldü (4/6 kol), **G4-A1 düştü**
**Öncül:** [KAYIT-040](KAYIT-040_2026-08-08_ensemble-fizibilitesi-A-prime-ile.md),
[G4-OLCUTLERI.md](../G4-OLCUTLERI.md)

---

## 0. TRUBA kapalı, yerel GPU açık

Kota dolu (`7 200 096 / 7 200 000`). Ama yerelde bir GPU var:

| | |
|---|---|
| kart | **NVIDIA RTX 3050 Laptop** |
| bellek | 4 GiB |
| compute | sm_86 (Ampere) |
| sürücü | 610.64 |
| warp | 1.16.0 (`pyproject.toml`'un kendi `gpu` ekstrası) |

### Hız **ölçüldü**, tahmin edilmedi

| | `µs/1000 parçacık` |
|---|---|
| TRUBA H200 (FIZIBILITE §2b) | 8 658 |
| **RTX 3050** | **24 659** (`275,3 ms/adım`, `N = 11 164`) |

> Yalnızca **`2,85×` yavaş.** FP64 oranı tüketici Ampere'de `1/64`
> olmasına rağmen — çünkü SPH **bellek ve komşu-arama sınırlı**, FP64-FLOP
> sınırlı değil. Beklentim `~400×` idi ve **yanlıştı**.

### Atlanan GPU testleri artık koşuyor

| dosya | sonuç |
|---|---|
| `test_adaptive_h_gpu` | **4/4**, 6,40 s |
| `test_solid_cross` | **13/13**, 14,38 s (CUDA kolları dahil) |

S9'un uyarısı (*"atlanan test geçmiş değildir"*) bu altküme için
**kalktı**.

---

## 1. G4-A1 **düştü** — ve ne kadar düştüğü belirleyici

Dört kolda da aynı:

| kurulum | yerel aralık | mermi çapı | **A1** | eşik | durum |
|---|---|---|---|---|---|
| `s7_λ2` | 3,500 m | 0,751 m | **0,215** | 2,0 | **ÇÖZÜLMEMİŞ** |
| `s7_λ3` | 2,333 m | 0,751 m | **0,322** | 2,0 | **ÇÖZÜLMEMİŞ** |
| `s5_λ2` | 2,500 m | 0,751 m | **0,300** | 2,0 | **ÇÖZÜLMEMİŞ** |

> En iyi kolda bile **6,2 kat** eksik.

Ölçüt **ölçümden önce** yazılmıştı (ADR-0040) ve tam olarak bunu
yakalamak için vardı. Düştü.

---

## 2. Gereken `λ` ve **bedelinin ayrıştırılması**

`A1 ≥ 2` ⇒ `s_ince ≤ 0,3755 m` ⇒ **`λ = 18,6`** (kütle oranı **6478:1**).

Oysa boşluk 3 `λ = 2` (8:1) oranında kapandı; KAYIT-033 `λ ≤ 3`'e kadar
taradı. Yani gereken oran **ölçülmüş her şeyin çok ötesinde**.

### Ensemble bedeli (1 s, 300 koşu)

| `λ` | `A1` | `r_iç` | `N` | ensemble |
|---|---|---|---|---|
| 2 | 0,21 ✘ | 25 m | 11 164 | **9,7 gün** |
| 19 | 2,04 ✔ | 25 m | 810 161 | 6707 gün |
| 19 | 2,04 ✔ | **3 m** | **11 613** | **96 gün** |

`r_iç`'i `25 → 3 m` küçültmek maliyeti **70 kat** düşürüyor. Parçacık
yükü artık ihmal edilebilir: çarpan **`1,13`**.

### Kalan bedel **tamamen CFL**

| bileşen | çarpan |
|---|---|
| parçacık sayısı | **1,13** |
| **`dt` cezası** | **9,3** |
| toplam (`λ=2`'ye göre) | **10,5** |

> **Tek global zaman adımlı bir şemada mermiyi çözmenin bedeli
> küçültülemez.** İnce bölge ne kadar küçülürse küçülsün `dt` yine
> `λ` kat iner ve bütün parçacıklar o adımla ilerler.

Çözümü **bireysel / blok zaman adımı** — standart bir SPH tekniği ve
bu kod tabanında **yok**. FAZ 5 için mimari bir açık.

---

## 3. Ölçülen `β` (4/6 kol)

`t_end` yerine `3000 adım` sabit; `t_sim` kollarda farklı çıkıyor
(`dt` farklı), o yüzden bunlar **yakınsama kanıtı değil** — yalnızca
koşuların çalıştığının ve `β`'nın makul mertebede olduğunun kaydı.

| kol | `N` | `β(son)` | `t_sim` | duvar |
|---|---|---|---|---|
| `s7_λ2` A′ | 11 164 | 1,583620 | 3,42e-01 s | 714 s |
| `s7_λ2` tek `h` | 11 164 | 1,553731 | 6,94e-01 s | 751 s |
| `s7_λ3` A′ | 13 457 | 1,605748 | 2,16e-01 s | 1119 s |
| `s7_λ3` tek `h` | 13 457 | 1,561803 | 6,95e-01 s | 1282 s |
| `s5_λ2` A′ | 29 105 | — | — | **kesildi** |
| `s5_λ2` tek `h` | 29 105 | — | — | **koşulmadı** |

> ### ⚠ B1 ve B3 **hesaplanmadı**
>
> Koşu son iki kol koşulmadan **elle durduruldu** (PC kapatılacaktı).
> `faz44_ozet` iki A′ kolu gördüğü için B1 üretebilirdi, ama `t_sim`
> kollarda **eşit değil** — sabit adım sayısıyla koşuldu, sabit süreyle
> değil. **Farklı `t`'deki `β`'ları kıyaslamak yakınsama ölçmez.**
>
> Bu bir kusur değil, ölçüm tasarımının bilinen bir sınırı: `faz44`
> `--steps` alıyor, `--t-end` almıyor. Sonraki koşuda düzeltilmeli.

---

## 4. Bu kayıtta yanlış çıkan tahminim

> *"RTX 3050'de FP64 `1/64` oranında; yaklaşık `400×` yavaş olur."*

**Ölçüm `2,85×` dedi.** Neden yanıldığım da açık: SPH'de darboğaz komşu
arama ve bellek erişimi, aritmetik değil. Bir donanım oranını iş yüküne
**doğrudan** taşımak hatalıydı.

> Bu tahmini koşmadan önce yazdım ve ölçüm çürüttü — **ölçmeden yazmak**
> kalıbının bu oturumdaki **dördüncü** örneği.

---

## 5. Sırada

| # | iş | engel |
|---|---|---|
| 4.4 | `--t-end` eklenip **eşit `t`**'de yeniden koşulması | — (yerel GPU var) |
| — | `λ`/`r_iç` kararı: A1 eşiği mi, mimari mi değişecek | karar |
| — | bireysel/blok zaman adımı değerlendirmesi | ADR gerekir |
| 4.5–4.7 | | 4.4 |

---

## 6. Bu kayıtta uygulanan kurallar

| kural | nerede |
|---|---|
| bir donanım oranı iş yüküne **doğrudan taşınmaz** — ölçülür | §0, §4 |
| ölçütün düşmesi **başarısızlık değil**, ölçütün işini yapmasıdır | §1 |
| bedel **ayrıştırılır**: hangi parçası küçültülebilir | §2 |
| eşit olmayan `t`'deki değerler **kıyaslanmaz** | §3 |
| kesilen koşu **kısmi** raporlanır, tamamlanmış gibi değil | §3 |
