# G ve H sonucu — gözlenebilir ayırt ediyor, ama niceliksel eşleme yakınsamıyor

**Tarih:** 2026-09-06 · **İşler:** `1548352`/`1548522` (G), `1548525` (H)
**Ölçütler:** `PROTOKOL-G-AYIRT.md`, `PROTOKOL-H-KRATER.md` —
**ikisi de koşudan önce commit'lendi**

---

## Özet

| soru | yanıt |
|---|---|
| Gözlenebilir `θ` hakkında **bilgi taşıyor mu**? | **EVET** — `F = 1006`, `Y₀` ile `ρ = −0,94` |
| Hangi eksende? | **yalnız matris `Y₀`**; blok `α₀` ve blok kesri değil |
| Niceliksel eşleme (`Y₀ = f(d)`) yakınsıyor mu? | **HAYIR** — çözünürlükle `%72` değişiyor |
| Çekme kırpık kol (`G2`) okunabildi mi? | **HAYIR** — şok kapısı `39/48` noktayı reddetti |

---

## 1. G1 — ayırt edilebilirlik: **AYIRT EDİYOR**

Üretim ayarı, kaba merdiven, `24 θ × 2` sahne gerçeklemesi, `48` koşu.
**Tanı hilesi yok.**

```
ON KOSULLAR
  kosu sayisi           : 48
  defter kapali         : [GECTI]
  sahne M1 (alpha0 >= 3): [GECTI]  benzersiz=[3]     <- A46 nobetcisi
VARYANS ORANI (krater_derinlik)
  S_theta = 0,00879   S_gurultu = 8,74e-06   F = 1006   (esik 4,0)
SIRA KORELASYONU
  blok_alpha0    rho = -0,2348   p = 0,2690
  matris_Y0      rho = -0,9417   p = 0,0000   ANLAMLI
  blok_kesri     rho = +0,0904   p = 0,6674
YARGI: AYIRT EDIYOR  (F = 1,01e+03, eksen: matris_Y0)
```

**Bu sınav bugüne kadar hiç geçerli yapılmamıştı** (A46: `θ`'nın üç
bileşeninden ikisi sahneye ulaşmıyordu).

### `β` için ölçüt **reddetti**

