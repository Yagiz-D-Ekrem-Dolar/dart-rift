# Kusur kaydı — bulunan her kusurun tam dökümü

Bu belge, hata ayıklama turlarında bulunan **her kusuru** rapor yazımına
doğrudan girecek ayrıntıda tutar. Her kayıt aynı şablonu izler:

> **belirti** → **nasıl bulundu** → **ölçülen etki** → **kök neden** →
> **neden hiçbir test görmedi** → **düzeltme** → **düzeltme sonrası ölçüm** →
> **yapısal önlem** → **kanıt**

Kural: **hiçbir sayı tahmin değildir.** Buradaki her rakam bir koşudan
gelir ve iş numarası ile commit'i yazılıdır.

---

## Özet tablo

| # | modül | kusur | ölçülen etki | ADR | durum |
|---|---|---|---|---|---|
| K1 | `warp_core/damage_gradykipp` | Hasar `S` **durum** değişkenini yerinde çarpıyordu | hiçbir fizik yokken **S: 1,0e7 → 4,88e3** (5 adımda, **1000 kat**) | 0029 | ✅ |
| K2 | `observables/crater_shape` | Referans tek sayı → cisim **küre** sanılıyordu | **kratersiz** elipsoitte **9,04 m hayali krater**; bilinen 8 m çukur **17,43 m** | 0029 | ✅ |
| K3 | `observables/momentum_transfer` | Duyarlılık taramasının **hız ekseni ölüydü** | `beta_spread_speed_axis = 0,0` — kriter yine geçiyordu | 0029 | ✅ |
| K4 | `observables/momentum_transfer` | Varsayılan hedef yarıçapı `median(dist)` | yarıçap **%21 küçük**, v_kaçış **%12,3 büyük** | 0029 | ✅ |
| K5 | `observables/period_interface` | Belgede `dv/v ~ 1e-3` | gerçek **1,72e-02** — **17 kat** | 0029 | ✅ |
| K6 | `tests/test_scene_checks` | `2.5 < beta < 4.5` bandı | β=3,22 ile β=3,6'yı **ayırt edemiyor** | 0029 | ✅ |
| K7 | `setup/rubble_generator` | Kütle tekdüze, yoğunluk parçacık başına → **tutarsız** | birim bölünmesi blok **0,77**; toplam yoğunlukla **−7,624e+09 Pa** yapay çekme | 0030 | ✅ |
| K8 | `warp_core/solver_solid` | `r_s` **katı** hacimden (gözenekler sayılmıyor) | r_s **%12,6 küçük** → hasar **%14,5 hızlı** | 0030 ek | ✅ |
| K9 | `cpu_reference/damage_ref` | Kusurlar **hacimden bağımsız** dağıtılıyordu | kusur hacmi **%56 yayılım**, dağıtım tekdüze | 0030 ek | ✅ |
| S1 | `tests/test_settling` | *Turun kendi hatası:* Y0 testinin **tahmini ters** | ölçülen 130 kat **ters yönde** | — | ✅ |

---

## K1 — Hasar, `S` durum değişkenini bozuyordu

**Modül:** `src/dartrift/warp_core/damage_gradykipp.py` · **Şiddet:** kritik

### Belirti
Yok. Bütün testler geçiyordu (34 hasar testi dahil), G3 7/7, kırmızı takım 14/14.

### Nasıl bulundu
Yöntem: **fiziği dondur, değişmemesi gerekeni ölç.** `D = 0,5` sabitlendi,
hiçbir gerinim üretmeyen kurulum yapıldı ve `_eval()` art arda çağrıldı.
Fizik durduğuna göre `S` sabit kalmalıydı.

### Ölçülen etki (iş 1446269, H100)
```
S[0,0,1] başlangıç : 1.000000e+07
1. _eval() sonrası : 5.000000e+06     <-- beklenen SABİT 5.0e+06
2. _eval() sonrası : 2.500000e+06
3. _eval() sonrası : 1.250000e+06
4. _eval() sonrası : 6.250000e+05
adım 5 sonrası     : 4.882812e+03     <-- 1000 kat sapma
```

### Kök neden
```python
S[i] = f * S[i]        # f = 1 - D   — YERİNDE çarpım
```
`S` bir **durum** değişkenidir: `kick_S_3d` ile integre edilir, hiçbir yerde
yeniden hesaplanmaz. `_eval()` ise KDK adımı başına **iki kez** çağrılır.
Sonuç: her adımda `S ← (1−D)² S`, birikimli. `P` kurtuluyordu çünkü EOS onu
her eval yeniden hesaplıyor.

