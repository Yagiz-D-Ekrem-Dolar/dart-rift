# Protokol DY — DART sahnesinin **geç evre modeliyle ilk** koşusu

**Yazıldı:** 2026-09-28, **DY koşusundan ÖNCE**. **Öncül:** KAYIT-064
(U/V: `HİÇBİR VARYANT ULAŞMIYOR`, en iyi `β ≈ 2,05` @ 0,2 s), PROTOKOL-UG
(üretim `t_geçiş = 1,0 s`), KAYIT-070 §3 (**A108** kütle tutarlılığı),
ADR-0050/0052. **Rapor:** `scripts/dy_dart_raporu.py` → `S_DY.json` (kilitli).

---

## 1. Neden

Geç evre modelinin **tamamı kıyas sahnesinde** doğrulandı (W2, UA, UY, UG,
A98–A105: 75 m homojen küre, dik çarpma, tek küre mermi). **Gerçek DART
sahnesi bu modelle hiç koşulmadı.** Bilinmeyenler: kararlılık, maliyet,
geçerlilik denetimleri ve — en önemlisi — `β`'nın nereye düştüğü.

U/V'nin negatif sonucu (`β ≈ 2,05`, gözlem `3,12 ± 0,34`) `0,2 s`'de
kesilmiş koşulardandı; W2 aynı anda `β ≈ 1,95` verip 600 s'de `3,7–4,4`'e
çıktı. **Soru:** aynı şey DART sahnesinde de oluyor mu?

## 2. Tasarım (tek koşu)

| ne | değer | gerekçe |
|---|---|---|
| şekil | elipsoit `88,5 × 87 × 58 m` | Daly ve diğ. 2023 |
| yığın yoğunluğu | **`2376 kg/m³`** | **A108**: bu hacimde `4,3e9 kg`'ı tutturan değer; gözlenen `β` bu kütleyle türetildi |
| mermi | **üç küre** (`%88 + 2 × %6`, `2,215 m` aralık), `579,4 kg`, `6144,9 m/s`, `ρ = 1000 kg/m³` | Daly Tablo 1; üç küre L9 (Owen 2022); yoğunluk L1/L2'nin "eşdeğer kütleli düşük yoğunluklu" pratiği (uzay aracı katı alüminyum değil) |
| çarpma açısı | `17°` (normalden) | Daly Tablo 1 |
| blok modeli | `SAHNE` varsayılanı (`r 14–42 m`, `f = 0,25`) | **A109 kilitli değil**; bu koşu varsayılanı kullanır ve seçimi *bağlamaz* |
| `θ` | `α_b = 1,15`, `Y₀ = 10 Pa`, `f = 0,25` | W2 kıyasıyla aynı `Y₀`; literatürün en iyi bölgesi (`< birkaç Pa – 500 Pa`) |
| merdiven / geçiş / süre | kaba, `t_geçiş = 1,0 s`, `600 s` | UG'nin kilitli üretim değeri |

**Kapsam dışı (bilerek):** çarpma yerinin merkezden `25 m` kaçıklığı
(`--nisan` ile ayrı ayarlanır), gerinim yumuşaması, çekme dayanımı (A105
kararı bekliyor). Bunlar bu koşuda **yok** ve sonuç öyle okunur.

Maliyet kestirimi `W2_Y10_g1p0`'dan (`3:56`) parçacık oranıyla: `~5 GPU-saat`.

## 3. Geçerlilik

`gecerli = True` (sonluluk, enerji `≤ %5`, momentum defteri `≤ 1e-3`,
kurucu sınır) **ve** `t = 600 s`. Değilse genel **OKUNMAZ** ve `β`
raporlanmaz.

## 4. Kilitli yargı

Gözlem bandı `period_interface.dart_beta_budget` ile: **`β = 3,12 ± 0,34`**
(`1σ`). Model tarafında **ölçülmüş** belirsizlikler paydaya girer
(`tarih_esleme.model_eksikligi_kaynakli`): `gerceklem_beta = 0,033`,
`cozunurluk_uzak = 0,004`, `plato = 0,01`, `carpma_yeri = 0,10`
(**`β − 1` üzerinden**, karelerin toplamı). Kesme Pukelsheim `3σ`:

    I = |β_model − 3,12| / √(σ_gözlem² + σ_model²)

| yargı | koşul |
|---|---|
| **MODEL GÖZLEME ULAŞIYOR** | `I < 3` **ve** `β_model ≥ 3,12 − 0,34` |
| **MODEL AŞIYOR** | `I ≥ 3` ve `β_model > 3,12` |
| **MODEL ULAŞMIYOR** | `I ≥ 3` ve `β_model < 3,12` |

> **Bu tek koşu `θ`'yı çıkarmaz.** Yalnız şunu söyler: geç evre modeli DART
> sahnesinde gözlemin *mertebesine* ulaşıyor mu. "Ulaşıyor" çıkarsa U/V'nin
> negatif dalı kapanır ve havuz anlamlı olur; "ulaşmıyor" çıkarsa havuzdan
> önce fizik tartışılır.

## 5. Kapı olmayan tanılar

`β` iki yöntem farkı, `impuls_sekli` (kıyas sahnesiyle **mekanizma**
karşılaştırması), `M_ejekta` (gözlem `1,6 ± 0,3e7 kg`), koni açıları
(**A95**: gözlemle kıyaslanmaz), blok çözünürlüğü, dondurulan sayı,
enerji sapması, duvar süresi, `kutle_tutarliligi`.
