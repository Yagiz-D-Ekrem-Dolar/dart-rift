# Protokol W — yayımlanmış bir SPH sonucuyla **kıyas sınaması**

**Yazıldı:** 2026-09-17, **koşudan ÖNCE**. Kural sonuç geldikten sonra
değişmez; düzeltme ancak "yan yana" alan olarak eklenir (depo kuralı 6).
**Öncül:** ADR-0050, KAYIT-064, `docs/LITERATUR-DART-SIMULASYONLARI.md` L1.
**Rapor:** `scripts/w_kiyas_raporu.py` → `S_W.json` (kilitli).

---

## 1. Neden

U ve V, modelin DART `β`'sını üretmediğini gösterdi. ADR-0050 literatürdeki
araçları (geç evre şeması, öz-yerçekimi, düşük kohezyon) koda ekledi. Bu
araçlarla **gerçek DART'a** koşmadan önce şu sorunun cevabı gerekiyor:

> Kodumuz, **aynı sahnede** yayımlanmış bir SPH sonucunu yeniden üretiyor mu?

Üretmiyorsa DART'a koşmanın anlamı yoktur; üretiyorsa açığın nedeni model
sınıfı değil, bizim kurulumumuzdur ve düzeltilebilir.

Kıyas kaynağı **L1** = Raducan & Jutzi 2022, *PSJ* 3, 128, Tablo 2 (küre,
dikey çarpma, `f = 0,6`):

| `Y₀` [Pa] | 50 | 10 | 1 | 0 |
|---|---|---|---|---|
| `β` (L1) | 3,63 | 4,18 | 4,66 | 4,93 |
| `β − 1` | 2,63 | 3,18 | 3,66 | 3,93 |

## 2. Sahne (L1'in kurulumu, bizim koda çevrilmiş)

| | değer | not |
|---|---|---|
| hedef | küre `R = 75 m`, `ρ_yığın = 1600 kg/m³`, **homojen** (`--model-sinifi M0`) | L1 |
| gözeneklilik | `α₀ = ρ₀_katı/ρ_yığın = 2700/1600 = 1,6875` (`%40,7`) | L1 `%40` |
| dayanım | Lundborg, `μ_f = 0,6`, `Y₀ ∈ {50, 10, 1} Pa` | L1 satırları |
| mermi | `500 kg`, `ρ = 1000 kg/m³`, `6000 m/s`, alüminyum EOS, **dik** | L1 |
| öz-yerçekimi | **açık** | L1 |
| çözünürlük | kaba merdiven (`N ≈ 1,7e4`) | bizim bütçe; L1 `5e5` |
| geç evre | `A_geç = 1e5 Pa`, `t_geçiş ∈ {0,2 s; 1,0 s}` | L1 `~0,1 MPa`; L3 sağlamlık |
| dondurma | `k_uzak = 3`, her `200` adım | ADR-0050 |
| `β` | iki yöntem + koni açısı, `--beta-km` | L1 |

**Bilinen farklar (koşudan önce yazıldı, sonradan gerekçe uydurulmasın):**
`Y₀ = 0` bizde geçersiz (`θ` pozitif `Y₀` ister) → **0 satırı koşulmaz**;
gerinimle kohezyon kaybı (L1'de var) bizde **yok**; çözünürlük `~30×` düşük;
L1 `t_geçiş ≈ 30 dk`, biz erken geçiyoruz; blok yok (her ikisinde de).

## 3. Sıra ve süre

1. **W0 — zamanlama koşusu** (bilimsel sonuç DEĞİL): `Y₀ = 10 Pa`,
   `t_geçiş = 0,2 s`, `t_end = 2 s`. Ölçülecek: geçiş öncesi/sonrası adım
   süresi, `dt`, toplam GPU-saat/saniye-simülasyon.
2. W0'ın ölçtüğü hıza göre `t_end` **kuralla** seçilir (sonuca değil, hıza
   bakarak): koşu başına tahmini maliyet
   - `≤ 8 GPU-saat` ise `t_end = 600 s`,
   - `≤ 8 GPU-saat` değil ama `≤ 8 GPU-saat` ile `60 s`'ye ulaşılıyorsa `t_end = 60 s`,
   - ikisi de olmuyorsa `t_end = 10 s` ve rapora **"süre yetersiz"** damgası.
3. **W1–W6:** `Y₀ ∈ {50, 10, 1} Pa` × `t_geçiş ∈ {0,2; 1,0} s`, tek tohum,
   sıralı gönderim (aynı anda en fazla 20 GPU; kural 2).

## 4. Geçerlilik (her koşu)

`gecerli = True` (`sayisal_gecerlilik`) **ve** momentum defteri kapalı.
Geçersiz koşu rapora **GEÇERSİZ** yazılır, yerine başka koşu konmaz.

## 5. Kilitli yargı

Her `Y₀` için `t_geçiş = 0,2 s` kolu esas alınır (öteki kol sağlamlık):

    oran(Y₀) = (β_biz(Y₀) − 1) / (β_L1(Y₀) − 1)

- **Nicel ölçüt:** `0,5 ≤ oran ≤ 2,0` (faktör 2). Gerekçe: çözünürlük `~30×`
  düşük, gerinim yumuşaması yok, geç evre parametreleri aynı değil; L1'in
  kendi çözünürlük sınaması bile ejekta kütlesinde `%6–15` oynuyor.
- **Eğilim ölçütü:** `β(1 Pa) > β(10 Pa) > β(50 Pa)` (kohezyon azalınca `β`
  artmalı).
- **Sağlamlık ölçütü:** `|β(t_geçiş=1,0) − β(t_geçiş=0,2)| / (β(0,2) − 1) ≤ 0,20`.

**GENEL:**

| yargı | koşul |
|---|---|
| **KIYAS TUTTU** | üç `Y₀`'da da oran bandında **ve** eğilim **ve** sağlamlık |
| **KISMİ** | eğilim var, en fazla bir `Y₀` band dışında (sağlamlık aranmaz) |
| **TUTMADI** | eğilim yok **ya da** iki+ `Y₀` band dışında |

## 6. Yorum tablosu (koşudan önce)

| sonuç | anlamı ve sonraki adım |
|---|---|
| KIYAS TUTTU | Kodumuz literatürdeki sonucu üretiyor. U/V'nin açığı **kurulumdan** (süre + önsel) geliyor → gerçek DART sahnesiyle yeni model kurulur (önsel `Y₀` 0–500 Pa'ya, üç küre mermi, elipsoit şekil), Protokol X ile havuzlar. |
| KISMİ | Bir bileşen eksik. Sıradaki aday: gerinimle kohezyon kaybı, çözünürlük, `t_geçiş`. Eksik bileşen ADR ile eklenir, W **aynı kurallarla** yeniden koşulur. |
| TUTMADI | Geç evre şemasının bizdeki uygulaması ya da model sınıfı yetersiz. Gerçek DART'a koşulmaz; Faz D (nicel teşhis + koşulsuz Hera öngörüsü) yazılır. |

## 7. Rapora giren, ama **kapı olmayan** sayılar

`β` iki yöntem farkı ve `mermi_bagsiz_kesri`, ejekta koni açısı, ejekta
kütlesi, dondurulan parçacık sayısı, enerji sapması, adım sayısı, geçiş anı
ve GPU-saat. Bunlar yargıyı değiştirmez; yorumu değiştirir.
