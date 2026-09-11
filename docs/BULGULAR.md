# DART-RIFT — bulgular ve durum

**Son güncelleme:** 2026-09-11

Bu belge projenin **ne kanıtladığını** ve **neyi kanıtlamadığını** tek
yerde toplar. Ayrıntılar `SONUC-*.md` belgelerinde; kusurların tam
dökümü `FAZ4-SIKINTI-RAPORU.md`'de (**61 açık kayıt**).

---

## 0. Uzman yanıtından sonra (2026-09-11) — ne değişti

Uzman üç kod kusuru buldu; üçü de bizim kodumuzda **ölçüldü**:

| kusur | ölçüm | yapılan |
|---|---|---|
| **A72** kuvvet, akma sınırını aşan gerilmeyi görüyor | birim sınavda `q/Y = 1 966`; **üretim koşusunda** zayıf matriste hedef kütlesinin `%27–42`'si akmanın `10⁴–10⁵` katını görüyor, kuvvetin gördüğü gerilme `Y₀`'dan bağımsız `~5e8 Pa` | `akma_kipi = "ara"`; orta ölçekte (I2) her noktada `q/Y = 1` |
| **A73** krater derinliği bir yüzey değil | dış kabuk sabitken `0,49 m`; 8× örnekleme `0,34 → 0,71 m` | `krater_yuzey`: aynı sınavlarda `8,9e-4 m` ve fark `0` |
| **A74** blok kesri sahneye ulaşmıyor | G1/G2'de nominal `0,05–0,48` → gerçek **`0,10–0,37`**; üç tohumda `0,43` ve `0,55` aynı geometri | `place_boulders_v2` (gerçek hacim kesri) + geometriden malzeme |

**A52** (çözünürlük kilidi): destek kutulu BVH + sıralı CSR yazıldı ve
sınandı; yerel GPU'da `3,73×`. H100 ölçümü bekleniyor.

**Protokol J koşuyor** (iş `1555356`, 84 görev): sabit `h`'de `Δt`
yarılanınca `x₀` kayıyor mu, `ara` bunu kaldırıyor mu. Ön koşul `O4`
**geçti**: yeni kodun varsayılan yolu G1'i 13/13 noktada **bit bit**
tekrar ediyor.

> J *"zaman adımı yolu gösterildi"* derse, G1'deki `Y₀ < 1e5` platosu
> ve I'daki `x₀` kayması **fizik değil sayısal yapıt** olabilir — ve
> ikisi de düzeltilebilir. J'nin yargısı gelmeden bu cümle bir
> **hipotez**.

---

## 1. Kanıtlanan

### 1.1 Motor doğrulaması

| sınav | durum |
|---|---|
| Sod şok tüpü (kesin Riemann çözümüne karşı) | ✅ |
| Sedov patlaması | ✅ |
| Tillotson Hugoniot'u | ✅ |
| Momentum ve enerji korunumu | ✅ makine hassasiyeti |
| CPU ↔ GPU bit-eşitliği | ✅ |

### 1.2 Şok gözlendi ve karakterize edildi

`E1a`, yoğun izlemeyle (`--iz-every 2`):

```
sikisma  %14,1 -> %69,2 -> %53,5      zirve t = 8,61e-05 s
ongoru   r_mermi/Us = 0,371/6145 = 6,0e-05 s
```

Şok gözeneklerin **`%96`'sını** kapatıyor (`ρ = 2601,6` →
`α = 1,038`) ve orada duruyor. Hiçbir kolda **temiz katı sıkışma**
yok.

> Depodaki tüm önceki ölçümler şoku **`134` kat geç** görmüştü
> (A45). Bu, ilk canlı gözlem.

### 1.3 Kazı akışını durduran kuvvet: **matris çekmesi**

Kontrollü deney (`E2`), ön koşul sağlandı — iki kolun şoku birebir
aynı (zirve `2601,6`, medyan bağıl fark `%0,007`):

