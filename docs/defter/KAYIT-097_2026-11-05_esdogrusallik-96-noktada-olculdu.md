# KAYIT-097 — Eşdoğrusallık tasarımın **96 noktasında** ölçüldü

**Tarih:** 2026-11-05 · **Sıfır GPU, sıfır TRUBA** (yalnız depodaki CSV)
**Betik:** `scripts/tani_esdogrusallik_96.py` (kapıları koşudan önce yazılı)
**Öncül:** [KAYIT-079](KAYIT-079_2026-10-16_UP-gozlemli-secimi-ve-n-yon.md)
**Kapsam:** DART/Dimorphos sahnesi; hedefin şekli/kütlesi ve merminin
kütlesi/hızı/açısı **sabit**. İki üretim gözlenebiliri (`β`, `M_ejekta`),
üretim hata korelasyonu.

---

## 1. Niçin

KAYIT-079 gözlenebilir gradyanlarının neredeyse aynı yöne baktığını
**beş köşe noktasında** ölçmüştü. Beş noktalık bir gözlem ile tasarım
boyunca ölçülmüş bir dağılım aynı şey değildir. Bu kayıt aynı hesabı
`96` noktanın hepsinde yapar.

**Bu bir yargı değil.** `n_yön = 1` yargısı PROTOKOL-UP'a göre,
belirlenen noktada, kilitli eşikle verildi (KAYIT-079) ve
**değiştirilmedi**. Eşik (`FISHER_ESIGI = 36`), ölçüt ve yargı tablosu
aynı.

## 2. Kapılar — koşudan önce

| kapı | eşik | ölçülen | sonuç |
|---|---|---|---|
| ortanca gradyan açısı | `< 30°` | **`7,95°`** | **GEÇTİ** |
| `n_yön = 1` oranı | `> %50` | **`%96,9`** | **GEÇTİ** |

## 3. Ölçüm

| | birinci yön | ikinci yön |
|---|---:|---:|
| öz değer ortancası | **`579,5`** | **`1,88`** |
| aralık | `7,7 – 1097,7` | `0,00 – 33,09` |
| eşiği (`36`) geçen | **`93/96`** | **`0/96`** |

`n_yön` dağılımı: `93` noktada `1`, `3` noktada `0`.

`β ~ M_ejekta` gradyan açısı: ortanca `7,95°`, `q10 = 3,05°`,
`q90 = 57,61°`, aralık `0,05° – 88,14°`.

## 4. Bulgu: iki ayrı mekanizma, ve basit hikâye tam değil

Açıyı bantlayınca eşdoğrusallığın mekanizmanın **parçası** olduğu
görülüyor — `r(açı, λ₂) = +0,657`:

| açı bandı | n | `λ₂` ortanca | `λ₂` maks |
|---|---:|---:|---:|
| `0 – 10°` | 54 | `1,02` | `7,23` |
| `10 – 30°` | 29 | `5,41` | `18,66` |
| `30 – 60°` | 5 | `16,15` | `22,23` |
| `60 – 90°` | 8 | `12,84` | **`33,09`** |

**Ama eşdoğrusallık tek açıklama değil.** Gradyanların `60–90°`
ayrıştığı noktalarda bile `λ₂` en fazla `33,09`'a çıkıyor ve eşik `36`
— yani ikinci yön orada da **öğrenilemiyor**. Sebebi yön değil
**büyüklük**: ikinci yönün taşıdığı bilgi ortancada birincinin
`1/300`'ü (`1,88` vs `579,5`).

> Yani *"gözlenebilirler paralel olduğu için ikinci yön çözülmüyor"*
> cümlesi eksik. Doğrusu: **ileri model duyarlılığının neredeyse
> tamamını tek bir yöne yığıyor**; paralellik bunun bir parçası, ama
> ayrıştığı yerde de ikinci yön bilgi olarak zayıf kalıyor.

`n_yön = 0` çıkan üç nokta (`30`, `86`, `89`) birinci yönü de eşiğin
altında: `λ₁ = 20,84 / 17,62 / 7,71`. Orada **hiçbir şey**
öğrenilmiyor.

## 4.1 Öğrenilen yön **hangi eksende?** (aynı koşu, 2026-11-05)