Aynı veride `Δβ` `F = 18,12` ve `matris_Y0` ile `p = 0,0026`
veriyordu — cazip sayılar. Betik **OKUNMAZ** dedi: ön koşul düştü
(`%10,4 < %80`; `48` koşunun yalnız `5`'inde kaçan hedef maddesi var).

Koşudan önce yazılmış bir ölçüt, sonradan cazip görünen bir sonucu
engelledi.

---

## 2. Fiziksel biçim — mukavemet rejimi geçişi

| `Y₀` | krater derinliği |
|---|---|
| `1,3e3 – 1e5 Pa` | `≈ 0,35 m` — **plato** |
| `3e5 – 9,3e6 Pa` | `0,30 → 0,081 m` — **dik düşüş** |

Doğrusal uydurma `R² = 0,789`; sigmoid `0,941`. Yani gözlenebilir
`Y₀`'ı **yalnız eşik üstünde** sınırlıyor; altında bilgi tek yanlı.

Kısıtlı sigmoid (`d_alt ≥ 0`, rapor A67):

```
d_alt = 0,0000 m   (KISIT SINIRINDA -- veriden degil)
d_ust = 0,3698 m
x0    = 6,340      (gecis: Y0 = 2,19e6 Pa)   <- veri ICINDE
w     = 0,538
R^2   = 0,9411     artik sigma = 0,0244 m
```

Birini dışarıda bırak (`24` kat): `RMSE = 0,0258 m`,
yanlılık `+0,0004 m`, `z` sapması `1,318`, `1σ` kapsama `0,750`.

---

## 3. H — çözünürlük direnci: **KORUNMUYOR**

`6 θ`, iki çözünürlük (`N = 17 201` ve `69 886`), iki gerçeklem.

| `log₁₀ Y₀` | `d_kaba` | `d_orta` | fark | gürültü | oran |
|---:|---:|---:|---:|---:|---:|
| `3,631` | `0,3556` | `0,6120` | `0,419` | `0,0244` | `17` |
| `4,220` | `0,3618` | `0,6951` | `0,480` | `0,0043` | `111` |
| `4,930` | `0,3498` | `0,6483` | `0,460` | `0,0152` | `30` |
| `5,880` | `0,2364` | `0,3706` | `0,362` | `0,0008` | `483` |
| `6,574` | `0,1420` | `0,1658` | `0,144` | `0,0273` | `5` |
| `6,801` | `0,0997` | `0,1056` | `0,056` | `0,0005` | `108` |

Oran medyanı **`69`**; kilitli eşik `> 10` → **KORUNMUYOR**.

### Ama iki şey ayrı — ve bu ayrım sonucun kendisi

| nicelik | kaba | orta | durum |
|---|---|---|---|
| **mutlak derinlik** | `0,36 m` | `0,61 m` | `%72` fark — **yakınsamamış** |
| **`Y₀` ile ilişki** | `r = −0,943` | `r = −0,925` | **neredeyse aynı** |

`4` kat parçacık sayısı değişimi ilişkinin **gücünü ve işaretini**
değiştirmiyor; **ölçeğini** değiştiriyor.

---

## 4. Ne ayakta, ne değil

| iddia | durum |
|---|---|
| Krater derinliği `Y₀` hakkında bilgi taşıyor | **ayakta** — iki ölçekte de |
| Bilgi **yalnız** `Y₀` ekseninde; blok yapısı çözülmüyor | **ayakta** |
| Eşik altında sınır **tek yanlı** | **ayakta** |
| `Y₀ = f(derinlik)` **niceliksel eşlemesi** | **DÜŞTÜ** — ölçeğe bağlı |
| Hesaplanan posterior (`Y₀ ∈ [4,5e5 ; 1,3e6] Pa`) | **aktarılamaz** |

`vekil_posterior.py`'nin ürettiği sayı bir **yöntem gösterimi**dir —
zincirin uçtan uca çalıştığını kanıtlar, fiziksel bir öngörü vermez.

---

## 5. G2 okunamadı — ve nedeni bir bulgu

`48` noktanın **`39`'u** `SOK KURULMADI` ile düştü (rapor A68).

| kol | son sıkışma medyanı | geçen |
|---|---:|---:|
| `G1` üretim | `%21,70` | `24/48` |
| `G2` çekme kırpık | `%5,38` | **`5/48`** |

Kapı eşiği `%4,561`. Çekme kırpılınca madde **gerçekten gevşiyor**,
artık sıkışma `2 – 5` kat düşüyor, ve kapı **daha iyi davranan kolu
reddediyor**. Geçen `5` nokta da en yüksek `Y₀`'lar — örneklem
**güçlü matrise sapıyor**.

Uzmanın uyarısı ölçüldü: *"son zamanda kalıcı yoğunluk isteyen kapı,
gözenekli malzemeyi seçici biçimde avantajlı gösterebilir."*

`G2` ancak kapı **koşu boyunca zirve** üzerinden kurulunca (A45'in
önerisi) koşulabilir.

---

## 6. Bundan sonrası

| iş | neyi açar | engel |
|---|---|---|
| Şok kapısını **zirveye** taşı | `G2` okunabilir olur | küçük; A45 tasarımı hazır |
| A52 (komşu yarıçapı) | üç noktalı yakınsama, `Y₀ = f(d)` kalibrasyonu | büyük, haftalık |
| Granüler çekme modeli | üretim modelinde kazı | büyük, ADR gerekiyor |

İlki bu turda yapılabilir; diğer ikisi yapılamaz ve **öyle
bildiriliyor**.
