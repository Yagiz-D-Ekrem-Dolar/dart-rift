# ADR-0013 — Wendland C2 için komşu sayısı: 3B'de h/dx = 2,0 (~268 komşu)

- **Durum:** Kabul edildi (kilitli)
- **Tarih:** 2026-07-28
- **İlgili gereksinim:** P1-FR-04, P1-VR-05; DR-RIFT-P1 §2.4, §2.6

## Bağlam
Şartname §2.4 çekirdek olarak Wendland C2'yi kilitler ("pairing kararsızlığını
azaltmak için"), §2.6 ise düzgünleştirme uzunluğu için sabit h zorunlu kılar
ama **h/dx oranını belirtmez**. İlk uygulamada 3B senaryolarda h/dx ≈ 1,25–1,3
kullanıldı — bu, kübik spline için alışılmış değerdir ve ~65–74 komşu verir.

Sedov testinde şok yarıçapı hatası bu değerle %15–16'da takılıydı ve
çözünürlükten bağımsızdı. Bağımsız gösterge de aynı yöne işaret ediyordu:
kinetik enerji oranı 0,12 ölçülüyordu, oysa γ=1,4 için Sedov benzerlik çözümü
0,28 verir — enerji şok cephesine geçmiyordu.

## Ölçüm
Aynı başlangıç koşulu, n = 48, yalnızca h/dx değiştirildi:

| h/dx | komşu ≈ (4/3)π(2h/dx)³ | şok yarıçapı hatası | KE/E (teorik 0,28) |
|------|------------------------|---------------------|--------------------|
| 1,25 | 65 | %15,8 | 0,121 |
| 1,60 | 137 | %6,5 | 0,161 |
| **2,00** | **268** | **%2,6** | **0,191** |

Yapay viskozite katsayıları (α=1,0/β=2,0 ile α=0,5/β=1,0) aynı taramada
denendi ve etkisi ikincil kaldı (%15,8 → %14,5): sorun sönüm fazlalığı değil,
**kernel toplamının yetersiz örneklenmesiydi**.

Bu, Dehnen & Aly (2012) ile uyumludur: Wendland çekirdekleri pairing
kararsızlığına dirençlidir, ancak bu direnç ancak **yüksek komşu sayısında**
işe yarar; 3B Wendland C2 için ~200 komşu önerilir. Kübik spline'ın ~50
komşuluk alışkanlığını Wendland'a taşımak, çekirdeği seçme gerekçesini
boşa çıkarıyordu.

## Karar
Tüm **3B** senaryolarda h/dx = 2,0 (destek 4dx, ~268 komşu):
`sedov.py`, `conservation.py`, `gravity.py`, `ablation.py`, `solids.py`
(Taylor ve rijit dönme). 1B senaryolarda (Sod, plate, elastik dalga) h/dx = 2,0
zaten kullanılıyordu; 1B'de bu ~8 komşuya karşılık gelir ve yeterlidir.

## Sonuçlar
- (+) Sedov hatası %15,8 → %2,6; P1-VR-05'in %5 eşiğinin altına indi.
- (+) KE/E 0,121 → 0,191; benzerlik çözümünün 0,28'ine yaklaştı (kalan fark
  sonlu enjeksiyon bölgesi ve cephe kalınlığından gelir, bkz. ADR-0011).
- (−) Komşu sayısı ~4× arttı → çift etkileşim maliyeti ~4×. FAZ 1'in ilkesi
  "önce doğruluk" olduğu için kabul edildi.
- Aynı yetersizlik Taylor bar ve öz-yerçekimi senaryolarında da mevcuttu;
  düzeltme oralara da uygulandı.

## Ders (yöntemsel)
Çekirdek seçimi tek başına bir karar değildir: **çekirdek + komşu sayısı**
birlikte bir karardır. Bir çekirdeği "pairing kararsızlığına dirençli olduğu
için" seçip, onu o direnci sağlamayan bir komşu sayısıyla çalıştırmak, kararın
gerekçesini geçersiz kılar. Şartname çekirdeği kilitlemiş ama komşu sayısını
belirtmemişti; bu boşluk varsayılan bir alışkanlıkla doldurulmuş ve hata
oradan girmişti.

## İlgili testler
`tests/test_sedov.py`, `tests/test_kernel_fn.py::TestPartitionOfUnity`,
`tests/test_taylor_bar.py`, `scripts/run_g1_gate.py` (C5)
