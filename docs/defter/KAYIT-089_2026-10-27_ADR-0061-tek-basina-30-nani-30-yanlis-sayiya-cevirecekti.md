# KAYIT-089 — ADR-0061 tek başına 30 `nan`'ı 30 **yanlış sayıya** çevirecekti

**Tarih:** 2026-10-27 · **Sıfır GPU** (TRUBA erişilemezdi) · **Yerel ölçüm**
**Öncül:** A86, [KAYIT-088](KAYIT-088_2026-10-22_A86-kok-sebep-tepe-ortak-alininca-referans-yuzey-kaciyor.md),
[ADR-0061](../adr/ADR-0061-krater-penceresi-durum-basina-kurulur.md)
**Sonuç:** [ADR-0062](../adr/ADR-0062-ortulu-krater-olculemez-sayi-yerine-red.md)

---

## 1. Tek cümle

KAYIT-088'in önerdiği düzeltmeyi (pencere durum başına) uyguladım,
**sonra ölçtüm**: `nan` kalkıyor ama yerine gelen sayı krater derinliği
değil, eksendeki örtünün tepesi. Yani düzeltmeyi tek başına yayınlamak
30 dürüst `nan`'ı 30 yanlış sayıya çevirecekti.

## 2. Niçin yakalandı

Sınavı önce yazmaya başladım ve `derinlik ≈ 1,0 m` bekleyen bir
doğrulama kurdum. O beklentiyi **tahminle sabitlemek yerine ölçtüm**.
Ölçüm beklentiyi çürüttü. Sınav o hâliyle geçseydi (yani ben
beklediğimi yazıp geçirmeye çalışsaydım) kusur sınava gömülmüş
olacaktı.

> Ders: düzeltmeyi yazan kişi, düzeltmenin sınavını **ölçmeden**
> yazmamalı. Sınav beklentiyi değil ölçümü bağlar.

## 3. Ölçüm — `d_merkez = −(yükseklik + 0,913)`

Sentetik levha (FCC `s = 0,35`, `h = 0,70`, `N = 32 490`), `2 m` ayak
izli `1 m` derin paraboloit çukur, eksen üstüne **hızsız** (yani
`bagli` sayılan) bir örtü:

| örtü yüksekliği (m) | `d_merkez` (m) | kapı `−2h = −1,4` |
|---:|---:|---|
| 0,0 | −0,913 | geçer |
| 0,1 | −1,013 | geçer |
| 0,2 | −1,113 | geçer |
| 0,3 | −1,213 | geçer |
| 0,4 | −1,313 | geçer |
| **0,5** | **−1,413** | **RED** |
| 1,0 | −1,913 | RED |
| 2,0 | −2,913 | RED |
| 12,0 | −12,913 | RED |
| 30,0 | −30,913 | RED |
| 50,0 | −50,913 | RED |
| *ejekta kaçmış* | **+0,922** | geçer |

Doğrusal uyum eğimi **`−1,000 ± 0,001`**: örtü `1 m` yükselince
"derinlik" `1 m` düşüyor. Bu, okunan şeyin kraterin tabanı **değil**
örtünün tepesi olduğunun doğrudan kanıtı.

## 4. Üretim sayıları aynı mekanizmayı söylüyor

KAYIT-088 §2'deki ölçüm:

| | `z_ref` (m) | `z_son` (m) | `d_merkez` (m) |
|---|---:|---:|---:|
| çalışan nokta (idx 1, `Y₀ = 58 708` Pa) | 59,517 | 58,769 | **+0,748** |
| çalışan nokta (idx 2, `Y₀ = 1 266` Pa) | 59,517 | 58,625 | **+0,892** |
| düşen noktalar (idx 0, `Y₀ = 28,3` Pa) | 59,517 | 105,916 | **−46,399** |

Yani ADR-0061 tek başına uygulansa 30 noktanın çıktısı
`≈ −46 m "derinlik"` olacaktı. Bir `nan`, yanlış bir sayıdan
dürüsttür (kural 8).

## 5. Sebep operatörün tanımında