| ölçü | üretim | çekme kırpık |
|---|---:|---:|
| yüzey `v_r` medyanı | **`−0,177 m/s`** | **`+0,094 m/s`** |
| yüzey `v_r` `p95` | `0,575` | **`13,8`** (`24×`) |
| cismin içinde `v_r > 10 m/s` | **`0`** | **`3 375` / `23 250 kg`** |
| krater derinliği (`24 ms`) | `0,780 m` | **`1,457 m`** |
| `Δβ_hedef` | `0,0352` | **`0,2715`** (`7,7×`) |

Etki `3 139` **en ince** parçacıktan geliyor — artefakt değil.

**Mekanizma ölçüldü (A51):** `Y₀` yalnız deviatorik gerilmeyi
sınırlıyor, Tillotson'un negatif hidrostatik dalını **değil**.

| `Y₀` | EOS basıncı |
|---|---:|
| `1 Pa` | `−1,518635e+07` |
| `1e8 Pa` | `−1,518635e+07` |

**Sekiz mertebe, yedi haneye kadar aynı.** *"Zayıf matris"*
kollarımız hiç zayıf değildi.

### 1.4 Ejekta dağılımı Housen–Holsapple'a oturuyor

Çekme kırpıldığında, dışarı hareket eden tüm madde sayılarak:

| `μ` ortalama | sapma | aralık | en düşük `R²` |
|---:|---:|---|---:|
| **`0,463`** | `0,016` | `0,432 – 0,492` | `0,9932` |

Sekiz farklı uydurma bandının **sekizi de** H&H'nin
`0,40 – 0,55` aralığında. Üretim kolunda dağılım **yok** — `12`
eşikte `3` farklı kütle değeri (basamak fonksiyonu).

### 1.5 Kazı akışı doğuyor ve ölüyor

| `t` | kaçan | `⟨v⟩` |
|---|---:|---:|
| `0,024 s` | `18 735 kg` | `−6,70 m/s` |
| `0,200 s` | `93 kg` | `−1 264 m/s` (jet) |

`176 ms`'te `18,7` ton madde `8 cm/s`'nin altına yavaşladı. Bütün
eski `t_end = 0,2 s` ölçümleri akışın **öldükten sonraki** hâlini
ölçmüş.

### 1.6 Gözlenebilir iç yapıyı **ayırt ediyor**

`G1`, üretim ayarı, `24 θ × 2` gerçeklem, `48` koşu, kilitli ölçüt:

```
F = 1006  (esik 4,0)
matris_Y0   rho = -0,9417   p = 0,0000   ANLAMLI
blok_alpha0 rho = -0,2348   p = 0,2690
blok_kesri  rho = +0,0904   p = 0,6674
YARGI: AYIRT EDIYOR
```

Fiziksel biçim bir **mukavemet rejimi geçişi**: `Y₀ < 1e5 Pa`'da
plato, üstünde dik düşüş. Sigmoid `R² = 0,941`.

> Bu sınav bugüne kadar **hiç geçerli yapılmamıştı** (A46: `θ`'nın
> üç bileşeninden ikisi sahneye ulaşmıyordu).

---

## 2. Kanıtlanmayan — ve nedeni

| iddia | durum | engel |
|---|---|---|
| `β` gözlenebilir olarak kullanılabilir | **hayır** | her ölçekte ayrıklaştırma tabanında |
| Uzamsal yakınsama (üç nokta) | **hayır** | A52: `R3` için `224` saat |
| `Y₀ = f(derinlik)` niceliksel eşlemesi | **hayır** | `%72` çözünürlük kayması (A69) |
| Üretim modelinde kazı akışı | **hayır** | granüler çekme modeli yok |
| `G2` (çekme kolu) ayırt ediyor mu | **evet** (`F = 25,4`, `ρ_Y₀ = −0,66`) | A70 ile okundu; `blok_kesri` `p = 0,084` (eşik altı) |
| `x₀` çözünürlüğe dayanıklı | **hayır** (ZAYIF, `2,44σ`) | A71; iki aday neden A72/A73 |
| Kuvvet akma sınırına uyuyor | **hayır** (üretimde `q/Y ~ 10²–10⁵`) | A72 — düzeltme yazıldı, J sınıyor |
| Krater ölçüsü bir yüzey | **hayır** | A73 — yeni operatör yazıldı |
| Blok kesri ekseni sahneye ulaşıyor | **kısmen** (`ρ(nominal, gerçek) = 0,97`, aralık sıkışık) | A74 — v2 yazıldı |

