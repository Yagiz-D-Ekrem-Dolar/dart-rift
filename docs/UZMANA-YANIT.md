# Uzman incelemesine yanıt — ne doğrulandı, ne yapıldı

**Tarih:** 2026-09-06 · **İnceleme:** `c94d74e` · **Yanıt:** bu commit

---

## Özet

Beş kod bulgusunun **beşini de bağımsız olarak ürettim; beşi de
gerçek.** Hepsi düzeltildi ve her biri için onu yakalayacak bir
sınav yazıldı (`tests/test_uzman_bulgulari.py`, `17` sınav).

İki fizik ölçümünüzü de ürettim ve **ikisi de tuttu.** Biri benim
bir çıkarımımı çürüttü; rapordaki yorumu düzelttim.

---

## 1. Beş kod bulgusu — doğrulama ve çare

### 1.1 Ensemble yanlış sahne sınıfıyla kuruluyor ✅

Ürettim. `sahne_taban=None` → `build_scene` varsayılanı `M0` →
`rubble_generator.py:406`'da `boulders = None`.

```
theta=(1,05; 1e4; 0,10) vs (1,30; 1e4; 0,40)
  x       BIREBIR AYNI: True
  m       BIREBIR AYNI: True
  alpha0  BIREBIR AYNI: True     benzersiz degerler: [1,0 ; 1,5]
  Y0      BIREBIR AYNI: True
```

`SAHNE` sabitinin kendisi `model_class = "M1"` taşıyor —
gönderilmiyordu. Önerdiğiniz düzeltme (`{**SAHNE, "root_seed": kök}`)
uygulandı; sonrası:

```
A.alpha0 benzersiz: [1 ; 1,05 ; 2,016]
B.alpha0 benzersiz: [1 ; 1,30 ; 1,6518]
```

**Sonuç:** bütün ensemble koşuları (`K5`, `L1`) fiilen tek eksenliydi.
O sırada `6` GPU'da koşan `L1` **iptal edildi**.

### 1.2 Rapordaki `β` ile ileri modelin `β`'sı farklı ✅

Sizin sentetik denetiminizi kurdum:

```
DEFTER (R,  hedef-özel):  beta_hedef = 1,280871   artık   = 0,000e+00
İLERİ  (2R, mermi dâhil): beta       = 1,000000   kapanış = 0,000e+00
n_ejekta (2R) = 0
```

Ek olarak şunu ölçtüm: `2R` yüzeyi bir **zaman süzgeci**. Yüzeyden
`2R`'ye `0,2 s`'te varmak `R/t = 410 m/s` gerektiriyor; kazı akışı
`0,1 – 10 m/s`. Yani çıkarıma giden gözlenebilir aradığımız sinyali
**yapısal olarak** göremiyordu.

**Çare:** `y[0]` artık defterin `beta_hedef`'i. Eski değer atılmadı.

### 1.3 Şok kapısı hedefte şok oluştuğunu doğrulamıyor ✅

İki ayrı kusur olduğunu buldum:

**(a) Mermi maskelenmiyordu** — sizin bulgunuz. Sınavla gösterildi:
hiç sıkışmamış bir hedef (`ρ = ρ₀/α₀`) kapıdan düşüyor; aynı hedefe
beş sıkışmış mermi parçacığı eklenince **geçiyor**. Düzeltildi.

**(b) Ölçüm zamanı** — bunu incelemeden önce bulmuştuk (rapor A45),
sizin 1. maddeniz doğruladı ve keskinleştirdi:

| büyüklük | değer |
|---|---|
| şok mermiyi geçme süresi `r_p/Us` | `6,0e-5 s` |
| `dt` | `≈ 5,4e-6 s` → geçiş **`≈ 11` adım** |
| iz aralığı | **`2 000` adım** |
| depodaki **en erken** iz | **`8,03e-3 s`** = geçişin `134` katı |

Ve `t = 0,2 s`'te hiçbir kolda `ρ > ρ₀ᵏᵃᵗⁱ` yok (`ρ_max/2700 = 0,960`).

### 1.4 Durum dosyaları birbirinin üzerine yazılıyor ✅

Diskteki kanıt: `24` noktalık `L1`'de dilim başına **tek**
`nokta_0000.npz`. Ad artık `θ`'nın SHA-256 özetini taşıyor.

### 1.5 Kaydedilen durum tanı için eksik ✅

Eklendi: `alpha, P, S, D, h, cs, strain`. `h` çözücüden **hiç**
dışarı verilmiyordu (`state_numpy` onu içermiyordu; `self.h` zaten
skaler özet, dizi `h_arr`).

Kimlik isteğinizi de uyguladım: `npz` artık `theta`, `surum`
(commit) ve `fizik_ozeti` (sahne + malzeme + merdiven + `spacing` +
`t_end`'in SHA-256'sı) taşıyor. Gerekçe: aynı commit'te farklı
bayraklarla koşulabiliyor, yani commit tek başına yetmiyor.

---

## 2. İki fizik ölçümünüz — ikisi de tuttu

### 2.1 `Y₀` çekmeyi hiç sınırlamıyor

