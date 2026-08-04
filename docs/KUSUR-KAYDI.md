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
| K21 | `eos_tillotson`, `materials` | Genleşmiş-**sıcak** kolda `ρ ≤ 0` → **NaN**; GPU'da **sessiz** | `u = 2·u_cv`, `ρ = −0,27` → `P = nan`; `ρ = −27` → sonlu (**dar bir bant**) | — | ✅ |
| B1 | `warp_core/timestep` | **Kapsam boşluğu:** `dt` hesabı CPU referansıyla hiç karşılaştırılmamış | çapraz kontroller **sabit** `DT=5e-7` kullanıyordu; `dt` doğrudan `O(dt)` enerji kaymasına giriyor | — | ✅ |
| B2 | `warp_core/*` | **Tarama:** K21 sınıfının başka örneği var mı — `exp`/`log`/`sqrt`/`pow`/`acos`/bölme | 9 aday incelendi; 7'si kelepçeli, 2'si (`div/ρ`, `P/ρ²`) `ρ ≤ 0`'a açık ama **artık deftere işleniyor** → **yeni kusur yok** | — | ✅ |
| S1 | `tests/test_settling` | *Turun kendi hatası:* Y0 testinin **tahmini ters** | ölçülen 130 kat **ters yönde** | — | ✅ |
| S2 | `docs/KUSUR-KAYDI.md` | *Turun ikinci hatası:* kaydın kendisi **sessizce eksik kaldı** | `str.replace` çapası tutmadı → **3 bölüm birden** kayboldu (K10/K11/K12) | — | ✅ |
| S3 | `tests/test_solid_cross` | *Turun üçüncü hatası:* `dt`'nin **hızla** değişeceği varsayımı | ölçülen yayılım **%1,9** — boşluk kontrolü haklı olarak düştü; CFL **ses hızına** bağlı | — | ✅ |
| S4 | FAZ 4 E2 ölçümü | *Turun dördüncü hatası:* ses hızı için **kaba vekil** (`√(P/ρ)`) | 316 m/s dedim, gerçeği **10150**; `dt` **32,1 kat** büyük → koşu patladı (ve K21'i açığa çıkardı) | — | ✅ |
| S5 | FAZ 4 E2 ölçümü | *Turun beşinci hatası:* nedensel pencere **komşu bölgeden** hesaplandı | pencere 2,44 ms, koştuğum 2,46 ms — son adımlar **fiziksel dalgayı** ölçüyordu | — | ✅ |
| S6 | `tests/test_mass_ratio_probe` | *Turun altıncı hatası:* eşiği **ölçmeden** yazdım — **iki kez** | *(a)* "yanlış taban kuvveti büyütür" → ölçülen `1,29e-15`; *(b)* "basıncın işaretini çevirir" → **ters yönde** | — | ✅ |
| S7 | `validation/resolution_scaling` | *Turun yedinci hatası:* boşluk kontrolünü **ADR'yi okumadan** tasarladım | "hata küçülmeli" dedim; ADR-0011 zaten **%3,9 model-form tabanı** ölçmüştü | — | ✅ |
| S8 | `validation/coupling_conservation` | *Turun sekizinci hatası:* eşleme kaymasını **sıfıra** kıyasladım | ölçülen `0,9789` — ama **λ=2 ile λ=4 birebir aynı**; sayılmayan dış kabuk tepkisiymiş | — | ✅ |
| S9 | `tests/test_solver_idempotence` | *Turun dokuzuncu hatası:* koşulsuz kapsam doğrulaması **bir kolda düşerdi** | `damage=False`'da `D`/`D_cbrt` yok; yerelde CUDA olmadığı için görünmedi, **G3 C6'yı düşürdü** | — | ✅ |

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

## K21 — Tillotson genleşmiş-sıcak kolda `ρ ≤ 0` → NaN, ve GPU'da **sessiz**

**Nerede:** `src/dartrift/warp_core/eos_tillotson.py` (`_till_hot`),
`src/dartrift/cpu_reference/materials.py` (`tillotson_pressure`)
**Nasıl bulundu:** FAZ 4 E2 ölçümünde `RuntimeWarning: overflow encountered
in exp`. Uyarı **atlanabilirdi** — üstelik GPU'da hiç görünmezdi.

### Kök neden

Genleşmiş-sıcak kolun üssü:

```
ex = exp(−β·(1/η − 1)),      η = ρ/ρ₀
```

`η` küçük **negatif** iken `1/η` büyük negatif olur, üs büyük **pozitif**
olur, `exp` **taşar** → `inf`. Hemen ardından:

```
p_hot = a·ρ·u + (b·ρ·u/ω + A·μ·ex)·ex2 ,   ex2 = exp(−α·(1/η−1)²) = 0
```

`inf · 0` → **NaN**. NaN oradan **her komşu toplamına** yayılır.

### Ölçüldü (`u = 2·u_cv`)

| ρ | P | sonlu mu |
|---|---|---|
| +0,27 | 4,914000e+06 | ✔ |
| 0,00 | 0,000000e+00 | ✔ |
| **−0,27** | **nan** | **✘** |
| −27,0 | −4,914000e+08 | ✔ |

Dikkat: kusur **aralıksız değil**, yalnızca `ρ`'nin sıfıra yakın negatif
olduğu **dar bir bantta**. Yani rastgele bir sınamayla kolayca kaçırılır.

### Neden ciddi

1. **GPU'da sessizdir.** `wp.exp` uyarı vermez. Bir üretim koşusu baştan
   sona NaN üretip *"bitti"* diyebilirdi.
2. **Yayılır.** Tek bir NaN parçacık, komşuluğu üzerinden her toplamı
   NaN yapar; birkaç adımda tüm alan.
3. **Tam da ejekta rejiminde.** `ρ → 0` **ve** `u ≥ u_cv` koşulu, seyrelmiş
   sıcak ejektanın ta kendisidir — FAZ 4'ün ölçmek istediği şey.

### Neden bir kusurdur, "geçersiz girdi" değil

`ρ ≤ 0` **asla fizik değildir**: süreklilikte `dρ/dt = −ρ·∇·v` üstel azalır,
sıfırı **ancak `dt` fazla büyükse** geçer. Yani her zaman bir **sayısal
başarısızlıktır**. Doğru tepki onu *maskelemek* değil, **görünür kılmaktır**.

### Düzeltme — iki parçalı

**(1) EOS toplam yapıldı.** Sonlu girdi → sonlu çıktı. `ρ ≤ 0` için soğuk kol
(polinom, her zaman sonlu). CPU'da ayrıca sıcak kol **güvenli `η`** ile
hesaplanıyor ki üs hiç oluşmasın. `ω`'nın tekil noktasında (`ρ = 0`) doğru
**limit** yazıldı: `u > 0` ise `ω → ∞` (ve `b/ω → 0`).

**(2) Maskelenmiyor.** Hem GPU çözücüsünün hem CPU referansının defteri artık
`nonpositive_density_count`, `rho_min` ve `state_is_finite` raporluyor.
**Sayaç sıfırdan büyükse o koşu geçersizdir.**

### Determinizm korundu — ve ilk denemem bunu bozmuştu

İlk düzeltmemde `ω`'yı `u/(u0·(η·η))` diye yazdım. Eski ifade
`u/((u0·η)·η)` idi. **Farklı yuvarlıyorlar** — 8000 örnekte göreli `~1e-14`
fark ölçüldü ve geri alındı. Determinizm kilitli bir özelliktir (ADR-0004),
`1e-14` bile kabul edilemez.

Doğrulandı: geçerli girdide **bit aynı** (8000 örnek; sıkışmış 4000, sıcak
3049, ara 951 — üç kolun da gezildiği **ayrıca** sınanıyor).

### Yapısal kapatma

`tests/test_eos_totality.py` — 9 test, `-W error::RuntimeWarning` ile geçiyor:

- `ρ ∈ {−1e-9, −0,27, −27, −2700, 0}` × sıcak enerji → **sonlu**
- beş enerji seviyesinde, yedi yoğunlukta → **sonlu**
- geçerli girdide **bit aynı** (gerileme)
- **boşluk kontrolü**: gerileme örneklemi gerçekten üç kolu da geziyor mu
- defter `ρ ≤ 0`'ı **sayıyor** ve `rho_min`'i yazıyor


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

## B2 — K21 sınıfı taraması: GPU çekirdeklerinde başka sessiz NaN var mı?

**Ne zaman:** K21 kapatıldıktan hemen sonra (4 Ağustos).
**Neden:** K21'in tehlikesi *NaN üretmesi* değil, **GPU'da sessiz** olmasıydı.
Aynı kalıp başka çekirdeklerde de olabilir.

**Nasıl:** her `wp.exp`, `wp.log`, `wp.sqrt`, `wp.pow`, `wp.acos` ve dizi
bölmesi tarandı; her biri için *"hangi fiziksel olarak erişilebilir girdi
bunu bozar?"* soruldu.

| yer | riskli ifade | sonuç |
|---|---|---|
| `damage_gradykipp:74` | `wp.acos(r)` | **kelepçeli** — `r ≤ −1` / `r ≥ 1` ayrı kollarda |
| `damage_gradykipp:58` | `1/p` (izotropik gerilmede `p = 0`) | **kelepçeli** — `p1 ≤ 0` ve `p ≤ 0` erken dönüşleri |
| `damage_gradykipp:93` | `wp.pow(oran, m)` | güvenli — `oran > 1` garantili, sonuç `wp.min` ile sınırlı |
| `eos_test:26` | `sqrt(γ·p/ρ)` | **kelepçeli** — `if p > 0` |
| `gravity_tree:35,78` | `1/sqrt(r2)` | **yumuşatılmış** — `r2 = d·d + eps2` |
| `timestep:42,64` | `sqrt(h/|a|)` | **kelepçeli** — `_TINY_C` tabanı |
| `porosity_palpha:72` | `wp.pow(t, n)` | güvenli — `t ∈ (0,1)`, `Pe < P < Ps` kollarıyla |
| `forces:61,172` | `div/ρ` | kelepçesiz; `ρ = 0`'da `inf` |
| `forces:91,133` `solid_stress:160` | `P/ρ²` | kelepçesiz; `ρ < 0`'da **sonlu**, `ρ = 0`'da `inf` |

**Sonuç: yeni kusur yok.** Son iki satır kelepçesizdir ama açığı `ρ ≤ 0`
durumudur ve o durum K21'in düzeltmesiyle birlikte **deftere işlendi**
(`nonpositive_density_count`, `rho_min`, `state_is_finite`). Yani artık
sessiz değil.

**Bu turda kapatılan boşluk:** `state_is_finite`'ın **düşme yolu** hiç
sınanmıyordu — bayrak sabit `True` olsa test yine geçerdi. `rho`, `v` ve `u`
alanlarına ayrı ayrı `NaN`/`inf` konup bayrağın düştüğü doğrulandı.

> Bulgu çıkmayan bir tarama da bilgidir: riskin **sınırı** ölçülmüş olur.

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

---

## S4 — Turun dördüncü hatası: ses hızı için kaba bir vekil kullandım

**Nerede:** FAZ 4 E2 (dinamik birikim) ölçümümde.
**Ne yaptım:** `dt`'yi kendim hesapladım: `dt = 0,2·h/c`, `c = √(P/ρ)`.

`√(2,6967e8 / 2700) = 316 m/s`. Gerçek Tillotson ses hızı (kodun kendi
`compute_timestep_solid`'i): **10150 m/s**. Yani `dt`'m **32,1 kat**
büyüktü — CFL ihlali.

**Sonuç:** koşu patladı.

```
adim   t (ms)    v_rms (m/s)     KE_ic (J)   rho sapma
   1    6.582    4.3054e-02    9.5581e+05   6.805e-04
   4   26.326    2.7414e+02    3.8750e+13   1.730e-01
   8   52.652    9.5555e+06    4.7081e+22   3.425e+02
  12   78.979    9.5555e+06    4.7081e+22   3.425e+02   <-- donmus: NaN
```

Son iki satırın **aynı** olması NaN'ın işaretiydi. Yoğunluk `ρ₀`'ın 342
katı sapmıştı; bu sırada **K21 de ortaya çıktı** — yani hatalı ölçümüm
gerçek bir kusuru açığa çıkardı, ama bu bir savunma değil.

**Ders:** `√(P/ρ)` bir **şok** ses hızı kestirimidir. Tillotson'ın küçük
sıkışmadaki ses hızını **hacim modülü** `A` belirler:
`√(A/ρ₀) = √(2,67e10/2700) ≈ 3145 m/s` — o bile 3 kat düşüktü, çünkü asıl
ifade `c² = ∂P/∂ρ|_u + (P/ρ²)·∂P/∂u|_ρ`.

> **Kural:** kodun kendi hesabı varken **elle vekil yazma.**
> `compute_timestep_solid` zaten oradaydı.

Bu, S3'ün ikizidir: orada da `dt` hakkında **ölçmeden** varsayım yapmıştım.

---

## S5 — Turun beşinci hatası: nedensel pencereyi yanlış bölgeden hesapladım

**Nerede:** aynı E2 ölçümü, `dt` düzeltildikten sonra.

Ölçümün mantığı şuydu: düzgün basınçlı bir küre, **serbest yüzeyinden**
içeri bir seyrelme dalgası gönderir. Dalga varana kadar iç bölge **tam
durgun** kalmalıdır, dolayısıyla o pencerede görülen her hareket **yapaydır**.

**Hata:** hareketi `kenar` maskesinde (yüzeye **24,8 m**) ölçtüm ama
pencereyi `arayüz` geometrisinden (yüzeye **34,6 m**) hesapladım:

```
iddia ettigim  : (70 − 35,4)/10150 = 3,41 ms
gercek         : (70 − 45,2)/10150 = 2,44 ms
kostugum       : 12 adim x 0,2049 ms = 2,46 ms   <-- DISARIDA
```

Yani son adımlar **fiziksel** dalgayı ölçüyordu, yapay kuvveti değil. Bu,
1:1 durumundaki `v ~ t^4,55` gibi tuhaf bir üssü açıklar: sabit bir yapay
kuvvet `t¹` verir, gelen bir dalga çok daha dik.

**Düzeltme:** pencere artık **ölçülen bölgenin kendi dış kenarından**
türetiliyor ve kaç adımın güvenli olduğu **koşudan önce yazdırılıyor**:

```python
r_dis = float(mk["r"][bolge].max())        # bolgenin YUZEYE en yakin noktasi
t_nedensel = (r_outer - r_dis) / c
n_guvenli = int(np.floor(t_nedensel / dt))
n_adim = min(n_guvenli, 16)
```

> **Kural:** *"bu ölçüm hangi süre boyunca geçerli?"* sorusunun yanıtı
> **ölçülen bölgeden** türetilmeli, komşu bir bölgeden değil.

Bu, K18'in dersinin bir başka yüzüdür: ölçüm = sinyal + (bu kez) **fiziksel
bir katkı**. Katkının ne zaman devreye girdiğini bilmiyorsan sinyali
okuyamazsın.

---

## S6 — Turun altıncı hatası: eşiği ölçmeden yazdım, iki kez üst üste

**Nerede:** `tests/test_mass_ratio_probe.py`, `rho_base` parametresini
koruyan boşluk kontrolünü yazarken.

`rho_base`'in **ne işe yaradığını** iki kez tahmin ettim, ikisi de yanlıştı.

### Birinci tahmin

> *"Yanlış taban yoğunluğu kullanılırsa yapay kuvvet büyür."*

**Ölçülen: `1,29e-15` — hâlâ makine sıfırı.** Test düştü.

**Neden yanlıştı:** kütleleri **tekdüze** bir çarpanla ölçeklemek FCC kafesin
simetrisini bozmaz. Düzgün bir alanda `Σ_j ∇W_ij = 0` kalır ve kuvvet doğmaz.
K7'nin zararı **tekdüze olmayan** tutarsızlıktan geliyordu (kaya ile matris
farklı `α₀` taşıyor); tekdüze bir kaymadan değil.

### İkinci tahmin

> *"Yanlış yol basıncın işaretini çevirir."*

**Ölçülen: ters yönde.** Basınç `m`'den değil `ρ` ve `α`'dan gelir:

```
rho_base VERILMEZSE : rho = 2700*1,01, alpha = 1      -> P = +2,6967e+08
```

Normal bir sıkışma. İşareti çeviren şey **benim** `rho_base`'i
**distansiyonsuz** eklememdi:

```
rho_base=2400, alpha=1  -> rho_kati = 2424 < rho0 -> P = -2,4503e+09  GERILME
```

Yani kendi düzeltmem bir kusur üretmişti ve tahminim onu yanlış yere
atfediyordu.

### Gerçek işlev

`rho_base`, `α = ρ₀/ρ_taban` kurar; `ρ_katı = ρ₀` olur ve `eps` gerçek bir
sıkışma verir — gerçek çözücünün gözenekli malzemede yaptığının aynısı
(ADR-0022/0031). Verilmezse bozulan şey **kuvvet değil, ADR-0030'un
değişmezidir**: `m/ρ = V_p` tutmaz.

### Ders

Bu, S1 ve S3'ün **aynı** hatasıdır: *sonucu ölçmeden iddia yazmak.* Bu turda
**dördüncü** kez oldu (S1, S3, S4, S6). Kalıcı kural:

> Bir eşik ya da yön iddiası yazmadan **önce** o sayıyı yazdır. Boşluk
> kontrolünün kendisi de bir iddiadır ve **o da ölçülmelidir.**

---

## S7 — Turun yedinci hatası: boşluk kontrolünü ilgili ADR'yi okumadan tasarladım

**Nerede:** `src/dartrift/validation/resolution_scaling.py`, ilk tasarım.

Sınav şuydu: *"olağan yakınsamada hata **küçülmeli** (boşluk kontrolü), sabit
`h`'de **düzleşmeli**."*

Ama **ADR-0011 bunu zaten ölçmüştü**: bu kurulumda şok yarıçapı hatası
**%3,9'luk bir tabana** oturur ve sıfıra gitmez. Sebebi ayrıklaştırma değil
**model-form**: enerji noktasal değil, şok yarıçapının ~%32'si kadar bir
bölgeye konuyor; analitik çözüm ise nokta patlaması varsayar.

Yani boşluk kontrolüm, **küçülmeyeceği bilinen** bir şeyin küçülmesini
bekliyordu.

### Ölçüm (iş 1450756) — ve iyi haber

```
(a) olagan (h/dx = 2)
     n=32  r=0.25278  hata 0.01153
     n=40  r=0.24819  hata 0.00685
     n=48  r=0.24336  hata 0.02618
     n=56  r=0.24083  hata 0.03628
     n=64  r=0.23874  hata 0.04464
  BOSLUK KONTROLU  olagan kol kuculuyor mu : False
  -> "SINAV AYIRT ETMIYOR: sonuc yorumlanamaz"
```

**Betik doğru davrandı**: boşluk kontrolü düştüğü için *"h belirliyor"*
sonucunu **vermedi**, `inconclusive` dedi. ADR-0040'ın koyduğu kural burada
beni kendi hatamdan korudu.

Ayrıca ölçülen değerler ADR-0011'in tablosuyla **birebir aynı** (0,2528 /
0,2434 / 0,2387) — yani gerileme yok, yalnızca tasarım yanlıştı.

