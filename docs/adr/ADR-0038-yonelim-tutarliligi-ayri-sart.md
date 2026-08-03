# ADR-0038 — Yönelim tutarlılığı, kenar-manifoldluktan AYRI bir şarttır

- **Durum:** Kabul edildi
- **Tarih:** 2026-08-03
- **Bağlam:** FAZ 3, G3 C1 (şekil-mesh hattı), P3-FR-01
- **İlgili:** ADR-0025 (ışın dejenereliği), ADR-0035–0037 (ölçüt kusurları)

## Kusur

`TriMesh.is_edge_manifold()` kenarları **sıralayarak** sayar:

```python
e = np.sort(e, axis=1)          # (a,b) ile (b,a) AYNI sayılır
return bool(np.all(counts == 2))
```

Bu yüzden **ters sarılmış bir yüzü göremez.** Ölçüldü (ikosfer(3), yüzler
rastgele ters çevrilerek):

| ters yüz | `is_edge_manifold()` | hacim hatası |
|---|---|---|
| 1 | **True** | %0,109 |
| 5 | **True** | %0,764 |
| 20 | **True** | %3,112 |
| 100 | **True** | **%15,545** |

Yani yönelimi bozuk bir ağ "manifold" sayılıp **hacmi %15,5 yanlış**
verebiliyordu.

## Neden önemli

Mesh hacmi üç yere giriyor:

1. **yığın yoğunluğu** — `Σm / V_mesh` (ADR-0033)
2. **blok hacim hedefi** — `f_boulder · V_mesh`
3. **etkin yarıçap** — kaçış hızı ve bağlanma enerjisi

Analitik şekillerde (ikosfer, elipsoit) C1'in `max_volume_rel_err < 0.01`
kontrolü bunu yakalar. **Yüklenen OBJ'de — yani gerçek PDS Dimorphos
modelinde — karşılaştırılacak analitik hacim YOKTUR**; orada yakalayan başka
bir şey de yoktu. `orient_outward` yalnızca toplam hacim negatifse **tüm**
ağı çevirir; yüz başına sarımı düzeltmez.

## Karar

Yeni `TriMesh.is_consistently_oriented()`: her **yönlü** kenar tam bir kez
görünmeli. Kapalı ve tutarlı yönelimli bir ağda her kenar bir üçgende `(a,b)`,
komşusunda `(b,a)` olarak geçer.

Bağlandığı yerler:
- `run_shape_pipeline` → `orientation_consistent`, `all_oriented`
- **G3 C1** artık `all_oriented` şartını da koşar
- `test_pds_shapemodel` gerçek PDS ağında ayrıca doğrular

Tespit edilir ve **reddedilir**; sessizce onarılmaz. Onarım (yüz başına sarım
düzeltme) ayrı bir karardır ve bu ADR'nin kapsamı dışındadır.

## Ölçülen: iki kontrol BAĞIMSIZ

| bozulma | `is_edge_manifold()` | `is_consistently_oriented()` |
|---|---|---|
| delik (bir yüz silinmiş) | **False** | True |
| ters sarım | True | **False** |

İlk yazdığım test *"delik ikisini de bozar"* diye **tahmin** ediyordu ve
düştü. Kod doğru: kapalılık ile yönelim ayrı özelliklerdir ve **tam bu yüzden
ikisi de gereklidir.** Test, ölçülen davranışı yazacak şekilde düzeltildi.

## Yapısal önlem

`TestOrientationConsistency`:
- sağlam ağlar her iki kontrolden geçer,
- 1/5/20/100 ters yüzde **kenar-manifold geçer, yönelim kalır** (kusurun
  ölçüsü testin içinde),
- **boşluk kontrolü:** ters sarım hacmi gerçekten bozuyor mu — hata ters yüz
  sayısıyla monoton artmalı ve 100 yüzde %10'u geçmeli,
- iki kontrolün bağımsızlığı.

## Ders

Desenin dokuzuncu örneği:

> **Bir kontrolün adı, neyi kontrol ettiğini söylemeyebilir.** "Manifold"
> sezgisel olarak "ağ sağlam" demek gibi durur; gerçekte yalnızca *her kenar
> iki yüzde mi* sorusunu yanıtlar. Sağlamlığın diğer yarısı (yönelim)
> sorulmuyordu.
