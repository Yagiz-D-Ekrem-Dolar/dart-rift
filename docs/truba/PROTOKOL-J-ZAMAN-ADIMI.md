# Protokol J — sabit `h`'de zaman adımı deneyi (+ I2: `ara` kipinde çözünürlük)

**Yazıldı:** 2026-09-11, **koşudan ÖNCE**. Eşikler `scripts/dt_raporu.py`
içinde kilitli ve sınavlarıyla (`tests/test_dt_raporu.py`) birlikte
commit'lendi. Sonuç geldikten sonra eşik değiştirilmez; değişirse
eski ve yeni yargı ikisi birden yazılır (A45 usulü).

**Kaynak:** uzman yanıtı `DART_RIFT_22_SORU_TEKNIK_YANIT.md`
(2026-09-11), "En kritik yeni bulgu" ve Soru 16.

---

## 1. Neden

Uzman ölçtü, biz doğruladık (rapor A72, `tests/test_akma_kuvvet_ani.py`):

- Gerilme yarım adım ilerletiliyor, kuvvet **geri döndürülmemiş**
  deneme gerilmesiyle hesaplanıyor; akma yüzeyine dönüş adım sonunda.
- Saf kaymada (`G = 2,27e10`, `γ̇ = 1/s`, `Δt = 1e-5`, `Y = 100 Pa`)
  kuvvetin gördüğü eşdeğer gerilme `196 588 Pa` = `Y × 1 966`.
- Fazlalık `≈ (√3/2) G γ̇ Δt`; `Δt` ile **doğrusal** (ölçüldü:
  `Δt/2 → 0,500`, `Δt/4 → 0,250`).
- Deviatorik hız tepkisi aynı oranla (`1 966,1`) büyüyor.

**Sonuç:** kuvvetin gördüğü etkin dayanım `max(Y₀, ~G ε̇ Δt)` gibi
davranabilir. Çarpma bölgesinde `ε̇` büyük olduğundan zayıf matrisler
birbirinden ayırt edilemez hale gelebilir. Bu, G1'deki
*"`Y₀ < 1e5 Pa`'da plato"* ile I'daki *"`x₀` çözünürlükle aşağı
kayıyor"* (`6,340 → 5,950`) sonuçlarını **açıklayabilir**: kaba →
orta geçişi `h`'yi yarıya indirdiğinde `Δt`'yi de yarıya indiriyor.

> Bu henüz bir **hipotez**. Uzman açıkça uyardı: *"`x₀` mutlaka
> bundan" sonucu peşinen yazılmaz.* Protokol J onu sınıyor.

## 2. Tasarım

Ortak: G1/I ile **aynı 24 θ** (tasarım tohumu `20260906`, `--n-lhs 24`),
**iki** sahne gerçeklemesi (`20260906`, `99991111`) → kol başına 48 nokta.
`t_end = 0,024 s`, üretim AV'si (`α = 1,0`, `β = 2,0`).

| seri | çekme | merdiven | kollar | görev |
|---|---|---|---|---|
| **J1** | üretim (G1 koşulu) | kaba (`N = 17 201`) | `{son, ara} × cfl {0,25 ; 0,125 ; 0,0625}` | 36 |
| **J2** | kırpık (G2 koşulu, TANI) | kaba | aynı 6 kol | 36 |
| **I2** | üretim | **orta** (`N = 69 886`) | `ara`, `cfl 0,25` | 12 |

- `cfl` yarılanınca her adımda `Δt` yarılanır (`compute_dt` bütün
  ölçütleri aynı çarpanla ölçekler); `h`, sahne, tohum **aynı**.
- `J1_son_c0250`, G1'in **aynısıdır** → tekrar edilebilirlik ön koşulu.
- `J1_*_c0125`, orta merdivenin `Δt`'sini kaba `h`'de taklit eder:
  I'daki kaymanın ne kadarının `Δt`'den geldiği **doğrudan** okunur.
- `I2`, Protokol I'yı **`ara` kipinde** tekrarlar: `J1_ara_c0250`
  (kaba) ile `I2_ara_c0250` (orta).

## 3. Ön koşullar (biri düşerse ilgili yargı OKUNMAZ)

| # | ön koşul | eşik |
|---|---|---|
| Ö1 | kol başına tamamlanan nokta / 48 | `≥ 0,90` |
| Ö2 | sigmoid geçerli (Protokol I ile aynı) | `R² > 0,85` ve `x₀` veri aralığında |
| Ö3 | `ara` kollarında HER noktada kuvvet anı `q/Y(P)` | `≤ 1 + 1e-9` (aşılırsa uygulama kusurlu, kol OKUNMAZ) |
| Ö4 | `J1_son_c0250` ↔ G1, eşleşen noktalarda krater derinliği bağıl farkı (medyan) | `≤ 1e-9` → **BİT-TEKRAR**; aşarsa `TEKRAR EDİLEMEDİ` yazılır, J içi eşleştirme yine geçerli |

