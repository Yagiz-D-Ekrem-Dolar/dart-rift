# İzlenebilirlik Matrisi — FAZ 0 (DR-RIFT-P0)

Şartnamenin §4 başlığı "Gereksinimler (**izlenebilir**)" der. Bu belge her
gereksinim kimliğini uygulayan koda, onu doğrulayan teste ve kanıtına bağlar.
Bir satırın "Test" sütunu boşsa o gereksinim için **başarı iddia edilemez**.

Geçerli kanıt: `docs/evidence/G0_report_truba_1425656.md`
(TRUBA palamut4 / A100, job 1425656, 219 test, kapsam %97,1).

## Fonksiyonel gereksinimler (§4.1)

| ID | Gereksinim | Uygulama | Test |
|----|-----------|----------|------|
| P0-FR-01 | SI birim/sabit modülü, boyut analizi | `units.py` | `test_units.py` (26 test: kesin dönüşümler, boyutlar-arası dönüşüm reddi, CODATA sabitleri) |
| P0-FR-02 | YAML config şema doğrulama, açık hata | `config.py` | `test_config.py` (15 geçersiz vaka + hash + CLI) |
| P0-FR-03 | SoA depo, CPU↔GPU kayıpsız kopya | `particles.py` | `test_particles.py::TestWarpBridgeGpu` (FP64/FP32/uç değerler, **3 GPU mimarisi**) |
| P0-FR-04 | Tek kök tohum, shard-değişmezlik | `rng.py` | `test_rng.py::TestShardInvariance` (shard 1/2/3/5/7/101) |
| P0-FR-05 | Invariant denetleyici (NaN, kütle, sınır) | `invariants.py` | `test_invariants.py` (13 enjeksiyon vakası) |
| P0-FR-06 | Koşu manifesti (SHA, config, donanım, zaman) | `logging_cfg.py` | `test_manifest.py::TestManifestCompleteness` (her zorunlu alan tek tek) |
| P0-FR-07 | HDF5 3 katman, ayrı gruplar | `io_hdf5.py` | `test_io.py` (yaz-oku eşitliği + checksum) |

## Yazılım-kalite gereksinimleri (§4.2)

| ID | Gereksinim | Uygulama | Test / Kanıt |
|----|-----------|----------|--------------|
| P0-QR-01 | Her commit'te derleme, statik analiz, test, şema | `.github/workflows/ci.yml` | CI yeşil (Python 3.10 + 3.12 matrisi) |
| P0-QR-02 | Her büyük karar bir ADR | `docs/adr/` | 6 ADR; kapı kriteri C7 sayıyor |
| P0-QR-03 | Determinizm altın hash'i, sapma CI'yı kırar | `tests/golden/p0_canonical_v1.json` | `test_determinism_golden.py` (+ 2 işletim sistemi şartı) |
| P0-QR-04 | Çekirdek modüllerde kapsam ≥ %85 | — | %97,1 (kapı koşucusu eşiği zorlar; CI `--cov-fail-under=85`) |

## Veri gereksinimleri (§4.3)

| ID | Gereksinim | Uygulama | Test |
|----|-----------|----------|------|
| P0-DR-01 | `schema_version` zorunlu ve sürümlü | `config.py` | `configs/invalid/01,02,03` + `test_config.py` |
| P0-DR-02 | Manifest yeniden-üretim için tam (Ek A) | `logging_cfg.py` | `test_manifest.py::TestReproducibility` (config manifestten geri kuruluyor) |

## Şartnamenin sözde-kod maddeleri (§6)

| Madde | Uygulama | Test |
|-------|----------|------|
| §6.1 deterministik tohumlama (`spawn_key`) | `rng.py` | `test_rng.py` |
| §6.2 invariant denetimi | `invariants.py` | `test_invariants.py` |
| §6.2 son satır: ihlal → `numerical_failure` + **config dondur** | `failure.py` | `test_failure.py` (9 test) |
| §6.3 manifest üretim akışı | `logging_cfg.py` | `test_manifest.py` |

## Kapı ve kırmızı takım

| Kaynak | Otomasyon | Kanıt |
|--------|-----------|-------|
| §9 G0 sekiz kriteri | `scripts/run_g0_gate.py` | `G0_report_truba_1425656.md` Bölüm 2 |
| §12 kırmızı-takım listesi (5 madde + 1 ek) | `scripts/run_red_team.py` | aynı raporun Bölüm 1'i; her CI koşusunda da işletilir |

## Teslimatlar (§10 Definition of Done)

| Teslimat | Durum |
|----------|-------|
| `dart-rift/` iskelet deposu, CI yeşil | ✔ |
| Birim/sabit modülü, config şeması + doğrulayıcı | ✔ |
| SoA depo + Warp köprüsü + roundtrip testi | ✔ (3 GPU mimarisi) |
| Deterministik RNG + shard-değişmezlik testi | ✔ |
| Invariant çerçevesi + enjeksiyon testleri | ✔ |
| HDF5 üç-katman G/Ç + şema | ✔ |
| Manifest üreteci | ✔ (config gömülü) |
| ≥4 ADR; kapsam ≥ %85; determinizm altın hash'leri | ✔ (6 ADR; %97,1; 2 işletim sistemi) |

## Kapsam dışı olduğu için BİLEREK yapılmayanlar (§1.3)

Bunlar eksik değil, şartnamece **yasaktır**:

- SPH/DEM fiziği, EOS, kuvvet hesabı — FAZ 1+
- DART simülasyonu veya Dimorphos kurulumu — FAZ 3
- GPU performans optimizasyonu — köprü yalnızca doğruluk odaklıdır
- `data_manifest/` içeriği (PDS ürünleri) — FAZ 3'te dolar
- `numerics.kernel` ve `numerics.cfl` değerleri — FAZ 1'de dolar; şema
  bunları opsiyonel taşır ve ADR-0006 gereği ancak onları tüketen kod ve
  davranış testiyle birlikte devreye alınacaktır.
- Manifestteki `outputs.*_sha256` alanları sıfır doludur: FAZ 0'da checkpoint
  üretilmez. Bu, geçmiş bir test sonucu olarak sunulmamaktadır.
