# Eksikler kaydı — ne kapandı, ne açık, neden

Bu belge projenin **bilinen eksiklerini** tek yerde tutar. Amaç: bir eksiğin
"unutuldu" mu yoksa "bilinçli bırakıldı" mı olduğu hiçbir zaman belirsiz
kalmasın.

**Son güncelleme:** 2026-08-01

---

## Kapatılanlar

### 1. Hasar/kırılma modeli — KAPANDI

**Durum:** P2 §1.3'te STRETCH olarak bırakılmış, kod `D = 0` sabitlemişti.

**Kapanış:** Grady-Kipp + Weibull kusur dağılımı (Benz & Asphaug 1995)
uygulandı — CPU referansı, GPU çekirdeği, config şeması, 32 test.
Ayrıntı: **ADR-0027**.

Öne çıkan tasarım noktası: hasar **yalnızca çekmeyi** zayıflatır, basmayı
değil. Basmayı da zayıflatmak kraterlenmeyi tamamen yanlış yapardı.

Dış kaynak kontrolü: varsayılan parametrelerle çekme dayanımı ≈ 32 MPa —
bazalt için literatür bandı (10–30 MPa) ile uyumlu.

**Kalan sınır:** hasar enerji defterine ayrı kalem olarak girmiyor (kırılma
yüzey enerjisi modellenmiyor). Bu, Benz & Asphaug formülasyonunun kendi
sınırıdır; ADR-0027'de kayıtlı.

### 2. Sahnenin makineler arası determinizmi — KAPANDI

**Durum:** `Scene.digest` G3'e "determinizm kanıtı" diye bağlanmıştı ama
referansı yoktu; iki makinede **tutmuyordu**.

**Kapanış:** İki gerçek kusur bulundu ve düzeltildi (**ADR-0025**) —
ışın-yüzey kesişiminin mesh köşesinde dejenere olması (yüzey normali makineye
göre **2,5°** oynuyordu, fiziksel olarak önemli) ve `centroid`'de toplama
sırası. Altın karma bekçisi kuruldu (`tests/golden/p3_scene_v1.json`,
en az iki işletim sistemi + iki numpy sürümü şartı), kırmızı takıma RT13/RT14
eklendi.

### 3. `volume`/`area` toplama sırası latent riski — KAPANDI

ADR-0025'te "kapatılmadı, izleniyor" diye bırakılmıştı; gerekçe altın karmayı
bozma riskiydi. Ölçüldü: fsum'a çevirince karma **hiç değişmedi**, yani
gerekçe geçersizdi. Kapatıldı.

### 4. Blok kesri hedefe ulaşmıyordu — KAPANDI

**Durum:** hedef 0,30 iken 0,2672 kalıyordu (doyma bayrağı açık, dürüstçe
raporlanıyordu ama hedef tutmuyordu).

**Kök neden (ölçüldü):** bloklar rastgele sırada yerleştiriliyordu; büyük
bloklar sona kalınca sığacak yer bulamıyordu. 20000 denemenin 15402'si mesh
dışı, 4565'i çakışma nedeniyle reddediliyordu.

**Kapanış:** her partide **büyükten küçüğe** yerleştirme. Ölçülen:
f 0,2672 → **0,3034** (hedef 0,30) ve deneme 20000 → 2048 (**~10× hızlı**).
Altın karma yenilendi, eski değer `history` alanında saklandı.

### 5. RNG akış kilidinin fazla geniş olması — KAPANDI

`test_stream_ids_are_locked` tam eşitlik arıyordu ve **sona ekleme**yi de
yasaklıyordu. ADR-0004'ün yasakladığı şey var olan bir akışın kimliğini
oynatmaktır. Test, "mevcut girdiler değişmesin + yeni kimlikler ≥ 3 olsun +
boşluksuz olsun" biçimine daraltıldı.

---

## Açık kalanlar

### A. G3 C7 — PDS veri manifestosu · **ONAY BEKLİYOR**

