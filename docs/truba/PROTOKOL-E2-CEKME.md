# Protokol E2 — matris çekmede mi bağlı kalıyor

**Yazıldı:** 2026-09-06, **koşudan önce** · **Dayanak:** rapor A51
**Kaynak:** dış uzman incelemesi (2026-09-05), *birinci* hipotez

---

## Neden

`Y₀` **yalnız deviatorik** gerilmeyi sınırlıyor; Tillotson'un
negatif hidrostatik dalını sınırlamıyor. Ölçüldü (A51):
`u = 0`, `α = 1,7564`, `ρ_katı = 0,999 ρ_katı⁰` için
**`P = −1,518635e+07 Pa`** ve bu değer `Y₀ = 1 Pa` ile
`Y₀ = 1e8 Pa` arasında **yedi haneye kadar aynı**.

Yani *"zayıf matris"* kollarımız zayıf değildi: `1 Pa` kohezyonlu
matris hâlâ `−15 MPa` çekme taşıyordu. Sağlam kayanın çekme dalı
granüler malzemeye uygulanıyor.

Bu, hem `Y₀` duyarsızlığını (A17, A45) hem kraterin **kapanmasını**
(`1,0409 → 1,0322 m`) açıklayabilir.

## Tasarım

| | E2a — üretim | E2b — **çekme kırpılmış** |
|---|---|---|
| matris `P < 0` | olduğu gibi | **`0`'a kırpılır** (`--matris-cekme-yok`) |
| bloklar, mermi | değişmez | **değişmez** (sağlam kaya; çekme dalı fiziksel) |
| AV, basma basıncı, kayma dayanımı, kompaksiyon | üretim | **üretim** |
| `--t-end` | `0,024` | `0,024` |
| `--iz-every` | `20` | `20` |

Kırpma EOS'un **hemen ardında** yapılıyor; böylece kuvvet terimi
`t = (S − P I)/ρ²` ve enerji işi `du` **aynı** etkin basıncı görüyor.
Uzmanın şartı buydu.

### Uzmanın tasarımından bilerek ayrıldığım nokta

Uzman `8 ms`'te ortak durumdan **dallanmayı** öneriyor, ki şok
evresi iki kolda birebir aynı kalsın. Depoda yeniden başlatma
düzeneği yok ve onu kurmak deneyi geciktirir.

Bunun yerine iki kol **`t = 0`'dan** koşuyor — tek değişkenli, ama
şok evresi de etkilenebilir. Bu karışıklığı **ölçerek** kapatıyorum:
her iki kolda `ρ_max`, `sikisma_max` ve `n_kati_sikisan` izleniyor
(E1'in aracı). Şoklar örtüşüyorsa akış farkı çekmeye atfedilebilir.
**Örtüşmüyorsa bu deney sonuçsuzdur ve dallanmalı sürüm gerekir.**

## Yargı — **şimdi kilitleniyor**

Karar `r > R` sayısıyla **verilmiyor** (uzmanın uyarısı: `v_esc`'e
yakın parçacık `0,2 s`'te `1,64 cm` gider, aralık `17,5 cm`).
Karar şu üç nicelikle:

1. **`v_r` dağılımı**, çarpma noktasının `3 m` yakınındaki matris
   parçacıklarında — medyan ve `p95`.
2. **Kaçış hızını aşan hedef kütlesi**, `r > R` şartı **olmadan**
   (`M(>v)` alt bandı).
3. **Krater derinliğinin gidişi** — hâlâ kapanıyor mu.

| gözlenen (şoklar örtüşmek koşuluyla) | sonuç |
|---|---|
| E2b'de `v_r` p95 belirgin artıyor **ve** krater kapanması duruyor | **Çekme hipotezi destekleniyor.** Kazıyı durduran kuvvet bulundu. |
| İki kol ayırt edilemiyor | Çekme **baskın neden olarak elenir**; sıradaki şüpheli kompaksiyon (E1). |
| Fark yalnız birkaç kaba parçacıktan geliyor | **Sonuçsuz** — arayüz/çözünürlük belirsizliği sürüyor (A25 sınıfı). |

## Ne DEĞİL

Bu, üretim modeline önerilen bir basınç kırpması **değildir**.
Granüler malzemenin basınca bağlı sürtünmesini modellemez. Uzmanın
cümlesiyle: *"hangi kuvvetin kazıyı durdurduğunu ayıran kontrol
deneyidir."*

Gerçek çözüm — eğer hipotez tutarsa — granüler bir çekme/sürtünme
davranışıdır ve **ayrı bir tasarım kararıdır** (ADR).

## Geçersizlik koşulları

1. Adım sınırına takılma (`ADIM SINIRINA TAKILDI`).
2. Tesisat sınavı düşerse (`exit 91`).
3. İki kolun `ρ_max` gidişi ayrışırsa → sonuçsuz (yukarıda).

## Maliyet

`0,024 / 5,4e-6 ≈ 4 450` adım, ölçülen `≈ 2,8 adım/s` →
**kol başına `~27` dakika**. İki kol, tek dizi.

---

# Ek: E3 — yapay viskozite kolu (rapor A53)

**Eklendi:** 2026-09-06, **koşudan önce**

## Neden kampanyaya girdi

`L2` kolları `⟨v⟩ = P_kaçan/M_kaçan` ile yeniden okunduğunda:

| kol | `M_kaçan` | `⟨v⟩` |
|---|---:|---:|
| taban | `93,21 kg` | **`−1264 m/s`** (jet) |
| `α_av 0,1` | **`12 303 kg`** | **`−0,397 m/s`** (**kazı akışı**) |

Yani viskoziteyi düşürünce **akış ortaya çıkıyor**. Bu, üç aday
içinde **doğrudan olumlu kanıtı olan tek aday**.

## Kollar

| kol | `α_av` | `β_av` |
|---|---:|---:|
| `E2a` (aynı zamanda AV tabanı) | `1,0` | `2,0` |
| `E3o_av_orta` | `0,4` | `0,8` |
| `E3_av_dusuk` | `0,1` | `0,2` |

## Yargı — **şimdi kilitleniyor**

Ölçülen: `M_kaçan`, `⟨v⟩`, `Δβ_hedef` ve **kaçan kütlenin inceltme
seviyesi dağılımı** (`ejekta_seviyeleri`).

| gözlenen | sonuç |
|---|---|
| `⟨v⟩` üç noktada **düzgün** azalıyor (`α_av` ile monoton) | AV gerçek bir **kontrol parametresi**; mekanizma sürekli |
| `⟨v⟩` yalnız `0,1`'de sıçrıyor, `0,4`'te taban gibi | **eşikli** → sayısal artefakt şüphesi güçlü |
| Akış hâlâ **yalnız kaba seviyeden** | **Sonuçsuz** — çözünürlükte yaşamıyor |

## Neden asıl sınav yapılamıyor

Doğru sınav, `E3`'ü **bir kademe ince** merdivenle tekrarlamaktı.
A52 yüzünden `107` saat sürerdi (sınır `24`). Bu yüzden burada
**AV taramasıyla** yetiniliyor ve çözünürlük sorusu **açık kalıyor**.

> Bu, A52'nin çare bekleyen ikinci maliyeti: `R3` bitemedi,
> `E3i` kurulamadı.
