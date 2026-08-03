# KAYIT-018 — İkinci tur: veri tutarlılığı (2026-08-03)

**Kapsam:** K7–K12 · **ADR:** 0030–0033
**Sonuç:** 6 kusur; ikisi gigapaskal mertebesinde yapay gerilme üretiyordu.

> **Numaralandırma notu.** Bu kayıt kronolojik olarak KAYIT-017'den
> **öncedir** (ikinci tur, üçüncü turdan önce yaşandı) ama sonra yazıldı.
> Sıra bozulmasın diye içerik burada, çapraz atıflar iki yönlü.

---

## 0. Turun çıkış noktası

Birinci tur (KAYIT-016) hasarın **döngüsünde** bir kusur bulmuştu. Soru şuydu:

> Aynı sınıftan başka ne var? Bir büyüklük **iki yerde** yazılıysa ve
> ikincisi birincisinden **türetilmiyorsa**, er geç ayrışır.

Bu tek soru **altı kusur** buldu ve üçü üretim değerlerinde **tesadüfen**
tutuyordu — yani "şu an doğru" ama hiçbir şey onu doğru tutmuyordu.

---

## 1. K7 — Kütle ile gözeneklilik tutarsızdı

### Nasıl bulundu
ADR-0022 gerilmesiz başlangıç için `ρ·α = ρ₀_katı` şart koşuyor. Üretici ise
kütleyi **tekdüze** atıyordu (`m = bulk_density · V_p`). İkisi aynı anda doğru
olamaz. SPH'de parçacığın hacmi `m/ρ`'dur ve kafeste kapladığı hacme eşit
olmalı:

```
Σ_j (m_j / ρ_j) W_ij = 1        (birim bölünmesi)
```

### Ölçüm — h'den bağımsız
| h/spacing | M0 homojen | M1 matris | M1 blok |
|---|---|---|---|
| 1,3 | 1,0707 | 0,9837 | **0,7705** |
| 1,6 | 1,0677 | 0,9662 | **0,7842** |
| 2,0 | 1,0669 | 0,9519 | **0,8031** |

M0'daki sabit **+%6,7** tam olarak `1800/(2700/1,6) = 1,0667` — kusurun
**kapalı-form imzası**.

Aynı dizilim, iki yoğunluk yöntemi (ADR-0015 ikisini de destekliyor):

| | atanan ρ | toplam ρ | P (toplam ile) |
|---|---|---|---|
| matris | 1687,5 | 1800,4 | **1,117e+09 Pa** |
| blok | 2571,4 | 1800,4 | **−7,624e+09 Pa** |

Bloklarda **7,6 GPa yapay çekme**. Ablasyon karşılaştırması geçersizdi.

### Üretim konfigürasyonu kendi yorumuyla çelişiyordu
```yaml
rho0: 2700.0
bulk_density: 1800.0   # yorumu: "~%33 gözeneklilik" -> α = 1,5 demek
matrix_alpha0: 1.6     # -> yığın yoğunluğu 1687,5, 1800 DEĞİL
```

### Neden hiçbir kriter görmedi
- **C2** kütle bütçesini ölçüyor (`m` kullanır) → geçer
- **C3** gerilmesiz başlangıcı ölçüyor (`ρ` kullanır) → geçer
- **Tutarlılığa bakan kriter yoktu.**

### Çözüm
Kütle gözeneklilikten türer: `m_i = (ρ₀/α₀ᵢ)·V_p`. `bulk_density` bir
**hedef**; `matrix_alpha0` yerleştirmeden **sonra** ondan çözülür. Çelişik
değer verilirse **hata** — tutturan değeri de söyleyerek.

### Sonuç
| | M0 | M1 |
|---|---|---|
| çözülen α | **1,5000** | **1,7273** |
| hacim tutarlılığı | **[1,000000 ; 1,000000]** | **[1,000000 ; 1,000000]** |
| birim bölünmesi | 1,0002 | 1,0002 (blok dahil) |
| blok/matris kütle | — | **+%65** |

M0 için çözülen değer **tam 1,5000** — konfigürasyonun **kendi yorumundaki**
değerin ta kendisi. Doğru sayı zaten belgede yazılıydı, **parametrede yanlış
yazılmıştı.** Bloklar artık gerçekten ağır; önceden "blok" yalnızca bir
etiketti.

