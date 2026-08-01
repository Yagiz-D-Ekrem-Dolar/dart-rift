# Fizibilite: motor projenin amacına yetiyor mu?

Bu belge tek bir soruyu ölçümle yanıtlar: **FAZ 0–2'de kurulan motor,
projenin asıl hedefine (DART verisinden Dimorphos'un iç yapısını Bayesçi
çıkarımla geri hesaplamak) gerçekten yetiyor mu?**

Bir motorun doğrulama senaryolarını geçmesi, hedef problemi çözebileceği
anlamına gelmez. Ölçek, süre ve maliyet ayrıca sınanmalıdır.

## 1. Ölçek — ölçüldü (TRUBA, NVIDIA H200, 150 GB)

Düzgün kübik kafes, `h/dx = 2` (~268 komşu), tam FAZ 2 fiziği (Tillotson +
dayanım + süreklilik yoğunluğu):

| N | eval | µs / 1000 parçacık | adım | bellek |
|---|---|---|---|---|
| 64 000 | 9,62 ms | 150,3 | 102 ms | 0,59 GB |
| 373 248 | 49,20 ms | 131,8 | 113 ms | 0,76 GB |
| 1 000 000 | 126,88 ms | 126,9 | 287 ms | 1,09 GB |
| 2 744 000 | 361,15 ms | 131,6 | 805 ms | 2,00 GB |
| 5 832 000 | 756,55 ms | 129,7 | 1 724 ms | 3,48 GB |
| **11 239 424** | 1 388,63 ms | **123,6** | 3 009 ms | **5,99 GB** |

**Sonuç:**

- Maliyet **N ile doğrusal** — 175 kat aralıkta parçacık başına maliyet
  123–150 µs bandında sabit. Hash-grid komşu arama beklendiği gibi çalışıyor;
  gizli bir `O(N²)` yok.
- **Bellek darboğaz değil.** 11,2 milyon parçacık 150 GB'ın yalnızca 6'sını
  kullanıyor. Aynı düğümde ~200 milyon parçacık belleğe sığar; sınır hesap
  süresidir.
- H200, yerel RTX 3050'den **~50 kat** hızlı (aynı N'de 49,2 ms ↔ 2 472 ms).

## 2. Bir DART koşusunun maliyeti

Dimorphos ≈ 160 m. Yayımlanmış benzer çalışmalar (Raducan & Jutzi tipi)
tipik olarak ~2 × 10⁶ parçacık kullanır → `dx ≈ 1,3 m`, `h ≈ 2,5 m`.

Zaman adımı, çarpma hızı da dahil sinyal hızıyla sınırlanır:
`dt ≈ cfl · h / (c_s + v) ≈ 0,25 · 2,5 / (3000 + 6100) ≈ 6,9 × 10⁻⁵ s`.

Ölçülen adım maliyeti (2,74 M'de 805 ms → 2 M'de ~600 ms):

| Simüle edilen süre | adım | tek koşu |
|---|---|---|
| 1 s | ~14 500 | **~2,4 saat** |
| 10 s | ~145 000 | ~24 saat |

FAZ 5 için ADR-0004 **"yüzlerce koşu"** öngörüyor:

| Senaryo | Toplam |
|---|---|
| 300 koşu × 1 s | ~30 GPU-günü |
| 300 koşu × 10 s | ~300 GPU-günü |

**Sonuç: 1 saniyelik koşularla ensemble fizibil.** 10 saniyelik koşularla
sınırda — bu durumda ya çözünürlük düşürülür, ya vekil (surrogate) model
kullanılır, ya da daha fazla GPU-saat gerekir. Bu, FAZ 3'te *ölçülerek*
karara bağlanmalıdır; şu an tahmin edilebilir ama bilinemez, çünkü gereken
simüle süre momentum aktarımının ne zaman durulduğuna bağlıdır.

## 2b. ÖNEMLİ DÜZELTME — yukarıdaki ölçüm yerçekimi KAPALI yapıldı

§1'deki tablo `porozite` ve `öz-yerçekimi` kapalı ölçülmüştür. Tam fizikle
(ikisi de açık) yeniden ölçüldü (TRUBA H100, iş 1429628):

| N | adım | µs / 1000 parçacık | bellek |
|---|---|---|---|
| 19 416 | 301 ms | 15 520 | 0,63 GB |
| 65 840 | 570 ms | 8 658 | 0,63 GB |
| 180 136 | 2 909 ms | 16 146 | 0,69 GB |
| 403 176 | 4 005 ms | 9 934 | 0,79 GB |
| 831 932 | 4 837 ms | 5 814 | 1,03 GB |

Karşılaştırma: yerçekimi kapalı 1 M parçacıkta adım **287 ms**; tam fizikle
832 K parçacıkta **4 837 ms** — yaklaşık **17 kat** yavaş. Parçacık başına
maliyet de artık sabit değil (5 814–16 146 µs), çünkü baskın kalem **CPU'da
Python'da kurulan Barnes-Hut ağacı**dır ve maliyeti ağaç yapısına bağlıdır.

