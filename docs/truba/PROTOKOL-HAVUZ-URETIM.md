# Protokol HAVUZ — üretim havuzu ve posterior (**havuz koşmadan ÖNCE yazıldı**)

**Yazıldı:** 2026-10-05, **havuz gönderilmeden ÖNCE.**
**Öncül:** KABUL EDİLMİŞ beş karar —
[ADR-0053](../adr/ADR-0053-y0-onseli-ve-tanimlayici-gozlemli.md) (A2),
[ADR-0054](../adr/ADR-0054-c1-gozlenen-beta-hangi-sayi.md) (C1),
[ADR-0055](../adr/ADR-0055-gozlemli-vektoru-ve-krater-kutusu.md) (A114),
[ADR-0056](../adr/ADR-0056-a105-matris-cekme-dayanimi.md) (A105),
[ADR-0057](../adr/ADR-0057-a109-hangi-blok-modeli.md) (A109),
[ADR-0058](../adr/ADR-0058-uretim-posteriorunun-tarifi.md) (posterior tarifi) ·
ölçümler KAYIT-067, 070–074 · **Karar:** KAYIT-075
**Betikler:** `scripts/faz5_ensemble_merdiven.py` (koşu),
`scripts/prova_cikarim.py --vekil gp` (SBC kapısı), `truba/is_HAVUZ.slurm`

---

## 1. Ne soruyoruz

Dimorphos'un iç yapı parametreleri `θ = (α_b, Y₀, f)` için, gerçek DART
gözleminden **kalibre edilmiş** bir posterior. Tek koşu değil; `96` noktalı
bir tasarım, vekil ve posterior.

Bu protokol **sonucu** değil **yöntemi** kilitler. Sonuç gelince kural
değişmez; düzeltme yan yana alan olarak eklenir (kural 6).

## 2. Sahne — DY2 ile **birebir aynı**

Tek değişen `θ`. Geri kalanı KAYIT-072'nin doğruladığı sahne:

| ne | değer | kaynak |
|---|---|---|
| şekil | elipsoit `88,5 × 87 × 58 m` (yarı eksen) | Daly 2023 |
| yığın yoğunluğu | `2306,1 kg/m³` (kalibre: `4,3000e9 kg`) | A108/A111 |
| mermi | **üç küre** (`%88 + 2 × %6`, `2,215 m`), `579,4 kg`, `6144,9 m/s` | Daly T1, L9 |
| çarpma açısı | `17°` (normalden) | Daly T1 |
| nişan | **kutup** (`0 0 1`) | PROTOKOL-DY §9.4: üretim nişanı DN ile **değişmez** |
| matris çekmesi | **KAPALI** (`--matris-cekme-yok`) | **ADR-0056 KABUL** |
| bloklar | **`r ∈ [14 , 56] m`, `q = 3`** — *sayı olarak*, varsayılan türetme kullanılmaz | **ADR-0057 KABUL** (`URETIM_BLOK`) |
| merdiven / geçiş / süre | kaba, `t_geçiş = 1,0 s`, `600 s` | UG, UY2 |
| tohum | `20260906` (sahne), `20260906` (kök) | DY2 ile aynı |

## 3. Tasarım

| ne | değer | gerekçe |
|---|---|---|
| uzay | **`DART_UZAYI_S4`** — `α_b ∈ [1,00 ; 1,30]`, **`Y₀ ∈ [1e0 ; 1e5] Pa`** (log), `f ∈ [0,05 ; 0,50]` | **ADR-0053 KABUL**, §3.1 |
| nokta sayısı | **`96`** (LHS, `root_seed = 20260906`) | bütçe: `96 × ~5 sa ≈ 480 GPU-saat` |
| gözlemli | `β`, `M_ejekta` | ADR-0053 §4.2 |
| `krater_derinlik` | **isteğe bağlı** (`istege_bagli=("krater_derinlik",)`, `nan_izinli=(1,)`) | **ADR-0055 KABUL**; A114 |

### 3.1 `Y₀` önselinin **DO'ya bağlı** kapısı

ADR-0053 §4.4: önsel **DO okunmadan değişmez.** PROTOKOL-DO §5.1'in
kilitli yargısı:

| DO yargısı | havuzun uzayı |
|---|---|
| `ONSEL GOZLEMI ICERMIYOR` | **`DART_UZAYI_S4`** (`Y₀ ∈ [1e0, 1e5]`) |
| `GOZLEM ONSEL KENARINDA` | `DART_UZAYI_S4` (alt kenar yine `1 Pa`) |
| `ONSEL GOZLEMI ICERIYOR` | **`DART_UZAYI_S3`** (`[1e3, 1e7]`) — eski önsel korunur |
| `OKUNMAZ` | havuz **gönderilmez**; DO tekrarlanır |

Bu tablo **DO sonucunu görmeden** yazıldı.

## 4. Geçerlilik ve beklenen sayım (kural 8)

Her nokta için `gecerli = True`, `t = 600 s`, `kutle_tutarliligi ≤ %5`.
Rapor **beklediğini sayar**: `96` nokta bekler, eksikse adıyla söyler.

| kayıp oranı | karar |
|---|---|
| `≤ %5` | havuz okunur, düşenler listelenir |
| `%5 – %20` | okunur ama posterior **"eksik tasarım"** etiketiyle; düşenlerin `θ` dağılımı raporlanır (yanlı kayıp sınanır) |
| `> %20` | **okunmaz.** Sebep bulunur, havuz tekrarlanır |

`krater_derinlik`'in `nan` sayısı ayrı sayılır (A114) ve kayıp sayılmaz.