### Doğru ölçüt: **platonun yeri**

Hata sıfıra gitmiyor ama yarıçap bir değere **oturuyor**. Soru hangi değere:

| kol | plato |
|---|---|
| `h/dx = 2` sabit (yani `h → 0`) | **0,2400** |
| `h = 0,0625` sabit | **0,2565** |

**%6,85 uzakta.** Sabit `h`'de ne kadar parçacık eklenirse eklensin `h → 0`
limitinin oturduğu yere ulaşılamıyor.

### Ders

> Bir ölçüm tasarlamadan önce, ölçtüğün büyüklük hakkında **projenin kendi
> ADR'leri** okunur. ADR-0011 tam da bu büyüklüğün neden yakınsamadığını
> anlatıyordu.


---

## S8 — Turun sekizinci hatası: eşleme kaymasını sıfıra kıyasladım

**Nerede:** `src/dartrift/validation/coupling_conservation.py` (C-2), ilk
tasarım.

**İddiam:** *"Tek parçada `Σ m a = 0`. Öyleyse eşlenmiş sistemde
`Σ_A + Σ_B` de sıfır olmalı; sapma **eşlemenin** momentum kaymasıdır."*

**Ölçtüm:**

```
lam  ortusme    n_A    n_B |    tekparca    ESLENMIS       oran
2.0     2.60   2969   1808 |   2.670e-15   9.789e-01   3.67e+14
4.0     2.60  24303   1808 |   2.670e-15   9.789e-01   3.67e+14
```

