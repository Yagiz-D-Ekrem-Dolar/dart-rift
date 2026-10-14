# DART-RIFT

**DART'ın bıraktığı tek sayıdan Dimorphos'un içini geri okumak — ve bu
tahmini Hera oraya varmadan mühürlemek.**

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23284193.svg)](https://doi.org/10.5281/zenodo.23284193)
[![Lisans: MIT](https://img.shields.io/badge/lisans-MIT-blue.svg)](LICENSE)

> **In English.** DART-RIFT infers the interior of asteroid Dimorphos —
> boulder porosity, matrix strength, boulder volume fraction — from
> DART's measured momentum enhancement β, using GPU SPH (NVIDIA Warp), a
> Gaussian-process surrogate and a **pre-registered** Bayesian posterior.
> The central question is not *"what is the interior?"* but *"how many
> directions of it can one scalar actually constrain?"* Preprint:
> [10.5281/zenodo.23284193](https://doi.org/10.5281/zenodo.23284193).
> The repository language is Turkish.

---

## Soru

2022'de NASA'nın DART aracı Dimorphos'a çarptı ve geriye **tek bir sayı**
bıraktı: momentum artırma katsayısı `β`. Bu sayı asteroidin içine bağlı —
gevşek bir moloz yığını ile taşlı bir gövde çarpmaya aynı tepkiyi
vermez. O yüzden akla gelen ilk iş `β`'dan içeriye gitmektir.

Gelgelelim üç bilinmeyen var: **blok gözenekliliği `α_b`**, **matris
dayanımı `Y₀`** ve **blok hacim kesri `f`**. Bir skaleri üç bilinmeyene
çevirmek tanım gereği mümkün değil. Bu projenin asıl sorusu bu yüzden
şudur:

> **Tek skaler gözlem, üç boyutlu iç yapı uzayında kaç yönü
> kısıtlıyor?**

Cevabı tahmin etmek yerine **ölçüyoruz**: yüzlerce GPU çarpma
benzetimiyle ileri modeli kuruyor, üzerine bir vekil oturtuyor,
ardından karar kurallarını **veriyi görmeden** kilitleyip posterior'un
Fisher öz değerlerini sayıyoruz.

## Şu ana kadarki cevap

Üretim havuzu 96 kilitli tasarım noktasından oluşuyor; 2026-10-14
itibarıyla **90'ı tamamlandı** (TRUBA/H100, **kayıp koşu yok** — Kapı 1
ölçütü %20, ölçülen %0,00). Aşağıdaki sıra korelasyonları havuz 88
noktadayken ölçüldü:

| gözlenebilir | `α_b` | `log Y₀` | `f` |
|---|---|---|---|
| **`β`** (momentum artırma) | −0,061 | **−0,983** | +0,055 |
| **`ω`** (kazanılan spin) | −0,316 | −0,111 | **+0,459** |

İki satır bu projenin özeti:

1. **`β` pratikte tek bir koordinat taşıyor.** `Y₀` ile neredeyse tam
   tekdüze, diğer iki eksenle korelasyonu sıfıra yakın. Yani DART'ın
   tek sayısı üç boyutlu uzayda **bir yön** görüyor — dejenerasyon
   ölçülmüş bir olgu, varsayım değil.
2. **Çarpmanın kazandırdığı spin, `β`'nın kör olduğu yerleri görüyor.**
   İki gözlenebilir neredeyse dik (`r(β,ω) = +0,131`) ve `ω` en çok
   `f`'ye duyarlı. Dejenerasyonu kırmanın yolu daha iyi bir `β` ölçümü
   değil, **başka bir eksene bakan ikinci bir gözlenebilir**.

İkinci bulgu projenin özgün katkısıdır: dejenerasyonun yalnız *var
olduğunu* değil, **hangi yönde** olduğunu ve hangi gözlenebilirin onu
kesebileceğini veriyor. `ω` bu projede ölçülen bir gözlenebilirdir
([PROTOKOL-SI](docs/truba/PROTOKOL-SI-SON-ISLEME.md) §5: bağlı
malzemenin açısal momentumu / eylemsizlik tensörü), ek bir koşu
gerektirmez — aynı durum dosyalarından çıkar.

> Yukarıdaki sayılar **kısmi havuzdandır** ve havuz dolduğunda
> yenilenecektir. Asıl yargı — kaç yön öğrenildiğinin **mühürlü**
> ölçümü — Fisher öz değerleriyle verilir ve tam havuzu, kalibre
> edilmiş vekili ve ölçülmüş artık korelasyonunu gerektirir
> ([PROTOKOL-UP](docs/truba/PROTOKOL-UP-POSTERIOR.md),
> [ADR-0058](docs/adr/ADR-0058-uretim-posteriorunun-tarifi.md)). O ölçüm
> havuzdan **önce** yazıldı ve sonucuna göre değiştirilmeyecek.

## Neyi iddia etmiyoruz

Bu bölüm README'nin en önemli kısmıdır.

- **`(α_b, Y₀, f)` için nokta tahmini ya da güven aralığı vermiyoruz.**
  Dejenerasyon ölçülmüş; bir nokta tahmini onu gizlemek olurdu.
- **Hera için sayısal bir öngörü henüz mühürlü değil.** Protokol yazılı
  ([PROTOKOL-HT](docs/truba/PROTOKOL-HT-HERA-TAHMIN.md)), sayı yok.
- **Çözünürlük yakınsaması sağlanmadı.** Protokol M yargısı
  **YAKINSAMIYOR**: farklar inceldikçe büyüyor. Bu yüzden mutlak
  değerler değil, çözünürlüğe dayanıklı olduğu ayrıca ölçülmüş
  **kontrastlar** kullanılıyor.
- **Hedef gerçek PDS şekil modeli değil.** PDS paketi
  (`urn:nasa:pds:dart_shapemodel::1.0`) çekildi ve 10/10 ürün resmî
  MD5'iyle doğrulandı ([`data_manifest/`](data_manifest/README.md)), ama
  üretim sahnesi Dimorphos'un ölçülerine oturtulmuş üç eksenli bir
  **elipsoittir** (88,5 × 87,0 × 58,0 m, kütle 4,2980e9 kg).
- **Kapıların geçmesi fiziğin doğrulandığını göstermez.** Mühendislik
  doğrulaması (çözücü doğru denklemleri doğru çözüyor mu) ile bilimsel
  doğrulama (bu model DART çarpışmasını doğru modelliyor mu) ayrı
  tutulur; ikincisi açık.

Tam döküm: [`docs/BULGULAR.md`](docs/BULGULAR.md) — ne kanıtlandı, ne
kanıtlanmadı, hangi iddia hangi ölçümle daraltıldı.

## Boru hattı

```
sahne (elipsoit + bloklar)     kilitli tasarım: 96 nokta, LHS, tohum 20260906
        |                      θ = (α_b, Y₀, f)          [ADR-0053]
        v
SPH çarpma benzetimi           Warp/CUDA FP64, Wendland C2, Tillotson EOS,
  600 s, merdivenli incelme    P-α gözeneklilik, Grady-Kipp hasar, öz çekim
        |                      5 iç içe bölge: 48 m yarıçapta 5,6 m aralık
        |                      -> 3 m yarıçapta 0,35 m  (kaba, N ~ 17 000)
        v
gözlenebilirler                β (fırlatı geleneğinde)   [ADR-0060]
                               ω (kazanılan spin)        [PROTOKOL-SI]
        |                      krater, ejekta kütle kesri
        v
vekil                          GP, ARD kare-eksponansiyel;
                               θ-gruplu 4-kat CV, Bachoc varyans kalibrasyonu
        |
        v
posterior                      ızgara, ölçülmüş artık korelasyonu (λ = 0,3)
        |
        v
yargı                          Fisher öz değerleri -> öğrenilen yön sayısı
                               eşik ve kurallar havuzdan ÖNCE kilitli
```

Her GPU çekirdeğinin **Warp'tan bağımsız bir NumPy FP64 referansı**
vardır ve ikisi çapraz kontrol edilir (tipik sapma `< 1e-8`). Bu
kontrol, tek başına yeşil görünen bir çekirdeğin yanlış ayrıklaştırma
yapmasını engeller — nitekim
[ADR-0015](docs/adr/ADR-0015-sureklilik-yogunlugu.md) bu yolla yakalanmış
gerçek bir çekirdek hatasını kaydeder.

## Motor doğrulaması

Analitik ve deneysel referanslara karşı **ölçülen** hatalar. Hepsi kapı
kanıtlarından, koşu künyeleriyle:

| senaryo | referans | ölçülen | eşik |
|---|---|---|---|
| Sod şok tüpü | kesin Riemann | şok hızı %0,08; post-şok en kötü %0,80 | %3–5 |
| Sedov-Taylor | benzerlik çözümü | şok yarıçapı %4,46 | %5 |
| kütle korunumu | — | **0,00e+00** | ~makine hassasiyeti |
| momentum korunumu | — | **8,39e-16** | 1e-6 |
| enerji korunumu | — | %0,432 | %0,5 |
| elastik dalga hızı | 4593 m/s teorik | 4458 m/s → %2,96 | %3 |
| Taylor bar (bakır) | deney bandı 0,60–0,80 | `L/L₀ = 0,731`; enerji %0,083 | %1,5 |

Kanıtlar: [G0](docs/evidence/G0_report_truba_1425656.md) ·
[G1](docs/evidence/G1_report_truba_1426162.md) ·
[G2](docs/evidence/G2_report_truba_1426596.md) ·
[G3](docs/evidence/G3_GATE_0b88ae9.md) ·
[G4 kapanışı](docs/FAZ4-KAPANIS.md)

> **Marj dürüstlüğü.** Bir ölçütün geçmesi sağlam geçtiği anlamına
> gelmez: elastik dalga `%2,96`'da ve eşiği `%3`. Kılpayı geçen ölçütler
> saklanmıyor; davranışları ayrıca incelenmiş (elastik dalga hatası
> çözünürlükle sıfıra yakınsıyor, Sedov hatası ise `~%3,9`'luk bir
> **tabana** iniyor ve bu ayrıklaştırma değil model-form hatasıdır —
> [ADR-0011](docs/adr/ADR-0011-sedov-yakinsama-kurulumu.md)).

## Depo düzeni

```
src/dartrift/
  warp_core/        GPU çekirdekleri: çekirdek fonksiyonu, komşuluk, yoğunluk,
                    kuvvet, integratör, Tillotson, dayanım, P-α, Grady-Kipp,
                    Barnes-Hut çekim
  cpu_reference/    her çekirdeğin bağımsız NumPy FP64 referansı
  setup/            şekil, moloz üretici, oturma, mermi, sahne, incelme
  observables/      β, ejekta kataloğu, krater biçimi, periyot arayüzü,
                    β gelenek dönüşümü
  inference/        tasarım, ileri model, vekil, posterior, artık korelasyonu,
                    tarih eşleme (model hatası paydası)
  validation/       kapı ölçütlerinin koşucuları
docs/
  adr/              60 mimari karar kaydı
  defter/           78 mühendislik defteri kaydı
  truba/            39 kilitli protokol (koşudan ÖNCE yazılır)
  evidence/         kapı raporları, koşu künyeleriyle
  rapor2204/        TÜBİTAK 2204-A proje raporu (LaTeX)
  preprint/         bilimsel ön baskı (İngilizce, DOI'li)
truba/              Slurm iş betikleri ve sıra planları
data_manifest/      dış veri ürünlerinin kimlik + sağlama kaydı
```

Gereksinim → kod → sınav → kanıt eşlemesinin tamamı:
[`docs/IZLENEBILIRLIK.md`](docs/IZLENEBILIRLIK.md).

## Kurulum ve sınav

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

```bash
pip install -e ".[dev,gpu]"
```

GPU'suz ortamda (2705 sınav toplanıyor, GPU gerektirenler atlanır):

```bash
pytest tests -m "not gpu" --cov=dartrift
```

CUDA'lı ortamda tam paket:

```bash
pytest tests --cov=dartrift
```

Kapı koşucuları CUDA ister ve CUDA bulunmayan bir makinede **"geçti"
demez**: ilgili ölçüt kanıtlanamadığı için `KANITLANAMADI` yazıp exit 2
döner.

```bash
python scripts/run_g1_gate.py
```

> **Kütüphane tabanı.** Hedef ortam NumPy **1.26.4** kullanır; NumPy 2.0+
> API'leri (`np.trapezoid`, `np.concat`, …) kullanılamaz
> ([ADR-0005](docs/adr/ADR-0005-python-surumu-truba.md)).

## TRUBA (ARF-ACC) üzerinde kanıt üretimi

Kanıtlar hedef ortamda, temiz git ağacıyla üretilir. TRUBA kuralları
gereği `/arf`'a pip/conda ile **kurulum yapılmaz**; merkezî modül
kullanılır ve ek paketler wheel arşivleri açılarak `PYTHONPATH` üzerinden
verilir. Hazırlık giriş düğümünde bir kez yapılır:

```bash
cd /arf/scratch/<grup>/driftclaude && module purge && module load apps/truba-ai/gpu-2024.0 && python3 -m pip download warp-lang pytest-cov coverage --no-deps -d wheels && mkdir -p pylib && for w in wheels/*.whl; do python3 -m zipfile -e "$w" pylib; done
```

```bash
sbatch truba/is_HAVUZ.slurm
```

> **Donanım arızası kapı sonucu değildir.** Betikler bilinen arızalı
> düğümleri `--exclude` ile dışlar ve arıza saptarsa 75
> (`EX_TEMPFAIL`) ile çıkar; böylece bir düğüm sorunu "kapı kaldı" gibi
> görünmez.

## Mühendislik disiplini

Bu depo, doğru çıktığı şeyler kadar **yanıldığı yerlerin izlenebilir
olmasıyla** kurulmuştur.

| | |
|---|---|
| mimari karar kaydı | **60** — her büyük karar gerekçesi, alternatifleri ve sınavıyla; sessiz değişiklik yasak |
| mühendislik defteri | **78** — başarısız denemeler ve negatif sonuçlar silinmez, işlenir |
| kilitli protokol | **39** — karar kuralları koşudan **önce** yazılır, sonuç gelince değişmez |
| kusur kütüğü | [`FAZ4-SIKINTI-RAPORU.md`](docs/FAZ4-SIKINTI-RAPORU.md), A117'ye kadar — kapanan kayıtlar da duruyor |
| sınav | **2705** toplanıyor; kapı koşumları ayrıca kırmızı takım sınavlarını koşar |

Dört kural, kendimize dayattığımız biçimde:

1. **Sınav geçilmediyse iddia edilmez.** İddia daraltılır, bilim
   bükülmez — nitekim çıkarım uzayı bir kez üç parametreden bire
   indirildi ([ADR-0046](docs/adr/ADR-0046-cikarim-uzayi-olculebilir-olana-indirilir.md));
   ölçüm iyileşince üretim uzayı yeniden üç eksene açıldı
   (`DART_UZAYI_S4`, [ADR-0053](docs/adr/ADR-0053-y0-onseli-ve-tanimlayici-gozlemli.md)
   kabulüyle).
2. **Görsel olarak makul bir sonuç kanıt değildir;** kanıt sınav ve
   sayıdır.
3. **Kanıt hedef ortamda üretilir.** Yerelde yeşil olanın kümede de
   yeşil olduğu varsayılmaz — kapı mekanizması üç kez, yerelde
   görünmeyen bir kusuru yakaladı.
4. **Düzeltme silmek değildir.** Yanlış çıkan bir iddia kaydın
   üzerinden geçilerek değil, tarihli bir düzeltme notuyla kapatılır.

Son örnek: `β`'nın hangi doğrultuya izdüşürüldüğü. Ön baskı iki izdüşüm
arasındaki açıyı vermiyordu; sonradan ölçüldüğünde terimin yörünge
geometrisine değil koşunun kendi fırlatı alanına bağlı olduğu ve
ortanca farkın **1,166** olduğu görüldü — ilan edilen bütün model hata
bütçesinden büyük. Ön baskı metni değiştirilmedi (yayımlanmış kayıttır);
düzeltme [ADR-0060](docs/adr/ADR-0060-beta-hangi-dogrultuya-izdusurulur.md)
olarak eklendi ve rapor düzeltilmiş hâli taşıyor.

## Belgeler

| belge | ne |
|---|---|
| [`docs/BULGULAR.md`](docs/BULGULAR.md) | ne kanıtlandı, ne kanıtlanmadı |
| [`docs/DEVAM-BITIS3.md`](docs/DEVAM-BITIS3.md) | devir notu: durum, plan, bütçe, riskler, dersler |
| [`docs/preprint/`](docs/preprint/) | bilimsel ön baskı (İngilizce) |
| [`docs/rapor2204/`](docs/rapor2204/) | TÜBİTAK 2204-A proje raporu (Türkçe) |
| [`docs/FIZIBILITE.md`](docs/FIZIBILITE.md) | motor hedefe yetiyor mu — ölçülmüş maliyet |
| [`docs/EKSIKLER.md`](docs/EKSIKLER.md) | eksiklerin tek kaydı: kapandı / açık / kapsam dışı |

## Lisans ve atıf

Yazılım **MIT** — [LICENSE](LICENSE). Ön baskı metni ve özgün figürleri
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); üçüncü taraf
logoları (Ethosoft, ORCID, GitHub) bu lisansın dışındadır.

Atıf için [CITATION.cff](CITATION.cff) —
[10.5281/zenodo.23284193](https://doi.org/10.5281/zenodo.23284193)
(sürüm), [10.5281/zenodo.23284192](https://doi.org/10.5281/zenodo.23284192)
(kavram, en yeni sürüme çözülür).
