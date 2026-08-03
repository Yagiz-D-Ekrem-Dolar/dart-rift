# KAYIT-021 — Sessiz NaN: hatalı bir ölçümün açığa çıkardığı gerçek kusur (2026-08-04)

**Kapsam:** FAZ 4.1-E2 · **Durum:** K21 kapatıldı, S4/S5 kaydedildi
**Öncül:** [KAYIT-020](KAYIT-020_2026-08-04_arayuz-hatasi-nicel.md) §6-E2

---

## 0. Bu kaydın konusu iki şey

Bir **kusur** (K21) ve **onu bulan hatalı ölçüm** (S4). İkisi ayrılamaz,
çünkü kusur ancak ben yanlış bir `dt` seçtiğim için ortaya çıktı.

Bu, kaydın en önemli cümlesidir:

> **Hatalı ölçümüm gerçek bir kusuru açığa çıkardı. Bu, ölçümü savunmaz —
> ama kusurun ne kadar iyi saklandığını gösterir.**

---

## 1. Ne aranıyordu

KAYIT-020 §6 üç eksik bırakmıştı. E2 şuydu:

> **`t = 0` anlık bir ölçümdür.** Sabit bir yapay ivme hızı **doğrusal**,
> konumu **karesel** büyütür. Hata birikiyor mu?

Düzenek: düzgün basınçlı bir küre, serbest yüzeyinden içeri bir **seyrelme
dalgası** gönderir. Dalga varana kadar iç bölge **tam durgun** kalmalıdır.
O pencerede görülen her hareket **yapaydır**.

---

## 2. S4 — kodun kendi hesabı varken elle vekil yazdım

`dt`'yi kendim hesapladım:

```python
c = float(np.sqrt(np.max(np.abs(st.P)) / RHO0))     # KABA VEKIL
dt = 0.2 * h / max(c, 1.0)
```

`√(2,6967e8/2700) = 316 m/s`. Kodun kendi `compute_timestep_solid`'i:
**10150 m/s**. `dt`'m **32,1 kat** büyüktü.

### Koşu patladı

```
adim   t (ms)    v_rms (m/s)     KE_ic (J)   rho sapma
   1    6.582    4.3054e-02    9.5581e+05   6.805e-04
   2   13.163    2.5311e+01    3.3034e+11   3.012e-02
   4   26.326    2.7414e+02    3.8750e+13   1.730e-01
   8   52.652    9.5555e+06    4.7081e+22   3.425e+02
  12   78.979    9.5555e+06    4.7081e+22   3.425e+02   <-- AYNI
```

Son iki satırın **birebir aynı** olması NaN'ın imzasıydı: `max` bir kez NaN
görünce donar.

### Neden vekil yanlıştı

`√(P/ρ)` bir **şok** ses hızı kestirimidir. Tillotson'ın küçük sıkışmadaki
ses hızını **hacim modülü** belirler. `√(A/ρ₀) = √(2,67e10/2700) ≈ 3145 m/s`
— o bile 3 kat düşük, çünkü asıl ifade

```
c² = ∂P/∂ρ|_u + (P/ρ²)·∂P/∂u|_ρ
```

ve `B·μ²` terimi ile `∂P/∂u` katkısı ekleniyor.

> **Kural:** kodun kendi hesabı varken elle vekil yazma.
> `compute_timestep_solid` zaten oradaydı. Bu S3'ün ikizidir.

---

## 3. K21 — patlamanın altından çıkan gerçek kusur

Patlamanın **yanında** bir uyarı vardı:

```
materials.py:269: RuntimeWarning: overflow encountered in exp
  ex = np.exp(-p.beta_t * (1.0 / eta - 1.0))
materials.py:271: RuntimeWarning: invalid value encountered in multiply
  p_hot = p.a * rho * u + (p.b * rho * u / omega + p.A * mu_t * ex) * ex2
```

Bunu "patlamanın yan etkisi" diye geçebilirdim. Geçmedim.

### Kök neden