Sayı `0,9789` — devasa. **Ama λ=2 ile λ=4 için birebir aynı.**

### Aynı çıkması kurtardı

Eşleme kaymasının kütle oranından **bağımsız** olması fiziksel olarak
anlamsızdır. Demek ki ölçülen şey eşleme değildi.

**Kök neden — iki katmanlı:**

1. Bir **alt küme** için `Σ m a` zaten sıfır değildir; çevresindeki madde
   onu iter. Bu **fizikseldir**, kayma değil.
2. `B_gerçek`ten dış kabuğu (kesik komşuluklu, D1 kuralı gereği) dışlamıştım
   ve o kabuğun tepkisi **hiç sayılmıyordu**. Ölçülen `0,9789` tamamen oydu.

### Düzeltme

Doğru kıyas **sıfıra değil, tek parça cevabına**:

```
kayma = |F_eşlenmiş − F_tekparça| / ölçek
```

`F_tekparça`, **aynı bölgenin** tek çözünürlüklü ince kafeste ölçülen net
kuvvetidir. Dış kabuk etkisi **iki tarafta da** vardır ve sadeleşir.

Boşluk kontrolü de değişti: artık **tüm** parçacıklarda `Σ m a = 0` tam
olmalı — bu, aracın kalibrasyonudur, ölçülen büyüklük değil.

