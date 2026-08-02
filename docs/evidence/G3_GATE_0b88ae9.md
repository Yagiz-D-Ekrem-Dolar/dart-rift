# G3 kapısı — **TAM GEÇTİ** (7/7)

**Kanıt commit'i:** `0b88ae9`
**Makine:** TRUBA — NVIDIA H100 80GB HBM3
**İş:** SLURM 1446129 · **Tarih:** 2026-08-02
**Ham rapor:** `gate_runs/g3_truba_0b88ae9_1446129/G3_report.md`

---

## Sonuç

| kapı | sonuç | çıkış kodu |
|---|---|---|
| **G3** | **GEÇTİ — 7/7 kriter** | **0** |

**620 test geçti / 0 kaldı**, kapsam **%97,0** (4080 ifade, 121 kapsanmayan).
Kırmızı takım **14/14 temiz**.

> Önceki koşularda G3 **KISMİ** idi, çünkü C7 (PDS veri manifestosu)
> kanıtlanamıyordu. Gerçek PDS ürünleri çekildi ve doğrulandı; **kapı artık
> tam geçiyor ve çıkış kodu 0.**

---

## Kriterler

| # | Kriter | Sonuç | Ölçülen |
|---|---|---|---|
| C1 | Şekil-mesh hattı (P3-FR-01) | **GEÇTİ** | kenar-manifold ✓; hacim hatası %0,217; bölünmeyle %3,38 → %0,217 |
| C2 | Moloz yığını (P3-FR-02/03/04) | **GEÇTİ** | N=8842; yoğunluk sapması %0,210; iç koordinasyon **12,00** (FCC teorik 12); **blok kesri 0,303** (hedef 0,30, doyma yok) |
| C3 | Settling (P3-FR-05, P3-VR-01) | **GEÇTİ** | KE_son/E_bağ = 4,958e-12 (eşik 1e-3); t=0'da maks \|a_SPH\| = **0,0 tam** |
| C4 | Mermi (P3-FR-06/07, P3-VR-02) | **GEÇTİ** | 3 çözünürlük; kütle hatası 5,9e-16; momentum 4,0e-14 |
| C5 | Gözlenebilirler (P3-FR-08, P3-VR-03) | **GEÇTİ** | β geri kazanımı 3,0e-16; momentum defteri 9,0e-13; duyarlılık %7,30 |
| C6 | Determinizm + regresyon | **GEÇTİ** | karma `6d6f1d10eaff64e2…`; farklı tohum farklı sahne ✓ |
| **C7** | **Veri manifestosu (PDS)** | **GEÇTİ** | **10 ürün; kimlik+SHA-256 10/10; arşivin resmi MD5'iyle doğrulanmış 10/10; diskte yeniden hesaplanıp eşleşen 10/10** |

---

## C7 nasıl kapandı

**Paket:** `urn:nasa:pds:dart_shapemodel::1.0` — DART Shapemodel Archive
Bundle (Daly, Barnouin, Ernst, Nair, Espiritu, Waller; NASA PDS, 2023).
DRACO + LICIACube/LUKE görüntülerinden stereofotoklinometri (SPC) ile
türetilmiş şekil modelleri.

İndirilen 10 ürün: Dimorphos v004 global şekil modelleri (19,40 / 9,72 /
4,87 m çözünürlük) + PDS4 etiketleri, Didymos v003 global model, koleksiyon
envanteri, genel bakış belgesi. Toplam ~134 MB.

**Doğrulama üç kademeli:**

1. İndirici SHA-256 ve MD5'i **baytlar diske yazılırken** hesaplar — dosyayı
   sonradan okumaz. Manifest gerçekten indirilen baytların karmasını taşır.
2. Her ürün arşivin **resmi `SUPPORT/CHECKSUM/current.md5`** dosyasına karşı
   doğrulanır. Kendi karmamız "diskte ne var" der; arşivinki "doğru dosya mı"
   — ayrı sorulardır. **10/10 eşleşti.**
3. Kapı, dosyalar makinede varsa SHA-256'ları **yeniden hesaplar** ve
   manifestle karşılaştırır; bayat bir manifest sessizce geçemez.
   **10/10 eşleşti.**

**Veri depoda değildir** (134 MB, `.gitignore`). Depoya giren şey **köken
kaydıdır**: `data_manifest/dart_shapemodel.json`.

### Dış kaynak kontrolü — şekil modeli doğru okundu

| ölçülen | değer | yayımlanan |
|---|---|---|
| Dimorphos eşdeğer yarıçapı | **75,0 m** | ~75 m (Daly ve dig. 2023) |
| eksen boyutları | ~177 × 174 × 116 m | aynı mertebede |
| kenar-manifold | ✓ | — |
| 3 çözünürlüğün hacim yakınsaması | %1 içinde | — |

### ⚠ Birim tuzağı — yakalandı ve kilitlendi

PDS şekil modelleri **kilometre** cinsindendir. Ham sınırlar
±0,09 × ±0,08 × ±0,06 geliyor; metre sayılsaydı cisim **1000 kat** küçük,
kütlesi **1e9 kat** az olurdu ve bütün fizik *hiçbir yerde hata vermeden*
anlamsızlaşırdı.

`load_obj` bu dönüşümü **sessizce yapmaz**: `units="km"` açıkça verilir,
`units` ile `scale` birlikte verilirse reddedilir. `configs/p3_dimorphos.yaml`
`obj_units: km` yazar. `tests/test_pds_shapemodel.py` her iki yönü de sınar —
doğru birimde 75 m, yanlış birimde 1 m'nin altı.

---

## Kırmızı takım — 14/14 TEMİZ

RT12 bu turda **yeniden yazıldı**. Eski hâli `run_g3_gate.py` içinde
"unprovable", README'de "KANITLANAMADI" dizesi arıyordu. C7 gerçekten
kapandıktan sonra o kelime README'de yalnızca tarihsel bir notta kaldı ve
madde **tesadüfen** geçmeye başladı — rastlantıyla geçen bir kırmızı takım
maddesi hiç olmamasından kötüdür.

Yeni hâli **davranışsal**: kapının denetleyicisini üç senaryoda doğrudan
çalıştırır ve üçünün de reddedildiğini doğrular — (a) manifest yok,
(b) sağlamasız ürün, (c) bozuk SHA-256.

---

## FAZ 3 kapanış durumu

Açık kusur **yok**. `xfail` **yok**. Kanıtlanamayan kriter **yok**.

Taşınan tek tasarım kararı: **mermi çözünürlüğü** (ADR-0026). DART mermisini
çapı boyunca 6 parçacıkla çözmek 1,72e9 parçacık ister — fizibil sınırın 153
katı. Bu bir kusur değil, ölçülmüş bir ölçek gerçeğidir ve FAZ 4'ün çarpma
bölgesinde **yerel yüksek çözünürlük** kullanmasını gerektirir. "Gereken
simüle süre" sorusu buna bağlı olduğu için birlikte taşınır.
