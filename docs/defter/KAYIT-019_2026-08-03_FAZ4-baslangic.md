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

## 4. Ölçüm sonucu

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

1. **Derin bölge arayüzden daha kötü.** Ölçülen: `a_derin = 5,48e2` vs
   `a_arayüz = 2,48e2` (1:1'de). Yani baskın hata kaynağı **arayüz değil**,
   kafesin küre sınırıyla kesilmesi. Arayüz katkısı bu gürültünün içinde.
   Daha temiz bir düzenek (periyodik kutu, yüzeysiz) gerekiyor.

2. **`t = 0` anlık bir ölçümdür.** Asıl soru yapay kuvvetin **birikip
   birikmediği**. ADR-0028'de ölçüldüğü gibi, sabit kalan bir hata ile
   büyüyen bir hata tamamen farklı sonuçlar doğurur. Dinamik koşu gerekiyor.

3. **Şok yok.** Ölçüm yumuşak bir basınç alanında yapıldı. Çarpma probleminde
   arayüzden **şok** geçecek; oradaki davranış ayrı bir sorudur.

---

## 6. Sırada ne var

| # | iş | neden |
|---|---|---|
| 4.1b | **Periyodik kutu** düzeneği — yüzey etkisini tamamen kaldır | tabanı 0'a indirip arayüz katkısını yalnız bırakmak |
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
