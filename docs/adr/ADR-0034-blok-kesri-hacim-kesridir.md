# ADR-0034 — Blok kesri HACİM kesridir, kütle kesri değil

- **Durum:** Kabul edildi
- **Tarih:** 2026-08-03
- **Bağlam:** FAZ 3, P3-FR-03 ("f_boulder geri-ölçüm testi"), G3 C2
- **İlgili:** ADR-0030 (kütle gözeneklilikten türer), ADR-0033

## Kusur

`run_rubble_quality` blok kesrini şöyle ölçüyordu:

```python
f_meas = float(np.sum(boul.m[boul.is_boulder]) / np.sum(boul.m))   # KÜTLE kesri
...
"boulder_fraction_target": 0.30,                                    # HACİM hedefi
```

`f_boulder` hedefi **hacim** olarak tanımlıdır —
`boulder_volume_target = f_boulder * mesh.volume`. Ölçülen ise **kütle**
kesriydi. Tekdüze kütlede bu ikisi **aynı sayıdır**; ADR-0030'dan sonra
bloklar ağırlaştığı için ayrıştılar.

## Ölçülen etki (ikosfer r=80, s=7, f_boulder=0,30)

| büyüklük | değer | hedeften sapma |
|---|---|---|
| hedef (hacim) | 0,3000 | — |
| ölçülen **hacim** kesri | **0,3034** | **+%1,1** |
| ölçülen **kütle** kesri (eski kod) | **0,4335** | **+%44,5** |

**Üretici doğruydu.** G3 C2 *"blok kesri 0.433 (hedef 0.30)"* diye kalıyordu,
oysa üretici hedefi %1,1 hatayla tutturuyor.

Kapalı form doğrulandı (6 hane):

```
f_kütle = f_h·r / (f_h·r + 1 − f_h),      r = m_blok/m_matris
f_h = 0,3034 ,  r = 1,7565  ->  0,433483
ölçülen                        0,433483
```

ve `r`, ADR-0030'un doğrudan sonucudur: `r = α_matris/α_blok = 1,8443/1,05`.

## Karar

- Kriter **hacim** kesrini okur: `boul.boulder_volume_fraction`.
- Kütle kesri **fiziksel olarak anlamlıdır** (bloklar kütlenin daha büyük
  payını taşır) ve **ayrı adla** raporlanır: `boulder_mass_fraction`,
  `boulder_mass_over_volume_fraction`. Hedefle karşılaştırılmaz.

## Yapısal önlem

`TestBoulderFractionIsVolumeNotMass`:
- hacim kesri hedefi tutturur,
- kütle kesri hacim kesrinden **belirgin** büyük — eşitlik çıkarsa ADR-0030
  geri alınmış demektir, yani test **iki düzeltmeyi birden** bekçilik eder,
- iki kesir arasındaki **kapalı-form** ilişki `rel=1e-12` ile kilitli,
- `r`'nin α oranından türediği de kilitli,
- denetimin **hacim** kesrini raporladığı doğrulanır.

## Ders

Desenin beşinci örneği ve en öğretici olanı: burada **kod doğruydu, ölçüm
yanlıştı.** Bir kriter kaldığında ilk soru *"üretici mi bozuk, ölçü mü
yanlış?"* olmalı. Ölçüt ile hedefin **aynı büyüklüğü** ifade ettiği ayrıca
doğrulanmalıdır — ADR-0033'teki gibi, ad aynı olduğunda ayrım gizlenir.
