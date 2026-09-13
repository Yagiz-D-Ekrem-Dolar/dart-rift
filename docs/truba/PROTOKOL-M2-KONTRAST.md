# Protokol M2 — θ-kontrastlarının çözünürlük kararlılığı

**Yazıldı:** 2026-09-13, **koşudan ÖNCE**. Kural
`scripts/m2_kontrast_raporu.py`'de kilitli; sınavı
`tests/test_m2_kontrast_raporu.py`.

## 1. Neden

Protokol M'nin kilitli yargısı: beş gözlenebilirin **mutlak** değeri kaba
/ orta / ince merdivende **YAKINSAMIYOR**; fark inceldikçe büyüyor
(`β−1`: `0,74 → 0,64 → 0,46`; `V_krater`: `24 → 36 → 53 m³`).
Mutlak değerlere dayanan bir posterior çözünürlüğe bağlı olur.

Koşudan SONRA, aynı veride yapılan keşif: **iki θ arasındaki fark çok
daha kararlı**. `β−1(Y₀ = 3e6) − β−1(Y₀ = 1e5)` = `−0,242 / −0,237 /
−0,215`; `V_krater` oranı `0,58 / 0,48 / 0,60`. `α_b` ve `f` kontrastları
küçük ve işaret değiştiriyor. Bu **hipotez**; M2 onu yeni θ'larla sınar.

Doğrulanırsa çıkarım "mutlak değer + θ'dan bağımsız çözünürlük kayması"
modeliyle kurulabilir: kayma bir **rahatsız edici parametre** olur ve
yalnız kontrastın taşıdığı bilgi kullanılır.

## 2. Tasarım

| nokta | `α_b` | `Y₀` [Pa] | `f` |
|---|---:|---:|---:|
| `θ_b` (taban) | 1,10 | 3e4 | 0,20 |
| `θ_Y` | 1,10 | **1e6** | 0,20 |
| `θ_a` | **1,25** | 3e4 | 0,20 |
| `θ_f` | 1,10 | 3e4 | **0,40** |

İki sahne tohumu (`20260906`, `99991111`), üç merdiven (kaba/orta/ince),
matris sahası, `t = 24 ms`, en iyi fizik + `--dayanim-kesme` (A80).
24 koşu (`truba/is_M2_kontrast.slurm`).

## 3. Kontrast ve yargı

- `β−1`, `d_merkez`: fark; `V_krater`, `M_ejekta`: log oran. İki tohum
  ortalaması; `σ_c² = σ̄_j² + σ̄_b²`.
- **SİNYAL YOK:** `|c_ince| ≤ 2 σ_c`.
- **KARARLI:** sinyal var, üç seviyede işaret aynı ve
  `|c_ince − c_orta| ≤ max(0,25 |c_ince|, 2 σ_c)`.
- **KARARSIZ:** diğer.

**Hipotez `H_Y`:** `Y₀` kontrastı `{β−1, ln V, ln M_ej}` üçlüsünün
en az ikisinde KARARLI → **DAYANIKLI**; biri → KISMİ; hiçbiri →
DAYANIKSIZ. `H_a`, `H_f` aynı kuralla.

## 4. Yorum tablosu (koşudan önce)

| `H_Y` | `H_a`, `H_f` | anlamı |
|---|---|---|
| DAYANIKLI | DAYANIKSIZ / SİNYAL YOK | `Y₀` çözünürlüğe dayanıklı biçimde çıkarılabilir; `α_b`, `f` bu gözlemlerle çıkarılamaz — N ve P'nin kaba sonucuyla tutarlı. Çıkarım kontrast + kayma modeliyle |
| DAYANIKLI | DAYANIKLI | üç eksen kontrastla çıkarılabilir; N'deki zayıflık kaba çözünürlüğün |
| KISMİ / DAYANIKSIZ | — | kontrast da çözünürlüğe bağlı; 24 ms gözlemlerinden çözünürlükten bağımsız bir `θ` çıkarımı bu merdivenlerle **kurulamaz** |

## 5. Bilinen sınırlar

- Üç seviye, iki tohum; `σ_c` iki örnekten.
- Tek taban nokta; kontrast doğrusallığı varsayılıyor.
- `R_krater` nicemli (`0,2 m` adım), dışarıda.
