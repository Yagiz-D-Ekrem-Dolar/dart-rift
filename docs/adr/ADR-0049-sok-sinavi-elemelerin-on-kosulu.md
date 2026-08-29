# ADR-0049 — Şok sınavı, fizik elemelerinin **ön koşuludur**

**Durum:** ÖNERİ (karar kullanıcıda) · **Tarih:** 2026-08-29
**Öncül:** rapor A22, A23 · **Araç:** `scripts/sok_sinavi.py`

---

## 1. Bağlam — dört kez aynı hata

Bu depoda dört kez şu yapıldı: **bir şeyin etkisiz olduğu, o şeyin
etki edeceği fiziğin hiç oluşmadığı bir koşuda ölçüldü.**

| eleme | koşulduğu `λ₂` | `s` | o `s`'de sıkışma |
|---|---|---|---|
| hasar (Grady-Kipp) | `2` | `3,500` | `%0,006` |
| matris `Y0` | `2` | `3,500` | `%0,006` |
| blok `Y0` | `2` | `3,500` | `%0,006` |
| gözeneklilik (P-α) | `6 – 8` | `1,17 – 0,875` | `≤ %1,68` |
| yerçekimi | `2` | `3,500` | `%0,006` |

A23'e göre şok `s ≤ 0,175 m`'de kuruluyor. **Yukarıdakilerin hiçbiri
o rejimde koşulmadı.** Hepsi, şoku olmayan bir çarpmada şok
sonrasının malzeme tepkisini aradı.

KAYIT-053 bunu bir kez fark edip *"bütün elemelerim geçersiz
olabilir"* dedi ve hasarı `μ ≈ 1`'de yeniden koştu. Ama `μ` (kütle
oranı) **yanlış ölçüydü**: `μ ≈ 1` `λ₂ = 8` demek ve orada sıkışma
hâlâ `%1,68`. Doğru ölçü `μ` değil, **sıkışma**.

## 2. Karar (önerilen)

> Hiçbir fizik elemesi, **aynı koşuda** şok sınavı `KISMI` ya da
> `SOK_VAR` vermedikçe geçerli sayılmaz.

Yani her eleme koşusu `rho`, `u`, `m`, `alpha0` kaydeder; rapor
`sikisma_max` ve yargıyı **sonucun yanında** taşır. `SOK_YOK` ile
gelen bir *"etkisiz"* sonucu **eleme değildir** — yalnızca *"o
çözünürlükte ölçülemedi"*tir ve öyle yazılır.

## 3. Neden `β` ya da `μ` değil

| ölçü | doğru cevabı biliyor muyuz | ne oldu |
|---|---|---|
| `β` yakınsaması | hayır (modelin kendi çıktısı) | `λ₂` `%5` oynattı, *"geçti"* dedi; **aynı** düğme iç enerjiyi `450×` değiştirdi |
| `μ ≈ 1` | hayır (dolaylı) | `λ₂ = 8`'i yeterli gösterdi; sıkışma `%1,68` |
| **sıkışma** | **evet — Rankine-Hugoniot** | eşiği `s ≤ 0,175 m` diye **sayıyla** verdi |

Şok sınavının farkı: hedef sayı **dışarıdan** geliyor. Model onu
kendi lehine kaydıramaz.

## 4. Sonuçları

- **Geçmiş elemeler geçersiz** — silinmiyor (depo kuralı), *"şok
  yokken ölçüldü"* damgasıyla duruyorlar ve yeniden koşulacaklar.
- Yeniden koşma **ucuz değil ama olanaksız da değil**: A23'ün üç
  seviyeli şeması nokta başına `~56 dakika` (H100).
- `sok_sinavi.py` koşu sonrası değil, **koşu betiğinin içinde**
  çalışmalı ki sonuç dosyası yargıyı kendisi taşısın.

## 5. Maliyeti ve reddedilen seçenek

*"Ucuz çözünürlükte tara, sonra bir kez ince koş"* denebilirdi.
**Reddedildi:** A23 sıkışmanın `s` ile `~4.` kuvvetten değiştiğini
ölçtü; ucuz rejimdeki sıralama ince rejimde korunacak diye bir
neden yok ve bu tam olarak dört kez düşülen tuzak.

## 6. Bu ADR neyi **çözmüyor**

Şok sınavını geçen bir koşunun `β = 3,22` vereceğini söylemiyor.
Yalnızca şunu söylüyor: **geçmeyen bir koşunun `β`'sı hakkında
konuşulamaz.**
