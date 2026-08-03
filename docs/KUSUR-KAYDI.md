# Kusur kaydı — bulunan her kusurun tam dökümü

Bu belge, hata ayıklama turlarında bulunan **her kusuru** rapor yazımına
doğrudan girecek ayrıntıda tutar. Her kayıt aynı şablonu izler:

> **belirti** → **nasıl bulundu** → **ölçülen etki** → **kök neden** →
> **neden hiçbir test görmedi** → **düzeltme** → **düzeltme sonrası ölçüm** →
> **yapısal önlem** → **kanıt**

Kural: **hiçbir sayı tahmin değildir.** Buradaki her rakam bir koşudan
gelir ve iş numarası ile commit'i yazılıdır.

### İlgili belgeler

| belge | ne verir |
|---|---|
| [`KUSUR-KAYDI-KOD.md`](KUSUR-KAYDI-KOD.md) | her kusurun **önce/sonra kodu**, çalıştırılabilir **yeniden üretme** betiği, ve seçilmeyen alternatifler |
| [`YONTEM.md`](YONTEM.md) | kusurları bulan **üç soru** ve aktarılabilir hâli |
| [`DURUM-DEGERLENDIRMESI.md`](DURUM-DEGERLENDIRMESI.md) | verdikt + kalan riskler (R1–R10) |
| [`defter/`](defter/README.md) | **anlatı** — nasıl bulundu, hangi tahmin tutmadı |

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
| K10 | `warp_core/porosity_palpha` | Crush tavanı **skaler**, gözeneklilik parçacık başına | tavanı aşan parçacık ilk adımda ezilir → **−1,14 GPa** yapay çekme; KE bağ. enerjisinin **2,9 milyon katı** | 0031 | ✅ |
| K11 | `setup/scene` | Mermi distansiyonu **sabit 1**, yogunlugu ayri parametre | yogunluklar ayrisinca SPH/paketleme hacmi orani **1,1111** ya da **0,7407** | 0032 | ✅ |
| K12 | `setup/rubble_generator` | **Ayni ad iki buyukluk**: yigin yogunlugu mesh mi dolu hacim mi | fark = dolum orani, **-%1,19 … +%0,44**; `rel=0.05` bandi yutuyordu | 0033 | ✅ |
| K13 | `validation/scene_checks` | Blok kesri **kütle** olarak ölçülüp **hacim** hedefiyle karşılaştırılıyordu | hacim 0,3034 (+%1,1) ama kütle **0,4335** (+%44,5) → G3 C2 **kalıyordu** | 0034 | ✅ |
| K14 | `validation/scene_checks` | "Mermi dışarıda mı" **eşdeğer küre yarıçapı vekiliyle** ölçülüyordu | elipsoit kısa eksende **yanlış negatif**: gerçekte 0/207 içeride ama kriter False | 0035 | ✅ |
| K15 | `validation/scene_checks` | Komşuluk "iç bölge"si **ölçülen büyüklükle** seçiliyordu | %25 bozuk kafes **11,19** ile bant [11,0–12,01]'den **geçiyordu**; gerçek **10,25** | 0036 | ✅ |
| K16 | `validation/scene_checks` | "Yakınsıyor" ölçütü **monoton olmayan** bir büyüklüğe bakıyordu | kalıntı bir adımda **+0,01625 artıyor**; kriter seçilen N'lere bağlı — (400,800,1600) ile **False** | 0037 | ✅ |
| K17 | `setup/shape_mesh` | Kenar-manifold kontrolü **ters sarımı göremiyor** | 100 yüz ters → manifold hâlâ **True**, hacim **%15,5 yanlış**; yüklenen OBJ'de yakalayan yok | 0038 | ✅ |
| K18 | `validation/scene_checks` | Krater ölçütü **yanlılık + sinyal** toplamına elle yazılmış eşik uyguluyordu | yanlılık **−1,5335 m**; eşik 5,0 ikisini ayırmıyordu, pozitif kontrol yoktu | 0039 | ✅ |
| K19 | `scripts/run_red_team` | Kırmızı takımın **kendi** ölçütlerinde iki kusur: RT7 kütle kesri, RT11 **kendini doğrulayan** koşul | RT11'in üçüncü anahtarı `"X" if "X" in doc else "Y"` — **asla düşemez** | — | ✅ |
| K20 | `scripts/run_g1_gate` | G1 C7 bir **özdeşliği** sınıyordu — asla düşemez | iki yüzde `100·n_cfl/n` ve `100·(n−n_cfl)/n`; toplamları **inşaat gereği 100** | 0040 | ✅ |
| B1 | `warp_core/timestep` | **Kapsam boşluğu:** `dt` hesabı CPU referansıyla hiç karşılaştırılmamış | çapraz kontroller **sabit** `DT=5e-7` kullanıyordu; `dt` doğrudan `O(dt)` enerji kaymasına giriyor | — | ✅ |
| S1 | `tests/test_settling` | *Turun kendi hatası:* Y0 testinin **tahmini ters** | ölçülen 130 kat **ters yönde** | — | ✅ |
| S2 | `docs/KUSUR-KAYDI.md` | *Turun ikinci hatası:* kaydın kendisi **sessizce eksik kaldı** | `str.replace` çapası tutmadı → **3 bölüm birden** kayboldu (K10/K11/K12) | — | ✅ |
| S3 | `tests/test_solid_cross` | *Turun üçüncü hatası:* `dt`'nin **hızla** değişeceği varsayımı | ölçülen yayılım **%1,9** — boşluk kontrolü haklı olarak düştü; CFL **ses hızına** bağlı | — | ✅ |

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

