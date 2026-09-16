# KAYIT-059 — Uzman incelemesi, şok kapısının gerçekte ne ölçtüğü, yapay viskozite (2026-09-05 – 09-06)

**Kapsam:** FAZ 4 → Bitiş 3 · **Durum:** GERİYE DÖNÜK yazıldı (2026-09-16) ·
**Kaynak:** [`FAZ4-SIKINTI-RAPORU.md`](../FAZ4-SIKINTI-RAPORU.md) A38–A70 ve
"Uzman incelemesi (2026-09-05)" (satır ~3611–4983); sayılar aynen aktarıldı ·
**Öncül:** [KAYIT-058](KAYIT-058_2026-08-30_geriye-donuk-momentum-defteri-ve-sessiz-basarilar.md)

---

## 0. İki günün özeti

Dış uzman `c94d74e`'yi inceledi; beş bulgusu bağımsız olarak yeniden üretildi ve
**beşi de çıkış kodu 0 veriyordu**. Aynı iki günde: şok kapısının canlı şoku
değil **ezilme artığını** ölçtüğü, **yapay viskozitenin** kazı akışının en güçlü
kontrolü olduğu ve ensemble'a hiç geçmediği, çözünürlük merdiveninin gizli
maliyetinin komşu aramada olduğu bulundu. Kendi yorumlarımı iki kez yanlış, bir
kez doğru düzelttim — hepsi kayıtta.

## 1. Altyapı ve sessiz düşmeler

| kayıt | ne oldu | ölçülen | çare / ders |
|---|---|---|---|
| A38 | A34'ün "işin içinde `git pull`" çaresi, eşzamanlı dizi görevlerinde yarış yarattı | `cannot lock ref`; `\|\| echo` ile **sessizce** eski sürümle devam (`44abe54`) | `flock` ile serileştirme (16.09'da pull tamamen kaldırıldı, bkz. KAYIT-058 §2) |
| A39 | `kolyoz19`: Slurm GPU verdi, sürücü yoktu | `CUDA driver not available`, üç görev `57 s`'de düştü | **tesisat sınavı** `nvidia-smi -L \|\| exit 91` + `kolyoz19` dışlandı; `ortak_bas.sh` doğdu (16.09'da `kolyoz9` için aynı yol) |
| A40 | yeniden gönderilen `L1` `47 s`'de COMPLETED, **hiçbir şey koşmadı** | devam mantığı eski (`3bbc722`, npz'siz) JSONL'i "veri var" saydı | "veri var" ≠ "veri geçerli" |
| A44 | kırmızı test 31.08'den beri push ediliyordu | test kalıbı iki satırı yanlışlıkla kimlik sandı; teşhis döngüm ağacı bozup testi **eski belgeyle** geçirdi | sıkı çapa + `BEKLENEN_GIRIS = 32` sayacı (mutasyonla sınandı) |
| A54 | A44'ün yapısal sebebi: tam takım koşulamıyordu | `gpu` işaretsiz üç test `> 1 saat`; işaretleyince dosya `1,90 s` | "koşulamayan bir kapı, kapı değildir" |
| A55 | zincir betiği yorumunun tersini yapıyordu (`-e` yok diyor, `-e` var) | ara adım düşünce kapı raporu hiç üretilmiyor | toplu kural uygulaması dosyanın gerekçesini okumadan yapılmaz |
| A49 | `nokta_{i:04d}.npz` — `i` her zaman 0 | `L1`'de dilim başına **tek** npz; her nokta öncekini siliyordu | ad `θ`'nın SHA-256 özetini taşır (bugünkü `nokta_0000_e95badc02819.npz` biçimi) |
| A50 | npz tanı için eksikti (güncel `α`, `P`, `S`, `D`, `h` yok) | — | eklendi |
| A64 | `G2`'de 48 noktanın **39'u** düştü, sebep hiçbir yerde yok | `except` dalında koşullu günlükleme; üretim yolu koşulu sağlamıyordu | tek noktalı çağrıda `raise`; sebep `hata` alanına |
| A66 | dizin sayısı gerçeklem sayısı sanıldı | `3 dilim × 2 tohum = 6 dizin, 2 gerçeklem` → `IndexError` | dizinler `sahne<TOHUM>`'dan gruplanır |

