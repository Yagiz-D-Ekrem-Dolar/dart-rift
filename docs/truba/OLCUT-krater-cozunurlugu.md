# A17 — ejekta **çözünürlük mü, mekanizma mı**? (2026-08-21, koşudan **önce**)

## Nereye geldik

Parametre tarafı kapandı: koşu süresi, yerçekimi, matris `Y0`, blok
`Y0`, hasar, gözeneklilik — hiçbiri `β`'yı oynatmadı ve kaçan hedef
kütlesi **her koşuda tam sıfır**. Kalan iki açıklama var ve ayrılması
gereken şey bu:

| | iddia |
|---|---|
| **S1 — çözünürlük** | Ejekta perdesi kraterin üst birkaç metresinden fırlar. `λ₂ = 2` ile orada `3,5 m`'lik parçacıklar var, yani fırlatma tabakası **1–2 parçacık kalınlığında**. Perde temsil edilemiyor. |
| **S2 — mekanizma** | Çözünürlükten bağımsız olarak bu formülasyon kazı akışını üretmiyor (model-form). |

Bugüne kadarki `λ₂` taraması (`2 -> 4`) `β`'ya bakıyordu ve `β`'nın
tamamı **merminin** sekmesi olduğu için o tarama **hedef ejektasını
hiç sınamadı**.

## Koşu

Kol **C**: `λ₂ = 2 -> 4` (krater bölgesinde aralık `3,5 -> 1,75 m`),
geri kalan her şey kol **B** ile aynı — `matrix_Y0 = 1 Pa`,
`boulder_Y0 = 1 Pa`, yerçekimi **açık**, `t_end = 5 s`.

Karşılaştırma tabanı (kol B, iş `1515196`):

| | B |
|---|---|
| kaçan hedef kütlesi | `0` |
| `bekleyen` (içeride, `r > R`, `v_r > v_kaçış`) | `0` |
| `beta_bal` | `1,411231` |

## Ölçüt — **veriye bakılmadan**

`t_end = 5 s`'de hedef maddesi `2R`'ye varamaz; o yüzden karar
**`bekleyen`** ve **`beta_bal`** üzerinden veriliyor — ikisi de
`t = 5 s`'de yanıt verebilen büyüklükler.

- `bekleyen >= 100` **veya** `beta_bal >= 1,6` -> **S1**: çözünürlük
  ejekta üretimini açıyor; A17 bir ayrıklaştırma sınırıdır ve yol
  krater bölgesini inceltmekten geçer.
- `bekleyen <= 5` **ve** `|beta_bal - 1,4112| < 0,01` -> **S2**:
  çözünürlük de değil; eksik olan mekanizmanın kendisi ve bu bir
  **model-form** kararıdır.
- arası -> kısmi; `λ₂ = 6` ile üçüncü nokta gerekir.

## Koruyucu

Kol B'nin koruyucusu aynen geçerli: momentum kapanışı `> 1e-10` ya da
cisim kendiliğinden dağılıyorsa koşu **geçersiz**.

Ayrıca `A1` (mermi çözünürlüğü) bu kolda **artmalı** (`λ₂` büyüyünce
aşama-2 aralığı küçülüyor); bu bir yan etki ve `β`'yı `1`'e doğru
iter. O yüzden karar `β`'ya değil **hedef** göstergelerine bağlandı.