## K10 — Crush eğrisinin tavanı skalerdi, gözeneklilik parçacık başına

**Modül:** `warp_core/porosity_palpha.py` + `cpu_reference/materials.py`
**Şiddet:** kritik · **ADR:** 0031

### Belirti
ADR-0030'dan sonra `test_esik_altinda_ve_yakinsadi` kaldı — settling
yakınsamıyordu.

### Nasıl bulundu
Testi düzeltmek yerine **ne değiştiği ölçüldü** (iş 1449843):

```
E_bağ = 1,703479e+06 J     eşik(1e-3) = 1,703479e+03 J
  40 adım: KE_son = 4,894274e+12 J   KE/E_bağ = 2,873e+06
 200 adım: KE_son = 3,896113e+09 J   KE/E_bağ = 2,287e+03
1000 adım: KE_son = 3,556281e+07 J   KE/E_bağ = 2,088e+01
```

KE, bağlanma enerjisinin **2,9 milyon katı**. Yerçekiminden gelemez:
`a_yerçekimi(t=0) = 3,213e-05 m/s²` ile 0,0134 s'de `v ~ 4e-7 m/s` beklenirken
ölçülen `v_rms ≈ 78 m/s`. Yani enerji **başka bir yerden** giriyordu.

### Ölçülen etki — karşı-kontrollü (iş 1449888, H100)
| adım | malzeme tavanı 1,6 (mevcut) | malzeme tavanı 1,7273 (uygun) |
|---|---|---|
| 0 | α=1,727253 · P=0 · KE=0 | α=1,727253 · P=0 · KE=0 |
| 1 | **α=1,600000** · P=0 · KE=8,23e-08 | α=1,727253 · P=0 · KE=8,23e-08 |
| 2 | α=1,600000 · **P=−1,1389e+09 Pa** · KE=3,36e+10 | α=1,727253 · P=−1,6e-04 Pa · KE=2,70e-07 |
| 4 | α=1,600000 · P=−1,1294e+09 Pa · **KE=8,29e+11** | α=1,727253 · P=5,1e-03 Pa · **KE=9,66e-07** |

**KE oranı: 8,587e+17.**

### Kök neden
`crush_alpha` distansiyonun üst sınırını **malzemenin skaler** `alpha0`
değerinden alıyordu. Yığının matris α'sı 1,7273 (ADR-0030 ile hedef yığın
yoğunluğundan çözülüyor), malzemenin skaleri 1,6. Fark %7,4 ve ilk adımda
`rho·alpha = rho0` şartını (ADR-0022) bozarak **−1,14 GPa** üretiyor.

### Kusur ne kadar eskiydi
**ADR-0030 onu görünür yaptı, ama kusur hep vardı.** Önceden matris α₀ = 1,6
**tesadüfen** malzemeninkine eşitti; bloklar (1,05 < 1,6) ise geri-genleşme
yasağıyla korunuyordu. Model **yalnızca homojen gözeneklilik için** doğruydu —
oysa heterojen yığın tam olarak FAZ 3'ün ürettiği şey.

### Düzeltme
Tavan parçacık başına: GPU'da `alpha_ref` dizisi, CPU'da
`crush_alpha(P, alpha_ref)` ve `solve_alpha_implicit(..., alpha_ref)`.
Verilmezse skaler kullanılır — homojen koşularda davranış değişmez.

### Düzeltme sonrası ölçüm (iş 1449929, H100)
```
40 adım: yakınsadı=True
KE_son = 5,724292e-06 J   KE/E_bağ = 3,360e-12    (önce 2,873e+06)
```

### Yapısal önlem
`TestPerParticleCrushCeiling` — eşik altında her parçacık kendi α₀'ını korur;
geriye dönük uyum; gerilmesiz başlangıç bozulmuyor; **boşluk kontrolü:**
gerçek basma hâlâ eziyor.

---

## K11 — Merminin distansiyonu sabit 1'di, yoğunluğu ayrı parametre