## 5. Posterior — kilitli tarif (ADR-0058)

1. **Vekil:** gözlemli başına GP (`gp_uydur`) + **Bachoc** varyans
   kalibrasyonu (`gp_varyans_kalibre`, `yalniz_buyut=True`), `θ`-gruplu
   4 kat CV.
2. **Olabilirlik:** `grid_posterior_hetero`, `n_grid = 40`.
   Varyans `= GP öngörü varyansı + σ_gözlem² + σ_model²`.
3. **`R` ÖLÇÜLÜR:** `β` ve `M_ejekta` vekil artıklarının örnek korelasyonu
   (grup-CV artıklarından). **Varsayılmaz** — ADR-0058 §3 ölçtü:
   `ρ` `0 → 0,8` `α_b`'nin daralmasını `0,372 → 0,708` yapıyor.
   `R` ayrıca `ρ = 0` ile **yan yana** raporlanır.
4. **Hedefler:**
   - `β`: `uretim_hedef_beta(M_sahne)` → **`3,5418 (+0,188 / −0,247)`**
     (**ADR-0054 KABUL**). Asimetrik sd; model `β` hedefin üstündeyse
     `+` tarafı kullanılır.
   - `M_ejekta`: `1,6 ± 0,3e7 kg` (L17 Lolachi).
5. **`σ_model` — yalnız ÖLÇÜLMÜŞ terimler** (KAYIT-067/070/072/074):

   | gözlemli | terimler |
   |---|---|
   | `β` | `gerceklem_beta_DART` `0,013` · `cozunurluk_uzak` `0,004` · `cozunurluk_yakin` `0,053` · `plato_olculen_DART` `0,016` · `hedef_sekli_olculen` `0,009` · `carpma_yeri` (DN'den; ölçülemezse L12 `0,10`) |
   | `M_ejekta` | `gerceklem_M_ejekta_DART` `0,129` |

   **Girmeyen:** `mermi_geometrisi` (ADR-0056 mantığı, KAYIT-074 §2),
   `matris_cekme` (ADR-0056 §3), `carpma_acisi` (kapsam dışı).
   Her biri **koşullu duyarlılık** olarak raporlanır, paydaya değil.

## 6. **SBC KAPISI** — posteriorun yayımlanma koşulu

`prova_cikarim.py` mantığıyla, ama **havuzun gerçek vekiliyle**:
`n_sbc ≥ 200`, aynı `R`, aynı `σ`.

| SBC sonucu (her eksen) | karar |
|---|---|
| hepsi `KALİBRE` / `DÜZGÜN` | **posterior yayımlanır** |
| bir eksen `AŞIRI TEMKİNLİ` | yayımlanır, o eksen **"muhafazakâr"** etiketiyle (iddia küçülür, yanlış olmaz) |
| bir eksen **`YANLI`** | **YAYIMLANMAZ.** (a) sırt boyunca `+24` nokta eklenir ve SBC yeniden koşar, ya da (b) tek posterior yerine `tarih_esleme` (Vernon, `I = 3` kesmesi) ile **eleme** raporlanır |
| `DÜZGÜN DEĞİL` (başka) | yayımlanmaz; sebep bulunur |

**Paydayı büyütüp geçmek yasak** (A115 (c)3: yanlılık bir kaymadır,
paydayı büyütmek onu gizler).

## 7. Yanında **zorunlu** raporlar

1. **Tanımlanabilirlik** (ADR-0051): daralma, profil (`Δ = 1,92`),
   Fisher yönleri. **İki gözemliyle en çok iki yön** öğrenilir; bu
   aritmetik ve rapor onu **önceden** söyler.
2. **Kapsam sınırı** (ADR-0057) — raporda **birebir** şu cümle durur:

   > Çıkarılan `(α_b, f)`, Dimorphos'un **`≳ 14 m`** ölçeğindeki **iç**
   > blok topluluğunu tanımlar. Daly ve diğ. 2023'ün ölçtüğü **yüzey**
   > blokları (`0,16 – 6,5 m`) bu çözünürlüğün **altındadır** ve
   > çıkarımın erişiminde **değildir**. İkisi aynı şey diye sunulamaz.
3. **Koşullu duyarlılıklar:** matris çekmesi (`−%23`, DC ölçecek),
   mermi geometrisi (`0,134`, KAYIT-074), nişan (`σ_çarpma_yeri`, DN).
4. **Ejekta ayrışması** (KAYIT-073): `M_kaçan / v_ort / kos_ort` `θ`'nın
   **üç** ekseninde. `α_b` ve `f`'de de götürme var mı — havuz bunu ilk
   kez söyleyecek.

## 8. Bu havuzun **çıkarmayacağı** şey

- **"Üç parametreyi çözdük."** İki gözemliyle en çok iki yön; `f_boulder`'ın
  önsel-baskın çıkması **beklenen** sonuçtur ve kusur değildir.
- **Krater öngörüsü.** `krater_derinlik` havuzda isteğe bağlı ve `nan`
  olabilir; Hera öngörüsü (PROTOKOL-HT) **kendi** turundan gelir
  (ADR-0055 §3, `2c`).
- **Mutlak `Y₀` değeri, SBC geçmeden.** §6 kapısı.

## 9. Maliyet

`96 × ~5 GPU-saat ≈ 480 GPU-saat`. Kalan bütçe `~1100 GPU-saat`
(harcanan `392`), yani bir **tekrar** payı var (§6'nın `+24` noktası
`~120 saat`). 4 GPU ile saf hesap `~5 gün`; ortak kuyrukla `2-3 hafta`.
