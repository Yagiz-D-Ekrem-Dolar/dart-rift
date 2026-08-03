# KAYIT-019 — FAZ 4 başlangıç: kütle oranı toleransı (2026-08-03)

**Kapsam:** FAZ 4.1 · **Durum:** ilk ölçüm alındı, karar **verilmedi**
**Önkoşul:** ADR-0026 (mermi çözünürlüğü sınırı), ADR-0030 (kütle tutarlılığı)

---

## 1. Neden bu ölçüm, neden şimdi

ADR-0026 FAZ 4'ün önüne bir sınır koydu ve kararı **ölçüme** bıraktı:

> DART mermisini çapı boyunca 6 parçacıkla çözmek **1,72e9** parçacık ister;
> fizibil sınır **1,12e7** — **153 kat**. Yerel incelmenin *nasıl* yapılacağı
> FAZ 4'te ölçümle seçilecek.

Dört seçenek var (A: değişken kütle bölgeleri, B: parçacık bölme, C: iki alan
eşlemesi, D: kaynak terimi). **A** ile başlandı çünkü diğer üçü de A'nın
sınırını bilmeyi gerektirir: B bölme oranını, C arayüz kontrastını, D "ne
kadar kaba yeterli"yi.

Sayı doğrudan seviye sayısını verir: oran `R` ise `153 = R^k`.
`R = 8` → `k ≈ 2,4` → **3 seviye**.

### Bu ölçüm ADR-0030'dan önce yapılamazdı

Kütleler tekdüzeydi ve `m/ρ ≠ V_p` tutarsızlığı (K7) her sonucu kirletirdi.
Şimdi `m_i = ρ_i·V_p` **tam** tutuyor (`[1,000000 ; 1,000000]`), yani kütle
oranını değiştirmek **yalnızca** kütle oranını değiştiriyor.

> Hata ayıklama kampanyasının FAZ 4'e doğrudan katkısı budur.

---

## 2. Düzenek

Aynı küre iki popülasyonla dolduruldu: iç bölge (`r < 25 m`) `λ` kat daha
ince, dış bölge kaba (`s = 8 m`). Kütle ADR-0030 kuralıyla `m = ρ·V_p`, yani
oran tam `λ³`.

### Kurulumda K7'nin tekrarı yakalandı

İlk yazdığım sürüm `ρ = 1800` kullanıyordu. Ama gözeneklilik kapalıyken
(`α = 1`) çözücü `ρ = ρ₀_katı = 2700` atar (ADR-0022) — yani `m/ρ ≠ V_p`
olurdu: **K7'nin ta kendisi**, bu kez benim düzeneğimde. Düzeltildi.

---

## 3. Birinci ölçüm boştu — kendi kuralımı ihlal ettim

İlk "keskin sınav"ım şuydu: gerilmesiz durumda (`ρ = ρ₀`, `u = 0`) `a_SPH`
tam sıfır olmalı. Ölçüm:

```
lam    kütle oranı    a_arayüz
1.00      1.00       0.0000e+00
2.00      8.00       0.0000e+00
2.52     16.00       0.0000e+00
```

**16:1'de bile tam sıfır.** Sevindirici değil — **kuşku verici**.

Sebep: `P = 0` ve `S = 0` iken kuvvet terimi `T = (−P I + S)/ρ²` **özdeş
olarak sıfırdır**. İvmenin sıfır çıkması ayrıklaştırmayla ilgisiz, cebirsel
bir zorunluluk. Test **düşemiyordu** — ADR-0040'ın tam olarak yasakladığı şey.

### Düzeltme

**Düzgün ama sıfırdan farklı** basınç alanı: `ρ = ρ₀·(1 + 0,01)`. Bu, SPH'in
**sıfırıncı mertebe tutarlılık** sınavıdır: *sabit bir alanın gradyanı
sıfırdır.* Ayrık gradyan bunu tam veremezse **yapay kuvvet** doğar — yerel
incelmenin bedeli tam olarak budur.

Alanın gerçekten düzgün olduğu ayrıca doğrulanıyor (`field_is_uniform`).

---

## 3b. DÜZELTME — ilk ölçümün maskesi de bozuktu (4 Ağustos)

§4'teki tablo **geçersizdir**. Silinmiyor, üstü çiziliyor ve nedeni yazılıyor.

