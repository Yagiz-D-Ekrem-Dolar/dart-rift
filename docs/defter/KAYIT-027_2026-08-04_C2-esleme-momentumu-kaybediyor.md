# KAYIT-027 — C-2: örtüşmeli eşleme momentumu **kaybediyor** (2026-08-04)

**Kapsam:** FAZ 4.2 karar verisi · **Durum:** ölçüldü — **C'nin asıl riski
gerçek**
**Öncül:** [KAYIT-025](KAYIT-025_2026-08-04_C-eslemenin-bedeli.md) §5

---

## 0. KAYIT-025'in bıraktığı uyarı

> A ve A′ momentumu **tam** korur (`< 1e-12`), çünkü kuvvet biçimi
> antisimetriktir. **Örtüşmeli eşlemede bu güvence yoktur.** Hayaletler
> *dayatılır*, dinamik olarak eşleşmez. **C'yi seçmeden önce ölçülmesi
> gereken:** eşlenmiş sistemde momentum ne kadar kayıyor ve **birikiyor mu**?

Bu kayıt onu ölçer.

---

## 1. Korunum sorusu **referanssız** sorulabilir

Eşlenmiş sistemin toplam momentum değişimi:

```
Σ_A_gerçek m a^A  +  Σ_B_gerçek m a^B
```

Her alanın **gerçek–gerçek** etkileşimleri kendi içinde **antisimetriktir**
ve toplamda sadeleşir. Geriye **yalnızca hayalet kuvvetleri** kalır:

```
=  F(A_gerçek ← A_hayalet)  +  F(B_gerçek ← B_hayalet)
```

**Momentum korunuyorsa bu tam sıfırdır.** Tek parça referansına gerek yok.

**Şart:** `B_gerçek`, B'nin **tüm** hayalet-olmayan parçacıklarını içermeli.
İlk sürümde dış kabuğu dışlamıştım ve iç toplam sadeleşmiyordu — **S8'in kök
nedeni.**

### Zaman integrasyonu gerekmiyor

Kayma `t = 0`'da doğrudan ölçülür. Sıfırdan sapma, **her adımda** sisteme
giren sahte momentumdur.

---

## 2. İki yanlış formülasyondan geçti

| deneme | kıyas | ölçülen | neden yanlıştı |
|---|---|---|---|
| 1 | eşlenmiş **sıfıra** | 0,9789 (λ=2 **ve** λ=4 **aynı**) | alt kümenin fiziksel itmesi + dışlanan dış kabuk (**S8**) |
| 2 | eşlenmiş **tek parça ince**'ye | 0,15231 (λ=2), 0,00583 (λ=3) — **ters yön** | referans bir **çözünürlük** farkı da taşıyordu |
| **3** | **referanssız** (yukarıdaki özdeşlik) | aşağıda | — |

İkisini de **raporlamadan önce** yakalayan işaret aynıydı: *sayının kütle
oranıyla anlamsız davranması.*

---

## 3. Ölçüm (`half = 9`, `r_split = 5,5`, örtüşme `2h_kaba`, doğrusal rampa)

| λ | kütle oranı | n_A | n_B | boşluk kontrolü | **KAYMA** |
|---|---|---|---|---|---|
| **1,0** | **1:1** | 739 | 6120 | 2,670e-15 | **2,6696e-15** |
| 2,0 | 8:1 | 5497 | 6120 | 2,670e-15 | **7,4599e-03** |
| 3,0 | 27:1 | 18853 | 6120 | 2,670e-15 | **5,8491e-03** |

### Boşluk kontrolü **mükemmel** geçti

`λ = 1`'de iki alan **aynı** çözünürlüktedir; hayaletler ötekinin gerçek
parçacıklarının **birebir kopyasıdır**. Kayma `2,67e-15` — **makine sıfırı.**

> Bu, `λ > 1`'deki sayının **gerçekten eşlemeden** geldiğinin kanıtıdır.
> S8'de eksik olan tam da buydu.

---

## 4. Kayma **sistematik** — birikir

`λ = 2`'de kayma vektörü:

```
[5,0780e+09 ,  4,1788e-07 ,  -4,8630e-06]

|x| / |v|  =  1,000000        isaret: +  (rampa yonunde)
```

**Tamamen basınç gradyanı ekseninde.** Enine bileşenler `1e-16` düzeyinde.

