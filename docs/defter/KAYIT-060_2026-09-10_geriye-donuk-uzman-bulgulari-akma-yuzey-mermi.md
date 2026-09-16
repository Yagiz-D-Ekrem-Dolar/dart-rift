# KAYIT-060 — Uzman bulguları: akma kuvvet anında aşılıyor, krater bir yüzey değil, mermi fazla yumuşak (2026-09-10 – 09-12)

**Kapsam:** Bitiş 3 öncesi sayısal doğruluk · **Durum:** GERİYE DÖNÜK yazıldı
(2026-09-16) · **Kaynak:** [`FAZ4-SIKINTI-RAPORU.md`](../FAZ4-SIKINTI-RAPORU.md)
A71–A79 (satır ~4985–5150 ve ~5389–5516); sayılar aynen aktarıldı ·
**Öncül:** [KAYIT-059](KAYIT-059_2026-09-05_geriye-donuk-uzman-incelemesi-sok-kapisi-viskozite.md)

---

## 0. Bu kaydın bugünle bağı

Bugün (16.09) U kampanyasının her görevinde koşan üretim bayraklarının üçü bu
üç günde doğdu: **`--akma-kipi ara`** (A72), **`--ilk-dt-duzelt`** (A77),
**`--mermi-h-kipi kendi`** (A78); ayrıca **`--blok-uretici v2`** ve
**`--malzeme-kaynagi geometri`** (A74) ve yüzey tabanlı krater operatörü (A73).

## 1. Olaylar

| kayıt | tarih | bulgu | ölçülen | sonuç |
|---|---|---|---|---|
| A71 | 10.09 | **Protokol I**: geçiş noktası `x₀` çözünürlüğe dayanıklı mı | kaba `6,340`, orta `5,950`; `\|Δx₀\| = 0,3898`, **`2,44σ` → ZAYIF** (uzman jackknife `1,86σ`, "kararı geri almak için kullanılmamalı") | "mutlak derinlik yakınsamıyor ama `x₀` aktarılabilir" hipotezi tutmadı |
| **A72** | 11.09 | **Kuvvet anında akma sınırı aşılıyor**: gerilme yarım adım ilerletilip kuvvet geri döndürülmemiş deneme gerilmesiyle hesaplanıyor | birim sınav `q/Y = 1 966` (`(√3/2) G γ̇ Δt / Y`), `Δt` ile doğrusal; üretimde `Y₀ = 1,28e3 Pa`'da `q/Y` en büyük `457 600`, hedef kütlesinin **%42,2**'si akmayı aşıyor; eşdeğer gerilme `Y₀`'dan bağımsız `~5e8 Pa` | `akma_kipi = "ara"` (her kuvvet çağrısından önce akma yüzeyine dönüş); `I2_ara` orta ölçekte `q/Y` en büyük **tam 1**; **Protokol J** kilitlendi |
| **A73** | 11.09 | **`krater_derinlik` bir yüzey değil** (açısal halkadaki bütün parçacıkların sayı ağırlıklı `p95`'i) | dış 1 m kabuk sabit, yalnız iç taşınınca üç deneyde de `~0,49 m`; 8 kat çoğaltınca `0,34 → 0,71`; `1 m` derin analitik çukurda `0,0012 m` | `krater_yuzey`: SPH doluluk `φ` eş-yüzeyi, sabit fiziksel yanal ışınlar; kabuk sınavı `8,9e-4 m`, yeniden örnekleme farkı **0**, geniş çukur `0,9899` (ayrık gerçek). Kendi hatam: kütle merkezi kaymasını rijit hareket saydım (`0,375 m`), düzeltildi |
| **A74** | 11.09 | **Blok kesri düğmesinin üst kısmı ölü; ince parçacık bloğu göremiyor** | v1 yerleştirici `~0,35–0,37`'de doyuyor; G1/G2'nin 48 noktasında nominal `0,051–0,484` → gerçek **`0,102–0,371`**, 11/48 doymuş; ince parçacık malzemesi kabadan kopyalanıyor | `place_boulders_v2` (gerçek hacim kesri ya da açık "doydu"), `malzeme_kaynagi="geometri"`; varsayılanlar bit-aynı |
| A75 | 11.09 | mermi hedefin Tillotson parametrelerini kullanıyor | tek `TillotsonWp` bütün parçacıklara | açık kaldı; sonra `--mermi-eos aluminyum` ile yönlendirme (bugün üretimde) |
| A76 | 11.09 | "katı sıkışma" tanısı ham `ρ`'ya bakıyor; katı iskelet `α ρ` | uzman: `max(αρ/2700) ≈ 1,00008 – 1,00033` | sonuç değişmiyor, **tanım** yanlış |
| **A77** | 11.09 | **çarpma başında toplam enerji kayboluyor; ilk `Δt` bayat** | `cfl 0,25`: ilk adımda **%0,94**, 1 ms'de `−%2,19`; ilk `dt 1,82e-5`, ikinci `9,96e-6`; `hazirla()` ilk kaybı `%0,94 → %0,30` | `--ilk-dt-duzelt`; kalan kayıp `Δt` ile ~doğrusal (birinci mertebe şok zaman hatası); J'nin yorumuna "koşudan sonra" notu |
| **A78** | 12.09 | **mermi `h/s ≈ 10` ile çok yumuşatılmış** (h hedefin en ince seviyesine bağlı) | kaba `h/s = 9,7`, orta `4,9`, ince `2,4`; `Δt` eşleştirilmiş kontrolle: `β − 1` `5e-5 → 0,031` (**600 ×**), şok kapısı `KISMI → SOK_VAR`; ikinci θ (`Y₀` 225 × farklı) aynı yön `0,027` | `--mermi-h-kipi kendi`; krater (yeni operatör) `%0,2 / −%6` değişiyor |
| A79 | 13.09 | duyarlılık raporu "türev gürültüde → OKUNMAZ" kuralını **uygulamıyordu** | L2 blok kolunda `turev_gurultude: [Y₀, f]` iken yargı "ÜÇ EKSEN AYRIŞIYOR" | `karar` aynen, yanına `karar_okunur` (belge–kod ayrışması: eşik sınanıyordu, **uygulanış** sınanmıyordu) |

## 2. Ne anlaşıldı

1. **"`Y₀` duyarsızlığı" üç ayrı katmandan geliyor olabilir:** A51 (çekme dalı
   kırpılmıyor), A72 (kuvvet anında akma binlerce kat aşılıyor), A78 (mermi
   yumuşak, şok zayıf). Hiçbiri tek başına "fizik Y₀'a duyarsız" demek değil;
   üçü de **sayısal yol** adayı. (16.09 U1/U2: `ara` kipinde bile 10 Pa altında
   doyum — bu kez basınç–sürtünme terimi açıklıyor, bkz. KAYIT-057.)
2. **Ölçüm operatörü, ölçtüğü şeyin geometrisinden bağımsız olmalı** (A73):
   çoğaltma ve iç taşıma sınavları operatör sınavının standart parçası oldu.
3. **Bir düğmenin çalıştığı aralık ölçülmeli** (A74): nominal değer analize
   girerken sahnede gerçekleşen değer başka olabilir.
