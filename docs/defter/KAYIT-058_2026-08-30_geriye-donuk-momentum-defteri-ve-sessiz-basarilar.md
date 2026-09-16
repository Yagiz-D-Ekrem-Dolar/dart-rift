# KAYIT-058 — Momentum defteri ve "sıfır çıkış kodlu" sessiz başarılar (2026-08-30 – 09-03)

**Kapsam:** FAZ 4 → Bitiş 3 geçişi · **Durum:** GERİYE DÖNÜK yazıldı (2026-09-16)
· **Kaynak:** [`FAZ4-SIKINTI-RAPORU.md`](../FAZ4-SIKINTI-RAPORU.md) A26–A37
(satır ~3101–3609); sayılar oradan aynen aktarıldı, yeni ölçüm yok ·
**Öncül:** [KAYIT-055](KAYIT-055_2026-08-29_sok-arayuzu-cozuldu.md)

> Bu dönem defterde yazılmamıştı (boşluk notu, dizin). Olaylar o günlerde
> sıkıntı raporuna kaydedildi; bu kayıt onları **neyin nasıl anlaşıldığı**
> ekseninde birleştirir. Numara yazım sırasıdır (bkz. dizin notu).

---

## 0. Dönemin tek cümlesi

**Program "başarılı" dedi, ölçülen şey başka bir şeydi** — altı kez, altı farklı
kılıkta. Momentum defteri kurulunca da eski `β`'nın aslında hedefin değil
**merminin geri tepmesini** ölçtüğü ortaya çıktı.

## 1. Olaylar

| kayıt | tarih | ne oldu | ölçülen | ders |
|---|---|---|---|---|
| A26 | 30.08 | `--kademeler "3:20"` iki betikte farklı aralık demek (`λ` tabana bağlı) → TRUBA `J4` **iki kat kaba** koştu | `N` beklenen `131 057` → ölçülen **`17 201`**; `s_min 0,175 → 0,350 m`; hata yok | çare: merdiven **metre** ile (`48:2.8 …`), tek ayrıştırıcı `kademe_ayristir` |
| A27 | 30.08 | Sahnesiz şok tüpü: koşudan önce yazılan kural "denetim kolu `κ = 1`'de şok yoksa düzenek geçersiz" | denetim kolunda sıkışma **`%0,294`** (Hugoniot `%45,6`); sebep yanal boşalma | kural kendi yanlış pozitifimi (`κ = 20`, 4 parçacık) engelledi; düzenek "geçersiz" damgalı, silinmedi |
| A28 | 31.08 | Elemeler ilk kez şok varken ölçüldü (ama A26 yüzünden iki kat kaba) | beş kol sıkışma `%28,615`; **gözeneksiz `%0,518` (ŞOK YOK)**; `Y₀ 10 MPa → 1 Pa` sıkışmayı oynatmadı (şok basıncı `20,3 GPa`, `2 034` kat) | "Y₀ şoku etkilemiyor" ≠ "Y₀ β'yı etkilemiyor" — sonucu **kapsamının dışında okumama** (dördüncü kez) |
| **A29** | 31.08 | **Momentum defteri** kuruldu, makine hassasiyetinde kapandı (`artık/p = 1,15e-14`) | tek basamakta `β = 1,379`'un hedef katkısı **tam 0**; kaçan `579,4 kg` = merminin **tamamı**; merdivende `β_hedef = 1,033102`, `β_mermi = 0,052`, kaçan hedef `93,2 kg`; `β = 3,2225` için hedef ejekta momentumu **67 kat** büyümeli | `β` artık defterden türetilir; defter kapanmazsa "β RAPORLANMAZ"; `β_hedef` ve `β_mermi` ayrı |
| A30 | 01.09 | `K6`: altı kol, 0,2 s | kaçan hedef **`16` parçacık** = `93,2 kg` = `16 × 5,83 kg` (en ince parçacık); `Y₀` 8 mertebe → `β_hedef` `5e-5` oynadı | "etki yok" değil **"ölçülemez"**: `n_kaçan ≥ 50` güvenlik kapısı; asıl ölçüt yakınsama |
| A31 | 01.09 | `K5` altı eşzamanlı görev aynı noktaları koştu | `30` satır, **`5`** benzersiz nokta; `108` GPU-saat harcandı, `18`'lik iş; **%83 israf** | paylaşım yerine **bölüşüm** (`--dilim i/n`) |
| A32 | 01.09 | `pytest … \| tail && git push` — düşen test push edildi | boru hattının çıkış kodu `tail`'in (`0`) | bütün betiklerde `set -euo pipefail`; `test_kabuk_pipefail.py` yazıldığı anda **5 betikte eksik** buldu |
| A33 | 03.09 | `L1` ~15 saat koştu, **özet satırında** `AttributeError` ile çöktü; kusurun "testi vardı" | test **varlığı** sınıyordu (`durum.tamamlanan` var mı); `durum.n_tamam` da duruyordu | **yokluk** sınavı; JSONL satır satır yazıldığı için 24 noktanın tamamı kurtuldu |
| A34 | 03.09 | TRUBA iki gün eski kodla (`3bbc722`) koştu | `L1` alan adı kusuruyla çöktü; `L2` momentum defterini taşımıyor | o günkü çare: `git pull` işin **içinde** (bkz. A38 ve §2) |
| A35 | 03.09 | Şok kapısının **üst sınırı yok** | düşük AV kolu `%75,65`, band `%45,6 – 74,3` → yine `SOK_VAR` | `v/2` üst kenarı sezgisel (empedans eşleşmesi değil) — ölçütün sonuçla çürütülmesi kaydedildi |
| A36 | 03.09 | `n_kaçan > 32` eşiği düşük AV koluyla (`33`) geçildi | 33 parçacığın **hepsi kaba** (`372,83 kg`, `s = 0,700 m`; ince taban `5,83 kg`) | 33 kaba ≠ 33 ince; mekanizma adayı okuması düştü |
| A37 | 03.09 | `ileri_kosu_merdiven` **npz kaydetmiyordu** | `L1`'in 24 noktasında defter/`M_ejekta`/`θ` hesaplanamıyor; `β = 1,10077 – 1,10106` kullanılamaz | `npz` kaydı eklendi; bundan sonra her koşu defteri ve parçacık kimliğini taşır |

