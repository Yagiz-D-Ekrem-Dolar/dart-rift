# ADR-0042 — `h` sabittir, dolayısıyla `Ω ≡ 1`

- **Durum:** KABUL EDİLDİ (kilitli)
- **Tarih:** 2026-08-08
- **Değiştirdiği:** [ADR-0041](ADR-0041-yerel-incelme-yaklasimi.md) §5b madde 2
- **Kanıt:** [KAYIT-035](../defter/KAYIT-035_2026-08-08_omega-celiskisi-olculerek-cozuldu.md)
- **İlgili:** [ADR-0004](ADR-0004-determinizm.md) (determinizm kilidi)

---

## 1. Bağlam

ADR-0041 A′'yı seçerken dört maddelik bir sözleşme kilitledi. İkisi
**birbirini kesiyor**:

| madde | metin |
|---|---|
| 2 | `Ω` (grad-h) düzeltmesi **uygulanır** — enerji tutarlılığı için |
| 4 | skaler `h` yolu **bit düzeyinde korunur** — determinizm kilitli |

Çelişki A′ GPU'da doğrulandıktan sonra (KAYIT-034) madde 2'yi uygulamaya
geçerken ortaya çıktı.

---

## 2. Karar

> **`h` parçacık başına taşınır ama zaman içinde SABİTTİR** — kurulumda
> atanır, evrilmez. Dolayısıyla `∂h/∂ρ = 0` ve **`Ω ≡ 1`, tam olarak**.
> Ayrı bir `Ω` kod yolu **yoktur ve olmayacaktır**.

ADR-0041 §5b madde 2 şu metinle **değiştirilir**:

> ~~2. `Ω` (grad-h) düzeltmesi **uygulanır** — enerji tutarlılığı için.~~
>
> **2. `h` zaman içinde sabittir; `Ω ≡ 1`'dir ve ayrıca hesaplanmaz.**
> `h` ileride evrilmeye başlarsa `Ω` **zorunlu** hâle gelir ve bu ADR ile
> madde 4 birlikte yeniden değerlendirilir.

Diğer üç madde **değişmiyor**.

---

## 3. Gerekçe

### 3.1 Cebir: `Ω` sabit `h`'de birimdir

```
Ω_i = 1 − (∂h_i/∂ρ_i) · Σ_j m_j ∂W_ij/∂h_i
```

`∂h_i/∂ρ_i` çarpanı **yalnızca** uyarlamalı bağıntıdan (`h ∝ ρ^{-1/3}`)
gelir. `h` reçeteliyse bu türev **sıfırdır** ve terim kapanır. Bu bir
yaklaşıklık değil; toplamın **önündeki çarpan** sıfırdır.

### 3.2 `Ω`'yı yine de uygulamak madde 4'ü kırardı

Sabit `h`'de `Σ_j m_j ∂W_ij/∂h_i ≠ 0`'dır. Zincir kuralı çarpanı
atılıp yalnızca toplam kullanılsaydı skaler `h` yolunda bile `Ω ≠ 1`
çıkar, basınç terimi değişir ve ADR-0004'ün determinizm kilidi kırılırdı.
İki madde **aynı anda** sağlanamaz; biri gitmek zorundaydı.

### 3.3 Ölçüm: sabit `h` yeterli (KAYIT-035)

Madde 2'yi düşürmek ancak sabit `h`'nin **yeterli** olduğu gösterilirse
meşrudur. Ölçüldü:

| büyüklük | değer |
|---|---|
| gerçek koşuda `N_komşu` salınımı | **268,2 → 551,5** (`2,06×`) |
| çalışma aralığında ölçülen yarıçap yayılımı | **%0,607** |
| tolerans | %2 |

`N_komşu` iki kat değişirken sonuç `%0,607` oynuyor — ve bu bir **üst
sınırdır** (`dx` yakınsaması da içinde).

---

## 4. Sonuçlar

### Olumlu

- **Kod yalınlaşıyor**: `Ω` için ek geçiş, ek dizi, ek çekirdek **yok**.
  KAYIT-031'in "92 site + `Ω`" bedeli `Ω` kadar **küçüldü**.
- **Determinizm kilidi sağlam** (ADR-0004): skaler yol bit düzeyinde
  korunuyor, KAYIT-034'te GPU'da ölçüldü.
- **Momentum tam** kalıyor: `f_ij = −f_ji` simetrik `h_ij`'den geliyor,
  `Ω` ile ilgisi yok (`8,608e-17`, KAYIT-034).

### Olumsuz / kabul edilen bedel

- **Komşu sayısı sabit değil.** `ρ` salınırken `N_komşu` onunla salınır.
  Ölçülen aralıkta bedeli `≤ %0,607`; **daha şiddetli** bir sıkışmada
  bu ölçülmemiştir.
- **Uyarlamalı `h`'nin bilinen yararlarından vazgeçiliyor**: genleşen
  malzemede çözünürlüğü koruma, çok geniş yoğunluk aralıklarında tekdüze
  doğruluk.

### Bu kararın **geçersiz** olacağı koşul

> DART kurulumunda ölçülen `N_komşu` salınımı `2,06×`'ı **belirgin biçimde**
> aşarsa, veya çalışma aralığındaki yayılım `%2`'yi geçerse, bu ADR
> yeniden açılır. Ölçüm FAZ 4.4'te DART geometrisinde **tekrarlanacaktır**.

---

## 5. Değerlendirilen alternatifler

| seçenek | neden seçilmedi |
|---|---|
| **Uyarlamalı `h` + `Ω`** | Sabit `h`'nin yetersiz olduğu **gösterilmedi**; ölçüm tersini söylüyor. Madde 4'ü (determinizm) kırardı ve yeni bir kod yolu getirirdi. Bedeli var, karşılığı ölçülmedi. |
| **`Ω`'yı sabit `h`'de de hesapla** | Cebirsel olarak **yanlış** — zincir kuralı çarpanı sıfır. Ayrıca madde 4'ü kırar. |
| **Madde 2'yi sessizce uygulama** | RULES.txt: kilitli karara sessiz değişiklik yok. |

---

## 6. Açık kalan

- **ADR-0041 §5 boşluk 3** — mukavemet/gözeneklilik/hasar etkileşimi.
  FAZ 4.4'te ölçülüyor; bu ADR'yi de sınayacak çünkü `N_komşu` salınımı
  orada farklı olabilir.
- Salınım ölçümü **Sedov geometrisinde** yapıldı. DART geometrisinde
  (moloz yığını, gerçek mermi) tekrarlanmadan bu karar **koşulludur**.
