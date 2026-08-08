# KAYIT-035 — `Ω` çelişkisi **ölçülerek** çözüldü (2026-08-08)

**Kapsam:** FAZ 4.3b · **Durum:** ölçüldü — ADR-0041 §5b madde 2 **boş
çıktı**, madde 4 korunuyor
**Öncül:** [ADR-0041](../adr/ADR-0041-yerel-incelme-yaklasimi.md) (kilitli),
[KAYIT-034](KAYIT-034_2026-08-04_A-prime-GPU-dogrulandi.md)

---

## 0. Çelişki

ADR-0041 §5b'nin kilitlenen sözleşmesinde iki madde birbirini kesiyor:

| madde | metin |
|---|---|
| **2** | `Ω` (grad-h) düzeltmesi **uygulanır** |
| **4** | skaler `h` yolu **bit düzeyinde korunur** |

`Ω`'nın türetimi baştan sona bir **zincir kuralıdır**:

```
Ω_i = 1 − (∂h_i/∂ρ_i) · Σ_j m_j ∂W_ij/∂h_i
```

`∂h_i/∂ρ_i` çarpanı **yalnızca** `h_i = η(m_i/ρ_i)^{1/3}` bağıntısından
gelir. Kod okundu: `h`, `solver_solid.py:82`'de bir kez atanıyor ve **hiç
evrilmiyor**. Sabit `h` ⇒ `∂h_i/∂ρ_i = 0` ⇒ **`Ω_i ≡ 1`, tam olarak**.

> Yani madde 2 mevcut `h` politikasında **boştur**. Üstelik `Ω`'yı yine de
> hesaplayıp uygulamak madde 4'ü **kırardı** — skaler `h`'de bile `Ω ≠ 1`
> çıkar ve basınç terimi değişir.

Bu sessizce bir tarafa çözülemez (RULES.txt: kilitli karara sessiz
değişiklik yok). Çözüm bir tercih değil, bir **ölçüm**: sabit `h` yeterli mi?

---

## 1. Ölçülen büyüklük

Sabit `h` ve sabit parçacık kütlesiyle `N_komşu ∝ ρ`. Şok 4 kat
sıkıştırırsa komşu sayısı 4 katına çıkar. Soru: **doğruluk bu aralıkta
değişiyor mu?**

### Çalışma noktası ölçüldü (tahmin edilmedi)

Gerçek bir Sedov koşusunda (n = 64, H200), iç bölgede:

| büyüklük | değer |
|---|---|
| `N_komşu` (`p01`) | **268,2** |
| `N_komşu` (`p99`) | **551,5** |
| salınım `p99/p01` | **2,056×** |

---

## 2. Deneyin kurgusu — ve **kendi tasarım iddiamın düzeltilmesi**

`h` sabit tutulup `dx` tarandı. İlk yazdığımda modül başlığına şunu
yazmıştım:

> *"O zaman çözülen ölçek sabittir, yalnızca `N_komşu` değişir. Plato
> kırılıyorsa suçlu komşu sayısıdır."*

**Bu yanlıştı.** Sabit `h`'de `dx`'i değiştirmek komşu sayısını **ve**
ayrıklaştırma hatasını aynı anda değiştirir — ikisi **tek düğmedir**.
Ölçülen eğri bunu açıkça gösteriyor: hata `%17,03 → %2,87` ve hâlâ
**düşüyor**, yani sabit-`h` platosuna oturulmamış.

> **Ama ölçüm yine de sonuç veriyor**, çünkü aranan şey bir **üst
> sınırdır**. Çalışma aralığındaki yayılım hem `dx` yakınsamasını hem komşu
> sayısını içerir; komşu sayısının **tek başına** payı bundan **küçüktür**.

Yargı bu yüzden *"komşu sayısı etkisizdir"* değil, ***"etkisi şu üst
sınırın altındadır"***.

İkinci sınır da yazılıyor: deney `N_komşu`'yu koşular **arasında, tekdüze**
değiştiriyor; gerçek bir çarpışmada tek bir parçacığın komşu sayısı **zaman
içinde** salınır. Aynı şey değil — makul gösterge, kesin kanıt değil.

---

## 3. Ölçüm (job 1460675, H200, `h = 0,03125` **sabit**)

| `n` | `N_komşu` | `r_ölç` | hata | çalışma aralığında |
|---|---|---|---|---|
| 38 | 56,1 | 0,207348 | %17,03 | dış |
| 60 | 220,9 | 0,237069 | %5,13 | dış |
| **67** | **307,6** | **0,240342** | %3,82 | **iç** |
| **72** | **381,7** | **0,240682** | %3,69 | **iç** |
| **78** | **485,3** | **0,241804** | %3,24 | **iç** |
| 86 | 650,5 | 0,242723 | %2,87 | dış |

