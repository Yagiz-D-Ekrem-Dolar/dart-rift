# KAYIT-055 — Şok doğuyordu, arayüzde ölüyordu; kademeli inceltmeyle geçti (2026-08-29)

**Kapsam:** A22 (düzeltildi) · A23 · A24 · A25 · ADR-0049
**Öncül:** [KAYIT-054](KAYIT-054_2026-08-29_sok-doguyor-aktarim-siliyor.md)
**Koşular:** yerel RTX 3050

---

## 1. Başlangıç: kendi bulgumu çürüttüm

Tur, A22'nin *"model şok üretmiyor"* yargısıyla açıldı. **Yanlıştı.**

A22 iki **karışık** noktadan (`tek aşama λ = 2` ve `iki aşama
λ₁ = 38`) `sıkışma ~ A1^0,92` çıkarmış ve *"Hugoniot için `A1 ≈ 64`,
`~55 gün`"* demişti. Tek düzenekte, tek değişkenli tarama koşuldu —
ve şok mikro-saniyede kurulduğu için `t_end = 1e-3 s` yetti:
**dört kol, dakikalar.**

| `λ₂` | `s` | `r_mermi/h` | sıkışma max | artış (üs) |
|---|---|---|---|---|
| `2` | `3,500` | `0,053` | `%0,0057` | — |
| `8` | `0,875` | `0,212` | `%1,683` | `296×` (`4,10`) |
| `20` | `0,350` | `0,531` | `%22,024` | `13,1×` (`2,81`) |
| `40` | `0,175` | `1,061` | **`%40,521`** | `1,8×` (`0,88`) |

A22'nin yasası `λ₂ = 20` için `%0,047` derdi; ölçülen `%22,02` —
**`470` kat** yanlış. Ve üs `4,10 -> 0,88` ile **doyuma** gidiyor:
fiziksel tavana yakınsama imzası, doyum `r_mermi/h ≈ 1`'de.

**Bağımsız sınav:** ölçülen tepe sıkışma `%22,02` -> Rankine-Hugoniot
`Us = 3 565 m/s`. Cephe `1e-3 s`'de `3,41 m` gitmiş -> `3 410 m/s`.
Sapma **`%4,3`**. İki sayı birbirine uydurulmadı.

## 2. A24: aktarım ısıyı taşıyıp sıkışmayı atıyordu

Üretim aşama-1'i `s = 0,368 m`'de koşuyor — yani şok **üretiyor**
olmalı. Ölçüldü: `%26,08` sıkışma, `72 936 kg`, kütle kesri
`1,750e-5`. Deftere `t₁`'de yazılan sayı: **`1,81e-5`**. Aynı şey.

> Üretim aşama-1 şok üretiyordu. Ben o kaydı *"şok yok"* diye
> okumuştum.

Kod düzeyinde kesin: `solver_solid.py:139` `ρ`'yu **her zaman**
`ρ₀/α₀` ile kuruyordu ve `_cozucu`'nun `rho` parametresi **yoktu**.
`u` taşındığı için aşama-2 **sıcak ama sıkışmamış** — şoklanmış madde
için olanaksız — bir durumla başlıyordu. A22'nin *"sıkışmadan ısınan
madde"* belirtisi tam olarak buydu.

**Çare:** hacim korunumlu (harmonik) aktarım. Kütle-ağırlıklı düz
ortalama **yanlış** olurdu: yoğunluk `m/V`, birleşen parçacıklar hem
kütleyi hem **hacmi** korumalı. `11` test.

## 3. A25: şok, inceltmenin kendi ördüğü duvara çarpıyor

Cephe `3,41 m`'de **hızı `0,0 m/s`** ile duruyordu. Sebep:

| kabuk | kütle medyan |
|---|---|
| `0 – 3,5 m` | `46,6 kg` |
| **`3,5 – 4,0 m`** | **`372 834 kg`** |

