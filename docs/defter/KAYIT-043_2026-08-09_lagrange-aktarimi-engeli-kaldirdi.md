# KAYIT-043 — Lagrange'cı aktarım engeli kaldırdı (2026-08-09)

**Kapsam:** ADR-0043 §7 madde 2–5 · FAZ 4.6 çekirdeği
**Durum:** madde 1, 2, 5 **ölçüldü**; 4'ün geometrik yarısı ölçüldü;
**3 ölçülemedi** (sebebi somut)
**Öncül:** [KAYIT-042](KAYIT-042_2026-08-09_iki-asama-aktarimi-dustu.md)

---

## 1. Ana bulgu: aynı `t₁`, iki aktarım, **zıt** sonuç

KAYIT-042 iki aşamalı aktarımın düştüğünü kaydetmişti: ölçülen
`t₁ = 4,767e-3 s`'de ısıya dönen kinetik `%99,3`, atama mesafesi `4,35`
hücre. Sonuç *"`t₁`'in iki şartı çelişiyor, aralık boş"* idi.

**Çelişki `t₁`'in değil, aktarımın çelişkisiymiş.**

| `t₁` [s] | kip | site | ısıya dönen | atama mesafesi |
|---|---|---|---|---|
| `1e-4` | euler | 2 | %98,2 | 0,97 |
| `1e-4` | **lagrange** | 4 | %97,1 | **0,73** |
| `1e-3` | euler | 2 | %93,2 | 0,97 |
| `1e-3` | **lagrange** | 7 | %85,9 | **0,73** |
| **`4,77e-3`** | euler | 2 | **%99,3** | **4,35** |
| **`4,77e-3`** | **lagrange** | **40** | **%2,88** | **0,73** |
| `1e-2` | euler | 2 | %99,9 | **10,16** |
| `1e-2` | **lagrange** | **210** | **%0,46** | **0,73** |

Korunum her iki kipte de `≤ 3,6e-15` — kütle, momentum, enerji.

### Neden zıt yönlere gidiyorlar

Tek bir olay iki kipi ters etkiliyor: **madde genişliyor.**

- **Euler'ci** hedefler aşama-2'nin `t = 0` kafesinden, yani `r_iç = 3 m`
  içinde **sabit**. Madde oradan çıktıkça aktarım onu geri **ışınlıyor**
  — `t₁ = 1e-2 s`'de `35,6 m` öteden.
- **Lagrange'cı** hedefler `t₁` anındaki **bulutun** üzerine oturuyor.
  Bulut genişledikçe akış `s₂` ölçeğinde giderek daha **düzgün**
  görünüyor, yani ortalamak giderek **daha az** bilgi yok ediyor.

> Korunum bunların **hiçbirini** göremiyordu. Üç yasa da `~1e-15`'te
> tutuyordu — çünkü toplamlar doğruydu. Kusuru bulan şey ADR'nin
> istemediği, sonradan eklenen **atama mesafesi** tanısıydı.

### Bedeli: nötr değil

Aşama-2'nin o bölgede `2` parçacığı olurdu; aktarım `40` (ölçülen `t₁`)
ya da `210` (`1e-2 s`) üretiyor. Toplamın `%0,4`–`%1,9`'u, yani bedel
ihmal edilebilir. Ama **ölçülmedi**: (a) ek parçacıkların aşama-2
kafesiyle **dikişi**, (b) site sayısına **üst sınır** yok.

---

## 2. `λ = 19`'da arayüz — **ölçülemedi**, sebebi somut

`run_solid_interface`'in üçüncü kolu **tekdüze ince** referanstır ve
kenarı `n_coarse · λ`:

| `n_coarse` | `λ` | referans `N` | |
|---|---|---|---|
| 32 | 2 | `64³` = 262 144 | koştu (KAYIT-037) |
| 32 | 6 | `192³` = 7,1 M | 4 GiB'a sığmaz |
| 32 | **19** | **`608³` = 225 M** | **imkânsız** |

Referans kolu olmadan **taşma** ölçülemez — parantezin üst ucu odur.
`faz43f_arayuz_lam_taramasi.py` soruyu **eğilime** çeviriyor, ama
`λ = 19` **ölçülmemiş** kalıyor ve betik bunu her koşuda basıyor.

