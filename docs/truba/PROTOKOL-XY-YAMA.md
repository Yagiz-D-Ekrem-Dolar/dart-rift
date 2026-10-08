# Protokol XY — **çözünürlük yaması** (KİLİTLİ)

**Yazıldı:** 2026-10-08, **tek bir yama koşusu yapılmadan ÖNCE.**
**Öncül:** [PLAN-90-GUN](../PLAN-90-GUN.md) §1 (3. kuşak, 15. iş),
PROTOKOL-M-YAKINSAMA, KAYIT-077 §5, ADR-0058.
**Bütçe tavanı:** **`37 GPU-saat`.** Aşarsa iş **durur**, kapsam dışı yazılır.

---

## 1. Soru ve niçin ayrı protokol

Dimorphos koşularımızın taban aralığı `7 m`. Krater fiziğinin bir kısmı
(şok cephesi kalınlığı, blok-matris arayüzü, kazı akışının ince yapısı)
bu ölçeğin **altında**. PROTOKOL-M bunun **ne kadar** sorun olduğunu
`β` üzerinde ölçüyor; bu protokol farklı bir şey soruyor:

> Düşük çözünürlüklü bir koşunun hatası, **öğrenilebilir bir düzeltme**
> midir?

İkisi bir değil. M "yakınsadı mı" diye bakar; XY "yakınsamadıysa farkı
modelleyebilir miyiz" diye bakar.

### Niçin tam cisimde yapılamaz

`X` ve `Y` **aynı alan** üzerinde olmak zorunda (farklı alan =
karşılaştırılamaz). `7 m` aralıkla anlamlı bir Dimorphos için en az
`~100 m` gerekiyor; o alanı `1 cm`'e indirmek `3,4e11` parçacık, yani
`~5,4e7 GPU-saat`. **Kapalı.** (Bu hesap KAYIT-077'de yazılı; bu
protokol onu tekrar açmıyor.)

Yani yama **küçük, düzlemsel bir alanda** yapılır ve oradan tam cisme
**taşınabilirliği bir iddia olarak** sınanır — kanıt olarak değil.

---

## 2. KAPI 1 — analitik plaka kapısı (bu geçmezse hiç koşulmaz)

Yama alanı **yeni bir sahne** (kutu/dilim). Mevcut `shape_mesh.py` yalnız
ikosfer ve elipsoit üretiyor; `validation/plate.py` 1-B CPU referansı.
Yani **önce sahne yazılacak**. Yazılan sahnenin doğru olduğu, sonuç
görülmeden, analitik çözümle sınanır.

| sınav | eşik |
|---|---|
| Düzlemsel çarpmada şok hızı `U_s` analitik Hugoniot değerini veriyor | bağıl hata `< 0,05` |
| Şok arkası basınç platosu analitik `P_H` | bağıl hata `< 0,05` |
| Serbest yüzey hız ikilenmesi (`v_fs ≈ 2 u_p`) | bağıl hata `< 0,10` |
| Toplam momentum korunuyor (çekim ve dayanım kapalı) | bağıl artık `< 1e-10` |

**Dördünden biri geçmezse:** yama koşuları **gönderilmez**, bütçe (`37 sa`)
paya döner, PLAN-90-GUN'da iş "kapsam dışı — kapı 1 düştü" diye yazılır.

Bu kapı kasten sert. Yanlış bir kutu sahnesinden öğrenilen "düzeltme",
sahnenin kendi hatasını öğrenir.

---

## 3. Tasarım

### Alan

Düzlemsel dilim: kalınlık `H`, yan uzunluk `≥ 3 H`, yanlardan periyodik
ya da yeterince geniş (kenar etkisi ölçülür, §3.3). Hedef cismin
malzemesi (Tillotson + `URETIM_BLOK` bloklar + matris `Y₀`), aynı geç-evre
hızlı entegrasyon şeması, aynı `t_geçiş = 1,0 s`.

### Üç çözünürlük — iki değil

| ad | aralık | niçin |
|---|---|---|
| `X0` | `h` | referans kaba |
| `X1` | `h / 2` | ara |
| `Y`  | `h / 4` | ince |

**Üç** nokta zorunlu: ikisi yalnız "fark" verir, üçü **yakınsama mertebesi**
verir (Richardson) ve düzeltmenin orana nasıl bağlandığını gösterir. İki
noktayla "düzeltme öğrendik" demek, tek veri noktasından eğim çıkarmaktır.

