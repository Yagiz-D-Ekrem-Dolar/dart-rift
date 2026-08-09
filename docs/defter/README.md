# Mühendislik defteri — indeks

Her kayıt **ne yapıldığını değil, neyin nasıl anlaşıldığını** anlatır: hangi
soru soruldu, ne ölçüldü, hangi tahmin tuttu, hangisi tutmadı. Sayılar
koşulardan gelir; iş numaraları yazılıdır.

| kayıt | tarih | konu |
|---|---|---|
| [001](KAYIT-001_2026-07-27_FAZ0.md) | 27.07 | FAZ 0 — deterministik altyapı |
| [002](KAYIT-002_2026-07-27_ozdenetim.md) | 27.07 | öz-denetim |
| [003](KAYIT-003_2026-07-27_son_denetim.md) | 27.07 | son denetim |
| [004](KAYIT-004_2026-07-27_FAZ1_FAZ2.md) | 27.07 | FAZ 1 + FAZ 2 |
| [005](KAYIT-005_2026-07-28_kok_neden_turu.md) | 28.07 | kök neden turu |
| [006](KAYIT-006_2026-07-28_sureklilik_yogunlugu.md) | 28.07 | süreklilik yoğunluğu (ADR-0015) |
| [007](KAYIT-007_2026-07-28_G1_G2_gecildi.md) | 28.07 | G1 + G2 geçildi |
| [008](KAYIT-008_2026-07-28_faz012_son_denetim.md) | 28.07 | FAZ 0/1/2 son denetim |
| [009](KAYIT-009_2026-07-28_olcum_denetimi.md) | 28.07 | ölçüm denetimi |
| [010](KAYIT-010_2026-07-28_performans.md) | 28.07 | performans |
| [011](KAYIT-011_2026-07-29_kapanis_denetimi.md) | 29.07 | kapanış denetimi |
| [012](KAYIT-012_2026-07-29_dayaniklilik.md) | 29.07 | dayanıklılık |
| [013](KAYIT-013_2026-07-29_porozite_cozuldu.md) | 29.07 | porozite çözüldü (ADR-0023) |
| [014](KAYIT-014_2026-07-29_faz012_sentez.md) | 29.07 | FAZ 0/1/2 sentez |
| [015](KAYIT-015_2026-08-01_FAZ3.md) | 01.08 | FAZ 3 — sahne kurulumu |
| **[016](KAYIT-016_2026-08-02_hata-ayiklama-turu.md)** | 02.08 | **1. tur** — hasar döngüsü, krater, β (K1–K6) |
| **[018](KAYIT-018_2026-08-03_ikinci-tur-veri-tutarliligi.md)** | 03.08 | **2. tur** — veri tutarlılığı (K7–K12) |
| **[017](KAYIT-017_2026-08-03_ucuncu-tur-olcut-denetimi.md)** | 03.08 | **3. tur** — denetim kodunun kendisi (K13–K20) |
| **[019](KAYIT-019_2026-08-03_FAZ4-baslangic.md)** | 03.08 | **FAZ 4 başlangıç** — kütle oranı toleransı, ilk ölçüm |
| **[020](KAYIT-020_2026-08-04_arayuz-hatasi-nicel.md)** | 04.08 | **FAZ 4.1** — arayüz hatası nicelendi: gürültü tabakası, `0,21·L/h`, %5 düzensizlik 8:1'den kötü |
| **[021](KAYIT-021_2026-08-04_K21-sessiz-nan.md)** | 04.08 | **K21** — Tillotson'da sessiz NaN; hatalı bir ölçümün (S4) açığa çıkardığı gerçek kusur |
| **[022](KAYIT-022_2026-08-04_E1-E2-karar-verisi.md)** | 04.08 | **E1+E2** — model kusursuz kafes (eşdeğer sarsıntı ~0) → arayüz hatası maskelenmiyor; ama 8:1'de **doyuyor** |
| **[023](KAYIT-023_2026-08-04_cozunurlugu-h-belirliyor.md)** | 04.08 | **Çözünürlüğü `h` belirliyor** — sabit `h`'de plato %6,84 uzakta ve kapanmıyor; **A yaklaşımı elendi** |
| **[024](KAYIT-024_2026-08-04_degisken-h-arayuzu-kotulestiriyor.md)** | 04.08 | **Parçacık başına `h` arayüzü kötüleştiriyor** — 3,2–6,5 kat; `Ω` düzeltmesi kurtarmıyor |
| **[025](KAYIT-025_2026-08-04_C-eslemenin-bedeli.md)** | 04.08 | **C'nin bedeli ara değerlemede** — sabit/doğrusal makine sıfırı, karesel `O(h²)`; **korunum ölçülmedi** |
| **[026](KAYIT-026_2026-08-04_E3-sok-arayuzden-gecerken.md)** | 04.08 | **E3: şok arayüzü bedelsiz geçiyor** — 8:1 arayüz, ince koşuyla %0,125 fark; `interface_harmless` |
| **[027](KAYIT-027_2026-08-04_C2-esleme-momentumu-kaybediyor.md)** | 04.08 | **C-2: eşleme momentumu kaybediyor** — `7,5e-03`, **tamamen sistematik** (birikir); A/A′ `1e-16` |
| **[028](KAYIT-028_2026-08-04_D1-kaynak-terimi-model-form.md)** | 04.08 | **D-1: kaynak terimi** — hata biriktirme yarıçapına **duyarsız** (2,4 kat → 1,2 puan); ~%4 taban `h`-sınırlı çıktı |
| **[029](KAYIT-029_2026-08-04_D1b-duzeltme-kaynak-terimi-duyarli.md)** | 04.08 | **DÜZELTME** — KAYIT-028'in "duyarsız" yargısı **dar aralığın artefaktı**; DART bandında model-form **%5–7** |
| **[030](KAYIT-030_2026-08-04_D2-tek-parametreli-kalibrasyon-yetmiyor.md)** | 04.08 | **D-2: kalibrasyon yetmiyor** — şok yarıçapı eşlenirken `KE/E` **%14,5–18,0** ayrışıyor; **A′ öne geçti** |
| **[031](KAYIT-031_2026-08-04_A-prime-tek-izgara-ise-yaramiyor.md)** | 04.08 | **A′-1: tek ızgara yetmiyor** — israf küpsel; 16:1'de A′ her yeri inceltmekten **pahalı** |
| **[032](KAYIT-032_2026-08-04_A-prime-2-cok-seviyeli-izgara.md)** | 04.08 | **A′-2: çok seviyeli ızgara** israfı **tam** kaldırıyor; 16:1'de `9,45×` ucuz |
| **[033](KAYIT-033_2026-08-04_A-prime-3-ince-bolge-orani-belirleyici.md)** | 04.08 | **A′-3: DÜZELTME** — belirleyici olan **ince bölge oranı**; DART rejiminde tek ızgara **yeterli** |
| **[034](KAYIT-034_2026-08-04_A-prime-GPU-dogrulandi.md)** | 04.08 | **A′ GPU'da doğrulandı** — bit uyumu **True**, momentum **8,6e-17**, CPU-GPU çapraz **True** |
| **[035](KAYIT-035_2026-08-08_omega-celiskisi-olculerek-cozuldu.md)** | 08.08 | **`Ω` çelişkisi çözüldü** — `h` sabit ⇒ `Ω ≡ 1`; `N_komşu` `2,06×` salınırken yayılım **%0,607** (ADR-0042) |
| **[036](KAYIT-036_2026-08-08_bosluk3-mukavemette-olculdu.md)** | 08.08 | **Boşluk 3 KISMEN kapandı** — mukavemette taşma **%0,0000**; gözeneklilikte **ölçülemedi** (kutu penceresi yok) |
| **[037](KAYIT-037_2026-08-08_bosluk3-kapandi.md)** | 08.08 | **Boşluk 3 KAPANDI** — gözlenebilir değişti (iletilen momentum); A′ kazancın **%67,1**'ini, tek `h` **%9,1**'ini veriyor |
| **[038](KAYIT-038_2026-08-08_kota-dolunca-kod-yazildi.md)** | 08.08 | **Kota doldu, kod yazıldı** — 4.4–4.7'nin kodu + 136 test; G4 eşikleri **ölçümden önce**; R4 kapandı |
| **[039](KAYIT-039_2026-08-08_dokuz-turluk-hata-ayiklama.md)** | 08.08 | **11 tur hata ayıklama** — 11 kusur, **dördü testleri geçiyordu**; `prior_width` paydası, kenara çakılma, `None` çökmesi, numpy tipleri |
| **[040](KAYIT-040_2026-08-08_ensemble-fizibilitesi-A-prime-ile.md)** | 08.08 | **A′ ensemble'ı mümkün kılıyor** — 1 s için A′ **9,73** GPU-günü, tekdüze ince **66,85**; `~30` günlük bütçeye yalnızca A′ sığıyor |
| **[041](KAYIT-041_2026-08-08_yerel-gpu-ve-mermi-cozulmemis.md)** | 08.08 | **Yerel GPU açıldı** (RTX 3050, yalnızca `2,85×` yavaş) ve **G4-A1 DÜŞTÜ**: mermi `0,215` parçacık/çap, eşik `2,0` |
| **[042](KAYIT-042_2026-08-09_iki-asama-aktarimi-dustu.md)** | 09.08 | **FAZ 4.4 bitti** (6 kol, eşit `t`; `B1`/`B3` geçti) · `t₁ = 4,767e-3 s` ölçüldü · kabalaştırmada korunum `~1e-15` **geçti** ama **atama mesafesi düştü**: `t₁`'in iki şartı **çelişiyor** |
| **[043](KAYIT-043_2026-08-09_lagrange-aktarimi-engeli-kaldirdi.md)** | 09.08 | **Lagrange'cı aktarım engeli kaldırdı**: ısıya dönen `%99,3 → %2,88`, atama mesafesi `4,35 → 0,73` hücre · `λ=19` arayüzü **ölçülemedi** (referans `608³`) · çıkarım hattı ilk kez uçtan uca sınandı |
| **[044](KAYIT-044_2026-08-09_gate-6-7-ve-iki-asama-kuruldu.md)** | 09.08 | **G4'te 6/7 geçti** (B2, B4 eklendi; `A1` tek düşen) · **ADR-0044 KABUL**: çıkarım uzayı `ρ_yığın` ile tutarsızdı, `29/29` nokta düşüyordu · iki aşama **uçtan uca kuruldu** · `WarpSPH1D` continuity yolu hiç çalışmamış |

