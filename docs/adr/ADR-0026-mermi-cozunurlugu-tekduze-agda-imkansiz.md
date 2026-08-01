# ADR-0026 — DART mermisi tekdüze çözünürlükte çözülemez: FAZ 4 yerel incelme gerektirir

- **Durum:** Kabul edildi
- **Tarih:** 2026-08-01
- **Bağlam:** FAZ 3 sonrası fizibilite denetimi; FAZ 4 tasarımını belirler
- **İlgili:** `docs/FIZIBILITE.md` §1–2 (**bir iddiası bu ADR ile düzeltiliyor**),
  ADR-0011 (enerji enjeksiyonu), P3-FR-06 (nokta parçacık yasağı)

## Nasıl bulundu

Uzun koşu kararlılığını ölçmek için bir çarpma senaryosu koştum. β hiç
değişmedi, sabit 1,0 kaldı. Sebebini aradığımda ölçüm şuydu:

**DART mermisinin küre eşdeğer yarıçapı 0,3714 m (çap 0,743 m).** Hedef
parçacık aralığı 12 m idi. Yani mermi, hedefin **tek bir parçacığından 16 kat
küçüktü** — hedefe hiç bağlanamıyordu.

## Ölçüm — Dimorphos ölçeğinde ne gerekiyor

Dimorphos hacmi (ikosfer, R = 82 m): 2,3046e+06 m³.
FCC'de parçacık başına hacim V_p = s³/√2.

| aralık s [m] | N_hedef | merminin çapı boyunca parçacık | bellek ~[GB] |
|---|---|---|---|
| 12,00 | 1,89e+03 | 0,06 | ~0 |
| 4,00 | 5,09e+04 | 0,19 | ~0 |
| 2,00 | 4,07e+05 | 0,37 | 0,2 |
| 1,00 | 3,26e+06 | 0,74 | 1,7 |
| **0,663** | **1,12e+07** ← ölçülmüş fizibil üst sınır | **1,12** | **6** |
| 0,50 | 2,61e+07 | 1,49 | 14 |
| 0,18 | 5,59e+08 | 4,13 | 299 |
| **0,124** | **1,72e+09** | **6,00** | **1010** |

(Bellek, FAZ 2'de ölçülen 6 GB / 11,2 M parçacık oranından ölçeklendi.)

**Sonuç:** SPH'de bir şoku kaynağında çözmek için çap boyunca en az ~6
parçacık gerekir. Bu, **1,72e9 parçacık** demektir — ölçülmüş fizibil üst
sınırın (1,12e7, H200/150 GB) **153 katı**.

Fizibil üst sınırda (1,12e7) aralık 0,663 m'dir ve mermi çapı boyunca **1,12
parçacık** düşer: mermi pratik olarak **tek bir parçacıktır**.

## FIZIBILITE'deki iddianın düzeltilmesi

`docs/FIZIBILITE.md` özetinde şöyle yazıyordu:

> | Motor DART ölçeğine çıkabiliyor mu? | **Evet** — 11,2 M parçacık ölçüldü, doğrusal, bellek bol |

Bu iddia **parçacık sayısı** için doğrudur ve ölçüme dayanır. Ama **eksiktir**:
o parçacık sayısının merminin çözülmesine yetip yetmediğini hiç kontrol
etmemiştim. Yetmiyor. İddia bu ADR ile daraltılıyor — silinmiyor, notla
düzeltiliyor (RULES.txt).

Doğru ifade: *motor 11,2 M parçacığa çıkabiliyor; ancak Dimorphos'u tekdüze
11,2 M parçacıkla ayrıklaştırmak DART mermisini çözmez.*

## Bunun neden önemli olduğu

Projenin çıkarımı **β** üzerinden yürüyor ve β, şokun hedefe **hangi alandan
ve hangi basınçla** girdiğine duyarlı. Mermi çözülmemişse:

- İlk temas basıncı çözünürlüğün bir yapayı olur (P3-FR-06'nın nokta parçacık
  yasağının gerekçesi tam buydu — ama yasak *merminin kendi* ayrıklaştırması
  için yazılmıştı, **hedefe göreli** çözünürlük için değil).
- Erken zamanlı enerji/momentum bağlanması güvenilmez; geç zamanlı kraterlenme
  ise bağlanma ölçüsüne (coupling parameter) bağlı olduğu için kısmen kurtarılabilir.

Yani **P3-FR-06 yarım kalmış bir gereksinimdir**: merminin kendi içinde kaç
parçacık olduğunu şart koşuyor (sağlandı, ≥6), ama merminin hedef aralığına
göre kaç parçacık ettiğini şart koşmuyor (sağlanmıyor, 1,12).

## Karar

1. **FAZ 4 tekdüze küresel ağla yapılmayacak.** DART senaryosu, çarpma
   bölgesinde **yerel yüksek çözünürlüklü** bir alt bölge ile kurulacak;
   uzak alan daha kaba ayrıklaştırılacak. Bu, çarpma simülasyonu
   literatüründe standarttır ve tek uygulanabilir yoldur.

2. **Bu ADR bir tasarım kararı değil, bir SINIR kaydıdır.** Yerel incelmenin
   nasıl yapılacağı (parçacık bölme mi, iki-alan eşlemesi mi, değişken kütle
   mi) FAZ 4'te ölçümle seçilecek ve ayrı bir ADR ile kaydedilecek. Burada
   kilitlenen tek şey: **tekdüze ağ yeterli değildir ve bunun sayısı budur.**

3. **Çözücüye tanı eklendi.** `scripts/measure_longrun.py` her koşuda merminin
   hedef aralığına göre kaç parçacık ettiğini yazar ve 2'nin altındaysa açık
   uyarı verir. Sessiz kalan bir çözünürlük yetersizliği, ölçülmemiş bir
   yetersizliktir.

4. **Kararlılık ölçümü ayrıştırıldı.** "Uzun koşuda defter kayıyor mu"
   sorusu, mermi çözünürlüğünden bağımsızdır. O ölçüm, merminin yoğunluğu
   düşürülerek (kütle ve hız sabit → momentum ve kinetik enerji korunur)
   **çözünür hale getirildiği** bir kurulumda yapılır ve sonuçlar bu haliyle
   raporlanır — DART sayısı olarak değil.

## Reddedilen seçenekler

- **"11,2 M yeter" deyip devam etmek.** Ölçüm bunun aksini söylüyor; β o
  kurulumda sayısal bir yapay olurdu ve projenin tek çıktısı β.
- **Merminin yarıçapını büyütüp DART diye sunmak.** Momentum ve enerji korunsa
  bile temas alanı ve basıncı değişir; bu, ölçülmemiş bir şeyi ölçülmüş gibi
  göstermek olurdu. Yoğunluk düşürme yalnızca **kararlılık** ölçümünde ve
  açıkça etiketlenerek kullanılır.
- **Nokta kaynak (point-source) yaklaşımına geçmek.** Geç zamanlı kraterlenme
  için savunulabilir ama P3-FR-06 nokta parçacığı açıkça yasaklıyor ve erken
  zamanlı β bilgisini tamamen kaybederdik. FAZ 4'te yerel incelme ile birlikte
  bir *karşılaştırma* olarak değerlendirilebilir.
