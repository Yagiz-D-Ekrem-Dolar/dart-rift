# data_manifest/

Bu dizin, projeye giren **dış veri ürünlerini** kimlik + sağlama toplamıyla
kayda geçirir. Amaç tek: bir sonuç yeniden üretilmek istendiğinde, hangi veri
sürümüyle üretildiği tartışmasız olsun.

## Durum: DOLU — G3 C7 kanıtlandı

| alan | değer |
|---|---|
| **paket (LID)** | `urn:nasa:pds:dart_shapemodel::1.0` |
| **manifest** | [`dart_shapemodel.json`](dart_shapemodel.json) — 10 ürün |
| **doğrulama** | 10/10 ürün arşivin **resmi MD5**'iyle eşleşti |
| **kaynak** | NASA PDS Small Bodies Node (açık veri) |
| **atıf** | Daly, T., Barnouin, O., Ernst, C., Nair, H., Espiritu, R., Waller, D., *DART Shapemodel Archive Bundle*, `urn:nasa:pds:dart_shapemodel::1.0`, NASA Planetary Data System, 2023. |

İndirilen ürünler: Dimorphos v004 global şekil modelleri (19,40 / 9,72 /
4,87 m çözünürlük) + PDS4 etiketleri, Didymos v003 global model, koleksiyon
envanteri ve genel bakış belgesi.

> **FAZ 0'da verilen söz tutuldu.** O zaman "PDS ürün kimlikleri ve
> checksumları FAZ 3'te bu dizine eklenecektir" yazılmıştı. FAZ 3 sonunda
> henüz eklenememişti ve bu açıkça KANITLANAMADI olarak kaydedilmişti;
> sonrasında veri çekildi ve söz tamamlandı.

## Veri depoda DEĞİLDİR

Ürünler 130+ MB; `.gitignore` `data/` dizinini dışlar. Depoya giren şey
**köken kaydıdır** — ürün kimliği, SHA-256, arşivin resmi MD5'i, kaynak adres.
Veriyi çekmek için:

```bash
python scripts/fetch_pds_shapemodel.py --url-file urls.txt --out data/pds --yes
```

Betik, SHA-256 ve MD5'i **baytlar diske yazılırken** hesaplar ve indirilen her
dosyayı arşivin `SUPPORT/CHECKSUM/current.md5` dosyasına karşı doğrular. Bir
uyuşmazlıkta hata verip çıkar.

## Kapının C7 denetimi üç kademelidir

`scripts/run_g3_gate.py`:

1. Manifest var mı, her ürün **kimlik + SHA-256** taşıyor mu?
2. Her ürün **arşivin resmi MD5**'iyle doğrulanmış mı (`md5_verified`)?
   Kendi karmamız "diskte ne var" der; arşivinki "doğru dosya mı" — ayrı sorular.
3. Dosyalar bu makinede varsa **SHA-256'ları yeniden hesaplanır** ve
   manifestle karşılaştırılır. Bayat bir manifestin sessizce geçmesi böylece
   engellenir.

Veri dizini `DARTRIFT_PDS_DIR` ile ya da manifestteki `data_root` ile bulunur.

## ⚠ BİRİM: PDS şekil modelleri KİLOMETRE cinsindendir

Ölçüldü: ham `dimorphos_g_*_v004.obj` sınırları ±0,09 × ±0,08 × ±0,06.
Kilometre kabul edilince eşdeğer yarıçap **75,0 m** çıkıyor — Daly ve diğerleri
(2023) tarafından yayımlanan Dimorphos yarıçapıyla birebir.

Metre saymak cismi **1000 kat** küçültür, kütlesini **1e9 kat** azaltır ve
bütün fiziği *hiçbir yerde hata vermeden* anlamsızlaştırır. Bu yüzden
`load_obj` dönüşümü **sessizce yapmaz**: `units="km"` açıkça verilmelidir ve
`configs/p3_dimorphos.yaml` bunu `obj_units: km` ile yazar.

`tests/test_pds_shapemodel.py` her iki yönü de sınar — doğru birimde 75 m,
yanlış birimde 1 m'nin altı.

## Şema

`run_g3_gate.py` bu dizindeki `*.json` dosyalarını okur:

```json
{
  "bundle": "urn:nasa:pds:dart_shapemodel::1.0",
  "retrieved_utc": "...", "retrieved_by": "...", "source_url": "...",
  "license": "...", "citation": "...",
  "data_root": "data/pds",
  "products": [
    {
      "product_id": "...", "filename": "...", "source_url": "...",
      "sha256": "...", "md5": "...", "md5_official": "...",
      "md5_verified": true, "bytes": 0, "used_by": "..."
    }
  ]
}
```

`filename` **taşınabilir** (yalnızca dosya adı): manifest depoya girer ve
başka makinede de okunur; mutlak yol yazmak onu üretildiği makineye bağlardı.

## Kural

Manifest **indirmeyle aynı anda** yazılır, sonradan değil. Sonradan hesaplanan
sağlama toplamı, dosyanın indirildiği andaki halini değil o an diskte ne varsa
onu kaydeder — ki yakalamaya çalıştığı hata tam olarak budur.
