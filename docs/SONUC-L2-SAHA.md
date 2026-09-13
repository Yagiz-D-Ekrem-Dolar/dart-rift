# Protokol L2 sonucu — çarpma sahası koşullanmış duyarlılık

**Tarih:** 2026-09-13 · **İşler:** L2 `1559142` (12 görev, 36 nokta), rapor
kilitli betiklerle, iş `1559330`'un ayırmasında `srun --overlap` adımı
olarak koşuldu (rapor işi `1559143` GPU sırasında bekliyordu; betik ve
girdiler aynı). Hepsi `egitimg16u4`, NVIDIA H200, kod `799ce8f`+.
**Ölçüt:** [`PROTOKOL-L2-SAHA.md`](truba/PROTOKOL-L2-SAHA.md), koşudan
önce commit'lendi.

---

## 1. Kilitli yargılar

### Yargı 1 — duyarlılık (Protokol L eşikleri)

| kol | geçerli | `q/Y` en büyük | tekil değerler | türev tekrarı (`α_b`, `log Y₀`, `f`) | kilitli yargı |
|---|---|---|---|---|---|
| **L2_matris** | **18/18** | `1 + 7e-16` | **15,76 · 4,71 · 3,60** | 0,094 · 0,200 · 0,306 | **ÜÇ EKSEN AYRIŞIYOR** |
| **L2_blok** | 18/18 | `1 + 7e-16` | 70,42 · 13,14 · 3,84 | 0,450 · **1,743** · **0,679** | ÜÇ EKSEN AYRIŞIYOR — **`log10_Y0`, `f_boulder` OKUNMAZ** |

Enerji sapması: matris `−%0,35`, blok `−%0,44…−%0,49` (A77 öncesi `~%2`).

> **A79.** Belge *"türev gürültüdeyse tekil değer yargısı o eksen için
> OKUNMAZ"* diyor; rapor betiğinin `karar` alanı bunu uygulamıyordu ve
> blok kolu için yalın "ÜÇ EKSEN" yazdı. Belgedeki kural esastır; betiğe
> `karar_okunur` alanı eklendi (eski alan yerinde). Matris kolunda üç
> eksenin tekrarı da `< 0,5` — yargı olduğu gibi okunur.

### Yargı 2 — rejim tekrar sınavı

| | merkez `β − 1` (6 gerçekleme) | medyan |
|---|---|---:|
| L2_matris | 0,7394 · 0,7452 · 0,7387 · 0,7407 · 0,7379 · 0,7403 | **0,740** |
| L2_blok | 0,0533 × 6 | **0,053** |

`oran = 13,9 ≥ 5` → **REPLİKE**. Protokol L'de koşudan sonra görülen
"çarpma noktası altındaki blok `β`'yı belirliyor" bulgusu, önceden
kilitlenmiş bir sınavda tekrarlandı.

## 2. Yorum tablosu (§5) — hangi satır

`L2_matris ≥ İKİ YÖN` → *"saha koşullanınca parametreler gürültünün
üstüne çıkıyor → orta çözünürlükte tekrar; gözlem modeline sahanın gerçek
(DRACO) geometrisi girer."* Tablo satırı önceden yazılmıştı; sonuç tabloda.

## 3. Koşudan SONRA yapılan sağlamlık okumaları (betimleyici, yargıyı değiştirmez)

### 3.1 Kopya gözlenebilirler tekil değerleri şişiriyor mu?

Gözlem vektöründe iki tam kopya var: `d_max = d_merkez` (bu sahnede),
`P_ejekta = −β` (beyaz sütunlar birebir ters işaretli). Aynı bilgiyi iki
kez saymak tekil değerleri büyütür. Matris kolunun beyaz `J`'si üzerinde:

| gözlem kümesi | `s₁` | `s₂` | `s₃` | zayıf yön (`α_b`, `log Y₀`, `f`) |
|---|---:|---:|---:|---|
| kilitli (10) | 15,76 | 4,71 | 3,60 | 0,17 · 0,86 · −0,49 |
| kopyalar çıkarıldı (8) | 12,48 | 4,12 | **3,31** | −0,18 · −0,90 · 0,40 |
| N/P kümesi (7) | 12,47 | 4,09 | **3,30** | −0,20 · −0,90 · 0,38 |
| kopyasız, **`β` yok** | 8,34 | 4,12 | **1,76** | 0,05 · −0,97 · 0,26 |

- Kopyalar çıkınca `s₃` `3,60 → 3,31`: yargı değişmiyor (`≥ 2`).
- **En zayıf yön `Y₀`** ve onu gürültünün üstüne taşıyan `β`: `β`
  çıkarılınca `s₃ = 1,76` (ZAYIF). Matris sahasında `β − 1 ≈ 0,74`; Protokol
  L'nin karışık sahasında bu sinyal blok anahtarının gürültüsüne gömülüydü.

### 3.2 Blok kolunda gerçekleme gürültüsü neredeyse sıfır

Blok kolunda `σ(β) = 6,6e-6`, `σ(R_krater) = 2,4e-16`, `σ(d) = 2,4e-3 m`:
`4 m`'lik blok 24 ms içinde iç yapıyı çarpmadan **yalıtıyor**. Beyazlatma
bu küçük `σ`'lara bölündüğü için tekil değerler çok büyük (`s₁ = 70`) ve
türev tekrarı kararsız (`1,74`). Blok kolunun "üç eksen"i bu yüzden
güvenilir değil; A79 kuralı da iki eksenini okumaz sayıyor.

### 3.3 Açık bir tuhaflık

`dV_sikisma` için matris kolunda `σ = 1` **tam** çıktı. Nicemlenmiş bir
büyüklük olabilir (yüzey operatörünün hacim ızgarası); incelenmedi.
N/P kümesinde bu gözlenebilir var; N raporu onu ayrıca yargılayacak.

## 4. Bilinen sınırlar

- Kaba merdiven, `t = 24 ms`; M (yakınsama) ve T (zamanda plato)
  sonuçları gelmeden bu duyarlılık **üretim çözünürlüğünde** kanıtlı değil.
- Yerel türev (tek merkez `θ_c`); küresel harita Protokol N'de.
- İdealleştirilmiş matris sahası (`3 m` bloksuz küre).
- Köşegen gürültü (6 gerçekleme tam kovaryans vermiyor); P tam kovaryansı
  kullanıyor.

## 5. Bitiş 3 için anlamı

Protokol L'de kilitli yargı HİÇBİR YÖN idi. Aynı fizik, aynı gözlemler,
aynı eşikler — tek fark çarpma sahasının koşullanması — ve yargı
**ÜÇ EKSEN**. Üç parametre bu çözünürlükte ve bu anda, koşullanmış sahada,
gerçekleme gürültüsünün `3,3–15,8σ` üstünde birbirinden ayrı iz bırakıyor.
Bu, üç parametreli bir posteriorun **ilk kez mümkün göründüğü** ölçüm.
Posteriorun kendisi değil: küresel ayırt edilebilirlik (N), kalibrasyon
(P, dış örneklem N2) ve çözünürlük/zaman (M, T, No_orta) sırada.
