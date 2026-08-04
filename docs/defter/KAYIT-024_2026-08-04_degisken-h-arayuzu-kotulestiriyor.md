# KAYIT-024 — Parçacık başına `h` arayüzü **kötüleştiriyor** (2026-08-04)

**Kapsam:** FAZ 4.2 karar verisi · **Durum:** ölçüldü
**Öncül:** [KAYIT-023](KAYIT-023_2026-08-04_cozunurlugu-h-belirliyor.md)

---

## 0. Soru

KAYIT-023 **A**'yı eledi: çözülen ölçeği `h` belirliyor, dolayısıyla tek
global `h` ile kütle oranı değiştirmek çözünürlüğü artırmıyor. Geriye kalan
"mermiyi çöz" seçenekleri **A′** (parçacık başına `h`) ve **C** (iki alan
eşlemesi).

A′ **mimari** bir bedel ister: çekirdek, hash-grid, CFL ve `Ω` düzeltmesi.
Bedelin karşılığı ne? En azından şu umulurdu:

> *Parçacık başına `h`, arayüzü de **iyileştirir** — çünkü her bölge kendi
> doğal çözünürlüğünde çalışır.*

**Ölçüldü. Tam tersi.**

---

## 1. Düzenek

Aynı iki bölgeli geometri, aynı sınav (düzgün basınçta `a = 0`), **dört
şema**:

| şema | tanım | kaynak |
|---|---|---|
| `global_h` | `h = max(h)` — A'nın bugünkü hâli | KAYIT-023 |
| `average_h` | `h_ij = ½(h_i + h_j)` | standart uyarlamalı SPH |
| `symmetric_kernel` | `W_ij = ½(W(r,h_i) + W(r,h_j))` | Hernquist & Katz 1989 |
| `gradh` | `Ω` düzeltmeli tam biçim | Price & Monaghan 2004 |

`Ω` biçimi, `h_i = η(m_i/ρ_i)^{1/3}` ⇒ `∂h_i/∂ρ_i = −h_i/3ρ_i` ile:

```
Ω_i = 1 + (h_i/3ρ_i) Σ_j m_j ∂W_ij(h_i)/∂h_i
a_i = −Σ_j m_j [ P_i/(Ω_i ρ_i²) ∇_i W_ij(h_i) + P_j/(Ω_j ρ_j²) ∇_i W_ij(h_j) ]
```

Dördü de momentumu **tam** koruyor (ölçülen artık `< 1e-12`); yani hiçbiri
"daha az hata"yı momentum kaybederek satın almıyor.

### Prototip bağımsız olarak doğrulandı

`global_h` şeması 8:1'de `0,2150` verdi; **tam çözücüyle** ölçülen
`mass_ratio` sonucu `0,2108` (KAYIT-020). **%2 fark** — iki bağımsız yol
aynı sayıyı veriyor.

---

## 2. Kendi prototipimde hata buldum — sonucu raporlamadan

grad-h, `λ = 1`'de (tüm `h`'ler eşit, doğru cevap **tam sıfır**) `7,69e-06`
verdi; diğer üç şema `1,86e-15`.

`Ω`'yı doğrudan ölçtüm: **iç bölgede tam düzgün** (yayılım `6,7e-16`). Yani
`Ω` hesabında sorun yoktu.

**Kök neden:** grad-h kuvveti **komşunun** `Ω_j`'sini kullanır; `Ω_j` ise o
komşunun **kendi** komşuluğundan gelir. Dolayısıyla serbest yüzeyin kestiği
bilgi **bir çekirdek daha** içeri sızar.

> Diğer şemalarda kenar payı `2h` yeter (KAYIT-019 §3b). **grad-h'de `4h`
> gerekir.**

Düzeltildi: paylar şema başına ayrıldı (`gradh_margin_factor`), geometri
denetimi en büyük paya göre yapılıyor, ölçüm bölgesi şema başına raporlanıyor.
Ayrıca `N×N×3` dizi hiç oluşturulmuyor (bloklu hesap).

Düzeltmeden **sonra** dört şema da `λ=1`'de makine sıfırı veriyor.

---

## 3. Ölçüm (TRUBA, iş 1450836; `r_out=88`, `r_in=24`, `s=8`, `h/s=1,3`)

### `a/ölçek` (maksimum, kaba `h` ile normalize)

| oran | N | `global_h` | `average_h` | `symmetric_kernel` | `gradh` |
|---|---|---|---|---|---|
| 1,00 | 7893 | 0,0000 | 0,0000 | 0,0000 | 0,0000 |
| 2,00 | 8073 | **0,2001** | 0,3579 | 0,3354 | 0,3248 |
| 2,99 | — | — | — | — | — |
| 4,02 | 8379 | **0,1937** | 0,6876 | 0,8580 | 0,9201 |
| 8,00 | 9005 | **0,1684** | 1,0998 | 1,6806 | 1,5978 |

### Ham `a_rms` — normalizasyondan bağımsız

Normalizasyon `P/(ρ·max h)` kaba `h`'yi kullanıyor; değişken-`h` şemalarında
ince bölgenin yerel ölçeği farklı olduğu için **ham** değerler de verilmeli:

| oran | `global_h` | `average_h` | `symmetric_kernel` | `gradh` |
|---|---|---|---|---|
| 1,00 | 6,77e-12 | 6,77e-12 | 6,77e-12 | 6,04e-12 |
| 2,00 | **1,31e+03** | 2,19e+03 | 2,17e+03 | 2,08e+03 |
| 4,02 | **1,37e+03** | 4,09e+03 | 4,27e+03 | 4,20e+03 |
| 8,00 | **1,06e+03** | 6,16e+03 | 7,74e+03 | 7,26e+03 |

