# KAYIT-020 — Arayüz hatası nicelendi: düzensizlikle kıyaslama (2026-08-04)

**Kapsam:** FAZ 4.1 · **Durum:** ölçüm bitti, **4.2 kararı için tek eksik**
gerçek yığının düzensizliği
**Öncül:** [KAYIT-019](KAYIT-019_2026-08-03_FAZ4-baslangic.md) §3b (maske düzeltmesi)

---

## 0. Bu kayıt neyi kapatıyor

KAYIT-019 §3b arayüz katkısını **yalnız bıraktı** (taban `1,4e-15`). Ama
yalnız bırakılmış bir sayı hâlâ yorumlanamaz: **`0,21` büyük mü küçük mü?**

Bu kayıt o soruyu üç ölçümle yanıtlıyor:

1. Hata **sistematik mi rastgele mi**? → arayüzü sürükler mi?
2. Hata **neyle ölçekleniyor**? → gerçek problemdeki göreli zararı ne?
3. **Doğru taban ne?** → mükemmel kafes değil, **düzensiz** paketleme.

Üçüncüsü kararı tersine çevirdi.

---

## 1. Ölçüm aracının kendi kalibrasyonu

YÖNTEM'in kuralı: *"ölçüm aracını da kalibre et."* Bu kez araca **kendi
sınavı** kondu.

SPH'in simetrik kuvvet biçimi **antisimetriktir**: `f_ij = −f_ji`. Öyleyse
`Σ mᵢaᵢ` **tam sıfır** olmak zorundadır. Sıfır değilse hata arayüzde değil,
**çözücüde**dir.

| kütle oranı | `‖Σmᵢaᵢ‖ / Σmᵢ‖aᵢ‖` |
|---|---|
| 1,00 | 4,50e-17 |
| 2,00 | 2,56e-16 |
| 2,99 | 1,70e-17 |
| 4,02 | 4,63e-17 |
| 8,00 | 3,23e-16 |
| 16,00 | 8,52e-17 |

**Makine hassasiyeti.** Momentum korunumu kütle oranından **etkilenmiyor** —
bu, aşağıdaki sayıların çözücü hatası değil, ayrıklaştırma hatası olduğunu
gösterir.

> Bu bir yan sonuç değil, **ön koşuldur**: bu satır bozuk olsaydı
> aşağıdaki hiçbir sayı yorumlanamazdı.

---

## 2. Hata sistematik mi, rastgele mi?

Maksimum **tek bir parçacığı** gösterir. Asıl soru: hata arayüzü bir yöne
**sürüklüyor** mu, yoksa birbirini **götürüyor** mu? Ölçülen: işaretli radyal
bileşenin ortalaması / RMS.

| oran | a_maks | a_rms | a_p50 | a_radyal_ort | **sistematik oran** |
|---|---|---|---|---|---|
| 1,00 | 1,3013e-11 | 6,8097e-12 | 5,1618e-12 | −6,2394e-13 | 0,0916 |
| 2,00 | 1,2349e+03 | 7,5816e+02 | 6,6193e+02 | +1,0359e+02 | 0,1366 |
| 2,99 | 2,7995e+03 | 1,2063e+03 | 7,4008e+02 | +6,1423e+00 | 0,0051 |
| 4,02 | 2,0837e+03 | 9,4056e+02 | 6,5463e+02 | +1,3885e+01 | 0,0148 |
| 8,00 | 2,0240e+03 | 1,3158e+03 | 1,2557e+03 | −1,2257e+02 | 0,0931 |
| 16,00 | 1,8798e+03 | 1,2079e+03 | 1,1225e+03 | −1,2293e+02 | 0,1018 |

### İki ayrı okuma

**(a) Yönlü bileşen küçük.** Sistematik oran %0,5–14. Yani hatanın
**%86–99,5'i yönsüz** — arayüzü topluca itmiyor.