**Modül:** `src/dartrift/setup/scene.py` · **Şiddet:** yüksek · **ADR:** 0032

### Nasıl bulundu
K7 ve K10'un ortak deseni ("aynı büyüklük iki yerde") **sistematik** arandı.
Mermi, çözücünün `rho0_solid/alpha0` kuralına tabi ama yoğunluğu
`impactor_density` ile ayrıca veriliyor.

### Ölçülen etki (`rho0_solid = 2700`)
| `impactor_density` | `alpha0` | çözücünün ρ'su | V_SPH / V_paketleme |
|---|---|---|---|
| 2700 | 1,0000 | 2700,0 | 1,0000 |
| 3000 | 1,0000 | 2700,0 | **1,1111** |
| 2000 | 1,0000 | 2700,0 | **0,7407** |

%11–26 tutarsızlık, hiçbir uyarı olmadan. **Mermi β'yı taşıyan bileşendir**;
buradaki hata doğrudan başlık sayısına gider.

### Neden görünmüyordu
Üretim konfigürasyonunda ikisi de 2700 — **tesadüfen**. Bağlayan hiçbir şey
yoktu; biri değiştiğinde sessizce ayrışacaktı.

### Düzeltme
`alpha_imp = rho0_solid / impactor_density`. Eşitken α = 1,0 **tam** çıkar
(geriye dönük aynı); `impactor_density > rho0_solid` ise α < 1 gerekirdi —
fiziksel değil, **açık hata** (çözücü tek malzemeli; mermi ancak **seyrek**
temsil edilebilir).

### Düzeltme sonrası ölçüm
| `impactor_density` | `alpha0` | tutarlılık |
|---|---|---|
| 2700 | 1,0000 | **1,000000** |
| 2000 | 1,3500 | **1,000000** |
| 1500 | 1,8000 | **1,000000** |
| 3000 | — | **açık hata** |

Kütle ve momentum defteri etkilenmiyor (test ile kilitli).

---

## K12 — "Yığın yoğunluğu" iki farklı şeydi, ikisi de aynı adla

**Modül:** `src/dartrift/setup/rubble_generator.py` · **Şiddet:** düşük-orta
**ADR:** 0033

### Nasıl bulundu
Desenin daha yumuşak biçimi arandı: *aynı ad iki farklı hesabı taşıyor mu?*

### Ölçülen etki
| şekil | dolum | A (mesh) | B (dolu) | A sapma |
|---|---|---|---|---|
| ikosfer r=100 s=9 | 0,9993 | 1798,80 | 1800,00 | −%0,07 |
| ikosfer r=60 s=8 | 0,9881 | 1778,51 | 1800,00 | **−%1,19** |
| elipsoit 120×100×85 | 0,9987 | 1797,65 | 1800,00 | −%0,13 |
| ikosfer r=82 s=7 | 1,0044 | 1807,98 | 1800,00 | **+%0,44** |

Somut sonucu: `settle_pile` bağlanma enerjisini **kütleyi bir hacim
tanımından, yarıçapı diğerinden** alarak hesaplıyordu.

### Neden görünmüyordu
`test_bulk_density_recovered` `rel=0.05` bandı kullanıyordu — ayrımı yutuyordu.

### Düzeltme
İki tanım ayrı adlandırıldı; `discretised_volume`/`discretised_radius`
eklendi; `settle_pile` artık kütle ile yarıçapı **aynı** tanımdan alıyor.

### Yapısal önlem
`A = B × dolum_oranı` kapalı-form ilişkisi **toleranssız** (`rel=1e-12`)
kilitlendi. Kural genişletildi: *"yaklaşık eşit" bir tolerans bandı, ayrımı
gizlemenin en kolay yoludur.*

---

## K13 — Blok kesri kütle olarak ölçülüp hacim hedefiyle karşılaştırılıyordu

**Modül:** `src/dartrift/validation/scene_checks.py` · **Şiddet:** yüksek
**ADR:** 0034

### Belirti
ADR-0030+0031 sonrası G3 C2 kaldı: *"blok kesri 0.433 (hedef 0.30)"*.
Bu sefer pytest geçiyordu — kriterin kendisi düşüyordu.

### Nasıl bulundu
İlk soru: *"üretici mi bozuk, ölçü mü yanlış?"* Üretici ölçüldü.

### Ölçülen etki (ikosfer r=80, s=7, f_boulder=0,30)
| büyüklük | değer | sapma |
|---|---|---|
| hedef (hacim) | 0,3000 | — |
| ölçülen **hacim** kesri | **0,3034** | **+%1,1** |
| ölçülen **kütle** kesri (eski kod) | **0,4335** | **+%44,5** |

