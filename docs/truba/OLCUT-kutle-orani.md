# A17 — `β` eksikliği bir **kütle oranı** sorunu mu? (2026-08-21, koşudan **önce**)

## Ölçülen belirti

Tek aşamalı kontrol kolunun son durumundan (`t = 0,2 s`):

| | ölçülen |
|---|---|
| merminin en sıcak parçacığı `u_mermi_max` | `5,6445e6 J/kg` |
| **hedefin** en sıcak parçacığı `u_hedef_max` | **`8 993 J/kg`** |
| oran | **`0,0016`** |

Hedefin en sıcak parçacığı, merminin **binde 1,6**'sı kadar iç enerji
taşıyor. `6,1 km/s`'lik bir çarpmada hedefin çarpma noktası
`1e6 – 1e7 J/kg` mertebesine çıkmalı; `9e3` çıkıyor — **üç mertebe**
eksik.

> Şok hedefe **girmiyor**. `β`'nın hedeften beslenmemesi bunun
> sonucu; sebep değil.

## Hipotez: uzunluk değil **kütle** oranı

Bugüne kadarki bütün çözünürlük ölçütleri **uzunluk** ölçütüydü.
`A1 = mermi çapı / yerel aralık ≥ 2` geçiyor (`2,039`) ama o ölçüt
merminin **aşama-1** ızgarasında çözülüp çözülmediğini soruyor.

Aktarımdan sonra mermi aşama-2 ızgarasında ilerliyor ve orada
ölçülmesi gereken şey **kütle**. Ölçüldü (sahne kurulumu, `r ≤ 15 m`,
üretim `r_ince2 = 25 m`):

| `λ₂` | `s_ince` | hedef parçacığı | **`μ = m_hedef / m_mermi`** | `N` |
|---|---|---|---|---|
| **2** (üretim) | `3,50 m` | `4,66e4 kg` | **`80,4`** | `10 413` |
| 4 | `1,75 m` | `5,83e3 kg` | `10,1` | `10 880` |
| 6 | `1,17 m` | `1,73e3 kg` | `2,98` | `35 959` |
| 8 | `0,875 m` | `7,28e2 kg` | **`1,26`** | `71 134` |
| `μ = 1` için | `≈ 0,81 m` | — | `1,00` | — |

Mermi (`579,4 kg`), üretimde kendisinden **`80` kat ağır tek bir
parçacığa** çarpıyor. Böyle bir çarpışmada momentumun büyük kısmının
geri sekmesi **beklenen** davranıştır — ve ölçülen tam bu.

Bu, `λ₁` taramasının `β`'yı neden **düşürdüğünü** de açıklıyor:
`λ₁` mermiyi inceltiyor, hedefi değil; oran daha da bozuluyor.

## Koşu

Üç kol, tek değişen `λ₂`, gerisi **üretim** (`λ₁ = 19`, `r₂ = 25 m`,
`spacing = 7`, `t_end = 0,2 s`, tohum aynı):

| kol | `λ₂` | `μ` | `N` |
|---|---|---|---|
| F6 | 6 | `2,98` | `35 959` |
| F8 | 8 | `1,26` | `71 134` |
| F12 | 12 | `0,37` | `~240 000` |

Taban zaten var: `λ₂ = 2`, `β = 1,411216`, `u_hedef/u_mermi = 0,0016`.

## Ölçüt — **veriye bakılmadan**

### 1. Birincil — şok hedefe **giriyor mu**

`u_hedef_max / u_mermi_max`:

- **`>= 0,5`** (`μ ≲ 1`'de) -> şok hedefe geçiyor; eşleşmeyi **kütle
  oranı** yönetiyor ve A17'nin mekanizması budur.
- **`< 0,05`** (`μ = 0,37`'de bile) -> kütle oranı da değil; eşleşme
  başka bir şeyle bozuk ve hipotez **çürür**.
- arası -> kısmi.

Bu ölçüt `β`'ya bağlanmadı **bilerek**: `λ₂` büyüyünce `A1` de
artıyor ve o `β`'yı `1`'e iter (ölçüldü, `λ₁` taraması). `β` bu
kolda **karışık sinyal**; iç enerji değil.

### 2. İkincil — `β` ve hedef ejektası

- `β` ve kaçan **hedef** kütlesi kaydedilir. Birincil ölçüt geçer
  **ve** `β` yükselirse sonuç güçlenir; birincil geçip `β` düşerse
  bu, `A1` etkisinin baskın olduğu anlamına gelir ve ayrı bir kol
  (`λ₁` sabit tutulamıyor) gerekir.

### 3. Koruyucu

- Momentum kapanışı `< 1e-10`, koşu patlamamış olmalı.
- `A1` her kolda kaydedilir; `λ₂` ile birlikte arttığı **görünmeli**
  ki karışık sinyal gizlenmesin.

## Bu koşunun karar **veremeyeceği** şey

`μ ≈ 1` çözünürlüğü **üretim çözünürlüğü değil** ve ensemble maliyeti
ayrı bir karardır (ADR-0043 `λ₂ = 2`'yi seçmişti). Burada sınanan tek
şey **mekanizma**: şokun hedefe geçmesini kütle oranı mı belirliyor.
