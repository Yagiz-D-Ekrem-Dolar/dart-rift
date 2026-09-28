# KAYIT-070 — GPU'suz güçlendirme turu: gerçeklem saçılması, β(t) şekli, sahne tutarlılığı (2026-09-28)

**Kapsam:** ana koşu öncesi hata ayıklama · **Durum:** dört ölçüm (keşif) +
üç kod güçlendirmesi + iki yeni kusur · **Kaynak:** `kampanya/` mevcut
koşular (yeni koşu **yok**, 0 GPU-saat) · **Öncül:** KAYIT-069, ADR-0051,
ADR-0052

> **Bağlam:** kullanıcı ana koşu (~1000 GPU-saat) öncesinde önce GPU'suz
> işlerin bitirilmesini istedi. Bu turun tamamı **elde duran veriyle**
> yapıldı.

---

## 1. Gerçeklem saçılması ölçüldü — "kelebek" terimi

U/V havuzunda her `θ` **iki sahne tohumuyla** koşulmuştu (blok dizilimi
değişiyor, `θ` aynı). 15 geçerli çift:

| büyüklük | bağıl fark (ortanca) | sd kestirimi (`|fark|/√2`) |
|---|---|---|
| `β − 1` | `%4,6` (aralık `%0,9 – %8,1`) | **`%3,3`** |
| `M_ejekta` | `%20,9` | **`%15`** |

**Anlamı:** gerçek DART da blok diziliminin **tek bir gerçeklemesidir**.
Hiçbir model tek gözlemi `%3`'ten iyi tutturduğunu iddia edemez; bu terim
olabilirlikte yoksa posterior yapay olarak daralır (tek gerçeklemeye
overfit). `MODEL_EKSIKLIGI_KAYNAKLI`'ya **ölçülmüş** olarak eklendi
(`gerceklem_beta = 0,033`, `gerceklem_M_ejekta = 0,15`).

**İkincil sonuç:** `M_ejekta` beklediğimizden **zayıf** bir gözlenebilir.
Gözlemin kendi hatası `±%19` (`1,6 ± 0,3 × 10⁷ kg`), üstüne `%15`
gerçeklem gürültüsü biniyor. Dejenereliği kırma umudumuz azalıyor.

## 2. `β(t)` eğrisinin şekli fiziği sayısaldan ayırıyor

Mükemmel bir dejenerelik çifti bulundu (`β(300 s)` **tıpatıp aynı**):

| koşu | ne | `β` | `t50` |
|---|---|---|---|
| W2_Y1_g0p2 | `Y₀ = 1 Pa`, kaba | **4,023** | **1,60 s** |
| A104_k15 | `Y₀ = 10 Pa`, keskin çekirdek | **4,023** | **0,62 s** |

Kohezyonu 10 kat düşürmek ile çekirdeği keskinleştirmek aynı sayıyı veriyor;
eğrinin şekli ayırıyor. En ayırt edici ölçü `s(1 s)`:

| değişen | `Δ s(1 s)` |
|---|---|
| **fizik:** `Y₀` 10 → 1 Pa | **0,059** |
| sayısal: kaba → orta merdiven | 0,014 |
| sayısal: keskin çekirdek | 0,012 |
| sayısal: mermi 800 → 6400 | 0,003 |
| sayısal: uzak alan 7 → 3,5 m | 0,002 |

**Fizik sinyali / sayısal gürültü ≈ 4–5.** Aynı oran `β`'nın kendisinde
**≈ 1** (fizik `%12,5`, sayısal `%10,9`). Yani bugüne kadar kullandığımız
gözlenebilir, fiziği sayısaldan neredeyse hiç ayıramıyormuş.

**Sınırı açıkça:** `s(t)` gerçek DART'ta **ölçülemez** (yörüngeden yalnız
son `β` gelir). Bu yüzden çıkarımdaki dejenereliği kırmaz. Kırdığı şey:
bir sayısal ayarın literatürü **doğru sebeple** mi tutturduğunu sınamak.
Kod: `observables/impuls_sekli.py`.

