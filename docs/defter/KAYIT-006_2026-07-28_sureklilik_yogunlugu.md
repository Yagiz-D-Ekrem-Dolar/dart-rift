```
TÜBİTAK 2204 PROJESİ
MÜHENDİSLİK DEFTERİ — GÜNLÜK ÇALIŞMA KAYDI

Proje Adı   : DART-RIFT
Takım       : kayıt bulunamadı
Danışman    : kayıt bulunamadı
```

============================================================
GÜNLÜK KAYIT NO: 006
============================================================

**Tarih**       : 28.07.2026
**Saat**        : 02:30 – 06:10 UTC+3
**Çalışanlar**  : Yağız Ekrem Dalar (`egitimg16u4`)
**Çalışma Yeri**: Çevrim içi — yerel makine (RTX 3050)

## BUGÜNKÜ HEDEF

KAYIT-005'te açık kalan tek eşik: Taylor bar enerji defteri. Yapay gerilme
(ADR-0014) eklendikten sonra bile %13,95 idi; eşik %1,5.

## BULGU 1 — Kök neden başlangıç durumundaydı, dinamikte değil

Hiçbir zaman adımı atılmadan, yalnızca alan değerlendirmesi yapılarak t=0
durumu incelendi:

| Büyüklük | Değer |
|---|---|
| rho/rho0 aralığı | 0,379 – 1,000 |
| P aralığı | −8,697e10 … +4,168e7 Pa |
| P < 0 olan parçacık | 2526 / 2590 (%97,5) |
| en negatif P / K | −0,621 |
| yüzey bölgesi (rad > R−2h) | 2590 parçacık |
| **iç bölge** | **0 parçacık** |

Çubukta tek bir iç parçacık bile yoktu: `nx=7`, `h/dx=2` ile kernel desteği
(4dx) çubuk çapını (7dx) aşıyordu. Parçacıkların %97,5'i daha ilk adımdan
önce, hacim modülünün %62'sine varan yapay çekme altındaydı.

## BULGU 2 — "Çözünürlüğü artır" hipotezi yanlıştı

İlk akla gelen çözüm denendi ve **çürütüldü**:

| nx | N | 2h/r_cyl | rho_min/rho0 | P_min/K | P<0 |
|---|---|---|---|---|---|
| 7 | 2 590 | 1,143 | 0,379 | −0,621 | %97,5 |
| 12 | 13 664 | 0,667 | 0,390 | −0,610 | %79,6 |
| 16 | 33 696 | 0,500 | 0,391 | −0,609 | %63,0 |
| 20 | 63 832 | 0,400 | 0,390 | −0,610 | %54,6 |

Etkilenen parçacıkların oranı düşüyor, ama açığın **büyüklüğü** (0,39 rho0) ve
ürettiği çekme (−0,61 K) hiç değişmiyor. Bu, serbest yüzeyde kernel desteğinin
yarısının boş kalmasından doğan bir toplama (summation) artefaktıdır; tanımı
gereği çözünürlükle geçmez. nx=20'ye çıkmak maliyeti 25 kat artırıp sorunu
çözmeyecekti.

## BULGU 3 — Çözüm: süreklilik denklemi (ADR-0015)

Yoğunluk, serbest yüzeyli katı senaryolarında bir **durum değişkeni** yapıldı:
malzeme yoğunluğundan başlar, `drho/dt = -rho div v` ile u ve S ile aynı
trapez şemasında ilerletilir. Komşu toplamından hiç okunmadığı için yüzeyde
eksiklik oluşmaz. Şartname P1-FR-02 zaten her iki formu da öngörüyordu.

Ablasyon (nx=7, v=200 m/s, Y0=400 MPa):

| Yoğunluk | Yapay gerilme | L/L0 | Mantar | Enerji hatası |
|---|---|---|---|---|
| summation | kapalı | 0,5663 | 1,420 | %15,710 |
| summation | açık | 0,5822 | 1,396 | %13,953 |
| continuity | kapalı | 0,7079 | 1,519 | **%0,096** |
| continuity | açık | 0,7078 | 1,506 | **%0,094** |

Enerji hatası eşiğin 15 katı altına indi. Bağımsız doğrulama: L/L0 = 0,708,
Taylor testinin bakır için literatürde bildirdiği ~0,70 bandının içinde. Eski
0,566 bandın dışındaydı — yani yapay çekme yalnızca enerji defterini değil
**deformasyonun kendisini** de bozuyormuş. İki ayrı ölçütün aynı düzeltmeyle
birlikte sağlanması, bunun eşiğe uydurma değil fiziksel bir düzeltme olduğunu
gösteriyor.

