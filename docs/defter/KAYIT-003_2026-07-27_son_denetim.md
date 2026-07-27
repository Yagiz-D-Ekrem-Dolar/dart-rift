```
TÜBİTAK 2204 PROJESİ
MÜHENDİSLİK DEFTERİ — GÜNLÜK ÇALIŞMA KAYDI

Proje Adı   : DART-RIFT
Takım       : kayıt bulunamadı
Danışman    : kayıt bulunamadı
```

============================================================
GÜNLÜK KAYIT NO: 003
============================================================

**Tarih**       : 27.07.2026
**Saat**        : 14:20 – 14:50 UTC
**Çalışanlar**  : Yağız Ekrem Dalar (`egitimg16u4`)
**Çalışma Yeri**: Çevrim içi — yerel makine + TRUBA/ARF-ACC

## BUGÜNKÜ HEDEF

FAZ 0 temel faz olduğu için üçüncü ve son bir denetim turu: şartnamenin
sözde-kod düzeyindeki maddelerini tek tek koda karşı okumak, kapı koşucusunun
**iddia dürüstlüğünü** sınamak ve önceki kayıtlarda yanlış kalmış bilgileri
düzeltmek.

## KARŞILAŞILAN SORUNLAR (bu turun bulguları)

### Kusur 4 — §6.2'nin son satırı uygulanmamıştı

Şartname §6.2 sözde-kodunun son satırı şudur:

```
# ihlal -> koşuyu 'numerical_failure' etiketiyle durdur, config dondur
```

Bende invariant ihlali `InvariantViolation` fırlatıyordu, ama:
- `numerical_failure` durumu hiçbir yerde **üretilmiyordu** (sabit listede
  tanımlıydı, kullanılmıyordu),
- başarısız koşunun config'i **dondurulmuyordu**.

Bu, Kusur 1 ile aynı türden bir boşluktu: iki parça mevcut, aralarındaki köprü
yok. Ana Plan'ın risk tablosu da aynı davranışı istiyor ("şok motoru kararsız →
failing config'i dondur"), yani FAZ 1'de ilk NaN görüldüğünde hazır olmalıydı.

### Kusur 5 — Kapı koşucusu GPU'suz ortamda "G0 GEÇTİ" diyordu

`--require-gpu` bayrağı verilmezse, CUDA bulunmayan bir makinede C3 kriteri
("CPU↔GPU roundtrip bit-eşit") **GEÇTİ** sayılıyor ve rapor "SONUÇ: G0 GEÇTİ"
yazıyordu. Oysa gerçek bir CUDA cihazı olmadan bu kriter kanıtlanamaz.

Bu sadece bir bayrak hatası değil, bir **iddia dürüstlüğü** hatasıdır:
projenin altın kuralı "test geçilmediyse iddia edilmez" der; burada koşucu,
koşulmamış bir testi geçmiş sayıyordu.

### Düzeltme — önceki kayıtta yanlış bilgi

KAYIT-001, yerel makinede Warp'ın "DLL ilkesi nedeniyle init edilemediğini" ve
GPU testlerinin SKIP olduğunu yazıyordu. Bu bilgi **yanlış çıktı**: ilk
denemede warp.dll gerçekten engellendi, ancak sonraki koşularda yüklendi.
Yerel makinede NVIDIA GeForce RTX 3050 Laptop GPU (sm_86, sürücü 573.05)
mevcut ve GPU roundtrip testleri orada da geçiyor.

RULES.txt "kayıtları silmek yerine yanlış bilgiyi düzelterek açıklama ekleyin"
dediği için KAYIT-001 silinmedi; başına düzeltme notu eklendi.

**Beklenmedik kazanç:** Bit-eşit CPU↔GPU roundtrip artık iki farklı GPU
mimarisinde doğrulanmış oldu — sm_86 (RTX 3050, Windows) ve sm_90 (H100,
Linux). Determinizm iddiası tek bir donanıma bağlı değil.

## UYGULANAN ÇÖZÜMLER

1. **`src/dartrift/failure.py`** yazıldı: `freeze_failed_run()` bir ihlalde
   koşuyu `numerical_failure` etiketiyle mühürler ve üç dosya üretir —
   `manifest.yaml` (Ek A tam, config gömülü), `failing_config.yaml`
   (dondurulan config), `violation_report.txt` (ihlal eden alanlar, kural,
   parçacık indeksleri). Başarısız koşu da **yeniden üretilebilirdir**; bu
   olmadan hata ayıklama mümkün değildir. Temiz bir raporu başarısızlık gibi
   dondurmak açıkça reddedilir. 9 test.

2. **Kapı koşucusu artık kanıtlanmamış kriteri geçmiş saymıyor.** CUDA yoksa:
   C3 **KANITLANAMADI** olarak işaretlenir, rapor başlığı "G0 ÖN-KONTROL
   Raporu (KAPI DEĞİL)" olur ve metin hiçbir koşulda "G0 GEÇTİ" içermez.
   Bayraksız çalıştırma exit 2 döner; yerel ön kontrol için `--allow-no-gpu`
   gerekir ve o mod da kapı iddiası üretmez.

3. **Bu davranış gerçek bir GPU'suz ortamda test ediliyor.** Yerel makinede GPU
   olduğu için burada sınanamıyordu; GitHub CI runner'ı gerçekten GPU'suz
   olduğundan doğrulama oraya kondu: exit kodunun 2 olduğu, raporda
   "ÖN-KONTROL" ve "KANITLANAMADI" geçtiği, "G0 GECTI" **geçmediği** denetleniyor.
   Kırmızı takım listesi de artık her CI koşusunda işletiliyor.

