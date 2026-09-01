# Anlık görüntüler — ne **garanti ediyor**, ne **etmiyor**

## Doğru terim: **değişiklik algılanabilir**, "değiştirilemez" değil

`MANIFEST.sha256` + `tests/test_anlik_degismez.py` bir görüntünün
**değiştirildiğini yakalar**. Ama depoya tam yetkisi olan biri
kuramsal olarak **üçünü birden** değiştirebilir: dosyayı, manifesti ve
testi. O yüzden sistem *tamper-evident*'tir — *immutable* değil.

> `ANLIK-2026-09-01_momentum-defteri.md` başlığında
> **"Değiştirilemez kayıt"** yazıyor. Bu ifade **fazla güçlü**.
> Düzeltilmedi çünkü o dosya kilitli; deponun kuralı gereği çürüyen
> ifade **silinmez**, burada **geçersiz** işaretlenir.
>
> **Yerine:** *"Değişiklik algılanabilir kayıt."*

Aynı disiplinin kendi mekanizmasına uygulanması bu.

## Daha sert kayıt isteyen milestone'lar için

| katman | ne ekler |
|---|---|
| `MANIFEST.sha256` + test | dosya değişti mi — **depo içinde** |
| **imzalı git etiketi** | commit'i kimin, ne zaman işaretlediği — anahtarla |
| **GitHub Release** | zaman damgası depo dışında, üçüncü tarafta |

Üçü birlikte kullanıldığında tarihsel durum yalnızca depoya değil,
**depo geçmişine ve dışarıya** bağlanır. Bu depoda imzalama için
kullanıcının GPG anahtarı gerekiyor:

```
git tag -s anlik/2026-09-01-momentum-defteri -m "..."
git push origin anlik/2026-09-01-momentum-defteri
```

## Ne zaman yeni görüntü alınır

- Bir yorum **çürüdüğünde** (eski görüntü düzeltilmez, yenisi yazılır)
- Bir kampanya sonuçlandığında
- Yayın/sunum öncesi **dondurulmuş tahmin** için

Her görüntü zorunlu olarak şunları taşır (testle kilitli):
`40` haneli commit SHA · **geçersiz kılınan yorumlar** tablosu ·
koşu kimlikleri.
