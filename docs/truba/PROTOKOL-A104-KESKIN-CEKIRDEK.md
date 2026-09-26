# Protokol A104 — geç `β` `h`'ye mi parçacık sayısına mı bağlı? (keskin çekirdek)

**Yazıldı:** 2026-09-26, **A104 koşularından ÖNCE**.

**Kilitlemeden önce bilinenler:**
- UY, UG;
- PROTOKOL-A98'in üç kolu (`k_av1`, `k_av01`, `k_av0`; orta kol henüz
  bitmedi);
- PROTOKOL-A98K (kontrollü deney) ve PROTOKOL-A103 kilitli sonuçları.

Hiçbir A104 kolu koşulmadı.

**Öncül:** `docs/COZUNURLUK-DENETIMI.md` §8.3.
**Rapor:** `scripts/a104_keskin_cekirdek_raporu.py` → `S_A104.json`
(kilitli). **İş:** `truba/is_A104_keskin_cekirdek.slurm`.

---

## 1. Neden

Güncel teşhis (§8.3):
- UY'deki çözünürlük farkı 3–100 s'deki yavaş geç krater büyümesinde doğuyor.
- Bu akış kontrollü deneyde (A98K) `r₀/h = 8`'de bile yakınsamıyor.
- Merdivenin tek kuşağını inceltmek yetmiyor (A103: bütünsel).
- Geç AV küçültme kısmi etki gösteriyor ve yan etkili (A98, A98K).

Üçüncü bir çözünürlük seviyesi (`ince`, ~530 bin parçacık) orta'nın ~16
katı maliyet (~100 GPU-sa). Daha ucuz bir yol: merdiven her parçacığa
`h = 2s` veriyor. `h/s`'yi `1,5`'e indirmek, aynı parçacık sayısında `h`'yi
`%25` küçültür. Wendland C2 için bu `~160` komşu demek; `≥ 100` önerilir.

**Soru 1 (H1):** Sonuç `h`'ye mi, parçacık sayısına (`N`, aralık `s`) mı
bağlı?
- `h`'ye bağlıysa keskin çekirdek ucuz bir çözünürlük artışıdır. Kaba
  merdiven `h/s = 1,5` ile kaba–orta arasına düşer.
- `N`'ye bağlıysa kabaya yakın kalır.

**Soru 2 (H2):** Orta merdiven `h/s = 1,5` ile koşulursa `h` orta'nın
`0,75`'i olur. Kaba–orta eğimi bu üçüncü noktada yarıya iniyor mu, yani
yakınsama başlıyor mu?

## 2. Tasarım

UY, A98 ve A103 ile **aynı** her şey:
- L1 küresi, `Y₀ = 10 Pa`, `t_geçiş = 0,2 s`, `A_geç = 1e5 Pa`;
- AV `(1, 2)`, dondurma, yerçekimi.

Kod `agac_a104`:
- `SABIT_COMMIT` `b738992` + **yalnız** `h_orani` anahtarı (yerel yan dal
  `a104-taban`, `60d70d9`);
- A99, A100, A101 **yok**; fizik UY ile aynı, tek eksen `h/s`.

| görev | ad | merdiven | `h/s` | `h_rel` (kaba `h`'sine göre) |
|---|---|---|---|---|
| 0 | `A104_k15` | kaba | 1,5 | 0,75 |
| 1 | `A104_o15` | orta (`48:2.8 … 3:0.175`) | 1,5 | 0,375 |

Kıyas kolları (yeniden koşulmaz):
- kaba `A98_k_av1` (`h_rel` 1; R0'da W2 ile aynı);
- orta `UY_orta` (`h_rel` 0,5).

Merminin `h`'si de aynı oranla ölçeklenir (`kendi` kipi).

## 3. Geçerlilik

Her kol `gecerli = True` olmalı ve 300 s'ye ulaşmalı. Değilse o kolun girdiği
yargı OKUNMAZ. Rapor **beklenen dört kolu** sayar.

## 4. Kilitli yargı

`β = β(300 s)` (`beta_aninda`).

**H1 — `h` mi `N` mi (kaba, orta, k15):**
`β_doğrusal = β_kaba + ½ (β_orta − β_kaba)`, yani `h_rel = 0,75`'te
doğrusal aradeğer.

| yargı | koşul |
|---|---|
| **SONUÇ ÖNCELİKLE h'YE BAĞLI** | `|β_k15 − β_doğrusal| ≤ 0,05` |
| **SONUÇ ÖNCELİKLE PARÇACIK SAYISINA BAĞLI** | değilse, `|β_k15 − β_kaba| ≤ 0,05` |
| **KARIŞIK** | ikisi de değil |

**H2 — üçüncü seviye (kaba, orta, o15):**
- `e₁ = (β_orta − β_kaba) / 0,5`
- `e₂ = (β_o15 − β_orta) / 0,125`

`e₂/e₁ ≤ 0,5` → **YAKINSAMA BAŞLIYOR**; `< 1` → **YAVAŞ YAKINSAMA**; değilse
**YAKINSAMA YOK**.

`genel` = H1.

## 5. Dürüst sınırlar

- `h/s` değişince yalnız `h` değişmez: komşu sayısı ve sıfırıncı mertebe
  SPH hatası da değişir. H1 "yalnız `h` önemli" demez; "sonuç öncelikle
  hangisiyle hareket ediyor" der.
- H2 tek bir üçüncü nokta. Mertebe tahmini kaba olur.
- `h/s = 1,5`'in doğruluğu ayrıca sınanmadı: yüzey kusuru ve gürültü
  artabilir. Kol geçersizse OKUNMAZ.
- Hiçbir ayar gözlenen DART `β`'sına göre yapılmaz.

## 6. Maliyet

- **Görev 0:** `n = 14 616`. Komşu `~160` (`~380` yerine), `Δt` `0,75×`.
  Beklenen `~1–2 sa`.
- **Görev 1:** `n = 66 601`. Beklenen `~5–7 sa`.
- Toplam `≤ ~9 GPU-sa`, **2 GPU**, süre sınırı 16 sa.
- Otomatik yeniden gönderim yok.