### Ne yanlıştı
Bölge maskeleri dış yüzeyden **2,5·aralık** pay bırakıyordu. Ama `h = 2·aralık`
olduğu için Wendland C2'nin desteği **`2h` = 4·aralık**tır. Yani yüzeye
`4·aralık`tan yakın parçacıkların komşuluğu **kesikti** ve orada yapay kuvvet
doğuyordu — kütle oranıyla **ilgisiz** bir yüzey artığı.

### Ölçüldü (tek popülasyon, düzgün basınç — doğru cevap **tam sıfır**)

| kenar payı | n | a_maks | a/ölçek |
|---|---|---|---|
| 2,5·s | 683 | 5,4813e+02 | 0,0878 |
| 3,0·s | 555 | 8,5467e+01 | 0,0137 |
| **4,0·s** | 249 | **5,8938e-12** | **0,0000** |
| 5,0·s | 87 | 4,1911e-12 | 0,0000 |

**"Taban 0,0397" diye raporladığım şey tamamen maskemin artığıydı.** Doğru
payla taban makine hassasiyetinde sıfır — mükemmel FCC kafes düzgün basınçta
hiç yapay kuvvet üretmiyor, üretmemesi gerektiği gibi.

### İkinci sorun: geometri yetersizdi
Pay `2h + s/2 = 36 m` iken `r_inner = 25 m` idi; yani **"derin dış" bölge
tamamen boş kalıyordu** ve ölçüm sessizce yalnızca iç bölgeyi ölçüyordu.
Düzeltme: geometri `r_outer = 70`, `h/s = 1,3` (projenin kendi değeri) ve
**bölge boş kalırsa artık hata veriliyor**.

### Düzeltilmiş ölçüm

`r_outer = 70`, `r_inner = 25`, `s = 8`, `h/s = 1,3`, pay `= 2h + s/2`:

| λ | kütle oranı | N | n_arayüz | birim bölünmesi | a_arayüz | **a/ölçek** |
|---|---|---|---|---|---|---|
| 1,00 | 1,00 | 3997 | 488 | 0,00381 | 1,3013e-11 | **0,0000** |
| 1,26 | 2,00 | 4189 | 644 | 0,04009 | 1,2349e+03 | **0,1286** |
| 1,44 | 2,99 | 4375 | 822 | 0,08814 | 2,7995e+03 | **0,2915** |
| 1,59 | 4,02 | 4503 | 896 | 0,08619 | 2,0837e+03 | 0,2170 |
| 2,00 | 8,00 | 5301 | 1514 | 0,08787 | 2,0240e+03 | 0,2108 |
| 2,52 | 16,00 | 6719 | 2650 | 0,08296 | 1,8798e+03 | 0,1957 |

**Taban artık gerçekten sıfır** (`1,355e-15`), yani arayüz katkısı **yalnız**.

### Bu tablo ne diyor — ve öncekinden farkı

| | önceki (kirli) | düzeltilmiş |
|---|---|---|
| taban | 0,0397 | **1,4e-15** |
| 2:1 katkısı | +0,023 | **0,129** |
| 3:1 katkısı | +0,032 | **0,292** |
| en büyük | 0,049 | **0,292** |

Yapay kuvvet **beş kat daha büyük** ve **2:1'de bile** ortaya çıkıyor.
Üstelik oranla **monoton büyümüyor**: 3:1'de tepe yapıp ~%20'de duruyor.

**Yorum:** arayüz hatasını belirleyen şey süreksizliğin *büyüklüğü* değil,
**varlığı**. Bu, tasarım kararı için doğrudan anlamlıdır: ani kütle
sıçramasıyla bölgeleme **her oranda** sorunlu görünüyor.

> Bu, K18'in dersinin bir kez daha doğrulanmasıdır: ölçüm = taban + sinyal.
> Ama bu kez taban **ölçüm düzeneğinden** geliyordu, fizikten değil — ve o
> yüzden sinyali beş kat küçük gösteriyordu.

---

## 4. Ölçüm sonucu ~~(GEÇERSİZ — bkz. §3b)~~

Uygulanan düzgün basınç: `P = 2,6967e+08 Pa` (her yerde aynı, doğrulandı).