`_doluluk_kesisimi` doluluk eş-yüzeyini **dıştan içe** ilk kesişimde
buluyor. Eksende kaçmamış yoğun malzeme varsa ilk kesişim onun
tepesidir. "Kaçmamış" demek önemli: ayrılma ölçütü
`vr > v_kaçış` **ve** `r − r0 > 2h`. Dimorphos'ta `v_kaçış ≈ 8,2 cm/s`;
`600 s`'te `46 m` yükselmiş malzemenin ortalama hızı `≈ 7,7 cm/s`
— **tam eşiğin altında**. Yani fizik olarak geri düşecek, ama ölçüm
anında havada ve `phi = 0,5`'i kesecek kadar yoğun.

Bu, `tests/test_krater_yuzey.py` içinde **zaten kayıtlı** bir sınırın
üretimde vurması: *"Ayrılma ölçütü hıza dayanıyor; hız yoksa perde
yüzey sayılır. Bu bir sınır, kusur değil."* O satırlar silinmedi;
sınav artık sınırın sonucunu (red) bağlıyor.

## 6. Yapılan — ADR-0062

Merkezde son yüzey, referans yüzeyin **bir çekirdek desteği (`2h`)**
üzerine çıkmışsa operatör `ValueError("ORTULU KRATER: ...")` atar.

Eşik ayarlanmadı: `2h` doluluk alanının çözünürlüğü. Ve yeri geniş —
çalışan noktalar `+0,75/+0,89`, düşenler `−46,4`; kapı `−1` ile `−45`
arasında herhangi bir yerde aynı sınıflamayı verir. Sınav bunu dört
ayrı değerle bağlıyor.

## 7. Bulgu: `600 s`'te geçici krater **gözlenemez**

Kapının söylediği şey bir kusur değil, bir ölçüm sınırı:

> Zayıf matris rejiminde (`Y₀ ≲ 149` Pa) `t = 600 s`'te krater, kaçış
> hızını geçmemiş ejekta tarafından örtülüdür; eksende doluluk
> eş-yüzeyi tabanı değil örtüyü okur.

Örtü rastgele değil: `nan` olma ile `log₁₀ Y₀` arasındaki ayırt
edicilik `AUC = 0,087` (güçlü, ters; KAYIT-088 §6). Düşen 30 noktanın
**hepsinde** `Y₀ < 149` Pa, posteriorun kipi `18,7` Pa. Yani kusur
tam da verinin işaret ettiği bölgede.

## 8. Hera için sonucu — ön kayıt yazılmadan bilinmesi gerekiyordu

Hera **son** krateri görecek (ejekta düştükten sonra). Bizim `600 s`
anlık görüntümüz, verinin işaret ettiği rejimde *geçici* krateri bile
göstermiyor. Dolayısıyla:

- Krater ön kaydı (PROTOKOL-HT) `600 s` durumundan `d_merkez` /
  `V_krater` olarak **kurulamaz**.
- Kurulabilmesi için ya daha geç bir anlık görüntü (ejekta düştükten
  sonra) ya da yüzey tanımının içten dışa çevrilmesi gerekir
  (ADR-0062 §3, reddedilmedi — sıraya alındı).

Bu, ön kayıt mühürlenmeden ve Hera verisi gelmeden ölçüldü; bu
KAYIT'ın tarihi ve commit'i sıralamanın kanıtıdır.

## 9. Kilitli yargılara etkisi — YOK

`krater_derinlik` ADR-0055 ile isteğe bağlı; `nan` kayıt düşürmüyor,
posteriora girmiyor. `n_yön = 1` (KAYIT-079), tarih eşlemesi
(KAYIT-080), SBC (KAYIT-081), çözünürlük yanlılığı (KAYIT-085),
`n_yön` dayanıklılığı (KAYIT-087) ve mühürlü spin ön kaydı
**etkilenmez**.

## 10. Sınavlar

`tests/test_krater_pencere_durum_basina.py` — 10 sınav:
pencere durum başına (3), örtü kapısı (4), hata mesajının hangi tarafı
suçladığı (3). `tests/test_krater_yuzey.py` 14/14 (biri NOT ile
güncellendi, hiçbir satır silinmedi).