### Neden hiçbir test görmedi
Hasarın bütün testleri *"hasar sonucu değiştiriyor mu?"* diye soruyordu.
Değiştiriyordu — **ama yanlış nedenle**. Formül testlerinin hepsi doğruydu;
hiçbir formül yanlış değildi. Kusur **döngüdeydi**.

### Düzeltme
Hasar ayrı `P_eff`/`S_eff` dizilerine yazar; durumu okur, yazmaz. Kuvvetler
taşınan gerilmeyi görür, `kick_S_3d` ham `S`'yi evrimler. Hasar kapalıyken
ek dizi yok, ek maliyet yok.

### Düzeltme sonrası ölçüm (iş 1448947, H100)
```
1..4. _eval(): S(DURUM)=1.000000e+07   S_eff(TAŞINAN)=5.000000e+06
adım 1..5    : S(DURUM)=1.000000e+07   (sabit)
```

### Yapısal önlem
- `tests/test_solver_idempotence.py` — **`_eval()` saf bir fonksiyondur**:
  iki ardışık çağrı sonrası tüm durum dizileri bit düzeyinde aynı. Üç yolda
  (hasar kapalı / açık / hepsi açık).
- `cpu_reference/solid_ref.py` artık hasar **döngüsünü** içeriyor;
  `TestDamageCross` GPU↔CPU'yu 10 adım karşılaştırıyor. **Bu referans yoktu**
  — kusurun yaşadığı boşluk tam olarak buydu.

### Kanıt
İş 1446269 (kusur), 1446277 (düzeltme), 1448947 (tam doğrulama).

---

## K2 — Krater çıkarıcı cismi küre sanıyordu

**Modül:** `src/dartrift/observables/crater_shape.py` · **Şiddet:** kritik

### Belirti
Yok. Krater testlerinin hepsi geçiyordu.

### Nasıl bulundu
Modülün kendi belgesi ile kodu karşılaştırıldı. Belge:
> *"θ > θ_dış olan yüzey parçacıklarıyla bir REFERANS yarıçap profili
> R_ref(θ) **uydurulur**"*

Kod: `prof_ref = np.full(n_bins, r_ref_global)` — **tek sayı**.

Sonra: kratersiz bir cisme çıkarıcı uygulandı. Kürede 0 veriyordu (bütün
testler o yüzden geçiyordu); **Dimorphos elipsoidinde** değil.

### Ölçülen etki (kratersiz elipsoit, 88×87×65 m — doğru cevap 0 m)
| çarpma ekseni | derinlik | çap |
|---|---|---|
| kısa (z) | **9,04 m** | 66,76 m |
| uzun (x) | 1,46 m | 0,00 m |

Bilinen 8 m'lik çukur kazılınca: **17,43 m** — iki kat şişirme.
Cismin yarıçapı zaten kendiliğinden ~11,5 m oynuyor.

### Kök neden
Cisim küre kabul ediliyordu. Dimorphos küre değil: eksenler arası **%26** fark.

### Neden hiçbir test görmedi
Krater çıkarıcının **bütün** sınavları küre üzerindeydi: bilinen kalot,
küresel büzüşme (RT9), az örneklenen kutular. RT9'un adı *"küresel deformasyon
krater sayılıyor mu"* ama izotropik büzüşme referansa zaten girer; asıl tehlike
cismin **kendi şekli**ydi ve o hiç sınanmamıştı.

### Düzeltme
Referans, cismin **kendi çarpma öncesi şekli**. `x_reference` verilirse
`R_0(θ)` aynı kutulama ve aynı eksenle ölçülür; çarpma dışı bölgede ölçülen
küresel ölçek kayması referansa eklenir. Verilmezse eski davranış sürer ama
`reference_is_spherical` tanısı **açıkça** `True` döner.

### Düzeltme sonrası ölçüm
| | küresel referans | çarpma öncesi referans |
|---|---|---|
| kratersiz elipsoit | 9,04 m | **0,000 m** |
| bilinen 8 m çukur | 17,43 m | **8,66–9,04 m** |

Kalan %8–13 fazlalık yeni kusur değil: `surface_particles`in bilinen örneklem
yanlılığı (aynı etki küre testinde de türetilmişti: 20 m → 21,1 m, +%5,5).

### Yapısal önlem
`run_crater_irregular_selftest` — G3 C5 ve RT9 artık düzensiz cisim
senaryosunu **şart koşuyor**.

### Kanıt
İş 1448947, RT9 kanıtı loglarda.

---

## K3 — β duyarlılık taramasının hız ekseni tamamen ölüydü

