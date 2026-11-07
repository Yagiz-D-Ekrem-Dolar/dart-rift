# İnce koşu — üretim havuzunun yarı aralıkla tekrarı

Üretim havuzu `spacing = 7,0 m` tabanıyla koştu. Bu dizin, **aynı tasarım
noktalarının** `spacing = 3,5 m` ile, yani her yönde iki kat ince
ayrıklaştırmayla tekrarlanmış hâlini taşır. Amaç tek bir soruyu
cevaplamaktır: **çözünürlük değişince `β` ne yapıyor?**

Bu bir ikinci üretim havuzu **değildir**. Tasarımın 96 noktasının hepsi
ince koşulmadı ve koşulması planlanmıyor; nokta başına ~45–60 GPU saati
gerekiyor.

## Dosyalar

| dosya | ne |
|---|---|
| `ince_96.csv` | tamamlanan noktaların ölçülen gözlenebilirleri |
| `ince_kunye.json` | koşuların **ortak** yapılandırması + nokta başına duvar süresi |

`ince_96.csv` sütunları:

| sütun | ne |
|---|---|
| `idx` | tasarım noktasının indisi (`0–95`, kilitli LHS; ADR-0053 S4) |
| `beta` | momentum artırma katsayısı |
| `krater_derinlik_m` | krater derinliği [m]; **boş hücre = `NaN`** |
| `ejekta_kutle_kesri` | kaçan ejekta kütlesinin hedef kütlesine oranı |
| `duvar_s` | o noktanın GPU duvar süresi [s] |

## Durum

Tamamlanan **8** nokta: `11, 33, 44, 45, 57, 58, 62, 74`.
Toplam **373,8 GPU saati** (H100).

`44` numaralı nokta tek başına `216 565 s` (60,2 saat) sürdü — diğerlerinin
yaklaşık `160 000 s`'sine karşılık. Yavaşlığın sebebi geç evrede zaman
adımının düşmesidir; koşu temiz bitti (`n_tamam 1`, `n_dusen 0`).

## Künyeler birebir aynı — ve bu doğrulandı

Sekiz koşunun künyesi `dilim` ve `duvar_s` alanları dışında **birebir
aynıdır**. Bu bir varsayım değil, ölçülmüş bir olgudur: her künyeden o iki
alan çıkarılıp kalanın `sha256`'sı alındığında sekizi de
`e816dbc0e002` veriyor. `ince_kunye.json` o ortak künyeyi ve hash'i
taşır; sekiz ayrı kopya tutmak, sekiz dosyanın sessizce ayrışabileceği
bir durum yaratırdı.

Koşuların kod sürümü: `d96c4ee6f29cd76eb327d360bba34334d0a20837`.

## Okurken dikkat

- **Krater derinlikleri çoğunlukla negatif.** Bu bir işaret hatası değil,
  ölçülmüş bir kusurdur: zayıf matris rejiminde kaçmamış ejekta krateri
  örtüyor ve referans yüzey kraterin tabanının üstünde kalıyor
  ([ADR-0062](../../adr/ADR-0062-ortulu-krater-olculemez-sayi-yerine-red.md)).
  Bu sayılar **krater derinliği olarak kullanılmamalıdır**; buraya
  koşunun ürettiği hâliyle, kırpılmadan yazılmışlardır.
- **`74` numaralı noktanın krateri `NaN`.** Krater çıkarıcısı o noktada
  (haklı olarak) reddetti. ADR-0055 gereği bu, kaydın tamamını
  düşürmez — `beta` ve ejekta kesri geçerlidir.
- **Bu veri `β`'nın mutlak değerini doğrulamaz.** Protokol M'in kilitli
  yargısı hâlâ **YAKINSAMIYOR**: farklar inceldikçe büyüyor. İnce ile
  kaba koşunun karşılaştırılması o protokole ve
  [KAYIT-085](../../defter/KAYIT-085_2026-10-22_cozunurluk-farki-YANLILIK-cikti.md)'e
  aittir; orada çözünürlük farkının saçılma değil **yanlılık** olduğu
  ölçülmüştür (`7/7` nokta aynı yönde, `Y₀`'da `×3,22`, `p = 0,0156`).
  Bu dizin o yargıyı değiştirmez, verisini çoğaltır.

## Kaynak

TRUBA (TÜBİTAK ULAKBİM), `kolyoz-cuda` kuyruğu, NVIDIA H100.
Kampanya dosyaları: `HAVUZ_INCE_g1p0.dilim<idx>_96.{jsonl,ozet.json}`.
Her noktanın parçacık düzeyindeki son durumu (`.durumlar`, nokta başına
~14 MB) kümede kalır; depoya yalnız ölçülen nicelikler alınır.