**(b) Ama birkaç aykırı parçacık değil.** `a_p50` (medyan) `a_maks`'a çok
yakın: 8:1'de `1,2557e+03` vs `2,0240e+03`. Yani hata **arayüzün tamamına
yayılmış**. Bir avuç bozuk komşuluk olsaydı medyan sıfıra yakın olurdu.

**Sonuç:** arayüz bir *kuvvet* uygulamıyor, bir *gürültü tabakası* yaratıyor.
İşaret 8:1 ve 16:1'de **negatife** (içe) dönüyor — orada ~%10'luk tutarlı bir
sıkıştırma bileşeni var.

---

## 3. Hata neyle ölçekleniyor — ve bu neden kötü haber

Uygulanan basınç 16 kat tarandı (`eps = 0,0025 … 0,04`), 8:1 sabit:

| eps | P_uygulanan | a_rms | **a_rms / P** | a/ölçek |
|---|---|---|---|---|
| 0,0025 | 6,6917e+07 | 3,3142e+02 | 4,9527e-06 | 0,2139 |
| 0,0050 | 1,3417e+08 | 6,6119e+02 | 4,9281e-06 | 0,2129 |
| 0,0100 | 2,6967e+08 | 1,3158e+03 | 4,8795e-06 | 0,2108 |
| 0,0200 | 5,4468e+08 | 2,6059e+03 | 4,7842e-06 | 0,2066 |
| 0,0400 | 1,1107e+09 | 5,1115e+03 | 4,6020e-06 | 0,1988 |

`a_rms/P` 16 kat aralıkta **%6 içinde sabit**.

### Bunun anlamı

Yapay ivme **mutlak basınçla** ölçekleniyor, basınç **gradyanıyla** değil:

```
a_yapay  ≈  0,21 · P / (ρ·h)
a_fiziksel ≈ |∇P| / ρ  ≈  P / (ρ·L)      (L = gradyanın uzunluk ölçeği)

a_yapay / a_fiziksel  ≈  0,21 · L / h
```

**Alan ne kadar düzgünse hata o kadar baskın.** `L = 10h` ise yapay kuvvet
fizikselin **iki katı**; `L = 50h` ise **on katı**. Çarpma bölgesinde `L ~ h`
olduğu için orada sorun yok — ama **uzak alanda**, ejektanın yavaşça
salındığı bölgede tam tersi.

> Bu tek başına A yaklaşımına karşı ağır bir bulgudur. §4 onu hafifletiyor —
> ama ortadan kaldırmıyor.

---

## 4. Doğru taban mükemmel kafes değil

§3'e kadarki her sayı **mükemmel FCC** kafeste ölçüldü. Ama **gerçek moloz
yığını mükemmel FCC değildir**: yerçekimi altında oturur, sınırla kesilir,
kayaları farklı yoğunluktadır.

Öyleyse doğru soru şu değil:

> ~~"Arayüz sıfıra göre ne kadar hata katıyor?"~~

Şu:

> **"Arayüz, ZATEN VAR OLAN düzensizlik hatasına ne kadar ekliyor?"**

Bu, K18'in dersinin üçüncü uygulaması — ama bu kez taban ne ölçüm aracından
ne de yüzeyden geliyor, **fiziğin kendisinden** geliyor.

### Ölçüm: eşit kütle (1:1), yalnızca konum sarsıntısı

| sarsıntı (aralık kesri) | a_rms | a_maks | **a/ölçek** |
|---|---|---|---|
| 0,00 | 6,8097e-12 | 1,3013e-11 | 0,0000 |
| 0,01 | 1,9881e+02 | 4,6457e+02 | 0,0484 |
| 0,02 | 4,2400e+02 | 9,1384e+02 | 0,0952 |
| **0,05** | **1,0274e+03** | 2,5016e+03 | **0,2605** |
| 0,10 | 2,0725e+03 | 4,7851e+03 | 0,4983 |
| 0,20 | 3,8378e+03 | 8,3178e+03 | 0,8661 |

