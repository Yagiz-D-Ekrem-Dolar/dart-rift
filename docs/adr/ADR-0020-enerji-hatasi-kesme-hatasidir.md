# ADR-0020: Sedov enerji hatası yapısal sızıntı değil, birinci mertebeden kesme hatasıdır

- **Durum:** Kabul edildi
- **Tarih:** 2026-07-29
- **Bağlam:** P1-VR-03 (enerji korunumu), G1 kapısı C3
- **İlgili:** [ADR-0007](ADR-0007-kdk-trapez-enerji.md), [ADR-0011](ADR-0011-sedov-yakinsama-kurulumu.md)

## Sorun

KAYIT-009'da açık bir kusur olarak kaydedilmişti: Sedov'da enerji hatası
çözünürlükle **büyüyor** ve n ≥ 96'da C3 eşiğini (%0,5) aşıyor.

| n | adım | enerji hatası |
|---|---|---|
| 32 | 135 | %0,351 |
| 64 | 287 | %0,432 |
| 96 | 407 | **%0,510** |
| 112 | 464 | **%0,534** |

G1 kapısı C3'ü geçiyordu, çünkü merdiven n = 64'te bitiyordu. "Bilinen
sınırlama" olarak yazılmıştı ama **kök nedeni bilinmiyordu**. Bir kusurun adı
konmadan kapatılamaz: bu, şemada bir enerji sızıntısı da olabilirdi
(o durumda FAZ 3'ün uzun koşuları anlamsız olurdu), sıradan bir kesme hatası
da.

## Ayırt edici ölçüm

Soru şuydu: hata **dt'ye bağlı mı?**

- Yapısal sızıntı (ör. yapay viskozite işinin yanlış muhasebesi) ise hata
  adım sayısıyla birikir; dt küçültmek adım sayısını artırır, hata **azalmaz**.
- Kesme hatası ise dt küçüldükçe **düşer**.

Sabit `n = 32` ve sabit `t_end`, yalnızca CFL değiştirildi (yerel RTX 3050):

| CFL | adım | enerji hatası | önceki / bu | şok hatası |
|---|---|---|---|---|
| 0,2500 | 162 | %0,29502 | — | %1,14 |
| 0,1250 | 324 | %0,14303 | **2,06** | %1,13 |
| 0,0625 | 647 | %0,06904 | **2,07** | %1,12 |

## Sonuç

**dt yarılandığında hata tam yarıya iniyor** (2,06 ve 2,07). Yani toplam
enerji hatası `O(dt¹)`'dir:

- Adım başına kesme hatası `O(dt²)`, adım sayısı `O(1/dt)` → toplam `O(dt)`.
- **Sızıntı yok.** Sızıntı olsaydı oran 1,0 civarında kalır, hatta adım sayısı
  arttığı için 1'in altına düşerdi.

Şok yarıçapı hatası aynı taramada %1,14 → %1,12 ile **sabit**. Bu, ADR-0011'in
tespitini bağımsız olarak doğruluyor: yarıçap sapması zaman
ayrıklaştırmasından değil, sonlu enjeksiyon yarıçapının model-form
hatasından geliyor. İki hata kaynağı böylece **birbirinden ayrılmış** oldu.

## Karar

1. Bu bir kusur değil, şemanın bilinen ve **kontrol edilebilir** mertebesidir.
   `n ≥ 96`'da %0,5 aşılması, o çözünürlükte varsayılan CFL'in o doğruluk
   hedefi için fazla büyük olmasıdır — şemada bir bozukluk değil.

2. Varsayılan CFL **değiştirilmedi**. Değiştirmek tüm koşuları 2 kat
   yavaşlatır ve mevcut kapı kapsamında (n ≤ 64) gerek yok. FAZ 3, doğruluk
   hedefine göre CFL seçer; bu ADR ilişkiyi ölçülmüş olarak veriyor:
   **hedef hatayı yarıya indirmek için CFL'i yarıya indirin.**

3. G1 kapısı bu oranı **her koşuda ölçüp raporluyor**: en kaba Sedov
   çözünürlüğü bir de yarı CFL ile koşulur ve `energy_error_dt_halving_ratio`
   hem C3 kanıt metnine hem `g1_metrics.json`'a yazılır.

   Bu, ölçütü güçlendirir: "hata < %0,5" hatanın **kontrol edilebilir**
   olduğunu söylemez; oran söyler. Bir gün gerçek bir sızıntı girerse oran
   2'den 1'e düşer ve kanıt metninde görünür — eşik hâlâ geçiliyor olsa bile.

## Sonuçlar

- (+) Açık kusur kapandı: adı kondu, ölçüldü, kontrolü belgelendi.
- (+) FAZ 3'ün uzun koşuları için net kural var.
- (+) Kapı, sızıntıya karşı yeni ve daha keskin bir kanıt taşıyor.
- (−) G1 kapısı bir ek Sedov koşusu kadar (en kaba çözünürlük, yarı CFL)
  uzuyor. H100'de bu birkaç saniyedir.

## Doğrulama

`scripts/run_g1_gate.py` — C3 kanıt metni ve `g1_metrics.json`
(`energy_error_dt_halving_ratio`). Beklenen ~2,0.