**Modül:** `src/dartrift/observables/momentum_transfer.py` · **Şiddet:** yüksek

### Nasıl bulundu
Toplam yayılım yerine **eksen başına** yayılım ölçüldü.

### Ölçülen etki
```
beta_spread_radius_axis = 0,2189
beta_spread_speed_axis  = 0,0000     <-- TAM SIFIR
```
Sebep: o senaryoda kaçış hızı **0,0803 m/s**, en yavaş ejekta **0,2 m/s**;
en yüksek eşik (2×) **0,161 m/s** bile hiçbir parçacığı eleyemiyor.

### Neden hiçbir test görmedi
**Toplam yayılım pozitif olduğu için** G3 C5 ve RT10 geçiyordu — hız eşiği
kod yolu hiç koşulmadan. RT12 ile aynı sınıf: doğru sonuç, yanlış sebep.

### Düzeltme
`beta_sensitivity` artık **eksen başına** yayılım ve `*_axis_active` raporlar.
`run_speed_threshold_selftest` hızları kaçış hızının etrafına yayar.

### Düzeltme sonrası ölçüm
```
hız ekseni yayılımı = 0,3209
beta: 1,735 → 1,633 → 1,414   (eşikle MONOTON azalıyor)
ejekta sayısı: 2265 → 1535 → 748
```

---

## K4 — Varsayılan hedef yarıçapı %21 küçüktü

**Modül:** `src/dartrift/observables/momentum_transfer.py` · **Şiddet:** orta

### Ölçülen etki (300k parçacık, R = 100 m düzgün dolu küre)
```
median(dist) = 79,294 m       (kuramsal 79,370 = R/2^(1/3))
v_kaçış      = %12,3 BÜYÜK    (v ~ 1/sqrt(R))
r_kontrol    = 1,59 R         (2,00 R sanılıyordu)
```
Üçü de ejekta ölçütünü **sıkılaştırır** ve β'yı sessizce kaydırır.

### Neden hiçbir test görmedi
**Gerçek çağıranların hepsi `target_radius` veriyor**; varsayılan yol hiç
koşulmuyordu — kod bir **tuzak** olarak bekliyordu.

### Düzeltme
`estimate_target_radius()` (medyan × 2^(1/3)), varsayımı açık, aykırı ejektaya
dayanıklı. `target_radius_estimated` tanısı eklendi.

---

## K5 — `dv/v` belgede 17 kat yanlıştı

**Modül:** `src/dartrift/observables/period_interface.py` · **Şiddet:** düşük (belge)

### Ölçülen etki
| β | dv/v |
|---|---|
| 1,0 | 4,77e-03 |
| 3,0 | 1,43e-02 |
| 3,6 | **1,72e-02** |

Belge `~1e-3` diyordu. Sonuç değişmiyor (ikinci mertebe düzeltme ~3e-4, hâlâ
ihmal edilebilir) ama **yaklaşımın gerekçesi olan sayı** yanlıştı.
Not düşülerek düzeltildi, silinmedi.

---

## K6 — β test bandı hiçbir şey ayırt etmiyordu

**Modül:** `tests/test_scene_checks.py` · **Şiddet:** orta (sınama boşluğu)

### Ölçülen etki
`2.5 < beta_from_dart_period < 4.5` — iki birim genişliğinde bir band.
Ölçülen değer 3,2225; yayınlanan ~3,6. Band ikisini de kabul ediyor.

Bu sayı **FAZ 4+'ta modelin hedefleyeceği** değerdir.

### Kritik ek bulgu
ΔT'nin ±1,0 dakikalık belirsizliğinden gelen band **[3,125 ; 3,320]** ve bu
band **3,6'yı içermiyor**. Yani fark periyot ölçümünün hatasıyla
**açıklanamaz**; kaynağı girdi varsayımıdır. β kütleyle doğru orantılı
olduğundan (d ln β / d ln M = 1), yayınlanan değeri verecek Dimorphos kütlesi
**4,80e9 kg**'dır (varsayılan 4,3e9).

### Düzeltme
`dart_beta_budget()` bunların hepsini döndürür; test bandı ölçülen değere
bağlandı (`rel=1e-3`) ve fark kütle varsayımına bağlandı.

---

## K7 — Kütle ile gözeneklilik tutarsızdı

**Modül:** `src/dartrift/setup/rubble_generator.py` · **Şiddet:** kritik
**ADR:** 0030

