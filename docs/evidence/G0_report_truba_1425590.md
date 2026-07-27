# G0 Kapi Raporu + Kirmizi Takim — NIHAI KANIT (job 1425590)

*TRUBA / ARF-ACC, temiz calisma agacindan uretilmis kanit kosusu. Bu kosu,
`G0_report_truba_1425495.md` kanitinin yerini alir: ondan sonra bulunan uc
kusur giderildi ve §12 kirmizi-takim listesi ilk kez isletildi.*

- Tarih (UTC): 2026-07-27T14:12:11
- Makine: kolyoz19 / Linux-5.14.0-427.13.1.el9_4.x86_64, NVIDIA H100 80GB HBM3
- Python 3.10.15 · Warp 1.15.0 (CUDA Toolkit 12.9, surucu 580.95.05)
- SLURM: `1425590  COMPLETED  0:0  00:00:17  kolyoz19`
- **git_sha: `260f1324dce8e3b1349897a0028217a93c450c1e`** (dirty isareti YOK)

## Bolum 1 — Kirmizi-takim kontrol listesi (DR-RIFT-P0 §12)

| # | Soru | Sonuc | Kanit |
|---|------|-------|-------|
| RT1 | Ayni config + tohum iki farkli makinede ayni hash'i veriyor mu? | **TEMIZ** | bu platform=Linux/CPython 3.10.15, hash=ESLESTI; dogrulanan platformlar=['Linux/CPython 3.10.15', 'Windows/CPython 3.12.10'] |
| RT2 | Shard sayisini degistirmek sonucu degistiriyor mu? | **TEMIZ** | shard 1..257 (9 vaka); sapan=yok |
| RT3 | Gecersiz her config gercekten reddediliyor mu? | **TEMIZ** | 15 gecersiz vaka; sessizce kabul edilen=yok |
| RT4 | Manifest, kosuyu sifirdan yeniden uretmeye yetiyor mu? | **TEMIZ** | config manifestten geri kuruldu (hash ayni), ayni depo modu, kurcalama tespiti calisiyor |
| RT5 | Bir invariant ihlali kosuyu durduruyor mu? | **TEMIZ** | 6 enjeksiyon; yakalanmayan=yok |
| RT6 | Kapatilmis cikti katmanina yazmak sessizce yutuluyor mu? | **TEMIZ** | kapali katmana yazma acik hata verdi |

**Sonuc: Tum maddeler temiz.**

## Bolum 2 — G0 kapisi (DR-RIFT-P0 §9)

| # | Kriter | Sonuc | Kanit |
|---|--------|-------|-------|
| C1 | Depo derleniyor; CI katmani yesil | **GECTI** | pytest cikis kodu=0; kapsam=97.4% (esik 85.0%) |
| C2 | Config sema dogrulayici; gecersizler reddediliyor | **GECTI** | 15 gecersiz vaka |
| C3 | Parcacik deposu CPU<->GPU roundtrip bit-esit | **GECTI** | `TestWarpBridgeGpu::test_roundtrip_bitwise_gpu_science PASSED` (cuda:0) |
| C4 | Tohum determinizmi + shard-degismezligi | **GECTI** | altin hash + shard testleri |
| C5 | Invariant cercevesi enjekte hatalari yakaliyor | **GECTI** | enjeksiyon testleri |
| C6 | HDF5 uc-katman yaz-oku esitligi | **GECTI** | checksum dahil |
| C7 | En az 4 ADR | **GECTI** | 6 ADR (ADR-0001..0006) |
| C8 | Manifest uretimi tam (Ek A) | **GECTI** | alan tamligi yazim aninda zorlandi |

**SONUC: G0 GECTI — FAZ 1 baslayabilir.**

## Test ve kapsam

```
210 passed in 5.95s          # hicbir test atlanmadi (GPU testleri dahil)

Name                                  Stmts   Miss  Cover
src/dartrift/__init__.py                  3      0  100.0%
src/dartrift/config.py                   96      0  100.0%
src/dartrift/cpu_math/__init__.py         3      0  100.0%
src/dartrift/cpu_math/reductions.py      19      0  100.0%
src/dartrift/cpu_math/vector.py          20      0  100.0%
src/dartrift/invariants.py               62      0  100.0%
src/dartrift/io_hdf5.py                 164      2   98.8%
src/dartrift/logging_cfg.py             123     11   91.1%
src/dartrift/particles.py               115      4   96.5%
src/dartrift/rng.py                      39      0  100.0%
src/dartrift/units.py                    85      2   97.6%
TOTAL                                   729     19   97.4%
```

