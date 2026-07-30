# ADR-0021: Barnes-Hut ağacı adım içinde yeniden kurulmaz (konum sürümü önbelleği)

- **Durum:** Kabul edildi
- **Tarih:** 2026-07-29
- **Bağlam:** P2-FR-05; FAZ 3 ölçek sınırı
- **İlgili:** [ADR-0018](ADR-0018-cpu-referans-performansi.md)

## Bağlam

`GravitySolver.compute`, Barnes-Hut modunda her `_eval()` çağrısında:

1. `self.x.numpy()` ile tüm konumları GPU'dan CPU'ya kopyalıyor,
2. `build_octree` ile **Python'da özyinelemeli** ağaç kuruyor,
3. dokuz yeni GPU dizisi tahsis edip yüklüyordu.

`step()` içinde `_eval()` **iki kez** çağrılır:

```
kick_v, kick_u, kick_S, [continuity]
drift(dt)          <- konumlar burada degisir
_eval()            <- agac #1 (gerekli)
kick_v             <- yalnizca HIZ degisir
_eval()            <- agac #2: konumlar AYNI -> agac birebir ayni
```

İkinci ağaç, birincisinin birebir aynısıdır.

## Karar

Çözücü bir **konum sürümü** (`_x_version`) taşır; yalnızca `drift` içinde
artar. `GravitySolver` aynı sürüm için önbellekteki GPU dizilerini kullanır
ve hem ağaç kurulumunu hem GPU→CPU kopyasını atlar.

`mode="direct"` etkilenmez (orada ağaç yoktur).

## Doğrulama

Üç ölçekte (N = 4 000 / 12 000 / 30 000) sonuç **bit-eşit**: `x`, `v`, `u`,
`rho`, `S` dizileri tam olarak aynı. Bu beklenen sonuçtur — aynı konumlar,
deterministik ağaç kurulumu, aynı diziler.

## Kazanç hakkında dürüst not

Yerel ölçümde hızlanma **~1,0×** çıktı, yani gürültü içinde kaldı. Sebep:
RTX 3050'de ağaç kurulumu eval maliyetinin yalnızca **%8**'i, dolayısıyla
ikisinden birini atlamak toplamda ~%4 eder.

Kazanç **hızlı GPU'da** ortaya çıkar. H100/H200'de GPU çekirdek işi ~50 kat
hızlıdır ama ağaç kurulumu CPU'da olduğu için **değişmez**; orada ağaç baskın
kalem hâline gelir. Değişiklik bu nedenle korunmuştur: doğruluğu bit
düzeyinde kanıtlı, maliyeti sıfır, faydası hedef donanımda.

## FAZ 3 için açık ölçek sınırı

Bu önbellek ağaç kurulumunu **yarıya** indirir ama ortadan kaldırmaz. Ölçülen
kurulum maliyeti ~`O(N^1,2)`:

| N | ağaç kurulumu |
|---|---|
| 4 000 | 22,6 ms |
| 12 000 | 48,0 ms |
| 30 000 | 187,3 ms |

2 × 10⁶ parçacıkta tek kurulum ~**29 s** eder. Adım başına bir kurulumla
10⁴ adım = ~80 saat, yalnızca ağaç için.

Tam fizikli ölçüm bunu doğruluyor (TRUBA H100, iş 1429628): 832 K parçacıkta
adım **4 837 ms**, oysa yerçekimi kapalı 1 M parçacıkta **287 ms** — ~17 kat.

Dolayısıyla FAZ 3'te öz-yerçekimli DART ölçeği için üç seçenekten biri
gerekir:

1. **Çarpma fazını yerçekimsiz koşmak** — 160 m'lik bir cisimde ilk
   saniyelerde yerçekimi, malzeme dayanımının yanında ihmal edilebilir;
   literatürdeki standart yaklaşım budur.
2. **Ağacı GPU'da kurmak** — determinizmi korumak zorlaşır (ADR-0002).
3. **Ağacı K adımda bir yenilemek** — yaklaşıklık getirir, ayrı bir karar ve
   hata ölçümü gerektirir.

Bu ADR seçeneklerden birini **seçmez**; sınırı ölçülmüş olarak kayda geçirir.

## Sonuçlar

- (+) Adım başına bir gereksiz ağaç kurulumu ve bir GPU→CPU kopyası kalktı.
- (+) Sonuç bit-eşit; hiçbir doğruluk ödünü yok.
- (−) `GravitySolver` artık durum taşıyor (`_cache_version`, `_cache_arrays`).
  Konum sürümünü artırmayı unutmak sessiz bir hataya yol açardı; bu yüzden
  sürüm yalnızca `drift_3d` çağrısının hemen yanında artırılır.
