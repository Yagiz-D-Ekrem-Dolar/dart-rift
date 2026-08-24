# DART-RIFT

> Dimorphos için GPU hızlandırmalı SPH şok-fiziği motoru ve Bayesçi iç-yapı
> çıkarımı projesi.
> Şartname: `DR-RIFT-P0/P1/P2 v1.0` · Ana Plan: `DART-RIFT Ana Proje Planı v1.0`

NASA'nın DART aracının Dimorphos'a çarpmasından elde edilen verilerden,
asteroidin **içinin neye benzediğini olasılıksal olarak** geri hesaplamayı ve
bu tahmini ESA'nın Hera aracı oraya varıp ölçmeden **önce** kilitlemeyi
hedefliyoruz.

Bu depo, o çıkarımın dayanacağı **motoru** içerir: deterministik altyapı
(FAZ 0), SPH şok-fiziği çekirdeği (FAZ 1), gerçek malzeme fiziği — dayanım,
gözeneklilik, öz-yerçekimi (FAZ 2), çarpma sahnesi (FAZ 3) ve iki aşamalı
çözünürlük + Bayesçi çıkarım hattı (FAZ 4).

> ### Yeni bir oturuma mı başladın?
>
> **[DEVAM.md](DEVAM.md)** en üstteki `2026-08-21` bölümü, hiçbir önceki
> bağlam olmadan işe devam edebilmek için yazıldı: nerede çalışıldığı
> (yerel + **yeni** TRUBA alanı), `β` sonucunun kanıt zinciri, **tekrar
> koşulmaması gereken** elemeler, bulunan kusurlar ve bekleyen kararlar.

## Kapı durumu

Her faz, şartnamedeki kabul ölçütlerini **kanıtla** geçmeden bir sonrakine
geçilmez. Kanıtlar TRUBA/ARF-ACC üzerinde, temiz git ağacıyla üretilir.

| Kapı | Kapsam | Sonuç | Karar |
|---|---|---|---|
| **G0** | Zemin sağlam (altyapı) | **GEÇTİ** | FAZ 1 başlayabilir |
| **G1** | Şok motoru çalışıyor | **GEÇTİ** | FAZ 2 başlayabilir |
| **G2** | Gerçek malzeme fiziği | **GEÇTİ** | FAZ 3 başlayabilir |
| **G3** | Sahne kurulumu | **GEÇTİ** 7/7 | FAZ 5 değil — önce G4 |
| **G4** | Çözünürlük + çıkarım | **GEÇTİ** 10/10 | **FAZ 4 KAPANDI** ([kapanış](docs/FAZ4-KAPANIS.md)) |

### G4 geçti — ve neyin karşılığında

| # | ölçüt | ölçülen |
|---|---|---|
| A1 | mermi çapı / aralık | `2,03906` |
| A2 | `r_ince / R_mermi` | `66,5573` |
| A3 | ek yerinde kütle sapması | `3,48e-4` |
| B1 | ardışık çözünürlükte `β` farkı | `8,43e-4` |
| B2 | `β` durulmuş | `1` |
| B3 | A′ ince kola yakın | `1` |
| B4 | enerji sapması eğimi | `−2,39e-3` |
| C1 | parametre kapsaması | `1` |
| **C2** | en dar bant / önsel | **`0,221`** |
| C3 | gürültüyle genişleme | `1` |

`C2`'yi geçiren şey bir eşik gevşetmesi **değil**: çıkarım uzayı üç
parametreden **bire** indirildi ([ADR-0046](docs/adr/ADR-0046-cikarim-uzayi-olculebilir-olana-indirilir.md)).
Bedeli açıkça kayıtlı:

> **İddia daraldı:** *"iç yapıyı çıkardık"* → **"matris gözenekliliğini
> çıkardık"**. `f_boulder` artık serbest değil — ve Hera onu görüntüleyecek.
> Kapının geçmesi bu kaybı telafi etmiyor.