## 2. Uzman incelemesi — beş sessiz kusur

| kayıt | kusur | kanıt | sonucu |
|---|---|---|---|
| **A46** | `sahne_taban=None` → `model_class = M0` → **blok yerleştirilmiyor** | iki farklı θ'da `x, m, α₀, Y₀` **birebir aynı**; `α₀` değerleri yalnız `[1,0 ; 1,5]` | **üç eksenin ikisi sahneye hiç ulaşmıyordu**; `K5`, `L1` fiilen tek eksenli; `L1` (6 GPU, 4,5 sa) iptal |
| A47 | raporlanan β (defter, `R`, hedef) ≠ çıkarıma giden β (`2R`, mermi dahil) | sentetikte ikisi de 0 artıkla kapandı ama `1,280871` vs `1,000000`; `2R`'ye 0,2 s'de varmak `410 m/s` ister | `y[0]` artık defterin `beta_hedef`'i |
| A48 | şok kapısı maskesiz → mermi sıkışmasıyla geçilebiliyordu | sınavla gösterildi | mermi maskesi |
| A51 | `Y₀` Tillotson'un **negatif dalını** sınırlamıyor | `Y₀ 1 Pa – 1e8 Pa`: EOS basıncı hep `−1,518635e+07 Pa` | "`1 Pa` matris" hâlâ `−15,19 MPa` çekme taşıyor; Y₀ duyarsızlığının açıklaması (bugün U1/U2 doyumu da bu ailede) |
| A43 | brifingde üretim `Y₀`'ı bellekten yanlış yazdım (`1e7`; doğrusu matris `1e4`, blok `1e7`) | oran `2 000` değil `2 030 000` kat | "parametreyi bellekten yazma, **sahneden oku**" |

## 3. Şok kapısı ne ölçüyor (A45 → A68 → A70)

| adım | bulgu | sayı |
|---|---|---|
| A45 | kapı **son durumda** okunuyordu; şok geçişi `6,0e-5 s` (~11 adım), en erken iz `8,03e-3 s` = **134 ×** geçiş | hiçbir kolda `ρ > ρ₀ᵏᵃᵗⁱ` yok (`ρ_max/2700 ≤ 0,960`); gözenek tavanı `%75,64` > Hugoniot bandı `%45,6 – 74,3` → kapı **salt ezilmeyle** geçilebiliyor |
| ↩ A45 düzeltme | "madde gevşemiyor" yorumu **yanlış** | `%45,34` durumunda `P = 8,33e4 Pa ≈ 0`: gevşemiş ama itecek basınç yok, çekme geri çekiyor |
| A59 | E1a canlı şoku **ilk kez gördü** | zirve `t = 8,61e-05 s` (öngörü `6,0e-05 s`) |
| A68 | çekme kırpılınca madde gerçekten gevşiyor → kapı düzeltmeyi **reddediyor** | `G1` medyan `%21,70` (24/48 geçer), `G2` `%5,38` (**5/48**); geçenler en yüksek `Y₀`'lar → seçme yanlılığı |
| **A70** | kapı artık **koşu boyunca zirveden** (`SOK_PENCERESI = 1e-3 s` her adım) | 10.09 doğrulama: `G2` son-durum kapısı `9/48`, zirve kapısı **`47/48`** → KAPANDI |

## 4. Yapay viskozite ve kazı akışı (A53, A56, A58–A62)

