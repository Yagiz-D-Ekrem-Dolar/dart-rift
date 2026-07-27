# G0 Kapi Raporu — "Zemin saglam"

*TRUBA / ARF-ACC kanit kosusu — SLURM job 1425495. Bu dosya, hesap dugumunde
uretilen `gate_runs/g0_truba_1425495/G0_report.md` ciktisinin degistirilmemis
kopyasidir.*

- Tarih (UTC): 2026-07-27T13:31:08.893083+00:00
- Makine: kolyoz19 / Linux-5.14.0-427.13.1.el9_4.x86_64-x86_64-with-glibc2.34
- Python: 3.10.15
- GPU ortami: CUDA mevcut
- Kapsam: kapsam=97.2% (esik 85.0%)

| # | Kriter | Sonuc | Kanit |
|---|--------|-------|-------|
| C1 | Depo derleniyor / testler toplaniyor; CI katmani yesil | **GECTI** | pytest cikis kodu=0 (pytest_full.log); kapsam=97.2% (esik 85.0%) |
| C2 | Config sema dogrulayici calisiyor; gecersizler reddediliyor | **GECTI** | tests/test_config.py (15 gecersiz vaka) |
| C3 | Parcacik deposu CPU<->GPU roundtrip bit-esit | **GECTI** | GPU roundtrip: tests/test_particles.py::TestWarpBridgeGpu::test_roundtrip_bitwise_gpu_science PASSED [ 69%] |
| C4 | Tohum determinizmi + shard-degismezligi testleri geciyor | **GECTI** | tests/test_rng.py + tests/test_determinism_golden.py (altin hash) |
| C5 | Invariant cercevesi enjekte edilmis hatalari yakaliyor | **GECTI** | tests/test_invariants.py (enjeksiyon) |
| C6 | HDF5 uc-katman yaz-oku esitligi | **GECTI** | tests/test_io.py (uc katman + checksum) |
| C7 | En az 4 ADR yazilmis | **GECTI** | 5 ADR: ['ADR-0001-soa-vs-aos.md', 'ADR-0002-hassasiyet-politikasi.md', 'ADR-0003-hdf5-yerlesim-checksum.md', 'ADR-0004-rng-mimarisi.md', 'ADR-0005-python-surumu-truba.md'] |
| C8 | Manifest uretimi tam (Ek A alanlari) | **GECTI** | manifest.yaml yazildi; Ek A alan tamligi dogrulandi |

## SONUC: G0 GECTI — FAZ 1 baslayabilir

> Altin kural: Her iddianin arkasinda bir test vardir. Test gecilmediyse iddia edilmez.

---

## Kosu ortami (SLURM ciktisindan)

```
== dugum: kolyoz19 ==
NVIDIA H100 80GB HBM3, 580.95.05
== python: Python 3.10.15 ==
warp 1.15.0
Warp 1.15.0 initialized:
   CUDA Toolkit 12.9, Driver 13.0
   Devices:
     "cpu"      : "x86_64"
     "cuda:0"   : "NVIDIA H100 80GB HBM3" (79 GiB, sm_90, mempool enabled)
   Kernel cache:
     /tmp/drift_1425495/warp_cache/1.15.0
cihazlar: ['cpu', 'cuda:0']
== G0 kapi kosusu bitti; cikis kodu: 0 ==
```

SLURM muhasebesi: `1425495  COMPLETED  0:0  00:00:58  kolyoz19`

## Test ozeti

```
platform linux -- Python 3.10.15, pytest-8.3.5, pluggy-1.5.0
rootdir: /arf/scratch/egitimg16/driftclaude/dart-rift
plugins: cov-7.1.0, typeguard-4.4.1, anyio-4.4.0
collected 185 items
...
185 passed in 9.83s
```

Bu kosuda **hicbir test atlanmadi** (GPU isaretli testler dahil hepsi kosuldu).

### Kapi acisindan kritik test satirlari

