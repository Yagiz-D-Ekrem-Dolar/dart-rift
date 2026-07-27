# DART-RIFT — FAZ 0: Temel Altyapı ve Test İskeleti

> Dimorphos için GPU hızlandırmalı SPH şok-fiziği motoru ve Bayesçi iç-yapı
> çıkarımı projesinin **G0 kapısı** ("zemin sağlam") uygulaması.
> Şartname: `DR-RIFT-P0 v1.0` · Ana Plan: `DART-RIFT Ana Proje Planı v1.0`

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
python scripts/run_g0_gate.py               # G0 kapı raporu üret
```

## TRUBA (ARF-ACC) üzerinde G0 kanıtı

TRUBA kuralları gereği `/arf`'a pip/conda kurulumu yapılmaz; merkezî modül
kullanılır, warp-lang wheel'i job-yerel diske açılır:

```bash
# giriş düğümünde bir kez: wheel'leri indir
pip download warp-lang pytest-cov coverage -d /arf/scratch/<grup>/driftclaude/wheels

# GPU kuyruğuna gönder (16 çekirdek + 1 GPU zorunlu)
sbatch slurm/faz0_g0_gate.sh
```

Kapı kanıtları `gate_runs/<koşu>/G0_report.md` + `manifest.yaml` içinde üretilir;
kabul edilen kanıtlar `docs/evidence/` altına kopyalanıp sürümlenir.

## G0 kapı kriterleri (DR-RIFT-P0 §9)

1. Depo derleniyor; CI (commit katmanı) yeşil
2. Config şema doğrulayıcı çalışıyor; geçersiz vakalar reddediliyor
3. Parçacık deposu CPU↔GPU roundtrip **bit-eşit**
4. Tohum determinizmi ve shard-değişmezliği testleri geçiyor
5. Invariant çerçevesi enjekte edilmiş hataları yakalıyor
6. HDF5 üç-katman yaz-oku eşitliği sağlanıyor
7. En az 4 ADR yazılmış (`docs/adr/`)
8. Manifest üretimi tam (Ek A alanları)

## Dürüstlük sınırı

- Fiziği motor çözecek; bu faz yalnızca zemindir. **Test geçilmediyse iddia edilmez.**
- Her büyük teknik karar bir ADR ile kayıtlıdır; sessiz değişiklik yasaktır.
- Başarısız denemeler ve negatif sonuçlar saklanmaz; mühendislik defterine işlenir
  (`docs/defter/`).

## Lisans

MIT — bkz. [LICENSE](LICENSE). Atıf için [CITATION.cff](CITATION.cff).