## 4. Yargılar (J1 ve J2 için AYRI ayrı)

Tanımlar: `x₀(kip, cfl)` Protokol I'nın kısıtlı sigmoid uydurması
(`d_alt ≥ 0`), `σ` birini-dışarıda-bırak jackknife; iki kol farkının
sigması `√(σ₁² + σ₂²)`.

### Y1 — `son` kipinde zaman adımı yolu var mı

`Δ_son = x₀(son, 0,0625) − x₀(son, 0,25)`, `kat = |Δ_son| / σ`

| koşul | yargı |
|---|---|
| `kat ≥ 2` ve `Δ_son < 0` | **ZAMAN ADIMI YOLU GÖSTERİLDİ** (I'daki kaymayla aynı yön) |
| `kat ≥ 2` ve `Δ_son > 0` | **ZAMAN ADIMI ETKİLİ, TERS YÖN** (I'daki kaymayı açıklayamaz) |
| `kat < 2` | **Δt YOLU GÖSTERİLEMEDİ** (kayma geometri / ölçüm / arayüzden aranır) |

Ayrıca raporlanır (yargı değil): **açıklanan pay**
`[x₀(son, 0,125) − x₀(son, 0,25)] / (5,950 − 6,340)`.

### Y2 — `ara` kipi Δt bağımlılığını kaldırıyor mu

`Δ_ara = x₀(ara, 0,0625) − x₀(ara, 0,25)`

| koşul | yargı |
|---|---|
| `|Δ_ara|/σ < 2` **ve** `|Δ_ara| ≤ 0,5 |Δ_son|` | **ARA KALDIRIYOR** → enerji / kurucu doğrulamasına geçilir |
| aksi | **ARA KALDIRMIYOR** |

Y1 "gösterilemedi" ise Y2 yazılır ama *"Δt bağımlılığı zaten
gösterilemedi"* notuyla.

### Y3 — mekanizma kontrolü (raporlanır)

- `son` kollarında hedef kütlesinin kuvvet anında akmayı aşan payı
  ve `oran_p99(0,0625) / oran_p99(0,25)` (kusur baskınsa `~0,25`).
- Her kolda `ρ(krater, log Y₀)` ve permütasyon `p` (Protokol G'nin
  `|ρ| > 0,5`, `p < 0,05` eşiği). `ara`'da `Y₀` sinyali kaybolursa
  **"G1'deki `Y₀` sinyalinin bir kısmı Δt yapıtı olabilir"** yazılır.

## 5. I2 yargısı — `ara` kipinde `x₀` çözünürlüğe dayanıklı mı

Protokol I'nın **aynı** kilitli tablosu, `J1_ara_c0250` (kaba) ile
`I2_ara_c0250` (orta) arasında:

| `|Δx₀| / σ` | yargı |
|---|---|
| `< 2` | **DAYANIKLI** |
| `2 – 4` | **ZAYIF** |
| `> 4` | **DAYANIKSIZ** |

Ayrıca `son` kipindeki I sonucu (`2,44σ`, ZAYIF) ile yan yana yazılır.

> **Uzmanın uyarısı kayda geçiyor:** *"2 sigma altında" yakınsama
> kanıtı değildir; hata çubuğu büyüdükçe geçmek kolaylaşır.* I2'nin
> `DAYANIKLI` çıkması `x₀`'ın **yakınsadığını** göstermez; yalnız iki
> çözünürlüğün bu ölçüt altında ayrışmadığını söyler. Yakınsama için
> üçüncü seviye (A52) gerekir.

## 6. Kapsam dışı — bilerek

- **Gözlenebilir:** yargılar mevcut `krater_derinlik` üzerinden
  (G1/I ile eşleşme için). Uzman bu ölçümün yüzey olmadığını gösterdi
  (dış kabuk sabitken `0,49 m`). Yeni yüzey operatörü durum
  dosyalarına **sonradan** uygulanır ve **betimleyici** raporlanır;
  bu protokolün yargısına girmez.
- **Blok üreticisi** (hedef kesre ulaşmıyor, etiketler kabadan
  kopyalanıyor) bu deneyde sabit tutuluyor — J yalnız `Δt`'yi sınıyor.
- **Granüler model** yok; J2'nin çekme kırpması TANI kolu.

## 7. Maliyet

Kaba nokta `~5 dk` (`cfl 0,25`), `~10` / `~20 dk` (`0,125` / `0,0625`);
orta nokta `~1,2 sa`. J1 + J2 `≈ 112` GPU-saat, I2 `≈ 58` GPU-saat.