> Bu bir **sonuç değil, ölçümün sınırı**. ADR-0043 §7 madde 3 açık.

---

## 3. Blok sınırları — geometrik yarısı ölçüldü

| `λ` | `s_ince` | yanlış sınıflanan | `f_blok` sapması |
|---|---|---|---|
| 2 | 3,500 m | %4,73 | **%3,02** |
| 6 | 1,167 m | %5,48 | **%6,45** |

**`λ` arttıkça kötüleşiyor**: ince kafes inceldikçe daha çok parçacık
blok sınırına düşüyor, `7 m`'lik komşudan örnekleme onları çözemiyor.
`f_boulder` çıkarımın üç parametresinden biri. Dinamik etki
**ölçülmedi**.

---

## 4. Çıkarım hattı ilk kez **uçtan uca** sınandı

42 test vardı ama hiçbiri uçtan uca değildi: posterior testleri veriyi
**vekilin kendisinden** üretiyordu. Yeni testlerde veri, vekilin
öğrenemeyeceği bir modelden geliyor.

- `C1` doğru çalışıyor: üç doğrusalsızlık düzeyinin **üçünde de**
  *"gerçek posteriorda mı"* sorusuyla birebir örtüşüyor.
- `ensemble_kos` ilk kez **kuru olmayan** kipte koştu: sürdürme, düşen
  nokta politikası, kesinti → **aynı vekil** (katsayılar birebir).

### Yan bulgu: `q2 > 0,5` **zayıf** bir koruma

| tepki yüzeyi | `q2` | geçiyor mu |
|---|---|---|
| `a³` | 0,9944 | ✔ |
| basamak `a > ½` | 0,6706 | ✔ |
| `1/(0,05+a)` | 0,7812 | ✔ |
| **`sin(4πa)`** | **−0,0262** | **✘** |

İkinci derece vekil şaşırtıcı ölçüde dayanıklı; yalnızca **salınımlı**
bir yüzeyde uyarı veriyor. `β(θ)` fizik gereği salınımlı olmadığından
`guvenilir` pratikte **neredeyse her zaman** geçecek. G4-C buna tek
başına yaslanmamalı — sınır artık **testle** belgeli.

---

## 5. Kendi kusurlarım (bu turda 5 tane)

| # | kusur | nasıl bulundu |
|---|---|---|
| 25 | `refine.py`'de **iki** `N×M×3` bellek bombası (`36,8 GiB`) | `r_iç` taraması patladı |
| 26 | kabalaştırmanın hedef kafesi yanlıştı | **CPU ön uçuşu** |
| 27 | açısal momentum anlamsız paydayla (`%72 870`) | rakam okunamadı |
| 28 | dejenere ölçüm `%0` diye raporlanıyordu | bir an *"hata yok"* diye okudum |
| 29 | test fikstürüm eşiği yuvarlıyordu (`%9,9 → %10,0`) | sınav düştü |
| 32 | yavaşlığın nedenini **ölçmeden** aradım (2 yanlış varsayım) | profil çıkarınca |

> 27 ve 29 aynı sınıf: **fikstür** kusuru, testi *"kod yanlış"* diye
> bağırtıyordu. Bu turda **iki kez**.
>
> 32'de kendi ölçüm betiğim yükün **parçasıydı** — ölçtüğüm yavaşlığa
> ölçüm işlemi de katkı veriyordu.

---

## 6. Durum

| | |
|---|---|
| ADR-0043 madde 1 (`t₁`) | ✔ ölçüldü — `4,767e-3 s` |
| ADR-0043 madde 2 (korunum) | ✔ ölçüldü — `≤ 6e-15` |
| ADR-0043 madde 3 (`λ=19` arayüz) | ✘ **ölçülemedi** (bellek) |
| ADR-0043 madde 4 (blok sınırı) | ◐ geometrik yarısı |
| ADR-0043 madde 5 (Lagrange) | ✔ ölçüldü — engel **kalktı** |
| **ADR-0043 durumu** | **ÖNERİLDİ** — madde 3 yüzünden kilitlenemez |
| G4 kapısı | **GEÇİLEMEDİ** — düşen: `A1` |