Yapay gerilmenin katkısı artık %0,096 → %0,094, yani gürültü düzeyinde.
ADR-0014 geri alınmadı (gerçek çekme kararsızlığına karşı koruma olarak açık),
ama yükü taşıyan modülün o olmadığı kayda geçirildi ve ablasyon testi yoğunluk
formunu sınayacak şekilde değiştirildi.

## BULGU 4 — Çapraz kontrol, yeni yolda gerçek bir hata yakaladı

Süreklilik için CPU referansı ↔ GPU çapraz kontrolü eklendi ve **başarısız**
oldu: P'de 5,66e-6 sapma. Sapmanın kaynağını ayırt etmek için üç ölçüm yapıldı:

| Karşılaştırma | 200 adım sonra Δrho/rho0 |
|---|---|
| t=0'da parçacık başına divv farkı | medyan 1,78e-16 → ayrıklaştırmalar aynı |
| Aynı çekirdekler, iki cihaz (salt toplama sırası) | 1,59e-13 |
| CPU ref ↔ GPU | **3,56e-8** (10⁵ kat fazla) |

Alan değerlendirmesi makine hassasiyetinde uyuşuyordu, yani sorun zaman
adımındaydı. Nedeni bulundu: GPU, `rho`'yu tekme anında `rho - dt*rho*divv`
ile ilerletiyordu; ikinci yarım tekmede `rho` güncellenmiş olduğu için CPU'nun
donmuş `drhodt`'sinden `dt*divv` (~1e-5) mertebesinde **sistematik** olarak
ayrılıyordu. Ölçülen sabit 6,3e-6'lık oran bu tahminle uyuştu.

Düzeltme: hız artık değerlendirmede dondurulup `u` ve `S` ile aynı
`accumulate_scalar_3d` yolundan uygulanıyor. Sapma **3,56e-8 → 3,37e-16**
(150 adım boyunca tam sıfır).

Not: Bu hata yalnızca çapraz kontrol sayesinde görüldü. Taylor sonucu (%0,096)
hata varken de "başarılı" görünüyordu — tek bir yeşil ölçüt, altındaki
ayrıklaştırmanın doğru olduğunu göstermiyor.

## BULGU 5 — TRUBA G1 koşusu (1426017): yerelde yeşil, kümede kırmızı

Kolyoz14/H100 üzerinde koşan G1 kapısı **geçemedi**. Rapor satırı ilk bakışta
anlamsızdı:

```
| C1 | Kutle korunumu ~makine hassasiyeti | **KALDI** | maks kutle sapmasi 0.00e+00 |
```

Sapma tam sıfırken ölçüt nasıl düşer? Çünkü C1'in şartı `tests_ok and
mass_max < 1e-12` idi ve düşen kısım `tests_ok`'tu. Aynı nedenle C6 da düştü.
Kanıt metni bunu söylemiyordu — **rapor yanıltıcıydı** ve düzeltildi: artık
pytest kaldıysa bunu açıkça yazıyor.

Asıl neden, paketteki 3 hatadan ikisi:

```
FAILED tests/test_kernel_fn.py::TestNormalization::test_3d_integral_is_one
FAILED tests/test_kernel_fn.py::TestNormalization::test_1d_integral_is_one
FAILED tests/test_taylor_bar.py::TestTaylorBar::test_energy_ledger_closes
```

Üçüncüsü zaten bilinen Taylor sorunuydu (bu kayıtta çözüldü). İlk ikisi ise
yeni: `np.trapz` bir kullanım dışı bırakma uyarısı verdiği için `np.trapezoid`
yapılmıştı, ama `np.trapezoid` NumPy 2.0 ile geldi. Ortamlar ölçüldü:

| | TRUBA (hedef) | yerel |
|---|---|---|
| Python | 3.10.15 | 3.12 |
| NumPy | **1.26.4** | 2.x |
| `np.trapezoid` | **yok** | var |

Yani bir uyarıyı susturmak için yapılan değişiklik, kodu hedef kümede
kırmıştı. Sürümden bağımsız köprü yazıldı ve kısıt ADR-0005'e eklendi. Tarama
yapıldı: NumPy 2'ye özgü başka API kullanılmıyor.

Bu olay kapı mekanizmasının **amaçlandığı gibi çalıştığını** gösteriyor:
yerelde yeşil olan paket hedef ortamda yeşil demek değildir; kanıt bu yüzden
TRUBA'da üretiliyor.

## YARIN

- Düzeltilmiş commit ile G1 + G2 kapılarını TRUBA'da yeniden koşmak.
