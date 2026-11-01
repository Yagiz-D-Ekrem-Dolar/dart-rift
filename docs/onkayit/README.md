# Mühürlü ön kayıtlar

Hera verisi **görülmeden önce** üretilmiş, SHA-256'lı ve commit'lenmiş
öngörüler. Bir kayıt buraya girdikten sonra **değiştirilmez**; yanlış
çıkarsa yanlış çıktığı yazılır, kayıt silinmez.

| kayıt | protokol | ne öngörüyor | durum |
|---|---|---|---|
| [`ONKAYIT_HERA_SPIN_uretim96.json`](ONKAYIT_HERA_SPIN_uretim96.json) | [HS](../truba/PROTOKOL-HS-HERA-SPIN.md) | çarpmanın kattığı açısal hız `ω`, ve `ω → f` eşlemesi | **mühürlü**, Hera bekleniyor |
| [`ONKAYIT_HERA_KRATER_uretim66.json`](ONKAYIT_HERA_KRATER_uretim66.json) | [HT](../truba/PROTOKOL-HT-HERA-TAHMIN.md) + [EK-1](../truba/PROTOKOL-HT-EK1-2026-10-28.md) | gecici krater `V_krater` ve `d_merkez` (`t = 600 s`), ve `V_krater -> Y0` eslemesi | **muhurlu**, Hera bekleniyor |

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

**`ONKAYIT_HERA_KRATER_uretim66`** — üç şerhi **kendi gövdesinde** taşıyor
ve burada tekrarlanıyor, çünkü kaydın değerinden daha önemli:

1. **Seçilim yanlılığı ölçüldü ve büyük.** Kullanılan 66 noktanın `Y₀`
   ortancası `1 918` Pa, dışlanan 30'un `10,58` Pa — ve posteriorun kipi
   `18,7` Pa. Yani vekil, eğitim desteğinin **~2 dekad dışına**
   ekstrapole ediyor. Sebep KAYIT-090: `t = 600 s`'te zayıf matriste
   krater kaçmamış ejekta tarafından örtülü, yani tam verinin işaret
   ettiği yerde okunamıyor.
2. **Öngörü fiziksel desteğin dışına taşıyor.** `V_krater` örneklerinin
   bir kısmı **negatif** (`q05 = −46,3 m³`); hacim negatif olamaz.
   Kırpılmadı — kırpmak genişliği sahte biçimde daraltırdı. Oran kaydın
   `vekil.V_krater.ornek_destek_disi_orani` alanında.
3. **PROTOKOL-HT §5 aynen geçerli ve artık sayılı:** bu *geçici*
   kraterdir, Hera *son* krateri ölçecek. Eksende kaçmamış ejekta
   `6,50 – 47,99` m, ortanca `30,89` m.

> Bu kayıt **dar değil, geniş** ve bu bilinçli. Dar çıkması başarı değil
> hata işareti olurdu (EK-1 §3). Kaydın işlevi "Hera'nın krateri şu
> olacak" demek değil; **ne kadar bilmediğimizi Hera'dan önce
> kilitlemek**.