| λ | kütle oranı | N | birim bölünmesi sapması | a/ölçek | **fazlalık** |
|---|---|---|---|---|---|
| 1,00 | 1,00 | 2491 | 0,00186 | 0,0397 | **+0,0000** |
| 1,26 | 2,00 | 2683 | 0,01816 | 0,0629 | +0,0232 |
| 1,44 | 2,99 | 2869 | 0,03017 | 0,0713 | +0,0317 |
| 1,59 | 4,02 | 2997 | 0,03215 | 0,0653 | +0,0257 |
| 2,00 | 8,00 | 3795 | 0,03499 | 0,0890 | **+0,0493** |
| 2,52 | 16,00 | 5213 | 0,02607 | 0,0795 | +0,0398 |

**Boşluk kontrolü geçti:** 1:1 tabanı temiz (birim bölünmesi sapması 0,00186).

### K18'in dersi burada da gerekti

Ham `a/ölçek` sayısı **taban + kütle oranı katkısı** toplamıdır. Taban
(0,0397) kafesin küreyle kesilmesinden gelir ve **kütle oranıyla ilgisizdir**.
Bu yüzden **fazlalık** raporlanıyor.

---

## 5. Ölçümün söylediği ve söylemediği

### Söylediği

- Kütle oranı arttıkça yapay kuvvet **artıyor** ama **doymuş** görünüyor:
  fazlalık 8:1'de %4,9, 16:1'de %4,0.
- Birim bölünmesi sapması da benzer: 3:1'den sonra ~%3'te platoya çıkıyor.
- **Felaketli bir büyüme yok.** 16:1 bile taban hatasının iki katından az
  ekliyor.

### Söylemediği — ve bu yüzden karar verilmedi

1. ~~**Derin bölge arayüzden daha kötü.**~~ **ÇÖZÜLDÜ (§3b).** O gözlem
   maskenin artığıydı; kenar payı çekirdek desteğine çıkarılınca taban
   `1,4e-15`'e düştü ve arayüz katkısı yalnız kaldı. Periyodik kutuya gerek
   kalmadı — yeterli pay yetti.

2. **`t = 0` anlık bir ölçümdür.** Asıl soru yapay kuvvetin **birikip
   birikmediği**. ADR-0028'de ölçüldüğü gibi, sabit kalan bir hata ile
   büyüyen bir hata tamamen farklı sonuçlar doğurur. Dinamik koşu gerekiyor.

3. **Şok yok.** Ölçüm yumuşak bir basınç alanında yapıldı. Çarpma probleminde
   arayüzden **şok** geçecek; oradaki davranış ayrı bir sorudur.

---

## 6. Sırada ne var

| # | iş | neden |
|---|---|---|
| ~~4.1b~~ | ~~periyodik kutu~~ | **TAMAMLANDI (§3b)** — yeterli kenar payı yetti, taban `1,4e-15` |
| 4.1c | **Dinamik koşu**: N adım, enerji/momentum defteri | hata birikiyor mu? |
| 4.1d | **Şok geçişi**: arayüzden şok geçir, yansıma ve iletim ölç | çarpma probleminin gerçek sorusu |
| 4.2 | ADR-0041: yaklaşımın seçimi | ancak yukarıdakiler ölçüldükten sonra |

**Karar bu kayıtta verilmiyor.** Eldeki sayı umut verici ama düzeneğin
gürültüsü katkıyla aynı mertebede; ADR-0026 §2 "ölçümle seçilecek" diyor ve
bu ölçüm henüz seçim için yeterli değil.

---

## 7. Bu kayıttan çıkan süreç notu

Kampanyanın kuralları FAZ 4'ün **ilk gününde** iki kez işe yaradı:

1. Düzenekte K7 tekrarlandı (`ρ = 1800` vs çözücünün `2700`'ü) — kural
   *"kütle, çözücünün atadığı yoğunlukla tutarlı olmalı"* yakaladı.
2. İlk sınav **boş bir doğruydu** (`P = 0` → kuvvet özdeş sıfır) — ADR-0040
   *"bu koşulun düştüğü bir dünya var mı?"* yakaladı.

İkisi de **yeni yazılan kodda** oldu. Yani bu kurallar geçmişi temizlemek
için değil, **yeni işi doğru kurmak** için.
