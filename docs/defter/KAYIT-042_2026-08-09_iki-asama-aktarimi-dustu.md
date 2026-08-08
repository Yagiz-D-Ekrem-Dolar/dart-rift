# KAYIT-042 — FAZ 4.4 tamam; iki aşamalı **aktarım** düştü (2026-08-09)

**Kapsam:** FAZ 4.4 · ADR-0043 §7 madde 1–2 · **Durum:** FAZ 4.4 **bitti**,
ADR-0043 **kilitlenemez**
**Öncül:** [KAYIT-041](KAYIT-041_2026-08-08_yerel-gpu-ve-mermi-cozulmemis.md),
[ADR-0043](../adr/ADR-0043-iki-asamali-cozunurluk.md)

---

## 1. FAZ 4.4 **tamamlandı** — altı kol, **aynı** simüle sürede

`--t-end` düzeltmesi (sıkıntı A6) çalıştı. Önceki koşuda kollar farklı
`t_sim`'e gidiyordu (A′ `0,342 s`, tek-`h` `0,694 s`) ve `B1`/`B3`
hesaplanamıyordu. Şimdi **altısı da** tam `2,0000e-01 s`:

| kurulum | A′ `β` | tek-`h` `β` | duvar (A′ / tek-`h`) |
|---|---|---|---|
| `s7_λ2` | 1,583620 | 1,553731 | 418,8 / 225,6 s |
| `s7_λ3` | 1,605748 | 1,561803 | 2423,5 / 644,7 s |
| `s5_λ2` | 1,607102 | 1,591140 | 1654,4 / 876,5 s |

### G4 kapısı — **iki ölçüt daha** ölçüldü

| | ölçüt | eşik | ölçülen | |
|---|---|---|---|---|
| A1 | mermi çapı / yerel aralık | `≥ 2` | **0,2146** | **DÜŞTÜ** |
| A2 | `r_ince / R_mermi` | `≥ 3` | 66,56 | GEÇTİ |
| A3 | ek yerinde kütle sapması | `< 0,005` | 3,48e-04 | GEÇTİ |
| **B1** | ardışık çözünürlükte `β` farkı | `< 0,1` | **8,43e-04** | **GEÇTİ** ✱ |
| **B3** | A′, tek `h`'den ince kola yakın | `= 1` | **1** | **GEÇTİ** ✱ |
| B2, B4, C1, C2, C3 | | | — | koşulmadı |

✱ = bu turda yeni. **Sonuç hâlâ `GEÇİLEMEDİ`** — düşen: `A1`.

> `B1 = 8,4e-04` eşiğin `119` katı altında. Ama bu **`A1` düşerken**
> ölçüldü: mermi çözülmemişken `β` çözünürlükle değişmiyor olması,
> yakınsamanın **kanıtı değil** — üç kurulum da aynı çözülmemiş
> mermiyi çözüyor olabilir. Kapı bunu ayrı bir ölçütle (`A1`) zaten
> yakalıyor; not düşülüyor ki `B1` tek başına okunmasın.

---

## 2. ADR-0043 madde 1: **`t₁` ölçüldü** — tahminin 4,8 katı

`u = |⟨v⟩_mermi − ⟨v⟩_yakın hedef| / v_çarpma`, `λ=19`, `A1 = 2,04`.

| | |
|---|---|
| `u` en düşük | `0,1177` (`t = 3,7e-4 s`) |
| `u` **plato** | `0,4093` |
| durulma penceresi | `[0,0353 , 0,0500] s`, 28 nokta |
| eğim kayması / yarım-pencere | `%0,067` / `%0,035` (tol `%2`) |
| **`t₁`** | **`4,767e-3 s`** (ADR tahmini `1e-3 s`) |
| bedele etkisi | `+%0,9` → **`+%4,7`** (10,19 vs 9,73 GPU-günü) |

**Bu kalemde öneri ayakta.** `%4,7` bütçenin çok altında.

### Ama **ölçütün tanımı** yanlıştı

*"`u → 0`"*, *"mermi hedefle aynı hıza gelince bağlanma biter"*
yazmıştım. `u` sıfıra **inmiyor** — `0,409`'da düzleşiyor ve oraya
*aşağıdan*, `0,118`'den **yükselerek** geliyor (92 adımın 16'sı artış).

Doğrusu: momentum alışverişi bitince iki topluluk balistikleşir ve fark
**sabitlenir**; sabitlendiği **değerin** sıfır olması gerekmez. Mermi
maddesi geri saçılırken hedef maddesi ileri gider.

> Eşiği değil **tanımı** yanlış yazmak daha sinsi: yanlış tanım, ölçüm
> yapılsa bile yanlış sonucu *doğru* gösterir. Burada kurtaran şey
> ham izi **çizip bakmak** oldu, sadece `durulmuş = True`'ya değil.

---

