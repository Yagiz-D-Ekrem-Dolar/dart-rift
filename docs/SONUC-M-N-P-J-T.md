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

## 2c. Kilitli: M2 (kontrast), Z (bölge), A80, A83 — aynı gece

| protokol | yargı |
|---|---|
| **M2** (yeni θ, 3 merdiven, kesmeli) | **H_Y DAYANIKLI** · H_a DAYANIKSIZ · H_f DAYANIKSIZ |
| **Z** (ince bölge yarıçapı 2×) | **KISMİ** — kabada `β−1` `+%12–13`, ortada `−%0,3…+%3,9`; M'nin orta → ince farkını açıklamıyor |
| **A80** (dayanım kesmesi) | V1 KARARLI · V2 FİZİĞİ DEĞİŞTİRİYOR (`β−1` `+%1,7`) → üretimde |
| **A83** (yoğunluk tabanı) | V1 12/12 + 6/6 (Tkt bekleniyor) · **V2 NÖTR** (60/60) → üretimde |

M2 kontrastları:

| kontrast | kaba | orta | ince | yargı |
|---|---:|---:|---:|---|
| `β−1`: `Y₀ 1e6` − `3e4` | −0,071 | −0,105 | −0,101 | KARARLI |
| `ln M_ej`: aynı | −0,021 | −0,278 | −0,244 | KARARLI |
| `β−1`: `α_b 1,25` − `1,10` | +0,013 | −0,017 | +0,027 | KARARSIZ |
| `β−1`: `f 0,40` − `0,20` | −0,078 | +0,055 | −0,043 | KARARSIZ |

`V_krater` ve `d_merkez` OKUNMAZ: taban θ'nın ince `99991111` koşusunda
krater operatörü `nan` döndü (A84 adayı, incelenmedi → kayıt numarası **A86** oldu; A84 başka kusura verildi). Kabada `Y₀ = 1e6`
noktasında `d_merkez` negatif (`−0,09 / −0,21 m`) — A81 ile tutarlı.

**Okuma:** `Y₀`'ın izi orta ve ince çözünürlükte aynı (kaba asimptotik
bölgede değil); `α_b` ve `f`'nin izi çözünürlükle işaret değiştiriyor.
Önceden yazılmış yorum tablosu: *"`Y₀` çözünürlüğe dayanıklı biçimde
çıkarılabilir; `α_b`, `f` bu gözlemlerle çıkarılamaz."*

## 2d. KİLİTLİ: P-v4 / P-v4b — kaba üretim fiziği (kesme + taban), 48 θ

Havuz: Nk + N2k (kesmeli) + Nkd (patlayan 3 θ, kesme + taban dolgusu),
tekrar (θ, tohum) elenmiş; 96 koşu, 48 θ. θ-gruplu 4 kat dış doğrulama,
iç kovaryans 4-kat artıklarından (§4d).

**N havuzu:** **İKİ EKSEN GÖRÜNÜR** (`Y₀`, `f`); `α_b` `dV_sıkışma`'da
`p = 0,0026` — Bonferroni eşiğini (`0,00238`) yine kıl payı kaçırıyor.

| yol | `α_b` (kapsama68 / genişlik) | `log Y₀` | `f` | genel |
|---|---|---|---|---|
| P-v4 kuadratik | 0,58 / 0,48 BİLGİ YOK | 0,68 / 0,36 BİLGİ YOK | 0,71 / 0,44 BİLGİ YOK | HİÇBİR EKSEN |
| P-v4 GP | 0,60 / 0,42 BİLGİ YOK | 0,60 / 0,37 BİLGİ YOK | 0,61 / **0,31 ÇÖZÜLÜYOR** | TEK EKSEN |
| **P-v4b kuadratik** (+ 8/16 ms) | 0,52 / 0,44 BİLGİ YOK | 0,57 / **0,33 ÇÖZÜLÜYOR** | 0,79 / **0,32 ÇÖZÜLÜYOR** | **İKİ EKSEN** |
| P-v4b GP | **0,44 AŞIRI GÜVENLİ** | 0,50 / 0,27 | 0,56 / 0,15 | KALİBRASYON DÜŞTÜ |

Kilitli yol seçimi: P-v4 → GP, TEK EKSEN; P-v4b → kuadratik, İKİ EKSEN.
§4e: P-v4b kalibre ve daha çok ekseni çözüyor → yargıya girer.

> **Kaba çözünürlükte, üretim fiziğiyle, zaman örnekleriyle genişletilmiş
> gözlem vektörü: dış doğrulamada kalibre posterior `Y₀` ve `f`'yi
> ÇÖZÜYOR, `α_b`'yi çözmüyor.** `%95` kapsama `0,82 / 0,96 / 0,96`.

Sınırlar: (i) kaba çözünürlük — M2'ye göre `Y₀` kontrastı çözünürlüğe
dayanıklı, **`f` değil**; orta çözünürlükte aynı kural koşuluyor (Pv4o).
(ii) `Y₀` genişliği `0,334`, eşiğin (`0,34`) hemen altında. (iii) Sentetik
kapalı sınama: gerçek DART verisi değil.

## 2e. KİLİTLİ (2026-09-14): orta P-v4 / P-v4b, T platosu, A83 V1c

**Orta, kesme + taban, 48 θ (Nok + N2ok + Nokd dolgusu), 96 koşu:**