### Ders

> **Bir referansın sıfır olduğunu varsayma; sıfır olduğunu ölç.**
> "Tek parçada toplam sıfırdır" doğruydu — ama **hangi toplam** olduğunu
> yanlış aldım.

Ve: bir sayının **iki farklı koşulda birebir aynı çıkması**, o sayının o
koşullardan bağımsız bir şeyi ölçtüğünün en güçlü işaretidir. Bu turda
**iki kez** bu işaret hatayı yakaladı (S4'te donmuş `9,5555e+06`, burada
`0,9789`).

---

## S9 — Turun dokuzuncu hatası: kapsam doğrulaması bir kolda düşüyordu

**Nerede:** `tests/test_solver_idempotence.py`, `_eval()` saflık kapsamını
çözücüden **türetilir** hâle getirirken.

Türetilen kümenin, elle yazılan `DURUM`'u kapsadığını doğrulamak için şunu
yazdım:

```python
assert set(DURUM) <= set(izlenen)
```

**`DURUM` `D` ve `D_cbrt`'yi içeriyor, ama `damage=False` kolunda o diziler
hiç oluşturulmuyor.** O kolda doğrulama düşer.

### Yerelde görünmedi — GPU yok

Bu dosyanın **tüm** testleri CUDA ister; yerel makinede **6/6 atlanıyor
(%100)**. `pytest -q` yeşil göründü ve commit'lendi.