```
tests/test_particles.py::TestWarpBridgeGpu::test_roundtrip_bitwise_gpu_science      PASSED
tests/test_particles.py::TestWarpBridgeGpu::test_roundtrip_bitwise_gpu_performance  PASSED
tests/test_particles.py::TestWarpBridgeGpu::test_roundtrip_bitwise_gpu_extreme_values PASSED
tests/test_determinism_golden.py::test_golden_hash_matches                          PASSED
tests/test_rng.py::TestShardInvariance::test_sharded_equals_unsharded_bitwise[1]    PASSED
tests/test_rng.py::TestShardInvariance::test_sharded_equals_unsharded_bitwise[2]    PASSED
tests/test_rng.py::TestShardInvariance::test_sharded_equals_unsharded_bitwise[3]    PASSED
tests/test_rng.py::TestShardInvariance::test_sharded_equals_unsharded_bitwise[5]    PASSED
tests/test_rng.py::TestShardInvariance::test_sharded_equals_unsharded_bitwise[7]    PASSED
tests/test_rng.py::TestShardInvariance::test_sharded_equals_unsharded_bitwise[101]  PASSED
tests/test_io.py::test_snapshot_roundtrip_bitwise                                   PASSED
```

Altin hash (`tests/golden/p0_canonical_v1.json`) Windows/CPython 3.12 uzerinde
uretilmisti; ayni hash Linux/CPython 3.10 + H100 dugumunde dogrulandi. Bu,
platformlar-arasi bit-esit determinizmin kanitidir (P0-QR-03).

## Kapsam (P0-QR-04, esik %85)

```
Name                                  Stmts   Miss  Cover
src/dartrift/__init__.py                  3      0  100.0%
src/dartrift/config.py                   87      0  100.0%
src/dartrift/cpu_math/__init__.py         3      0  100.0%
src/dartrift/cpu_math/reductions.py      19      0  100.0%
src/dartrift/cpu_math/vector.py          20      0  100.0%
src/dartrift/invariants.py               62      0  100.0%
src/dartrift/io_hdf5.py                 139      2   98.6%
src/dartrift/logging_cfg.py             114     11   90.4%
src/dartrift/particles.py               112      4   96.4%
src/dartrift/rng.py                      39      0  100.0%
src/dartrift/units.py                    85      2   97.6%
TOTAL                                   683     19   97.2%
```

## Uretilen kosu manifesti (Ek A)

```yaml
build:
  compiler: cpython-3.10.15
  cuda: (12, 9)
  flags: numpy-1.26.4;precision=deterministic_fp64
config_hash: dfc0fb5f07041742b0f5d7c2de44c5cf85ad013a526c8a97a27fdf1297b1d718
data:
  note: FAZ 0 - veri girisi yok; PDS manifesti FAZ 3'te dolar
git_sha: 3be483a318d215081bd44f7a2a33d3f2763bb6ef
hardware:
  cpu: x86_64
  driver: 580.95.05
  gpu: NVIDIA H100 80GB HBM3
numerics:
  cfl: null
  kernel: null
  precision: deterministic_fp64
outputs:
  checkpoint_sha256: '0000000000000000000000000000000000000000000000000000000000000000'
  observables_sha256: '0000000000000000000000000000000000000000000000000000000000000000'
physics:
  enabled: false
  note: 'FAZ 0: fizik yok'
random_seed: 104729
run_id: P0_smoke_0001
schema_version: 1
status: accepted
timestamp_utc: '2026-07-27T13:31:08.881515+00:00'
wall_time: 17.95632375101559
```

**Durus notu (dururstluk siniri):** `outputs.*_sha256` alanlari sifir doludur.
FAZ 0'da fizik kosusu ve dolayisiyla checkpoint/gozlenebilir dosyasi
uretilmez; alanlar Ek A'yi karsilamak icin bilincli yer tutucudur ve FAZ 1'de
gercek saglamalarla dolacaktir. Bu, gecmis bir testin sonucu olarak
sunulmamaktadir.

## Onceki basarisiz kosular (saklanmaz)

| Job | Dugum | Sonuc | Neden |
|-----|-------|-------|-------|
| 1425468 | palamut5 | FAILED | `pip install --target` -> OSError Errno 5 |
| 1425474 | palamut5 | FAILED | wheel acma -> BadZipFile |
| 1425480 | palamut5 | FAILED | 2 saniyede, stderr bos, cikis 1 |
| 1425489 | palamut5 | FAILED | `echo: write error: Input/output error` (kok neden gorundu) |
| 1425490 | palamut5 | FAILED (10) | kontrollu yazma testi: dd 5MB -> 0 bayt |
| 1425491 | kolyoz19 | COMPLETED | ayni test temiz: 5MB, 587 MB/s |
| **1425495** | **kolyoz19** | **COMPLETED (0)** | **G0 kapi kosusu — 8/8 GECTI** |

Kok neden palamut5 dugumunun /arf uzerine veri yazamamasiydi; kodda veya
wheel'lerde sorun yoktu. Ayrintili gunluk: `docs/defter/`.
