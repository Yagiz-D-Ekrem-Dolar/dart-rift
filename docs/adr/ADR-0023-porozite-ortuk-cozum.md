# ADR-0023: P-α distansiyonu **örtük** çözülür (açık güncelleme aşırı atıyordu)

- **Durum:** Kabul edildi — ADR-0022'deki açık kusuru **kapatır**
- **Tarih:** 2026-07-29
- **Bağlam:** P2-FR-04, P2-VR-06; FAZ 3 engelleyicisi
- **İlgili:** [ADR-0008](ADR-0008-porozite-enerji-muhasebesi.md), [ADR-0020](ADR-0020-enerji-hatasi-kesme-hatasidir.md), [ADR-0022](ADR-0022-porozite-baslangic-ve-acik-enerji-kusuru.md)

## Sorun

ADR-0022 başlangıç durumu hatasını düzelttikten sonra da gözeneklilik açıkken
enerji hatası **çözünürlükle büyüyordu** (nside 32 → 44: %6,74 → %15,81),
gözenekliksiz ise sabitti (%0,244 / %0,264). İç enerji ezilme sırasında
**negatife** düşüyordu.

## Kök nedene giden ölçüm

Önce "şiddetli rejimde model zorlanıyor" hipotezi kuruldu ve **çürütüldü**:
sıkıştırma hızı düşürüldükçe hata **kötüleşti**.

| v_iç | E hatası | max&#124;dα&#124; / adım | α_son |
|---|---|---|---|
| 5 m/s | **%8127,60** | 0,471 | 1,0000 |
| 50 m/s | %79,80 | 0,395 | 1,0000 |
| 500 m/s | %2,40 | 0,500 | 1,0000 |

Belirleyici gözlem: **`max|dα|` her koşuda ~0,5.** Yani α, sıkıştırma hızından
**bağımsız olarak** 1,5'ten 1,0'a **tek adımda** çöküyordu. Mutlak hata
sabitti; oranın değişmesi yalnızca `E₀ ∝ v²` küçüldüğü içindi.

## Kök neden

`porosity_update`, distansiyonu **açık** (explicit) güncelliyordu: bir önceki
adımın `P`'sinden `crush_alpha(P)` okunup doğrudan yazılıyordu.

Tillotson gibi sert bir EOS'ta bu kararsızdır. Başlangıçta `ρ=1800`, `α=1,5`
→ `ρ_s = 2700` → `P = 0`. Küçücük bir sıkıştırma (`ρ → 1810`) `ρ_s`'yi 2715'e
çıkarır ve `P ≈ 9,9×10⁷ ≈ P_s` olur — yani **crush eğrisinin tamamı %0,4'lük
bir gerinimle aşılır**. Açık güncelleme α'yı bir anda 1'e indirir; o anda
`ρ_s = ρ = 1810` olur ve katı, gerilmesiz 2700'e göre **%33 genleşmiş**
sayılır. Sonuç: devasa sahte çekme, negatif iç enerji, patlayan enerji
defteri.

Denklem aslında **örtüktür**: `α`, kendi belirlediği basınca bağlıdır.

```
α = crush_alpha( P_katı(α·ρ, u) / α )
```

## Karar

Bu skaler denklem, her parçacık için `[1, α_eski]` aralığında **bisection**
ile çözülür. Kalıntı bu aralıkta monotondur, dolayısıyla bisection kararlıdır.
Adım sayısı **sabittir** (40 → ~1e-12 hassasiyet): koşudan koşuya aynı iş,
aynı sonuç — ADR-0002'nin determinizm şartı korunur.

Geri genleşme yasağı ve `α ≥ 1` kısıtı aynen sürer.

Uygulama hem CPU referansında (`materials.solve_alpha_implicit`) hem GPU
çekirdeğinde (`porosity_palpha.porosity_update_k`) aynıdır; çekirdek artık
`P` yerine `rho` ve `u` alır.

## Sonuç

Aynı sıkıştırma testi, örtük çözümle:

| v_iç | E hatası | α_son | max&#124;dα&#124; | ρ_s | u_min |
|---|---|---|---|---|---|
| 5 m/s | **%0,4647** | 1,4941 | 0,00061 | **2700,0** | **+1,64** |
| 50 m/s | %0,4743 | 1,4312 | 0,00623 | 2698,7 | +171 |
| 500 m/s | %0,5879 | 1,0510 | 0,05767 | 2618,5 | +2,61e4 |

Beş şey birden düzeldi:

1. **Enerji hatası %8127 → %0,46** ve artık sıkıştırma hızından bağımsız
   (~%0,5, yani normal kesme hatası seviyesi).
2. **İç enerji pozitif** — gözenek çökmesi artık malzemeyi ısıtıyor.
3. **α kademeli evriliyor**: adım başına maks. değişim 0,47 → 0,0006.
4. **α sıkıştırmayı izliyor**: v=5'te 1,494, v=500'de 1,051. Eskiden her
   durumda 1,000'e çöküyordu — yani model gözenekliliği hiç modellemiyordu.
5. **ρ_s = α·ρ ≈ 2700 kalıyor** — katı artık sahte biçimde sıkışıp
   genleşmiyor. Fizik gereği olması gereken budur: gözenekler kapanır, katı
   sıkışmaz.

Çarpma senaryosunda (ADR-0022'nin ölçüsü):

| nside | gözenekli | gözenekliksiz | fark |
|---|---|---|---|
| 32 | %6,74 → **%0,3798** | %0,2437 | %0,1362 |
| 44 | %15,81 → **%0,3955** | %0,2638 | %0,1317 |

Hata artık **çözünürlükle büyümüyor** (0,3798 → 0,3955) ve gözenekliliğin
getirdiği fazladan yük sabit ~%0,13 — sıradan kesme hatası mertebesinde.
nside=44'te **40 kat** iyileşme.

## ADR-0008 ile ilişkisi

ADR-0008 sıkışma işinin `u`'ya **ayrıca eklenmemesi** gerektiğini
söylüyordu. **Bu karar doğruydu ve korunuyor.** Ölçümle de doğrulandı: işi
eklemek (şartname sözde-kodu) hatayı %1,88'den %20,33'e çıkarıyordu; ters
işaretle (%51,51) daha da kötüydü. Sorun muhasebede değil, **α'nın
çözülüşündeydi**.

## Sonuçlar

- (+) FAZ 3 engelleyicisi kalktı. Gözenekli hedeflerle çalışılabilir.
- (+) Model artık gözenekliliği gerçekten modelliyor (α ara değerlerde
  kalabiliyor); bu, çıkarımın asıl parametresi olduğu için kritik.
- (−) Adım sonunda parçacık başına 40 bisection yinelemesi eklendi. Her
  yineleme bir Tillotson değerlendirmesi içerir. Maliyet ölçülmeli; gerekirse
  yineleme sayısı toleransa göre azaltılabilir (determinizm için sabit
  kalmak şartıyla).

## Doğrulama

- `tests/test_porous_continuity.py` — 10 test, aralarında:
  - `test_porous_ledger_matches_solid_ledger` (eskiden `xfail`)
  - `test_porous_ledger_does_not_grow_with_resolution` (kusurun imzası)
  - `test_internal_energy_stays_physical_during_crush` (u > 0)
- `tests/test_solid_cross.py` — CPU↔GPU çapraz kontrolü (GPU çekirdeği
  değiştiği için zorunlu)
- `tests/test_crush_curve.py`, `tests/test_ablation.py` — regresyon