### Nasıl bulundu
ADR-0022 gerilmesiz başlangıç için `rho·alpha = rho0_katı` şart koşuyor.
Üretici ise kütleyi tekdüze atıyordu. İkisi aynı anda doğru olamaz →
SPH birim bölünmesi ölçüldü.

### Ölçülen etki
Birim bölünmesi `Σ_j (m_j/ρ_j) W_ij` (1 olmalı) — **h'den bağımsız**:

| h/spacing | M0 homojen | M1 matris | M1 blok |
|---|---|---|---|
| 1,3 | 1,0707 | 0,9837 | **0,7705** |
| 1,6 | 1,0677 | 0,9662 | **0,7842** |
| 2,0 | 1,0669 | 0,9519 | **0,8031** |

M0'daki sabit +%6,7 tam olarak `1800/(2700/1,6) = 1,0667` — **kapalı-form
imza**.

Aynı dizilim, iki yoğunluk yöntemi (ADR-0015 ikisini de destekliyor):

| | atanan ρ | toplam ρ | ayrışma | P (toplam ile) |
|---|---|---|---|---|
| matris | 1687,5 | 1800,4 | +%6,7 | **1,117e+09 Pa** |
| blok | 2571,4 | 1800,4 | −%30,0 | **−7,624e+09 Pa** |

### Kök neden
Üretici `rho0`'ı **hiç bilmiyordu**. Üç büyüklük (`rho0`, `bulk_density`,
`alpha0`) aşırı-belirlenmiş ve hiçbir yerde uzlaştırılmıyordu.

Üretim konfigürasyonu kendi yorumuyla çelişiyordu:
```yaml
bulk_density: 1800.0   # yorumu: "~%33 gözeneklilik" → α = 1,5 demek
matrix_alpha0: 1.6     # → yığın yoğunluğu 1687,5, 1800 DEĞİL
```

### Neden hiçbir kriter görmedi
- **C2** kütle bütçesini ölçüyor (`m` kullanır) → geçer
- **C3** gerilmesiz başlangıcı ölçüyor (`rho` kullanır) → geçer
- **Tutarlılığa bakan kriter yoktu.** K1'in kök nedeninin aynısı.

### Düzeltme
1. `m_i = (rho0_solid/alpha0_i)·V_p` — kütle gözeneklilikten türer.
2. `bulk_density` bir **hedef**; `matrix_alpha0` yerleştirmeden sonra ondan
   **çözülür**.
3. Açık `matrix_alpha0` hedefi tutturmuyorsa **hata** (tutturan değeri söyler).
4. `matrix_alpha0` konfigürasyonlardan **çıkarıldı**.

### Düzeltme sonrası ölçüm (yerel + TRUBA iş 1449560, Linux)
| | M0 | M1 |
|---|---|---|
| çözülen α | **1,5000** | **1,7273** |
| yığın yoğunluğu (hedef 1800) | 1800,0000 | 1800,0000 |
| hacim tutarlılığı `m/(ρ·V_p)` | **[1,000000 ; 1,000000]** | **[1,000000 ; 1,000000]** |
| birim bölünmesi matris / blok | 1,0002 / — | 1,0002 / **1,0002** |
| blok/matris kütle | — | **+%65** |

M0 için çözülen değer **tam 1,5000** — konfigürasyonun kendi yorumundaki
değerin ta kendisi. Doğru sayı zaten belgede yazılıydı, **parametrede yanlış
yazılmıştı.**

### Altın dosya
Karma değişti (`6d6f1d10` → `ca730c2c`); mekanizma sessiz değişikliği
**durdurdu** — amacına uygun çalıştı. Yeni karma iki bağımsız ortamda birebir
aynı doğrulandı: Linux/numpy 1.26.4 (TRUBA) ve Windows/numpy 2.4.6.

### Yapısal önlem
`TestMassPorosityConsistency` — `m_i/ρ_i = V_p` her parçacıkta; hedef tam
tutturuluyor; bloklar gerçekten ağır; çelişik değer hata veriyor; `rho0_solid`
zorunlu; ulaşılamaz hedef açık reddediliyor.

---

## K8 — `r_s` gözenekleri saymıyordu

**Modül:** `src/dartrift/warp_core/solver_solid.py` · **Şiddet:** orta

### Nasıl bulundu
K7 kütleleri heterojenleştirince hasar modülünün hacim kullanımı sınandı.

### Ölçülen etki (α = 1,5)
```
r_s mevcut (katı hacimden)  = 3,8624 m
r_s doğru  (geometrik)      = 4,4214 m      → %12,6 küçük
dD/dt ~ 1/r_s               → hasar %14,5 HIZLI büyüyordu
```

