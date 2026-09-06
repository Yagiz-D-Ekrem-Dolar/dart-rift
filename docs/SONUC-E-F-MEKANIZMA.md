# E ve F kampanyası sonucu — bir mekanizma bulundu, iki iddia düştü

**Tarih:** 2026-09-06 · **İşler:** `1548148` (E, 6 kol), `1548149` (F, 6 kol)
**Ölçütler:** `PROTOKOL-E1-ERKEN.md` v2, `PROTOKOL-E2-CEKME.md`,
`PROTOKOL-F-AV.md` — **hepsi koşudan önce commit'lendi**

---

## Özet

| kampanya | ölçütün dediği |
|---|---|
| **E2 — çekme** | **ÇEKME HİPOTEZİ DESTEKLENİYOR** |
| **E1 — şok** | *"Çözücü kusuru"* — **hâlâ açık**; çürüttüğünü sandığım kol da düştü (A61) |
| **F — AV** | **SONUÇSUZ** (monotonluk ölçülemedi) |

Ve iki bulgu daha:

1. **Şok depoda ilk kez gözlendi.** `E1a`'da sıkışma
   `%14 → %69,2 → %53`, zirve `t = 8,61e-05 s` — öngörülen geçiş
   süresi `6,0e-05 s`. Gözeneklerin **`%96`'sını** kapatıyor ve
   orada duruyor.
2. `t = 0,024 s`'te **18,7 ton** madde `6,7 m/s` ile dışarıda;
   `t = 0,2 s`'te geriye **93 kg** kalıyor. Kazı akışı **doğuyor ve
   ölüyor**.

> **Bu belgede bir iddiayı kendim çürüttüm.** İlk yazdığım
> *"üretim AV'si şoku bastırıyor"* **yanlıştı**; dayanağı olan
> `ρ = 2891,5` şok değil **kümelenme** çıktı (§2.1, rapor A61).

---

## 1. E2 — matris çekmesi kazıyı durduruyor

### Ön koşul sağlandı

Protokol şart koşuyordu: *"iki kolun `ρ_max` gidişi örtüşmeli;
örtüşmezse deney sonuçsuzdur."*

| | E2a (üretim) | E2b (kırpık) |
|---|---:|---:|
| `ρ_max` zirve | `2601,6` | `2601,6` |
| bağıl fark, medyan | — | **`%0,007`** |
| bağıl fark, max | — | `%0,072` |

Şoklar **birebir aynı**. Fark yalnız çekmeden gelebilir.

### Karar niceliği 1 — `v_r` dağılımı (yüzey kabuğu `73,75 – 81,94 m`)

| kol | medyan | `p95` | max |
|---|---:|---:|---:|
| E2a (üretim) | **`−0,177`** | `0,575` | `1,52` |
| E2b (kırpık) | **`+0,094`** | **`13,8`** | **`37,6`** |

`p95` **`24` kat** artıyor. Ve medyan **işaret değiştiriyor**:
üretimde yüzey **içeri** doğru hareket ediyor — krater kapanması
doğrudan ölçüldü. Çekme kırpılınca dışarı dönüyor.

Dış kabukta (`81,94 – 90,13 m`) fark daha da keskin:
`55` parçacık → **`3 286`**; medyan `0,131 → 29,1 m/s`.

### Karar niceliği 2 — kaçış hızını aşan kütle, `r > R` şartı **olmadan**

Cismin **içinde** ama `v_r > 10 m/s` olan madde:

| kol | `n` | `M` |
|---|---:|---:|
| E2a | **`0`** | `0 kg` |
| E2b | **`3 375`** | **`23 250 kg`** |

Üretim kolunda cismin içinde `10 m/s`'yi aşan **tek parçacık yok**.

### Karar niceliği 3 — krater gidişi

| `t` | E2a | E2b |
|---|---:|---:|
| `0,0078` | `0,242` | `0,355` |
| `0,0155` | `0,590` | `0,981` |
| `0,0233` | **`0,780`** | **`1,457`** |

`24 ms`'te **`1,87` kat derin**, ve ikisi de hâlâ açılıyor.

### Dışlama maddesi uygulanmıyor

Protokol: *"Fark yalnız birkaç kaba parçacıktan geliyorsa sonuçsuz."*

Kaçan kütlenin inceltme seviyesi dağılımı:

| kol | dağılım |
|---|---|
| E2a | `16×5,83 kg`, `26×372,8 kg`, `3×2 983 kg` — **kabaya baskın** |
| E2b | **`3 139×5,83 kg`**, `141×46,6 kg`, `35×372,8 kg`, `3×2 983 kg` |

