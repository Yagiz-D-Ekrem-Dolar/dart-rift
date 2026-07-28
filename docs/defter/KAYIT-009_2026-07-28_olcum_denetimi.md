```
TÜBİTAK 2204 PROJESİ
MÜHENDİSLİK DEFTERİ — GÜNLÜK ÇALIŞMA KAYDI

Proje Adı   : DART-RIFT
Takım       : kayıt bulunamadı
Danışman    : kayıt bulunamadı
```

============================================================
GÜNLÜK KAYIT NO: 009
============================================================

**Tarih**       : 28.07.2026
**Saat**        : 21:30 – 02:00 UTC+3
**Çalışanlar**  : Yağız Ekrem Dalar (`egitimg16u4`)
**Çalışma Yeri**: Yerel makine + TRUBA/ARF-ACC (kolyoz19)

## BUGÜNKÜ HEDEF

FAZ 3'e geçmeden önce fazları test etmeye devam etmek. Bu kez sorulan soru
"testler geçiyor mu" değil, **"testler geçtiklerinde ne kanıtlıyorlar"**.

## BULGU 1 — Kapsam ölçümü ölçemediği şeyi sayıyordu (ADR-0016)

CI birkaç koşudur kırmızıydı: G0 kapısı GPU'suz ortamda %81,6 ölçüp C1'i
düşürüyordu — kod doğru olduğu hâlde. GPU'lu ölçümde ise oran %85,1'di,
eşiğin (%85) 0,1 puan üstü. Bu kadar dar bir marj ölçünün anlamsız olduğuna
işaretti.

Kök neden: **coverage.py, Warp çekirdek gövdelerini ölçemez.** Ölçüm dosyası
üzerinde doğrudan gösterildi — `density_3d` projenin en çok çalışan
çekirdeğidir (her SPH adımında çağrılır), yine de gövdesinin her satırı
"eksik" görünüyordu; yalnızca dekoratör satırı "çalıştı" sayılıyordu (import
anında).

Üç seçenek ölçüldü:

| Seçenek | Kapsam | Ölçülen satır |
|---|---|---|
| Her şey dahil (eski kapı ölçümü) | %85,1 | 3214 — 412'si ölçülemeyen gövde |
| `warp_core/` tamamen hariç | %97,8 | 2145 |
| **Yalnızca çekirdek gövdeleri hariç** | **%97,6** | **2802** |

Seçilen yöntem 657 satır daha fazla kod ölçüyor ve ölçülemeyen hiçbir şeyi
orana katmıyor. GPU'suz marj 0,1 puandan **8,5 puana** çıktı (%93,5).

Yan bulgu: eski `.coveragerc-ci`'deki "Kapı → tüm kodun (GPU dahil) ≥ %85'i"
ifadesi **yanlıştı**. Ölçülemeyen bir şey için eşik koymak, ölçüyormuş gibi
görünmekten başka işe yaramıyordu.

## BULGU 2 — Elastik dalga ölçümü yanlış tepeyi seçebiliyordu

Elastik dalga hatası eşiğe çok yakındı (%2,96 vs %3). "Sistematik bir tabana
mı yakınsıyor?" sorusunu yanıtlamak için merdiven aşağı doğru uzatıldı ve
res=150'de şu çıktı:

```
res=150 -> ölçülen hız -1854.4 m/s, hata %140
```

**Negatif hız.** Nedeni fizik: gerinimsiz bir hız darbesi d'Alembert'e göre
eşit genlikli iki dalgaya ayrılır — `v = ½f(x−ct) + ½f(x+ct)`. İki tepe de
pozitif ve büyüklükleri **eşit**; dolayısıyla tüm dizi üzerinde `argmax`
hangisini seçeceği yazı-turadır. res=150'de sola gideni seçmişti.

Kapı çözünürlüklerinde doğru tepe seçildiği için sorun görünmüyordu — ama bu
bir tesadüf, garanti değil. Arama artık `x > x_c0` ile sınırlı.

Düzeltmeden sonra merdiven monoton:

| res | hata | oran |
|---|---|---|
| 150 | %9,24 | — |
| 300 | %5,49 | 1,68 |
| 400 | %4,32 | 1,27 |
| 600 | %2,96 | 1,46 |

Yaklaşık birinci mertebe. Yani hata **sistematik bir tabana değil sıfıra**
yakınsıyor; %2,96 salt ayrıklaştırma hatasıdır ve çözünürlükle iyileşir.

