# ANLIK 2026-09-01 — yontem-donduruldu

> **Değiştirilemez kayıt.** Bu dosya `MANIFEST.sha256` ile
> kilitli; düzenlemek testi düşürür. Sonradan öğrenilen
> her şey **yeni** bir anlık görüntüye yazılır.

| | |
|---|---|
| commit | `260b95a068147715d50fff7c1436acef65588ac8` |
| kısa | `260b95a` · dal `main` |
| commit tarihi | `2026-09-01T21:07:47+03:00` |
| çalışma ağacı | **temiz** |

---

## Bu anlık görüntünün konusu

**Yöntem donduruldu.** Bundan sonra yeni kontrol, yeni gözlenebilir
ya da yeni eşik **eklenmeyecek**; kurulan sistemin ne söyleyeceği
görülecek. Bu, ön kayıt (*preregistration*) noktasıdır.

## DONDURULAN KURALLAR

### Dört kapı — `β_hedef` ancak dördü birden yeşilse gözlenebilir

| kapı | ölçüt | nerede |
|---|---|---|
| **şok geçerli** | sıkışma `≥ %4,56` (Hugoniot alt ucunun `1/10`'u) | `observables/sok.py` |
| **defter kapalı** | `\|artık\| / p_mermi ≤ 1e-3` | `observables/momentum_defteri.py` |
| **zamansal plato** | `\|ΔΔβ\| < max(1e-4, 0,05·\|Δβ\|)`, pencere **boyunca** sapma **ve** eğim | `plato_gecti()` |
| **uzamsal yakınsama** | `Δβ`, `M_ejekta`, `P_ejekta,∥` **üçü birden** | `OLCUT-yakinsama-gozlenebilir.md` |

### Ölçülen nicelik `β` **değil**

`Δβ_hedef = β_hedef − 1`. Gerekçe ölçüldü: `β = 1,030 -> 1,040`
geçişinde `β`'nın bağıl farkı `%0,96`, `Δβ`'nın `%25` — **`26` kat**.

### Eşikler

| aşama | eşik | sonucu |
|---|---|---|
| A1 tarama | `< 0,20` | gözlenebilir **aday** |
| A2 nihai | `< 0,10` | Dimorphos sonucu için |
| A2 sağlanmazsa | — | fark `σ_sayısal` olarak **posteriora taşınır** |

### `σ_sayısal` yöntemi — **veriden önce**

| davranış | yöntem |
|---|---|
| monoton | gözlenen mertebe `p`'den süreklilik-limiti hatası (`r = 2`) |
| monoton değil | muhafazakâr zarf `max\|Rᵢ − Rⱼ\|` |

Her nicelik için ayrı.

### `L2` karar ağacı

| kazanan kol | açılan hat |
|---|---|
| gözeneksiz | sıkıştırma / P-α |
| düşük AV | şok dağıtımı |
| `u` tabanı | termodinamik başlatma |
| hiçbiri | yeni hipotez (çözünürlük / arayüz / bünye) |

Eşik: kaçan hedef parçacığı tabanın (`16`) **iki katı** —
**mekanizma adayı eşiği**, kanıt değil. Ve kazanan ne olursa olsun
ifade *"model yanlış"* değil, **"mevcut parametreleme kazıyı
baskılıyor"**.

### Yalnızca **tanı** olanlar

`n_kaçan` (çıktı, kontrol değişkeni olamaz) · `θ_ejekta` (açısal
dağılım) · `β_mermi` (geri tepme).

## GEÇERSİZ KILINAN YORUMLAR

| yorum | neden | yerine |
|---|---|---|
| *"Değiştirilemez kayıt"* (`ANLIK-2026-09-01_momentum-defteri`) | depoya tam yetkisi olan biri dosyayı, manifesti ve testi birlikte değiştirebilir | **değişiklik algılanabilir** (*tamper-evident*) |
| *"`β_hedef` `%20` içinde yakınsarsa yeter"* | `β ≈ 1` rejiminde `26` kat gevşek | **`Δβ_hedef`** üzerinden |
| *"`~500`, `~2 000`, `~8 000` kaçan parçacıkta aynı `β`"* | `n_kaçan` bir **çıktı**, kontrol değişkeni olamaz | kontrol değişkeni **`m_p`** |
| *"iki uç nokta plato için yeter"* | uçlar tesadüfen aynı olup arada salınım olabilir | pencere **boyunca** sapma **ve** eğim |
| *"testler geçti"* (A32 öncesi) | `pytest \| tail` çıkış kodunu yutuyordu | `set -euo pipefail` + denetim testi |

## KOŞU KİMLİKLERİ

| iş | JOBID | ne | durum |
|---|---|---|---|
| `L1` | `1540987` | ensemble, bölüşümlü (`24` nokta / `6` görev) | koşuyor |
| `L2` | `1540986` | mekanizma sınavı (`taban`/`gözeneksiz`/`u_tabanı`/`düşük AV`) | koşuyor |

Sıradaki: `R1/R2/R3` çözünürlük taraması
(`s_min = 0,350 / 0,175 / 0,0875 m`).

## O GÜN NE BİLİNMİYORDU

- Maddenin neden akmadığı
- `Δβ_hedef`, `M_ejekta`, `P_ejekta,∥` üçünün yakınsayıp yakınsamadığı
- `θ_ejekta`'nın çözünürlükle savrulup savrulmadığı
- Dört kapının aynı koşuda yeşile dönüp dönemeyeceği

## BU GÖRÜNTÜNÜN AMACI

Sonuçlar geldiğinde *"kuralı sonuca göre mi seçti"* sorusunun cevabı
**bu dosyanın hash'i**. Kurallar burada, sonuçlar henüz yok.
