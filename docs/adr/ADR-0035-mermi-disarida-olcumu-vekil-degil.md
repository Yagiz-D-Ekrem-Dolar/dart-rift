# ADR-0035 — "Mermi hedefin dışında mı" doğrudan ölçülür, vekille değil

- **Durum:** Kabul edildi
- **Tarih:** 2026-08-03
- **Bağlam:** FAZ 3, G3 C6 (sahne fiziksel bütünlüğü), P3-FR-06/07
- **İlgili:** ADR-0033 (iki hacim tanımı), ADR-0034 (hacim vs kütle kesri)

## Kusur

Kriter şuydu:

```python
"impactor_outside_target": bool(imp_dist > a.target_radius)
```

`target_radius` **eşdeğer küre** yarıçapıdır (`r_eff = (3V/4π)^(1/3)`).
Bu, yalnızca **küre** için geçerli bir vekildir. Denetim ikosfer üzerinde
koşuyordu — orada `r_eff` gerçek yarıçapa eşit olduğu için vekil **tesadüfen**
doğruydu. Üretim konfigürasyonu (`p3_dimorphos.yaml`) ise **gerçek PDS
şeklini** kullanıyor.

## Ölçülen etki

Gerçek Dimorphos oranlarında elipsoit (88 × 87 × 65 m), r_eff = 39,59 m:

| çarpma ekseni | mermi min uzaklık | vekil (`\|x\|>r_eff`) | mesh içinde parçacık | gerçek |
|---|---|---|---|---|
| kısa (z) | 32,63 m | **False** | **0/207** | dışarıda |
| uzun (x) | 44,13 m | True | 0/207 | dışarıda |

Kısa eksende vekil **yanlış negatif** veriyor: mermi gerçekten dışarıda
(hiçbir parçacığı mesh'in içinde değil) ama kriter "değil" diyor.

Ters yön de mümkündür: uzun eksende yüzey `r_eff`'ten **4,4 m dışarıda**
olduğu için, `r_eff`'i geçen ama gövdeye **gömülü** bir mermi vekile göre
"dışarıda" sayılırdı.

## Karar

Kriter **doğrudan** ölçülür: hiçbir mermi parçacığı hedef mesh'inin içinde
olmamalı (`inside_points`). Ek olarak aynı sınav **düzensiz cisimde** de
koşulur — vekilin kırıldığı yer orasıdır.

Raporlanan yeni alanlar:
`impactor_particles_inside_mesh`, `irregular_impactor_inside_mesh`,
`irregular_all_outside`, `irregular_proxy_disagrees`, `irregular_detail`.

G3 C6 artık `irregular_all_outside` şartını da koşar.

## Doğrulanan: yerleştirme kodu DOĞRU

`place_impactor` kusurlu değil. Dört senaryoda (küre/elipsoit × kısa/uzun
eksen) **0/207** mermi parçacığı mesh içinde; en yakın mermi-hedef mesafesi
1,72–4,09 m (parçacık aralığı 6,0). Kusur **ölçütteydi**, üreticide değil —
K13 ile aynı sınıf.

## Yapısal önlem

`test_mermi_disarida_olcumu_VEKIL_DEGIL`,
`test_duzensiz_cisimde_de_mermi_disarida`,
`test_vekil_olcutun_yanildigi_KAYITLI`.

Sonuncusu bir **boşluk kontrolüdür**: vekil gerçekten yanılıyor mu?
Yanılmıyorsa bu düzeltmenin gerekçesi kaybolmuş ve ilk iki test boş bir
doğruyu sınıyor demektir.

## Ders

Desenin altıncı örneği. Bir kriterin **vekil** kullanıp kullanmadığı ayrıca
sorulmalıdır: *"bu ölçüt, sormak istediğim soruyu mu ölçüyor, yoksa çoğu
zaman ona eşit olan başka bir şeyi mi?"* Vekiller, sınandıkları özel durumda
(burada: küre) tesadüfen doğrudur.
