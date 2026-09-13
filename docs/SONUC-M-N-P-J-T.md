# Sonuçlar — M, N, P, J, T, L2o (2026-09-13, `egitimg16u4`, H200)

Hepsi koşudan önce commit'lenmiş protokollerle okundu. Koşudan sonra
yapılan her şey **KEŞİF** diye etiketli ve yargı değildir.

---

## 1. Kilitli yargılar

| protokol | soru | yargı |
|---|---|---|
| **J1** | sabit `h`'de `Δt` yarılanınca `x₀` kayıyor mu; `ara` kaldırıyor mu | **Y1: ZAMAN ADIMI YOLU GÖSTERİLDİ** (`son`: `Δ = −0,343`, `2,27σ`) · **Y2: ARA KALDIRIYOR** (`0,04σ`) · I'daki kaymanın `%25`'i `Δt`'den |
| **J2** | aynı, ikinci seri | **OKUNMAZ** (sigmoid geçersiz, `R²` / `x₀` aralığı) |
| **I2** | `ara` kipinde `x₀` çözünürlüğe dayanıklı mı | **DAYANIKLI** (`kat 0,44`; yakınsama kanıtı değil) |
| **O4** | G1 bit-tekrarı | **OKUNMAZ** (G1 verisi u1'de) |
| **T** blok | `β` zamanda plato | **GEÇTİ** (iki tohum; `β−1 = 0,0532`, 12 ms → 0,2 s sabit) · `M_ej` bir tohumda düştü |
| **T** matris | aynı | **KOŞULAMADI** — iki tohum da patladı (A80) |
| **M** | üç çözünürlükte yakınsama (6 θ × 2 tohum) | **YAKINSAMIYOR** — 5/5 gözlenebilir (`YAKINSAMIŞ` toplam 1/30) |
| **L2o** | L2 matris kolu orta çözünürlükte | **ÜÇ EKSEN AYRIŞIYOR — `boulder_alpha0` OKUNMAZ** (`s = 31,6 · 7,0 · 4,0`; tekrar `0,94 / 0,10 / 0,30`; `R_krater` düştü, `σ = 0`) |
| **N** | küresel ayırt edilebilirlik (kaba, 23 θ) | **TEK EKSEN (`log10 Y₀`)** — Bonferroni `p < 0,00238` |
| **P** kuadratik | kapalı döngü | **TEK EKSEN ÇÖZÜLÜYOR** (`Y₀` kapsama68 `0,57`, genişlik `0,31`) |
| **P** GP | kapalı döngü | **ÜÇ EKSEN ÇÖZÜLÜYOR** (kapsama68 `0,54/0,52/0,59`; kapsama95 `0,74/0,74/0,83`) |
| **P2** kuadratik | dış örneklem (N2) | **KALİBRASYON DÜŞTÜ** (`Y₀` `0,48`) |
| **P2** GP | dış örneklem | **KALİBRASYON DÜŞTÜ** (`Y₀` `0,26`, `f` `0,46`, `α_b` `0,43`) |
| **P yol seçimi (§4c)** | | **KALİBRASYON DÜŞTÜ** (iki yol elendi) → A82 |

### 1.1 M ayrıntısı — farklar inceldikçe büyüyor

| gözlenebilir (t0) | kaba | orta | ince |
|---|---:|---:|---:|
| `β − 1` | 0,743 | 0,642 | 0,459 |
| `V_krater` [m³] | 23,9 | 35,7 | 52,6 |
| `d_merkez` [m] | 2,63 | 2,99 | 3,94 |
| `M_ejekta` [kg] | 40 110 | 38 290 | 34 010 |

Richardson durumu çoğunlukla "ASİMPTOTİK DEĞİL": `|orta − ince| >
|kaba − orta|`. Bu merdivenlerle 24 ms'deki **mutlak** gözlenebilirler
çözünürlükten bağımsız değil.

### 1.2 N ayrıntısı

| gözlenebilir | `F` | en güçlü eksen (`ρ`, `p`) | yargı |
|---|---:|---|---|
| `β − 1` | 821 | `Y₀` (−0,69, 0,0004) | AYIRT EDİYOR |
| `R_krater` | 9,4 | `Y₀` (−0,79, <1e-4) | AYIRT EDİYOR |
| `μ_ejekta` | 22 | `Y₀` (−0,82, <1e-4) | AYIRT EDİYOR |
| `dV_sıkışma` | 10,5 | `Y₀` (−0,75, 1e-4); `α_b` (−0,62, **0,0024**) | AYIRT EDİYOR |
| `M_ejekta` | 68 | `f` (−0,62, **0,0025**) | AYIRT EDİYOR |
| `V_krater` | 62 | `Y₀` (−0,62, 0,0019) | AYIRT EDİYOR |
| `d_merkez` | 24 | `Y₀` (−0,48, 0,021) | AYIRT ETMİYOR |

`α_b` ve `f` Bonferroni eşiğini (`0,00238`) kıl payı kaçırıyor.

---

## 2. KEŞİF (koşudan sonra, yargı değil): kontrastlar mutlak değerlerden kararlı

M verisinde `y(θ_k) − y(θ_0)`:

| kontrast | kaba | orta | ince |
|---|---:|---:|---:|
| `β−1`: `Y₀ 3e6` − `Y₀ 1e5` | −0,242 | −0,237 | −0,215 |
| `V_krater` oranı, aynı | 0,58 | 0,48 | 0,60 |
| `M_ej` oranı, aynı | 0,95 | 0,56 | 0,60 |
| `β−1`: `α_b 1,05, f 0,10` − t0 | +0,032 | −0,034 | +0,043 |
| `β−1`: `α_b 1,25, f 0,45` − t0 | −0,036 | +0,009 | −0,020 |

Mutlak `β−1` kaba → ince `%62` kayarken `Y₀` kontrastı `%11` değişiyor.
`α_b` / `f` kontrastları küçük ve işaret değiştiriyor. N ve P'nin kaba
sonucuyla (yalnız `Y₀`) tutarlı. **Yeni θ'larla sınanıyor: Protokol M2**
([PROTOKOL-M2-KONTRAST](truba/PROTOKOL-M2-KONTRAST.md), iş `1559586`).

---

## 2b. KEŞİF: A82 tanısı, havuzlanmış N ve P-v4 (kesmesiz veri, yargı değil)

**Dış örneklem neden düştü** (`scripts/p_tani_raporu.py`, yalnız N → N2):

| ölçü | değer | kalibre bir modelde |
|---|---|---|
| sınama `z` sapması (6 gözlenebilir) | `1,04–1,55` | `≈ 1` (eğitim LOO'da `1,00`) |
| `z` ortalaması | `−0,41 … +0,31` | `≈ 0` |
| `χ²` ortalama / medyan | `10,2` / `4,9` | `6` / `5,3` |
| en kötü noktalar | `α_b ≈ 1,0`, `Y₀ ≈ 9e6` köşesi | — |

Korelasyon küçültmesi etkisiz (`λ = 0 / 0,3 / 1` → kapsama `0,43 / 0,46 /
0,41`); kovaryans `×2` → kapsama `0,63` ama genişlik `0,39`. 4-kat
artıklar tek başına (P-v3) yetmedi (`0,46` kuadratik, `0,33` GP).

**Havuz (N + N2 = 47 θ):**

- N raporu: **ÜÇ EKSEN GÖRÜNÜR** — `α_b` `dV_sıkışma`'da `ρ = −0,50`,
  `p = 0,0004`; `f` `M_ejekta`'da `ρ = −0,63`, `p < 1e-4`. 24 θ'lık tarama
  yetersiz güçteymiş.
- P-v4 (4-kat dış doğrulama, kuadratik): **kalibre** (kapsama68
  `0,63 / 0,63 / 0,71`, kapsama95 `0,86 / 0,96 / 0,91`), ama medyan
  genişlik `0,47 / 0,38 / 0,47 ≥ 0,34` → HİÇBİR EKSEN ÇÖZÜLMÜYOR.
  Posterior önseli `Y₀`'da `~%45`, `α_b` ve `f`'de `~%30` daraltıyor.

Bu keşif üzerine, kesmeli üretim verisi (Nk) **gelmeden** P-v4 (§4d) ve
zaman örnekli P-v4b (§4e) kilitlendi.

## 3. Bitiş 3 için anlamı

1. **Mutlak** 24 ms gözlenebilirlerine dayanan bir posterior bu
   merdivenlerle çözünürlüğe bağlı (M). Gerçek veriye doğrudan
   uygulanamaz.
2. Kaba çözünürlükte küresel olarak yalnız **`Y₀`** görünüyor (N) ve
   posterior dış örneklemde **kalibre değil** (P2, A82).
3. Yerel duyarlılık (L2, L2o) üç ekseni gösteriyor ama küresel harita (N)
   göstermiyor: `α_b` ve `f`'nin izi yerel ve önsel boyunca tutarsız.
4. En umut veren yol: **kontrast + θ'dan bağımsız çözünürlük kayması**
   modeliyle `Y₀` çıkarımı (M2 doğrularsa).
5. Sayısal kararsızlık A80 düzeltildi; doğrulama (K80, Tk) koşuyor.
