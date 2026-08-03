# ADR-0037 — Mermi yakınsaması çözünürlükle ölçülür, kafes kalıntısıyla değil

- **Durum:** Kabul edildi
- **Tarih:** 2026-08-03
- **Bağlam:** FAZ 3, G3 C4, P3-VR-02 (">=3 çözünürlükte yakınsak")
- **İlgili:** ADR-0035 (vekil ölçüt), ADR-0036 (yanlı örneklem)

## Kusur

Kriter şuydu:

```python
"volume_error_converges": bool(rows[0]["volume_error"] > rows[-1]["volume_error"])
```

`volume_error = |N·V_p − V_küre| / V_küre` — yani **kafesin küreye nasıl
oturduğunun kalıntısıdır**, düzgün bir ayrıklaştırma hatası değil. FCC kafesi
bir küreye kesişirken kaç parçacığın içeri düştüğü N ile **sıçramalı** değişir.

## Ölçülen etki

| N (gerçek) | 207 | 399 | 803 | 1568 | 3184 | 6401 | 12808 |
|---|---|---|---|---|---|---|---|
| kafes kalıntısı | 0,03500 | 0,00250 | 0,00375 | **0,02000** | 0,00500 | 0,00016 | 0,00063 |

**Monoton değil**; bir adımda **+0,01625 artıyor** (803 → 1568).

Kriterin sonucu **hangi N'lerin seçildiğine bağlı**:
- `(200, 800, 3200)` → `0,03500 > 0,00500` → **True** (mevcut seçim)
- `(400, 800, 1600)` → `0,00250 > 0,02000` → **False**

Yani kriter, senaryonun keyfi bir parametresiyle geçiyordu.

## Gerçekten yakınsayan ne?

| büyüklük | davranış |
|---|---|
| çap boyunca parçacık | 6,46 → 8,14 → 10,26 → 12,93 → 16,29 → 20,52 → 25,86 — **kesin artan** |
| kütle hatası | ≤ 5,89e-16 — makine hassasiyeti |
| momentum hatası | ≤ 4,0e-14 |
| kafes kalıntısı | **dalgalanıyor**, zarfı küçülüyor |

Oran kontrolü: `25,86/6,46 = 4,00` ve `(12808/207)^(1/3) = 3,94` — çözünürlük
`N^(1/3)` ile ölçekleniyor, beklendiği gibi.

## Karar

- Kriter **`resolution_increases`**: çap boyunca parçacık sayısı kesin artmalı.
- Kafes kalıntısı **olduğu gibi raporlanır**: `volume_error_ladder`,
  `volume_error_monotone` (False), `volume_error_envelope_shrinks`,
  `volume_error_max`. G3 C4 **zarfın** küçülmesini şart koşar, monotonluğu
  değil — çünkü monotonluk bu büyüklük için fiziksel bir beklenti değil.
- Kanıt metni artık merdiveni ve "MONOTON DEĞİL" ibaresini **açıkça** yazar.

Ayrıca `starts_outside_target` elle yazılmış `> 80.0` eşiğini bırakıp
ADR-0035'in mesh üyeliği ölçüsünü kullanır: eşik mesh yarıçapına eşitti
(tesadüfen doğru) ama **sabit bir sayıydı**; mesh değişirse sessizce
anlamsızlaşırdı.

## Yapısal önlem

- `test_yakinsama_olcusu_CAP_BOYUNCA_parcacik` — merdiven kesin artan.
- `test_kafes_kalintisi_MONOTON_OLMADIGI_kayitli` — **boşluk kontrolü**:
  kalıntı monoton çıkarsa bu düzeltmenin gerekçesi kaybolmuş demektir.
- `test_mermi_disarida_MESH_UYELIGIYLE` — üç çözünürlükte de `0` parçacık
  içeride.

## Ders

Desenin sekizinci örneği:

> **Bir büyüklüğün "yakınsadığını" iddia etmeden önce, o büyüklüğün
> yakınsaması BEKLENEN bir büyüklük olup olmadığı sorulmalıdır.**

Kafes-oturma kalıntısı, ayrıklaştırma hatası gibi *görünen* ama öyle olmayan
bir sayıdır. K13/K14/K15 ile aynı aile: ölçüt yanlış büyüklüğü, vekili ya da
yanlı örneklemi ölçüyordu; burada ölçüt **yanlış davranış beklentisini**
ölçüyor.
