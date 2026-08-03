# ADR-0032 — Merminin distansiyonu türetilir, sabit 1 değildir

- **Durum:** Kabul edildi
- **Tarih:** 2026-08-03
- **Bağlam:** FAZ 3 sahne birleştirici (`setup/scene.py`), P3-FR-06
- **İlgili:** ADR-0022 (gerilmesiz gözenekli başlangıç), ADR-0030 (kütle
  gözeneklilikten türer), ADR-0031 (crush tavanı parçacık başına)

## Kusur

Sahne birleştirici merminin distansiyonunu **sabit** yazıyordu:

```python
alpha0 = np.concatenate([pile.alpha0, np.ones(n_i)])    # mermi: alpha = 1
```

Çözücü **tek malzemelidir**: her parçacığın yoğunluğunu `rho0_solid / alpha0`
diye atar (ADR-0022). Merminin yoğunluğu ise `impactor_density` ile **ayrıca**
veriliyor ve `build_impactor` paketleme hacmini ondan hesaplıyor.

İkisi ayrışırsa SPH hacmi paketleme hacminden kopar. Ölçüldü
(`rho0_solid = 2700`):

| `impactor_density` | `alpha0` | çözücünün ρ'su | V_SPH / V_paketleme |
|---|---|---|---|
| 2700 | 1,0000 | 2700,0 | 1,0000 |
| 3000 | 1,0000 | 2700,0 | **1,1111** |
| 2000 | 1,0000 | 2700,0 | **0,7407** |

Yani %11–26 tutarsızlık, **hiçbir uyarı olmadan** — ve mermi, β'yı taşıyan
bileşendir; buradaki hata doğrudan başlık sayısına gider.

## Neden görünmüyordu

Üretim konfigürasyonunda `impactor.density: 2700.0` ve `tillotson.rho0: 2700.0`
**aynı** yazılı. Oran 1,0 çıkıyordu — ama **tesadüfen**, tıpkı K10'da matris
α₀'ının malzemeninkine tesadüfen eşit olması gibi. İkisini bağlayan hiçbir şey
yoktu; biri değiştiğinde sessizce ayrışacaktı.

## Karar

Distansiyon **türetilir**:

```python
alpha_imp = rho0_solid / impactor_density
```

Böylece çözücünün atadığı yoğunluk `rho0_solid / alpha_imp = impactor_density`
olur ve `V_SPH = m/impactor_density = V_paketleme` — **inşaat gereği** tutarlı.

- `impactor_density == rho0_solid` iken `alpha = 1,0` **tam** çıkar; üretim
  koşularında davranış değişmez.
- `impactor_density > rho0_solid` ise α < 1 gerekirdi — fiziksel değil, **hata
  verilir**. Çözücü tek malzemeli olduğu için mermi ancak hedef malzemesinden
  **seyrek** (gözenekli) temsil edilebilir; bu sınır açıkça söylenir.

Tanılar: `impactor_alpha0`, `impactor_density`, `rho0_solid`,
`impactor_volume_consistency` (1,0 olmalı).

## Düzeltme sonrası ölçüm

| `impactor_density` | `alpha0` | tutarlılık |
|---|---|---|
| 2700 | 1,0000 | **1,000000** |
| 2000 | 1,3500 | **1,000000** |
| 1500 | 1,8000 | **1,000000** |
| 3000 | — | **açık hata** |

Kütle ve momentum defteri etkilenmiyor (test ile kilitli).

## Ders — desenin dördüncü örneği

| # | büyüklük | yer 1 | yer 2 | sonuç |
|---|---|---|---|---|
| K7 | yığın yoğunluğu | `bulk_density` | `alpha0` | −7,6 GPa |
| K10 | başlangıç distansiyonu | `pile.alpha0` | `porosity.alpha0` | −1,14 GPa |
| K11 | mermi yoğunluğu | `impactor_density` | `rho0_solid`/`alpha0` | %11–26 hacim |

Üçünde de aynı imza: **aynı fiziksel büyüklük iki yerde yazılı, biri
türetilmiyor.** Üçü de üretim değerlerinde *tesadüfen* tutuyordu.

Kural: **bir büyüklük iki yerde yazılıysa, ikincisi birinciden türetilmeli ya
da ayrışma hata vermeli.** "Şu an aynı" bir güvence değildir.