`h` değeri **kapı 1 geçtikten sonra** bir kalibrasyon koşusuyla seçilir:
ölçüt, `Y`'nin şok cephesini en az `~10` parçacıkla çözmesi. Kalibrasyon
koşularının tavanı **`5 GPU-saat`** (37'nin içinden).

### 3.3 Yazılı ihmaller

Yama alanı düz, tek katmanlı ve öz çekimsiz. Tam cisimdeki eğrilik,
serbest yüzey geometrisi, öz çekim ve `17°` eğiklik **yok**. Bunlar
"taşınabilirlik varsayımı"nın içinde ve §5'te açıkça yazılır.

---

## 4. Düzeltme ve KAPI 2

### Öğrenilen şey

Bir özet vektörü `s` üzerinde çalışılır — `β`'nın yama karşılığı
(aktarılan momentum), kaçan kütle, hız dağılımının iki yüzdeliği.

    δ(h) = s_Y − s_X        (ince eksi kaba)

`δ`, `h` ve `θ`'ya bağlı bir **düzeltme** olarak öğrenilir. Biçim
**önceden sabitlenir** (veriye bakıp model seçmek yok):

    s_düzeltmeli(θ, h) = s_X(θ, h) + c(θ) · h^p

`p` üç çözünürlükten **ölçülür** (Richardson). `c(θ)` yama
tasarımındaki `θ` noktalarına GP ile oturtulur. Üstel/karmaşık biçim
denenmez; denenirse bu protokol **ihlal** edilmiş sayılır ve sonuç
"keşif" etiketiyle raporlanır.

### Çapraz geçerlilik hatası

`E` = **dışarıda bırak-bir** çapraz geçerlilik hatası, `s_Y`'ye karşı:

    E_düzeltmesiz = RMS( s_X  − s_Y )
    E_düzeltmeli  = RMS( s_düz − s_Y )     (her nokta kendi dışında eğitilerek)

### KAPI 2 — kilitli yargı

| yargı | koşul | sonucu |
|---|---|---|
| **DUZELTME ISE YARIYOR** | `E_düzeltmeli < E_düzeltmesiz / 3` | araç olarak kullanılabilir; §5'in sınırlarıyla |
| **DUZELTME ZAYIF** | `E_düzeltmesiz/3 ≤ E_düzeltmeli < E_düzeltmesiz` | **araç olarak kullanılmaz**; bulgu olarak raporlanır ("fark öğrenilebilir değil") |
| **DUZELTME ZARARLI** | `E_düzeltmeli ≥ E_düzeltmesiz` | aynı; ayrıca ters işaret incelenir |

`3` katsayısı **şimdi** seçildi: `%33`'ten fazla kalan hata, `β`'nın
gözlem belirsizliğinden (`+0,19/−0,25`, bağıl `~%6`) hâlâ çok büyük
olduğu için araç sayılmaz.

---

## 5. Kapı 2 geçerse NE söylenebilir, NE söylenemez

**Söylenebilir:**
- "Düzlemsel bir dilimde, `h → h/4` arasında, `β`'nın çözünürlük hatası
  `h^p` biçiminde öğrenilebilir ve çapraz geçerlilikte `≥3×` azalıyor."
- `p`'nin ölçülen değeri ve Richardson kestirimi.

**Söylenemez (yazılı yasak):**
- "Dimorphos koşumuzu `1 cm` çözünürlüğe çıkardık." **Hayır.** Yama
  `h/4`'e kadar gider; `7 m → 1 cm` `700×`'tür ve ölçülmemiştir.
- "Düzeltme tam cisimde geçerli." **Varsayım.** Düz dilimden eğri,
  öz çekimli, eğik çarpmalı cisme taşınabilirliği sınanmadı.
- Düzeltilmiş `β`'nın **posteriora girmesi.** Posterior tarifi
  KAYIT-075'te kilitli; XY onu değiştirmez. Düzeltme en çok
  **model eksikliği bütçesinde ölçülmüş bir terim** olabilir
  (`cozunurluk_olculen_yama`), o da yan yana.

## 6. Bu protokolün yapmadığı şey

- Vekil modeli değiştirmiyor. Çok doğruluklu vekil (UY2, `3,5 m` ince
  noktalar) **ayrı** iştir ve **tam cisimde** eşleşmiş tasarımla yapılır;
  XY onun yerine geçmez.
- PROTOKOL-M'in yakınsama yargısını değiştirmiyor.
- Aksarsa proje aksamıyor: PLAN-90-GUN'da 10-11. haftada ve "aksarsa
  atılır" yazılı.
