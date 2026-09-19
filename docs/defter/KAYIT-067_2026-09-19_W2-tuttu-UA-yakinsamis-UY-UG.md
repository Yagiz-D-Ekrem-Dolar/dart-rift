# KAYIT-067 — W2: KIYAS TUTTU · UA: UZAK ALAN YAKINSAMIŞ · U/V'nin sebebi görüldü · UY/UG gönderildi (2026-09-19)

**Kapsam:** kıyas + çözünürlük · **Durum:** iki kilitli sonuç + keşif +
iki yeni protokol · **Kaynak:** `docs/olcumler/W2_UA_2026-09-19/`,
[PROTOKOL-W2](../truba/PROTOKOL-W2-KIYAS-TEKRAR.md), [PROTOKOL-UA](../truba/PROTOKOL-UA-UZAK-ALAN.md),
[PROTOKOL-UY](../truba/PROTOKOL-UY-YAKIN-ALAN.md), [PROTOKOL-UG](../truba/PROTOKOL-UG-GECIS-ANI.md) ·
**Öncül:** [KAYIT-066](KAYIT-066_2026-09-18_W-okunmaz-A92-ve-W2.md)

---

## 1. Kilitli yargılar

### W2 — `KIYAS TUTTU` (kapsam TAM, 6/6 geçerli)

| `Y₀` | bizim `β` (`t_geçiş` 0,2 s) | L1 Tablo 2 | oran | `β_km` | sağlamlık farkı |
|---|---|---|---|---|---|
| 50 Pa | 3,295 | 3,63 | 0,87 BANDDA | 3,294 | 0,09 |
| 10 Pa | 3,667 | 4,18 | 0,84 BANDDA | 3,711 | 0,15 |
| 1 Pa | 3,992 | 4,66 | 0,82 BANDDA | 4,100 | 0,13 |

Eğilim VAR (`Y₀` düştükçe `β` artıyor), sağlamlık VAR (`≤ 0,20`), enerji sapması
`−%0,91`. **Kendi GPU kodumuz, literatürün tüm cisim DART-benzeri kıyasını
faktör 2 bandının çok içinde, %13–18 altında üretiyor.**

### UA — `UZAK ALAN YAKINSAMIŞ` (3/3 geçerli)

| taban aralık | parçacık | `β` (600 s) |
|---|---|---|
| 7 m | 14 616 | 3,667 |
| 5 m | 26 586 | 3,675 |
| 3,5 m | 64 239 | 3,677 |

`Δ(3,5; 5) = 0,001`, `Δ(3,5; 7) = 0,004`. 48 m ötesinin çözünürlüğü `β`'yı
değiştirmiyor. LITERATUR §10'daki "ilk şüpheli uzak alan" hipotezi **çürüdü**.

## 2. Keşif (koşudan sonra bakıldı — yargı değil)

**(a) U/V başarısızlığının sebebi görüldü.** W2'nin `β(t)` eğrisi (özet CSV):

| t | 0,024 s | 0,1 s | 0,2 s | 1 s | 10 s | 100 s | 600 s |
|---|---|---|---|---|---|---|---|
| `β` (Y10, 0,2 s) | 1,54 | 1,85 | **1,95** | 2,45 | 3,30 | 3,79 | 3,67 |

0,2 s'deki `β ≈ 1,95`, U/V'nin 0,1–0,2 s'de ölçtüğü `≈ 2,05` ile aynı
mertebe. `β`'nın yarıdan fazlası 0,2 s'den **sonra**, geç evre küresel
akışta geliyor. KAYIT-064/065'teki "süre kırpması" hipotezi kendi kodumuzla
**gözlendi** (kıyas sahnesinde; DART sahnesinde henüz değil).

**(b) Plato.** `β` 50–150 s'de tepe yapıyor, sonra 600 s'ye kadar `%1–3`
geri iniyor (gövde, uzaklaşan ejektayı kütleçekimiyle geri çekiyor — beklenen
yön). 600 s değeri platonun içinde; süre `β`'yı aşağı kırpmıyor.

