# Gereken PDS ürünleri — belirlendi, henüz indirilmedi

> **Bu bir manifest DEĞİLDİR.** Manifest, indirilmiş ürünlerin kimliklerini ve
> sağlama toplamlarını taşır ve `*.json` olarak yazılır. Bu dosya yalnızca
> **neyin gerektiğini** kaydeder. G3 kriter C7 hâlâ **KANITLANAMADI**
> durumundadır; kapı `*.json` arar ve bu dosyayı saymaz.

## Belirlenen paket

| alan | değer |
|---|---|
| **LID** | `urn:nasa:pds:dart_shapemodel::1.0` |
| **ad** | DART Shapemodel Archive Bundle, Version 1.0 |
| **iniş sayfası** | https://pds-smallbodies.astro.umd.edu/holdings/pds4-dart_shapemodel-v1.0/SUPPORT/dataset.shtml |
| **içerik** | DRACO + LICIACube/LUKE görüntülerinden stereofotoklinometri (SPC) ile türetilmiş şekil, topografya ve geometri ürünleri |
| **atıf** | Daly, T., Barnouin, O., Ernst, C., Nair, H., Espiritu, R., Waller, D., *DART Shapemodel Archive Bundle*, urn:nasa:pds:dart_shapemodel::1.0, NASA Planetary Data System, 2023. |

Bu paket, C7'nin istediği **Dimorphos ve Didymos şekil modellerini** içeren
doğru kaynaktır. FAZ 4'te `setup/shape_mesh.load_obj` (test edilmiş yol) ile
okunacak ve `configs/p3_scene.yaml` içinde `target.shape: obj` yapılacaktır.

## Erişilebilirlik — ölçüldü

TRUBA giriş düğümünden PDS-SBN'e **erişim var** (HTTP 200, 2026-08-01).
Yani indirme teknik olarak mümkündür; yapılmamış olmasının sebebi teknik
değildir.

## İndirme yolu hazır

`scripts/fetch_pds_shapemodel.py` yazıldı. Özellikleri:

- **Varsayılan olarak hiçbir şey indirmez** — `--yes` verilmeden yalnızca
  hedef adresleri listeler ve boyutlarını raporlar.
- SHA-256'yı **akış halinde**, baytlar diske yazılırken hesaplar. Böylece
  manifest, gerçekten indirilen baytların karmasını taşır — `README.md`'deki
  "manifest indirmeyle aynı anda yazılır" kuralının uygulaması budur.
- Manifesti `data_manifest/dart_shapemodel.json` olarak, kapının beklediği
  şemada yazar.

```bash
python scripts/fetch_pds_shapemodel.py --url-file urls.txt --out data/pds --yes
```

## Neden hâlâ indirilmedi

Dış kaynaktan dosya indirmek, bu ortamda **açık onay gerektiren** bir
işlemdir. Paket kimliği, kaynağı ve indirme yolu hazır; eksik olan tek şey o
onaydır. Onay geldiğinde C7 tek komutla kapanır.
