# data_manifest/

PDS (Planetary Data System) ürün kimlikleri ve checksumları **FAZ 3'te** bu
dizine eklenecektir (Dimorphos şekil mesh'i, DART/LICIACube türev ürünleri).

FAZ 0'da bu dizin bilinçli olarak boştur: G0 kapısından önce hiçbir veri
girişi ve hiçbir DART/fizik koşusu yapılamaz (DR-RIFT-P0 §1.3).

Şema (FAZ 3'te doldurulacak):

```yaml
- product_id: <PDS urun kimligi>
  source_url: <resmi arsiv adresi>
  sha256: <indirilen dosyanin saglamasi>
  retrieved_utc: <ISO 8601 zaman damgasi>
  license: <urun lisansi>
```
