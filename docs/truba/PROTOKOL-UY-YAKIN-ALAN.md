# Protokol UY — yakın/orta alan çözünürlüğü, geç evre modelinde `β`'yı değiştiriyor mu?

**Yazıldı:** 2026-09-19, **UY koşularından ÖNCE**. W2 ve UA'nın kilitli
sonuçları biliniyor (KAYIT-067): W2 `KIYAS TUTTU`, UA `UZAK ALAN YAKINSAMIŞ`.
**Öncül:** PROTOKOL-M (eski model, 24 ms: `YAKINSAMIYOR`), PROTOKOL-UA,
ADR-0051. **Rapor:** `scripts/uy_yakin_alan_raporu.py` → `S_UY.json` (kilitli).

---

## 1. Neden

M, **eski modelde** (geç evre yok, 24 ms) merdivenin bütün kademeleri
inceldikçe `β − 1`'in `0,743 → 0,642 → 0,459` düştüğünü ölçtü (yakınsamıyor).
UA, **yeni modelde** 48 m ötesinin (uzak alan) `β`'yı `%0,4`'ten az
değiştirdiğini gösterdi. Arada test edilmemiş bölge: **çarpma çevresinden
48 m'ye kadar** (yakın + orta alan). Soru:

> Geç evre modelinde (600 s'ye kadar küresel akış), 48 m içindeki bütün
> kademeleri 2 kat inceltmek `β`'yı ne kadar değiştiriyor?

Hipotez (yargı değil): zayıf hedefte momentumun çoğu geç evre küresel akıştan
geldiği için (W2 `β(t)`: 0,2 s'de `≈ 2,0`, 100–200 s'de `3,3–4,5`), M'deki
erken evre duyarlılığı `β`'nın son değerine **seyrelerek** yansır.

## 2. Tasarım

`W2_Y10_g0p2` ile **aynı** her şey (L1 küresi, `Y₀ = 10 Pa`, `t_geçiş = 0,2 s`,
`A_geç = 1e5 Pa`, dondurma, `β` iki yöntem), yalnız merdiven değişir:

| kol | merdiven (taban 7 m) | kaynak | `t_end` |
|---|---|---|---|
| **kaba** | `48:5.6 24:2.8 12:1.4 6:0.7 3:0.35` | **W2_Y10_g0p2** (yeniden koşulmaz; `β(300 s)` eğrisinden) | 600 s |
| **orta** | `48:2.8 24:1.4 12:0.7 6:0.35 3:0.175` (M'nin "orta"sı) | UY görev 0 | **300 s** |
| **iç** | `48:5.6 24:2.8 12:0.7 6:0.35 3:0.175` (yalnız ≤ 12 m inceltilir) | UY görev 1 | **300 s** |

**Neden 300 s:** W2'de `β` 100–200 s'de platoya ulaşıyor; 300 → 600 s arası
değişim `%0,3` (`Y₀ = 10`: 3,687 → 3,667). Orta kolun geç evresi kabadan
`~2×` küçük adım ve `~4,7×` parçacık ister; 600 s `~15 sa`, 300 s `~8 sa`.
**Karşılaştırma aynı anda yapılır:** kaba kolun `β`'sı `impuls_egrisi`nden
`t = 300 s`'de **log-zaman doğrusal aradeğerle** okunur.

## 3. Geçerlilik

Üç kolun hepsi `gecerli = True` (momentum defteri dahil); biri değilse genel
**OKUNMAZ**, yerine koşu konmaz. Orta ya da iç kol `t = 300 s`'ye ulaşmadıysa
(süre aşımı) **OKUNMAZ**.

## 4. Kilitli yargı

`b = β − 1` (300 s). `Δ_orta = |b_orta − b_kaba| / b_orta`.

| yargı | koşul | anlamı |
|---|---|---|
| **İKİ NOKTADA FARK KÜÇÜK** | `Δ_orta ≤ 0,05` | kaba merdiven havuz için yeterli; çözünürlük terimi `σ = Δ_orta` |
| **ÇÖZÜNÜRLÜK TERİMİ GEREKLİ** | `0,05 < Δ_orta ≤ 0,15` | havuz kaba + az orta, çok doğruluklu vekil (`cok_dogruluk.py`); posteriora `σ_çöz = Δ_orta` |
| **ÇÖZÜNÜRLÜĞE DUYARLI** | `Δ_orta > 0,15` | kaba tek başına kullanılamaz; orta çözünürlük üretim, iddia sınırlanır |

> **Dürüst sınır:** iki nokta **yakınsamayı kanıtlamaz**, yalnız bir adımlık
> farkın büyüklüğünü ölçer. Yargının adı bu yüzden "YAKINSAMIŞ" değil.

**Kapı olmayan tanı:** `Δ_iç = |b_iç − b_kaba| / b_iç` ve farkın iç bölgeden
gelen payı `(b_iç − b_kaba) / (b_orta − b_kaba)` (payda sıfıra yakınsa
yazılmaz); `M_ejekta` ve koni açıları üç kolda; duvar süresi.

## 5. Maliyet

Orta `~8 sa`, iç `~4 sa` (W2 ve UA ölçümlerinden: adım maliyeti parçacıkla
`~N^0,8`; erken evre adımı mermi parçacıklarıyla sınırlı). Toplam `~12 GPU-sa`.