**Arayüz oranı `8 000`** — KAYIT-053'ün `μ = 80`'inin `100` katı.
Ve inceltme arttıkça **kötüleşiyor** (`λ = 40` -> `64 000`): şoku
doğuran şey aynı anda onu hapsediyor.

### Kullanıcının teşhisi bunu keskinleştirdi

Kütle parmak izi sınandı ve **her iki zamanda da** tuttu:

| `t` | şoklanan | ince | **kaba** | `n × 46,6043` | ölçülen |
|---|---|---|---|---|---|
| `1e-3` | `1 306` | `1 306` | **`0`** | `60 865,2` | `60 865,2` |
| `4,767e-3` | `1 565` | `1 565` | **`0`** | `72 935,7` | `72 935,7` |

Yani `3,41 m` bir **cephe değil** — ince parçacıkların dışarı
taşınmış kenarı. Benim *"cephe duruyor"* ifadem düzeltildi.

Ve `h_ij = (h_i + h_j)/2 = 7,35 m` -> destek `14,70 m`, şoklanan
bölgenin (`3,41 m`) **`4,3` katı**. Aynı `h_ij` yapay viskozitede de
kullanılıyor; dar şok darbesi `14,7 m`'ye yayılıp siliniyor.

### Ve asıl sınır kütle oranı **değil**

Destekteki ince parçacık sayısı `(2h_kaba)³`, gereken kütle
`s_kaba³` — ikisi aynı oranda büyüdüğü için pay **basamak
boyutundan bağımsız** (`189,6×`). Düşüren şey **geometri**: kaba
desteği `4 × 7,0 = 28 m`, ince bölge `3 m`. Destekte `1,5` milyon
ince parçacık gerekiyordu; `1 828` vardı.

> **Ölçüt:** her seviyenin kabuğu en az `~4 s` kalın olmalı.

Bu, koşmakta olduğum merdivenin kusurunu **koşu sırasında** ortaya
çıkardı (dış üç kabuk `1,4 – 2,1 s`).

## 4. Çare ölçüldü: **işliyor**

| ölçü | tek basamak | **merdiven** |
|---|---|---|
| şoklanan **seviye** | `1` | **`3`** |
| kaba seviyelerde şoklu | **`0`** | **`2 983`** |
| şoklanan kütle | `72 936 kg` | **`240 905 kg`** |
| sıkışma max | `%26,08` | **`%45,18`** |

Hugoniot bandının alt ucu `%45,6`. Model şoku artık **doğru
değerde** üretiyor *ve* ızgarada taşıyor. Bedeli: **`%13` parçacık**,
`dt` değişmiyor.

## 5. Bu turda **kendi hatalarım**

- A22'nin `55 gün`'ü: karışık iki noktadan üs yasası. `470` kat yanlış.
- *"Cephe `3,41 m`'de duruyor"*: cephe değil, ızgara sınırı.
- Kilitlediğim H1 kuralı tek yönde **sınanamazdı** (artışın hızlanması
  Hugoniot tavanı yüzünden olanaksızdı); kendi kuralımla düştü.
- Komşu çölü hipotezi: ölçüldü, **yok** (boşluk `0,02 m`).
- Merdivenin kabuk kalınlığını gözden kaçırdım; koşu sırasında yakaladım.
- Arka plan kuyruk kapısı (`pgrep -f`) **sessizce açık kaldı**: dört iş
  saatlerce aynı kartta yarıştı ve bir koşuyu iki kez başlattım.

## 6. Ne **yapılmadı**

- `β` bu turda **hiç ölçülmedi** (bilerek: `t ≤ 6e-3 s`'de kazı akışı yok).
- Şokun **yayılması** için gereken bağıl çözünürlük (`r/s`) ölçülmedi;
  ölçüt yazıldı, kol sırada.
- A24'ün A/B kıyası koşulmadı (kuyrukta).
- ADR-0046, 0047, 0048, 0049 kararları kullanıcıda.
