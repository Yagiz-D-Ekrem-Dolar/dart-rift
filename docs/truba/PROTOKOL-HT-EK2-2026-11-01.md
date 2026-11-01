# PROTOKOL-HT EK-2 — **geç dökümlü** koşu: örtü açılıyor mu?

**Yazıldı:** 2026-11-01, **koşu gönderilmeden ÖNCE.**
**Ana protokol:** [PROTOKOL-HT](PROTOKOL-HT-HERA-TAHMIN.md) ·
**EK-1:** [EK-1](PROTOKOL-HT-EK1-2026-10-28.md) ·
**Mühürlü kayıt:** `docs/onkayit/ONKAYIT_HERA_KRATER_uretim66.json`
(SHA-256 `1b3b811e…`, **bu koşudan önce mühürlendi**)
**İş betiği:** `truba/is_GEC_DOKUM.slurm`

---

## 1. Tek soru

`t = 600 s`'te krater, kaçmamış ejekta tarafından örtülü (KAYIT-090:
eksende `6,50 – 47,99` m, ortanca `30,89` m). **Ejekta düştükten sonra
krater okunabilir hâle geliyor mu?**

Bu, Hera için belirleyici: Hera **son** krateri görecek; mühürlü kayıt
ise *geçici* kraterin kaydı. Cevap "evet" ise ikinci, **ayrı etiketli**
bir ön kayıt kurulabilir. "Hayır" ise `600 s` anlık görüntüsünün sınırı
kesinleşir ve mühürlü kaydın 1. şerhi son söz olur.

## 2. Niçin `t_end = 5000 s`

Balistik tahmin, ölçülen örtü yüksekliğinden:
`g = GM/R² ≈ 4,27e−5 m/s²`, `v_kaçış ≈ 8,2 cm/s`. `600 s`'te `31 m`
yükselmiş malzemenin fırlatma hızı `v₀ = (31 + ½gt²)/t ≈ 6,5 cm/s`;
tepeye çıkış `v₀/g ≈ 1 500 s`, gidiş-dönüş **`≈ 3 000 s`**. `48 m` için
`≈ 4 300 s`. `5 000 s` ikisini de kapsar.

**Maliyet kütükten ölçüldü** (iş `1592569`, nokta 0): erken evre
`dt = 4,4e−6 s` (ilk `1 s` ≈ `227 000` adım), geç evre `dt = 3,8e−3 s`
(`20 000` adım ≈ `75,7 s`). `600 s` toplam `≈ 390 000` adım.
`5 000 s` → `≈ 1 550 000` adım, yani **`≈ 4 kat`**; nokta başına
`~5 → ~20` GPU-saat. İş sınırı `3-00:00:00`, pay geniş.

## 3. Hangi dört nokta — **koşudan önce** seçildi

Ölçüt: **örtü yüksekliği aralığını** kapsamak ve posteriorun kipini
(`Y₀ ≈ 18,7` Pa) içermek. Hepsi `t = 600 s`'te ÖRTÜLÜ reddi alıyor.

| `--dilim` | `Y₀` (Pa) | `α_b` | `f` | örtü (m) | niçin |
|---:|---:|---:|---:|---:|---|
| `16/96` | 1,15 | 1,183 | 0,351 | **10,27** | en ince örtü |
| `20/96` | 6,46 | 1,008 | 0,441 | **30,89** | örtü ortancası |
| `84/96` | 18,57 | 1,209 | 0,167 | **44,95** | **posteriorun kipi** |
| `87/96` | 1,35 | 1,013 | 0,111 | **47,99** | en kalın örtü |

Dört iş, her biri **1 GPU** (kullanıcı 2026-11-01'de 4 GPU serbest
bıraktı). Kuyruğa yığın yok: `--array` ile `%4`.

## 4. Değişen TEK şey `--t-end`

`is_GEC_DOKUM.slurm`'ün `ORTAK` satırı `is_HAVUZ.slurm` ile
**birebir aynıdır**; farklar yalnız:

- `--t-end 5000` (havuz: `600`)
- `--dilim <k>/96` (havuz: `<i>/24`, yani 4 nokta birden)
- `--azami-adim` yükseltilir (`4e7` → `8e7`): `5 000 s` adım bütçesini
  aşmasın. Bu bir fizik ayarı **değil**, tavan.

Başka bir şey değişirse ölçülen şey "geç döküm" olmaz, karışım olur.

## 5. Yargı — **önceden** kilitli

Her nokta için `krater_yuzey` (varsayılan `distan`) ve ADR-0063
`icten` ile okunur; `scripts/havuz_krater_yeniden_oku.py` sınıfları
verir.

| sonuç | yargı |
|---|---|
| `600 s`'te ÖRTÜLÜ, `5 000 s`'te **ÖLÇÜLDÜ** | **ÖRTÜ AÇILDI** |
| iki anda da ÖRTÜLÜ | **ÖRTÜ AÇILMADI** |
| `5 000 s`'te YÜZEY_YOK | **BELİRSİZ** (başka bir kusur) |

**Dört noktanın en az üçünde "ÖRTÜ AÇILDI"** çıkmazsa, geç döküm yolu
krater ön kaydı için **yeterli değildir** ve bu yazılır. Üç/dört eşiği
şimdi, sonuç görülmeden kondu.

Örtü açılan noktalarda `d_merkez` ve `V_krater` ayrıca kaydedilir, ama
**mühürlü kayıt `uretim66` DEĞİŞTİRİLMEZ**: yeni sayı gerekiyorsa yeni
etiketle (`gec_dokum4`) ayrı mühür kurulur. Mühürün anlamı budur.

## 6. Bilinen sınır — kaydın parçası

Geç evre (`--gec-evre-t 1.0 --gec-evre-A 1.0e5`) **düşük ses hızlı bir
vekil malzemedir** (ADR-0050/L1, Raducan & Jutzi 2022): enerji
terimleri `0`, kayma modülü ölçekli. `5 000 s`'e kadar koşmak o vekil
içinde geri birikmeyi izlemek demektir; gerçek granüler oturmanın
**aynısı değildir**. Bu koşu bir **ölçüm aracı sınavıdır** (örtü
açılıyor mu), son kraterin niceliksel öngörüsü değil. Niceliksel
öngörü için ayrıca yakınsama ve malzeme sınavı gerekir ve o
yapılmadı.

## 7. Bütçe ve durdurma

`4 × ~20 = ~80` GPU-saat, duvar süresi `~1 gün`. Herhangi bir iş
`--azami-adim` tavanına çarparsa **sessiz kısa koşu kabul edilmez**:
kütüğe yazılır ve o nokta `BELİRSİZ` sayılır (kural 8).
