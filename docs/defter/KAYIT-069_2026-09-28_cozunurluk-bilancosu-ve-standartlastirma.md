# KAYIT-069 — Çözünürlük bilançosu: UY/UG sonuçları, A98–A105 birleştirildi, standartlaştırma kuralı (2026-09-28)

**Kapsam:** çözünürlük + sayısal ayar · **Durum:** iki kilitli sonuç + beş
kilitli sonuç (başka oturum) + birleştirme + yeni kural ·
**Kaynak:** `S_UY.json`, `S_UG.json`, `S_A98.json`, `S_A98K.json`,
`S_A103.json`, `S_A104.json`, `S_A105.json`,
[COZUNURLUK-STANDARDI](../COZUNURLUK-STANDARDI.md), ADR-0051, ADR-0052 ·
**Öncül:** [KAYIT-067](KAYIT-067_2026-09-19_W2-tuttu-UA-yakinsamis-UY-UG.md)

> **KAYIT-068 bu depoda yok.** PROTOKOL-A98 ve A98K onu öncül gösteriyor;
> commit'lerde bulunamadı (A107). Bu kayıt onun yerine geçmez, eksikliği
> kaydeder.

---

## 1. Kilitli yargılar

### UY — **ÇÖZÜNÜRLÜK TERİMİ GEREKLİ** (`β(300 s)`, `Y₀ = 10 Pa`)

| kol | parçacık | `β` |
|---|---|---|
| kaba | 14 616 | 3,686 |
| iç (≤ 12 m ince) | 48 233 | 3,823 |
| orta (48 m içi 2× ince) | 66 601 | 3,978 |

`Δ_orta = 0,098` → üçlü eşiğin ortasında: `0,05 < 0,098 ≤ 0,15`.
İç bölgenin payı `%47` (kapı olmayan tanı).

### UG — **GEÇİŞ YAKINSAMIŞ**, üretim `t_geçiş = 1,0 s`

| `t_geçiş` | 0,2 s | 1,0 s | 2,5 s | 5,0 s |
|---|---|---|---|---|
| `β` | 3,667 | 4,070 | **4,167** | **4,165** |
| L1 oranı | 0,88 | 0,97 | **0,997** | 0,996 |

`Δ(5,0; 2,5) = 0,0007`. Kilitli üretim kuralı `Δ(t; 5,0) ≤ 0,05` olan en
küçük `t` → **1,0 s**.

**Bu, KAYIT-067'deki A97'nin cevabıdır:** W2'nin literatüre `%13–18` uzak
kalması çözünürlükten değil, **geç evreye çok erken geçmekten**geliyormuş.
Doğru geçiş anıyla kaba merdiven literatürü **binde 3** farkla tutuyor.

### Başka oturumların kilitli sonuçları (aynı çalışma alanında koşmuş)

| protokol | yargı | sayı |
|---|---|---|
| **A98** (geç evre AV) | **AV SEBEP DEĞİL** | AV `1 → 0,1`: `β` `−%7,8`; ama kaba–orta farkı `0,098 → 0,147` **büyüdü**. M5: **mermi 800 → 6400 parçacık `β`'yı `+%7,4`** artırıyor |
| **A98K** (kontrollü kazı akışı) | GEÇ AV KÜÇÜLTME BAĞIMLILIĞI KISMEN KALDIRIYOR | `D`: `0,222 → 0,170 → 0,119`; `p = 0,33` (**birinci mertebe değil**) |
| **A103** (dış kuşak) | DIŞ KUŞAK FARKIN AZINI TAŞIYOR | pay `%26`; **TOPLAMSAL DEĞİL** |
| **A104** (keskin çekirdek) | KARIŞIK; YAKINSAMA BAŞLIYOR | aynı `N`, `h/s = 1,5` → `β` `3,686 → 4,023`: **`β`, `N`'ye değil `h`'ye bağlı** |
| **A105** (çekme dayanımı) | BETA ÇEKME DAYANIMINA DUYARLI | `T_m = Y₀/μ_f` açılınca `β` `3,686 → 2,854` (**−%23**) |

## 2. Keşif: bütün çözünürlük ölçümleri tek tabloda (yargı değil)

