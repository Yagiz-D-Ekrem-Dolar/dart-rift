# KAYIT-017 — Üçüncü tur: denetim kodunun kendisi (2026-08-03)

**Kapsam:** K13–K20, B1, S2 · **ADR:** 0034–0040
**Sonuç:** 8 kusur + 1 kapsam boşluğu + 1 süreç hatası.
**Önceki:** [KAYIT-016](KAYIT-016_2026-08-02_hata-ayiklama-turu.md) (K1–K6),
ikinci tur K7–K12 (ADR-0030…0033).

---

## 0. Bu turun karakteri

İlk iki tur **üretilen kodu** hedefledi. Bu tur **onu denetleyen kodu**
hedefledi ve orası daha verimli çıktı.

Soru şuydu:

> Bir kriter "GEÇTİ" diyorsa, **geçme sebebi** ölçülmüş müdür?

Sekiz kusurun tamamı bu sorudan çıktı ve dört alt biçime ayrıldı:

| biçim | kusur | örnek |
|---|---|---|
| yanlış **büyüklüğü** ölçüyor | K13 | kütle kesri ↔ hacim hedefi |
| **vekil** ölçüyor | K14, K16-b | eşdeğer küre yarıçapı ↔ gerçek mesh |
| **yanlı örneklemde** ölçüyor | K15 | örneklem, ölçülen büyüklükle seçiliyor |
| yanlış **davranış** bekliyor | K16 | monoton olmayan büyüklüğe "yakınsıyor" |
| **hiç düşemiyor** | K19-B, K20 | özdeşlik, kendini doğrulayan koşul |

Ve bir tanesi bunların hiçbiri değildi — **kontrolün adı yanlıştı** (K17).

---

## 1. K13 — Blok kesri kütle olarak ölçülüyordu

### Belirti
ADR-0030+0031 sonrası **G3 C2 kaldı**: *"blok kesri 0.433 (hedef 0.30)"*.
Bu sefer pytest **geçiyordu** — kriterin kendisi düşüyordu.

### İlk soru
*Üretici mi bozuk, ölçü mü yanlış?* Bu soruyu sormasaydım üreticiyi
"düzeltmeye" başlardım ve doğru kodu bozardım.

### Ölçüm
```
hedef (hacim)                     0.3000
ölçülen HACİM kesri               0.3034   (+%1,1)   <-- ÜRETİCİ DOĞRU
ölçülen KÜTLE kesri (eski kod)    0.4335   (+%44,5)  <-- yanlış büyüklük
```

Kapalı formla 6 hane doğrulandı:
```
f_kütle = f_h·r / (f_h·r + 1 − f_h),   r = m_blok/m_matris
f_h = 0,3034 ,  r = 1,7565            ->  0,433483
ölçülen                                   0,433483
```
ve `r = α_matris/α_blok = 1,8443/1,05` — **ADR-0030'un doğrudan sonucu**.

### Neden şimdi çıktı
Tekdüze kütlede kütle kesri = hacim kesri. ADR-0030 blokları %65
ağırlaştırınca ikisi **ayrıştı**. Yani ADR-0030 bir kusur **yaratmadı**,
var olan bir kusuru **görünür kıldı**.

### Çözüm
Kriter `boulder_volume_fraction` okur; kütle kesri **ayrı adla** raporlanır
(fiziksel olarak anlamlı ama hedefle karşılaştırılmaz).

### Ders
> **Bir kriter kaldığında ilk soru "üretici mi bozuk, ölçü mü yanlış?"
> olmalıdır.**

---

## 2. K14 — "Mermi dışarıda mı" vekil ölçütle

### Nasıl bulundu
K12/K13 deseni sahne bütünlüğü kriterine uygulandı: `imp_dist > target_radius`.
`target_radius` **eşdeğer küre** yarıçapı — yalnızca küre için geçerli.

### Ölçüm (elipsoit 88×87×65 m, r_eff = 39,59 m)
| eksen | mermi min uzaklık | vekil | mesh içinde | gerçek |
|---|---|---|---|---|
| kısa (z) | 32,63 m | **False** | **0/207** | dışarıda |
| uzun (x) | 44,13 m | True | 0/207 | dışarıda |

Kısa eksende **yanlış negatif**. Ters yön de mümkün: uzun eksende yüzey
r_eff'ten 4,4 m dışarıda olduğu için, r_eff'i geçen ama gövdeye **gömülü** bir
mermi "dışarıda" sayılırdı.

