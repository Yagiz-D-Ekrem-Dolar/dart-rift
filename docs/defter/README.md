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