> 017/018 numaraları kronolojiyle ters: 018 (2. tur) 017'den (3. tur) **önce**
> yaşandı ama sonra yazıldı. Numaralar yazım sırasını, tablo yaşanma sırasını
> gösterir. Kayıt numarası değiştirilmedi — geriye dönük numara değiştirmek,
> daha önce verilen atıfları kırar.

---

## Hata ayıklama kampanyası (2–3 Ağustos 2026)

Üç tur, **20 kusur + 2 süreç hatası + 3 kapsam boşluğu**.

| kaynak | ne içerir |
|---|---|
| [`docs/KUSUR-KAYDI.md`](../KUSUR-KAYDI.md) | **kayıt** — her kusurun tam dökümü, ölçülen sayılarla |
| [`docs/KUSUR-KAYDI-KOD.md`](../KUSUR-KAYDI-KOD.md) | **kod** — önce/sonra, yeniden üretme betikleri, seçilmeyen alternatifler |
| [`docs/YONTEM.md`](../YONTEM.md) | **yöntem** — kusurları bulan üç soru, aktarılabilir hâli |
| [`docs/DURUM-DEGERLENDIRMESI.md`](../DURUM-DEGERLENDIRMESI.md) | **verdikt** — ne kanıtlandı, nerede hâlâ risk var |
| KAYIT-016/017/018 | **anlatı** — nasıl bulundu, hangi tahmin tutmadı |
| ADR-0029…0040 | **kararlar** — neden böyle çözüldü |

### Üç turun ortak dersi

1. **1. tur:** testler *parçaların doğruluğunu* sınıyordu, *bütünün
   davranışını* değil.
2. **2. tur:** aynı büyüklük iki yerde yazılıysa ve biri türetilmiyorsa,
   er geç ayrışır — **"şu an aynı" bir güvence değildir**.
3. **3. tur:** bir kriter "GEÇTİ" diyorsa, **geçme sebebi** ölçülmüş olmalıdır.

Ve hepsinin üstünde: **20 kusurun tamamı kapsanan satırlardaydı** (kapsam
%96,5–100). Ne testler ne kapsama onları bulabilirdi.
