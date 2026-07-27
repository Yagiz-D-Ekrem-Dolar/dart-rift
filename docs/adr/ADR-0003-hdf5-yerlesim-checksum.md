# ADR-0003 — HDF5 yerleşimi, chunking ve checksum politikası

- **Durum:** Kabul edildi (kilitli)
- **Tarih:** 2026-07-27
- **İlgili gereksinim:** P0-FR-07, P0-DR-02

## Bağlam
Çıktı üç ayrı bilgi katmanı taşır: adım-bazlı skaler korunum bütçeleri (küçük,
sık), seyrek tam-alan snapshot'ları (büyük, seyrek) ve olay kayıtları (düzensiz).
Manifest, çıktıların SHA-256'sını taşımak zorundadır (Ek A).

## Değerlendirilen seçenekler
1. Tek düz tablo: katmanlar karışır, seyrek snapshot'lar şişer.
2. Katman-başına ayrı dosya: dosya yönetimi ve manifest karmaşıklaşır.
3. **Tek dosya, üç grup (seçilen):** `/scalar_budget`, `/sparse_snapshot`,
   `/event_catalog`.

## Karar
- **Chunking:** skaler bütçe kolonları `chunks=(1024,)`, `maxshape=(None,)`
  (append-optimize); olaylar `chunks=(256,)`; snapshot alanları h5py otomatik chunk.
- **Sıkıştırma:** config'ten (`gzip` seviye 4 varsayılan; `lzf`, `none` seçenek).
- **Zaman damgaları:** tüm veri kümeleri `track_times=False` — HDF5 üstverisine
  gömülen saat, bayt-düzeyi tekrarlanabilirliği bozar.
- **Checksum:** kanonik sağlama `content_sha256` = sıralı gezinmeyle
  (ad + dtype + shape + veri baytları + attr'lar) SHA-256. Ham dosya baytı
  sağlaması (`file_sha256`) yalnızca arşiv bütünlüğü içindir; kanonik değildir,
  çünkü HDF5 süperblok/boş-alan yerleşimi kütüphane sürümüne bağımlı olabilir.

## Sonuçlar
- (+) Aynı içerik → aynı `content_sha256` (test: iki bağımsız yazım eşit hash).
- (+) Tek ULP'lik veri değişikliği hash'i değiştirir (test edildi).
- (−) İçerik sağlaması dosyayı baştan okur (FAZ 0 ölçeğinde önemsiz).

## İlgili testler
`tests/test_io.py::TestChecksum`, `test_snapshot_roundtrip_bitwise`