| `Y₀` | EOS basıncı (`u=0`, `α=1,7564`, `ρ_s=0,999ρ_s0`) |
|---|---:|
| `1 Pa` | `−1,518635e+07` |
| `1e4 Pa` | `−1,518635e+07` |
| `1e7 Pa` | `−1,518635e+07` |
| `1e8 Pa` | `−1,518635e+07` |

**Yedi haneye kadar aynı.** Bu, `Y₀`'ın sekiz mertebede etkisiz
kalmasını (raporda A17/A45) tek başına açıklıyor.

### 2.2 `%45,34`'lük durum gevşemiş

Karşı örneğiniz (`α = 1,20848`, `ρ = 2234,22`, `u = 0`):
sıkışma **`%45,34`**, basınç **`8,33e4 Pa ≈ 0`**.

**Bu benim bir çıkarımımı çürüttü.** A45'te *"sıkışma donuk ⇒
şoklanan madde gevşemiyor"* yazmıştım. Yanlış: madde gevşemiş.
Rapordaki yorum düzeltildi, ölçümler yerinde bırakıldı.

Düzeltilmiş açıklama: **madde gevşemiş ama itecek basıncı da yok**
— ve genişlemeye kalkınca `−15 MPa` çekme geri çekiyor. Kraterin
`56 ms`'te durup sonra **kapanması** (`1,0409 → 1,0322 m`) buna
uyuyor.

---

## 3. Önerdiğiniz deney — kurdu, iki noktada ayrıldım

`--matris-cekme-yok` eklendi: EOS'un **hemen ardında** matris hedef
parçacıklarında `P < 0 → 0`. Kırpılan `P` kuvvet teriminde
`t = (S − P I)/ρ²` ve enerji işinde `du` **aynı** değer olarak
kullanılıyor — şartınız buydu. Bloklar ve mermi kırpılmıyor.

Beş sınavla kilitlendi; ilki *"maske verilmezse davranış BİT-AYNI"*.

### Ayrıldığım nokta 1: dallanma yerine `t = 0`

`8 ms`'te ortak durumdan dallanmayı önerdiniz. Depoda yeniden
başlatma düzeneği yok. İki kol `t = 0`'dan koşuyor — tek değişkenli
ama şok evresi de etkilenebilir. Bu karışıklığı **ölçerek**
kapatıyorum: her iki kolda `ρ_max`, `sikisma_max`, `n_kati_sikisan`
izleniyor. **Örtüşmezlerse deney sonuçsuz sayılıyor** ve dallanmalı
sürüm gerekiyor. Yargı kuralı koşudan önce commit'lendi
(`docs/truba/PROTOKOL-E2-CEKME.md`).

### Ayrıldığım nokta 2: gözeneklilik kolunu da düzelttim

14. maddeniz uyarınca `α₀ = 1` kolundan vazgeçtim. `--alpha-donuk`
eklendi: `porosity.enabled=False` **ama üretim `alpha0` dizisi
çözücüye olduğu gibi gidiyor**; EOS hâlâ `P = P_katı(αρ,u)/α`
kullanıyor, yalnız ezilme güncellemesi duruyor. Konumlar, kütleler,
`h`, başlangıç yoğunlukları **değişmiyor**.

---

## 4. İncelemeden sonra bulduğum bir kusur daha

`R3` (`N = 493 330`) çözünürlük kolu **bitemiyor**:

| kol | `N` | hız |
|---|---:|---:|
| `R2` | `69 886` | `2,81` adım/s |
| `R3` | `493 330` | **`0,062`** adım/s |

`7,06` kat parçacık için **`45,3` kat** yavaşlama. Sebebi
`solver_solid.py:84`: `support = 2·h_max` ve komşu sorgusu **her
parçacık için aynı yarıçapı** kullanıyor. Kademeli merdivende `h`
`16` kat aralığa yayıldığı için ince parçacıklar kaba bölgenin
yarıçapıyla tarıyor. Beklenen `7,06 × 8 = 56,5`, ölçülen `45,3`.

`t_end = 0,1 s` için `224` saat gerekiyor; iş sınırı `48`. İptal
edildi. Üç noktalı Richardson şimdilik mümkün değil.

---

## 5. Kalan sorular

1. **Granüler çekme davranışı.** Hipotez tutarsa üretim çözümü ne
   olmalı? `D = 1` kayma gerilmesini tamamen sildiği için uygun
   değil dediniz. Basınca bağlı sürtünmeyi koruyan hangi model?
   (Collins–Melosh–Ivanov? Jutzi'nin granüler dalı?)

2. **Yarıçapı parçacık başına yapmanın** doğru SPH pratiği ne?
   Çok seviyeli ızgara mı, `h_i`'ye bağlı sorgu mu? Bit-eşitliği
   ve determinizmi korumak istiyoruz.

3. `M(>v)` ölçümünü kurduk ama **kaçış ölçütünü** de değiştirmemiz
   gerekiyor: `r > R` yerine önerdiğiniz enerji ölçütü
   `ε = ½|v − V_kalan|² + Φ_kalan > 0`. `Φ_kalan`'ı yerçekimi
   kapalıyken nasıl kuruyorsunuz — analitik küre mi?

4. `β` hedefini `2,2 – 4,9` aralığı olarak alıyoruz artık.
   Karşılaştırmayı **`M(>v)` dağılımı** üzerinden yapmak, tek
   `β` sayısından daha mı savunulabilir sizce?
