# G0 Kapı Raporu + Kırmızı Takım — NİHAİ KANIT (job 1425656)

*TRUBA / ARF-ACC, temiz çalışma ağacından üretilmiş kanıt koşusu. Bu koşu,
`G0_report_truba_1425590.md` kanıtının yerini alır: ondan sonra yapılan üçüncü
denetim turunda iki kusur daha bulunup giderildi.*

- Tarih (UTC): 2026-07-27
- Makine: **palamut4** / NVIDIA **A100-SXM4-80GB** (sm_80), sürücü 570.86.15
- Python 3.10.15 · Warp 1.15.0 (CUDA Toolkit 12.9)
- SLURM: `1425656  COMPLETED  0:0  00:00:36  palamut4`
- **git_sha: `4528baf11b58b1b1d5090d89acbd2c16c25a1f51`** (dirty işareti YOK)

## Bölüm 1 — Kırmızı-takım kontrol listesi (DR-RIFT-P0 §12)

| # | Soru | Sonuç | Kanıt |
|---|------|-------|-------|
| RT1 | Aynı config + tohum iki farklı makinede aynı hash'i veriyor mu? | **TEMİZ** | hash=EŞLEŞTİ; doğrulanan platformlar: Linux/CPython 3.10.15, Windows/CPython 3.12.10 |
| RT2 | Shard sayısını değiştirmek sonucu değiştiriyor mu? | **TEMİZ** | shard 1..257 (9 vaka); sapan=yok |
| RT3 | Geçersiz her config gerçekten reddediliyor mu? | **TEMİZ** | 15 geçersiz vaka; sessizce kabul edilen=yok |
| RT4 | Manifest, koşuyu sıfırdan yeniden üretmeye yetiyor mu? | **TEMİZ** | config manifestten geri kuruldu (hash aynı), aynı depo modu, kurcalama tespiti çalışıyor |
| RT5 | Bir invariant ihlali koşuyu durduruyor mu? | **TEMİZ** | 6 enjeksiyon; yakalanmayan=yok |
| RT6 | Kapatılmış çıktı katmanına yazmak sessizce yutuluyor mu? | **TEMİZ** | kapalı katmana yazma açık hata verdi |

**Sonuç: Tüm maddeler temiz.**

## Bölüm 2 — G0 kapısı (DR-RIFT-P0 §9)

| # | Kriter | Sonuç | Kanıt |
|---|--------|-------|-------|
| C1 | Depo derleniyor; CI katmanı yeşil | **GEÇTİ** | pytest çıkış kodu=0; kapsam=97.1% (eşik 85.0%) |
| C2 | Config şema doğrulayıcı; geçersizler reddediliyor | **GEÇTİ** | 15 geçersiz vaka |
| C3 | Parçacık deposu CPU↔GPU roundtrip bit-eşit | **GEÇTİ** | `TestWarpBridgeGpu::test_roundtrip_bitwise_gpu_science PASSED` (cuda:0, A100) |
| C4 | Tohum determinizmi + shard-değişmezliği | **GEÇTİ** | altın hash + shard testleri |
| C5 | Invariant çerçevesi enjekte hataları yakalıyor | **GEÇTİ** | enjeksiyon testleri |
| C6 | HDF5 üç-katman yaz-oku eşitliği | **GEÇTİ** | checksum dahil |
| C7 | En az 4 ADR | **GEÇTİ** | 6 ADR (ADR-0001..0006) |
| C8 | Manifest üretimi tam (Ek A) | **GEÇTİ** | alan tamlığı yazım anında zorlandı |

**SONUÇ: G0 GEÇTİ — FAZ 1 başlayabilir.**

## Üç GPU mimarisinde bit-eşit roundtrip

Determinizm iddiası tek bir donanıma bağlı değildir. Aynı roundtrip testleri
(FP64, FP32 ve uç değerler: float64 max, tiny, inf, NaN) üç ayrı mimaride
bit-eşit sonuç verdi:

| Mimari | GPU | Ortam |
|--------|-----|-------|
| sm_80 | NVIDIA A100-SXM4-80GB | TRUBA palamut4 — **bu koşu** |
| sm_90 | NVIDIA H100 80GB HBM3 | TRUBA kolyoz19 (job 1425590) |
| sm_86 | NVIDIA GeForce RTX 3050 Laptop | yerel geliştirme makinesi |

