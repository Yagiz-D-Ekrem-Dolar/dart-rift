# İzlenebilirlik Matrisi — FAZ 0, 1, 2

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

---

# FAZ 1 — Hidrodinamik SPH Çekirdeği (DR-RIFT-P1)

## Fonksiyonel gereksinimler (§3.1)

| ID | Gereksinim | Uygulama | Test |
|----|-----------|----------|------|
| P1-FR-01 | GPU hash-grid komşu arama; liste simetrik | `warp_core/hash_grid.py`, `neighbors.py` | `test_neighbors.py` (brute-force ile birebir, simetri, CUDA) |
| P1-FR-02 | Yoğunluk hem toplam hem süreklilikle; çapraz kontrol | `warp_core/density.py` | `test_sod.py::test_continuity_cross_check_tracks_summation` |
| P1-FR-03 | Çiftler-arası antisimetrik ivme; momentum korunur | `warp_core/forces.py` | `test_conservation.py`, `test_sod.py` (duvar-impuls kapanışı) |
| P1-FR-04 | Wendland C2 ve gradyanı doğru normalize | `warp_core/kernel_fn.py` | `test_kernel_fn.py` (∫W dV=1, PoU, gradyan antisimetrisi) |
| P1-FR-05 | Monaghan AV + Balsara; kesmede aşırı sönmez | `warp_core/forces.py` | `test_conservation.py::TestShearBalsara` |
| P1-FR-06 | KDK leapfrog; CFL + ivme kriterli dt | `warp_core/integrator.py`, `timestep.py` | `test_conservation.py`, ADR-0007 ölçümleri |
| P1-FR-07 | Zaman adımı kısıtı yüzdesel kaydedilir | `warp_core/timestep.py` | `test_sod.py::test_timestep_log_present` |

## Doğrulama eşikleri (§3.2)

| ID | Eşik | Test |
|----|------|------|
| P1-VR-01 | Kütle ≈ makine hassasiyeti | `test_conservation.py`, `test_sod.py` |
| P1-VR-02 | Momentum göreli hatası < 1e-6 | `test_conservation.py` (izole senaryolar) |
| P1-VR-03 | Enerji hatası < %0,5 | `test_conservation.py`, `test_sod.py` |
| P1-VR-04 | Sod post-şok %3–5 | `test_sod.py` |
| P1-VR-05 | Sedov r(t) ~%5 | `test_sedov.py` |
| P1-VR-06 | ≥3 çözünürlükte yakınsama | `test_convergence.py` |

**CPU referansı:** `cpu_reference/sph_ref.py` — Warp'tan bağımsız NumPy FP64;
`test_sph_cross.py` bit-yakınlığı ve tekrarda bit-eşitliği sınar.

---

# FAZ 2 — Katı, Porozite, Öz-Yerçekimi (DR-RIFT-P2)

## Fonksiyonel gereksinimler (§3.1)

| ID | Gereksinim | Uygulama | Test |
|----|-----------|----------|------|
| P2-FR-01 | Jaumann objektif gerilme hızı | `warp_core/solid_stress.py`, `cpu_reference/solid_ref.py` | `test_rigid_rotation.py` (+ Jaumann kapalı ablasyonu) |
| P2-FR-02 | von Mises + Y(P) return mapping; plastik iş → u | `warp_core/strength_lundborg.py`, `materials.py` | `test_eos_tillotson.py::TestReturnMapping`, `test_taylor_bar.py` |
| P2-FR-03 | Tillotson EOS, cs güvenli alt-sınırlı | `warp_core/eos_tillotson.py`, `materials.py` | `test_eos_tillotson.py` (kollar, süreklilik, taban) |
| P2-FR-04 | P-α crush-curve; yükleme/boşaltma fiziksel | `warp_core/porosity_palpha.py` | `test_crush_curve.py` (nokta modeli + SPH ablasyonu) |
| P2-FR-05 | Öz-yerçekimi N² + Barnes-Hut, yumuşatmalı | `warp_core/gravity_tree.py`, `cpu_reference/gravity_ref.py` | `test_two_body.py`, `test_uniform_sphere.py`, `test_cold_collapse.py` |
| P2-FR-06 | Her modül config ile açılıp kapanır | `config.py::PhysicsConfig`, `MaterialParams.from_config` | `test_ablation.py`, `test_config_wiring_p2.py` |

## Doğrulama eşikleri (§3.2)

| ID | Eşik | Test |
|----|------|------|
| P2-VR-01 | Rijit dönme yapay gerilme ≈0 | `test_rigid_rotation.py` |
| P2-VR-02 | Taylor bar son şekil benchmark'a yakın | `test_taylor_bar.py` (GPU) |
| P2-VR-03 | Elastik dalga √((K+4G/3)/ρ) | `test_elastic_wave.py` (yakınsama merdiveni) |
| P2-VR-04 | Crush curve fiziksel; α≥1 | `test_crush_curve.py` |
| P2-VR-05 | İki-cisim/küre; drift sınırlı | `test_two_body.py`, `test_uniform_sphere.py` |
| P2-VR-06 | Global korunum (yerçekimi dahil) | `test_cold_collapse.py` |

**FAZ 1'e indirgeme:** Tüm modüller kapalıyken katı çözücü FAZ 1
hidrodinamiğine bit-yakın indirgenmelidir —
`test_solid_cross.py::TestReductionToPhase1`. Bu bekçi, geliştirme sırasında
iki ayrı hatayı yakaladı (bkz. ADR-0009).

---

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
