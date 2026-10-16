# KAYIT-083 — Pilot interpolasyon ↔ posterior: `0,82σ` uyum, ve `Y₀`'nın niçin zor olduğunun sayısı

**Tarih:** 2026-10-16 (gece) · **Sıfır GPU**
**Öncül:** ön baskı §3 (üç noktalı güç yasası), ADR-0060, KAYIT-082,
PROTOKOL-DO

---

## 1. Niçin bakıldı

Düzeltilmiş posteriorun kipi `Y₀ ≈ 18,7 Pa` çıktı. Ön baskının özeti
beş pilot koşudan türetilmiş bir interpolasyonla **20,1 Pa** diyor.
İki sayı göz kararı uyuşuyor gibi durdu ve bunu bir iç tutarlılık
kanıtı olarak öne sürdüm.

**Yanlıştı.** İki sayı farklı geleneklerde.

## 2. Ön baskının sayısı doğrulandı

Üç nokta (`Y₀ = 10, 500, 5000` Pa; `β = 3,7480 / 2,6247 / 1,8738`),
ön kayıtlı `β−1 = C·Y₀^p` biçimi:

| | yeniden hesap | ön baskı |
|---|---:|---:|
| `p` | **−0,1791** | −0,1791 |
| azami bağıl artık | **0,1198** | 0,1198 |
| interpolasyon | **20,13 Pa** | 20,1 Pa |

Birebir. Ön baskı kendi içinde doğru.

## 3. Ama o hesap ADR-0060 öncesi

Ön baskı 2026-10-10'da yayımlandı; ADR-0060 2026-10-14'te kabul
edildi. Yani interpolasyon **çarpıcı geleneğindeki** `b`'yi, gözlemin
**fırlatı geleneğindeki** `β_göz`'üne eşitliyor — tam olarak ADR-0060'ın
yanlışladığı eşleştirme.

Aynı interpolasyon, ölçülmüş gelenek çarpanıyla (`1,1663`) düzeltilince:

| yol | `Y₀` |
|---|---:|
| ön baskı, düzeltilmemiş | 20,13 Pa |
| **aynı yol, ADR-0060 ile düzeltilmiş** | **47,54 Pa** |
| **96 noktalı GP posterior kipi** | **18,67 Pa** |

Yani "`20,1` ≈ `18,7`" uyumu **iki farklı geleneğin tesadüfü**ydü.
Aynı geleneğe çevrilince aradaki oran `2,55`.

## 4. Gerçek tutarlılık sınavı — ve geçiyor

Doğru soru "iki sayı yakın mı" değil, **"fark posteriorun kendi
belirsizliğinin içinde mi"**:

| | değer |
|---|---:|
| posterior `sd(log10 Y₀)` | **0,496 dex** (çarpan olarak `×3,13`) |
| iki yol arasındaki fark | 0,406 dex (`×2,55`) |
| **uyum** | **0,82σ** |

İki bağımsız kestirim yolu — 5 pilotla üç noktalı güç yasası, ve 96
noktayla GP posterioru — posteriorun **1σ**'sı içinde buluşuyor.
Bu meşru bir iç tutarlılık kanıtıdır; "%7 uyum" değildi.

> **Bağımsızlığın sınırı.** İki yol aynı ileri modeli ve aynı sahneyi
> kullanıyor; bağımsız oldukları yer **veri ve kestirim yöntemi**
> (5 nokta + güç yasası ↔ 96 nokta + GP + Bayes). Fiziğin doğruluğu
> hakkında bir şey söylemez.
>
> Ayrıca pilot interpolasyon `α_b` ve `f` **sabitken** bir doğru
> üzerinde; posterior ikisini marjinalleştiriyor. Birebir aynı nicelik
> değiller.

## 5. Asıl bulgu: `Y₀`'nın niçin zor olduğunun sayısı

Güç yasasının üssü `p = −0,1791`. Tersi `1/|p| = 5,59` ve bu bir
**yükselteç**: `b`'deki her hata `Y₀`'ya 5,59. kuvvetle geçiyor.

| `b`'de hata | `Y₀`'da |
|---|---:|
| %10 | **×1,70** |
| %16,6 (gelenek düzeltmesi) | ×2,36 |

Tersten okunuşu daha çarpıcı:

> **`Y₀`'yı iki katına çıkarmak `β−1`'i yalnız %11,7 değiştiriyor.**

Ve bizim `b` üzerindeki toplam belirsizliğimiz `sd = 0,3126`, sinyal
`b_göz = 2,5418` — yani **%12,3**.

İkisi neredeyse eşit. Yani ölçüm hassasiyetimiz, `Y₀`'daki **iki
katlık** bir değişimi ancak ayırt edebiliyor. Posteriorun `0,496 dex`
genişliği (`×3,1`) bunun doğrudan sonucu.

Bu, `n_yön = 1`'in Fisher öz değerlerinden daha anlaşılır bir
ifadesidir ve rapora/sunuma bu haliyle girmeli: *dejenerasyon bir
yöntem kusuru değil, `β`'nın `Y₀`'ya üs `−0,18` ile bağlı olmasının
kaçınılmaz sonucu.*

## 6. Ön baskı için sonuç

Ön baskının `20,1 Pa`'sı **düzeltme gerektiriyor**, ama metin
değiştirilmeyecek (yayımlanmış kayıt, kural 5/6). Paper II'de
ADR-0060 düzeltmesiyle birlikte `47,5 Pa` olarak yeniden verilecek ve
posteriorun `18,7 Pa`'sıyla `0,82σ` uyumu belirtilecek.

Ön baskının kendi şerhi zaten bunu karşılıyordu: *"That interpolation
is not an interior-strength measurement or posterior."* O cümle
olmasaydı bu düzeltme çok daha pahalıya mal olurdu.