> Kayma **rastgele değil**. Birbirini götürmez; adım sayısıyla **doğrusal**
> birikir. Rastgele olsaydı `√N` ile büyürdü — bu `N` ile büyür.

---

## 5. Büyüklük — ve kıyas

| yaklaşım | momentum artığı |
|---|---|
| A (global `h`) | `< 1e-12` (ölçülen `3,0e-16`) |
| A′ (parçacık başına `h`, dört şema) | `< 1e-12` (ölçülen `3,0–5,1e-16`) |
| **C (örtüşmeli eşleme)** | **`7,5e-03`** |

**On üç mertebe.** A ve A′ momentumu *cebirsel olarak* korur (antisimetri);
C onu **hiç korumaz**, yalnızca küçük tutar.

### Kütle oranıyla ilişkisi zayıf

`8:1` → `7,46e-03`, `27:1` → `5,85e-03`. Kütle oranını 3,4 kat artırmak
kaymayı **azaltıyor** (%22). Yani kayma, kütle oranının değil, **arayüzün
varlığının** bir işlevi — KAYIT-020 §2'deki gözlemin eşdeğeri.

---

## 6. Bunun anlamı — ve **anlamadığı**

### Söylenebilen

> **Örtüşmeli eşleme, bu prototipteki biçimiyle momentumu korumuyor ve
> kaybı sistematik olarak birikiyor.**

Bu, KAYIT-025'te *"C'de arayüz kaynaklı yapay kuvvet mekanizması yoktur"*
sonucunun **bedelidir**: C süreksizliği ortadan kaldırıyor ama bunu
**korunumu feda ederek** yapıyor.

### Söylenemeyen

1. **Bu, C'nin tek uygulaması değildir.** Korunumlu örtüşme şemaları vardır
   (karşılıklı kuvvet düzeltmesi, akı-tabanlı eşleme). Ölçülen şey **naif**
   hayalet biçimidir. Bir düzeltme terimiyle kapanıp kapanmayacağı
   **ölçülmedi**.
2. **Birikimin sonuca etkisi** ölçülmedi. `7,5e-03` göreli bir kuvvettir;
   `10⁴–10⁵` adımlık bir koşuda ne kadar hız kaymasına dönüştüğü ayrı bir
   hesap ister.
3. Prototipte hayaletler **tam** (ara değerleme hatasız). Gerçek bir
   uygulamada ara değerleme hatası (KAYIT-025 §3) **buna eklenir**.

---

## 7. Karar tablosu — beşinci güncelleme

| # | yaklaşım | mermiyi çözer | yapay kuvvet | şok geçişi | **momentum** | mimari bedel |
|---|---|---|---|---|---|---|
| ~~A~~ | global `h` | **hayır** | 0,168 | zararsız ✔ | **1e-16** ✔ | yok |
| **A′** | parçacık başına `h` | evet | 0,55–1,10 | (A'da zararsız) | **1e-16** ✔ | çekirdek+grid+CFL+Ω |
| **B** | bölme | A′ ile | = A′ | = A′ | = A′ | = A′ |
| **C** | iki alan eşlemesi | evet | yok | ölçülmedi | **7,5e-03 ✘ sistematik** | iki çözücü + örtüşme + MLS **+ korunum düzeltmesi** |
| **D** | kaynak terimi | **atlar** | yok | — | ✔ (tek çözücü) | ılımlı |

**C'nin mimari bedeli büyüdü:** artık bir de **korunum düzeltmesi**
gerekiyor, ve o düzeltmenin işe yarayıp yaramadığı ayrıca ölçülmeli.

**Kalan tek ölçüm: D-1** (kaynak teriminin model-form hatası).

---

## 8. Bu kayıtta uygulanan kurallar

| kural | nerede |
|---|---|
| soruyu **referanssız** sorabiliyorsan sor | §1 — antisimetri özdeşliği |
| bir sayının kütle oranıyla **anlamsız** davranması hatayı ele verir | §2 — iki kez |
| boşluk kontrolü **aynı düzeneği** sınamalı (`λ=1`) | §3 |
| büyüklük kadar **yön** de ölçülür | §4 — `\|x\|/\|v\| = 1` |
| ölçülen şeyin **hangi uygulama** olduğu yazılır | §6(1) — naif hayalet biçimi |
| ölçülmemiş sonuç **çıkarılmaz** | §6(2,3) |
