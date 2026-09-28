# Protokol UY2 — çözünürlük × geçiş anı **kesişimi**: iki hata birbirini mi götürüyor?

**Yazıldı:** 2026-09-28, **UY2 koşusundan ÖNCE**. **Öncül:** PROTOKOL-UY
(`ÇÖZÜNÜRLÜK TERİMİ GEREKLİ`), PROTOKOL-UG (`GEÇİŞ YAKINSAMIŞ`, üretim
`t_geçiş = 1,0 s`), ADR-0052, KAYIT-069.
**Rapor:** `scripts/uy2_kesisim_raporu.py` → `S_UY2.json` (kilitli).

---

## 1. Neden — ADR-0052'nin açık bıraktığı tek soru

İki eksen ayrı ayrı ölçüldü, **kesişimleri ölçülmedi**:

| ayar | `β` | kaynak |
|---|---|---|
| kaba, `t_geçiş = 0,2 s` | 3,686 (300 s) | W2_Y10_g0p2 |
| **orta**, `t_geçiş = 0,2 s` | 3,978 (300 s) | UY_orta |
| kaba, **`t_geçiş = 1,0 s`** | **4,097 (300 s)** | W2_Y10_g1p0 |
| **orta**, **`t_geçiş = 1,0 s`** | **?** | **bu koşu** |

Kaba + doğru geçiş anı literatürü `%0,3` farkla tutuyor (`4,167` vs `4,18`,
`t_geçiş ≥ 2,5 s`). Ama çözünürlük ekseni tek başına `β − 1`'i `+%11,8`
diyor. İki ihtimal ayırt edilmemiştir:

1. **Bağımsız değiller:** geçiş anı düzeltilince çözünürlük farkı küçülür →
   üretim kaba merdivenle koşulabilir, bütçe `~400 GPU-saat`.
2. **Bağımsızlar (tesadüf):** kaba koldaki uyum iki hatanın birbirini
   götürmesidir → üretim orta merdivene geçer, bütçe `~1400 GPU-saat`.

## 2. Tasarım

`W2_Y10_g1p0` ile **aynı** her şey (L1 küresi, `Y₀ = 10 Pa`, `t_geçiş = 1,0 s`
— UG'nin kilitli **üretim** değeri, `A_geç = 1e5`, dondurma, yerçekimi),
yalnız merdiven `kaba → orta` (`48:2.8 24:1.4 12:0.7 6:0.35 3:0.175`).
`t_end = 300 s` (UY ile aynı kıyas anı). Tek koşu, `~11 GPU-saat`.

Kıyas noktası `W2_Y10_g1p0`'ın `β(300 s)`'idir (eğrisinden log-zamanda
aradeğerle; **yeniden koşulmaz**).

## 3. Geçerlilik

Koşu `gecerli = True` (momentum defteri dahil) ve `t = 300 s`'ye ulaşmış
olmalı; değilse genel **OKUNMAZ**.

## 4. Kilitli yargı

`b = β(300 s) − 1`. `Δ_kesişim = |b_orta@1,0 − b_kaba@1,0| / b_orta@1,0`.
Ölçülmüş `Δ_0,2 = 0,098` (UY, aynı iki merdiven, `t_geçiş = 0,2 s`).

| yargı | koşul | üretim sonucu |
|---|---|---|
| **EKSENLER BAĞIMSIZ DEĞİL** | `Δ_kesişim ≤ 0,05` | üretim **kaba** merdiven; çözünürlük terimi `σ = Δ_kesişim` |
| **AZALIYOR** | `0,05 < Δ_kesişim < Δ_0,2` | üretim kaba + **çok doğruluklu vekil** (birkaç orta nokta); `σ = Δ_kesişim` |
| **EKSENLER BAĞIMSIZ** | `Δ_kesişim ≥ Δ_0,2` | üretim **orta** merdiven; bütçe `~3,4×` |

## 5. Kapı olmayan tanılar

`impuls_sekli` ölçüleri (`t50`, `s(1 s)`, `s(10 s)`) — kaba kolla
karşılaştırılır. **Aynı `β`, farklı şekil** çıkarsa sayı tuttu ama mekanizma
tutmadı demektir (KAYIT-070 §2). `M_ejekta`, koni açıları, duvar süresi.