**Üçüncü bulgu:** çekme dayanımı açıkken (`A105`) `t50 = 0,15 s` ve
`s(10 s) = 1,17` — yani momentum neredeyse tamamen 2 s içinde birikiyor ve
sonra geri iniyor. **Çekme açıksa geç evre şeması neredeyse gereksiz.**
A105 kararı yalnız `β`'yı `%23` değiştirmiyor, kampanyanın **tasarımını**
değiştiriyor.

## 3. Üretim sahnesi CPU'da kuruldu — iki tutarsızlık

Sahne `0,4 s`'de kuruluyor (CPU), DART geometrisi (elipsoit + `17°` +
üç küre mermi) **sorunsuz kuruluyor**: mermi `688 + 43 + 43` parçacık.

| | mevcut sahne (küre `R = 82`, `ρ = 1800`) | gerçek (Daly 2023) | fark |
|---|---|---|---|
| hacim | `2,31e6 m³` | `1,81e6 m³` | **+%27,6** |
| kütle | `4,17e9 kg` | `4,30e9 kg` | −%3,1 |
| yoğunluk | `1800` | `2376` | **−%24,2** |
| yüzey `g` | `4,13e-5` | `5,02e-5` | −%17,8 |
| kaçış hızı | `0,0823 m/s` | `0,0871 m/s` | −%5,6 |

Küre sahnenin **kütlesi** kabul edilebilir (−%3,1) ama hacmi ve yoğunluğu
değil. Asıl tehlike: **gerçek şekle geçilip yoğunluk aynı bırakılırsa kütle
`3,36e9 kg` olur (−%22)**. Gözlenen `β`, `4,3e9 kg` varsayılarak türetildi
(`period_interface.secondary_mass`) ve `β ∝ M`. O sahnenin `β`'sını gözlenen
`β` ile karşılaştırmak **sessiz bir hata** olurdu. → **A108**, ve kodda
denetim: `dart_gozlemleri.kutle_tutarliligi`.

## 4. A89 düzeltmesi: iki ayrı blok modeli var

Üretim varsayılanı `SAHNE` (`r_min = 14 m`, `r_max = 42 m`, `f = 0,25`) ile
bloklar **çözülüyor**: 7 blok, blok başına ortanca **231 parçacık**,
çözülmemiş **yok**. A89'un "`%99,3` çözülmemiş" ölçümü **başka bir
yapılandırmadadır** (`r 1,7–6,5 m`, `f = 0,275`, v2 üretici) — yani gözlenen
yüzey bloklarına benzeyen küçük bloklar.

Yani projede **iki farklı blok modeli** var ve üretimde hangisinin
kullanılacağı **kilitli değil**: büyük iç yapı blokları mı, gözlenen boyutta
küçük bloklar mı? İkisi `θ`'nın `f` ve `α_b` eksenlerine **farklı anlam**
veriyor. → **A109**.

## 5. Kod güçlendirmeleri (bu turda)

| ne | neden |
|---|---|
| `observables/impuls_sekli.py` | §2'nin ölçüsü tekrar üretilebilir olsun |
| `dart_gozlemleri.kutle_tutarliligi` / `yogunluk_kutleyi_tutturan` | §3'teki sessiz hata bir daha sessiz olmasın |
| `GridPosterior.aralik_kesin` | A85'siz merkezi aralık (düzgün dağılımda `%16` sınırı tam `0,16`); `hdi` **değişmedi**, kilitli yargılar korunuyor |
| `MODEL_EKSIKLIGI_KAYNAKLI` + iki gerçeklem terimi | §1 ölçümü olabilirliğe girebilsin |

## 6. Yapılamayan

P-v4 havuzunun ham verisi bu hesapta **yok** (eski `egitimg16u1`, okunamıyor).
Bu yüzden yeni kalibrasyon araçları (SBC, CV varyans ölçeği) **gerçek bir
havuzda** sınanamadı; yalnız sentetik sınavları var. Bu, ana koşudan sonra
ilk yapılacak işlerden biri olmalı.