> **G4, motorun *yakınsadığını* ve *çıkarımın işlediğini* kanıtlar; motorun
> *doğru* `β` ürettiğini kanıtlamaz.** İkisi ayrı sorular ve ikincisi açık
> ([A17](docs/FAZ4-SIKINTI-RAPORU.md)): motor `β ≈ 1,41` üretiyor, ölçülen
> periyot değişimi `3,2225` istiyor. Aday elemeleri ölçümle yapıldı —
> koşu süresi (`0,2 → 600 s`, `3000×`), mukavemet (`Y0` `1 → 2,15e6 Pa`,
> altı mertebe), yerçekimi, gözeneklilik, çözünürlük. Hiçbiri açığı
> kapatmıyor; hepsi aynı yere çıkıyor: `β`'nın kontrol yüzeyini geçen
> maddesi hedef ejektası değil **merminin geri sekmesi**
> ([ADR-0028](docs/adr/ADR-0028-uzun-kosu-kararliligi.md)).

[G3 kanıtı](docs/evidence/G3_GATE_0b88ae9.md) — commit `0b88ae9`, TRUBA / H100,
iş 1446129, **620 test geçti / 0 kaldı** (`xfail` yok), kapsam **%97,0**,
kırmızı takım (P0 §12 + P3 §10) **14/14 temiz**, çıkış kodu **0**.

> **Makineler arası determinizm — ölçüldü.** FAZ 3 sahne karması iki bağımsız
> ortamda birebir aynı: `6d6f1d10eaff64e2…` (Linux/numpy 1.26.4/H100 ve
> Windows/numpy 2.5.1/RTX 3050). Bu eşitlik önce **tutmuyordu**; iki gerçek
> kusur bulundu — ışın-yüzey kesişiminin mesh köşesinde dejenere olması
> (yüzey normali makineye göre **2,5°** oynuyordu, fiziksel olarak önemli) ve
> `centroid`'de toplama sırası. İkisi de düzeltildi ve bir altın-karma
> bekçisiyle kilitlendi ([ADR-0025](docs/adr/ADR-0025-sahne-makineler-arasi-determinizm.md)).

> **Gerçek Dimorphos geometrisi kullanılıyor.** C7 kriteri PDS veri
> ürünlerinin kimlik ve sağlama toplamlarını ister; paket
> `urn:nasa:pds:dart_shapemodel::1.0` çekildi (Daly ve dig., NASA PDS 2023) ve
> **10/10 ürün arşivin resmi MD5'iyle doğrulandı**. Okunan Dimorphos eşdeğer
> yarıçapı **75,0 m** — yayımlanan değerle birebir. Veri depoda değildir;
> depoya giren köken kaydıdır ([`data_manifest/`](data_manifest/README.md)).
>
> **Birim uyarısı:** PDS şekil modelleri kilometre cinsindendir. Metre saymak
> cismi 1000 kat küçültür ve hiçbir yerde hata vermeden bütün fiziği
> anlamsızlaştırır; bu yüzden dönüşüm `units="km"` ile **açıkça** verilir.

Koşu bazlı raporlar: [G0](docs/evidence/G0_report_truba_1425656.md) ·
[G1](docs/evidence/G1_report_truba_1426162.md) ·
[G2](docs/evidence/G2_report_truba_1426596.md). CPU↔GPU bit-eşit roundtrip
üç GPU mimarisinde doğrulandı: sm_80 (A100), sm_90 (H100), sm_86 (RTX 3050).
G1 ayrıca iki farklı düğümde koşulup sekiz ölçütün kanıt sayıları birebir
aynı çıktı.

> **Kapsam sınırı:** Kapılar motorun **doğrulama senaryolarını** geçtiği
> anlamına gelir. Dimorphos hakkında **henüz hiçbir bilimsel sonuç iddia
> edilmemektedir**. FAZ 3 çarpma **sahnesini** kurar; çarpma **koşuları**
> FAZ 4'tedir.