### Kök neden
`damage_ref.damage_rate` `r_s`'yi açıkça *"çatlağın kat etmesi gereken
uzunluk"* diye tanımlar; çatlak gözenekler dahil bütün parçacığı geçer. Kod
ise **katı** hacimden (`m/ρ₀`) hesaplıyordu.

### Düzeltme
Geometrik hacim (`m·α/ρ₀`). Bu hacim her parçacıkta **tam olarak kafes hacmi
V_p = 362,04 m³** çıkıyor — K7 tutarlılığının bağımsız doğrulaması.

---

## K9 — Kusurlar hacimden bağımsız dağıtılıyordu

**Modül:** `src/dartrift/cpu_reference/damage_ref.py` · **Şiddet:** orta

### Ölçülen etki
`seed_flaws` sahipliği `rng.integers` ile **tekdüze** seçiyordu. Bu yalnızca
bütün hacimler eşitken doğrudur. K7'den sonra M1 yığınında katı hacim gerçekten
değişiyor: **blok 344,8 · matris 209,6 m³ — %56 yayılım**. Tekdüze dağıtım
gözenekli matrise hak ettiğinden **fazla** kusur verirdi.

### Düzeltme
Ters-CDF ile hacimle orantılı sahiplik; aynı RNG akışı, deterministik.

### Düzeltme sonrası ölçüm
```
2× hacim → 1,9775× kusur          (beklenen 2,0)
tekdüze hacimde iki yarı oranı 0,9977   (beklenen 1,0)
deterministik: True   tohuma duyarlı: True
```

---

## S1 — Turun kendi hatası: GPU testinin tahmini ölçülmeden yazıldı

**Modül:** `tests/test_settling.py` · **Şiddet:** süreç

### Ne oldu
Eklediğim `test_parcacik_basina_Y0_SONUCU_degistiriyor` **kaldı** ve
**dört kapıyı birden düşürdü** (her kapı tam pytest paketini koşuyor).
Kusur kodda değildi, **tahminimdeydi**: *"zayıf kohezyon daha çok plastik iş
üretir"*.

### Ölçüm (iş 1448928, H100, üç kol)
| kol | Y0_ort | plastik iş |
|---|---|---|
| hepsi-zayıf | 1,0000e+04 | 1,459238e+07 J |
| heterojen | 2,3565e+06 | **1,890912e+09 J** |
| hepsi-güçlü | 1,0000e+07 | 1,264309e+10 J |

`hepsi-güçlü / hepsi-zayıf = 866,42` (Y0 oranı 1000).

### Fizik
Tam plastik rejimde dağılım hızı `σ_akma · ε̇_p`, yani iş yield gerilmesiyle
**artar**. Akmanın *başlangıcı* ile *büyüklüğünü* karıştırmışım.

### İki ders
1. **GPU-only testler yerelde SKIP oluyor.** Yerel takım 528/0 geçerken bu
   test hiç koşmadı. Yerel yeşil, GPU testi için kanıt değildir.
2. **GPU testinin tahmini önce ÖLÇÜLMELİ, sonra yazılmalı.**

---

## Ortak kök neden — dokuz kusurun tamamı

**Testler parçaların doğruluğunu sınıyordu, bütünün davranışını değil.**

- Hasarın formülleri doğruydu; **döngüsü** sınanmamıştı (K1).
- Krater çıkarıcı kürede doğruydu; **hedefin gerçek şekli** sınanmamıştı (K2).
- Tarama iki eksenli görünüyordu; **eksenlerin iş görüp görmediği** (K3).
- Yarıçap kestirimi vardı; **varsayılan yol hiç koşulmamıştı** (K4).
- C2 kütleyi, C3 yoğunluğu ölçüyordu; **tutarlılığı** kimse ölçmüyordu (K7).

Genellenebilir kural:

> **Bir kriter geçtiğinde, geçme SEBEBİNİN de ölçülmüş olması gerekir.**

*"Sonuç değişti"*, *"yayılım pozitif"*, *"derinlik makul"* — hepsi doğru
sebeple **ve** yanlış sebeple sağlanabilir.

Ayrıca **kapsama işe yaramaz**: dokuz kusurun hepsi **kapsanan satırlardaydı**
(kapsam %96,5–%100).

Bu yüzden eklenen her kriter artık **neyin iş gördüğünü** ayrı ayrı raporluyor:
`radius_axis_active`, `speed_axis_active`, `reference_is_spherical`,
`target_radius_estimated`, `volume_consistency_min/max`,
`matrix_alpha0_was_solved`, ve `_eval()` saflık değişmezi.
