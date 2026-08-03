# ADR-0031 — P-α crush eğrisinin tavanı parçacık başınadır

- **Durum:** Kabul edildi
- **Tarih:** 2026-08-03
- **Bağlam:** FAZ 2 porozite + FAZ 3 heterojen moloz yığını
- **İlgili:** ADR-0022 (gerilmesiz gözenekli başlangıç), ADR-0023 (örtük çözüm),
  ADR-0030 (kütle gözeneklilikten türer), P3-FR-03/04

## Kusur

P-α crush eğrisi, distansiyonun üst sınırını **malzemenin skaler**
`PorosityParams.alpha0` değerinden alıyordu:

```python
return np.where(P <= self.Pe, self.alpha0, ...)     # SKALER tavan
```

Gözeneklilik ise **parçacık başınadır**: P3-FR-03/04 gereği bloklar gözeneksiz
(α ≈ 1,05), matris gözeneklidir. Başlangıç distansiyonu bu skaleri **aşan** her
parçacık, ilk adımda tavana **ezilir**. O anda `rho·alpha = rho0` gerilmesiz
başlangıç şartı (ADR-0022) bozulur ve devasa **yapay çekme** doğar.

## Nasıl bulundu

ADR-0030'dan sonra `test_esik_altinda_ve_yakinsadi` kaldı: settling
yakınsamıyordu. Ölçüm (iş 1449843):

```
E_bağ = 1,703479e+06 J    eşik(1e-3) = 1,703479e+03 J
 40 adım: KE_son = 4,894274e+12 J   KE/E_bağ = 2,873e+06
200 adım: KE_son = 3,896113e+09 J   KE/E_bağ = 2,287e+03
```

KE, bağlanma enerjisinin **2,9 milyon katı**. Yerçekiminden gelemez:
`a_yerçekimi(t=0) = 3,213e-05 m/s²` ile 0,0134 s'de `v ~ 4e-7 m/s` olmalıydı;
ölçülen `v_rms ≈ 78 m/s`.

Hipotez kuruldu ve **karşı-kontrollü** ölçüldü (iş 1449888, H100):

| adım | malzeme tavanı 1,6 (mevcut) | malzeme tavanı 1,7273 (uygun) |
|---|---|---|
| 0 | α=1,727253 · P=0 · KE=0 | α=1,727253 · P=0 · KE=0 |
| 1 | **α=1,600000** · P=0 · KE=8,23e-08 | α=1,727253 · P=0 · KE=8,23e-08 |
| 2 | α=1,600000 · **P=−1,1389e+09 Pa** · KE=3,36e+10 | α=1,727253 · P=−1,6e-04 Pa · KE=2,70e-07 |
| 4 | α=1,600000 · P=−1,1294e+09 Pa · **KE=8,29e+11** | α=1,727253 · P=5,1e-03 Pa · **KE=9,66e-07** |

**KE oranı: 8,587e+17.** Hipotez doğrulandı.

Yığının matris α'sı 1,7273 (ADR-0030 ile hedef yığın yoğunluğundan çözülüyor),
malzemenin skaleri 1,6. Fark %7,4 ve tek adımda **−1,14 GPa** üretiyor.

## Kusur ne kadar eskiydi

**ADR-0030 onu görünür yaptı, ama kusur hep vardı.** Önceden:

- matris α₀ = 1,6 **tesadüfen** malzemeninkine eşitti → ezilme yok,
- bloklar α₀ = 1,05 < 1,6 → geri-genleşme yasağı (`min(alpha_old, ...)`)
  onları koruyordu.

Yani model **yalnızca homojen gözeneklilik için** doğruydu; heterojen yığın
tam olarak FAZ 3'ün ürettiği şey.

## Karar

Crush eğrisinin tavanı **parçacık başına başlangıç distansiyonudur**:

- GPU: `porosity_update_k` yeni bir `alpha_ref` dizisi alır;
  `crush_alpha(P, a0, pp)` tavanı oradan okur.
- CPU: `PorosityParams.crush_alpha(P, alpha_ref=None)` ve
  `solve_alpha_implicit(..., alpha_ref=None)`. Verilmezse skaler kullanılır —
  homojen koşularda davranış **değişmez**.
- `SolidState.alpha_ref` yoksa `__post_init__` `alpha`nın kopyasını alır.
- `WarpSolid3D.alpha_ref` başlangıç `alpha0` dizisinin kopyasıdır.

Fiziksel gerekçe: α₀ *"bu malzeme elemanının başlangıç distansiyonu"*dur.
Heterojen bir cisimde bu, tanımı gereği parçacık başınadır.

## Yapısal önlem

`TestPerParticleCrushCeiling`:
- eşik altında (P ≤ Pe) her parçacık **kendi** α₀'ını korur;
- tavan verilmezse skaler kullanılır (geriye dönük uyum);
- `solve_alpha_implicit` gerilmesiz başlangıcı **bozmaz**;
- **boşluk kontrolü:** gerçek basma hâlâ eziyor — tavanı parçacık başına
  yapmak crush işlevini kaybettirmiyor.

Her testte eski davranışın ölçüsü de assert ediliyor (`eski[0] < 1.65`), yani
düzeltmenin gerekçesi testin içinde ölçülü duruyor.

## Ders

Bu, **aynı fiziksel büyüklüğün iki yerde tanımlanması** sınıfının üçüncü
örneği:

| # | büyüklük | yer 1 | yer 2 | sonuç |
|---|---|---|---|---|
| K7 | yığın yoğunluğu | `bulk_density` (kütle) | `alpha0` (yoğunluk) | −7,6 GPa |
| K10 | başlangıç distansiyonu | `pile.alpha0` (dizi) | `porosity.alpha0` (skaler) | −1,14 GPa |

Kural: **bir büyüklük iki yerde yazılıysa, hangisinin türetildiği kodda
görünmelidir.** Türetilmeyen ikinci bir kopya er geç ayrışır.