## Kosu manifesti (Ek A) — artik config GOMULU

```yaml
build:
  compiler: cpython-3.10.15
  cuda: (12, 9)
  flags: numpy-1.26.4;precision=deterministic_fp64
config:                       # <-- yeni: kosu tek basina yeniden uretilebilir
  domain:
    max: [1000.0, 1000.0, 1000.0]
    min: [-1000.0, -1000.0, -1000.0]
  io:
    hdf5_compression: gzip
    output_layers: [scalar_budget, sparse_snapshot, event_catalog]
  numerics: {cfl: null, kernel: null, precision: deterministic_fp64}
  random_seed: 104729
  run_id: P0_smoke_0001
  schema_version: 1
config_hash: dfc0fb5f07041742b0f5d7c2de44c5cf85ad013a526c8a97a27fdf1297b1d718
data: {note: 'FAZ 0 - veri girisi yok; PDS manifesti FAZ 3''te dolar'}
git_sha: 260f1324dce8e3b1349897a0028217a93c450c1e
hardware: {cpu: x86_64, driver: 580.95.05, gpu: NVIDIA H100 80GB HBM3}
numerics: {cfl: null, kernel: null, precision: deterministic_fp64}
outputs:
  checkpoint_sha256: '0000...0000'
  observables_sha256: '0000...0000'
physics: {enabled: false, note: 'FAZ 0: fizik yok'}
random_seed: 104729
run_id: P0_smoke_0001
schema_version: 1
status: accepted
timestamp_utc: '2026-07-27T14:12:11.375001+00:00'
wall_time: 8.998244747985154
```

**Durustluk notu:** `outputs.*_sha256` sifir doludur. FAZ 0'da fizik kosusu ve
checkpoint uretilmez; bu alanlar Ek A'yi karsilayan bilincli yer tutuculardir ve
gecmis bir test sonucu olarak sunulmamaktadir.

## Bu kosuyu oncekinden ayiran nedir

Job 1425495 de sekiz kriteri geciyordu. Teslim oncesi oz-denetimde su uc kusur
bulundu ve giderildi:

1. **Sessiz config sapmasi.** Sema `numerics.precision`, `io.output_layers`,
   `io.hdf5_compression` ve `domain` alanlarini dogruluyor ama motor bunlari
   okumuyordu. `performance_mixed` yazan bir kosu FP64 kalir, tek katman
   isteyen bir kosu uc katman yazardi — ve manifest yine "dogru" degeri
   raporlardi. Duzeltme + 17 davranis testi: ADR-0006.
2. **Manifest kosuyu yeniden uretmeye yetmiyordu.** Yalnizca `config_hash`
   vardi; hash "ayni mi?" der, "neydi?" demez. Artik kanonik config gomulu ve
   `config_from_manifest()` kurcalamayi da yakaliyor.
3. **§12 kirmizi-takim listesi hic isletilmemisti.** Yol Haritasi §7.5 bunu
   teslim sarti sayiyor; artik `scripts/run_red_team.py` ile her kanit
   kosusunda otomatik isletiliyor (Bolum 1).

## Altyapi arizalari (kapi sonucu degildir)

| Job | Dugum | Durum | Aciklama |
|-----|-------|-------|----------|
| 1425468/74/80/89 | palamut5 | FAILED | dugum /arf'a veri yazamiyor |
| 1425490 | palamut5 | FAILED (10) | ayirt edici test: dd 5MB -> 0 bayt |
| 1425491 | kolyoz19 | COMPLETED | ayni test temiz: 587 MB/s |
| 1425588 | kolyoz13 | FAILED (6) | "No devices were found" — GPU surucu arizasi |
| 1425589 | kolyoz19 | COMPLETED | kirmizi takim + kapi (agac kirliydi) |
| **1425590** | **kolyoz19** | **COMPLETED (0)** | **nihai kanit, temiz agac** |

SLURM betigi artik GPU'yu erken sorgular ve arizali dugumde EX_TEMPFAIL (75) ile
cikar; boylece donanim arizasi kapi basarisizligi gibi gorunmez.
