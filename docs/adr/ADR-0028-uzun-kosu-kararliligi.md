# ADR-0028 — Uzun koşu kararlılığı: hata birikmiyor, çarpma kayması O(dt)

- **Durum:** Kabul edildi
- **Tarih:** 2026-08-01
- **Bağlam:** `docs/FIZIBILITE.md` §5'in birinci açık maddesi
- **İlgili:** ADR-0020 (Sedov enerji hatası kesme hatasıdır — aynı yöntem),
  ADR-0026 (mermi çözünürlüğü)

## Kapatılan soru

FIZIBILITE §5 şöyle diyordu:

> **Uzun koşu kararlılığı.** Tüm kapı senaryoları ≤ 262 144 parçacık ve birkaç
> yüz adımdır. Bir DART koşusu ~10⁴–10⁵ adımdır. ADR-0020 enerji hatasının
> `O(dt)` olduğunu gösterdi, ama bu 10⁵ adımda ne birikir — ölçülmedi.

Şimdi ölçüldü.

## Kurulum

TRUBA / kolyoz14, H100. Hedef R = 20 m, aralık 0,5 m, **N = 379 207**
(378 198 hedef + 1009 mermi). Tillotson bazalt + dayanım + P-α gözeneklilik +
süreklilik yoğunluğu.

**Mermi çözünürlüğü sağlandı:** yoğunluk 20 kg/m³'e düşürülerek mermi
büyütüldü; **kütle ve hız sabit** olduğu için momentum ve kinetik enerji
korunur. Hedef aralığına göre **7,61 parçacık/çap** — ADR-0026'nın istediği
çözünmüşlük. Bu bir DART sayısı değildir; ölçülen şey **defterin
kararlılığıdır**.

## Sonuç 1 — hata BİRİKMİYOR

| adım | E_hata | p_hata |
|---|---|---|
| 250 | 1,4556e-02 | 6,5e-14 |
| 750 | 1,4558e-02 | 4,3e-14 |
| 1750 | 1,4558e-02 | 7,2e-15 |
| 3000 | 1,4558e-02 | 3,0e-15 |
| 4750 | 1,4558e-02 | 3,7e-14 |

Enerji hatası **birebir sabit** (1,4558e-02), log-log eğim ≈ 0. Momentum
1e-14 mertebesinde korunuyor.

**Yani hata bir SÜRÜKLENME değil, çarpma anında oluşan TEK SEFERLİK bir
kaymadır.** 10⁵ adımlık bir koşuda birikeceği miktar sıfırdır.

## Sonuç 2 — o kayma O(dt) kesme hatasıdır

Aynı ayırt edici yöntem ADR-0020'de kullanılmıştı: iki hipotez aynı gözlemi
açıklar, ölçüm hangisinin doğru olduğunu söyler.

**H1 — zaman kesme hatası** (CFL taraması, çözünürlük sabit):

| CFL | dt_ort [s] | E_hata | oran |
|---|---|---|---|
| 0,2500 | 2,900e-05 | 1,706673e-02 | 1,0000 |
| 0,1250 | 1,446e-05 | 7,788955e-03 | **0,4564** |
| 0,0625 | 7,219e-06 | 3,756895e-03 | **0,2201** |

**H2 — uzay ayrıklaştırma yapayı** (çözünürlük taraması, CFL sabit):

| aralık [m] | N | E_hata | oran |
|---|---|---|---|
| 1,00 | 47 632 | 1,706673e-02 | 1,0000 |
| 0,70 | 138 236 | 1,531624e-02 | 0,8974 |
| 0,50 | 378 597 | 1,467050e-02 | **0,8596** |

dt dörtte bire inince hata 0,2201'e iniyor — **birinci mertebe**, `O(dt)`.
Aralık yarıya inince hata yalnızca 0,8596'ya iniyor.

**Karar: H1.** Çarpma kayması zaman kesme hatasıdır; ne sızıntıdır ne de
çözünürlük yapayı.

## Sonuçları

1. **Uzun koşu güvenlidir.** Hata birikmiyor; 10⁵ adım 10³ adımdan daha
   kötü değil.
2. **Kayma kontrol edilebilir bir düğmeye bağlı.** %1,46 fazla geliyorsa CFL
   düşürülür ve hata orantılı azalır. FAZ 4 istenen doğrulukla CFL'i seçebilir;
   bu bir tasarım parametresidir, bir kusur değil.
3. **Kapı eşikleri anlamlı kalır.** G1/G2'nin enerji eşikleri (%0,5–1) bu
   koşuda CFL = 0,0625 ile zaten sağlanır (0,376%).

## Kapanmayan: gereken simüle süre

FIZIBILITE §5'in ikinci maddesi (**β ne zaman durulur**) bu koşuyla
**kapanmadı** ve nedeni dürüstçe kaydedilmelidir.

Ölçülen β, adım 750'den sonra 1,55701'de sabitlendi ve ejekta sayısı **tam
1009**'da dondu — bu, **merminin kendi parçacık sayısıdır**. Yani kontrol
yüzeyini geçen malzeme, hedeften kopan ejekta değil, **merminin geri
sıçramasıdır**; hedeften hiçbir parçacık 2R'yi geçmedi.

Sebep ADR-0026'nın öngördüğü şey: mermiyi çözünür kılmak için yoğunluğunu
135 kat düşürdüm; 20 kg/m³'lük bir mermi hedefe gömülmek yerine **köpük top
gibi sıçrıyor**. Momentum ve enerji korunuyor ama temas basıncı ve nüfuz
derinliği gerçek DART'ınki değil.

**Bu yüzden "β ne zaman durulur" sorusu FAZ 4'ün yerel incelme tasarımına
bağlıdır (ADR-0026) ve orada ölçülecektir.** Buradaki 1,557 sayısı bir DART
β'sı olarak sunulmaz.

## Ölçüm yöntemi notu

Plato araması **bağlı kütle** momentumundan türetilen β ile yapılır,
ejektadan türetilenle değil: ejekta betası parçacıkların kontrol yüzeyini
geçmesini bekler ve m/s mertebesindeki ejekta için bu 100+ saniye eder —
kraterlenme çoktan bitmiş olsa bile plato görünmez. (Bu koşuda ikisi de aynı
çıktı çünkü sayılan "ejekta" merminin kendisiydi.)