## 2. Bugünden bakınca (2026-09-16 notu)

- **A34 → A38 → bugün.** A34'ün çaresi işin içinde `git pull`du; A38 (05.09)
  eşzamanlı pull'ların yarışını ve rastgele eski sürümle koşmayı buldu (`flock`
  ile serileştirildi). 16 Eylül'de YağızTRUBA kurulumunda `git pull` işten
  **tamamen kaldırıldı**; kod `SABIT_COMMIT` ile sabitleniyor, uymazsa iş 92
  ile duruyor ([KAYIT-056](KAYIT-056_2026-09-16_yagiztruba-kurulum-ve-duman.md)).
  Üç adımlık zincirin kök çaresi bu.
- **A32'nin dersi 16 Eylül'de tersinden geri döndü:** bu kez `set -euo
  pipefail` altında `grep -c` eşleşme yokken `1` döndürüp **başarılı** kurulumu
  kesecekti (KAYIT-056 §3). Katı mod da yanlış kullanılınca sessiz hata üretiyor.
- **A29'un "67 kat" açığı** bugün Protokol U'nun sorusu: plato anında taban
  `β ≈ 1,95`, gözlem `3,12` (KAYIT-057).

## 3. Kalıp

| | "başarı" bildirimi | aslında |
|---|---|---|
| A26 | koşu tamamlandı | iki kat kaba |
| A29 | `β = 1,379` | mermi geri tepmesi |
| A30 | parametreler β'yı etkilemiyor | β ölçülemiyor (16 parçacık) |
| A32 | çıkış kodu 0 | test düşmüştü |
| A33 | test geçti | kusur duruyordu |
| A36 | eşik geçildi | kaba bloklar |

Ortak çare: başarı bayrağına değil, **başarının nasıl üretildiğine** bakmak —
koşudan önce yazılmış ölçüt, yokluk sınavı, ayrıklaştırma sayısı, kapanan defter.