| kayıt | bulgu | sayı |
|---|---|---|
| **A53** | "madde akmıyor" koşusunda `α_av 1,0 → 0,1` akışı **üretiyor** | `M_kaçan` `93,21 → 12 303 kg` (**132 ×**), `⟨v⟩` `−1264 → −0,397 m/s` (**3 188 ×**; uzman `~3168`); taban jet, düşük AV kazı akışı ölçeği |
| **A56** | ensemble `RefParams(cfl=0.25)` ile kuruluyordu → `α_av` hep `1,0`, özete girmiyordu | en güçlü kontrol parametresi tarama dışı | `--alpha-av/--beta-av`, `fizik_ozeti`'ne girer; üretim değişmedi |
| A58 | `av_raporu` "ölçülemedi"yi **"etki yok, aday çıkar"** diye yazdı | `α_av = 0,1` kolu 24 ms'de `⟨v⟩ = nan` | `SONUCSUZ -- Bu 'etki yok' DEMEK DEGIL` dalı |
| A59 | E1 kilitli kuralı "çözücü kusuru" dedi; E3 çürüttü | `α_av 1,0/0,4/0,1` → `ρ_max 2601,6 / 2658,8 / 2891,5`, katı sıkışan `0/0/46` | pozitif denetimsiz olumsuz yargı çözücüyü suçlamaya gidiyor |
| A60 | kazı akışı doğuyor, sonra ölüyor | 24 ms `18 735 kg, −6,70 m/s`; 200 ms `93 kg, −1 264 m/s` jet | "0,2 s platosu **ölü bir plato**ydu" |
| A61 → **A62** | A61: düşük AV sıkışması "kümelenme" (oran `0,575`) → **YANLIŞ**: `E3` orta merdivenle koşmuştu, en ince `0,175 m` | kütleden türetilen aralık `0,1750 m`, oran **`1,150`** → kümelenme yok; A59'un çürütülmesi geri alındı | ölçek **elle** değil **veriden** türetilir (A26, A61, `--kademeler` — üç kez aynı hata) |

## 5. Ölçüm ve istatistik tuzakları

| kayıt | tuzak | sayı / çare |
|---|---|---|
| **A52** | komşu arama yarıçapı `2·h_max` herkese aynı → ince parçacık kaba yarıçapla tarıyor | `N` 7,06 ×, hız **45,3 × yavaş** (aşırı maliyet 6,4 ×); `R3` 224 saat isterdi, iptal. Çare (11–13.09): BVH + sıralı CSR; H200'de orta `336 → 41,4 ms/adım` (**8,13 ×**) |
| A57 | tek tohum hem tasarımı hem sahneyi sürüyordu | Protokol G'nin iki gerçeklemesi farklı θ'lar örneklerdi (`F = nan`); `--sahne-tohum` (bugün U'nun iki tohumu bununla) — koşudan önce yakalandı |
| A63 | `0/0 = ∞` | `G1`'de 48 koşunun 43'ünde `β_hedef = 1,0`; dejenere kolda `F = inf` → "mükemmel ayırt ediyor" diyecekti; `DEJENERE` dalı |
| A65 | "tek yanlı" ölçüsü platoda çalışmadı | posterior sınıra yığılmıyor, yayılıyor; `%68` ucunun önsel sınırına dayanması + `bilgi_orani` |
| A67 | vekil negatif krater derinliği | `d_alt = −0,1523 m`; `d_alt ≥ 0` kısıtı (`R² 0,9432 → 0,9411`), ekstrapolasyon bildirilir |
| **A69** | krater derinliği **mutlak** yakınsamıyor, **θ-tepkisi** dirençli | kaba `0,36`, orta `0,61 m` (%72 fark); `r(Y₀)` `−0,943` vs `−0,925` → "bilgi taşıyor" ayakta, "niceliksel eşleme" düştü (M2 kontrast fikrinin kökü) |

## 6. Ders

Beş sessiz kusurun ve üç yanlış yorumun ortak sorusu: **"bu sayı hangi ölçekte,
hangi zamanda, hangi kümede anlamlı?"** — kapı 0,2 s'de, olay 6e-5 s'de (A45);
kütle değil hız ölçeği (A53); elle değil veriden türetilen aralık (A62); parçacık
sayısı değil komşu sorgusu maliyeti (A52).