### Ara adım — kendi ölçümüm kirlendi
İlk denemede "o yöndeki yüzey"i eksen yakınındaki parçacıkların
`max |x|`'inden tahmin ettim ve **32,97 m** buldum; mermi 32,63'te olduğu için
"örtüşme var" gibi göründü. Tahminim eksen dışı parçacıklarla kirlenmişti.
**Kesin soruyu** sordum — *herhangi bir mermi parçacığı mesh'in içinde mi?* —
ve `inside_points` ile **0/207** çıktı. Yerleştirme kodu doğruymuş.

### Çözüm
Doğrudan `inside_points`; sınav **düzensiz cisimde** de koşuyor. G3 C6
`irregular_all_outside` şart koşuyor. Üçüncü test bir **boşluk kontrolü**:
*vekil gerçekten yanılıyor mu?*

---

## 3. K15 — İç bölge, ölçülen büyüklüğün kendisiyle seçiliyordu

### Kod
```python
coordination_interior_mean = np.mean(cn[cn >= np.median(cn)])
```
Parçacıklar **komşuluk sayısına göre** seçilip sonra komşuluk ortalanıyor.

### Ölçüm (ikosfer r=100, aralık 10)
| durum | eski ölçüt | gerçek iç ortalama |
|---|---|---|
| bozulmamış FCC | 12,00 | 12,00 |
| **%25 bozuk kafes** | **11,19** | **10,25** |
| %50 bozuk | 9,73 | 9,05 |
| %75 bozuk | 9,35 | 8,45 |
| tamamen rastgele | 15,20 | 13,31 |

Kapının bandı `[11,0 ; 12,01]`. **Parçacıkların dörtte biri 0,35·aralık
kaydırılmış bir yığın geçiyordu**; gerçek değeri 10,25.

Ek gözlem: rastgele bulut **15,20** verdiği için **üst** sınır işini
görüyordu; bozulmuş kafesi yakalayamayan **alt** sınırdı.

### Çözüm
İç bölge **geometrik**: yüzeyden ≥ 2,5·aralık. Eski ölçüt
`coordination_selfselected_mean` adıyla ayrıca raporlanıyor — **ikisi
arasındaki fark kafes düzgünlüğünün doğrudan göstergesi** (bozulmamış FCC'de
tam 0,0).

### Ders
> **Bir alt kümeyi, ölçmek istediğin büyüklüğe göre seçme.**

---

## 4. K16 — "Yakınsıyor" ölçütü monoton olmayan bir büyüklüğe bakıyordu

### Ölçüm
```
N:     207    399    803   1568   3184   6401  12808
kalıntı: .035  .0025 .00375 .02000  .005 .00016 .00063
```
Bir adımda **+0,01625 artıyor**.

Kriter `rows[0] > rows[-1]` idi ve sonucu **hangi N'lerin seçildiğine bağlı**:
- `(200, 800, 3200)` → **True** (mevcut seçim)
- `(400, 800, 1600)` → **False**

### Kök neden
`volume_error = |N·V_p − V_küre|/V_küre` kafesin küreye **nasıl oturduğunun**
kalıntısı — yakınsaması **beklenen** bir büyüklük değil.

### Gerçekten yakınsayan
çap boyunca parçacık: **6,46 → 25,86**, kesin artan.
Doğrulama: `25,86/6,46 = 4,00` vs `(12808/207)^(1/3) = 3,94` ✓

### Yan bulgu (K16-b)
`starts_outside_target` eşiği elle yazılmış `> 80.0` idi — mesh yarıçapına
eşit (tesadüfen doğru) ama **sabit sayı**. K14'ün mesh üyeliği ölçüsüne
bağlandı.

---

## 5. K17 — Kenar-manifold kontrolü ters sarımı göremiyordu

### Nasıl bulundu
Soru: *"manifold" adı neyi garanti ediyor?* Kod kenarları **sıralayarak**
sayıyor — `(a,b)` ile `(b,a)` aynı.

### Ara adım — kendi ölçümüm yanlıştı
İlk probumda `mesh.is_edge_manifold` yazdım, **parantezsiz**. Çıktı
`<bound method>` verdi ve bir an "her zaman truthy, kriter hiç çalışmıyor"
sandım. Kullanım yerlerini denetledim: hepsi `()` ile çağırıyor. **Kodda
kusur yoktu, ölçümümde vardı.** Düzeltip yeniden ölçtüm.