## BULGU 3 — Sedov: yarıçap bir tabana yakınsıyor, enerji eşiği aşıyor

Sedov merdiveni n=112'ye uzatıldı (TRUBA kolyoz19, iş 1427240):

| n | r_ölçülen | şok hatası | enerji hatası | adım |
|---|---|---|---|---|
| 32 | 0,2528 | %1,15 | %0,351 | 135 |
| 64 | 0,2387 | **%4,46** | %0,432 | 287 |
| 80 | 0,2398 | %4,03 | %0,480 | 345 |
| 96 | 0,2400 | %3,95 | **%0,510** | 407 |
| 112 | 0,2401 | %3,91 | **%0,534** | 464 |

**(a)** Şok yarıçapı 0,2400'e yakınsıyor; hata ~%3,9'luk bir **tabana**
iniyor. Bu ayrıklaştırma hatası değil, ADR-0011'in bilinçle seçtiği sonlu
enjeksiyon yarıçapının (r_inj = 0,08 = şok yarıçapının %32'si) model-form
hatasıdır. Beklenen ve anlaşılmış bir sapma.

G1 kapısı C5'i **n=64**'te ölçüyor — merdivenin **en kötü** noktası (%4,46,
eşiğe 0,54 puan). n≥96'da marj iki katına çıkıyor.

**(b)** Enerji hatası çözünürlükle **büyüyor** ve n≥96'da C3 eşiğini (%0,5)
**aşıyor**. Adım sayısı 3,44× artarken hata 1,52× artıyor — birikimli bir
integrasyon hatası. Kapı merdiveni n=64'te bitirdiği için bu görünmüyordu.

Bu bir **bilinen sınırlama** olarak kaydedildi: mevcut KDK+trapez şemasıyla
(ADR-0007) %0,5'lik enerji bütçesi ~300 adımı aşan Sedov koşularında
tutmuyor. FAZ 3 daha uzun koşular gerektireceği için orada çözülmesi gereken
açık bir maddedir. **Kapı ölçütü gevşetilmedi**; kapsam olduğu gibi bırakıldı
ve sınırlama ADR-0011'e açıkça yazıldı.

## BULGU 4 — Düğüm-arızası korumaları tek betikte kalmış

Sedov işi düz `sbatch` ile gönderildi, arızalı bir düğüme düştü ve warp
import hatasıyla öldü. İnceleyince görüldü ki `faz12_gates.sh`'ye eklenen
dört koruma (arızalı düğüm dışlaması, stderr birleştirme, warp import
sağlığı, CUDA cihazı sağlığı) `faz0_g0_gate.sh`'de **yoktu**. Aynı arıza
modları orada da açıktı; dersler bir betiğe uygulanmış, diğerine değil.
İkisi eşitlendi.

## DEĞERLENDİRME

Dört bulgunun üçü aynı desende: **yeşil bir test, ölçtüğü şeyin doğru
olduğunu göstermez.** Kapsam ölçülemeyeni sayıyordu; elastik dalga yanlış
tepeyi seçebiliyordu; Sedov'un "geçen" değeri merdivenin en kötü noktasıydı
ve komşusunda eşik aşılıyordu.

Hiçbiri testleri kırmızıya çevirmemişti. Bulunmalarının tek yolu, geçen bir
ölçüme "bu sayı neyi kanıtlıyor?" diye sormaktı.

## SIRADA

- Enerji bütçesinin uzun koşularda tutmaması (FAZ 3 önkoşulu).
- FAZ 3'e geçiş kararı.

> **KAPANIŞ NOTU (29.07.2026):** Yukarıdaki "enerji bütçesi tutmuyor" maddesi
> **çözüldü ve bir kusur olmadığı anlaşıldı**. Sabit çözünürlükte yalnızca CFL
> değiştirilerek ölçüldü: dt yarılanınca hata tam yarıya iniyor (2,06 ve
> 2,07). Yani `O(dt¹)` **kesme hatası**, yapısal sızıntı değil. Aynı taramada
> şok yarıçapı hatası sabit kaldığı için iki hata kaynağı da birbirinden
> ayrıldı. Ayrıntı: [ADR-0020](../adr/ADR-0020-enerji-hatasi-kesme-hatasidir.md).
> Bu kayıttaki BULGU 3(b) o zamanki bilgiyle doğruydu; kök neden sonradan
> bulundu ve burada düzeltiliyor.