### Altın dosya mekanizması amacına uygun çalıştı
Karma `6d6f1d10` → `ca730c2c` değişti ve test **sessiz değişikliği durdurdu**.
ADR yazıldı, gerekçe `history`'ye işlendi, yeni karma **iki bağımsız ortamda**
doğrulandı (Linux/numpy 1.26.4, Windows/numpy 2.4.6) — **birebir aynı**.

---

## 2. K8/K9 — ADR-0030'un ortaya çıkardığı iki hasar kusuru

Kütleler heterojenleşince hasar modülünün hacim kullanımı sınandı. **İki
farklı hacim** vardı ve karıştırılıyorlardı.

**K8 — `r_s` gözenekleri saymıyordu.** `damage_ref.damage_rate` `r_s`'yi
açıkça *"çatlağın kat etmesi gereken uzunluk"* diye tanımlar; çatlak gözenekler
dahil bütün parçacığı geçer. Kod **katı** hacimden hesaplıyordu:
```
r_s mevcut = 3,8624 m    r_s doğru = 4,4214 m   -> %12,6 küçük
dD/dt ~ 1/r_s            -> hasar %14,5 HIZLI büyüyordu
```

**K9 — kusurlar hacimden bağımsız dağıtılıyordu.** `rng.integers` ile
**tekdüze** — yalnızca hacimler eşitken doğru. ADR-0030'dan sonra M1'de katı
hacim gerçekten değişiyor: **blok 344,8 · matris 209,6 m³ — %56 yayılım**.

Düzeltme sonrası: 2× hacim → **1,9775× kusur** (beklenen 2,0); tekdüze hacimde
iki yarı oranı **0,9977**. Deterministik ve tohuma duyarlı.

**Yan kanıt:** `geometrik hacim = m·α/ρ₀` her parçacıkta **tam olarak kafes
hacmi 362,04 m³** çıkıyor — ADR-0030 tutarlılığının bağımsız doğrulaması.

---

## 3. K10 — Crush tavanı skalerdi (turun en şiddetlisi)

### Belirti
ADR-0030 sonrası `test_esik_altinda_ve_yakinsadi` **kaldı** — settling
yakınsamıyordu.

### Testi düzeltmedim, ne değiştiğini ölçtüm
```
E_bağ = 1,703479e+06 J     eşik(1e-3) = 1,703479e+03 J
  40 adım: KE = 4,894274e+12 J   KE/E_bağ = 2,873e+06
 200 adım: KE = 3,896113e+09 J   KE/E_bağ = 2,287e+03
1000 adım: KE = 3,556281e+07 J   KE/E_bağ = 2,088e+01
```

KE, bağlanma enerjisinin **2,9 milyon katı**. Yerçekiminden gelemez:
`a(t=0) = 3,213e-05 m/s²` ile 0,0134 s'de `v ~ 4e-7 m/s` beklenirken ölçülen
**v_rms ≈ 78 m/s**. Enerji **başka bir yerden** giriyordu.

### Hipotez ve karşı-kontrollü ölçüm
Şüphe: `crush_alpha` tavanı malzemenin **skaler** `α₀`'ından alıyor (1,6),
yığının matrisi ise 1,7273.

| adım | malzeme tavanı 1,6 | malzeme tavanı 1,7273 |
|---|---|---|
| 0 | α=1,727253 · P=0 · KE=0 | α=1,727253 · P=0 · KE=0 |
| 1 | **α=1,600000** · KE=8,23e-08 | α=1,727253 · KE=8,23e-08 |
| 2 | **P=−1,1389e+09 Pa** · KE=3,36e+10 | P=−1,6e-04 · KE=2,70e-07 |
| 4 | P=−1,1294e+09 · **KE=8,29e+11** | P=5,1e-03 · **KE=9,66e-07** |

**KE oranı: 8,587e+17.** Hipotez doğrulandı.

