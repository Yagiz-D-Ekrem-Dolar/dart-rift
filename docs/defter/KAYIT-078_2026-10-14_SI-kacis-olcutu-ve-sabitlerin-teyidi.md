# KAYIT-078 — Didymos sabitleri teyit edildi, PROTOKOL-SI §2 koşuldu

**Tarih:** 2026-10-14 · **Havuz:** 88/96 (kısmi) · **Maliyet:** sıfır GPU

> **Bu kayıt KISMİ havuzdan.** Mühürlü ölçüm 96 nokta tamamlandığında,
> `scripts/si_son_isleme.py` ile yeniden üretilecek. Yargı kuralları
> PROTOKOL-SI'de 2026-10-08'de, sayılar görülmeden kilitlenmişti;
> burada **uygulandı**, değiştirilmedi.

---

## 1. Sabitlerin teyidi — ve hatırlanan bir değerin yanlış çıkması

PROTOKOL-SI'nin ortak künyesi üç sabiti `teyit bekliyor` tutuyordu ve
kuralı netti: *teyit edilmemiş sabitle koşulan ölçüm OKUNMAZ.* Bu yüzden
§2, §3 ve §4 blokeliydi.

**Birincil kaynak:** Naidu, S. P., Chesley, S. R., Moskovitz, N., ve ark.
(2024), *The Planetary Science Journal* 5, 74,
[doi:10.3847/PSJ/ad26e7](https://doi.org/10.3847/PSJ/ad26e7). Değerler
Richardson ve ark. (2025), [arXiv:2502.14990](https://arxiv.org/abs/2502.14990)
**Tablo 2**'de derlenmiş ve orada Naidu 2024'e atfedilmiştir.

| sabit | teyitli (çarpma öncesi) |
|---|---|
| sistem toplam kütlesi | `5,3 ± 0,2 × 10¹¹ kg` |
| Dimorphos kütlesi | `4,5 ± 0,4 × 10⁹ kg` |
| Didymos (birincil) | `5,255 ± 0,020 × 10¹¹ kg` |
| yörünge ayrıklığı `a` | `1189 ± 17 m` |
| yörünge periyodu `T` | `11,921493 ± 0,000016 sa` |

**Bağımsız teyit:** Naidu ve ark. (2022),
[arXiv:2210.05101](https://arxiv.org/abs/2210.05101), çarpma epoğunda
periyodu `11,9214869 ± 0,000028 sa` veriyor — belirsizlikler içinde
örtüşüyor.

### Hatırlanan değer yanlışmış

Künyede `a ≈ 1206 m` yazılıydı; teyitli değer **`1189 ± 17 m`**. Fark
`17 m`, yani belirsizliğin tam bir katı. `1206` büyük olasılıkla
*karşılaşma öncesi* `1,20 ± 0,03 km` değerinin yuvarlanmışıyla karışmış.

`v_kaçış ∝ a^(−1/2)` olduğundan bu `%0,7`'lik bir kayma yapardı. Küçük —
ama kuralın engellemek için konduğu şeyin ta kendisi. **Kural işledi.**

Türetilen:

    v_kaçış,sistem = sqrt(2 G M_birincil / a) = 0,24289 ± 0,00494 m/s

Koşulardan geri çözülen cismin **kendi** kaçış hızı `0,0791–0,0890 m/s`;
sistemden kaçış onun **2,89 katı**. PROTOKOL-SI §2'nin beklediği
`~0,24 m/s` ile tutuyor.

---

## 2. Kaçış ölçütü koşunun kendi çıktısından geri çözülür

Etkin yarıçap `npz`'de **var** (`R`), ama koşunun uyguladığı eşik
bisection'ın döndürdüğü aralığın ortasıdır; nominal `sqrt(2GM/R)` ile
`%0,4` ayrılıyor. Doğrusu `M_kacan`'dan geri çözmektir.

**Ölçüt üç kez yanlış tahmin edildi**, doğrusu kaynak okunarak bulundu
(`observables/aday_gozlemliler.kacis_hizi_kalibre`):

| aday | 72 dosyada geçen |
|---|---|
| kütle merkezi çerçevesi + `m(1−mermi_kesri)` | 34 |
| öz-tutarlı (yinelemeli) kütle merkezi | 29 |
| **lab çerçevesi + `mermi_kesri > 0,5` tamamen atılır** | **72** |

Doğru bileşimle azami bağıl hata `3,4×10⁻¹⁴`. Fonksiyonun kendi notu
zaten uyarıyordu: *"Tahmin etmek, bütün aday gözlemlileri sessizce
kaydırır."*

---

## 3. §2 — iki kaçış ölçütü (kilitli yargı uygulandı)

`σ_kaçış = |b_Dimorphos − b_sistem| / b_Dimorphos`

### Yöntem notu — neden fark alındı, mutlak değer yeniden kurulmadı

`beta_hedef`'i ham durumdan yeniden üretmeyi denedim: ortanca bağıl hata
`2,1×10⁻⁴`, ama **azami `4,3×10⁻²`**. Sebebi, dosyada iki ayrı tanımın
bulunması (`beta_kacan` 3,8271 vs `beta_kacan_hedef` 3,8236; `M_kacan`
`2,835e7` vs `M_ejekta_hedef` `2,419e7`). Yani alt tanım yine tahmin
ediliyordu.

Bunun yerine `b_Dimorphos` **kayıtlı değerden** alındı ve yalnız
*cismi terk eden ama sistemi terk etmeyen* dar banttaki katkı çıkarıldı.
Kıyas için tamamen yeniden kurulmuş kol da hesaplandı:

    sigma_kacis (kayitli b_D ile)  : ortanca 0,0344
    sigma_kacis (tam yeniden kurma): ortanca 0,0348
    iki kol farki                  : ortanca 0,00001

İki kol `10⁻⁵` içinde uyuşuyor: **oran, `β`'nın alt tanım
belirsizliğinden etkilenmiyor**, sistematik sadeleşiyor.

### Sonuç (88 nokta)

| yargı | koşul | nokta |
|---|---|---|
| KACIS OLCUTU ONEMSIZ | `σ ≤ 0,03` | **42** |
| LITERATURLE UYUMLU | `0,03 < σ ≤ 0,12` | **33** |
| **KACIS OLCUTU BASAT** | `σ > 0,12` | **13** |

`σ_kaçış` ortancası `0,0344`, aralık `0,0002–0,3218`.

Ortanca "LİTERATÜRLE UYUMLU" bandında: literatürün bildirdiği `~%6`
mertebesi büyüklük olarak doğrulanmış sayılır.

**Ama 13 nokta BAŞAT.** O noktalarda kaçan kütlenin `%97`'ye kadarı cismi
terk edip **sistemi terk etmiyor**. Protokolün kilitli sonucu gereği o
noktalar için `β`'nın hangi ölçütle raporlandığı **başlıkta** yazılmalı
ve iki değer yan yana verilmelidir.

Kilitli karşılaştırma `b_Dimorphos` ile yapılır (Cheng'in `β`'sı yörünge
periyodu değişiminden türüyor); `b_sistem` yan yana raporlanır. Bu seçim
koşudan önce yapılmıştı, değiştirilmedi.

---

## 4. Hâlâ bloke olan

**§3 (yörünge yönüne projeksiyon)** — `ê_yörünge`, yani çarpma anındaki
yörünge hız doğrultusunun **sahne koordinatlarındaki** karşılığı teyit
edilmedi. Kütle, `a` ve `T` teyitlendi ama bu bir *geometri* sabiti ve
ayrı kaynak doğrulaması istiyor. §3 koşulmadı.

**§4 (balistik)** — entegratör kapısı (`t=0`'da `β`'yı `<1e-6` yeniden
üretme) yazılmadı; `b_Dimorphos`'u yeniden kurmadaki `4,3×10⁻²`'lik
azami sapma, o kapının neden gerekli olduğunu gösteriyor.

**§5'in yüzde yargısı** — çarpma öncesi *dönme* periyodu (yörünge
periyodu değil) ayrıca teyit edilmeli. `|L|` ve `ω` koşuyor.

---

## 5. Dürüst değerlendirme

Bugün üç kez aynı hata yapıldı ve üçünde de **kapı yakaladı**: ölçülmemiş
bir sabiti (`cozunurluk_yakin`), tahmin edilmiş bir ölçütü (kaçış eşiği),
ve hatırlanmış bir sayıyı (`a ≈ 1206 m`). Üçü de sessizce geçebilirdi.

Bu kayıt bir başarı kaydı değil; kuralların **neden** yazıldığının
kaydıdır.