4. Küçük sağlamlık düzeltmeleri: manifestteki CUDA sürümü ham tuple `(12, 9)`
   yerine `12.9` biçiminde yazılıyor; `ParticleStore.__getattr__` nesne henüz
   kurulmamışken (kopyalama/pickle) sonsuz özyinelemeye girmeyecek şekilde
   korundu.

## ALINAN SONUÇLAR

Nihai kanıt koşusu: **job 1425656**, **palamut4 / NVIDIA A100-SXM4-80GB**,
temiz git ağacı (`git_sha: 4528baf1…`).

| Bölüm | Sonuç |
|-------|-------|
| Kırmızı takım (§12) | 6/6 **TEMİZ** |
| G0 kapısı (§9) | 8/8 **GEÇTİ** |
| Test | 219 geçti, hiçbiri atlanmadı (4,99 s) |
| Kapsam | %97,1 (eşik %85) |
| ADR | 6 |

Kanıt koşusu bu kez A100'de yapıldı çünkü `kolyoz-cuda` kuyruğunun tamamı
doluydu (bekleyen iş 1425652 iptal edilip `palamut-cuda`'ya taşındı). Bunun
iki yan kazancı oldu:

1. **palamut4 sorunsuz çalıştı** — yani KAYIT-001'de bulunan depolama arızası
   `palamut-cuda` kuyruğunun tamamına değil, yalnızca `palamut5` düğümüne
   özgüymüş. Önceki kayıtta "palamut-cuda'daki palamut5" denmişti, bu doğrulandı.
2. **Üçüncü GPU mimarisi.** Bit-eşit roundtrip artık sm_80 (A100), sm_90 (H100)
   ve sm_86 (yerel RTX 3050) üzerinde doğrulanmış durumda; determinizm iddiası
   tek bir donanıma bağlı değil.

Betikteki `-C H100` kısıtı kolyoz kuyruğu içindir; palamut'ta koşarken komut
satırından geçersiz kılınır:
`sbatch -p palamut-cuda -C palamut --exclude=palamut5 slurm/faz0_g0_gate.sh`

## YAPILAN TESTLER

- **Başarısızlık dondurma:** ihlal içeren rapor `numerical_failure` statüsüyle
  mühürleniyor; manifest yine Ek A'yı tam dolduruyor; config diske
  donduruluyor; dondurulmuş koşu manifestten geri kurulabiliyor; ihlal raporu
  alan adlarını ve parçacık indekslerini içeriyor; temiz rapor başarısızlık
  olarak dondurulamıyor.
- **İddia dürüstlüğü:** GPU'suz ortamda kapı koşucusu exit 2 dönüyor ve
  `--allow-no-gpu` ile üretilen rapor "G0 GECTI" ifadesini içermiyor
  (GitHub CI, gerçek GPU'suz runner).

## ALINAN KARARLAR

- Başarısız koşu, başarılı koşuyla **aynı** manifest tamlığında kaydedilir.
  Başarısızlığı eksik kaydetmek, onu gizlemenin bir biçimidir.
- Kanıtlanamayan bir kriter asla "GEÇTİ" sayılmaz; "KANITLANAMADI" ayrı bir
  sonuçtur ve kapı iddiasını geçersiz kılar.
- Yanlış çıkan defter kayıtları silinmez, düzeltme notuyla işaretlenir.

## DEĞİŞTİRİLEN DOSYALAR / SÜRÜMLER

```
Kod sürümü : dartrift 0.1.0
Yeni       : src/dartrift/failure.py, tests/test_failure.py,
             docs/defter/KAYIT-003_*.md
Değişen    : scripts/run_g0_gate.py, src/dartrift/{logging_cfg,particles}.py,
             .github/workflows/ci.yml, environment.lock,
             docs/defter/KAYIT-001_*.md (düzeltme notu)
```

## KANITLAR

- **KANIT-010** — `docs/evidence/G0_report_truba_1425656.md` (nihai kanıt,
  palamut4 / A100)
- **KANIT-011** — CI adımı "Kapi, GPU'suz ortamda GECTI iddia etmemeli"
  (gerçek GPU'suz runner'da yeşil)
- **KANIT-012** — Üç GPU mimarisinde bit-eşit roundtrip: sm_80 (A100,
  job 1425656), sm_90 (H100, job 1425590), sm_86 (yerel RTX 3050)

## BUGÜNÜN DEĞERLENDİRMESİ

Üç denetim turunun toplamı beş kusur çıkardı ve hepsi aynı iki kalıba
giriyordu: **(a) iki doğru parça arasında kurulmamış köprü** (config↔motor,
invariant↔manifest), **(b) kanıtlanmamış bir şeyi kanıtlanmış gibi raporlamak**
(GPU'suz "G0 GEÇTİ", yalnızca hash taşıyan manifest).

Bu, FAZ 0 gibi "görünmez" bir fazın neden kapı arkasına alındığını gösteriyor:
kusurların hiçbiri koşuyu çökertmiyordu, hepsi sessizce yanlış kayıt üretiyordu
— ve sessiz yanlış kayıt, FAZ 6'daki kilitli tahminin değerini doğrudan yok
ederdi.

Şartnamenin ölçülebilir her maddesi artık karşılanıyor ve her biri bir testle
bağlı. Bulunabilecek başka kusur yok demiyorum; diyebileceğim şu: şartnamede
yazılı olup kodda karşılığı olmayan bir madde kalmadı.

## SONRAKİ ÇALIŞMA

FAZ 1 (DR-RIFT-P1). `failure.freeze_failed_run()` ilk NaN'de kullanıma hazır.
ADR-0006 gereği `numerics.kernel` ve `numerics.cfl` alanları, onları tüketen
kod ve davranış testiyle birlikte devreye alınacak.

**Kayıt Sahibi:** Yağız Ekrem Dalar
