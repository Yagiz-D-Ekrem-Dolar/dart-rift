# Mühürlü ön kayıtlar

Hera verisi **görülmeden önce** üretilmiş, SHA-256'lı ve commit'lenmiş
öngörüler. Bir kayıt buraya girdikten sonra **değiştirilmez**; yanlış
çıkarsa yanlış çıktığı yazılır, kayıt silinmez.

| kayıt | protokol | ne öngörüyor | durum |
|---|---|---|---|
| [`ONKAYIT_HERA_SPIN_uretim96.json`](ONKAYIT_HERA_SPIN_uretim96.json) | [HS](../truba/PROTOKOL-HS-HERA-SPIN.md) | çarpmanın kattığı açısal hız `ω`, ve `ω → f` eşlemesi | **mühürlü**, Hera bekleniyor |

## Doğrulama

Bir kaydın bozulmadığını sınamak için: `sha256` alanını çıkar, geri
kalanı `json.dumps(..., ensure_ascii=False, indent=1, sort_keys=True)`
ile serileştir, SHA-256'sını al. Kayıttaki değerle eşleşmeli.

## Bilinen şerhler

**`ONKAYIT_HERA_SPIN_uretim96`** — kendi gövdesindeki 4. uyarı
*"ADR-0059 çözünürlük açığı kapanmadı; ince koşu yanlılık gösterirse
bu kayıt yeniden üretilmeli"* diyordu.

[KAYIT-085](../defter/KAYIT-085_2026-10-22_cozunurluk-farki-YANLILIK-cikti.md)
(2026-10-22) **yanlılık gösterdi**: 7/7 noktada `b_ince > b_kaba`,
ortanca `%+23,3`, `p = 0,016`. Kayıt **olduğu gibi duruyor** (mühür
budur); ama Hera karşılaştırması yapılırken bu not birlikte okunmalı
ve kayıt yeniden üretilecekse **yeni etiketle** üretilmeli.