Altın hash de iki işletim sisteminde (Windows/CPython 3.12, Linux/CPython 3.10)
birebir aynı çıktı.

## Test ve kapsam

```
219 passed in 4.99s          # hiçbir test atlanmadı (GPU testleri dahil)

Name                                  Stmts   Miss  Cover
src/dartrift/__init__.py                  3      0  100.0%
src/dartrift/config.py                   96      0  100.0%
src/dartrift/cpu_math/__init__.py         3      0  100.0%
src/dartrift/cpu_math/reductions.py      19      0  100.0%
src/dartrift/cpu_math/vector.py          20      0  100.0%
src/dartrift/failure.py                  29      0  100.0%
src/dartrift/invariants.py               62      0  100.0%
src/dartrift/io_hdf5.py                 164      2   98.8%
src/dartrift/logging_cfg.py             125     12   90.4%
src/dartrift/particles.py               118      6   94.9%
src/dartrift/rng.py                      39      0  100.0%
src/dartrift/units.py                    85      2   97.6%
TOTAL                                   763     22   97.1%
```

## Bu koşuyu 1425590'dan ayıran nedir

Üçüncü denetim turunda iki kusur bulundu ve giderildi:

4. **§6.2'nin son satırı uygulanmamıştı.** Şartname sözde-kodu "ihlal →
   koşuyu `numerical_failure` etiketiyle durdur, config dondur" diyor. İhlal
   yakalanıyordu ama `numerical_failure` durumu hiç üretilmiyor, başarısız
   koşunun config'i dondurulmuyordu. `src/dartrift/failure.py` eklendi:
   başarısız koşu da tam manifest (Ek A) + dondurulmuş config + ihlal raporu
   üretir ve manifestten yeniden üretilebilir. 9 test.
5. **Kapı koşucusu GPU'suz ortamda "G0 GEÇTİ" diyordu.** `--require-gpu`
   verilmezse CUDA'sız makinede C3 GEÇTİ sayılıyordu — koşulmamış bir test
   geçmiş sayılıyordu. Artık CUDA yoksa C3 **KANITLANAMADI**, rapor başlığı
   "ÖN-KONTROL (KAPI DEĞİL)" olur ve metin hiçbir koşulda "G0 GECTI" içermez.
   Bu davranış gerçek GPU'suz bir ortamda (GitHub CI runner) doğrulanıyor.

Ayrıca manifestteki CUDA sürümü artık `12.9` biçiminde (önce ham tuple
`(12, 9)` yazılıyordu) ve `ParticleStore.__getattr__` kopyalama sırasında
sonsuz özyinelemeye karşı korundu.

## Altyapı arızaları (kapı sonucu değildir)

| Job | Düğüm | Durum | Açıklama |
|-----|-------|-------|----------|
| 1425468/74/80/89 | palamut5 | FAILED | düğüm /arf'a veri yazamıyor |
| 1425490 | palamut5 | FAILED (10) | ayırt edici test: dd 5MB → 0 bayt |
| 1425491 | kolyoz19 | COMPLETED | aynı test temiz: 587 MB/s |
| 1425588 | kolyoz13 | FAILED (6) | "No devices were found" — GPU sürücü arızası |
| 1425589/90 | kolyoz19 | COMPLETED | önceki kanıt turu |
| 1425652 | — | CANCELLED | kolyoz-cuda dolu; palamut'a taşındı |
| **1425656** | **palamut4** | **COMPLETED (0)** | **nihai kanıt, temiz ağaç** |

**palamut4'ün sorunsuz çalışması, depolama arızasının `palamut-cuda` kuyruğuna
değil yalnızca `palamut5` düğümüne özgü olduğunu doğrular.** SLURM betiği
arızalı düğümde EX_TEMPFAIL (75) ile çıkar; bu bir kapı sonucu değildir.

> Not: Betikteki `-C H100` kısıtı kolyoz kuyruğu içindir. palamut (A100)
> kuyruğunda koşarken komut satırından geçersiz kılınır:
> `sbatch -p palamut-cuda -C palamut --exclude=palamut5 slurm/faz0_g0_gate.sh`
