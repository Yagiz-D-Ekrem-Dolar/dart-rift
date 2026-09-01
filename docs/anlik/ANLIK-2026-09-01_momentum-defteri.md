# ANLIK 2026-09-01 — momentum-defteri

> **Değiştirilemez kayıt.** Bu dosya `MANIFEST.sha256` ile
> kilitli; düzenlemek testi düşürür. Sonradan öğrenilen
> her şey **yeni** bir anlık görüntüye yazılır.

| | |
|---|---|
| commit | `cc55481cd78cacef82ec9e9610c0ded4cef0d1da` |
| kısa | `cc55481` · dal `main` |
| commit tarihi | `2026-09-01T20:49:49+03:00` |
| çalışma ağacı | **temiz** |

---

## Bu anlık görüntünün konusu

Momentum defteri kuruldu ve `β`'nın bileşimi ilk kez ayrıştırıldı;
hedef ejektasının gürültü tabanında olduğu ölçüldü.

## GEÇERSİZ KILINAN YORUMLAR

| yorum | nerede söylenmişti | neden geçersiz | yerine |
|---|---|---|---|
| *"`β = 1,4112` motorun momentum artışıdır"* | FAZ 4 boyunca, `G4` kapı raporu | momentum defteri hedef katkısını **tam `0`** ölçtü | önceki `β`, hedef-ejekta momentumunu değil **baskın olarak mermi geri tepme momentumunu** ölçüyordu |
| *"model şok üretmiyor"* (A22) | `docs/FAZ4-SIKINTI-RAPORU.md` A22 | tek düzenekli tarama `%40,5` sıkışma ölçtü | şok **üretiliyordu**; aktarım siliyor, arayüz hapsediyordu (A23–A25) |
| *"`A1 ≈ 64` gerekli, nokta başına `~55` gün"* (A22) | aynı | karışık iki noktadan üs yasası | `470` kat yanlış; gerçek maliyet **`4,3` saat/nokta** |
| *"cephe `3,41 m`'de duruyor"* (A25 ilk hâli) | aynı | kütle parmak izi: şoklanan parçacıkların **tamamı** ince | `3,41 m` bir cephe değil, **ızgaranın sınırı** |
| *"`Y0` `β`'yı etkilemiyor"* (A28 okuması) | `J5`, `t = 6e-3 s` | şok basıncı `20,3 GPa` vs `Y0` `10 MPa` — `2 034` kat | `Y0` **şoku** etkilemiyor; kazı evresi `6e-3`'te henüz yok |

> Hiçbiri silinmedi. Hepsi kaynağında duruyor ve **geçersiz** diye
> işaretli.

## ANAHTAR SAYILAR

### Momentum defteri (`t = 0,2 s`, `p_mermi = 3 560 355 kg m/s`)

| | tek basamak | merdiven |
|---|---|---|
| `P_bağlı_hedef` | `4 909 756` | `3 863 797` |
| `P_kaçan_hedef` | `0,0` | `-117 854` |
| `P_bağlı_mermi` | `0,0` | `-21,8` |
| `P_kaçan_mermi` | `-1 349 401` | `-185 566` |
| **artık (bağıl)** | **`1,15e-14`** | **`1,15e-14`** |
| `β_hedef` | `1,000000` | `1,033102` |
| `β_mermi` | `0,379007` | `0,052120` |

### Şok ve krater

| | |
|---|---|
| sıkışma (`t = 0,2 s` boyunca sabit) | `%45,34` |
| Hugoniot bandı | `%45,6 – 74,3` |
| krater derinliği | `1,029 m` (doyum `~56 ms`) |
| kaçan hedef | `93,2 kg` = **`16` parçacık** × `5,83 kg` |
| gözlem hedefi | `β = 3,2225` -> gereken `P_kaçan_hedef` `7 912 889` (**`67` kat**) |

### Elemeler (`t = 0,2 s`, tek değişken, defter her kolda `~1e-14`)

| kol | `β_hedef` | kaçan hedef | `n` |
|---|---|---|---|
| güçlü matris (`Y0 = 1e8`) | `1,033146` | `262,1 kg` | `45` |
| hasarlı | `1,033097` | `93,2 kg` | `16` |
| taban | `1,033102` | `93,2 kg` | `16` |
| yerçekimli | `1,033102` | `93,2 kg` | `16` |
| zayıf blok (`1 Pa`) | `1,033116` | `93,2 kg` | `16` |
| zayıf matris (`1 Pa`) | `1,033098` | `93,2 kg` | `16` |

## KOŞU KİMLİKLERİ (TRUBA `kolyoz-cuda`, H100/H200)

| iş | JOBID | ne |
|---|---|---|
| `J1` | `1538888` | yayılma taraması — **tasarım kusurlu** (kollar şokun ulaşmadığı bölgede farklıydı) |
| `J2` | `1538887` | şok tüpü — **düzenek geçersiz** (denetim kolu düştü, A27) |
| `J3` | `1538889` | `ρ` aktarımı A/B — `47,6×` |
| `J4` | `1538890` | tam koşu — **`--kademeler` ölçek kusuru** (A26), `N = 17 201` |
| `K1` | `1539285` | yayılma, `t_end = 40e-3` |
| `K4` | `1539284` | tam koşu, düzeltilmiş merdiven — **bu görüntünün ana kaynağı** |
| `K5` | `1539871` | ensemble — **`%83` israf** (A31), `5` benzersiz nokta |
| `K6` | `1539872` | elemeler `t = 0,2 s` |
| `L1` | `1540987` | ensemble, bölüşümlü — koşuyor |
| `L2` | `1540986` | mekanizma sınavı — koşuyor |

## YAPILANDIRMA

| | |
|---|---|
| merdiven | `48:2.8 24:1.4 12:0.7 6:0.35 3:0.175` (metre, dıştan içe) |
| taban aralık | `7,0 m` · `N ≈ 76 700` |
| `t_end` | `0,2 s` · `27 429` adım · CFL `0,25` |
| malzeme | Tillotson bazalt, P-α açık (`α₀ = 1,7564`), hasar kapalı, yerçekimi kapalı |
| kaçış ölçütü | `r > R` **ve** `v_r > v_kaçış` |

## O GÜN NE BİLİNMİYORDU

- Maddenin neden akmadığı (`L2` koşuyor)
- `β_hedef`'in çözünürlükle yakınsayıp yakınsamadığı
- `α₀` değişince `n_kaçan`'ın büyüyüp büyümediği (`L1` koşuyor)
- Vekil modelin anlamlı veriyle davranışı