```
ex = exp(−β·(1/η − 1)) ,    η = ρ/ρ₀
```

`η` küçük **negatif** iken `1/η` büyük negatif → üs büyük **pozitif** →
`exp` **taşar** (`inf`). Hemen ardından `ex2 = exp(−α·(1/η−1)²) = 0` ve

```
inf · 0  =  NaN
```

### Ölçüldü (`u = 2·u_cv`)

| ρ | P | sonlu mu |
|---|---|---|
| +0,27 | 4,914000e+06 | ✔ |
| 0,00 | 0,000000e+00 | ✔ |
| **−0,27** | **nan** | **✘** |
| −27,0 | −4,914000e+08 | ✔ |
| −2700 | −1,329076e+11 | ✔ |

**Kusur aralıksız değil** — yalnızca `ρ`'nin sıfıra yakın negatif olduğu
**dar bir bantta**. Rastgele bir sınamayla kolayca kaçırılır.

### Neden ciddi

1. **GPU'da sessizdir.** `wp.exp` uyarı vermez. Aynı ifade
   `eos_tillotson.py`'nin `_till_hot`'unda birebir duruyor. Bir üretim koşusu
   baştan sona NaN üretip *"bitti"* diyebilirdi.
2. **Yayılır.** Tek bir NaN parçacık komşuluğu üzerinden her toplamı NaN
   yapar.
3. **Tam da ejekta rejiminde.** `ρ → 0` **ve** `u ≥ u_cv` koşulu, seyrelmiş
   sıcak ejektanın ta kendisidir — FAZ 4'ün ölçmek istediği şey.

### `ρ ≤ 0` bir "geçersiz girdi" değil, bir başarısızlık işaretidir

Süreklilikte `dρ/dt = −ρ·∇·v` **üstel** azalır; sıfırı **ancak `dt` fazla
büyükse** geçer. Yani `ρ ≤ 0` her zaman **sayısal başarısızlıktır**. Doğru
tepki maskelemek değil, **görünür kılmaktır**.

---

## 4. Düzeltme — toplam yap, ama maskeleme

**(1) EOS toplam.** Sonlu girdi → sonlu çıktı. `ρ ≤ 0` için soğuk kol
(polinom, her zaman sonlu). CPU'da sıcak kol **güvenli `η`** ile hesaplanıyor
ki üs hiç oluşmasın. `ω`'nın tekil noktasında (`ρ = 0`) doğru **limit**:
`u > 0` ise `ω → ∞`, dolayısıyla `b/ω → 0`.

**(2) Maskelenmiyor.** Hem GPU çözücüsünün hem CPU referansının defteri artık
şunları raporluyor:

| alan | anlamı |
|---|---|
| `nonpositive_density_count` | kaç parçacıkta `ρ ≤ 0` |
| `rho_min` | en küçük yoğunluk |
| `state_is_finite` | `ρ`, `v`, `u` sonlu mu |

**Sayaç sıfırdan büyükse o koşu geçersizdir.**

---

## 5. İlk düzeltmem determinizmi bozdu — ve geri alındı

`ω`'yı şöyle yazdım:

```python
eta2 = np.maximum(eta * eta, 1.0e-300)
omega = u / (p.u0 * eta2) + 1.0
```

Eski ifade `u / (p.u0 * eta * eta) + 1.0` idi. Bunlar **aynı sayı değil**:
`u0·(η·η)` ile `(u0·η)·η` farklı yuvarlar.

Ölçüldü: 8000 örnekte en büyük fark **6,103515625e-05** (göreli `~1e-14`).

Determinizm **kilitli** bir özelliktir (ADR-0004). `1e-14` bile kabul
edilemez. Geri alındı:

```python
payda = p.u0 * eta * eta          # SIRA korunur
tekil = payda == 0.0
oran = np.divide(u, np.where(tekil, 1.0, payda))
oran = np.where(tekil, np.where(u > 0.0, np.inf, 0.0), oran)
omega = oran + 1.0
```

