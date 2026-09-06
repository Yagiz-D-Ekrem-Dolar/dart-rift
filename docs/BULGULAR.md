# DART-RIFT — bulgular ve durum

**Son güncelleme:** 2026-09-06

Bu belge projenin **ne kanıtladığını** ve **neyi kanıtlamadığını** tek
yerde toplar. Ayrıntılar `SONUC-*.md` belgelerinde; kusurların tam
dökümü `FAZ4-SIKINTI-RAPORU.md`'de (**56 açık kayıt**).

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
| `G2` (çekme kolu) ayırt ediyor mu | **bilinmiyor** | şok kapısı `39/48` reddetti (A68) |

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

| iş | açtığı | maliyet |
|---|---|---|
| Şok kapısı → zirve (**A70, yapıldı**) | `G2` okunabilir olabilir | ✅ ama **doğrulanmadı** |
| `x₀` dayanıklılığı (Protokol I, **koşuyor**) | aktarılabilir tek nicelik | `~2` saat |
| A52 — parçacık başına arama yarıçapı | üç noktalı yakınsama | haftalık, riskli |
| Granüler çekme modeli | üretimde kazı | haftalık, ADR gerekiyor |

Son iki iş bu turda **yapılamaz** ve öyle bildiriliyor.
