# A17 — enerji **ısıya** gidiyor: gözeneklilik mi? (2026-08-21, koşudan **önce**)

## Ölçülen: enerji teslim ediliyor, akışa dönüşmüyor

Gelen enerji `½ m v² = 1,0939e10 J`. Kayıtlı durumlardan enerji
defteri (`t = 0,2 s`):

| kol | `KE` | `U` (ısı) | hedefte `KE` | hedefte `U` |
|---|---|---|---|---|
| tek aşama (`A1 = 0,215`) | `%38,2` | `%59,7` | `%0,004` | `%30,0` |
| iki aşama (`λ₁ = 38`, `A1 = 4,08`) | **`%5,6`** | **`%93,2`** | `%0,95` | **`%84,8`** |

İki bağımsız okuma:

1. **Merminin geri sekmesi çözünürlükle ölüyor.** Mermideki kinetik
   enerji `%38,2 → %4,7`. `β`'nın `1,618 → 1,185` düşüşü enerji
   defterinde de görünüyor — aynı olgunun ikinci ölçümü.
2. **Enerji hedefe geçiyor ama akış olmuyor.** Hedefin iç enerjisi
   `%84,8`; kinetik enerjisi `%0,95`. Yani madde **ısınıyor, hareket
   etmiyor**. Krater `9 cm`.

## Şüpheli: P-α gözeneklilik

Bu modelde ısının ana kuyusu **gözenek çökmesi**. P-α crush-up
geri dönüşsüz: malzeme sıkışır, ısınır ve **geri yaylanmaz**.
Gözenekli hedeflerde kraterin bastırılması gerçek bir fiziktir —
ama burada tek başına akışı öldürüyor olabilir.

`--gozeneksiz` kolu daha önce koşuldu ve `β`'yı `1,411 -> 1,517`
(`+%7,5`) oynattı. **Ama o ölçüm `μ = 80`'de yapıldı** — şokun
hedefe hiç girmediği rejimde. Hedefe enerji geçmiyorken gözenekliliği
kapatmanın etkisini ölçmek, bu turda üç kez düzelttiğim hatanın
aynısı.

## Koşu — yerel, `λ₂ = 6` (`μ = 2,98`), `t_end = 0,2 s`

| kol | ayar |
|---|---|
| **P** | üretim (gözenekli) |
| **G** | `--gozeneksiz` (P-α kapalı, sahne **katı** kurulur) |

`_sahne_kolu` gözeneksiz kolda sahneyi katı kuruyor (`ρ` ile `m/V`
uyuşmazlığı olmasın — rapor A14). Bu kol **tek değişkenli değil**:
gözeneksiz hedef `%50` daha ağır. Bu, *"gözeneksiz Dimorphos"*un
kaçınılmaz sonucu ve sonucun yanında okunmalı.

## Ölçüt — **veriye bakılmadan**

### 1. Birincil — enerji **akışa** mı gidiyor

`hedefte KE / gelen KE` (taban: `%0,95` — `λ₁=38` kolundan; `λ₂=6`
tabanı koşuyla birlikte ölçülecek):

- gözeneksiz kolda **`>= 3×`** artarsa -> gözeneklilik enerjiyi
  akıştan çalıyor; A17'nin mekanizması **budur**.
- **`< 1,5×`** -> gözeneklilik de değil; ısıya giden enerjinin sebebi
  başka (yapay viskozite ya da temas ayrıklaştırması).
- arası -> kısmi.

### 2. İkincil — krater derinliği (**yeni** ölçüyle)

`krater_yerdegistirme` ile ölçülür. Taban `λ₂ = 6`, `0,0728 m`.
Gözeneksiz kolda `>= 2×` derinleşme birincil ölçütü destekler.

### 3. Koruyucu

- Momentum kapanışı `< 1e-10`.
- `_alpha0_denetle` gözeneksiz kolda `alpha0 = 1` olduğunu zaten
  doğruluyor; patlarsa koşu **geçersiz**.
- Kütle farkı (`%50` daha ağır hedef) sonucun yanına yazılır;
  ölçüt bağıl oranlar üzerinden okunur.

## Bu koşunun karar **veremeyeceği** şey

`β`. `t = 0,2 s`'de ejekta perdesi yok. Enerji akışa dönüyorsa `β`
ayrı ve uzun bir koşuyla ölçülür.
