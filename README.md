# DART-RIFT

> Dimorphos için GPU hızlandırmalı SPH şok-fiziği motoru ve Bayesçi iç-yapı
> çıkarımı projesi.
> Şartname: `DR-RIFT-P0/P1/P2 v1.0` · Ana Plan: `DART-RIFT Ana Proje Planı v1.0`

NASA'nın DART aracının Dimorphos'a çarpmasından elde edilen verilerden,
asteroidin **içinin neye benzediğini olasılıksal olarak** geri hesaplamayı ve
bu tahmini ESA'nın Hera aracı oraya varıp ölçmeden **önce** kilitlemeyi
hedefliyoruz.

Bu depo, o çıkarımın dayanacağı **motoru** içerir: deterministik altyapı
(FAZ 0), SPH şok-fiziği çekirdeği (FAZ 1) ve gerçek malzeme fiziği — dayanım,
gözeneklilik, öz-yerçekimi (FAZ 2).

## Kapı durumu

Her faz, şartnamedeki kabul ölçütlerini **kanıtla** geçmeden bir sonrakine
geçilmez. Kanıtlar TRUBA/ARF-ACC üzerinde, temiz git ağacıyla üretilir.

| Kapı | Kapsam | Sonuç | Kanıt |
|---|---|---|---|
| **G0** | Zemin sağlam (altyapı) | **GEÇTİ** 8/8 | [rapor](docs/evidence/G0_report_truba_1425656.md) — `palamut4` A100, iş 1425656 |
| **G1** | Şok motoru çalışıyor | **GEÇTİ** 8/8 | [rapor](docs/evidence/G1_report_truba_1426162.md) — `kolyoz9` H100, iş 1426162 |
| **G2** | Gerçek malzeme fiziği | **GEÇTİ** 7/7 | [rapor](docs/evidence/G2_report_truba_1426596.md) — `kolyoz23` H100, iş 1426596 |

Son kanıt koşusunda **360 test geçti / 0 kaldı**. G0 ayrıca kırmızı takım
(§12) 6/6 temiz. CPU↔GPU bit-eşit roundtrip üç GPU mimarisinde doğrulandı:
sm_80 (A100), sm_90 (H100), sm_86 (RTX 3050). G1, iki farklı düğümde (kolyoz9
ve kolyoz23) koşuldu ve sekiz ölçütün kanıt sayıları birebir aynı çıktı.

> **Kapsam sınırı:** Kapılar motorun **doğrulama senaryolarını** geçtiği
> anlamına gelir. Dimorphos hakkında **henüz hiçbir bilimsel sonuç iddia
> edilmemektedir**; çarpma koşuları FAZ 3'tedir.

## Doğrulama sonuçları

Motorun analitik/deneysel referanslara karşı ölçülen hataları:

| Senaryo | Referans | Ölçülen | Eşik |
|---|---|---|---|
| Sod şok tüpü | Kesin Riemann (Toro) | şok hızı %0,08; post-şok en kötü %0,80 | %3–5 |
| Sedov-Taylor patlaması | Benzerlik çözümü | şok yarıçapı **%4,46** | %5 |
| Yakınsama | L1(ρ), 64→256 | 0,0200 → 0,0134 → 0,0111 (monoton) | azalmalı |
| Kütle korunumu | — | **0,00e+00** | ~makine hassasiyeti |
| Momentum korunumu | — | **8,39e-16** | 1e-6 |
| Enerji korunumu | — | %0,432 | %0,5 |
| Rijit dönme (objektiflik) | Jaumann | %1,66 (Jaumann kapalıyken %200) | — |
| Elastik dalga hızı | 4593 m/s teorik | 4458 m/s → %2,96 | %3 |
| Taylor bar (bakır) | Deney bandı 0,60–0,80 | **L/L0 = 0,731**, enerji %0,083 | %1,5 |
| İki-cisim (20 yörünge) | Kepler | E hatası 2,4e-07, yarıçap drifti 1,3e-08 | — |
| Soğuk çöküş | — | enerji %0,36; momentum 1,2e-17 | %1; 1e-6 |