E2b'nin farkı **en ince seviyeden** geliyor. Madde uygulanmıyor.

### Çekme oranı doğrudan görünüyor

Matris parçacıklarının `P < 0` olan kesri:

| `t` | E2a | E2b |
|---|---:|---:|
| `0,0078` | `%27,9` | `%2,9` |
| `0,0155` | `%41,5` | `%1,7` |
| `0,0233` | **`%47,6`** | `%3,8` |

Üretimde matrisin **yarısına yakını** çekme taşıyor ve oran
**zamanla artıyor**.

### **YARGI: ÇEKME HİPOTEZİ DESTEKLENİYOR**

Üç karar niceliği de öngörülen yönde ve büyük farkla; ön koşul
sağlandı; dışlama maddesi uygulanmıyor.

`Δβ_hedef`: `0,0352 → 0,2715` (**`7,7` kat**).

---

## 2. E1 — ölçüt *"çözücü kusuru"* dedi, **çürütüldü**

### Ölçütün dediği

Koşu boyunca `ρ_max` (eşik `2702,7`):

| kol | `ρ_max` | `t_zirve` | katı sıkışan |
|---|---:|---:|---:|
| E1a (üretim) | `2601,6` | `8,61e-05 s` | `0` |
| E1b (`α` donuk) | `2571,4` | `1,00e-03 s` | `0` |

Kilitli tabloya göre: *"`ρ_max ≤ 2702,7` her ikisinde → **Çözücü
kusuru.** Ezilme dondurulmuşken bile katı sıkışmıyorsa sorun P-α'da
değil. **En ağır sonuç.**"*

### Çürüttüğünü sandığım kol — **ve onun da çürümesi**

**E3 kolu:** aynı çözücü, aynı sahne, tek değişen `α_av`.

| `α_av` | `ρ_max` | katı sıkışan | zirve sıkışma |
|---:|---:|---:|---:|
| `1,0` (üretim) | `2601,6` | `0` | `%69,2` |
| `0,4` | `2658,8` | `0` | `%73,0` |
| **`0,1`** | **`2891,5`** | **`46`** | **`%88,1`** |

İlk okumam: *"çözücü katı sıkışması üretebiliyor; üretim AV'si onu
bastırıyor."*

#### O okuma da düştü (A61)

Katı sıkışan parçacıklara **nerede olduklarını** sordum:

| ölçüm | değer |
|---|---:|
| katı sıkışan (`t = 24 ms`) | `8` |
| hepsinin kütlesi | `5,826 kg` — en ince seviye |
| **en yakın komşu, medyan** | **`0,2013 m`** |
| ince seviye aralığı | `0,35 m` |
| oran | **`0,575`** |

Nominal aralığın `%57`'sinde paketlenmişler; eşdeğer yoğunluk artışı
`(1/0,575)³ = 5,26` kat. Bu **çekme kararsızlığı** (kümelenme),
düşük AV'de bilinen SPH kusuru.

İkinci kanıt zamanlama: katı sıkışma `1,27e-03 s`'te başlayıp
`24 ms`'e kadar **sürüyor**. Gerçek şok cephesi geçicidir —
E1a'da öyle davrandı.

### Geriye ne kalıyor

| iddia | durumu |
|---|---|
| Şok oluşuyor ve gözlendi | **ayakta** |
| Gözeneklerin `%96`'sı kapanıyor | **ayakta** |
| Hiçbir kolda temiz katı sıkışma yok | **ayakta** |
| *"AV şoku bastırıyor"* | **DÜŞTÜ** |
| E1'in *"çözücü kusuru"* yargısı | **hâlâ açık** |

**E1'in sorusu cevapsız kaldı.** Şok gözeneği kapatıyor ve duruyor;
bunun gözenekli hedefte beklenen fizik mi yoksa çözünürlük
yetersizliği mi olduğu **ayrılmadı**.

### Ve bu benim tasarım hatam

E1 **iki kollu** kuruldu ve o iki kol *"çözücü yapamıyor"* ile
*"bu ayarda yapmıyor"* arasını **ayırt edemiyordu**. Ayırt eden kol
(E3) E1'in tasarımının parçası değildi; aynı diziye başka bir soru
için konmuştu.

> Yargıyı **kolun kendisi** çürütmedi — **eksik kol** çürüttü.
> Kilitli ölçüt yanlış değildi; **yetersizdi**.

Ölçütün literal yargısı kayda geçiyor ve **çürütüldüğü** de
kayda geçiyor. Ölçüt geriye dönük değiştirilmiyor (A45 ile aynı usul).

