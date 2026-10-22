# KAYIT-086 — M ile ince koşu arasındaki "işaret çelişkisi" **çözüldü**: aynı şeyi ölçmüyorlardı

**Tarih:** 2026-10-22 · **Sıfır GPU** (kayıt arkeolojisi)
**Kapattığı:** [ADR-0059](../adr/ADR-0059-cok-dogruluklu-vekilin-geri-alinmasi.md) §2
"çözülmemiş uyuşmazlık", [KAYIT-085](KAYIT-085_2026-10-22_cozunurluk-farki-YANLILIK-cikti.md) §4

---

## 1. Çelişki neydi

ADR-0059 §2 şunu kaydediyordu:

> *"PROTOKOL-M / U0, kaba → orta geçişinde `β` için **`−%13`** ölçtü.
> `cozunurluk_yakin` ise **`%5,3`**. İkisi arasında `~2,5×` fark var.
> Bu uyuşmazlık **çözülmedi**."*

KAYIT-085 buna bir boyut daha ekledi: biz aynı geçişte **`+%15,1`**
ölçtük, yani **işaret de ters**.

## 2. Çözüm: iki ölçüm farklı zamanda ve farklı sahnede

`PROTOKOL-M-YAKINSAMA.md` satır 28 açıkça yazıyor:

```
| süre | t = 24 ms |
```

Ve §78: *"`24 ms` anlık görüntü; zamanda plato Protokol T'de ayrıca
bakılıyor."*

Bizim ince koşu ise **`t_end = 600 s`**'de ölçüyor. Arada **25 000 kat**
zaman var.

### 2.1 Bağımsız teyit: `M_ejekta` büyüklükleri

| | `M_ejekta` |
|---|---:|
| M (24 ms) | **40 110 kg** |
| üretim havuzu (600 s), ortanca | **3,985×10⁶ kg** |

**99 kat** fark. Fırlatı 24 ms'de daha yeni çıkmaya başlamış; 600 s'de
birikmiş. İki sayı aynı niceliğin iki anı bile değil — biri erken
evrenin anlık görüntüsü, diğeri son durum.

### 2.2 Yalnız zaman değil: sahne de başka

| | M (2026-09) | ince koşu (2026-10) |
|---|---|---|
| **süre** | **24 ms** | **600 s** |
| çarpma sahası | **matris** (3 m küresinde blok yok, zorlanmış) | üretim; saha koşullanmamış |
| blok yarıçapı | `1,7 – 6,5` m | **`14 – 56` m** |
| çekme yasası | `--matris-cekme-yok` | üretim (A80 kesmesi) |
| mermi `h` | `kendi` (sabit; `Δt` üç merdivende eşitlensin diye) | üretim ayarı |
| `θ` | 6 belirli nokta | 7 LHS noktası (maximin alt küme) |
| merdiven | kaba `0,35` → orta `0,175` | **aynı** |

Merdiven aynı; **geri kalan her şey farklı.**

## 3. Sonuç

**Ortada bir çelişki yok.** M, `Δt`'yi kasten eşitlenmiş, çarpma sahası
matrise zorlanmış, çekmesiz, küçük bloklu bir sahnede **24 ms**'deki
uzamsal yakınsamayı ölçüyordu — tasarımı gereği *kontrollü* bir
yakınsama deneyi. Bizim ince koşu ise üretim sahnesinde **600 s**'deki
son durumu ölçüyor.

İkisini "aynı geçişin iki ölçümü" sayıp farklarını uyuşmazlık diye
kaydetmek **benim hatamdı** (ADR-0059 §2'yi yazarken ve KAYIT-085 §4'te
tekrarlarken). İki sayı hiçbir zaman karşılaştırılabilir değildi.

> **Dikkat — bu bir iyileştirme değil.** KAYIT-085'in bulgusu
> (`7/7 aynı yön`, `p = 0,0156`, `b` ortancası `%+23,3`) **aynen
> geçerli**. Değişen tek şey, o bulgunun artık eski bir ölçümle
> çeliştiğinin sanılmaması. Yanlılık ölçümü ayakta; `Y₀`'ın mutlak
> değeri hâlâ belirlenemiyor.

## 4. Kendi başına ilginç olan

İki ölçüm çelişmiyor ama birlikte okununca bir şey söylüyor:
çözünürlüğün etkisi **zamana bağlı**. 24 ms'de ince çözünürlük `β−1`'i
**düşürüyor** (`0,743 → 0,642`), 600 s'de **yükseltiyor**
(`×1,23`). Yani erken evrede ve son durumda ters yönde çalışıyor.

Bu bir **hipotez değil gözlem**, ama iki ayrı sahnede yapıldığı için
nedensel yorum **yapılamaz**: sahne farkı mı, zaman farkı mı, yoksa
ikisi mi — ayrıştırılmadı. Ayrıştırmak için aynı sahnede iki zamanda
ölçüm gerekir ve bu yapılmadı.

## 5. Yapılan düzeltmeler

- KAYIT-085 §4 başına bu kaydın notu düşüldü (metin silinmedi).
- ADR-0059 §2'ye yan not eklendi (kural 5/6: ADR metni değişmez).
- `rapor.tex`'teki *Geçerlilik sınırları* kutusunda "çelişki açıktır ve
  kapatılmamıştır" cümlesi **yanlış** hâle geldi; düzeltildi.