> **Gözeneklilik kusuru — ÇÖZÜLDÜ:** P-α distansiyonu açık güncelleniyordu ve
> sert Tillotson EOS'unda aşırı atıyordu (α tek adımda 1,5→1,0). Örtük
> (bisection) çözümle çarpma senaryosunda enerji hatası **%15,81 → %0,3955**
> ve artık çözünürlükle büyümüyor —
> [ADR-0023](docs/adr/ADR-0023-porozite-ortuk-cozum.md).

### Uzun koşu ve determinizm — ölçüldü (TRUBA H100, iş 1429628)

| Ölçüm | Sonuç |
|---|---|
| 30 000 adım enerji drifti | **1,00×** (birikme yok) |
| 30 000 adım kütle korunumu | **0,00e+00** |
| Determinizm, tam fizik, 19 416 parçacık | **bit-eşit** |
| Determinizm, tam fizik, 65 840 parçacık | **bit-eşit** |

## Motor hedefe yetiyor mu? (ölçüldü)

Doğrulama senaryolarını geçmek, hedef problemi çözebilmek anlamına gelmez.
Ölçek ve maliyet ayrıca ölçüldü — [docs/FIZIBILITE.md](docs/FIZIBILITE.md):

- **11,2 milyon parçacık** TRUBA H200'de koştu, 150 GB'ın yalnızca 6'sını
  kullanarak. Maliyet 175 kat aralıkta **N ile doğrusal** (123–150 µs/1000
  parçacık) — gizli bir `O(N²)` yok, bellek darboğaz değil.