**Sonuç:** §2'deki "bir DART koşusu ~2,4 saat" tahmini **yalnızca
öz-yerçekimi kapalıyken** geçerlidir. Açıkken mevcut uygulamayla ~17 kat,
yani ~40 saat olur ve "yüzlerce koşu" fizibil değildir.

Bu, FAZ 3 için somut bir gereksinim doğurur: **ya çarpma fazı yerçekimsiz
koşulur** (160 m'lik bir cisimde ilk saniyelerde yerçekimi dayanımın yanında
ihmal edilebilir — literatürdeki standart yaklaşım), **ya ağaç GPU'da
kurulur**, ya da ağaç K adımda bir yenilenir. Ağaç kurulumu ~O(N^1,2)
ölçekleniyor (22,6 ms @ 4 K → 187,3 ms @ 30 K); 2 M parçacıkta tek kurulum
~29 s eder.

## 2c. Uzun koşu kararlılığı — ÖLÇÜLDÜ, sonuç iyi

FAZ 3'ün en büyük bilinmeyeni buydu: tüm kapı senaryoları birkaç yüz adım,
gerçek bir koşu ~10⁵ adım. Tam fizikli bir çarpma **30 000 adım** koşuldu
(TRUBA H100, iş 1429628):

| adım | enerji hatası | momentum | kütle |
|---|---|---|---|
| 2 000 | %44,81548 | 7,3e-12 | 0,00e+00 |
| 10 000 | %44,80285 | 2,9e-10 | 0,00e+00 |
| 20 000 | %44,80285 | 1,0e-09 | 0,00e+00 |
| **30 000** | **%44,80285** | 1,7e-09 | **0,00e+00** |

**Drift oranı 15 kat daha fazla adımda 1,00×** — yani enerji hatası
**hiç birikmiyor**. Kütle bit düzeyinde korunuyor, momentum 1e-9
mertebesinde kalıyor, tüm alanlar sonlu, `rho_min` pozitif.

Buradaki %44,8'in kendisi ayrı bir kusurdur (P-α sıkışma enerjisi,
[ADR-0022](adr/ADR-0022-porozite-baslangic-ve-acik-enerji-kusuru.md)); bu koşu
o düzeltmeden önceki kodla yapıldı. Önemli olan **eğimin sıfır olması**:
zaman integrasyonu uzun koşuda kararlıdır.

## 2d. Determinizm ölçekte — ÖLÇÜLDÜ

G0'ın bit-eşit determinizm iddiası yalnızca küçük N'de sınanmıştı. Tam
fizikle (Tillotson + dayanım + gözeneklilik + Barnes-Hut yerçekimi) aynı koşu
iki kez yapıldı:

| N | hash A | hash B | sonuç |
|---|---|---|---|
| 19 416 | `a6eabe4c53fef84b` | `a6eabe4c53fef84b` | **BİT-EŞİT** |
| 65 840 | `49b9cd70c51abcef` | `49b9cd70c51abcef` | **BİT-EŞİT** |

Bu, ensemble çıkarımının ön koşuludur: iki koşu arasındaki fark yalnızca
parametre değişikliğinden gelebilir, sayısal gürültüden gelemez.

## 3. Fizik kapsamı — hedefe uygun mu?

DART/Dimorphos gibi **zayıf ve gözenekli** bir hedef için literatürde
kullanılan standart model seti:

| Bileşen | Durum |
|---|---|
| Tillotson EOS | ✅ var — deneysel Hugoniot'a karşı doğrulandı (`test_hugoniot.py`) |
| P-α gözeneklilik (crush) | ✅ var |
| Basınca bağlı dayanım Y(P) + sürtünme | ✅ var |
| Öz-yerçekimi (Barnes-Hut) | ✅ var |
| **Hasar / kırılma (D)** | ❌ **yok** — `D = 0` sabit (P2 §1.3, STRETCH) |

Hasar modelinin yokluğu **zayıf/gözenekli hedefler için savunulabilir**:
o rejimde krater oluşumuna hâkim olan mekanizma gözenek çökmesidir (P-α),
kırılma değil. Ancak bu bir **model sınırlamasıdır** ve üretilecek her
posterior ile birlikte açıkça belirtilmelidir. Hedefin sanılandan daha
sağlam (kohezyonlu) çıkması durumunda sonuçlar yanlı olur.

## 4. Doğrulama işi neden anlamlı?

Bayesçi çıkarımda ileri model hatası **kaybolmaz, posteriora taşınır**.
Kalibre edilmemiş bir motor, dar ve **kendinden emin biçimde yanlış** bir
posterior üretir — ki bu, geniş ve dürüst bir posteriordan daha kötüdür,
çünkü Hera ölçümüyle karşılaştırıldığında projenin iddiasını çürütür.