**Kıyas: 8:1 arayüz, mükemmel kafes → `a_rms = 1,3158e+03`, `a/ölçek = 0,2108`.**

**%5 konum sarsıntısı, 8:1 kütle oranından daha fazla yapay kuvvet üretiyor.**

---

## 5. Karar ölçümü: ikisi bir arada

Sarsıntı ile arayüz **birlikte** ölçüldü. Her seviyede **aynı tohum**; tek
değişen kütle oranı. Sarsıntı **yerel aralıkla** ölçekleniyor (ince bölge
ince sarsılıyor) — yoksa iki bölge farklı düzensizlikte olurdu.

| sarsıntı | 1:1 a_rms | 8:1 a_rms | **artış** | 1:1 a/ölçek | 8:1 a/ölçek |
|---|---|---|---|---|---|
| 0,00 | 6,8097e-12 | 1,3158e+03 | ∞ | 0,0000 | 0,2108 |
| 0,02 | 4,0424e+02 | 1,3188e+03 | 3,26× | 0,0969 | 0,2279 |
| 0,05 | 1,0070e+03 | 1,4255e+03 | 1,42× | 0,2421 | 0,3291 |
| **0,10** | 1,9912e+03 | 1,7963e+03 | **0,90×** | 0,4714 | 0,5460 |

### Okuma

- **%10 düzensizlikte 8:1 arayüz RMS'i artırmıyor** (0,90×) — arayüz katkısı
  düzensizlik gürültüsünün içinde kayboluyor.
- Toplama **kareler toplamından bile az**: %5'te beklenen
  `√(1007² + 1316²) = 1657`, ölçülen **1426**. Hatalar kısmen **birbirini
  götürüyor**.
- Ama **maksimum** her seviyede ~`+0,08` artıyor. RMS ile maksimum farklı
  şeyler söylüyor ve ikisi de rapor ediliyor.

---

## 6. Şu ana kadarki yargı — ve neyin eksik olduğu

### Söylenebilen

1. Arayüz hatası **gürültü tabakasıdır**, yönlü kuvvet değil (%86–99,5 yönsüz).
2. Mutlak basınçla ölçeklenir → **düzgün alanlarda göreli olarak kötüdür**
   (`0,21·L/h`).
3. **Gerçekçi düzensizlik varken ikinci mertebeye düşer**: ≥%5 sarsıntıda
   RMS katkısı ≤%42, %10'da ölçülemez.
4. Momentum korunumu kütle oranından **etkilenmiyor** (1e-16).

### Söylenemeyen — ve 4.2 kararının beklediği

| # | eksik | neden karar için gerekli |
|---|---|---|
| **E1** | **Gerçek oturmuş yığının sarsıntısı kaç?** | §5 tablosunda hangi satırda olduğumuzu bilmiyoruz. %2 ise arayüz 3,26× katıyor; %10 ise hiç katmıyor. **Karar tamamen buna bağlı.** |
| E2 | Dinamik birikim | statik ölçüm `t = 0` anlıktır. Sabit bir yapay ivme hızı **doğrusal**, konumu **karesel** büyütür. |
| E3 | Şok geçişi | ölçüm yumuşak alanda yapıldı; çarpmanın asıl sorusu arayüzden geçen şoktur. |

**E1 bir sonraki iştir** ve ucuzdur: FAZ 3'ün ürettiği gerçek yığına aynı
sondayı uygulamak yeter.

---

## 7. Bu kayıtta uygulanan kurallar

| kural | nerede |
|---|---|
| ölçüm aracını kalibre et | §1 momentum artığı |
| boşluk kontrolü | §5'te 1:1 satırı — 0,00 sarsıntıda taban gerçekten sıfır |
| ölçüm = taban + sinyal (K18) | §4 — doğru tabanın **fizikten** geldiği fark edildi |
| maksimum tek parçacığı gösterir | §2 — medyan/RMS ayrı raporlandı |
| tek değişken değiştir | §5 — aynı tohum, yalnızca `λ` değişiyor |