### Kusur ne kadar eskiydi
**ADR-0030 onu görünür yaptı, ama hep vardı.** Önceden matris α₀ = 1,6
**tesadüfen** malzemeninkine eşitti; bloklar (1,05 < 1,6) geri-genleşme
yasağıyla korunuyordu. Model **yalnızca homojen gözeneklilik için**
doğruydu — oysa heterojen yığın tam olarak FAZ 3'ün ürettiği şey.

### Çözüm ve sonuç
Tavan parçacık başına (`alpha_ref`). Düzeltme sonrası:
```
40 adım: yakınsadı=True   KE/E_bağ = 3,360e-12   (önce 2,873e+06)
```
**1e18 katlık** düzelme.

---

## 4. K11 — Merminin distansiyonu sabit 1'di

Deseni **sistematik** aradım ve üçüncü örneğini buldum. Çözücü tek
malzemelidir (`ρ = ρ₀/α`), merminin yoğunluğu ise `impactor_density` ile
**ayrıca** veriliyor.

| `impactor_density` | `alpha0` | V_SPH / V_paketleme |
|---|---|---|
| 2700 | 1,0000 | 1,0000 |
| 3000 | 1,0000 | **1,1111** |
| 2000 | 1,0000 | **0,7407** |

%11–26 tutarsızlık, sessizce. **Ve mermi β'yı taşıyan bileşen.**

Üretim konfigürasyonunda ikisi de 2700 — **tesadüfen**.

**Çözüm:** `alpha_imp = ρ₀_katı / impactor_density`. Eşitken α = 1,0 **tam**
çıkar; mermi katıdan yoğunsa α < 1 gerekirdi — fiziksel değil, **açık hata**.

---

## 5. K12 — "Yığın yoğunluğu" iki farklı şeydi

Desenin daha yumuşak biçimi: aynı büyüklük iki yerde değil, aynı **ad** iki
hesap.

| şekil | dolum | A (mesh) | B (dolu) | A sapma |
|---|---|---|---|---|
| ikosfer r=100 s=9 | 0,9993 | 1798,80 | 1800,00 | −%0,07 |
| ikosfer r=60 s=8 | 0,9881 | 1778,51 | 1800,00 | **−%1,19** |
| ikosfer r=82 s=7 | 1,0044 | 1807,98 | 1800,00 | **+%0,44** |

Somut sonucu: `settle_pile` bağlanma enerjisini **kütleyi bir hacim
tanımından, yarıçapı diğerinden** alarak hesaplıyordu.

**Neden görünmüyordu:** test bandı `rel=0.05` — ayrımı yutuyordu.

**Çözüm:** iki tanım ayrı adlandırıldı; `discretised_volume`/`_radius`
eklendi; ilişki **toleranssız** (`rel=1e-12`) kapalı formda kilitlendi.

**Kavramsal duruş:** ayrıklaştırılmış cismin hacmi `N·V_p`'dir, `V_mesh`
değil. Mesh yalnızca bir **kalıp**tır.

---

## 6. Turun deseni

| # | büyüklük | yer 1 | yer 2 | sonuç |
|---|---|---|---|---|
| K7 | yığın yoğunluğu | `bulk_density` | `alpha0` | **−7,62 GPa** |
| K10 | başlangıç distansiyonu | `pile.alpha0` (dizi) | `porosity.alpha0` (skaler) | **−1,14 GPa** |
| K11 | mermi yoğunluğu | `impactor_density` | `ρ₀`/`alpha0` | %11–26 hacim |
| K12 | yığın yoğunluğu | mesh hacmi | dolu hacim | %1,19 |

**Dördü de üretim değerlerinde tesadüfen tutuyordu.**

### Kural
> Bir büyüklük iki yerde yazılıysa, ikincisi birinciden **türetilmeli** ya da
> ayrışma **hata vermeli**. Aynı **ad** iki hesabı taşıyorsa ikisi ayrı
> adlandırılmalı ve ilişki **kapalı formda** kilitlenmeli.
>
> **"Şu an aynı" bir güvence değildir.**

### Ve bir gözlem
K10, K8 ve K9 **ADR-0030'un düzeltmesi tarafından ortaya çıkarıldı**. Bir
düzeltme, gizli bir varsayımı görünür kılar. Bu yüzden her düzeltmeden sonra
"bu ne kırdı?" diye sormak, "bu ne düzeltti?" kadar önemlidir.
