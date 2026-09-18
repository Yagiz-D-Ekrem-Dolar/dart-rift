# Protokol UA — uzak alan çözünürlüğü `β`'yı değiştiriyor mu?

**Yazıldı:** 2026-09-18, **UA koşularından ve W2'nin hiçbir `β` değeri
okunmadan ÖNCE**. **Öncül:** LITERATUR §10, ADR-0050, PROTOKOL-W2.
**Rapor:** `scripts/ua_uzak_alan_raporu.py` → `S_UA.json` (kilitli).

---

## 1. Neden

Literatür (L1, L8) tüm cisim DART koşularını çarpma çevresinde cppr `< 1` ile,
ama **küresel** aralığı `~1–1,5 m` tutarak yapıyor. Bizim merdivenimiz çarpma
çevresinde daha ince (cppr `1,4`) ama uzak alanda `5,6–7 m` — `3–4×` kaba.
Zayıf hedefte `β`'nın çoğu **geç evre küresel akıştan** geliyor (L1: düşük
kohezyonda krater değil küresel deformasyon). Soru:

> Uzak alan aralığı değişince, geç evreden sonraki `β` ne kadar değişiyor?

Bu soru W2'nin sonucundan **bağımsız** bilgi verir: W2 tutsa da tutmasa da
havuzların hangi çözünürlükte koşulacağına karar vermek için gerekli.

## 2. Tasarım

W2'nin `Y₀ = 10 Pa`, `t_geçiş = 0,2 s` koşusuyla **aynı** her şey (sahne, mermi,
malzeme, geç evre, dondurma, 600 s), yalnız taban aralık değişir:

| kol | taban aralık | merdiven | parçacık (ölçüldü) | kaynak |
|---|---|---|---|---|
| **7 m** | 7,0 | `48:5.6 24:2.8 12:1.4 6:0.7 3:0.35` | 14 831 | **W2_Y10_g0p2** (yeniden koşulmaz) |
| **5 m** | 5,0 | `24:2.8 12:1.4 6:0.7 3:0.35` | 26 800 | UA görev 0 |
| **3,5 m** | 3,5 | `24:2.8 12:1.4 6:0.7 3:0.35` | 64 453 | UA görev 1 |

Çarpma çevresi (`≤ 24 m`) üç kolda da **aynı**; değişen yalnız uzak alan.
Maliyet (W2 ölçümüyle): 5 m `~4 sa`, 3,5 m `~9–15 sa` (tek GPU).

## 3. Geçerlilik

Üç kolun hepsi `gecerli = True` (momentum defteri dahil). Biri geçersizse
genel **OKUNMAZ**; yerine koşu konmaz.

## 4. Kilitli yargı

`b_s = β_s − 1`. Bağıl farklar:

    Δ(a, b) = |b_a − b_b| / b_b

| yargı | koşul |
|---|---|
| **UZAK ALAN YAKINSAMIŞ** | `Δ(3,5; 5) ≤ 0,05` **ve** `Δ(3,5; 7) ≤ 0,10` |
| **YAKINSIYOR** | yukarıdaki değil, ama `Δ(3,5; 5) < Δ(5; 7)` (fark daralıyor) |
| **YAKINSAMA YOK** | fark daralmıyor |

**YAKINSIYOR** durumunda Richardson tahmini **raporlanır, karar değildir**
(oran `r ≈ 1,4`): `p = ln(|b₇ − b₅| / |b₅ − b₃,₅|) / ln(1,4)`,
`b_∞ ≈ b₃,₅ + (b₃,₅ − b₅)/(1,4^p − 1)`.

## 5. Yorum tablosu (koşudan önce)

| yargı | havuzlar için anlamı |
|---|---|
| YAKINSAMIŞ | taban 7 m yeterli; havuz kaba merdivenle koşulur |
| YAKINSIYOR | havuz 7 m ile, **birkaç 3,5 m noktası** çok doğruluklu vekille (`cok_dogruluk.py`) birleştirilir; çözünürlük terimi posteriora girer |
| YAKINSAMA YOK | uzak alan çözünürlüğü baskın belirsizlik; üretim 3,5 m'ye (maliyet `~4×`) ya da daha ince bir taban sınamasına gider; bu **Bitiş 3'ün iddiasını sınırlar** ve öyle yazılır |

## 6. Kapı olmayan tanılar

`M_ejekta`, koni açıları (%90 ve kenar), dondurulan sayı, enerji sapması,
blok çözünürlüğü (homojen sahnede boş), duvar süresi.