**Üretici doğruydu.** Kapalı form 6 hane tuttu:
`f_kütle = f_h·r/(f_h·r + 1 − f_h)`, `f_h = 0,3034`, `r = 1,7565` → **0,433483**;
ölçülen **0,433483**. `r = α_matris/α_blok = 1,8443/1,05` — ADR-0030'un
doğrudan sonucu.

### Kök neden
`f_boulder` **hacim** olarak tanımlı (`boulder_volume_target = f_boulder ·
mesh.volume`), ölçülen ise **kütle** kesriydi. Tekdüze kütlede aynı sayı;
bloklar ağırlaşınca ayrıştılar.

### Düzeltme
Kriter `boulder_volume_fraction` okur. Kütle kesri **ayrı adla** raporlanır
(`boulder_mass_fraction`) — fiziksel olarak anlamlı ama hedefle
karşılaştırılmaz.

### Yapısal önlem
`TestBoulderFractionIsVolumeNotMass` — kapalı-form ilişki `rel=1e-12` ile
kilitli; kütle kesrinin hacim kesrinden **belirgin** büyük olması şart, yani
test **ADR-0030 ile ADR-0034'ü birden** bekçilik eder.

### Ders
Desenin en öğretici örneği: **kod doğruydu, ölçüm yanlıştı.** Bir kriter
kaldığında ilk soru *"üretici mi bozuk, ölçü mü yanlış?"* olmalıdır.

---

## K14 — "Mermi hedefin dışında mı" vekil ölçütle sınanıyordu

**Modül:** `src/dartrift/validation/scene_checks.py` · **Şiddet:** orta
**ADR:** 0035

### Nasıl bulundu
K12/K13 deseni ("ölçüt asıl soruyu mu ölçüyor?") sahne bütünlüğü kriterine
uygulandı.

### Ölçülen etki (elipsoit 88×87×65 m, r_eff = 39,59 m)
| çarpma ekseni | mermi min uzaklık | vekil (`\|x\|>r_eff`) | mesh içinde | gerçek |
|---|---|---|---|---|
| kısa (z) | 32,63 m | **False** | **0/207** | dışarıda |
| uzun (x) | 44,13 m | True | 0/207 | dışarıda |

Kısa eksende **yanlış negatif**. Ters yön de mümkün: uzun eksende yüzey
r_eff'ten 4,4 m dışarıda olduğu için, r_eff'i geçen ama gövdeye **gömülü**
bir mermi "dışarıda" sayılırdı.

### Neden görünmüyordu
Denetim **ikosfer** üzerinde koşuyordu; orada `r_eff` gerçek yarıçapa eşit ve
vekil **tesadüfen** doğru. Üretim konfigürasyonu gerçek PDS şeklini kullanıyor.

### Doğrulanan: yerleştirme kodu DOĞRU
Dört senaryoda (küre/elipsoit × kısa/uzun eksen) **0/207** mermi parçacığı
mesh içinde; en yakın mesafe 1,72–4,09 m (parçacık aralığı 6,0). Kusur
**ölçütteydi**, üreticide değil — K13 ile aynı sınıf.

### Düzeltme
Doğrudan `inside_points` ölçümü + aynı sınav **düzensiz cisimde** de.
G3 C6 artık `irregular_all_outside` şartını koşuyor.

### Yapısal önlem
Üç test; sonuncusu **boşluk kontrolü**: vekil gerçekten yanılıyor mu?
Yanılmıyorsa düzeltmenin gerekçesi kaybolmuş demektir.

---

## K15 — Komşuluk "iç bölge"si ölçülen büyüklüğün kendisiyle seçiliyordu

**Modül:** `src/dartrift/validation/scene_checks.py` · **Şiddet:** orta-yüksek
**ADR:** 0036

### Nasıl bulundu
ADR-0035'in sorusu ("ölçüt asıl soruyu mu ölçüyor?") bir adım ileri
götürüldü: *ölçüt, doğru büyüklüğü yanlı bir örneklem üzerinde mi ölçüyor?*

`coordination_interior_mean = np.mean(cn[cn >= np.median(cn)])` — parçacıklar
**ölçülen büyüklüğe göre** seçilip sonra o büyüklük ortalanıyor.

### Ölçülen etki (ikosfer r=100, aralık 10)
| durum | eski ölçüt | gerçek iç ortalama |
|---|---|---|
| bozulmamış FCC | 12,00 | 12,00 |
| **%25 bozuk kafes** | **11,19** | **10,25** |
| %50 bozuk kafes | 9,73 | 9,05 |
| %75 bozuk kafes | 9,35 | 8,45 |
| tamamen rastgele | 15,20 | 13,31 |

Kapının bandı `[11,0 ; 12,01]`. **Parçacıkların dörtte biri 0,35·aralık
kaydırılmış bir yığın GEÇİYORDU**; gerçek değeri 10,25, bandın dışında.

