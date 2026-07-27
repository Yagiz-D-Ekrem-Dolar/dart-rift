# ADR-0006 — Config–motor bağlama sözleşmesi: doğrulanan her alan tüketilmelidir

- **Durum:** Kabul edildi (kilitli)
- **Tarih:** 2026-07-27
- **İlgili gereksinim:** P0-FR-02, P0-DR-01; DR-RIFT-P0 §12 (kırmızı takım)

## Bağlam
FAZ 0'ın ilk uygulaması G0 kapısının sekiz kriterini de geçti, ama teslim
öncesi öz-denetimde şu bulundu: config şeması `numerics.precision`,
`io.output_layers`, `io.hdf5_compression` ve `domain` alanlarını **doğruluyor**
ama motorun hiçbir parçası bu değerleri **okumuyordu**.

Sonuç sessiz bir sapmaydı: `precision: performance_mixed` yazan bir koşu
FP64 çalışmaya devam ederdi, `output_layers: [scalar_budget]` yazan bir koşu
yine üç katmanı da yazardı. Manifest doğru precision'ı raporladığı için
kayıt da yanıltıcı olurdu — yani hata, yeniden-üretilebilirlik iddiasını
doğrudan zehirliyordu. Hiçbir test bunu yakalamıyordu, çünkü tüm testler
şemayı ve motoru **ayrı ayrı** sınıyordu.

Bu, "bir özelliğin adının onu uyguladığı anlamına geldiğini varsaymak" hata
sınıfının tam örneğidir.

## Değerlendirilen seçenekler
1. **Alanları şemadan çıkarmak** (FAZ 1'de geri eklemek): şema fakirleşir,
   Ek B örnek config'i şartnameyle çelişir.
2. **Bağlamayı FAZ 1'e bırakmak, "ileride kullanılacak" notu düşmek:**
   reddedildi — bugün yanlış davranan bir koşu bugün yanlış kayıt üretir.
3. **Her doğrulanan alanı tüketen bir köprü + davranış testi (seçilen).**

## Karar
**Sözleşme:** Config şemasına, onu tüketen kod ve o tüketimi kanıtlayan
davranış testi olmadan alan eklenmez.

Uygulama kuralları:
- Alan başına **tek** köprü noktası olur. Hassasiyet eşlemesi yalnızca
  `config._PRECISION_TO_STORE_MODE` sözlüğünde yaşar; `RunConfig`
  `store_precision` ve `domain_bounds` özelliklerini sunar.
- Bileşenler config'i doğrudan kabul eden fabrika metotlarıyla kurulur:
  `ParticleStore.from_config(cfg, n)`, `Hdf5Writer.from_config(cfg, path)`.
- Config bir yeteneği **kapatıyorsa**, o yeteneği kullanmak sessizce yok
  sayılmaz; açık hata üretir (`LayerDisabledError`). Sessiz yok sayma, sessiz
  sapmanın diğer yüzüdür.
- Kapatılan katmanlar dosyanın kök `output_layers` attr'ında kayıtlıdır;
  okuyucu "bu katman boş mu, kapalı mıydı" ayrımını yapabilmelidir.
- Davranış testi şu biçimdedir: *alanı değiştir → gözlemlenebilir çıktının
  gerçekten değiştiğini doğrula* (`tests/test_config_wiring.py`).

## Sonuçlar
- (+) Config artık koşunun tek gerçek kaynağıdır; manifest ile motor davranışı
  arasında sapma testle engellenir.
- (+) Şemaya yeni hassasiyet eklenirse `test_every_schema_precision_has_a_store_mode`
  köprü güncellenmeden CI'yi kırar.
- (−) Her yeni config alanı üç dosyaya dokunmayı gerektirir (şema, köprü, test).
  Bu bilinçli bir sürtünmedir.

## İlgili testler
`tests/test_config_wiring.py` (17 test), `scripts/run_red_team.py::rt6`,
TRUBA kanıt koşusu job 1425589