### Marj analizi — kapılar yeşil, ama bazıları kılpayı

Bir ölçütün geçmesi, sağlam geçtiği anlamına gelmez. Altı ölçüt eşiğine
%20'den yakın:

| Ölçüt | Ölçülen | Eşik | Marj |
|---|---|---|---|
| Elastik dalga hızı | %2,96 | %3 | **1,01×** |
| Yerçekimi: kabuk hatası | %4,65 | %5 | 1,08× |
| Sedov şok yarıçapı | %4,46 | %5 | 1,12× |
| Enerji korunumu | %0,432 | %0,5 | 1,16× |
| Yerçekimi: BH↔doğrudan medyan | %0,43 | %0,5 | 1,16× |
| von Mises drifti | %1,66 | %2 | 1,20× |

Bunların hiçbiri gizlenmiyor; ölçülen değerler yukarıdaki tabloda ve kapı
raporlarındadır. İkisinin davranışı ayrıca incelendi:

- **Elastik dalga** hatası çözünürlükle sıfıra yakınsıyor (%9,24 → %5,49 →
  %4,32 → %2,96, yaklaşık birinci mertebe). Sistematik bir taban yok; daha
  ince kafes marjı büyütür.
- **Sedov** hatası ise ~%3,9'luk bir **tabana** iniyor (n=112'ye kadar
  ölçüldü). Bu ayrıklaştırma değil, sonlu enjeksiyon yarıçapının model-form
  hatası — [ADR-0011](docs/adr/ADR-0011-sedov-yakinsama-kurulumu.md).

### Bilinen sınırlama

Sedov'da **enerji hatası çözünürlükle büyüyor** ve n≥96'da %0,5 bütçesini
aşıyor (%0,510 → %0,534). Kapı merdiveni n=64'te bittiği için bu ölçütte
görünmez. Mevcut KDK+trapez şemasıyla (ADR-0007) enerji bütçesi ~300 adımı
aşan koşularda tutmuyor; FAZ 3 daha uzun koşular gerektireceği için orada
çözülmesi gereken açık bir maddedir. Kapı ölçütü **gevşetilmedi**.

## Mimari

Her GPU çekirdeğinin **Warp'tan bağımsız bir NumPy FP64 referansı** vardır ve
ikisi çapraz kontrol edilir (tipik sapma < 1e-8). Bu, tek başına yeşil görünen
bir GPU çekirdeğinin yanlış ayrıklaştırma yapmasını engeller — nitekim
[ADR-0015](docs/adr/ADR-0015-sureklilik-yogunlugu.md) bu kontrolün yakaladığı
gerçek bir çekirdek hatasını kaydeder.

### FAZ 0 — Altyapı (DR-RIFT-P0)

| Modül | Gereksinim | İçerik |
|---|---|---|
| `units` | P0-FR-01 | SI birim sistemi, sabitler, boyut analizi (`UnitError`) |
| `config` | P0-FR-02, P0-DR-01 | Sürümlü YAML şeması (pydantic), 15 geçersiz vaka kataloğu |
| `particles` | P0-FR-03 | SoA parçacık deposu + Warp CPU↔GPU köprüsü (bit-eşit roundtrip) |
| `rng` | P0-FR-04 | Tek kök tohum, adlandırılmış akışlar, **shard-değişmez** örnekleme |
| `invariants` | P0-FR-05 | NaN/Inf, kütle/yoğunluk, hasar, distansiyon, sınır denetimi |
| `logging_cfg` | P0-FR-06, P0-DR-02 | JSONL log + Ek A manifest üreteci/doğrulayıcı |
| `io_hdf5` | P0-FR-07 | 3 katman: `scalar_budget` / `sparse_snapshot` / `event_catalog` |
| `cpu_math` | — | NumPy referans vektör matematiği, sabit-sıralı Kahan indirgeme |