**(c) Geçiş anı yakınsamamış.** `t_geçiş` 0,2 → 1,0 s: `β − 1` **+%9–15**
(Y50 3,295 → 3,494; Y10 3,667 → 4,070; Y1 3,992 → 4,389). Kilitli sağlamlık
eşiği (`0,20`) bunu tolere etti, ama fark tek yönlü. 1,0 s'de L1 oranları
**0,96 / 0,97 / 0,94**. Geçişte kinetik enerji 0,2 ile 1,0 s arasında hemen
hiç azalmıyor (`3,757e8 → 3,746e8 J`): 0,2 s'de hedef hâlâ akıyor. L3 ölçütü
`10 L / c_s ≈ 0,5–1 s`; L8 `5–500 s` kullanmış. → **PROTOKOL-UG.**

**(d) Koni açısı yakınsamamış.** UA kollarında `%90` açı `151 / 174 / 161°`,
kenar `162 / 194 / 174°` — `β` `%0,4` içinde kalırken koni `±%7` oynuyor ve
`180°`'yi aşıyor (küresel deformasyonda ejekta yarım küreden geniş). 600 s'de
**hız yönünden** ölçülen koni, LICIACube'ün 160–180 s'de **konumdan** ölçtüğü
koniyle (L2: `ω ≈ 115–139°`) aynı büyüklük değil → **A95**; gözlenebilir
olarak kullanılamaz.

**(e) Ejekta kütlesi** UA kollarında `2,53 / 3,00 / 2,82e7 kg` (`±%9`):
`β`'dan gevşek ama kullanılabilir (çözünürlük terimi `~0,1`).

**(f) İki yöntem.** `|β_km − β_kaçan|` `%0,05 – %2,7`. L2 bu farkı hata
payı olarak kullanıyor; biz de koşu başı model eksikliğine ekleyebiliriz.

## 3. Ders — koşu sürerken TRUBA ağacı güncellemek

UA gönderilirken W2 koşuyordu ve `dart-rift` ağacı güncellendi. Kod tembel
içe aktarıyor (ör. `beta_iki_yontem`, alüminyum Tillotson döngü içinde):
koşunun sonundaki içe aktarım **yeni** kodu okuyabilirdi. Bu sefer `src` farkı
boştu (doğrulandı). **Kalıcı düzeltme:** `is_UY_UG.slurm` kendi git
worktree'sinden koşuyor (`AGAC` zorunlu; `SABIT_COMMIT` ile aynı ve temiz
olmalı; `PYTHONPATH` ona bakıyor). Ana ağaç artık koşuları etkilemeden
güncellenebilir.

## 4. Gönderildi

**UY + UG** `1569287_0 … _3` (kod `0721629`, `agac_uyug`), 4 GPU, hepsi
başladı (kolyoz1/56/10/11):

| görev | ad | ne | `t_end` |
|---|---|---|---|
| 0 | UY_orta | 48 m içi bütün kademeler 2× ince (M'nin "orta"sı) | 300 s |
| 1 | UY_ic | yalnız 12 m içi 2× ince | 300 s |
| 2 | UG_Y10_g2p5 | `t_geçiş = 2,5 s` | 600 s |
| 3 | UG_Y10_g5p0 | `t_geçiş = 5,0 s` | 600 s |

Beklenen `~34 GPU-sa`. Kurallar koşudan önce commit'lendi (`0721629`).

## 5. Dürüst değerlendirme

- İyi haber gerçek ama **kıyas sahnesinde**: L1 küresi, homojen, dik çarpma.
  DART sahnesi (elipsoit, 17°, 25 m kaçık, üç küre mermi, bloklar) henüz
  geç evre modeliyle koşulmadı.
- `%13–18` altta kalmak "hata" değil ama **model eksikliği**: kodlar arası
  fark L6'da `±%5–10`. Bu fark posteriora `σ_kod` olarak girmeli (ADR-0051).
- 0,2 s geçişle koşulan her şey (W2 dahil) `β`'yı **düşük** veriyor olabilir;
  UG sonuçlanmadan üretim geçiş anı seçilmez.