Kullanıcının önerisiyle bütün koşular alt alta konup formül arandı
(ayrıntı: COZUNURLUK-STANDARDI §1–2).

**Çıkan:** `β(h)` düz bir eğri değil, **doyan** bir eğri. `h ≤ 0,75`'te üç
kol `4,02 ± 0,02`. Güç yasası uydurması `β_∞ = 4,06`, `p = 3,0`
(artık RMS `0,062`).

**İki tuzak ölçüldü:**

1. **Varsayılan `p` ile iki noktalı Richardson** `β_∞ = 5,11` derdi
   (`p = 0,33` varsayımıyla); ölçülen `4,01`. **`%27` fazla.**
2. **Çarpanlar çarpılmaz:** çözünürlük `1,118` × geçiş `1,187` = `1,327`
   → `β = 4,57`. Birlikte ölçülen nokta `4,167`, literatür `4,18`. Çarpım
   ikisini de `%9`'dan fazla aşıyor.

Bu iki ölçüm ADR-0052'nin 4. ve 5. kuralını doğurdu ve kodda **zorlanıyor**
(`carpan_carp` hata verir; ölçülmemiş dönüşüm reddedilir).

## 3. Birleştirme (GitHub)

Başka oturumların **10 commit'i yalnız TRUBA'da** duruyordu (ana ağaç
`detached HEAD`, hiçbir şey `origin`'e gitmemiş). TRUBA'dan GitHub'a doğrudan
gönderim yok (kimlik bilgisi yok), yamalar `xz + base64` ile 10 parçada
taşındı; `all.z` SHA doğrulandı (`12ec6fb4…`), `git am` ile uygulandı.
Tek çakışma `h_orani` yan dalıydı (aynı yere iki ayrı seçenek eklenmiş);
**ikisi de tutuldu**.

İçerik: A98 (AV anahtarı + tanı), **mermi EOS yönlendirmesi düzeltmesi**,
**katı hal güncellemesinden sonra türetilmiş alanların tazelenmesi**, A100
(eşleşik mermi aralığı), A101 (geç evrede düzeltilmiş süreklilik), beş
kilitli protokol + raporları + sınavları.

**Bulunan yeni kusur (A106):** bu raporlar Windows'ta **çöküyordu** —
`write_text(json.dumps(...))` kodlama vermeden yazıyor, K4 yargısındaki `∝`
cp1254'te kodlanamıyor. Yargı doğru hesaplanmış olsa bile rapor
`UnicodeEncodeError` veriyordu (TRUBA utf-8 olduğu için görünmemiş).
Bütün JSON okuma/yazma `encoding="utf-8"`; ekran çıktısı ASCII'ye düşebilir.
**Kilitli yargı metinleri değişmedi.**

## 4. Dürüst değerlendirme

- İyi haber: **doğru geçiş anıyla literatürü tutuyoruz** (`%0,3`). Bu, U/V
  felaketinden bu yana en sağlam sonuç.
- Kötü haber: bunu **kaba merdivende** tutuyoruz ve `h` ekseni tek başına
  `+%11,8` diyor. İkisi birlikte ölçülmedi. Şu an "yakınsadık ve doğruyuz"
  ile "iki hatamız birbirini götürüyor"u **ayırt edemiyoruz**.
- `β`'yı `%23` değiştiren bir modelleme seçimi (matris çekme dayanımı) hâlâ
  kararsız. Bu, çözünürlükten büyük bir belirsizlik.
- Mermi parçacık sayısı (`+%7,4`) yakınsamadı ve hiçbir protokolde
  değişken değildi.

## 5. Sıradaki (tek belirleyici koşu)

**orta merdiven × `t_geçiş = 2,5 s`**, `Y₀ = 10 Pa`, 300 s, `~10–15 GPU-sa`.
`≈ 4,2` → çözünürlük düzeltmesi gereksiz, üretim kaba merdivenle;
`≈ 4,6` → kaba koldaki uyum tesadüf, üretim ayarı yeniden seçilir.
Bu koşu yapılmadan üretim havuzu başlatılmaz (ADR-0052 §4).
