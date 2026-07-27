# DART-RIFT — FAZ 0: Temel Altyapı ve Test İskeleti

> Dimorphos için GPU hızlandırmalı SPH şok-fiziği motoru ve Bayesçi iç-yapı
> çıkarımı projesinin **G0 kapısı** ("zemin sağlam") uygulaması.
> Şartname: `DR-RIFT-P0 v1.0` · Ana Plan: `DART-RIFT Ana Proje Planı v1.0`

**G0 durumu: GEÇTİ** — kapı 8/8, kırmızı takım (§12) 6/6 temiz, 219 test,
kapsam %97,1. Kanıt koşusu: TRUBA/ARF-ACC `palamut4`, NVIDIA A100-SXM4-80GB,
SLURM job 1425656, temiz git ağacı
([kapı + kırmızı takım raporu](docs/evidence/G0_report_truba_1425656.md)).
CPU↔GPU bit-eşit roundtrip **üç GPU mimarisinde** doğrulandı: sm_80 (A100),
sm_90 (H100), sm_86 (RTX 3050).
Bu, altyapının geçtiği anlamına gelir — **hiçbir fizik veya bilimsel sonuç
iddia edilmemektedir**; FAZ 0'da fizik yoktur.

## Proje tek cümlede

NASA'nın DART aracının Dimorphos'a çarpmasından elde edilen verilerden,
asteroidin **içinin neye benzediğini olasılıksal olarak** geri hesaplıyoruz ve bu
tahmini ESA'nın Hera aracı oraya varıp ölçmeden **önce** kilitliyoruz.

Bu depo o motorun **FAZ 0** katmanıdır: hiçbir fizik içermez; fiziğin üzerine
güvenle inşa edileceği deterministik, sürümlenmiş, test edilebilir ve
denetlenebilir zemini kurar. **G0 kapısı geçilmeden hiçbir DART/fizik koşusu
çalıştırılamaz.**

## FAZ 0 kapsamı (DR-RIFT-P0)

| Modül | Gereksinim | İçerik |
|-------|------------|--------|
| `dartrift.units` | P0-FR-01 | SI birim sistemi, sabitler, boyut analizi (`UnitError`) |
| `dartrift.config` | P0-FR-02, P0-DR-01 | Sürümlü YAML şeması (pydantic), 15 geçersiz vaka kataloğu |
| `dartrift.particles` | P0-FR-03 | SoA parçacık deposu + Warp CPU↔GPU köprüsü (bit-eşit roundtrip) |
| `dartrift.rng` | P0-FR-04 | Tek kök tohum, adlandırılmış akışlar, **shard-değişmez** örnekleme |
| `dartrift.invariants` | P0-FR-05 | NaN/Inf, kütle/yoğunluk, hasar, distansiyon, sınır denetimi |
| `dartrift.logging_cfg` | P0-FR-06, P0-DR-02 | JSONL log + Ek A manifest üreteci/doğrulayıcı |
| `dartrift.io_hdf5` | P0-FR-07 | 3 katman: `scalar_budget` / `sparse_snapshot` / `event_catalog` |
| `dartrift.cpu_math` | — | NumPy referans vektör matematiği, sabit-sıralı Kahan indirgeme |

Kapsam dışı (bu fazda **yasak**): SPH/DEM fiziği, EOS, kuvvet hesabı, DART
simülasyonu, GPU performans optimizasyonu.