### Ölçüm (ikosfer(3), yüzler ters çevrilerek)
| ters yüz | `is_edge_manifold()` | hacim hatası |
|---|---|---|
| 1 | **True** | %0,109 |
| 5 | **True** | %0,764 |
| 20 | **True** | %3,112 |
| 100 | **True** | **%15,545** |

### Neden önemli
Mesh hacmi **üç** yere giriyor: yığın yoğunluğu (`Σm/V_mesh`), blok hacim
hedefi (`f_boulder·V_mesh`), etkin yarıçap (kaçış hızı, bağlanma enerjisi).

Analitik şekillerde C1'in hacim kontrolü yakalar. **Yüklenen OBJ'de — gerçek
PDS Dimorphos modelinde — karşılaştırılacak analitik hacim YOK.**

### Çözüm
`is_consistently_oriented()`: her **yönlü** kenar tam bir kez.

### Beklemediğim sonuç
Yazdığım test *"delik ikisini de bozar"* diye **tahmin** ediyordu ve düştü.
Ölçülen:

| bozulma | manifold | yönelim |
|---|---|---|
| delik | **False** | True |
| ters sarım | True | **False** |

Kod doğru: kapalılık ile yönelim **ayrı** özellikler — ve tam bu yüzden ikisi
de gerekli. Testi ölçülen davranışı yazacak şekilde düzelttim.

---

## 6. K18 — Krater ölçütü yanlılık ile sinyali karıştırıyordu

### Nasıl bulundu
Elle yazılmış eşikler tarandı: `abs(global_radius_change) < 5.0` — 5,0
nereden geliyor?

### Ölçüm (80 m küre, 40000 parçacık)
| durum | `global_radius_change` | yanlılıktan sapma |
|---|---|---|
| **deformasyonsuz** | **−1,5335 m** | — (saf yanlılık; gerçek 0) |
| 16 m kraterli | −1,5335 m | **+0,0000 m** |
| %10 küresel büzüşme | −9,3802 m | **−7,8466 m** (beklenen ≈ −8) |

**Çıkarıcı mükemmel ayırıyor.** Kusur ölçütteydi: `global_radius_change`
yüzey örneklem yanlılığı ile gerçek deformasyonun **toplamı**; 5,0 yalnızca
yanlılığı (1,53) barındıracak kadar genişti.

### Çözüm
Yanlılık **deformasyonsuz cisimden** ölçülür; kriter **farka** bakar
(`|excess| < 0,5` — 10 kat dar). **Pozitif kontrol** eklendi: %10 büzüşme
gerçekten yakalanmalı — yoksa "ayrışıyor" iddiası boş bir doğru olur; her şeye
"0" diyen bir çıkarıcı da onu sağlar.

---

## 7. K19 — Denetleyicinin kendi ölçütleri

