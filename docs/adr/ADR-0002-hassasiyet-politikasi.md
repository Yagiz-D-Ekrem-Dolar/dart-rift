# ADR-0002 — Hassasiyet politikası: FP64 bilim çekirdeği + ayrı performans modu

- **Durum:** Kabul edildi (kilitli)
- **Tarih:** 2026-07-27
- **İlgili gereksinim:** DR-RIFT-P0 §5.3, P0-QR-03

## Bağlam
Determinizm ve korunum tanıları FAZ 6'daki kilitli Hera tahmininin ön koşuludur.
Kayan-nokta hassasiyeti ve indirgeme sırası sonucu değiştirir; mod baştan
tanımlanmazsa FAZ 1'de kernel'ler iki kez yazılır.

## Değerlendirilen seçenekler
1. **Her yerde FP32:** hızlı ama şok problemlerinde enerji muhasebesi ve
   yoğunluk toplamlarında birikimli hata; doğrulama figürleri için kabul edilemez.
2. **Her yerde FP64:** güvenli, yavaş; GPU'da 1/2–1/32 oranında FP64 birimi.
3. **İki ayrı mod (seçilen):** `science` = kritik değişkenler FP64 + sabit-sıralı
   indirgeme + sabit tohum; `performance` = kinematik FP32, yalnızca bilim moduyla
   çapraz doğrulama sonrası kullanım.

## Karar
İki mod `ParticleStore(precision=...)` içinde FAZ 0'da tanımlanır:
- `science`: kinematik FP64; termodinamik/katı-hâl FP64. Doğrulama, yayın
  figürleri ve nihai tahmin **zorunlu** bu modda.
- `performance`: kinematik FP32; termodinamik FP64 kalır.
Korunum bütçeleri her modda **sabit-sıralı Kahan** toplamı ile hesaplanır
(`dartrift.cpu_math.reductions`); paralel atomik indirgeme yasak.

## Sonuçlar
- (+) Altın hash regresyonu (P0-QR-03) bilim modunda bit-eşit çalışır.
- (+) FAZ 1 kernel imzaları mod parametresiyle tek kez yazılır.
- (−) Performans modu çıktıları yayında kullanılamaz (bilinçli kısıt).

## İlgili testler
`tests/test_particles.py::TestAllocation::test_performance_dtypes`,
`tests/test_cpu_math.py::TestDeterministicReductions`,
`tests/test_determinism_golden.py`