"Bir yön öğreniliyor" yetmez; o yönün **ne olduğu** söylenmeli. Öz
vektör ilk turda kaydedilmemişti; aynı betik, aynı koşu, eklendi.

Birim küp koordinatlarında (yani *önsel aralık başına* duyarlılık —
"ne öğreniyoruz" sorusunun doğru ölçeği). Bileşenin **karesi** o
eksenin öğrenilen yöndeki payıdır, toplam `1`:

| eksen | pay ortanca | `q10` | `q90` |
|---|---:|---:|---:|
| `α_b` (blok gözenekliliği) | `0,001` | `0,000` | `0,328` |
| **`Y₀` (matris dayanımı)** | **`0,999`** | `0,609` | `1,000` |
| `f` (blok hacim kesri) | `0,000` | `0,000` | **`0,045`** |

Baskın eksen sayımı: **`Y₀` → 90/96**, `α_b` → 5, `f` → 1.

Yönün kararlılığı: ortalama yönden sapma ortanca `6,85°`,
`q90 = 35,37°`, maks `75,66°`. Yani yön **çoğunlukla** sabit ama
tasarımın kenarlarında dönüyor.

> **Ölçülen sıralama: `Y₀` ≫ `α_b` ≫ `f`.** Çarpma momentumunun
> taşıdığı bilgi matris dayanımına yığılmış; blok kesri `f`'in payı
> `q90`'da bile `0,045` — **neredeyse hiç görünmüyor**. Gözeneklilik
> `α_b` çoğu yerde görünmüyor ama bazı bölgelerde payı `0,33`'e
> çıkıyor.

**Abartmamak için:** bu `%94` ("90/96") bir ifadedir, "her yerde"
değil. `5` noktada `α_b`, `1` noktada `f` baskın çıkıyor; yön
tasarımın kenarlarında `75°`'ye kadar dönüyor.

Bu, literatürün davranışıyla tutarlı ve onu **açıklıyor**: Raducan ve
diğ. 2024 üç gözlenebilir kullandığı hâlde gözeneklilik ve blok kesri
için aralık bildirdi, tek değer değil. Ölçüm sebebini söylüyor —
momentumun duyarlılığı `Y₀` ekseninde yığılı.

## 5. KAYIT-079 ile çelişmiyor — farklı kurulum

KAYIT-079 §5'in kafesinde `λ₂` `1,67 – 140,53` arasında geziyor ve bazı
`(ρ, θ)` bileşimlerinde eşiği **geçiyor**. O kafes **üçüncü** bir
gözlenebilir (`e_hız`, `σ`'sı taranmış) ve değişken `ρ` içeriyor. Bu
kayıt ise **iki üretim gözlenebiliri** ve **üretim `ρ`'su** ile
ölçüyor. İkisi farklı soruları yanıtlıyor; biri ötekini geçersiz
kılmıyor.

## 6. Genellenebilir olan kısım — ve kapsamı

Genellenebilir ifade Dimorphos hakkında değil, **ileri modelin yapısı**
hakkındadır:

> Bu çarpma probleminde ileri model, duyarlılığının neredeyse tamamını
> `(α_b, Y₀, f)` uzayında **tek bir yöne** yığıyor; ikinci yön
> tasarımın hiçbir noktasında öğrenilebilir eşiğe ulaşmıyor. Ölçüm
> hassasiyetini artırmak bunu değiştirmez — `σ`'yı küçültmek bir
> satırın **ağırlığını** değiştirir, **yönünü** değil (KAYIT-079 §4:
> `σ`'yı `1000` kat küçültmek `λ₂`'yi `2,35 → 4,17` taşıdı). İkinci bir
> yön için **gradyanı gerçekten farklı** bir gözlenebilir gerekir.

**Kapsam:** DART/Dimorphos sahnesinde, iki üretim gözlenebiliri ve
üretim hata korelasyonuyla ölçüldü. İfade bu sahnenin ileri modeli
hakkındadır.

## 7. Kilitli yargılara etkisi — YOK

`n_yön = 1` (KAYIT-079), tarih eşlemesi (KAYIT-080), SBC (KAYIT-081),
çözünürlük yanlılığı (KAYIT-085), iki mühürlü ön kayıt **etkilenmez**.
Hiçbir eşik, ölçüt ya da mühür değişmedi.