Ölçüt sistematik iyimser: bozulma arttıkça fark +0,7 … +0,9. Rastgele bulut
15,20 verdiği için **üst** sınır işini görüyordu; **alt** sınır bozulmuş
kafesi yakalayamıyordu.

### Düzeltme
"İç bölge" geometrik: yüzeyden en az `2,5 × aralık` içeride — ölçülen
büyüklükten **bağımsız**. Eski ölçüt `coordination_selfselected_mean` adıyla
ayrıca raporlanır; ikisi arasındaki fark kafes düzgünlüğünün göstergesidir
(bozulmamış FCC'de tam **0,0**). İç bölge boş kalırsa **hata**.

### Yapısal önlem
`TestCoordinationInteriorIsGeometric` — **boşluk kontrolü** dahil: %25 bozuk
kafeste iki ölçüt ayrışmalı ve eski ölçüt eşiği geçerken gerçek geçmemeli.

### Ders
> **Bir alt kümeyi, ölçmek istediğin büyüklüğe göre seçme.** Seçim ölçütü ile
> ölçülen büyüklük aynı şeyse, sonuç kendini doğrular.

---

## K16 — "Yakınsıyor" ölçütü monoton olmayan bir büyüklüğe bakıyordu

**Modül:** `src/dartrift/validation/scene_checks.py` · **Şiddet:** orta
**ADR:** 0037

### Nasıl bulundu
K15'ten sonra soru genişletildi: *ölçüt, yakınsaması BEKLENEN bir büyüklüğe mi
bakıyor?*

### Ölçülen etki
| N | 207 | 399 | 803 | 1568 | 3184 | 6401 | 12808 |
|---|---|---|---|---|---|---|---|
| kafes kalıntısı | 0,03500 | 0,00250 | 0,00375 | **0,02000** | 0,00500 | 0,00016 | 0,00063 |

**Monoton değil**; bir adımda **+0,01625 artıyor**. Kriter `ilk > son` idi ve
sonucu **hangi N'lerin seçildiğine** bağlı:
- `(200, 800, 3200)` → True (mevcut seçim)
- `(400, 800, 1600)` → **False**

### Kök neden
`volume_error = |N·V_p − V_küre|/V_küre` kafesin küreye **nasıl oturduğunun**
kalıntısıdır, ayrıklaştırma hatası değil. Yakınsaması beklenen bir büyüklük
değil.

### Gerçekten yakınsayan
çap boyunca parçacık: 6,46 → 25,86 **kesin artan**
(`25,86/6,46 = 4,00` vs `(12808/207)^(1/3) = 3,94` ✓);
kütle ≤ 5,89e-16; momentum ≤ 4,0e-14.

### Düzeltme
Kriter `resolution_increases`. Kalıntı olduğu gibi raporlanır (merdiven,
`volume_error_monotone = False`, zarf). G3 C4 **zarfın** küçülmesini şart
koşar. Ayrıca elle yazılmış `> 80.0` eşiği kaldırıldı → ADR-0035'in mesh
üyeliği ölçüsü.

### Yapısal önlem
Üç test; ortadaki **boşluk kontrolü**: kalıntı monoton çıkarsa düzeltmenin
gerekçesi kaybolmuş demektir.

### Ders
> **Bir büyüklüğün "yakınsadığını" iddia etmeden önce, o büyüklüğün
> yakınsaması BEKLENEN bir büyüklük olup olmadığı sorulmalıdır.**

---

## K17 — Kenar-manifold kontrolü ters sarımı göremiyordu

**Modül:** `src/dartrift/setup/shape_mesh.py` · **Şiddet:** yüksek
**ADR:** 0038

### Nasıl bulundu
Ölçüt denetimi mesh kontrollerine uzatıldı: *"manifold" adı neyi garanti
ediyor?* Kod kenarları **sıralayarak** sayıyor — `(a,b)` ile `(b,a)` aynı.

### Ölçülen etki (ikosfer(3), yüzler ters çevrilerek)
| ters yüz | `is_edge_manifold()` | hacim hatası |
|---|---|---|
| 1 | **True** | %0,109 |
| 5 | **True** | %0,764 |
| 20 | **True** | %3,112 |
| 100 | **True** | **%15,545** |

### Neden önemli
Mesh hacmi üç yere giriyor: yığın yoğunluğu (`Σm/V_mesh`), blok hacim hedefi
(`f_boulder·V_mesh`), etkin yarıçap (kaçış hızı, bağlanma enerjisi).

### Neden görünmüyordu
Analitik şekillerde C1'in `max_volume_rel_err < 0.01` kontrolü yakalar.
**Yüklenen OBJ'de — gerçek PDS Dimorphos modelinde — analitik hacim YOK**;
orada yakalayan başka bir şey de yoktu. `orient_outward` yalnızca toplam
hacim negatifse **tüm** ağı çevirir.

### Düzeltme
`is_consistently_oriented()`: her **yönlü** kenar tam bir kez. G3 C1 ve PDS
testi artık bunu da şart koşuyor. Tespit edilir ve **reddedilir**, sessizce
onarılmaz.

### Ölçülen: iki kontrol BAĞIMSIZ
| bozulma | manifold | yönelim |
|---|---|---|
| delik | **False** | True |
| ters sarım | True | **False** |

İlk yazdığım test *"delik ikisini de bozar"* diye tahmin ediyordu ve düştü.
Kod doğru; kapalılık ile yönelim ayrı özellikler — **tam bu yüzden ikisi de
gerekli.**

### Ders
> **Bir kontrolün adı, neyi kontrol ettiğini söylemeyebilir.**

---

## K18 — Krater ölçütü yanlılık ile sinyali karıştırıyordu

**Modül:** `src/dartrift/validation/scene_checks.py` · **Şiddet:** orta
**ADR:** 0039

### Nasıl bulundu
Elle yazılmış eşikler tarandı: `abs(cs.global_radius_change) < 5.0` — 5,0
nereden geliyor?

### Ölçülen etki (80 m küre, 40000 parçacık)
| durum | `global_radius_change` | yanlılıktan sapma |
|---|---|---|
| **deformasyonsuz** | **−1,5335 m** | — (saf yanlılık; gerçek 0) |
| 16 m kraterli | −1,5335 m | **+0,0000 m** |
| %10 küresel büzüşme | −9,3802 m | **−7,8466 m** (beklenen ≈ −8) |

**Çıkarıcı mükemmel ayırıyor** — kusur ölçütteydi. `global_radius_change`
yüzey örneklem yanlılığı ile gerçek deformasyonun **toplamı**; eşik 5,0
yalnızca yanlılığı (1,53) barındıracak kadar genişti, ikisini **ayırmıyordu**.

### Düzeltme
Yanlılık, aynı cismin **deformasyonsuz** hâlinden ölçülür; kriter **farka**
bakar (`|excess| < 0,5` — 10 kat dar). **Pozitif kontrol** eklendi: %10
büzüşme gerçekten yakalanmalı — yoksa "ayrışıyor" iddiası boş bir doğru olur
(her şeye 0 diyen bir çıkarıcı da onu sağlar).

### Ek düzeltme
`deterministic` ölçütü yalnızca `x` ve `Y0` karşılaştırıyordu; `m` ve
`alpha0` ADR-0030'dan sonra **türetilmiş** — türetme yolundaki sapma
görünmezdi. Tam duruma genişletildi.

### Ders
> **Bir ölçüm, aradığın sinyal ile bilinen bir yanlılığın toplamıysa,
> yanlılığı ayrı ölç ve kriteri FARKA uygula.** Yanlılığı barındıracak kadar
> geniş bir eşik, sinyali de barındırır.

Ve her "ayrışıyor" iddiası bir **pozitif kontrol** ister.

---

## K19 — Kırmızı takımın kendi ölçütlerinde iki kusur

**Modül:** `scripts/run_red_team.py` · **Şiddet:** orta

### Nasıl bulundu
Ölçüt denetimi, denetleyicinin **kendisine** uygulandı: *kırmızı takım
maddeleri doğru sebeple mi geçiyor?*

### Kusur A — RT7 kütle kesri ölçüyordu (K13'ün ikinci sahnesi)
```python
olculen = float(np.sum(pile.m[pile.is_boulder]) / np.sum(pile.m))   # KÜTLE
```
İstenen `f_boulder = 0,90` ise **hacim** kesri. ADR-0030'dan sonra bloklar
%65 daha ağır olduğu için kütle kesri hacim kesrinden **büyük** çıkar
(ölçülen 0,3034 → 0,4335). RT7 bir *doyma* sınavı olduğu için (ölçülen ≪
istenen) yön kusuru sonucu değiştirmiyordu — ama yanlış büyüklüktü.

### Kusur B — RT11'de kendini doğrulayan koşul
```python
anahtar = ["denge", "ZATEN", "KAPSAM DISI" if "KAPSAM DISI" in doc else "hesaplanabilir"]
```
Üçüncü anahtar **belgede varsa onu arıyor** — yani `"KAPSAM DISI"` mevcutsa
onu, değilse `"hesaplanabilir"`i. Bu koşul **asla düşemez**.

Ölçüldü: belgede `"KAPSAM DISI"` **yok**, `"hesaplanabilir"` **var** → üçüncü
anahtar otomatik sağlanıyor. RT11 üç anahtar arıyor gibi görünüp **ikisini**
sınıyordu; üstelik ikisi de **dize eşleşmesi** — RT12'nin düzeltilmiş günahı.

### Düzeltme
- **RT7**: `boulder_volume_fraction`; kütle kesri ayrıca raporlanır.
- **RT11**: dize eşleşmesi yerine **davranışsal** sınav — bir iddia, onu
  destekleyen **ölçümü döndürmedikçe** geçerli sayılmaz:
  `a_sph_max_t0`, `a_gravity_max_t0`, `steps_per_free_fall`, `ke_threshold`,
  `converged` üretiliyor mu; `converged` **koşullu** mu (sabit True değil);
  `SettleResult` varsayılanı `converged=False` mi.

### Ders
> **Denetleyici de denetlenir.** Bir koşulun ölçtüğü şey, o koşulun kendi
> girdisinden türetiliyorsa, koşul boştur.

K15 ile aynı aile: orada örneklem ölçülen büyüklükle seçiliyordu, burada
**eşik** aranan metnin kendisinden seçiliyor.

---

## K20 — G1 C7 bir özdeşliği sınıyordu (asla düşemezdi)

**Modül:** `scripts/run_g1_gate.py` · **Şiddet:** orta (sınama boşluğu)
**ADR:** 0040

### Nasıl bulundu
K15/K19'un sorusu ("koşul kendi girdisinden mi türüyor?") FAZ 1 kapısına
uygulandı.

### Ölçülen etki
```python
# summarize_timestep_stats:
binding_cfl_viscous_pct  = 100.0 * n_cfl / n
binding_acceleration_pct = 100.0 * (n - n_cfl) / n
```
G1 C7 ise şunu sınıyordu:
```python
abs(binding_cfl_viscous_pct + binding_acceleration_pct - 100.0) < 1e-9
```
Toplam **inşaat gereği tam 100**. Bu bir **özdeşlik**, kanıt değil —
`1e-9` toleransı yalnızca kayan nokta yuvarlaması içindi. Kriterin
düşebileceği tek gerçek koşul `n_steps > 0` idi.

### Düzeltme
Düşebilecek şartlar:
- gerekli alanların **tamamı** var,
- `n_steps > 0`,
- üç yüzde de `[0, 100]` aralığında,
- `0 < dt_min ≤ dt_max < ∞`,
- **log anlamlı mı:** `dt_max > dt_min` — sabit `dt`'de kısıt-yüzdesi logu
  bilgi taşımaz ve P1-FR-07'nin amacı karşılanmaz.

Kanıt metni artık örnek `dt` aralığını ve bağlayıcı kısıt yüzdesini yazıyor.

### Ders
> **Bir koşulun düşebileceği bir dünya var mı?** Yoksa o koşul kanıt değil,
> yalnızca bir özdeşliğin yeniden yazımıdır.

K19-B ile aynı aile: orada eşik aranan metinden, burada karşılaştırılan
büyüklük kendi tanımından türüyordu.

---

## B1 — Kapsam boşluğu: `dt` hesabı hiç çapraz kontrol edilmemiş

**Modül:** `src/dartrift/warp_core/timestep.py`, `WarpSolid3D.compute_dt`
**Tür:** kapsam boşluğu (kod doğru, sınanmamış)

### Nasıl bulundu
Yapısal denetim: **16 GPU çekirdeği** ile **5 CPU referansı** eşleştirildi.
K1'in kök nedeni tam bu türdendi (hasarın CPU döngü referansı yoktu).

Eşleşme sonucu — tek boşluk `timestep`:

| GPU çekirdeği | CPU referansı | çapraz kontrol |
|---|---|---|
| `density`, `forces`, `integrator`, `kernel_fn`, `neighbors`, `hash_grid`, `solver` | `sph_ref` | `test_sph_cross` ✓ |
| `eos_tillotson`, `solid_stress`, `strength_lundborg`, `porosity_palpha`, `solver_solid` | `solid_ref`, `materials` | `test_solid_cross` ✓ |
| `gravity_tree` | `gravity_ref` | `test_uniform_sphere`, `test_two_body` ✓ |
| `damage_gradykipp` | `damage_ref` | `TestDamageCross` ✓ *(bu turda eklendi)* |
| **`timestep`** | `compute_timestep_solid` | **YOK** |

### Neden önemli
`dt` hem kararlılığı hem doğruluğu belirler. Üstelik mevcut çapraz kontroller
**sabit** `DT = 5.0e-7` kullanıyor — GPU ile CPU farklı `dt` seçseydi bu
testler **görmezdi**. ADR-0028'de ölçülen enerji kayması da tam olarak
`O(dt)` kesme hatasıydı, yani `dt` doğrudan bilimsel sonuca giriyor.

### Düzeltme
`TestTimestepCross` — dört farklı hız ölçeğinde (içe çökme, genleşme, yavaş,
hızlı) `WarpSolid3D.compute_dt()` ile `compute_timestep_solid()` **birebir**
karşılaştırılır (`rel=1e-12`), hem `cpu` hem `cuda:0` cihazında.

**Boşluk kontrolü** (ADR-0040): `dt` durumlar arasında gerçekten değişmeli
(`max/min > 1,5`) — hepsi aynı çıksaydı eşitlik testi hiçbir şey sınamazdı.

### Not
Bu bir **kusur kaydı değil**, kapatılan bir kapsam boşluğudur — kodun doğru
olup olmadığı TRUBA koşusunda görülecek.

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

## S2 — Turun ikinci hatası: kusur kaydının kendisi sessizce eksik kaldı

**Modül:** `docs/KUSUR-KAYDI.md` · **Şiddet:** süreç

### Ne oldu
K10, K11 ve K12 kayda eklenirken kullanılan `str.replace` çağrılarının çapası
`"## S1 — Turun kendi hatasi"` yazıyordu; dosyadaki gerçek başlık
`"...hatası"` (Türkçe **ı**). Eşleşme olmadı, `replace` **sessizce hiçbir şey
yapmadı** ve **üç bölüm birden kayboldu**. Tablo K11/K12'yi gösteriyordu ama
gövdelerinde bölüm yoktu; K10 ise **hiçbir yerde** yoktu.

### Nasıl bulundu
Belge okunurken tabloda K9'dan sonra doğrudan K11 geldiği görüldü. Denetim:
```
tablo : K1 K2 K3 K4 K5 K6 K7 K8 K9 K11 K12 S1     -> 12 kimlik
gövde : K1 K2 K3 K4 K5 K6 K7 K8 K9 S1             -> 10 kimlik
```
Ölçülen: beklenen **13,0** kayıttan tabloda **12,0**, gövdede **10,0** vardı;
**3,0** bölüm (K10, K11, K12) sessizce kaybolmuştu ve **1,0** kusur (K10)
hiçbir yerde yoktu. Kayıp oranı **%23,1**.

### Kök neden
**Doğrulanmamış varsayım + sessiz başarısızlık** — kayıtta belgelenen kusur
sınıfının tam aynısı. `str.replace` eşleşme bulamazsa hata vermez; ben de
sonucu denetlemedim.

### Düzeltme
Üç bölüm de yazıldı; ekleme **assert'li** yapıldı ve sonuç yeniden okunarak
tablo ile gövde karşılaştırıldı.

### Yapısal önlem
`tests/test_docs_registry.py` — **belge de sınanır**:
- tablo ile gövde birebir aynı (eksik/fazla kimlik yok),
- kimlikler K1..Kn kesintisiz, tekrarsız, sıralı,
- her kusur kaydında **en az bir ölçülen sayı** var (kaydın kendi kuralı:
  *"hiçbir sayı tahmin değildir"*),
- anılan her ADR dosyası diskte var.

### Ders
Teslim ürünü olan bir belge, kod kadar sınanmalıdır. Bu turda bulunan on iki
kusurun ortak imzası — *sessiz başarısızlık, doğrulanmamış varsayım* —
belgeyi yazan araçta da geçerliydi.

---


## S3 — Turun üçüncü hatası: `dt`'nin hızla değişeceği varsayımı

**Modül:** `tests/test_solid_cross.py` · **Şiddet:** süreç

### Ne oldu
B1 için yazdığım `TestTimestepCross`'ta **boşluk kontrolü** şuydu: `dt`, dört
farklı hız ölçeğinde en az 1,5 kat oynamalı — yoksa eşitlik testi boş bir
doğruyu sınar.

**Eşitlik geçti** (`dt_CPU == dt_GPU`, rel 1e-12, dört durumda da — yani `dt`
kodu **doğru**). Düşen şey benim boşluk kontrolümdü.

### Ölçüm (TRUBA iş 1450286, H100)
```
hız çarpanı   0,05      1        1        5
dt          5,320e-06 5,402e-06 5,402e-06 5,421e-06
yayılım     %1,9
```

### Kök neden — fizik
CFL kısıtı **ses hızına** bağlıdır (Tillotson bazaltta ~5000 m/s). Denenen
parçacık hızları (1,5–150 m/s) onun yanında ihmal edilebilir. Yani hız, bu
rejimde `dt`'yi **sürmüyor**. `dt` gerçekten `h` ve `cfl` ile oynar:
`dt_cfl = cfl · h / visc`.

### Düzeltme
Sınav `h` (0,5×, 1×, 2×) ve `cfl` (0,2 / 0,05) ile kuruldu; eşitlik böylece
**geniş** bir `dt` aralığında sınanıyor.

### Ders
Bu, S1 ile **aynı** hata: bir GPU testinin tahminini ölçmeden yazmak. İkinci
kez oldu. Kural artık kayıtlı: **boşluk kontrolünün kendisi de bir tahmindir
ve ölçülmelidir.**

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