Ölçülen fark: yerel paket **702** test geçiyor, TRUBA'da **827** — yani
**125** test (%17,8) yalnızca GPU'da koşuyor. Bu dosyanın altısı da o
dilimde.

### G3 yakaladı

TRUBA doğrulaması (iş **1451277**, commit `52896ec`):

```
tests/test_solver_idempotence.py::test_eval_durumu_degistirmez[False-False-False] FAILED
E   assert {'D', 'D_cbrt', ...} <= {'S', 'Y0', ...}
1 failed, 827 passed, 7 skipped in 1100.83s

| C6 | Determinizm + tam test paketi | **KALDI** | pytest cikis=1 |
## SONUC: G3 GECEMEDI
```

### Düzeltme

```python
var_olan = {d for d in DURUM if hasattr(s, d)}
assert var_olan <= set(izlenen)
assert len(var_olan) >= 6      # hasattr hepsini eleyip testi BOSALTAMASIN
```

İkinci satır zorunlu: `hasattr` hepsini elerse `var_olan` boşalır ve
`set() <= X` **her zaman doğrudur** — doğrulama sessizce boşalırdı.

### Ders — ve kabul

Düzeltmeyi kanıt koşusu gelmeden **önce** yaptım; sorunu koddan tahmin
etmiştim. Ama **bozuk commit'i push'lamıştım** ve kapıyı düşüren o oldu.

> **Yerelde atlanan bir test "geçti" değildir.** `pytest -q` çıktısındaki
> `s` harfleri sayılmalı; bir dosyanın **tamamı** atlanıyorsa o dosyada
> yapılan değişiklik **hiç çalıştırılmamış** demektir.

Kapı sistemi tasarlandığı gibi çalıştı: kanıtlanamayan kriter geçmiş
sayılmadı.

## Ortak kök neden — dokuz kusurun tamamı

**Testler parçaların doğruluğunu sınıyordu, bütünün davranışını değil.**

- Hasarın formülleri doğruydu; **döngüsü** sınanmamıştı (K1).
- Krater çıkarıcı kürede doğruydu; **hedefin gerçek şekli** sınanmamıştı (K2).
- Tarama iki eksenli görünüyordu; **eksenlerin iş görüp görmediği** (K3).
- Yarıçap kestirimi vardı; **varsayılan yol hiç koşulmamıştı** (K4).
- C2 kütleyi, C3 yoğunluğu ölçüyordu; **tutarlılığı** kimse ölçmüyordu (K7).