---

## 3. Yöntemsel bulgular — genellenebilir

Bunlar bu projeye özgü değil; aynı sınıf simülasyonları yapan
herkesi ilgilendiriyor.

| bulgu | ölçü |
|---|---|
| Yığın sıkışmasına dayalı şok kapısı, şokla kalıcı ezilmeyi **ayırt edemez** | Hugoniot bandı `%45,6–74,3`, gözenek tavanı `%75,64` — band tamamen altta |
| Son durumda değerlendirilen kapı, maddenin **doğru gevşediği** kolu reddeder | `%21,70 → %5,38`, `39/48` red, ve örneklem **güçlü matrise sapıyor** |
| Tek geç zamanda `β` ölçmek **cesedi ölçer** | `18,7 t @ 6,7 m/s` → `93 kg @ 1264 m/s` |
| Düşük yapay viskozitede kümelenme, katı sıkışma gibi görünür | oran `0,575` → `5,26×` sahte yoğunluk |
| Akma dayanımı `Y₀`, EOS'un çekme dalını **sınırlamaz** | `−15,19 MPa`, `8` mertebede sabit |
| `h_ij = (h_i+h_j)/2` çok çözünürlüklü aramayı kilitler | `7,06×` parçacık → `45,3×` yavaşlama |

---

## 4. Zincirin durumu

```
motor dogrulamasi        ✅
sok gozlemi              ✅
mekanizma teshisi        ✅  (cekme)
H&H kiyasi               ✅  (kosullu: cekme kirpik)
gozlenebilir var mi      ✅  (krater derinligi)
ayirt ediyor mu          ✅  (F = 1006, Y0 ekseni)
vekil model              ✅  (sigmoid, LOO RMSE 0,026 m)
posterior                ✅  (yontem gosterimi)
--------------------------------------------------
uzamsal yakinsama        ❌  A52
niceliksel kalibrasyon   ❌  A69
uretim modelinde akis    ❌  granuler cekme modeli
```

**Zincir uçtan uca çalışıyor**; kalibrasyonu yakınsamıyor.

---

## 5. Yöntem

- Her deneyin yargı kuralı **koşudan önce** commit'lendi
  (`docs/truba/PROTOKOL-*.md`), betikleri sınavlarıyla birlikte.
- Kilitli ölçüt üç kez beni **durdurdu**: `β` için `OKUNMAZ`
  (ön koşul), `F` için `SONUÇSUZ`, `E1` için *"çözücü kusuru"*.
- Kendi iddialarımı **üç kez** kendi verimle çürüttüm (A45 yorumu,
  A59→A61, A61→A62).
- **`56` kusur** ölçümüyle kayıtlı; çürütülen yorumlar silinmiyor,
  **geçersiz** işaretleniyor.

---

## 6. Bundan sonrası

| iş | açtığı | durum |
|---|---|---|
| Şok kapısı → zirve (A70) | `G2` okunabilir | ✅ **doğrulandı** (`47/48`) |
| `x₀` dayanıklılığı (Protokol I) | aktarılabilir nicelik | ❌ ZAYIF (A71) |
| Protokol J (`Δt` + `ara`) + I2 | A72'nin nedenselliği; `ara` ile `x₀` | **koşuyor** (iş `1555356`) |
| A52 — destek kutulu BVH | üç noktalı yakınsama | yazıldı, sınandı; H100 profili (iş K) |
| Fiziksel yüzey operatörü (A73) | doğru gözlenebilir | yazıldı; G1/G2/I'ya uygulanıyor (iş K) |
| Blok alanı v2 (A74) | çalışan `f` ekseni, fiziksel blok boyutu | yazıldı; kampanyada değil |
| Mermi EOS (A75) | doğru çarpan | **yapılmadı** |
| Granüler çekme modeli | üretimde kazı | `ara` + çekme sınırı ilk aday; ADR gerekiyor |
| Üç eksenli duyarlılık pilotu (uzman S13) | Bitiş 3'ün kapısı | tasarlanacak |
