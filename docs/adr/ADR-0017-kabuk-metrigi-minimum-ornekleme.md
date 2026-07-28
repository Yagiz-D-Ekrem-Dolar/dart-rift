# ADR-0017: Yerçekimi kabuk metriğinde minimum örnekleme 50 → 200

- **Durum:** Kabul edildi
- **Tarih:** 2026-07-28
- **Bağlam:** P2-VR-05, G2 kapısı C4 ölçütü
- **İlgili:** [ADR-0011](ADR-0011-sedov-yakinsama-kurulumu.md)

## Sorun

G2 kapısında C4'ün alt ölçütü `shell_mean_rel_err_max < %5` idi ve ölçülen
değer **%4,65** — eşiğe 0,35 puan. Bu kadar dar bir marj, ölçünün ne kadar
kararlı olduğu sorusunu doğurdu.

Metrik n'e karşı tarandı ve **monoton çıkmadı**:

| n | `shell_mean_rel_err_max` |
|---|---|
| 1 000 | %1,79 |
| 2 000 | **%8,97** |
| 4 000 | %4,65 |
| 8 000 | %2,98 |
| 16 000 | %1,63 |

n=2000'de değer eşiğin **neredeyse iki katı**. Kapı n=4000 kullandığı için
geçiyordu; başka bir n seçilseydi aynı kod kalırdı.

## Kök neden

Metrik, 8 radyal kabuğun her birinde ortalama radyal alanı analitik
`g(r) = GMr/R³` ile karşılaştırıp **maksimumu** alıyor. Kabuklar
`r ∈ [0,3R, 0,9R]` bandında, hacimleri `r²` ile büyüdüğü için iç kabuklar
çok daha az parçacık içeriyor.

Parçacık başına alan gürültüsü ~%10 (kod bunu `particle_noise_mean_rel`
olarak zaten raporluyordu). Kabuk ortalamasının gürültüsü ≈ %10/√N:

| Kabuk N | ortalamanın gürültüsü |
|---|---|
| 50 | ~%1,4 (kuyrukta çok daha fazla) |
| 64 | ~%1,25 |
| 200 | ~%0,7 |

Eski taban **50** idi. n=2000'deki kabuk dolulukları
`47, 64, 117, 137, 188, 219, 274, 353`; ilk kabuk 47 ile elendi ama
**64'lük ikinci kabuk kabul edildi** ve %8,97'yi o üretti.

Yani ölçüt, alanın doğruluğunu değil **örnekleme gürültüsünü** ölçüyordu.
Bir maksimum istatistiği olduğu için de en gürültülü kabuk sonucu tek başına
belirliyordu.

## Karar

`SHELL_MIN_COUNT = 200`.

Gerekçe niceliksel: N ≥ 200 ile kabuk-ortalama gürültüsü ~%0,7'ye iner, yani
%5'lik eşiğin yedide biri. Eşik böylece gürültüyü değil gerçek alan hatasını
sınar.

Ayrıca: ≥200'lük kabuk sayısı 3'ün altına düşerse ölçüm **açık hata verir**.
Eskiden yeterli veri olmadan da bir sayı üretiliyordu; boş/tek kabuk
üzerinden "geçen" bir ölçüt sessiz bir yanlış sonuçtur.

Dönen sözlüğe `n_shells_used` ve `shell_min_count` eklendi ki kanıt raporu
ölçünün kaç kabuğa dayandığını göstersin.

## Sonuç

Metrik n boyunca kararlı hale geldi:

| n | eski (min=50) | yeni (min=200) |
|---|---|---|
| 2 000 | %8,97 | %1,48 |
| 4 000 | %4,65 | **%1,90** |
| 8 000 | %2,98 | %2,98 |
| 16 000 | %1,63 | %1,63 |

G2 C4 marjı 1,08× → **2,6×**.

Bu bir eşik gevşetmesi **değildir**: eşik %5'te kaldı, değişen şey ölçünün
neyi ölçtüğüdür. Gevşetme olsaydı sayı eşiğe yaklaşırdı; burada sayı
küçüldü çünkü gürültü ölçüden çıkarıldı.

## Alternatifler

- **Maksimum yerine ortalama kullanmak** — varyansı düşürürdü ama tek bir
  kötü kabuğu gizlerdi; maksimum, kabuk bazında bozulmayı yakalamak için
  bilinçli seçim.
- **Kabuk sayısını azaltmak (8 → 4)** — her kabuğu doldururdu ama radyal
  çözünürlüğü yarıya indirirdi; `g ∝ r` doğrusallığını sınama gücü azalırdı.
- **Eşiği yükseltmek** — ölçüyü düzeltmeden eşiği gürültüye uydurmak olurdu.

## Doğrulama

- `tests/test_uniform_sphere.py::TestErrorScaling::test_shell_metric_is_stable_across_n`
  — n = 4000/8000/16000'de hem eşik hem de **n'ler arası tutarlılık**
  (maks/min < 3) sınanır; eski hatayı geri getiren bir değişiklik burada
  yakalanır.
- `...::test_undersampled_n_raises_instead_of_passing_silently` — n=800'de
  açık hata.
- `...::test_bh_error_grows_with_opening_angle` — ayrı hata kaynağı olan
  ağaç yaklaşımının θ ile ölçeklendiğini sabitler (%0,054 / %0,435 / %1,060).