**A.** RT7 kütle kesri ölçüyordu (K13'ün ikinci sahnesi).

**B.** RT11'de kendini doğrulayan koşul:
```python
anahtar = ["denge", "ZATEN", "KAPSAM DISI" if "KAPSAM DISI" in doc else "hesaplanabilir"]
```
Üçüncü anahtar **belgede varsa onu arıyor** — asla düşemez. Ölçüldü: belgede
`"KAPSAM DISI"` **yok**, `"hesaplanabilir"` **var** → otomatik sağlanıyor.
RT11 üç anahtar arıyor gibi görünüp **ikisini** sınıyordu; üstelik ikisi de
**dize eşleşmesi** — RT12'nin düzeltilmiş günahı.

**Çözüm:** RT11 davranışsal — bir iddia, onu destekleyen **ölçümü**
döndürmedikçe geçerli sayılmaz.

---

## 8. K20 — G1 C7 bir özdeşliği sınıyordu

```python
binding_cfl_viscous_pct  = 100.0 * n_cfl / n
binding_acceleration_pct = 100.0 * (n - n_cfl) / n
# kriter:
abs(a + b - 100.0) < 1e-9
```
Toplam **inşaat gereği** 100. `1e-9` toleransı yalnızca kayan nokta
yuvarlaması içindi. Kriterin düşebileceği tek gerçek koşul `n_steps > 0` idi.

**Çözüm:** düşebilecek şartlar — alanlar tam, yüzdeler `[0,100]`,
`0 < dt_min ≤ dt_max < ∞`, ve **log anlamlı mı**: `dt_max > dt_min`.

Bu üç örnek (K15, K19-B, K20) **ADR-0040**'ta tek kurala bağlandı.

---

## 9. B1 — `dt` hesabı hiç çapraz kontrol edilmemiş

### Nasıl bulundu
Yapısal denetim: **16 GPU çekirdeği** ile **5 CPU referansı** eşleştirildi.
Tek boşluk `timestep` çıktı.

Üstelik mevcut çapraz kontroller **sabit** `DT = 5.0e-7` kullanıyor — GPU ile
CPU farklı `dt` seçseydi bu testler **görmezdi**. ADR-0028'de ölçülen enerji
kayması tam olarak `O(dt)` kesme hatasıydı; `dt` doğrudan bilimsel sonuca
giriyor.

### Sonuç
`TestTimestepCross` eklendi. **Eşitlik geçti** — `dt_CPU == dt_GPU` (rel 1e-12)
her durumda. Yani kod doğruymuş; boşluk sınamadaydı.

### Kendi hatam (bkz. §10)
Boşluk kontrolüm düştü: `dt`'nin hızla değişeceğini varsaymıştım.

---

## 10. S2 ve turun kendi hataları

Bu turda **üç kez** kendi ölçümüm/varsayımım yanlış çıktı. Üçünü de
kaydediyorum çünkü yöntemin bir parçası:

| # | ne oldu | nasıl anlaşıldı |
|---|---|---|
| a | `is_edge_manifold` **parantezsiz** çağrıldı → "kriter hiç çalışmıyor" sanısı | kullanım yerleri denetlendi: hepsi `()` ile |
| b | *"delik ikisini de bozar"* tahmini | test düştü; ölçülen davranış yazıldı |
| c | *"dt hızla değişir"* tahmini | boşluk kontrolü düştü: yayılım **%1,9** |

**(c)'nin fiziği:** CFL kısıtı **ses hızına** bağlıdır (Tillotson bazaltta
~5000 m/s); denenen parçacık hızları (1,5–150 m/s) onun yanında ihmal
edilebilir. `dt` gerçekten `h` ve `cfl` ile oynar — sınav onlarla kuruldu.

Ayrıca **S2**: kusur kaydının kendisi sessizce eksik kalmıştı. `str.replace`
çapası `"hatasi"` yazıyordu, dosyada `"hatası"` (Türkçe **ı**) — eşleşme
olmadı, **üç bölüm birden** kayboldu:
```
tablo : K1..K9 K11 K12 S1   -> 12 kimlik
gövde : K1..K9 S1           -> 10 kimlik      (kayıp %23,1)
```
Artık **belge de sınanıyor** (`test_docs_registry.py`): tablo↔gövde birebir,
kimlikler kesintisiz, her kayıtta en az bir ölçülen sayı, anılan her ADR
diskte. Test yazıldığı anda işe yaradı — S2'yi yanlış sırada ve ölçümsüz
eklemiştim, ikisini de yakaladı.

---

## 11. Turun sonucu

TRUBA H100 (iş 1450286, commit `a5d9fa2`) — düzeltmelerin toplu ölçümü:

```
M0 alpha=1.5000  M1 alpha=1.7273   hacim=[1.000000, 1.000000]
blok hacim=0.3034 (hedef 0.30, hata %1.15)   kütle=0.4335
komşuluk GEOMETRİK iç=12.00 (n=4226)   kendi-seçen=12.00
çap boyunca [6.46, 10.26, 16.29]  artan=True
kalıntı [0.035, 0.00375, 0.005]  monoton=False  zarf küçülüyor=True
mermi mesh içinde [0, 0, 0]
krater: yanlılık=-1.5335  fazlalık=0.000000  büzüşme=-7.8466  yakalandı=True
düzensiz hepsi dışarıda=True   vekil yanılıyor=True
manifold=True   YÖNELİM=True
```

Yerel takım **596 geçti / 0 kaldı**.

---

## 12. Bu turdan kalan kural

Bir kriter yazarken **düşme senaryosu** açıkça düşünülür:

1. Örneklem, ölçülen büyüklükten **bağımsız** seçilmeli.
2. Eşik, karşılaştırılan veriden **türetilmemeli** — türetiliyorsa bağımsız
   bir **taban** ölçülmeli.
3. **Özdeşlikler kriter olamaz.**
4. Her "ayrışıyor / çalışıyor / yakınsıyor" iddiası bir **pozitif kontrol**
   ister.
5. Bir büyüklüğün "yakınsadığını" iddia etmeden önce, o büyüklüğün
   yakınsaması **beklenen** bir büyüklük olup olmadığı sorulmalıdır.
6. Bir kontrolün **adı**, neyi kontrol ettiğini söylemeyebilir.