### FAZ 1 — SPH şok motoru (DR-RIFT-P1)

| Modül | Gereksinim | İçerik |
|---|---|---|
| `warp_core/kernel_fn` | P1-FR-04 | Wendland C2 çekirdeği (FP64 tipli sabitlerle) |
| `warp_core/hash_grid`, `neighbors` | P1-FR-01 | GPU hash-grid komşu arama + parite testleri |
| `warp_core/density` | P1-FR-02 | Toplama **ve** süreklilik yoğunluğu, çapraz kontrol |
| `warp_core/forces` | P1-FR-03/05 | Çift-antisimetrik kuvvet, tutarlı enerji, Monaghan AV + Balsara |
| `warp_core/integrator` | P1-FR-06 | KDK leapfrog + tam-trapez u/S güncellemesi |
| `warp_core/timestep` | P1-FR-06/07 | CFL + ivme kriterleri, kısıt sınıfı tanısı |
| `warp_core/solver` | P1 §4.1 | 1B/3B çözücü orkestrasyonu (kernel sırası sözleşmesi) |
| `cpu_reference/sph_ref` | — | Warp'tan bağımsız NumPy FP64 referansı |
| `validation/riemann`, `sod`, `sedov`, `plate`, `conservation` | P1-VR-01..06 | Kesin Riemann, Sod, Sedov, plate impact, korunum |

### FAZ 2 — Malzeme fiziği (DR-RIFT-P2)

| Modül | Gereksinim | İçerik |
|---|---|---|
| `warp_core/eos_tillotson` | P2-FR-03 | Tillotson EOS (bazalt; Benz & Asphaug 1999) |
| `warp_core/solid_stress` | P2-FR-01 | Jaumann objektif gerilme hızı, Randles-Libersky gradyan düzeltmesi |
| `warp_core/strength_lundborg` | P2-FR-02 | Basınca bağlı dayanım Y(P) + von Mises return mapping |
| `warp_core/porosity_palpha` | P2-FR-04 | P-α crush curve (geri genleşme yok) |
| `warp_core/gravity_tree` | P2-FR-05 | Barnes-Hut halat-ağacı (deterministik DFS) + doğrudan N² referansı |
| `warp_core/solver_solid` | P2 §4.1 | Katı SPH çözücüsü |
| `cpu_reference/materials`, `solid_ref`, `gravity_ref` | — | NumPy referansları |
| `validation/solids`, `porous`, `gravity`, `ablation` | P2-VR-01..06, P2-FR-06 | Rijit dönme, elastik dalga, Taylor bar, crush, yerçekimi, ablasyon matrisi |

