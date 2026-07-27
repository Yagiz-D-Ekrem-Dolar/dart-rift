```
TÜBİTAK 2204 PROJESİ
MÜHENDİSLİK DEFTERİ — GÜNLÜK ÇALIŞMA KAYDI

Proje Adı   : DART-RIFT
Takım       : kayıt bulunamadı
Danışman    : kayıt bulunamadı
```

============================================================
GÜNLÜK KAYIT NO: 002
============================================================

**Tarih**       : 27.07.2026
**Saat**        : 13:45 – 14:15 UTC (TRUBA iş kayıtlarından)
**Çalışanlar**  : Yağız Ekrem Dalar (`egitimg16u4`)
**Çalışma Yeri**: Çevrim içi — yerel makine + TRUBA/ARF-ACC

## BUGÜNKÜ HEDEF

KAYIT-001'de G0 kapısı geçilmişti. Bu oturumun hedefi farklı: **"kapı geçti"
ile "iş kusursuz" aynı şey mi?** sorusunu ciddiye alıp FAZ 0 teslimatını
şartnameye karşı eleştirel biçimde denetlemek ve bulunan her kusuru kapatmak.

## YAPILAN ÇALIŞMALAR

1. DR-RIFT-P0 şartnamesi ile mevcut kod satır satır karşılaştırıldı
   (13 gereksinim ID'si, §5 mimari, §9 kapı, §10 teslimatlar, §12 kırmızı takım).
2. Üç kusur tespit edildi (aşağıda).
3. Kusurlar giderildi, her biri için davranış testi yazıldı.
4. ADR-0006 yazıldı; §12 kırmızı-takım listesi otomatik koşucuya dönüştürüldü.
5. Temiz git ağacından nihai kanıt koşusu alındı (job 1425590).

## KARŞILAŞILAN SORUNLAR (öz-denetim bulguları)

### Kusur 1 — Sessiz config sapması (ciddi)

Config şeması `numerics.precision`, `io.output_layers`, `io.hdf5_compression`
ve `domain` alanlarını **doğruluyordu**, ama motorun hiçbir parçası bu
değerleri **okumuyordu**.

Somut sonuç: `precision: performance_mixed` yazan bir koşu sessizce FP64
çalışmaya devam ederdi; `output_layers: [scalar_budget]` yazan bir koşu yine
üç katmanı da yazardı. Daha kötüsü, manifest config'ten okuduğu için "doğru"
değeri raporlardı — yani hata, yeniden-üretilebilirlik iddiasını doğrudan
zehirliyordu.

Bunu hiçbir test yakalamamıştı, çünkü tüm testler şemayı ve motoru **ayrı
ayrı** sınıyordu; ikisinin birbirine bağlı olduğunu sınayan tek bir test yoktu.

### Kusur 2 — Manifest koşuyu yeniden üretmeye yetmiyordu

§12'nin dördüncü maddesi "Manifest, koşuyu sıfırdan yeniden üretmeye yetiyor
mu?" diye soruyor. Önceki manifest yalnızca `config_hash` taşıyordu. Hash
"aynı mı?" sorusunu yanıtlar, "neydi?" sorusunu yanıtlamaz — orijinal YAML
kaybolursa koşu yeniden kurulamazdı.

### Kusur 3 — §12 kırmızı-takım listesi hiç işletilmemişti

Yol Haritası §7.5 bunu teslim şartı sayıyor ("her fazın kırmızı-takım kontrol
listesi teslimden önce işletilir"). KAYIT-001'de bu adım tamamen atlanmıştı.

## UYGULANAN ÇÖZÜMLER

1. **Bağlama köprüleri.** `RunConfig.store_precision` ve `.domain_bounds`
   özellikleri; hassasiyet eşlemesi tek bir sözlükte toplandı.
   `ParticleStore.from_config()` ve `Hdf5Writer.from_config()` fabrikaları.
   `output_layers` gerçekten uygulanıyor: kapalı katman oluşturulmuyor ve ona
   yazmak `LayerDisabledError` üretiyor — sessiz yok sayma, sessiz sapmanın
   diğer yüzü olduğu için yasaklandı. Açık katmanlar dosyanın kök attr'ına
   yazılıyor ki okuyucu "boş mu, kapalı mı" ayrımını yapabilsin.
   `tests/test_config_wiring.py`: 17 test, hepsi "alanı değiştir → çıktı
   gerçekten değişti mi" biçiminde.
2. **Config manifeste gömüldü.** `config` ve `config_hash` Ek A zorunlu
   alanlarına eklendi. `config_from_manifest()` config'i geri kurar ve gömülü
   içerik ile kayıtlı hash uyuşmazsa kurcalama olarak reddeder.
3. **`scripts/run_red_team.py`** yazıldı; altı maddeyi işletip kanıt raporu
   üretiyor ve artık her TRUBA kanıt koşusunda kapıdan önce çalışıyor.

Ek olarak SLURM betiğine **GPU sağlık kontrolü** eklendi (aşağıdaki arıza
nedeniyle): arızalı düğümde erken, net mesajla ve EX_TEMPFAIL (75) ile çıkılıyor.

## ALINAN SONUÇLAR

Nihai kanıt koşusu **job 1425590**, kolyoz19 / H100, temiz git ağacı
(`git_sha: 260f1324…`, dirty işareti yok):

| Bölüm | Sonuç |
|-------|-------|
| Kırmızı takım (§12) | 6/6 **TEMİZ** |
| G0 kapısı (§9) | 8/8 **GEÇTİ** |
| Test | 210 geçti, hiçbiri atlanmadı (5,95 s) |
| Kapsam | %97,4 (eşik %85) |
| ADR | 6 |

KAYIT-001'deki koşuya göre test sayısı 185 → 210, ADR 5 → 6.

## YAPILAN TESTLER

- **Hassasiyet bağlama:** `deterministic_fp64` → FP64 kinematik,
  `performance_mixed` → FP32 kinematik; ikisinin dtype'ları farklı olduğu
  doğrulandı. Şemaya yeni hassasiyet eklenirse köprü güncellenmeden CI kırılır.
- **Katman bağlama:** kapalı katman dosyada oluşturulmuyor; ona yazmak hata
  veriyor; açık katman aynı dosyada çalışmaya devam ediyor.
- **Sıkıştırma bağlama:** gzip/lzf/none üçü için HDF5 veri kümesinin gerçek
  `compression` özniteliği okunarak doğrulandı.
- **Domain bağlama:** dar domain kaçan parçacığı yakalıyor, geniş domain aynı
  durumu kabul ediyor.
- **Yeniden üretim:** config yalnızca manifestten geri kuruldu, aynı hash ve
  aynı depo modunu verdi; kurcalanmış manifest reddedildi.
- **Altın hash platform şartı:** en az iki farklı işletim sisteminde
  doğrulanmış olması artık ayrı bir testle zorlanıyor.

## ALINAN KARARLAR

- **ADR-0006 (yeni):** Config şemasına, onu tüketen kod ve tüketimi kanıtlayan
  davranış testi olmadan alan eklenmez. Kapatılan bir yetenek sessizce yok
  sayılmaz, açık hata verir.
- Kanıt dosyaları silinmez: aşılan kanıt (1425495) durur, geçerli olan
  (1425590) tabloda işaretlenir.
- Donanım arızası ile kapı başarısızlığı ayrı raporlanır (EX_TEMPFAIL 75).

## DEĞİŞTİRİLEN DOSYALAR / SÜRÜMLER

```
Kod sürümü : dartrift 0.1.0 — kanıt commit'i 260f132
Dosyalar   : src/dartrift/{config,particles,io_hdf5,logging_cfg}.py
             tests/{test_config_wiring,test_manifest,test_determinism_golden}.py
             tests/golden/p0_canonical_v1.json (verified_on eklendi)
             scripts/{run_red_team,update_golden}.py
             slurm/faz0_g0_gate.sh, docs/adr/ADR-0006-*.md
```

## KANITLAR

- **KANIT-006** — `docs/evidence/G0_report_truba_1425590.md` (kırmızı takım
  6/6 + G0 8/8, 210 test, %97,4, temiz ağaç)
- **KANIT-007** — SLURM: `1425590 COMPLETED 0:0 00:00:17 kolyoz19`
- **KANIT-008** — Manifest içinde gömülü config (yeniden üretim kanıtı)
- **KANIT-009** — Altyapı arızası: job 1425588 kolyoz13, "No devices were
  found" (GPU sürücü arızası; kapı sonucu değil)

## BUGÜNÜN DEĞERLENDİRMESİ

Hedef tamamlandı. En önemli çıkarım: **kapının sekiz kriterini geçmek, işin
kusursuz olduğunu göstermez.** Kriterler modülleri tek tek sınıyordu; kusur ise
modüllerin *arasındaki* boşlukta duruyordu — şema doğruluyor, motor okumuyordu.
Bu tür hatalar ancak "bu sistemi nasıl kandırabilirim" sorusuyla, yani kırmızı
takım bakışıyla bulunur. Şartname bu adımı zorunlu tutuyordu ve ilk turda
atlanmıştı; şimdi otomatikleştirildi, bir daha atlanamaz.

İkinci çıkarım: bir kusuru bulmak, onu bulan testi yazmadan kapatmak yetmez.
Her düzeltme, kusuru yeniden ortaya çıksa yakalayacak bir davranış testiyle
birlikte işlendi.

Dürüstlük sınırı değişmedi: bu faz hâlâ "boş ama sağlam" bir motordur. Hiçbir
fizik, hiçbir DART simülasyonu, hiçbir bilimsel sonuç iddia edilmemektedir.

## SONRAKİ ÇALIŞMA

FAZ 1 (DR-RIFT-P1). ADR-0006 sözleşmesi gereği, FAZ 1'de eklenecek
`numerics.kernel` ve `numerics.cfl` alanları da yalnızca onları tüketen kod ve
davranış testiyle birlikte devreye alınacaktır.

**Kayıt Sahibi:** Yağız Ekrem Dalar
