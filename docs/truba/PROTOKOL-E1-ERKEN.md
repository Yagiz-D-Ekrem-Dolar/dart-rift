# Protokol E1 — erken zaman: şok gerçekten oluşuyor mu

**Yazıldı:** 2026-09-05, **koşudan önce** · **Dayanak:** rapor A45
**v2:** uzman incelemesi (madde 14) — E1b `α₀=1` yerine `α` donuk

---

## Neden

A45 şunu ölçtü: depodaki **en erken** gözlem `t = 8,03e-3 s`, oysa
şok mermiyi `r_mermi/Us = 0,371/6145 =` **`6,0e-5 s`**'te geçiyor —
`dt ≈ 5,4e-6 s` ile **`≈ 11` adım**. İz aralığı `2 000` adım.
**Şok, tek bir iz noktası bile alınmadan gelip geçiyor.**

Ve `t = 0,2 s`'te ölçülen `%45,3`, matrisin salt gözenek kapanması
tavanının (`%75,64`) altında; `ρ_max = 2591 = 0,96 ρ₀ᵏᵃᵗⁱ`, yani
**hiçbir parçacıkta katı sıkışması yok.** Ölçülen sayı ezilme
artığıyla tamamen açıklanıyor.

Bu, şokun oluşmadığını **göstermez** — oluşup boşalmış da olabilir.
E1 bunu ayırt eder.

## Tasarım — **v2, uzman incelemesiyle düzeltildi**

| | E1a — üretim | E1b — **α donuk** |
|---|---|---|
| P-α güncellemesi | açık | **kapalı** (`--alpha-donuk`) |
| sahne | üretim | **birebir aynı** |
| `--t-end` | `1e-3` | `1e-3` |
| `--iz-every` | `2` | `2` |

### v1'de yanlış kurmuştum

v1'de E1b `--gozeneksiz` idi: `α₀ = 1`, `bulk_density = 2700`.
Uzmanın uyarısı: *"İlk kontrol kolunda `α₀=1` yapmayın. Şunları
aynı tutun: konumlar, kütleler, hızlar, `h`, başlangıç yoğunlukları,
başlangıç distansiyonları ve EOS. Yalnızca `α` güncellemesini
kapatın."*

Haklı: `α₀ = 1` sahneyi de değiştiriyor ve A27'de kol tam bu
yüzden kontrolsüz kalmıştı. Benim çözünürlük telafim (`s/1,20659`)
parçacık kütlesini eşitliyordu ama **konumları, `h`'yi ve komşuluk
yapısını** yine değiştiriyordu.

`--alpha-donuk` (bu turda eklendi) doğru kolu kuruyor:
`porosity.enabled=False` **ama üretim `alpha0` dizisi çözücüye
olduğu gibi gidiyor**. EOS hâlâ `P = P_katı(αρ, u)/α` kullanıyor;
yalnız `solver_solid.py:434`'teki ezilme güncellemesi durur —
distansiyon üretim değerinde **donar**.

Bu, *"gözeneksiz hedef"* deneyi **değil**; **geri dönüşsüz
kompaksiyonun etkisini** sınayan deney. Uzmanın dediği gibi
gerçek yoğun hedef karşılaştırması **ayrı** bir deneydir.

## Yargı — **şimdi kilitleniyor**

Ölçülen büyüklük: koşu boyunca `ρ_max` (hedef parçacıkları).
Eşik `ρ > ρ₀ᵏᵃᵗⁱ × 1,001 = 2702,7` — pay şart, çünkü `α₀ = 1`
kolunda başlangıç yoğunluğu **zaten** `2700`.

| E1a (üretim) | E1b (α donuk) | sonuç |
|---|---|---|
| `ρ_max ≤ 2702,7` | `ρ_max > 2702,7` | **Kompaksiyon şoku yutuyor.** α donduğunda katı sıkışıyor; ezilme serbestken sıkışmıyor. Kazı akışının yokluğunun sebebi geri dönüşsüz kompaksiyon. |
| `ρ_max > 2702,7` | `ρ_max > 2702,7` | Şok her iki hâlde de var; kompaksiyon onu **yok etmiyor**. Darboğaz başka yerde — sıradaki şüpheli **çekme** (uzmanın birinci adayı). |
| `ρ_max ≤ 2702,7` | `ρ_max ≤ 2702,7` | **Çözücü kusuru.** Ezilme dondurulmuşken bile katı sıkışmıyorsa sorun P-α'da değil. En ağır sonuç. |

**Not:** eşik `ρ > ρ₀ᵏᵃᵗⁱ × 1,001 = 2702,7`. Pay şart — gözeneksiz
kolda sayısal artık (`2700,1`) paysız sınavda `16 762` parçacığı
yanlışlıkla *"katı sıkışmış"* saymıştı.

### İkincil, yorum için (yargıyı değiştirmez)

- `t_zirve`: `ρ_max`'ın zamanı. Şoksa `~1e-4 s` olmalı.
- `sikisma_zirve / sikisma(0,2 s)`: boşalma oldu mu?
- `n_kati_sikisan(t)`: kaç parçacık, ne kadar süre.

## Geçersizlik koşulları

Şu hâllerde **hiçbir** sonuç okunmaz:

1. Koşu adım sınırına takılırsa (`ADIM SINIRINA TAKILDI`).
2. `ortak_bas.sh` tesisat sınavı düşerse (`exit 91`).
3. İki kolun parçacık kütlesi `%2`'den fazla ayrışırsa — telafi
   tutmamış demektir, A27 tekrarı olur. **Koşu çıktısında `m_p`
   yazdırılıyor; ilk kontrol bu.**

## Maliyet

`1e-3 / 5,4e-6 ≈ 185` adım. Ölçülen hız `≈ 2,8 adım/s` (R2).
Kurulum dâhil **kol başına `~15` dakika**. İki kol, tek dizi.