| yol | `α_b` | `log Y₀` | `f` | genel |
|---|---|---|---|---|
| P-v4 kuadratik | 0,61 / 0,55 BİLGİ YOK | 0,61 / 0,34 BİLGİ YOK | 0,67 / **0,34 ÇÖZÜLÜYOR** | TEK |
| **P-v4 GP** | 0,58 / 0,39 BİLGİ YOK | 0,55 / **0,18 ÇÖZÜLÜYOR** | 0,62 / **0,24 ÇÖZÜLÜYOR** | **İKİ** |
| **P-v4b kuadratik** | 0,61 / 0,54 BİLGİ YOK | 0,62 / **0,33 ÇÖZÜLÜYOR** | 0,67 / **0,31 ÇÖZÜLÜYOR** | **İKİ** |
| P-v4b GP | **0,34 AŞIRI GÜVENLİ** | 0,40 | 0,45 | KALİBRASYON DÜŞTÜ |

N havuzu (orta): İKİ EKSEN (`Y₀`, `f`). Kilitli yol seçimi: P-v4 → GP İKİ
EKSEN; P-v4b → kuadratik İKİ EKSEN. **Orta çözünürlükte de sonuç kaba
ile aynı: `Y₀` ve `f` çözülüyor, `α_b` çözülmüyor** (kapsama68 değerleri
çözülen eksenlerde `0,55–0,67`). P-v4 GP'de `Y₀` genişliği `0,18`:
önselin `%74`'ü eleniyor.

**T platosu (kesme + taban):**

| koşu | `β−1` @ 24 ms | @ 0,1 s | @ 0,2 s | `β` plato | `M_ej` plato |
|---|---:|---:|---:|---|---|
| Tot orta `20260906` | 0,651 | 0,817 | 0,820 | GEÇTİ | DÜŞTÜ |
| Tot orta `99991111` | 0,652 | 0,824 | 0,834 | GEÇTİ | DÜŞTÜ |
| Tkt kaba `99991111` | 0,753 | 0,974 | 0,923 | GEÇTİ | GEÇTİ |

24 ms değeri plato değerinin `%78–80`'i. Kaba ile orta platoları `%12`
farklı → Protokol Q (plato anında yakınsama) gönderildi.

**A83 V1 (c)** Tkt tamamlandı → A83 V1 tam: KARARLI. **İnce (Ni + N2i,
48 θ × 2) ve N3 kaba/orta: 66/66 görev, sıfır patlama.**

**GEÇERSİZ (A84):** 2026-09-14 gecesi ince-48, kaba-72, orta-72 ve kaba-48
figür raporları yalnız ilk kampanyayı okudu (`sbatch --export` virgül
bölmesi). Sonuçları kullanılmaz; düzeltilmiş işler `1561187–1561190`.

## 2e. KEŞİF: gerçek DART gözlemi, 24 ms kaba-72 havuzu (2026-09-14, yargı değil)

`scripts/dart_gozlem_posterior.py` (Protokol D kuralları, ama 24 ms plato
değil → keşif): sahne hedef kütlesi `4,164e9 kg`, `p_imp 3,56e6`.

| | değer |
|---|---|
| gözlenen `β` (depo arayüzü, sahne kütlesiyle) | **`3,12 ± 0,34`** |
| model `β` aralığı (144 koşu, önsel boyunca vekil) | **`1,25 – 1,85`** (en büyük: `α_b 1,02`, `Y₀ 2e4`, `f 0,05`) |
| `σ` (log): gözlem / vekil / toplam | `0,070 / 0,031 / 0,077` |
| önsel kapsama | **ÖNSEL DIŞI (YUKARI), +5,2σ** |
| **orta-72** (144 koşu) model `β` / kapsama | `1,27 – 1,72` (en büyük `α_b 1,17`, `Y₀ 1,7e4`, `f 0,34`) · **ÖNSEL DIŞI (YUKARI), +6,2σ** |

Plato anında `β` 24 ms'dekinin `~1,25` katı (T, Tkt) — o çarpanla bile
`~2,3`'e çıkar, band alt ucunun (`2,78`) altında. Kilitli D yargısı Q2/Q3
(0,1 s) ile gelecek; hangi model bileşeninin farkı kapattığı **Protokol U**.

> **Düzeltme (aynı gün):** yukarıdaki paragrafta iki hata var, satırlar
> silinmedi. (i) Plato çarpanı `β − 1`'e uygulanır (`0,65 → 0,82`, `×1,26`):
> en büyük model değeri `β − 1 ≈ 0,85 × 1,26 ≈ 1,07`, yani `β ≈ 2,1` —
> `~2,3` değil. (ii) Gözlem bandının `2σ` alt ucu `3,12 − 2·0,34 = 2,44`;
> yazılan `2,78` `1σ` ucudur. Sonuç (ÖNSEL DIŞI) değişmiyor.

## 3. Bitiş 3 için anlamı

1. **Mutlak** 24 ms gözlenebilirlerine dayanan bir posterior bu
   merdivenlerle çözünürlüğe bağlı (M). Gerçek veriye doğrudan
   uygulanamaz.
2. Kaba çözünürlükte küresel olarak yalnız **`Y₀`** görünüyor (N) ve
   posterior dış örneklemde **kalibre değil** (P2, A82).
3. Yerel duyarlılık (L2, L2o) üç ekseni gösteriyor ama küresel harita (N)
   göstermiyor: `α_b` ve `f`'nin izi yerel ve önsel boyunca tutarsız.
   **→ Aynı gece düzeltme (§2b, keşif):** 47 θ'lık havuzda N ÜÇ EKSEN
   GÖRÜNÜR dedi; bu madde 24 θ'nın güç yetersizliğini "tutarsızlık" diye
   okumuştu. Kilitli doğrulama kesmeli havuzda (Nk, S_Nkh).
4. En umut veren yol: **kontrast + θ'dan bağımsız çözünürlük kayması**
   modeliyle `Y₀` çıkarımı (M2 doğrularsa).
5. Sayısal kararsızlık A80 düzeltildi; doğrulama (K80, Tk) koşuyor.
