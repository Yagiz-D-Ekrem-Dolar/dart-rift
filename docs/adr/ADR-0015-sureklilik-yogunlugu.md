# ADR-0015: Serbest yüzeyli katı senaryolarında yoğunluk süreklilik denklemiyle taşınır

- **Durum:** Kabul edildi
- **Tarih:** 2026-07-28
- **Bağlam:** FAZ 2, P2-VR-02 (Taylor bar), G2 kapısı C2 ölçütü
- **İlgili:** [ADR-0007](ADR-0007-kdk-trapez-enerji.md), [ADR-0009](ADR-0009-kernel-gradyan-duzeltmesi.md), [ADR-0012](ADR-0012-plastik-is-cifte-sayim.md), [ADR-0014](ADR-0014-artificial-stress.md)

## Sorun

Taylor bar enerji defteri, ardışık üç düzeltmeden sonra bile kapanmıyordu:

| Aşama | Enerji hatası |
|---|---|
| Plastik iş çift sayımı + donmuş duvar düzeltilmeden | %288–576 |
| ADR-0012 + simetrik kurulum sonrası | %15,71 |
| ADR-0014 (yapay gerilme) sonrası | %13,95 |
| Eşik | **%1,5** |

Yapay gerilme hatayı yalnızca 1,76 puan düşürdü. Bu, semptomun bastırıldığını
ama kök nedenin yerinde durduğunu gösteriyordu.

## Kök neden

Başlangıç durumu, **hiçbir dinamik çalışmadan** (yalnızca alan
değerlendirmesi, t=0) incelendiğinde:

```
rho: 3382 .. 8933 kg/m3   (rho/rho0: 0.379 .. 1.000)
P  : -8.697e10 .. +4.168e7 Pa
P<0 olan parçacık: 2526 / 2590  (%97,5)
en negatif P / K = -0.621
yüzey bölgesi (rad > R-2h): 2590 parçacık
iç bölge:                      0 parçacık
```

Parçacıkların %97,5'i daha ilk adımdan önce çekme altındaydı ve en büyük
çekme, hacim modülünün %62'siydi. Çubukta **tek bir iç parçacık bile yoktu**:
her parçacık serbest yüzeye 2h'den yakındı.

İlk hipotez "çözünürlük yetersiz" idi. Çözünürlük taraması bunu çürüttü:

| nx | N | 2h/r_cyl | rho_min/rho0 | P_min/K | P<0 |
|---|---|---|---|---|---|
| 7 | 2 590 | 1,143 | 0,379 | −0,621 | %97,5 |
| 12 | 13 664 | 0,667 | 0,390 | −0,610 | %79,6 |
| 16 | 33 696 | 0,500 | 0,391 | −0,609 | %63,0 |
| 20 | 63 832 | 0,400 | 0,390 | −0,610 | %54,6 |

Etkilenen parçacıkların **oranı** azalıyor, ama yüzeydeki yoğunluk açığının
**büyüklüğü** (0,39 rho0) ve ürettiği çekme (−0,61 K) sabit kalıyor. Bu,
serbest yüzeyde kernel desteğinin yarısının boş kalmasından doğan bir
toplama (summation) artefaktıdır ve tanımı gereği çözünürlükle geçmez.

Lineer EOS'ta `P = c0^2 (rho - rho0)` olduğundan, geometrik bir eksiklik
doğrudan −87 GPa'lık fiziksel olmayan bir çekmeye çevriliyordu.

## Karar

`MaterialParams.density_method` alanı eklendi:

- `"summation"` (varsayılan): `rho = sum_j m_j W_ij`. Akışkan/şok
  senaryoları (FAZ 1) bu formu kullanmaya devam eder; Sod ve Sedov'da serbest
  yüzey yoktur ve toplama formu kesin korunum sağlar.
- `"continuity"`: `rho` bir **durum değişkenidir**. Malzeme yoğunluğundan
  başlar ve `drho/dt = -rho div v` ile, `u` ve `S` ile aynı tam-trapez
  şemasında (ADR-0007) ilerletilir. Serbest yüzeyde eksiklik oluşmaz, çünkü
  `rho` hiçbir zaman komşu toplamından okunmaz.

Serbest yüzeyli katı senaryoları (Taylor bar) `"continuity"` kullanır.

Bu, P1-FR-02'nin "yoğunluk hem toplama hem süreklilik denklemiyle hesaplanır"
maddesiyle uyumludur; `drho/dt` her iki modda da üretilir, yalnızca
`"continuity"` modunda `rho`'yu ilerletir.

## Sonuç

nx=7, v=200 m/s, Y0=400 MPa:

