# ADR-0036 — "İç bölge" geometrik tanımlanır, ölçülen büyüklükle değil

- **Durum:** Kabul edildi
- **Tarih:** 2026-08-03
- **Bağlam:** FAZ 3, G3 C2 (moloz yığını komşuluk sayısı), P3-FR-02
- **İlgili:** ADR-0034, ADR-0035 (ölçüt asıl soruyu mu ölçüyor?)

## Kusur

`coordination_interior_mean` şöyle hesaplanıyordu:

```python
np.mean(cn[cn >= np.median(cn)])
```

Parçacıklar **ölçülen büyüklüğe göre** seçilip sonra o büyüklük ortalanıyordu.
Ölçüt **kendi cevabını seçiyor**: hangi dağılım verilirse verilsin, üst yarının
ortalaması alt yarıyı görmez.

## Ölçülen etki (ikosfer r=100, aralık 10)

| durum | eski ölçüt | gerçek iç ortalama |
|---|---|---|
| bozulmamış FCC | 12,00 | 12,00 |
| **%25 bozuk kafes** | **11,19** | **10,25** |
| %50 bozuk kafes | 9,73 | 9,05 |
| %75 bozuk kafes | 9,35 | 8,45 |
| tamamen rastgele | 15,20 | 13,31 |

Kapının bandı `[11,0 ; 12,01]`. Yani **parçacıkların dörtte biri
0,35·aralık kaydırılmış bir yığın GEÇİYORDU** — gerçek değeri 10,25, bandın
dışında.

Ölçüt sistematik olarak **iyimser**: bozulma arttıkça fark +0,7 … +0,9.

Not: rastgele bulut 15,20 veriyor, yani **üst sınır** (12,01) kafes olmayanı
reddetme işini görüyor; **alt sınır** ise bozulmuş kafesi yakalayamıyordu.

## Karar

"İç bölge" **geometrik** tanımlanır: yüzeyden en az `2,5 × aralık` içeride.
Bu tanım, ölçülen büyüklükten **bağımsızdır**.

- `coordination_interior_mean` artık geometrik maskeyle hesaplanır,
- `coordination_interior_n` kaç parçacık kullanıldığını bildirir,
- eski, kendi cevabını seçen ölçüt `coordination_selfselected_mean` adıyla
  **ayrıca** raporlanır: ikisi arasındaki fark, kafesin ne kadar düzgün
  olduğunun doğrudan göstergesidir (bozulmamış FCC'de tam **0,0**).

İç bölge boş kalırsa (çözünürlük çok kaba) **hata verilir** — sessizce
sapılmaz.

## Yapısal önlem

`TestCoordinationInteriorIsGeometric`:
- bozulmamış FCC'de iki ölçüt de 12,00,
- **boşluk kontrolü:** %25 bozuk kafeste ikisi **ayrışmalı** (`kendi > geom +
  0,5`) ve tam olarak sorun budur: eski ölçüt eşiği geçer (≥ 11,0), gerçek
  geçmez (< 11,0). Ayrışmıyorsa düzeltmenin gerekçesi kaybolmuş demektir,
- denetim geometrik ölçütü raporlar.

## Ders

Desenin yedinci örneği ve en ince olanı:

> **Bir alt kümeyi, ölçmek istediğin büyüklüğe göre seçme.** Seçim ölçütü ile
> ölçülen büyüklük aynı şeyse, sonuç kendini doğrular.

ADR-0035'teki vekil sorusunun kardeşi: orada ölçüt yanlış büyüklüğü ölçüyordu,
burada doğru büyüklüğü **yanlı bir örneklem** üzerinde ölçüyor.