**Ham ivme de aynı şeyi söylüyor:** 8:1'de değişken `h`, sabit `h`'nin
**5,8–7,3 katı**. Sonuç normalizasyon seçimine bağlı değil.

---

## 4. Kademeli geçiş yardım ediyor — ama yetmiyor

`h` sıçraması `r_inner` çevresinde `smoothstep` bir bantla yayıldı (gerçek
uyarlamalı SPH'de `h` zaten süreklidir; ani sıçrama **en kötü** durumdur):

| bant | bant / `h_kaba` | `global_h` | `average_h` | `symmetric` | `gradh` |
|---|---|---|---|---|---|
| 0,0 | 0 | 0,1684 | 1,0998 | 1,6806 | 1,5978 |
| 10,4 | 1 | 0,1684 | 0,9527 | 0,9521 | 1,0099 |
| 20,8 | 2 | 0,1684 | 0,6669 | 0,6606 | 0,6496 |
| 41,6 | 4 | 0,1684 | 0,5771 | 0,5668 | 0,5596 |
| 62,4 | 6 | 0,1684 | **0,5507** | 0,5455 | **0,5428** |

**Doyuyor.** 4·`h` genişliğinden sonra kazanç bitiyor ve `~0,545`'te
duruyor — hâlâ `global_h`'nin **3,2 katı**.

### `Ω` düzeltmesi kurtarmıyor

grad-h, ani sıçramada `average_h`'den **daha kötü** (1,598 vs 1,100); geniş
bantta ise pratikte aynı (0,543 vs 0,551). Beklenen bir sonuç:
`Ω` düzeltmesi **düzgün değişen** `h` için türetilmiştir ve enerji
tutarlılığını sağlar; **süreksiz** bir `h` sıçramasında sıfırıncı mertebe
tutarlılığı geri getirmez.

---

## 5. Yargı

> **Parçacık başına `h`, arayüz hatasını düşürmüyor — 3,2 ila 6,5 kat
> artırıyor. Üç ayrı simetrileştirme biçimi de aynı sonucu veriyor.**

Sebebi anlaşılır: `h`'yi değiştirmek, kütle süreksizliğinin **üstüne ikinci
bir süreksizlik** koyar. Kademeli geçiş ikincisini yumuşatır ama
birincisini değil.

### A′'nın gerçek maliyeti

A′ **çözünürlüğü** satın alır (KAYIT-023: küçük `h` ince bölgeyi gerçekten
çözer) ama bedeli **iki kalemdir**:

1. **mimari** — çekirdek, hash-grid, CFL, `Ω`
2. **arayüz** — 3,2–6,5 kat daha gürültülü

İkincisi bu ölçüme kadar bilinmiyordu.

---

## 6. Karar tablosu — güncel

| # | yaklaşım | mermiyi çözer mi? | arayüz hatası | mimari bedel |
|---|---|---|---|---|
| ~~A~~ | global `h`, değişken kütle | **HAYIR** (KAYIT-023) | 0,168 *(en iyi)* | yok |
| **A′** | parçacık başına `h` | evet | **0,55–1,10** | çekirdek+grid+CFL+Ω |
| **B** | parçacık bölme | yalnızca A′ ile | = A′ | = A′ |
| **C** | iki alan eşlemesi | evet | **ölçülmedi** | iki çözücü + eşleme |
| **D** | kaynak terimi | çözmez, **atlar** | yok | ılımlı |

### C hakkında dürüst olmak gerekir

C'nin arayüzü de **iki farklı `h`'nin buluştuğu yerdir**. Eşleme, sınır
boyunca doğrudan SPH toplamıyla yapılırsa **C yerel olarak A′'ya eşittir** ve
aynı 3,2–6,5 kat cezayı öder. Örtüşme bölgesi + ara değerleme (AMR hayalet
hücresi gibi) yapılırsa farklı olabilir — **ama bu ölçülmedi.**

C'yi A′'dan ayıran şeyin ne olduğunu **ölçmeden** C'yi seçmek, bu projenin
kurallarına aykırı olur.

---

## 7. Hâlâ eksik — ve karar neden verilmedi

| # | eksik | neden gerekli |
|---|---|---|
| **E3** | arayüzden **şok** geçişi | tüm ölçümler yumuşak alanda; çarpmanın asıl sorusu bu |
| **C-1** | C'nin eşleme biçimi ve arayüz hatası | C'yi A′'dan ayıran şey ölçülmedi |
| **D-1** | D'nin model-form hatası | çözülmüş referans 1,72e9 parçacık ister; **dolaylı** kıyas tasarlanmalı |

Bu üçü olmadan ADR-0041 yazılmaz. Ama karar uzayı artık **ölçümle**
daralmış durumda ve kalan sorular **belirli**.

---

## 8. Bu kayıtta uygulanan kurallar

| kural | nerede |
|---|---|
| prototip de **sınanır**; boşluk kontrolü ondan da istenir | §2 — grad-h `λ=1`'de düştü |
| ölçüm aracının payı **fiziğe** göre türetilir | §2 — grad-h `4h`, diğerleri `2h` |
| iki bağımsız yol aynı sayıyı vermeli | §1 — 0,2150 vs 0,2108 |
| normalizasyon tartışılırsa **ham** değer de verilir | §3 |
| "daha az hata" momentum kaybederek alınmamalı | §1 — dördü de `< 1e-12` |
| ölçülmemiş bir seçenek **iyi** varsayılmaz | §6 — C hakkında |