| Yoğunluk | Yapay gerilme | L/L0 | Mantar | Enerji hatası |
|---|---|---|---|---|
| summation | kapalı | 0,5663 | 1,420 | %15,710 |
| summation | açık | 0,5822 | 1,396 | %13,953 |
| continuity | kapalı | 0,7079 | 1,519 | **%0,096** |
| continuity | açık | 0,7078 | 1,506 | **%0,094** |

Enerji hatası %13,95'ten %0,096'ya düştü — eşiğin 15 kat altında.

Bağımsız bir doğrulama: L/L0 = 0,708, Taylor testinin bakır için literatürde
bildirdiği ~0,70 bandının içindedir. Eski 0,566 değeri bandın dışındaydı,
yani yapay çekme yalnızca enerji defterini değil **deformasyonun kendisini**
de bozuyormuş. Enerji ölçütü ile şekil ölçütü aynı düzeltmeyle birlikte
sağlanıyor; bu, düzeltmenin eşiğe uydurma değil fiziksel olduğunun kanıtıdır.

Yapay gerilmenin katkısı artık %0,096 → %0,094, yani ölçüm gürültüsü
düzeyinde. ADR-0014 geri alınmadı (gerçek çekme kararsızlığına karşı koruma
olarak açık kalıyor) ama **yükü taşıyan modül olmadığı** kayda geçirildi.
`test_taylor_bar.py` içindeki ablasyon testi buna göre değiştirildi: artık
yapay gerilmeyi değil yoğunluk formunu sınıyor.

## Uygulama sırasında yakalanan hata: hızın dondurulması

İlk GPU uygulaması `rho`'yu tekme anında `rho - dt*rho*divv` ile ilerletiyordu.
Bu yanlıştı: ikinci yarım tekmede `rho` artık güncellenmiş olduğundan, CPU
referansının donmuş `drhodt`'sinden `dt*divv` (~1e-5) mertebesinde **sistematik**
olarak ayrılıyordu.

Çapraz kontrol bunu yakaladı. Ayırt edici ölçüm, farkın kaynağını kesinleştirdi:

| Karşılaştırma | 200 adım sonra Δrho/rho0 |
|---|---|
| t=0'da parçacık başına divv (CPU ref ↔ GPU) | medyan 1,78e-16 (ayrıklaştırmalar aynı) |
| Aynı çekirdekler, iki cihaz (salt toplama sırası) | 1,59e-13 |
| CPU ref ↔ GPU, hız tekmede hesaplanıyor | **3,56e-8** |
| CPU ref ↔ GPU, hız değerlendirmede donduruluyor | **3,37e-16** |

Alan değerlendirmesi makine hassasiyetinde uyuşuyordu; fark tamamen zaman
adımındaydı. Toplama sırası etkisinin 10⁵ katı bir sapma, "yuvarlama hatası"
açıklamasını çürütüyordu.

Düzeltme: `continuity_rate_3d` yalnızca `drhodt`'yi yazar, `rho`'yu ilerletmez;
tekmeler `u` ve `S` ile **aynı** `accumulate_scalar_3d` yolunu kullanır. Böylece
üç durum değişkeni de yapısal olarak tek bir trapez şemasından geçer.

## Alternatifler

- **Çözünürlüğü artırmak** — yukarıdaki tarama çürüttü; artefaktın büyüklüğü
  değişmiyor. Ayrıca nx=20 maliyeti 25 kata çıkarıyordu.
- **Çekme kesme (`P = max(P, 0)`)** — kohezyonsuz moloz yığını için fiziksel,
  ama bakır çubuk gerçek çekme taşır; testi geçirir, fiziği bozardı.
- **Yalnızca yapay gerilmeyi güçlendirmek** — semptom bastırma; eps'i
  büyütmek gerçek çekme dayanımını da siler.

## Doğrulama

- `tests/test_taylor_bar.py::test_summation_density_produces_spurious_tension_at_t0`
  — kök nedeni doğrudan sabitler (t=0'da `P_min < -0,5 K`, sürekliliğinse ~0).
- `tests/test_taylor_bar.py::test_continuity_density_closes_ledger_summation_does_not`
  — ablasyon: summation > %5, continuity < %1,5.
- `tests/test_solid_cross.py::TestContinuityDensityCross` — yeni ayrıklaştırma
  yolu için CPU referansı ↔ GPU çekirdeği çapraz kontrolü (< 1e-8), ayrıca
  `rho`'nun gerçekten evrildiğini doğrulayan boşluk kontrolü.
- FAZ 1 senaryoları etkilenmez: varsayılan `"summation"`.
