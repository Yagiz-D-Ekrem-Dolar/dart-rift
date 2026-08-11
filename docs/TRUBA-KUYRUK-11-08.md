# TRUBA kuyruğu — 11.08.2026'da gönderilenler

Kota açıldı (`7,2M → 37,2M` CPU-dakika). Dört iş kuyrukta; hepsi
`(Priority)` ile bekliyor (küme dolu: 52 alloc, boş düğüm yok).

| iş | id | ne ölçüyor | süre isteği |
|---|---|---|---|
| `duman` | 1469938 | ortam doğrulaması (`t_end = 0,01`, 1 nokta) | 12 dk |
| `y0lo` | 1469927 | `Y0 = 10³ Pa`, `t_end = 20 s` | 24 sa |
| `y0hi` | 1469935 | `Y0 = 10⁷ Pa`, `t_end = 20 s` | 24 sa |
| `g4cens` | 1469936 | G4-C eğitim kümesi: 9 köşe + 31 LHS, `t_end = 0,2 s` | 24 sa |

Commit: `9da74b1`.

---

## Neden bu dört iş

### `duman` — ilk okunacak dosya

Kısa iş olduğu için backfill'e girer ve diğer üçünden **önce** başlar.
Ortam bozuksa üç büyük iş de aynı sebeple düşer; bunu 12 dakikada
öğrenmek 24 saatte öğrenmekten iyidir.

> `pylib/warp` bugün **karışık kurulum** hâlindeydi ve import bile
> patlıyordu (`_ProtocolMeta | NoneType`). Temiz `1.15.0` açıldı ve
> login düğümünde import doğrulandı — ama **GPU yolu doğrulanmadı**.
> Duman işi tam o boşluğu kapatıyor.

### `y0lo` / `y0hi` — ADR-0046'nın 2. eksik ölçümü

`Y0` `t = 0,2 s`'de görünmüyor (dört mertebe → `β` `0,001`, derinlik
`0,077 m`). Hipotez: mukavemet kraterin **geç** evresinde belirleyici,
yani uzun koşuda ayrışabilir.

**Okuma ölçütü — veriye bakmadan yazıldı:**

İki koşunun `.izler.jsonl` dosyalarındaki `krater_derinlik` serileri
karşılaştırılacak.

| gözlenen | sonuç |
|---|---|
| ayrılma `t*`'ta başlıyor ve fark `> 1 m` | `Y0` görünür → ADR-0046 **S3**, uzay korunur |
| `t = 20 s`'ye kadar fark `< 0,25 m` (gürültü tabanı) | `Y0` görünmez → **S1**, uzay indirilir |
| arası | belirsiz; `t_end` büyütülmeli |

`0,25 m` eşiği ölçülmüş gürültü tabanı (rapor A16); **sonradan
düşürülmesi yasak**, o zaman ölçüt veriye uydurulmuş olur.

### `g4cens` — G4-C eğitim kümesi, **doğru** ileri modelle

`faz46_sentetik_kurtarma.py` kendi tek aşamalı `ileri_kosu`'sunu
kullanıyor (`λ = 2`) ve KAYIT-045 ölçtü ki o **başka bir problemi**
çözüyor (`n_ejekta` 803 = merminin tamamı sekiyor, `A1 = 0,215` düşük).
Onu aceleyle yeniden bağlayıp 24 saatlik yanlış iş göndermek yerine,
`faz412` (iki aşamalı, `A1` geçen, `ileri_kosu_ikiasama`) 40 noktada
koşuyor ve **her noktanın son durumunu `.npz` olarak yazıyor**.

Yani çıkan şey doğrudan vekil/posterior'a beslenebilecek `X, Y` matrisi
**ve** sonradan yeni bir gözlenebilir sorulursa koşu gerektirmeyen durum
arşivi.

`t_end = 0,2` yeterli çünkü `β` `t = 0,2` ile `t = 5,0`'da **bit
düzeyinde aynı** çıktı (iki bağımsız koşu, `1.4112162721355217`).

---

## Beklenen sonuç dosyaları

```
driftclaude/duman.json          + duman_durumlar/
driftclaude/y0lo.json           + y0lo.izler.jsonl  + y0lo.son_durum.npz
driftclaude/y0hi.json           + y0hi.izler.jsonl  + y0hi.son_durum.npz
driftclaude/g4c_ensemble.json   + g4c_durumlar/nokta_XX.npz
```

`.izler.jsonl` **artımlı** yazılıyor: iş duvar süresine takılsa bile o
ana kadarki seri kullanılabilir.

---

## Dokunulmayanlar

`1469911_[…] rel_bld` başka bir projeye ait
(`/arf/scratch/egitimg16u4/reddit_relevance/`) — kuyrukta bırakıldı.

TRUBA'daki `docs/G4-KAPI-RAPORU.md` yerel değişikliği
`driftclaude/yedek_20260811/` altına kopyalandıktan sonra depo
`origin/main`'e (94 commit geriydi) hızlı ileri sarıldı.