Doğrulandı: geçerli girdide **bit aynı** (`np.array_equal`), 8000 örnek.

> Bu, K1'in dersinin başka bir yüzü: *doğru sonuç* ile *doğru kod* aynı şey
> değildir. `1e-14` fark "doğru sonuç" verir ama determinizm sözünü bozar.

---

## 6. S5 — nedensel pencereyi komşu bölgeden hesapladım

`dt` düzeltildikten sonra ölçüm koştu. Ama:

```
hareketi olctugum bolge : `kenar`  -> yuzeye 24,8 m
pencereyi hesapladigim  : `arayuz` -> yuzeye 34,6 m

iddia    : (70 − 35,4)/10150 = 3,41 ms
gercek   : (70 − 45,2)/10150 = 2,44 ms
kostugum : 12 × 0,2049       = 2,46 ms      <-- DISARIDA
```

Son adımlar **fiziksel** dalgayı ölçüyordu. 1:1 durumunda çıkan `v ~ t^4,55`
gibi tuhaf üssü bu açıklar — sabit bir yapay kuvvet `t¹` verir, gelen bir
dalga çok daha dik.

**Düzeltme:** pencere artık **ölçülen bölgenin kendi dış kenarından**
türetiliyor ve kaç adımın güvenli olduğu koşudan **önce** yazdırılıyor:

```python
r_dis = float(mk["r"][bolge].max())      # bolgenin YUZEYE en yakin noktasi
t_nedensel = (r_outer - r_dis) / c
n_guvenli = int(np.floor(t_nedensel / dt))
n_adim = min(n_guvenli, 16)
```

> **Kural:** *"bu ölçüm hangi süre boyunca geçerli?"* sorusunun yanıtı
> **ölçülen bölgeden** türetilmeli, komşu bir bölgeden değil.

---

## 7. Yapısal kapatma

`tests/test_eos_totality.py` — 9 test, `-W error::RuntimeWarning` ile geçiyor:

| test | ne sınıyor |
|---|---|
| `test_k21_negatif_yogunluk_sicak_enerji_sonlu` | düzeltmeden önce **tam olarak NaN** veren durum |
| `test_k21_tum_enerji_kollarinda_sonlu` | 5 enerji × 7 yoğunluk |
| `test_gecerli_girdide_bit_ayni` | gerileme — determinizm |
| `test_gerileme_kontrolu_uc_kolu_da_kapsiyor` | **boşluk kontrolü**: örneklem üç kolu da geziyor mu |
| `test_defter_negatif_yogunlugu_rapor_ediyor` | maskelenmiyor mu |

Dördüncüsü olmasaydı, gerileme testi yalnızca sıkışmış kolu gezen bir
örneklemle **boş bir doğru** sınayabilirdi — düzeltmenin dokunduğu genleşmiş
kollara hiç uğramadan.

---

## 8. Bu turda denetim kodunun kendisi iki kez iş gördü

`tests/test_docs_registry.py` (S2'nin yapısal kapatması) bu kayıt yazılırken
**iki hatamı** yakaladı:

1. K21 gövdesini kapanış bölümünden **sonraya** koymuştum → sıra bozuktu.
2. S4/S5'i gövdeye yazıp **özet tabloya eklemeyi unutmuştum**.

Ve `tests/test_defter_index.py` (bu turda yazıldı) KAYIT-020'nin defter
dizinine **hiç eklenmediğini** yakaladı — çapa metni dosyanın biçimiyle
tutmamıştı, yani **S2 üçüncü kez** olmuştu.

> Kendi belgelerini sınayan testler, kendi kodunu sınayan testler kadar
> gereklidir. Üç kez aynı hata, bunu kanıtlar.

---

## 9. Sırada

| # | iş | durum |
|---|---|---|
| E1 | gerçek oturmuş yığının düzensizliği | TRUBA'da koşuyor |
| E2 | dinamik birikim (nedensel pencere denetimli) | yeniden koşuyor |
| E3 | arayüzden **şok** geçişi | sırada |
