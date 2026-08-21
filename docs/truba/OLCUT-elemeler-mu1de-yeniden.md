# A17 — bütün elemeler `μ ≈ 1`'de **yeniden** (2026-08-21, koşudan **önce**)

## Neden hepsi yeniden

Bugün ölçüldü: üretim çözünürlüğünde (`λ₂ = 2`, `μ = 80,4`) **şok
hedefe hiç girmiyordu** — `u_hedef/u_mermi = 0,0016`. `λ₂ = 6–8` ile
`μ ≈ 1–3`'e inilince oran `0,73` oldu.

Bunun sonucu geriye dönük ve ağır:

> **Bu projedeki bütün elemeler `μ = 80`'de yapıldı** — yani
> mekanizmanın **yok olduğu** rejimde. Bir şeyin etkisiz olduğunu,
> onun etki edeceği fiziğin hiç oluşmadığı bir koşuda ölçmek, bu
> deponun üç kez kaydettiği hatanın (*"ölçütü etkisiz olduğu yerde
> sınamak"*) ta kendisidir.

Etkilenen elemeler: **hasar** (`Δβ = 5,9e-6`), **matris `Y0`** (6
mertebe), **blok `Y0`**, **gözeneklilik**, **yerçekimi**, **süre**.
Hiçbiri `μ ≈ 1`'de sınanmadı.

## Neyi ölçüyoruz — `β` değil, **krater şekli**

`β` bu kolda karışık sinyal (`λ₂` ile `A1` de değişiyor) ve zaten
`t = 0,2 s`'de ejekta perdesi doğmamış oluyor. Ama **krater şekli**
`t = 0,2 s`'de zaten ölçülebiliyor (derinlik `13,6 – 16,5 m`, çap
`7,49 m`) ve dış kıyası **var**:

| | |
|---|---|
| literatür bandı (Melosh 1989) | `d/D = 0,15 – 0,30` |
| modelin bugünkü değeri | **`2,040`** — bandın `6,8` katı |
| π-ölçekleme çap aralığı | `13,3 – 85,6 m` |
| modelin çapı | `7,49 m` |

Yani **dışarıdan gelen, malzeme sabitlerinden bağımsız** bir ölçüt
var: model çanak açıyor mu, delik mi?

## Koşu — dört kol, `λ₂ = 8` (`μ = 1,26`), `t_end = 0,2 s`

Tek değişen malzeme; çözünürlük, tohum, `n_bins` (üretim `8`) ve
geri kalan her şey **aynı**.

| kol | ayar |
|---|---|
| **T** | üretim malzemesi (taban) |
| **H** | `--hasarli` |
| **Z** | `--Y0 1 --boulder-Y0 1` (zayıf) |
| **HZ** | `--hasarli --Y0 1 --boulder-Y0 1` |

## Ölçüt — **veriye bakılmadan**

### 1. Birincil — krater **şekli**

`d/D` (taban `2,040`, literatür üst sınırı `0,30`):

- herhangi bir kolda **`d/D <= 0,50`** -> o mekanizma **yanal akışı
  açıyor**; A17'nin kök nedeni bulunmuştur ve yol oradan gider.
- dört kolda da **`d/D >= 1,50`** -> bunların hiçbiri değil; eksik
  olan yapısal (ADR-0048 `M2`/`M3`) ve malzeme kolları **kapanır**.
- arası -> kısmi; kollar `d/D`'ye göre **sıralanır** ve en iyisi
  tek başına yeniden koşulur.

### 2. İkincil — çap

Çap `13,3 m`'yi (π-ölçeklemenin **en sert kaya** ucu) geçen kol,
birincil ölçütten bağımsız olarak kaydedilir.

### 3. Koruyucu

- Momentum kapanışı `< 1e-10`; koşu patlamamış olmalı.
- `u_hedef/u_mermi >= 0,5` her kolda **doğrulanmalı** — eşleşmenin
  hâlâ kurulu olduğu görülmeden şekil yargısı okunmaz.
- Zayıf kollarda (`Z`, `HZ`) cisim kendiliğinden dağılmamalı
  (`OLCUT-gercek-moloz-yigini.md` §3 koruyucusu geçerli).

## Bu koşunun karar **veremeyeceği** şey

`β`. `t = 0,2 s`'de ejekta perdesi yok; `β` bu kolda okunmaz.
Şekil düzelirse `β` ayrı ve **uzun** bir koşuyla ölçülür — ve
ADR-0048'in kama önerisi tam o koşu için.