- DART ölçeğinde (2 M parçacık) bir koşu ~**2,4 saat** (1 s simüle süre) —
  ama bu **öz-yerçekimi kapalıyken**. Açıkken mevcut uygulama ~17 kat yavaş
  (832 K parçacıkta adım 4 837 ms ↔ yerçekimsiz 1 M'de 287 ms), çünkü baskın
  kalem CPU'da Python'da kurulan Barnes-Hut ağacıdır. FAZ 5'in öngördüğü
  "yüzlerce koşu" yerçekimsiz ~30 GPU-günü ile **fizibil**; yerçekimli
  koşular için ağacın GPU'ya taşınması ya da K adımda bir yenilenmesi gerekir.
- Fizik seti (Tillotson + P-α + basınca bağlı dayanım + öz-yerçekimi +
  **Grady-Kipp hasar**) zayıf ve gözenekli hedefler için literatürdeki
  standart settir. Hasar modeli P2 §1.3'te STRETCH olarak bırakılmış ve `D = 0`
  sabitlenmişti; **kapatıldı** — Weibull kusur dağılımı, çekmeyi zayıflatan
  (basmayı değil) uygulama, 32 test, çekme dayanımı ≈32 MPa (bazalt bandı) —
  [ADR-0027](docs/adr/ADR-0027-grady-kipp-hasar-modeli.md).
- **Mermi çözünürlüğü FAZ 4'ün tasarımını belirliyor.** DART mermisini çapı
  boyunca 6 parçacıkla çözmek **1,72e9 parçacık** ister — ölçülmüş fizibil
  sınırın (1,12e7) **153 katı**. Tekdüze ağ yetmez; çarpma bölgesinde yerel
  yüksek çözünürlük gerekir —
  [ADR-0026](docs/adr/ADR-0026-mermi-cozunurlugu-tekduze-agda-imkansiz.md).

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
| Elastik dalga hızı | 4593 m/s teorik | 4463 m/s → **%2,83** | %3 |
| Taylor bar (bakır) | Deney bandı 0,60–0,80 | **L/L0 = 0,731**, enerji %0,083 | %1,5 |
| İki-cisim (20 yörünge) | Kepler | E hatası 2,4e-07, yarıçap drifti 1,3e-08 | — |
| Soğuk çöküş | — | enerji %0,36; momentum 1,2e-17 | %1; 1e-6 |

### Marj analizi — kapılar yeşil, ama bazıları kılpayı

Bir ölçütün geçmesi, sağlam geçtiği anlamına gelmez. Altı ölçüt eşiğine
%20'den yakın:

| Ölçüt | Ölçülen | Eşik | Marj |
|---|---|---|---|
| Elastik dalga hızı | %2,83 | %3 | **1,06×** |
| Sedov şok yarıçapı | %4,46 | %5 | 1,12× |
| Enerji korunumu | %0,432 | %0,5 | 1,16× |
| Yerçekimi: BH↔doğrudan medyan | %0,43 | %0,5 | 1,16× |
| von Mises drifti | %1,66 | %2 | 1,20× |
| Yerçekimi: kabuk hatası | %1,90 | %5 | 2,6× |

Kabuk hatası bu listede daha önce %4,65 (1,08×) ile yer alıyordu. İncelenince
metriğin alan doğruluğunu değil **örnekleme gürültüsünü** ölçtüğü ve n ile
monoton olmadığı görüldü (n=2000'de %8,97 — eşiğin neredeyse iki katı). Eşik
değiştirilmedi; düzeltilen şey ölçünün neyi ölçtüğü —
[ADR-0017](docs/adr/ADR-0017-kabuk-metrigi-minimum-ornekleme.md).

Bunların hiçbiri gizlenmiyor; ölçülen değerler yukarıdaki tabloda ve kapı
raporlarındadır. İkisinin davranışı ayrıca incelendi:

- **Elastik dalga** hatası çözünürlükle sıfıra yakınsıyor (%9,13 → %5,36 →
  %4,19 → %2,83, yaklaşık birinci mertebe). Sistematik bir taban yok; daha
  ince kafes marjı büyütür.
- **Sedov** hatası ise ~%3,9'luk bir **tabana** iniyor (n=112'ye kadar
  ölçüldü). Bu ayrıklaştırma değil, sonlu enjeksiyon yarıçapının model-form
  hatası — [ADR-0011](docs/adr/ADR-0011-sedov-yakinsama-kurulumu.md).

### Enerji hatasının mertebesi (ADR-0020)

Sedov'da enerji hatası çözünürlükle büyüyor ve n≥96'da %0,5 bütçesini aşıyor
(%0,510 → %0,534). Bu bir **sızıntı değil**: sabit çözünürlükte yalnızca CFL
değiştirilerek ölçüldü —

| CFL | adım | enerji hatası | önceki/bu |
|---|---|---|---|
| 0,2500 | 162 | %0,29502 | — |
| 0,1250 | 324 | %0,14303 | **2,06** |
| 0,0625 | 647 | %0,06904 | **2,07** |

dt yarılandığında hata tam yarıya iniyor, yani hata `O(dt¹)` **kesme
hatasıdır ve kontrol edilebilir**. Sızıntı olsaydı oran 1'e yakın olurdu.
Aynı taramada şok yarıçapı hatası %1,14 → %1,12 ile sabit; bu da onun
zaman ayrıklaştırmasından değil sonlu enjeksiyon yarıçapından geldiğini
bağımsız olarak doğruluyor.

G1 kapısı bu oranı **her koşuda ölçüp raporlar**
(`energy_error_dt_halving_ratio`). Böylece ölçüt "hata < %0,5"ten daha
keskindir: gerçek bir sızıntı girerse oran 2'den 1'e düşer ve eşik hâlâ
geçiliyor olsa bile kanıt metninde görünür.

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
| `warp_core/damage_gradykipp`, `cpu_reference/damage_ref` | P2 §1.3 (STRETCH → **kapandı**) | Grady-Kipp hasar + Weibull kusurları; yalnızca çekmeyi zayıflatır (ADR-0027) |
| `warp_core/gravity_tree` | P2-FR-05 | Barnes-Hut halat-ağacı (deterministik DFS) + doğrudan N² referansı |
| `warp_core/solver_solid` | P2 §4.1 | Katı SPH çözücüsü |
| `cpu_reference/materials`, `solid_ref`, `gravity_ref` | — | NumPy referansları |
| `validation/solids`, `porous`, `gravity`, `ablation` | P2-VR-01..06, P2-FR-06 | Rijit dönme, elastik dalga, Taylor bar, crush, yerçekimi, ablasyon matrisi |

### FAZ 3 — Sahne kurulumu (DR-RIFT-P3)

| Modül | Gereksinim | İçerik |
|---|---|---|
| `setup/shape_mesh` | P3-FR-01 | Mesh yükleme/temizleme/dışa yönlendirme, ışın-atma iç testi (sol-üst kenar kuralı) |
| `setup/rubble_generator` | P3-FR-02/03/04 | FCC doldurma, power-law iri-bloklar (hacim oranı geri ölçülür), parçacık başına malzeme |
| `setup/settling` | P3-FR-05, P3-VR-01 | Öz-yerçekimi altında **denge sınaması** (ADR-0024) |
| `setup/impactor` | P3-FR-06/07, P3-VR-02 | DART mermisi — sonlu boyutlu, nokta parçacık yasak; yüzey normaline göre çarpma geometrisi |
| `setup/scene` | P3 §4 | Sahne birleştirici: config → yeniden üretilebilir tam durum (`Scene.digest`) |
| `observables/momentum_transfer` | P3-FR-08, P3-VR-03 | β + kontrol yüzeyi duyarlılığı, momentum defteri kapanması |
| `observables/ejecta_catalog` | P3-FR-08 | Kütle-hız dağılımı (kutulama yok), fırlatma açıları, üslü yasa üssü + R² |
| `observables/crater_shape` | P3-FR-08 | **Yerel** krateri **küresel** biçim değişiminden ayırır (eşit katı açılı kutular) |
| `observables/period_interface` | P3-FR-08 | β ↔ yörünge periyodu değişimi (sınırları açık yazılı) |
| `validation/scene_checks` | G3 | Şekil hattı, yığın kalitesi, mermi yakınsaması, gözlenebilir öz-sınavı, sahne determinizmi |

> **Adlandırma:** FAZ 3 sahnesi bir "DART senaryosu" **değil**, "DART benzeri
> senaryo"dur. Hedef şekli analitik bir ikosferdir; gerçek PDS ürünleri depoda
> yok (G3 kriter C7 **KANITLANAMADI**, bkz. `data_manifest/README.md`). Şekil
> modeli geldiğinde `shape: obj` yeter — değişecek olan sayılardır, kod değil.

### FAZ 4 — Çözünürlük ve çıkarım (DR-RIFT-P4)

| Modül | İçerik |
|---|---|
| `setup/refine` | Yerel incelme; **parçacık başına `h`** (A′ yaklaşımı, [ADR-0041](docs/adr/ADR-0041-yerel-incelme-yaklasimi.md)) |
| `setup/coarsen` | Lagrange'cı kabalaştırma: kütle/momentum/enerji `~1e-15` korunumlu; `mermi_kesri` **kesir olarak** taşınır |
| `setup/two_stage` | İki aşamalı koşu ([ADR-0043](docs/adr/ADR-0043-iki-asamali-cozunurluk.md)): `λ₁ = 19` çekirdek → `λ₂ = 2`; üç seviyeli (iki seviyelide momentumun `%69`'u atılıyordu) |
| `inference/design` | Parametre uzayı, LHS/faktöriyel tasarım |
| `inference/forward` | İleri model: sahne → `(β, krater_derinlik, ejekta_kutle_kesri)` |
| `inference/surrogate` | İkinci derece vekil + **kapalı formda LOO** (`q2`); sabit/yetersiz gözlenebilir **durdurur** |
| `inference/posterior` | Izgara posterior'u, HDI |
| `inference/recovery` | G4-C yargısı (C1 kapsama / C2 daralma / C3 gürültü tepkisi) |
| `validation/h_policy` | Sabit `h` yeterli mi — küp **ve** DART geometrisinde ([ADR-0042](docs/adr/ADR-0042-h-sabittir-omega-birimdir.md)) |
| `validation/g4_gate` | Kapı yargısı + koşullu kabullerin **raporda görünmesi** |

> **`Ω ≡ 1` bir ölçüm değil cebir:** `h` reçeteli olduğu için `∂h/∂ρ = 0` ve
> zincir kuralı çarpanı terimi kapatır. Ölçülen şey sabit `h`'nin
> **yeterliliğiydi**; DART geometrisinde `N_komşu` salınımı `1,064×` çıktı —
> kanıtın kurulduğu küp aralığından (`2,06×`) **daha dar**.

## Bilinen açık sorunlar

Bu depo kendi sıkıntılarını [`docs/FAZ*-SIKINTI-RAPORU.md`](docs/FAZ4-SIKINTI-RAPORU.md)
altında izler; **motoru** engelleyen açıklar ayrıca
[issue](https://github.com/Yagiz-D-Ekrem-Dolar/dart-rift/issues?q=is%3Aissue+is%3Aopen+label%3Amotor)
olarak da duruyor ki dışarıdan görülebilsin.

| | konu | durum |
|---|---|---|
| [#6](https://github.com/Yagiz-D-Ekrem-Dolar/dart-rift/issues/6) | `β` hedef ejektasını değil merminin sekmesini ölçüyor (A17/A12) | açık |
| [#7](https://github.com/Yagiz-D-Ekrem-Dolar/dart-rift/issues/7) | Krater çapı gerçek ensemble'da gözlenemiyor (A11) | açık |

> Kapanmış sıkıntılar **silinmiyor**, raporda gerekçesiyle duruyor —
> deponun değeri nerede yanıldığının izlenebilir olmasında (`RULES.txt`).

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

- **[docs/IZLENEBILIRLIK.md](docs/IZLENEBILIRLIK.md)** — 49 gereksinim
  kimliğinin (13 P0 + 13 P1 + 12 P2 + 11 P3) her biri kodu, testi ve kanıtıyla
  eşlenmiştir. Aynı belge, şartnamece **yasak** olduğu için bilerek
  yapılmayanları da listeler ki eksik ile kapsam-dışı karışmasın.
- **[docs/EKSIKLER.md](docs/EKSIKLER.md)** — bilinen eksiklerin tek kaydı:
  ne kapandı, ne açık, ne bilinçli kapsam dışı. Amaç, bir eksiğin
  "unutuldu" mu "bilinçli bırakıldı" mı olduğunun hiç belirsiz kalmaması.
- **[docs/adr/](docs/adr/)** — 28 mimari karar kaydı. Her büyük teknik karar
  gerekçesi, değerlendirilen alternatifleri ve doğrulama testiyle kayıtlıdır;
  sessiz değişiklik yasaktır.
- **[docs/defter/](docs/defter/)** — 15 mühendislik defteri kaydı. Başarısız
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

## Devam etmek isteyenler için

Projeyi kaldığı yerden sürdürmek (veya ilk kez ele almak) için:
**[DEVAM.md](DEVAM.md)** — ortam ayrıntıları, mimarinin değişmez kuralları,
öğrenilmiş tuzaklar, ölçülmüş performans sınırları ve FAZ 3'e başlama adımları.

Üç günlük çalışmanın sentezi:
**[KAYIT-014](docs/defter/KAYIT-014_2026-07-29_faz012_sentez.md)** — ne
yapıldı, hangi sorunlar çıktı, ne öğrenildi.

## Lisans

MIT — bkz. [LICENSE](LICENSE). Atıf için [CITATION.cff](CITATION.cff).
