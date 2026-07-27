# ADR-0001 — Parçacık deposu düzeni: SoA (Structure-of-Arrays)

- **Durum:** Kabul edildi (kilitli)
- **Tarih:** 2026-07-27
- **İlgili gereksinim:** P0-FR-03

## Bağlam
GPU'da (Warp kernel'leri, FAZ 1+) parçacık alanlarına erişim coalesced (birleşik)
olmalıdır. Bu karar tüm sonraki kernel'lerin bellek düzenini belirlediği için
FAZ 1'de değil, FAZ 0'da verilir (DR-RIFT-P0 §3.2).

## Değerlendirilen seçenekler
1. **AoS (Array-of-Structs):** `particle[i].x` — CPU'da doğal, GPU'da bir warp'ın
   32 iş parçacığı ardışık olmayan adresler okur; bant genişliği boşa harcanır.
2. **SoA (Structure-of-Arrays):** `x[i], y[i], ...` — her alan ayrı bitişik dizi;
   GPU'da tam coalesced erişim, NumPy vektörleştirmesiyle de doğal uyum.
3. **AoSoA (hibrit):** blok-tabanlı karışım — performans ayarı gerektirir; FAZ 0'ın
   "yalnızca doğruluk" ilkesine aykırı karmaşıklık.

## Karar
**SoA.** `ParticleStore` her alanı ayrı, C-bitişik NumPy dizisi olarak tahsis eder;
Warp köprüsü alan-başına `wp.array` üretir. Alan dizilerinin yeniden bağlanması
(`store.x = ...`) sınıf düzeyinde engellenir (gölgeleme hatası önlenir).

## Sonuçlar
- (+) FAZ 1 kernel'leri düzen değişikliği olmadan yazılır.
- (+) CPU↔GPU köprüsü alan-başına kayıpsız (bit-eşit) kopyalanabilir.
- (−) Tek parçacığın tüm durumunu okumak N ayrı diziye dokunur (kabul edildi;
  sıcak yol her zaman alan-bazlıdır).

## İlgili testler
`tests/test_particles.py::TestAllocation`, `TestWarpBridgeCpu`, `TestWarpBridgeGpu`