Bu yüzden FAZ 0–2'deki her ölçüt doğrudan hedefe hizmet eder:

| Doğrulama | Hedefe katkısı |
|---|---|
| Sod / Sedov | şok yayılımı doğru; krater büyüklüğü buna bağlı |
| Hugoniot | EOS'un **mutlak ölçeği** doğru; basınç–yoğunluk ilişkisi çıkarımın temeli |
| Taylor bar | plastik akış doğru; kalıcı deformasyon = krater |
| Crush curve | gözenek çökmesi doğru; **çıkarımın asıl parametresi** budur |
| Öz-yerçekimi | ejekta yeniden birikmesi ve gravitasyon rejimi |
| Determinizm (G0) | aynı girdi → aynı çıktı; ensemble'da parametre etkisini gürültüden ayırmanın ön koşulu |

Son madde özellikle önemlidir: determinizm olmadan iki koşu arasındaki farkın
parametre değişikliğinden mi yoksa sayısal gürültüden mi geldiği ayırt
edilemez, ve çıkarım anlamsızlaşır.

## 5. FAZ 3'ün ölçmesi gerekenler — DURUM (2026-08-01, FAZ 3 bitti)

Bu belgedeki hiçbir sayı FAZ 3'ün yerini tutmaz. Üç madde vardı:

1. **Uzun koşu kararlılığı** — hâlâ ölçülmedi. Tüm kapı senaryoları
   ≤ 262 144 parçacık ve birkaç yüz adımdır; bir DART koşusu ~10⁴–10⁵
   adımdır. ADR-0020 enerji hatasının `O(dt)` olduğunu gösterdi, ama bu 10⁵
   adımda ne birikir bilinmiyor. **FAZ 4'e taşınıyor.**
2. **Gereken simüle süre** — hâlâ ölçülmedi. β'nın ne zaman durulduğu
   koşunun maliyetini 10 kat değiştirir. **FAZ 4'e taşınıyor.**
3. **Çözünürlük yakınsaması** — *mermi* tarafı ölçüldü (P3-VR-02: 3
   çözünürlükte hacim hatası %3,5 → %0,5, kütle hatası < 6e-16). *Krater çapı
   ve β'nın* çözünürlüğe duyarlılığı çarpma koşusu gerektirir; **FAZ 4'e
   taşınıyor.**

### FAZ 3'te ek olarak ölçülen ve fizibiliteyi etkileyen şey

**Yerçekimi maliyeti, sanıldığı gibi bir engel değil** (ADR-0024). Ölçüldü:

- Barnes-Hut ağacının kurulumu yerçekimli değerlendirmenin **%99,8'i**.
- Ama şok/krater fazında (~1–10 s) yerçekiminin ürettiği yer değiştirme,
  DART çözünürlüğünde parçacık aralığının **2e-05 – 2e-03 katı** — ihmal
  edilebilir.
- Ağaç yenileme aralığı K 1'den 1000'e çıkarken hata %0,92 → %0,96 (K=1'deki
  %0,92 zaten θ=0,5 Barnes-Hut'ın kendi tabanı). Denetim değişkeni **aralığa
  göre sürüklenme**, adım sayısı değil.

Sonuç: §2b'deki "yerçekimiyle ~17 kat yavaş" tablosu **kötümser bir üst
sınırdır**. Şok fazında ağaç seyrek yenilenebilir; ejekta/geç fazda ise
yerçekimi belirleyicidir (kaçış hızı 8,37 cm/s) ama orada uçan parçacık
sayısı ve zaman ölçeği farklıdır. FAZ 4 bu ayrımı kullanacak.

## Özet

| Soru | Cevap |
|---|---|
| Motor DART ölçeğine çıkabiliyor mu? | **Evet** — 11,2 M parçacık ölçüldü, doğrusal, bellek bol |
| Fizik hedefe uygun mu? | **Evet**, zayıf/gözenekli hedef için standart set — hasar hariç |
| Ensemble maliyeti karşılanabilir mi? | **1 s koşularla evet** (~30 GPU-günü); 10 s'de sınırda |
| Yapılan doğrulama işi anlamlı mı? | **Evet** — hata posteriora taşınır; kalibrasyon zorunlu |
| Yerçekimi maliyeti engel mi? | **Hayır** (ADR-0024) — şok fazında ihmal edilebilir; ağaç seyrek yenilenebilir |
| Sahne kurulabiliyor mu? | **Evet** — G3 KISMİ geçti; şekil, yığın, mermi, gözlenebilirler hazır |
| Eksik ne var? | Hasar modeli; uzun koşu kararlılığı; gereken simüle süre; **gerçek PDS şekil modeli** (G3 C7 KANITLANAMADI) |
