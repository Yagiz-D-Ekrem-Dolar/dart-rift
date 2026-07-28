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

   > **Düzeltme (29.07.2026):** Bu madde iki faz boyunca **uygulanmadı** —
   > `kinetic_fraction` hesaplanıyordu ama kapı raporuna hiç girmiyordu, yani
   > "raporlanır" iddiası doğru değildi. Denetimde yakalandı ve G1 C5 kanıt
   > metnine eklendi.
   >
   > Ayrıca beklenen değer düzeltildi: bu kurulumda hedef **0,28 değil ~0,19**.
   > Ölçülen (n = 32…112): 0,224 / 0,191 / 0,182 / 0,200 / 0,189 / 0,187.
   > Sebep aynı model-form seçimi: enerji noktasal değil, şok yarıçapının
   > ~%32'si kadar bir bölgeye ısı olarak konuyor; iç bölge sıcak kalıyor ve o
   > pay kinetiğe dönüşmüyor. 0,28 hedefi **nokta** patlaması içindir ve bu
   > kuruluma uygulanamaz. Eşik konmaz, sayı raporlanır.

## Sonuçlar
- (+) Yakınsama merdiveni artık anlamlı: aynı problem, farklı çözünürlük.
- (+) Erken biten koşu artık sessiz bir yanlış sonuç üretemez.
- (−) Enjeksiyon bölgesi en kaba kafeste kernel desteği kadar; n < 32
  çözünürlükler bu testte kullanılamaz (`build_sedov_ic` boş enjeksiyon
  bölgesinde açık hata verir).

## SONRAKİ ÖLÇÜM (28.07.2026, TRUBA kolyoz19, iş 1427240)

Merdiven n=112'ye kadar uzatıldı. İki bulgu, bu ADR'nin kapsamını netleştiriyor.

| n_side | r_ölçülen | şok yarıçapı hatası | enerji hatası | adım |
|---|---|---|---|---|
| 32 | 0,2528 | %1,15 | %0,351 | 135 |
| 48 | 0,2434 | %2,62 | %0,418 | 221 |
| 64 | 0,2387 | **%4,46** | %0,432 | 287 |
| 80 | 0,2398 | %4,03 | %0,480 | 345 |
| 96 | 0,2400 | %3,95 | **%0,510** | 407 |
| 112 | 0,2401 | %3,91 | **%0,534** | 464 |

**1. Şok yarıçapı yakınsıyor, ama sıfıra değil.** Ölçülen yarıçap
0,2400–0,2401'e oturuyor; hata **~%3,9'luk bir tabana** iniyor. Bu bir
ayrıklaştırma hatası değil, bu ADR'nin bilinçli olarak seçtiği kurulumun
**model-form hatasıdır**: enerji noktasal değil, sonlu bir yarıçapa
(`r_inj = 0,08`, şok yarıçapının %32'si) enjekte ediliyor; analitik çözüm ise
nokta patlaması varsayar. Yani %3,9 beklenen ve anlaşılmış bir sapmadır.

Düşük çözünürlükteki "iyi" değerler (n=32'de %1,15) yine bu ADR'nin
başında tarif edilen rastlantıdır — sayısal yayınım sapmayı tesadüfen
kapatıyor.

Not: G1 kapısı C5'i **n=64**'te ölçüyor ve bu merdivenin **en kötü**
noktasıdır (%4,46; eşiğe 0,54 puan). n≥96'da hata %3,9'a oturduğu için marj
aslında iki katına çıkıyor. Kapı çözünürlüğü bu ADR'de değiştirilmedi
(maliyet/kanıt dengesi ayrı bir karardır), ancak seçimin merdivenin en kötü
noktası olduğu artık kayıtlıdır.

**2. Enerji hatası çözünürlükle BÜYÜYOR ve n≥96'da C3 eşiğini aşıyor.**
%0,351 → %0,534; eşik %0,5. Adım sayısı 135'ten 464'e çıkıyor (3,44×) ve
hata 1,52× artıyor — yani adım başına değil, **birikimli** bir integrasyon
hatası ve adım sayısından daha yavaş büyüyor.

G1 kapısı merdiveni n=64'te bitirdiği için bu eşik aşımı kapıda görünmüyor.
Bu bir **bilinen sınırlamadır** ve şöyle kayda geçirilir: mevcut KDK+trapez
şeması (ADR-0007) ile %0,5'lik enerji bütçesi, ~300 adımı aşan Sedov
koşularında tutmuyor. FAZ 3'te daha uzun koşular gerekeceği için bu, orada
çözülmesi gereken açık bir maddedir. Kapı ölçütü **gevşetilmedi**; kapsam
(n≤64) olduğu gibi bırakıldı ve sınırlama burada açıkça yazıldı.

## Ders (yöntemsel)
"Çözünürlük artınca hata büyüyor" bulgusunun ilk yorumu *motor bozuk* oldu.
Korunum tanıları ise motorun sağlam olduğunu söylüyordu. Çelişkiyi çözen soru
şuydu: **her çözünürlükte aynı problemi mi çözüyorum?** Yakınsama testlerinde
başlangıç koşulunun çözünürlükten bağımsız olduğunu doğrulamak, testin kendi
ön koşuludur.

## İlgili testler
`tests/test_sedov.py`, `scripts/run_g1_gate.py` (C5 kriteri)
