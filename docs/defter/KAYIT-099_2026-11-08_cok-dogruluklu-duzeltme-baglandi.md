# KAYIT-099 — Çok doğruluklu düzeltme **bağlandı**; kaba havuz `β`'yı ortancada `%14` eksik ölçüyor

**Tarih:** 2026-11-08 · **Sıfır GPU** (yalnız depodaki iki CSV)
**Betik:** `scripts/cd_duzeltme.py`
**Modül:** `src/dartrift/inference/cok_dogruluk.py` (Kennedy–O'Hagan AR(1))
**Kapı:** [ADR-0059](../adr/ADR-0059-cok-dogruluklu-vekilin-geri-alinmasi.md) §3.4 — **burada seçilmedi, oradan alındı**
**Öncül:** [KAYIT-085](KAYIT-085_2026-10-22_cozunurluk-farki-YANLILIK-cikti.md), A116

---

## 1. Niçin

ADR-0059 (2026-10-09) üretim posteriorunun **iki yolla** hesaplanmasını
kilitlemişti: `SIGMA` (çözünürlük farkı varyansa katılır) ve `CD` (fark
bir düzeltme olarak taşınır). `cok_dogruluk.py` yazıldı, belgelendi,
sınavları geçti — ve **hiçbir üretim yolundan çağrılmadı.** A116'nın
adlandırdığı kusur sınıfının ta kendisi: *"yazılmış ama bağlanmamış
modül."*

Sonuç olarak ince koşuların **441 GPU saatlik** verisinin tüketicisi
yoktu. Bu kayıt o bağlantıyı kurar.

## 2. Girdi

| katman | taban aralık | nokta |
|---|---|---|
| kaba | `7,0 m` | `96` (üretim havuzu, tamamı) |
| orta (ince) | `3,5 m` | `9` → `11, 20, 33, 44, 45, 57, 58, 62, 74` |

Dokuz nokta, ADR-0059 §3.2'nin **veriye bakılmadan** kilitlediği `12`
noktalık maximin alt kümesinin ilk dokuzudur. Kalan üçü (`78, 87, 92`)
2026-11-07'de kullanıcı kararıyla iptal edildi; tasarım planlandığı gibi
tamamlanmadı ve bu §6'da yazılıdır.

## 3. Ham fark — yanlılık, 9/9

Aynı `θ` noktasında `β_ince − β_kaba`:

| nokta | kaba | ince | fark |
|---:|---:|---:|---:|
| 11 | `1,5828` | `1,7428` | **`+0,1601`** |
| 20 | `5,0402` | `5,7433` | **`+0,7031`** |
| 33 | `3,8793` | `4,8406` | **`+0,9613`** |
| 44 | `1,7278` | `1,7828` | **`+0,0550`** |
| 45 | `2,6439` | `2,9760` | **`+0,3322`** |
| 57 | `3,5236` | `4,6706` | **`+1,1470`** |
| 58 | `2,7578` | `3,2406` | **`+0,4828`** |
| 62 | `2,5577` | `2,7313` | **`+0,1737`** |
| 74 | `5,0155` | `5,7750` | **`+0,7595`** |

**Dokuzunun dokuzu da aynı yönde.** Tek taraflı işaret sınavı
`p = 2⁻⁹ = 0,00195`.

| | değer |
|---|---|
| fark aralığı | `+0,0550 … +1,1470` |
| fark ortancası | `+0,4828` |
| oran `ince/kaba` | `1,032 … 1,326` |
| **oran ortancası** | **`1,139`** |

> **Okunuşu:** üretim havuzu `β`'yı ortancada **`%14` eksik** ölçüyor ve
> bu bir saçılma değil, **kayma**. KAYIT-085 aynı şeyi `7` noktada
> ölçmüştü; `9` noktada ve bağımsız bir hesapla ayakta.

## 4. Düzeltme

Kennedy–O'Hagan AR(1): `y_orta(x) = ρ · f_kaba(x) + δ(x)`.

| | değer |
|---|---|
| `ρ` | **`0,8200`** |
| `ρ` ızgarası | `0,0 … 2,0` |
| uyarı alanı | **boş** |

## 5. KAPI — ADR-0059 §3.4

Dışarıda-bırak-bir, hedef `β_ince`. `SIGMA` yolu ince veriyi hiç
kullanmaz, o yüzden onun öngörüsü kaba GP'nin kendisidir.

| | `E_SIGMA` | `E_CD` |
|---|---:|---:|
| **rms** | **`0,6563`** | **`0,2617`** |

**İyileşme `2,51` kat.** Ve ortalamada değil, **nokta nokta**: dokuz
noktanın dokuzunda da `E_CD < E_SIGMA`.

| kapı | sonuç |
|---|---|
| tasarım iç içe | **GEÇTİ** |
| `ρ` ızgara kenarında değil | **GEÇTİ** |
| ince noktalarda `E_CD < E_SIGMA` | **GEÇTİ** |
| iki yolun kipleri | **ÖLÇÜLMEDİ** — tam posterior gerekir |

## 6. YARGI — ve niçin manşet hâlâ `SIGMA`

> **İlk üç kapı geçti. Dördüncüsü ölçülmedi ve GEÇMİŞ SAYILMADI.**
> ADR-0059 §3.4 *"dördü de geçerse"* diyor. Üçü geçti, dördü değil.
> Manşet **`SIGMA`** kalır; `CD` **"keşif"** etiketiyle ektir.

Eşik düşürülmedi, madde sayısı azaltılmadı. Kapı sonucu görülmeden
yazılmıştı ve öyle uygulandı.

**Tasarım eksiği:** `12` nokta planlanmış, `9`'u koşulmuştur. Maximin
alt kümesinin üç noktası (`78, 87, 92`) iptal edildiği için tasarımın
kenarlarında `δ(x)` ölçülmedi, kestirilecektir. Bu, kapının birinci
maddesini düşürmez (iç içelik sağlanıyor) ama kapsama planlanandan
dardır ve `CD`'nin tasarım kenarlarındaki öngörüsü buna göre okunmalıdır.

## 7. Bu ne demek DEĞİL

- **`CD` doğru cevabı vermez.** Orta katman da yakınsamış değildir;
  PROTOKOL-M yargısı hâlâ **YAKINSAMIYOR** ve farklar inceldikçe
  büyüyor. `CD`'nin verdiği şey *"bir kademe daha ince koşulsaydı ne
  çıkardı"*dır, *"gerçek değer"* değil.
- **`%14` evrensel bir düzeltme katsayısı değildir.** Oran `1,03` ile
  `1,33` arasında geziyor ve `θ`'ya bağlı; `δ(x)` zaten bu yüzden bir
  fonksiyondur, bir sayı değil.
- **A116 tamamen kapanmadı.** Bu modül bağlandı, ama kusurun kendisi
  (`failure`, `validation.adaptive_h_cost`,
  `validation.deposit_calibration`) duruyor.

## 8. Bu kayıt sırasında bulunan YENİ kusur

`tests/test_baglanmamis_modul.py` tam olarak A116 için yazılmıştı ve
`cok_dogruluk`'u **yakalamadı**. Sebebi: sınav *"modül adı `src/` veya
`scripts/` altında kendi dosyası dışında geçiyor mu"* diye bakıyor, ve
`inference/ic_ice_tasarim.py`'nin **3. satırındaki belge cümlesi** bu
şartı sağlıyordu.

Yani **bir cümle, bağlantı sayılıyordu.** A116'nın kendi örneği,
A116'nın çaresi olarak yazılan sınavdan kaçmıştı.

Sınav sıkılaştırılmalı: aranan şey ad geçişi değil, gerçek `import` ya
da çağrı olmalı. `FAZ4-SIKINTI-RAPORU`'na eklenecek.

## 9. Yeniden üretme

```
python scripts/cd_duzeltme.py --cikti docs/sonuclar/cd_duzeltme.json
```

Çıktı: `docs/sonuclar/cd_duzeltme.json` — ham farklar, `ρ`, nokta başına
dışarıda-bırak-bir hataları ve `96` noktanın düzeltilmiş `β`'ları.