## Kurulum ve test

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev,gpu]"    # gpu = warp-lang (CPU cihazıyla da çalışır)
pytest tests -m "not gpu" --cov=dartrift    # GPU'suz ortam
pytest tests --cov=dartrift                 # CUDA'lı ortam (roundtrip dahil)
python scripts/run_red_team.py              # §12 kırmızı-takım kontrol listesi
python scripts/run_g0_gate.py               # G0 kapısı (CUDA ister)
```

`run_g0_gate.py` CUDA bulunmayan bir makinede **kapı geçti demez**: C3
kanıtlanamadığı için exit 2 döner. Yalnızca ön kontrol istiyorsanız
`--allow-no-gpu` ekleyin; o mod da "G0 GEÇTİ" iddiası üretmez.

## TRUBA (ARF-ACC) üzerinde G0 kanıtı

TRUBA kuralları gereği `/arf`'a pip/conda ile **kurulum yapılmaz**; merkezî
modül kullanılır ve ek paketler wheel arşivleri açılarak `PYTHONPATH` üzerinden
kullanılır (639 dosya; inode kotası 500.000). Hazırlık **giriş düğümünde bir
kez** yapılır:

```bash
cd /arf/scratch/<grup>/driftclaude
module purge && module load apps/truba-ai/gpu-2024.0
python3 -m pip download warp-lang pytest-cov coverage --no-deps -d wheels
mkdir -p pylib && for w in wheels/*.whl; do python3 -m zipfile -e "$w" pylib; done
```

Ardından kapı koşusu GPU kuyruğuna gönderilir (16 çekirdek + 1 GPU zorunlu):

```bash
sbatch slurm/faz0_g0_gate.sh
```

Kapı kanıtları `gate_runs/<koşu>/G0_report.md` + `manifest.yaml` içinde üretilir;
kabul edilen kanıtlar `docs/evidence/` altına kopyalanıp sürümlenir.

> **Kuyruk notu:** Kanıt koşuları `kolyoz-cuda` (`-C H100`) üzerinde yapılır.
> `palamut-cuda`'daki `palamut5` düğümü `/arf`'a veri yazamıyordu (metadata
> yazılıyor, 5 MB `dd` → 0 bayt); ayırt edici test ve kök neden analizi
> [KAYIT-001](docs/defter/KAYIT-001_2026-07-27_FAZ0.md) içinde.

## G0 kapı kriterleri (DR-RIFT-P0 §9) ve kanıtlanan sonuç

| # | Kriter | Sonuç (job 1425656) |
|---|--------|---------------------|
| 1 | Depo derleniyor; CI (commit katmanı) yeşil | GEÇTİ — 219 test, kapsam %97,1 |
| 2 | Config şema doğrulayıcı; geçersizler reddediliyor | GEÇTİ — 15 geçersiz vaka |
| 3 | Parçacık deposu CPU↔GPU roundtrip **bit-eşit** | GEÇTİ — `cuda:0`, FP64/FP32/uç değerler |
| 4 | Tohum determinizmi ve shard-değişmezliği | GEÇTİ — shard 1/2/3/5/7/101 aynı sonuç |
| 5 | Invariant çerçevesi enjekte hataları yakalıyor | GEÇTİ — 13 enjeksiyon vakası |
| 6 | HDF5 üç-katman yaz-oku eşitliği | GEÇTİ — checksum dahil |
| 7 | En az 4 ADR yazılmış (`docs/adr/`) | GEÇTİ — 5 ADR |
| 8 | Manifest üretimi tam (Ek A alanları) | GEÇTİ — alan tamlığı zorlanıyor |

Altın hash Windows/CPython 3.12'de üretildi ve Linux/CPython 3.10 + H100
düğümünde birebir doğrulandı; platformlar arası bit-eşit determinizm bu
şekilde kanıtlanmıştır (P0-QR-03).

### Kırmızı takım (DR-RIFT-P0 §12)

Şartname bu listeyi teslim şartı sayar. Otomatik işletilir
(`python scripts/run_red_team.py`) ve her TRUBA kanıt koşusunda kapıdan önce
çalışır. Altı maddenin tamamı temiz: platformlar arası hash, shard
değişmezliği (1–257), 15 geçersiz config'in tamamının reddi, manifestten
koşunun yeniden üretilmesi + kurcalama tespiti, invariant ihlalinin koşuyu
durdurması, kapatılmış çıktı katmanının sessizce yutulmaması.

## Dürüstlük sınırı

- Fiziği motor çözecek; bu faz yalnızca zemindir. **Test geçilmediyse iddia edilmez.**
- Her büyük teknik karar bir ADR ile kayıtlıdır; sessiz değişiklik yasaktır.
- Başarısız denemeler ve negatif sonuçlar saklanmaz; mühendislik defterine işlenir
  (`docs/defter/`).

## Lisans

MIT — bkz. [LICENSE](LICENSE). Atıf için [CITATION.cff](CITATION.cff).
