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

## 5. FAZ 3'ün ölçmesi gerekenler

Bu belgedeki hiçbir sayı FAZ 3'ün yerini tutmaz. Ölçülmemiş üç şey:

1. **Uzun koşu kararlılığı.** Tüm kapı senaryoları ≤ 262 144 parçacık ve
   birkaç yüz adımdır. Bir DART koşusu ~10⁴–10⁵ adımdır. ADR-0020 enerji
   hatasının `O(dt)` olduğunu gösterdi, ama bu 10⁵ adımda ne birikir —
   ölçülmedi.
2. **Gereken simüle süre.** Momentum aktarımının (β) ne zaman durulduğu
   koşunun maliyetini 10 kat değiştirir.
3. **Çözünürlük yakınsaması DART kurulumunda.** Krater çapı ve β'nın
   parçacık sayısına duyarlılığı ayrıca gösterilmelidir.

## Özet

| Soru | Cevap |
|---|---|
| Motor DART ölçeğine çıkabiliyor mu? | **Evet** — 11,2 M parçacık ölçüldü, doğrusal, bellek bol |
| Fizik hedefe uygun mu? | **Evet**, zayıf/gözenekli hedef için standart set — hasar hariç |
| Ensemble maliyeti karşılanabilir mi? | **1 s koşularla evet** (~30 GPU-günü); 10 s'de sınırda |
| Yapılan doğrulama işi anlamlı mı? | **Evet** — hata posteriora taşınır; kalibrasyon zorunlu |
| Eksik ne var? | Hasar modeli; uzun koşu kararlılığı; gereken simüle sürenin ölçümü |