## 3. ADR-0043 madde 2: korunum **geçti**, aktarım **düştü**

`coarsen.py` yazıldı. Atama bir **bölüntü**, `v_k` kütle-ağırlıklı,
ortalamada kaybolan kinetik iç enerjiye ekleniyor.

### Korunum — §5'in istediği

| `t₁` [s] | kütle | momentum | enerji |
|---|---|---|---|
| `1e-4` | 3,9e-14 | 2,8e-16 | 1,8e-16 |
| `1e-3` | 3,9e-14 | 3,4e-15 | 5,7e-16 |
| `4,77e-3` | 3,9e-14 | 1,0e-15 | 7,4e-16 |
| `1e-2` | 3,9e-14 | 6,1e-15 | 1,5e-15 |

Reddedilen naif yol da **ölçüldü**: ağırlıksız ortalama momentumun
**`%38`**'ini kaybediyor. §5 bunu *iddia* ediyordu; artık **gösteriliyor**.

### Düşen: ADR'nin ölçmeyi istemediği iki tanı

| `t₁` [s] | ısıya dönen | **atama mesafesi** |
|---|---|---|
| `1e-3` | `%93,2` | `0,97` hücre |
| **`4,77e-3`** | **`%99,3`** | **`4,35` hücre** |
| `1e-2` | `%99,9` | **`10,16` hücre = 35,6 m** |

> **`t₁`'in iki şartı çelişiyor.** Bağlanma bitsin diye **büyük**
> olmalı (`4,77e-3 s`); aktarım maddeyi ışınlamasın diye **küçük**
> olmalı (`≤ 1e-3 s`). **Aralık boş.**

`r_iç`'i büyütmek çözmüyor — ölçüldü:

| `r_iç` | aşama-1 `N` | site | ince/site | toplam | `λ=2`'ye göre |
|---|---|---|---|---|---|
| 3 m | 11 871 | 2 | 1164 | 10,19 | +%4,7 |
| 6 m | 22 555 | 14 | 930 | 10,60 | +%8,9 |
| 9 m | 51 359 | 51 | 820 | 11,71 | +%20,4 |
| 12 m | 106 275 | 120 | 806 | 13,83 | +%42,1 |

Sıkıştırma `~857`'de **sabit** — tanım gereği `(λ₁/λ₂)³ = 9,5³`.
`r_iç` yalnızca **bedeli** büyütüyor.

### Kusur tanımlanabilir, dolayısıyla ADR ölmedi

Hedef siteler aşama-2'nin **başlangıç** kafesinden alınıyor — yani
**Euler**'ci, maddenin peşinden gitmiyor. **Lagrange**'cı bir sürüm
(`t₁` anındaki bulutun üzerine oturtulan `s₂` kafesi) çalışabilir.
**Yazılmadı, ölçülmedi**; ADR-0043 §7'ye madde 5 olarak eklendi.

---

## 4. Bu turda bulunan **kendi** kusurlarım

| # | kusur | nasıl bulundu |
|---|---|---|
| 25 | `refine.py`'de **iki** `N×M×3` bellek bombası (`36,8 GiB`) | `r_iç` taraması patladı |
| 26 | kabalaştırmanın hedef kafesi yanlıştı (kaba, ince olmalıydı) | **CPU ön uçuşu**, GPU'ya gitmeden |
| 27 | açısal momentum `\|L₀\|`'a bölünüyordu; merkezi çarpmada anlamsız | `%72 870` okununca |
| — | 27'nin **testinin fikstürü** de kusurluydu (`L₀ = 4` çıktı) | testin kendi iddiası tutmadı |

### `N×M×3` kalıbı **üçüncü kez**

`412 TiB` (`refine_scene_local`), `9,4 GB` (α₀ komşu araması),
`36,8 GiB` (`_dikiş_kalitesi`). Üçüncüsünün yorumu *"kuşak küçük
(yüzlerce)"* diyordu — `λ=2`'de **doğruydu**, `λ=19`'da çöküyor.

> Kural: `x[:, None, :] - y[None, :, :]` **asla** parçasız yazılmıyor.
> `coarsen.py` bu kuralla yazıldığı için oraya sızmadı.

---

## 5. Ne değişti, ne değişmedi

| | |
|---|---|
| FAZ 4.4 | **bitti** — altı kol, eşit `t`, `B1`/`B3` ölçüldü |
| G4 | hâlâ **`GEÇİLEMEDİ`**; düşen yalnızca `A1` |
| ADR-0043 madde 1 | ✔ ölçüldü (`t₁ = 4,767e-3 s`) |
| ADR-0043 madde 2 | ✔ ölçüldü — **geçti**, ama **madde 5'i doğurdu** |
| ADR-0043 madde 3, 4, 5 | **ölçülmedi** |
| ADR-0043 durumu | **ÖNERİLDİ** — kilitlenemez |