### E1 bir şeyi de **kanıtladı**

Şok gerçekten yakalandı: E1a'nın zirvesi `t = 8,61e-05 s`, öngörülen
geçiş süresi `r_mermi/Us = 6,0e-05 s`. Yoğun izleme (`--iz-every 2`)
çalıştı ve **depoda ilk kez canlı şok görüldü** (A45'in açtığı boşluk
kapandı).

---

## 3. F — SONUÇSUZ, ve raporum bunu yanlış söylüyordu

| kol | `N` | `α_av` | `M_kaçan` | `⟨v⟩` | `n` | şok |
|---|---:|---:|---:|---:|---:|---|
| `F_kaba_av10` | `17 201` | `1,0` | `17 896` | `−0,292` | `6` | KISMI |
| `F_kaba_av04` | `17 201` | `0,4` | `4 148` | `−0,120` | `12` | SOK_VAR |
| `F_kaba_av01` | `17 201` | `0,1` | **`0`** | `nan` | **`0`** | SOK_VAR |
| `F_orta_av10` | `69 886` | `1,0` | `18 735` | `−6,698` | `45` | KISMI |
| `F_orta_av04` | `69 886` | `0,4` | `18 653` | `−0,309` | `31` | SOK_VAR |
| `F_orta_av01` | `69 886` | `0,1` | **`0`** | `nan` | **`0`** | SOK_VAR |

`α_av = 0,1` kolunda `t = 0,024 s`'te **hiç ejekta yok** → monotonluk
sınavı **değerlendirilemiyor**.

Betiğim bunu *"ETKI YOK ya da TUTARSIZ — AV aday olmaktan çıkar"*
diye raporladı. **Veri o sonucu desteklemiyor** (rapor A58).
Düzeltildi: artık `SONUÇSUZ — monotonluk ÖLÇÜLEMEDİ` diyor.

**F'nin doğru yargısı: SONUÇSUZ.** AV ne elendi ne doğrulandı.
(İlk yazdığım *"aksine E1/E3 onun şok üzerindeki etkisini ölçtü"*
cümlesi de **geçersiz** — o ölçüm kümelenmeymiş, A61.)

---

## 4. Ölçülmemiş ama büyük: akış doğuyor ve ölüyor

Aynı düzenek, iki zaman:

| `t` | `M_kaçan` | `⟨v⟩` | `n` |
|---|---:|---:|---:|
| `0,024 s` (E2a) | **`18 735 kg`** | `−6,70 m/s` | `45` |
| `0,200 s` (L2_taban) | **`93 kg`** | `−1 264 m/s` | `16` |

`24 ms`'te `18,7` ton madde `6,7 m/s` ile dışarıda. `200 ms`'te
geriye `93 kg` kalıyor ve o da `1 264 m/s`'lik **jet**.

Aradaki `176 ms`'te `18,7` ton madde `8 cm/s`'nin altına yavaşladı.
Yani kazı akışı **doğuyor** — sonra **duruyor**.

E2'nin ölçtüğü kuvvet bunu açıklıyor: yüzeyin medyan `v_r`'si
üretimde **negatif** (`−0,177 m/s`), yani madde geri çekiliyor.

---

## 5. Şimdi ne biliyoruz

```
sok olusuyor (OLCULDU: zirve 8,61e-05 s, sikisma %69,2)
   ->  gozeneklerin %96'sini kapatiyor ve ORADA DURUYOR
       [bu beklenen fizik mi, cozunurluk mu -- AYRILMADI]
   ->  kazi akisi yine de doguyor (18,7 ton @ 6,7 m/s, t = 24 ms)
   ->  MATRIS CEKMESI onu geri cekiyor
       (-15,19 MPa, Y0'dan bagimsiz; yuzey v_r medyani -0,177 m/s)
   ->  200 ms'te geriye 93 kg jet kaliyor
```

**Ölçülen ve ayakta kalan tek mekanizma: çekme.** Zincirin ilk
halkası (şokun gözenekte durması) hâlâ açık bir soru.

## 6. Bu bir üretim çözümü **değil**

`--matris-cekme-yok` granüler malzemenin basınca bağlı sürtünmesini
modellemiyor; negatif basıncı **sıfırlıyor**. Uzmanın dediği gibi bu
*"hangi kuvvetin kazıyı durdurduğunu ayıran kontrol deneyi"*.

Gerçek çözüm ayrı bir tasarım kararıdır (ADR) ve uzmana sorulan
açık sorulardan biri (`UZMANA-YANIT.md` §5.1).