| yargı | değer |
|---|---|
| aralık kapsıyor | **True** (56,1 → 650,5 ⊇ 268,2 → 551,5) |
| çalışma noktası sayısı | **3** |
| tüm yayılım | %14,71 |
| **çalışma aralığındaki yayılım** | **%0,607** |
| tolerans | %2 |
| **karar** | **`sabit_h_yeterli`** |

> **`N_komşu` çalışma aralığında 2,06 kat değişirken ölçülen yarıçap
> `%0,607` oynuyor** — toleransın üçte biri. Ve bu bir **üst sınır**.

`n = 38`'deki `%17,03` hata yargıya **girmiyor**: `N_komşu = 56` çalışma
noktasının çok altında ve oradaki hata `dx` yakınsamasıdır, komşu sayısı
duyarlılığı değil.

---

## 4. Sonuç — sözleşme nasıl düzeltiliyor

| madde | eski | yeni |
|---|---|---|
| 1 | simetrik `h_ij = ½(h_i+h_j)` | **değişmedi** |
| **2** | `Ω` uygulanır | **`h` sabit olduğu için `Ω ≡ 1`; ayrı bir kod yolu YOK** |
| 3 | CPU referansı + çapraz kontrol | **değişmedi** (KAYIT-034'te doğrulandı) |
| 4 | skaler `h` bit korunur | **değişmedi** — ve madde 2'nin yeni hâli bunu artık **desteklıyor** |

Bir madde daha **ekleniyor**:

> **5. `h` sabittir** (kurulumda atanır, evrilmez). Bu bir ihmal değil, ADR-0042
> ile **kilitlenen bir karardır**; gerekçesi bu kayıttaki ölçümdür. `h`
> evrilmeye başlarsa `Ω` **zorunlu** hâle gelir ve madde 4 yeniden
> değerlendirilir.

Sabit `OMEGA_IS_UNITY_WHEN_H_FIXED` ve onu sınayan test bu yüzden var:
ileride biri `Ω`'yı sabit `h` yolunda hesaplamaya kalkarsa test kırılır.

---

## 5. Bu kayıtta yakalanan kendi hatalarım

| # | hata | nasıl yakalandı |
|---|---|---|
| 1 | "yayılım varsa suçlu komşu sayısıdır" — **ayrıştırma yok** | ölçülen eğrinin hâlâ düşmesi |
| 2 | tarama salınımı **kapsamadı** (üst uç 523,6 < 551,5) | `judge`'ın kapsam koruması → `belirsiz` |
| 3 | kapsadı ama çalışma aralığında **tek nokta** kaldı | `judge`'ın iç-nokta koruması → `belirsiz` |
| 4 | `rho_ilk_ortanca = 0,0` raporlandı | `_eval()` çağrılmadan `state_numpy()` okunmuş |

2 ve 3'ten sonra elle aritmetiği bıraktım: `n_sides_for_swing()` listeyi
**ölçülen salınımdan** türetiyor ve üç test onu sınıyor.

> **Ders:** iki şart aynı anda sağlanması gerekiyorsa ve **birbiriyle
> çakışıyorsa** (uçlar dışarıda, iç noktalar içeride), o aritmetik koda
> yazılır. Elle iki kez yanıldım.

---

## 6. Sırada

| # | iş | durum |
|---|---|---|
| — | **ADR-0042** — sözleşmenin düzeltilmesi | bu kayıttan doğrudan |
| 4.4 | ADR-0041 §5 boşluk 3 (mukavemetli malzemede A′) | ölçüm kuruldu, koşuyor |

---

## 7. Bu kayıtta uygulanan kurallar

| kural | nerede |
|---|---|
| kilitli karara **sessiz** değişiklik yok — ADR gerekir | §0, §4 |
| çelişki **tercih** değil **ölçümle** çözülür | §0 |
| çalışma noktası **ölçülür**, tahmin edilmez | §1 |
| kendi tasarım iddiam yanlışsa **düzeltilir**, ölçüm atılmaz | §2 |
| ölçüm bir **üst sınır**sa öyle yazılır | §2, §3 |
| çalışma noktası dışındaki noktalar yargıya **girmez** | §3 |
| çakışan iki şart varsa aritmetik **koda** yazılır | §5 |
