# data_manifest/

Bu dizin, projeye giren **dış veri ürünlerini** kimlik + sağlama toplamıyla
kayda geçirir. Amaç tek: bir sonuç yeniden üretilmek istendiğinde, hangi veri
sürümüyle üretildiği tartışmasız olsun.

## FAZ 3 durumu: DİZİN HÂLÂ BOŞ — verilen söz tutulamadı, saklanmıyor

FAZ 0'da bu dosya "PDS ürün kimlikleri ve checksumları **FAZ 3'te** bu dizine
eklenecektir" diyordu. FAZ 3 bitti ve **eklenemedi**: gerçek PDS ürünleri bu
çalışma ortamında mevcut değil.

Sonucu:

- `scripts/run_g3_gate.py`, C7 kriterini **KANITLANAMADI** işaretler —
  "GEÇTİ" değil. Kapı çıkış kodu 3 döner (kanıtlanabilir kriterler geçti,
  en az biri kanıtlanamadı).
- G3 raporu **KISMİ** verdikt yazar ve eksiği adıyla taşır.

Kanıtlanamayan bir kriteri geçmiş saymak kapının kendisini anlamsızlaştırır
(RULES.txt: başarısız/yapılmamış bir şey için başarı iddia edilmez).

## Bunun FAZ 3'ün geri kalanına etkisi

Yok. FAZ 3'ün ürettiği her şey — şekil-mesh hattı, moloz yığını, settling,
mermi, gözlenebilir çıkarıcılar — **sentetik** girdilerle kuruldu ve cevabı
analitik olarak bilinen sentetik sahnelerde doğrulandı. Gerçek şekil modeli
geldiğinde `setup/shape_mesh.load_obj` yolu hazırdır; değişecek olan
**sayılardır, kod değil**.

Şu an bilinen ve taşınan sınır: FAZ 4'ün nicel sonuçları gerçek Dimorphos
geometrisiyle tekrarlanana kadar "DART senaryosu" değil, "DART benzeri
senaryo" olarak adlandırılmalıdır.

## Gereken ürünler

| ne | kaynak | kullanım |
|---|---|---|
| Dimorphos şekil modeli (OBJ/PLY) | DART/DRACO türetilmiş şekil modeli, PDS Small Bodies Node | `setup/shape_mesh.load_obj` girdisi |
| Didymos şekil modeli | aynı | ikincil cisim bağlamı, yörünge geometrisi |
| DRACO son yaklaşma görüntüleri | PDS SBN, DART bundle | çarpma noktası, yüzey blok istatistiği (P3-FR-03) |
| LICIACube LUKE/LEIA görüntüleri | PDS SBN, LICIACube bundle | ejekta konisi karşılaştırması (`observables/ejecta_catalog`) |
| Yörünge periyodu ölçümü | yayımlanmış DART sonuçları | β doğrulaması (`observables/period_interface`) |

## Şema — JSON (FAZ 0'da YAML yazıyordu, değişti)

`run_g3_gate.py` bu dizindeki `*.json` dosyalarını okur ve **her ürünün** hem
`product_id` hem `sha256` taşımasını arar.

Biçim FAZ 0'daki YAML taslağından JSON'a çevrildi. Gerekçe ölçülmüş bir
tuzaktır: PyYAML (YAML 1.1) `2.67e10` gibi işaretsiz üslü sayıları **string**
olarak ayrıştırıyor ve bu, `configs/p2_basalt.yaml`'ın hiç geçerli olmadığının
aylarca fark edilmemesine yol açtı (ADR-0005). Manifest sağlama toplamı
taşıyor; sessiz tip sürprizi istemiyoruz.

```json
{
  "bundle": "urn:nasa:pds:dart_draco",
  "retrieved_utc": "YYYY-MM-DDTHH:MM:SSZ",
  "retrieved_by": "kim / hangi betik",
  "source_url": "https://...",
  "license": "urun lisansi",
  "products": [
    {
      "product_id": "urn:nasa:pds:...::1.0",
      "filename": "...",
      "sha256": "64 haneli onaltilik",
      "bytes": 0,
      "used_by": "hangi modul / hangi kosu"
    }
  ]
}
```

## Kural

Manifest **indirmeyle aynı anda** yazılır, sonradan değil. Sonradan hesaplanan
sağlama toplamı, dosyanın indirildiği andaki halini değil o an diskte ne varsa
onu kaydeder — ki yakalamaya çalıştığı hata tam olarak budur.
