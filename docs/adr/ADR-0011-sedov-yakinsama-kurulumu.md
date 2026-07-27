# ADR-0011 — Sedov testinde enjeksiyon ölçeği sabit fiziksel uzunluktur

- **Durum:** Kabul edildi (kilitli)
- **Tarih:** 2026-07-27
- **İlgili gereksinim:** P1-VR-05, P1-VR-06; DR-RIFT-P1 §6.2

## Bağlam
Sedov-Taylor patlaması testinde şok yarıçapı hatası, çözünürlük artırıldıkça
**küçülmek yerine büyüyordu**. Ölçüm (TRUBA kolyoz10 / H100, job 1425864;
yerel RTX 3050'de birebir aynı):

| n_side | N | yoğunluk tepesi | dış yamaç gradyanı |
|--------|---|-----------------|--------------------|
| 32 | 32 768 | %9,6 | %0,2 |
| 48 | 110 592 | %15,0 | %3,3 |
| 64 | 262 144 | %15,0 | %10,5 |
| 80 | 512 000 | %16,8 | %14,1 |

Motorun sağlıklı olduğuna dair kanıtlar aynı koşulardan geliyordu: `t_end`'e
her koşuda tam ulaşıldı, kütle bit düzeyinde ve momentum ~1e-15 korundu,
enerji hatası %0,4'te kaldı. Yani sorun kararsızlık ya da enerji sızıntısı
değildi.

## Kök neden
Enerji enjeksiyon yarıçapı düzgünleştirme uzunluğuna bağlanmıştı
(`h_inj = 2h`), `h` de kafes aralığıyla ölçekleniyordu (`h = 1.25·dx`).
Sonuç: her çözünürlük **farklı bir başlangıç koşulu** kuruyordu —

| n_side | enjeksiyon destek yarıçapı |
|--------|---------------------------|
| 32 | 0,156 (şok yarıçapının %62'si) |
| 64 | 0,078 (%31) |
| 80 | 0,062 (%25) |

Bunlar farklı fiziksel problemlerdir. Yakınsama testi ise tanımı gereği
**aynı problemin** farklı çözünürlüklerde çözülmesini gerektirir. Ölçtüğümüz
şey sayısal yakınsama değil, başlangıç koşulunun değişmesiydi.

Düşük çözünürlükteki "iyi" sonuç (%0,2) bu yüzden bir başarı değil, rastlantıydı:
geniş enjeksiyon bölgesi şoku hızlandırıyor ve ölçüm hatasını tesadüfen
kapatıyordu.

## Karar
1. **Enjeksiyon ölçeği sabit fiziksel uzunluktur:** `H_INJECT = 0.04`
   (destek yarıçapı 0,08). En kaba kafeste (n=32, h=0,039) kernel desteği
   kadar, en incede (n=80) ~3h genişliğindedir; her çözünürlük aynı başlangıç
   koşulunu görür.
2. **Koşu süresi**, şok yarıçapı domain yarı-genişliğinin yarısına ulaştığında
   biter (`t_end = 0.0288` → r_s ≈ 0,25). Önceki `t = 0.06`'da (r_s = 0,335,
   yarı-genişliğin %67'si) cephe kübün yüzüne yaklaşıyordu.
3. **Kısmi koşu sessizce geçerli sayılmaz:** adım bütçesi biterse
   `run_sedov_warp` açık hata verir. Erken biten bir koşu sistematik olarak
   küçük yarıçap ölçer ve tam da "çözünürlükle kötüleşen hata" gibi görünür.
4. **Kinetik enerji oranı raporlanır** (Sedov benzerlik çözümünde γ=1,4 için
   ≈0,28): enerjinin gerçekten şoka gidip gitmediğinin, şok yarıçapından
   bağımsız ikinci göstergesi.

## Sonuçlar
- (+) Yakınsama merdiveni artık anlamlı: aynı problem, farklı çözünürlük.
- (+) Erken biten koşu artık sessiz bir yanlış sonuç üretemez.
- (−) Enjeksiyon bölgesi en kaba kafeste kernel desteği kadar; n < 32
  çözünürlükler bu testte kullanılamaz (`build_sedov_ic` boş enjeksiyon
  bölgesinde açık hata verir).

## Ders (yöntemsel)
"Çözünürlük artınca hata büyüyor" bulgusunun ilk yorumu *motor bozuk* oldu.
Korunum tanıları ise motorun sağlam olduğunu söylüyordu. Çelişkiyi çözen soru
şuydu: **her çözünürlükte aynı problemi mi çözüyorum?** Yakınsama testlerinde
başlangıç koşulunun çözünürlükten bağımsız olduğunu doğrulamak, testin kendi
ön koşuludur.

## İlgili testler
`tests/test_sedov.py`, `scripts/run_g1_gate.py` (C5 kriteri)
