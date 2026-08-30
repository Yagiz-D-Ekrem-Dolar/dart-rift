# ÖLÇÜT — TRUBA kampanyası (koşulardan **önce**)

**Tarih:** 2026-08-29 · **Öncül:** A23, A24, A25 · **Ortam:** `kolyoz-cuda`, H100

---

## Neden kampanya

Yerelde (RTX 3050, `4 GB`) her ölçüm saatler sürdü ve bir kez dört iş
aynı kartta yarıştı. TRUBA'da **paralel** koşulabilirler. Ama kaynak
bolluğu ölçüt gevşetmez: her işin yargısı **burada, koşudan önce**
yazılı.

---

## J1 — Şokun **yayılması** hangi bağıl çözünürlüğü ister

Ayrıntılı ölçüt: `OLCUT-yayilma-cozunurlugu.md`. Özet: ortak çekirdek
(`r < 3` -> `0,175`; `3 – 6` -> `0,350`), yalnızca `r > 6 m` değişiyor.

| kol | `6 – 12 m` | `12 – 24 m` | dış `s/r` |
|---|---|---|---|
| A | `0,7` | `1,4` | `0,058` |
| B | `1,4` | `2,8` | `0,117` |
| C | `2,8` | `2,8` | `0,233` |

**Neden en önemli iş:** öz-benzer merdivende oktav maliyeti
`N = 20,7 (r/s)³`. `r/s = 8,6` ile dört oktav `0,7×` üretim bütçesi;
`r/s = 20` ile `9,3×`. **`12,6` kat fark** ve sayı ölçülmemiş.

## J2 — Arayüz şok tüpü: geçirgenlik **eğrisi**

`arayuz_sok_tupu.py`, `κ ∈ {1, 2, 4, 8, 20}` (kütle `1, 8, 64, 512,
8 000`). Sahnesiz, tek değişkenli.

**Yargı:** her `κ` için kaba tarafta `>%1` sıkışan parçacık sayısı.

| beklenen | anlamı |
|---|---|
| `κ = 2` (`8×`) geçer, `κ = 20` (`8 000×`) geçmez | A25 doğrulanır ve **eşik** belirlenir |
| hepsi geçer | tüpte engel yok -> A25'in sebebi kabuk **kalınlığı**, oran değil |
| hiçbiri geçmez | düzenek bozuk (denetim kolu `κ = 1` bunu yakalar) |

`κ = 1` **denetim**: aynı çözünürlük, şok `x > 0`'a ulaşmalı. Ulaşmazsa
düzenek geçersizdir ve öteki kollar okunmaz.

## J3 — A24: `ρ` aktarımı ölçülüyor

İki aşamalı koşu, `λ₁ = 19`, `λ₂ = 8`, `t_end = 6e-3 s`.
Kol A: `ρ` taşınıyor (yeni varsayılan). Kol B: `--rho-tasima-yok`.

**Yargı:** `sok` (t_end) alanındaki `sikisma_max`.
Çare işliyorsa A ≫ B. **A ≈ B ise A24'ün çaresi etkisizdir** ve öyle
yazılır — aktarımın taşıdığı sıkışma aşama-2'de zaten kayboluyordur.

## J4 — **Tam koşu**: merdiven + `t_end = 0,2 s`

Şimdiye kadarki bütün ölçümler `t ≤ 6e-3 s`. Krater ve `β` orada
**ölçülemez**. Bu iş, merdivenle tam süreye gidiyor.

Öz-benzer merdiven (`48:1.25 24:2.5 12:5 6:10 3:20`), tek aşama
(aktarım yok), `t_end = 0,2 s`. Ölçülen `dt = 3,99e-6` ile
`~50 000` adım; H100'de `~13 saat` beklenir.

**Yargı — üç ayrı soru, üçü de yazılı:**

| soru | ölçü | başarı |
|---|---|---|
| şok korunuyor mu | `sok` yargısı `t_end`'de | `KISMI` ya da `SOK_VAR` |
| krater oluşuyor mu | `krater.derinlik_m` | `> 1 m` (bugün `0,09 m`) |
| `β` kımıldıyor mu | `beta` | `> 1,5` (bugün `1,41`) |

**Başarısızlık da bilgidir ve yazılacak:** şok korunup krater
oluşmazsa sıkıntı kazı **mekanizmasındadır** (mukavemet/gözeneklilik),
ayrıklaştırmada değil — ve bu, çıkarım probleminin kapsamını
değiştirir.

> `β > 1,5` bir **hedef değil, eşik**. `3,22`'ye ulaşmak bu işin
> ölçtüğü şey değil; `β`'nın hedeften **beslenmeye başlaması**.

---

## Ortak kural

Her iş `sok_sinavi` yargısını sonuç dosyasında taşıyor (ADR-0049).
`SOK_YOK` ile gelen hiçbir kol fizik sonucu olarak okunmaz.

---

## Gönderildi (2026-08-29)

| iş | JOBID | süre sınırı | ne ölçüyor |
|---|---|---|---|
| **J2** tüp | `1538887` | `8 sa` | geçirgenlik eğrisi, `κ = 1 – 20` |
| **J1** yayılma | `1538888` | `1 gün` | `r/s` eşiği (maliyeti belirleyen sayı) |
| **J3** `ρ` A/B | `1538889` | `12 sa` | A24 çaresi işliyor mu |
| **J4** tam koşu | `1538890` | `2 gün` | krater + `β`, ilk kez `t = 0,2 s`'de merdivenle |

Bölüm `kolyoz-cuda` (`cuda-ui`); `arf` oturum düğümünde **yok** —
ilk gönderim oradan reddedildi ve hedef düzeltildi.

---

## Sıralama kararı (2026-08-31, A28'den sonra)

`J5` `t_end = 6e-3 s`'te koşuyor ve orada **mukavemet elemeleri
anlamsız**: şok basıncı `20,3 GPa`, `Y0` `10 MPa` — `2 034` kat fark,
ve kazı akışı henüz başlamamış. Beş kolun aynı çıkması bunun
doğrulaması (A28).

ADR-0049'un istediği gerçek eleme `t_end = 0,2 s` ister:
`6` kol × `~13 saat` = **`78` GPU-saat**.

> **Karar:** o harcama `K4`'ten **sonra**. `K4` krater üretmiyorsa
> elemelerin hepsi yine boş çıkar ve `78` saat çöpe gider.

`J5`'in `6e-3`'te kalmasının kendi değeri var: **gözeneksiz kolun
çökmesi** (`%28,6 -> %0,518`) ucuza ayrılıyor.

Sıra: `K4` -> (krater varsa) `K5 = elemeler @ 0,2 s` -> ensemble.
