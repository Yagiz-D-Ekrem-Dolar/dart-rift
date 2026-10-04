# ADR-0057 — **A109:** üretimde hangi blok modeli, ve `θ`'nın anlamı neye bağlı

**Durum:** ÖNERİ (karar kullanıcıda — **A109'un cevabı**) · **Tarih:** 2026-10-04
**Öncül:** **A109** (iki ayrı blok modeli var), **A89** (U/V'de bloklar
kütlece `%99,3` çözülmemiş), KAYIT-070 §4, KAYIT-073 §6 (ayrışma `α_b`/`f`
eksenlerinde ölçülmedi), L2 (Raducan ve diğ. 2024), Daly ve diğ. 2023
**Kod:** `setup/rubble_generator.build_rubble_pile`, `setup/blok_cozunurluk.py`

---

## 1. Ölçülen iki model

| yapılandırma | blok yarıçapı | blok sayısı | çözünürlük (kaba) |
|---|---|---|---|
| `SAHNE` varsayılanı (**DY2/DK/W2 bunu kullandı**) | `14 – 56 m` | 7 | ortanca **231** parçacık, çözülmemiş **yok** |
| U/V üretim koşuları | `1,7 – 6,5 m` | 2 387 | ortanca **1** parçacık, kütlece **`%99,3`** çözülmemiş |

Gözlem: Dimorphos yüzeyinde ölçülen bloklar **`0,16 – 6,5 m`**
(Daly ve diğ. 2023; en büyükleri Atabaque `6,5 m`, Bodhran `6,1 m`).

## 2. Önce bir **latent tuzak**: `θ`'nın anlamı sayısal aralığa bağlı

`build_rubble_pile`'da blok yarıçapı verilmezse:

    r_min = 2,0 × spacing        r_max = 8,0 × spacing

Yani **blok boyutu dağılımı fizikle değil, parçacık aralığıyla
tanımlanıyor.** `spacing = 7 m` → `14 – 56 m`.

Bu şu an bir hata **üretmiyor**: UY/UY2'nin kaba ve orta kolları **aynı
temel aralığı** (`--spacing 7.0`) kullanıyor ve merdiven yalnız kabukları
inceltiyor; yani iki kol **aynı cismi** kuruyor ve çözünürlük karşılaştırması
geçerli (denetlendi). Ama:

> **`spacing` bir gün değişirse `f` ve `α_b`'nin FİZİKSEL ANLAMI sessizce
> değişir** ve hiçbir yerde hata vermez. 650 GPU-saatlik bir havuzun
> parametrelerinin tanımı, bir sayısal ayara bağlı bırakılamaz.

**Öneri (her iki seçenekte de geçerli):** üretim protokolü `r_min` ve
`r_max`'ı **sayı olarak** yazar (`--r-min`/`--r-max`), varsayılan türetmeye
güvenmez. Bu bir karar değil, hijyen.

## 3. Karar (öneri): `SAHNE` varsayılanı + **açık kapsam sınırı**

**Üretim: bloklar `r ∈ [14 , 56] m`, `q = 3`, açıkça yazılı.**

Gerekçe:

1. **Çözülmüş bloklar, çözülmemiş bloklardan iyidir.** U/V'nin modelinde
   blokların kütlece `%99,3`'ü tek parçacık (A89): orada `α_b` (blok
   gözenekliliği) **hiçbir şey ifade etmiyor** — tek parçacığın
   gözenekliliği yalnız bir yoğunluk çarpanı. `f` de blok kesri değil,
   yoğunluk düzensizliği. Yani o modelle `θ`'nın iki ekseni **tanımsız**.
2. **Çözünürlük bunu değiştiremez.** `1,7 m` blokları çözmek için
   `~0,5 m` aralık gerekir: `(7/0,5)³ ≈ 2700` kat parçacık. UY2 orta
   merdiven bile `4,5` kat (havuz `750 → 3400 GPU-saat`). Bütçe yok.
3. **Literatür de iki ölçeği ayırıyor.** L1/L2 matrisi mikro-gözenekli,
   düşük kohezyonlu **homojen** malzeme sayıyor ve blokları **ayrı**
   gömüyor (bloklara `~10 MPa` çekme dayanımı veriyor). Yani "görünen
   yüzey blokları" ile "modelin blok bileşeni" literatürde de aynı şey
   değil.

### Kapsam sınırı — raporlarda **yan yana** yazılır

> Çıkarılan `(α_b, f)`, Dimorphos'un **`≳ 14 m` ölçeğindeki iç blok
> topluluğunu** tanımlar. Daly ve diğ. 2023'ün ölçtüğü **yüzey blokları**
> (`0,16 – 6,5 m`) bu çözünürlüğün **altındadır** ve çıkarımın
> erişiminde değildir. İkisi aynı şey diye sunulamaz.

Bu, iddiayı **küçültüyor** ama savunulabilir yapıyor. `14 m`'lik iç
bloklar hiçbir yüzey gözleminde görülmedi — görülemezdi de: gömülüler.
Varsayım açık: moloz yığınının boyut dağılımı yüzeyde gördüğümüzden
büyük ölçeklere uzanıyor. Bu **varsayım**, sonuç değil.

## 4. Ölçülmesi gereken (havuz zaten verecek, ek maliyet yok)

KAYIT-073 `β`'nın üç çarpanını `Y₀` ekseninde ölçtü ve **götürme** buldu.
`α_b` ve `f` eksenlerinde götürme var mı **bilinmiyor**. Havuz bunu ek
maliyetsiz verecek: `ejekta_ayrismasi` artık her koşuya yazılıyor.

**Niçin bu A109'u ilgilendiriyor:** eğer `α_b` ve `f`, `M_kaçan`'ı
`v_ort`/`kos_ort`'un tersi yönde değiştiriyorsa, `β` o eksenlerde de kör
olur ve `(β, M_ejekta)` çiftiyle bile ayrışmazlar. O durumda blok modeli
seçimi (hangi ölçekte bloklar) posterioru değil **kapsamı** belirler:
"çözemediğimiz bir eksen" olur. Havuzdan sonra `tanimlanabilirlik.py`
bunu sayıyla söyleyecek.

## 5. Reddedilen seçenekler

- **U/V'nin modeli (`1,7 – 6,5 m`).** `θ`'nın iki ekseni tanımsız olur
  (A89: kütlece `%99,3` çözülmemiş). Gözlenen boyutlara uymak,
  **çözülmeden** uymak değildir.
- **Ara bir aralık (`7 – 21 m`).** `7 m` bloklar `spacing = 7 m`'de
  ortanca `~4` parçacık: bıçak sırtı, hem de A114'le aynı türden
  (çözünürlüğün eşiğinde duran bir nicelik). Kaçınılır.
- **İki modeli de koşup posteriorları karşılaştırmak.** Bilimsel olarak
  en güçlüsü; maliyet **iki kat** (`~1500 GPU-saat`) ve `1500` toplam
  sınırını yer. Reddedilme nedeni bütçe, bilim değil — ve bu
  **yazılıyor**.
- **Varsayılan `2–8 × spacing` türetmesine güvenmeye devam etmek.**
  §2'de gerekçesiyle reddedildi: `θ`'nın anlamı sayısal ayara bağlı
  kalamaz.