## Kurulum ve test

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev,gpu]"    # gpu = warp-lang (CPU cihazıyla da çalışır)
```

```bash
pytest tests -m "not gpu" --cov=dartrift    # GPU'suz ortam
```

```bash
pytest tests --cov=dartrift                 # CUDA'lı ortam (tam paket)
```

Kapı koşucuları (her biri CUDA ister):

```bash
python scripts/run_g0_gate.py
```

```bash
python scripts/run_g1_gate.py
```

```bash
python scripts/run_g2_gate.py
```

```bash
python scripts/run_red_team.py
```

Kapı koşucuları CUDA bulunmayan bir makinede **"geçti" demez**: ilgili ölçüt
kanıtlanamadığı için `KANITLANAMADI` yazıp exit 2 döner. `--allow-no-gpu`
yalnızca ön kontrol içindir ve o mod da geçti iddiası üretmez.

> **Kütüphane tabanı:** Hedef ortam NumPy **1.26.4** kullanır. NumPy 2.0+ ile
> gelen API'ler (`np.trapezoid`, `np.concat`, …) kullanılamaz; gerekiyorsa
> sürümden bağımsız köprü yazılır. Gerekçe ve olay kaydı:
> [ADR-0005](docs/adr/ADR-0005-python-surumu-truba.md).

## TRUBA (ARF-ACC) üzerinde kanıt üretimi

TRUBA kuralları gereği `/arf`'a pip/conda ile **kurulum yapılmaz**; merkezî
modül kullanılır ve ek paketler wheel arşivleri açılarak `PYTHONPATH` üzerinden
kullanılır (639 dosya; inode kotası 500.000). Hazırlık **giriş düğümünde bir
kez** yapılır:

```bash
cd /arf/scratch/<grup>/driftclaude && module purge && module load apps/truba-ai/gpu-2024.0 && python3 -m pip download warp-lang pytest-cov coverage --no-deps -d wheels && mkdir -p pylib && for w in wheels/*.whl; do python3 -m zipfile -e "$w" pylib; done
```

Ardından kapı koşuları GPU kuyruğuna gönderilir:

```bash
sbatch slurm/faz0_g0_gate.sh
```

```bash
sbatch slurm/faz12_gates.sh
```

Kanıtlar `gate_runs/<koşu>/` içinde üretilir; kabul edilenler koşu künyesiyle
(iş kimliği, düğüm, commit, ortam sürümleri) `docs/evidence/` altına
kopyalanıp sürümlenir.

> **Donanım arızaları kapı sonucu değildir.** Betikler bilinen arızalı
> düğümleri `#SBATCH --exclude` ile dışlar ve arıza saptarsa 75 (`EX_TEMPFAIL`)
> ile çıkar — böylece bir düğüm sorunu "kapı kaldı" gibi görünmez. Saptanan
> arızalar: `palamut5` (`/arf`'a veri yazamıyor), `palamut6` (büyük dosya
> okuyamıyor), `kolyoz13` (`nvidia-smi` GPU'yu görüyor ama CUDA sürücüsü
> açılmıyor). Ayırt edici testler mühendislik defterindedir.

## İzlenebilirlik ve mühendislik disiplini

- **[docs/IZLENEBILIRLIK.md](docs/IZLENEBILIRLIK.md)** — 38 gereksinim
  kimliğinin (13 P0 + 13 P1 + 12 P2) her biri kodu, testi ve kanıtıyla
  eşlenmiştir. Aynı belge, şartnamece **yasak** olduğu için bilerek
  yapılmayanları da listeler ki eksik ile kapsam-dışı karışmasın.
- **[docs/adr/](docs/adr/)** — 15 mimari karar kaydı. Her büyük teknik karar
  gerekçesi, değerlendirilen alternatifleri ve doğrulama testiyle kayıtlıdır;
  sessiz değişiklik yasaktır.
- **[docs/defter/](docs/defter/)** — 7 mühendislik defteri kaydı. Başarısız
  denemeler ve negatif sonuçlar **silinmez**, işlenir; yanlış çıkan bir iddia
  da silinmez, düzeltme notuyla kayda geçer.
- **[docs/evidence/](docs/evidence/)** — kapı raporları, koşu künyeleriyle.

### Dürüstlük sınırı

- Test geçilmediyse iddia edilmez. Benchmark geçmeyen modülün iddiası
  yapılmaz; iddia daraltılır ama bilim bükülmez.
- Görsel olarak makul bir sonuç **kanıt değildir**; kanıt test ve sayıdır.
- Kanıt hedef ortamda üretilir. Yerelde yeşil olan bir paketin kümede de
  yeşil olduğu varsayılmaz — nitekim kapı mekanizması üç kez, yerelde
  görünmeyen bir kusuru yakaladı (NumPy sürüm farkı, düğüm sürücü arızası,
  metrik serileştirme hatası).

## Lisans

MIT — bkz. [LICENSE](LICENSE). Atıf için [CITATION.cff](CITATION.cff).