Gereken paket **belirlendi**: `urn:nasa:pds:dart_shapemodel::1.0`
(DART Shapemodel Archive Bundle, Daly ve diğerleri 2023). TRUBA giriş
düğümünden PDS-SBN'e erişim **ölçüldü ve var**. İndirme + manifest betiği
yazıldı (`scripts/fetch_pds_shapemodel.py`; SHA-256'yı indirme sırasında akış
halinde hesaplar, varsayılan olarak hiçbir şey indirmez).

**Eksik olan tek şey:** dış kaynaktan dosya indirme onayı. Onay geldiğinde tek
komutla kapanır. Ayrıntı: `data_manifest/GEREKEN_URUNLER.md`.

**Etkisi:** FAZ 4 çıktıları gerçek Dimorphos geometrisiyle tekrarlanana kadar
"DART senaryosu" değil **"DART benzeri senaryo"** olarak adlandırılır.

### B. Mermi çözünürlüğü · **ÖLÇÜLDÜ, FAZ 4 TASARIM KARARI**

DART mermisini çapı boyunca 6 parçacıkla çözmek **1,72e9 parçacık** gerektirir
— ölçülmüş fizibil üst sınırın (1,12e7) **153 katı**. Fizibil sınırda mermi
çapı boyunca yalnızca **1,12 parçacık** düşer.

Bu bir kusur değil, bir **ölçek gerçeğidir** ve FAZ 4'ün tekdüze ağla
yapılamayacağını söyler; çarpma bölgesinde yerel yüksek çözünürlük gerekir.
Karar ve sayılar: **ADR-0026**. Yerel incelmenin *nasıl* yapılacağı FAZ 4'te
ölçümle seçilecek.

> Bu, `docs/FIZIBILITE.md`'nin "11,2 M parçacık yeter" iddiasını daralttı.
> İddia silinmedi, §6'da notla düzeltildi.

### C. Uzun koşu kararlılığı · **ÖLÇÜM SÜRÜYOR**

Yerel ön ölçüm (çözünmüş mermi, 400 adım): enerji hatası **%1,49'da sabit**,
log-log eğim **0,001** — yani hata **birikmiyor**, çarpma anında oluşan tek
seferlik bir kaymadır. Momentum 6,6e-15'te korunuyor.

TRUBA'da 30 000 adımlık koşu sürüyor (iş 1445921). Sonuç geldiğinde bu bölüm
kesinleşecek ve `FIZIBILITE.md` §5'teki madde kapanacak.

### D. Gereken simüle süre · **ÖLÇÜM SÜRÜYOR**

β'nın ne zaman durulduğu koşu maliyetini 10 kat değiştirir. Yerel ön ölçümde
β yükselmeye başladı (adım 400'de 1,196, 208 ejekta parçacığı) ama plato
görülmedi. Aynı TRUBA koşusu bunu ölçüyor.

**Ölçüm yöntemi notu:** plato, **bağlı kütle** momentumundan türetilen β ile
aranır, ejektadan türetilenle değil. Ejekta betası parçacıkların kontrol
yüzeyini geçmesini bekler; m/s mertebesindeki ejekta için bu 100+ saniye eder
ve kraterlenme çoktan bitmiş olsa bile plato görünmez.

---

## Bilinçli kapsam dışı (eksik değil)

- **Yerçekimsel settling.** Bir serbest düşme süresi DART çözünürlüğünde
  1,28e7 adım eder ve Dimorphos'ta litostatik basınç (3,05 Pa) kohezyonun
  3300 katı altındadır — yani hem hesaplanabilir değil hem gereksiz.
  Gerekçe ve sayılar: **ADR-0024**.
- **Hedefin dönmesi.** Dimorphos gelgit kilitli; yüzey hızı ~1,2 cm/s. Şok
  fazı için ihmal edilebilir, ancak kaçış hızının (8,4 cm/s) %14'ü olduğu için
  ejekta fazında etkisi ölçülmelidir — FAZ 4.
