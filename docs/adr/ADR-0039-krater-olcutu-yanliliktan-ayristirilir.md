# ADR-0039 — Krater/küresel ayrımı, yüzey yanlılığından ayrıştırılarak ölçülür

- **Durum:** Kabul edildi
- **Tarih:** 2026-08-03
- **Bağlam:** FAZ 3, G3 C5, P3-FR-08
- **İlgili:** ADR-0029 (K2, küresellik varsayımı), ADR-0035–0038

## Kusur

Kriter şuydu:

```python
"crater_separates_global": bool(abs(cs.global_radius_change) < 5.0)
```

`global_radius_change = R_ölçülen − R_girdi` iki şeyin **toplamıdır**:

1. **yüzey örneklem yanlılığı** — "yüzey" yön kutusundaki en uzak parçacıktır
   ve gerçek yüzeyin bir miktar içinde kalır (ADR-0029'da K2 için de ölçülmüştü),
2. gerçek küresel deformasyon.

Elle yazılmış `5.0` bunları **ayırmıyordu**; yalnızca yanlılığı barındıracak
kadar genişti.

## Ölçülen etki (80 m küre, 40000 parçacık)

| durum | `global_radius_change` | yanlılıktan sapma |
|---|---|---|
| **deformasyonsuz** | **−1,5335 m** | — (saf yanlılık; gerçek 0) |
| 16 m kraterli | −1,5335 m | **+0,0000 m** |
| %10 küresel büzüşme | −9,3802 m | **−7,8466 m** (beklenen ≈ −8) |

**Çıkarıcı krateri küresel değişimden mükemmel ayırıyor** — krater durumunda
yanlılıktan sapma tam **sıfır**, gerçek büzüşme ise tam beklenen büyüklükte
yakalanıyor. Kusur **ölçütteydi**, çıkarıcıda değil (K13/K14 ile aynı sınıf).

## Karar

Yanlılık, **aynı cismin deformasyonsuz hâlinden doğrudan ölçülür**; kriter
ondan **sapmaya** bakar:

- `crater_global_bias` — deformasyonsuz taban (raporlanır, gizlenmez)
- `crater_global_excess` — krater durumundaki fazlalık; kriter `|excess| < 0,5`
- `crater_shrink_excess` — **pozitif kontrol**: %10 büzüşmede fazlalık
- `crater_detects_real_shrink` — gerçek deformasyon yakalanıyor mu

G3 C5 artık **her ikisini** şart koşar: krater sızmamalı **ve** gerçek
büzüşme yakalanmalı. Pozitif kontrol olmadan ilk şart boş bir doğru olurdu —
her şeye "0" diyen bir çıkarıcı da onu sağlardı.

Tolerans **0,5 m**: eskisinden **10 kat dar**, üstelik doğru büyüklüğü ölçüyor.

## Ek düzeltme — `deterministic` kapsamı

`run_rubble_quality`'deki determinizm ölçütü yalnızca `x` ve `Y0`'ı
karşılaştırıyordu. ADR-0030'dan sonra `m` ve `alpha0` **türetilmiş**
büyüklüklerdir; türetme yolundaki bir sapma görünmezdi. Ölçüt tam duruma
genişletildi: `x`, `m`, `alpha0`, `Y0`, `is_boulder`.

## Yapısal önlem

- `test_krater_kuresel_ayrimi_YANLILIKTAN_ayristirilmis` — fazlalık tam 0;
  **ve yanlılığın kendisi sıfır olmamalı** (sıfırsa ayrıştırmanın gerekçesi
  kalmaz),
- `test_krater_POZITIF_KONTROL_gercek_buzusmeyi_yakaliyor` — fazlalık ≈ −8,
- `test_determinizm_TAM_durumu_karsilastiriyor`.

## Ders

Desenin onuncu örneği:

> **Bir ölçüm, aradığın sinyal ile bilinen bir yanlılığın toplamıysa,
> yanlılığı ayrı ölç ve kriteri FARKA uygula.** Yanlılığı barındıracak kadar
> geniş bir eşik, sinyali de barındırır.

Ve her "ayrışıyor" iddiası bir **pozitif kontrol** ister: ayırt edemeyen bir
ölçüt de "ayrıştı" der.
