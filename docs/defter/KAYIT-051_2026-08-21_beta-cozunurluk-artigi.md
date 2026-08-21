# KAYIT-051 — `β` çözüldü: sekme bir ayrıklaştırma artığı, hedef ejektası **yok** (2026-08-21)

**Kapsam:** A17 · A12 · G4-B1
**Öncül:** [KAYIT-050](KAYIT-050_2026-08-21_boulder-Y0-hic-taranmadi.md)
**Koşular:** **yerel RTX 3050** — TRUBA çalışma alanına erişilemiyor

---

## 1. Yerel makine referansı **birebir** tutturuyor

TRUBA erişimi kapalı olduğu için bütün tur bu dizüstünde koştu.
Karşılaştırılabilirlik önce sınandı:

| | TRUBA / kayıtlı | **yerel** |
|---|---|---|
| iki aşamalı `β` | `1,411216` | **`1,411216`** |
| `A1` | `2,0391` | `2,0391` |
| aktarım momentum hatası | `8,76e-15` | `8,76e-15` |
| tek aşamalı `β` | `1,6175832076207557` | **`1,617583208`** |

`t_end = 0,2 s`'lik iki aşamalı koşu **`14` dakika**. Yani A17'nin
elemeleri TRUBA **olmadan** sürdürülebiliyor.

---

## 2. Üç hipotezim de çürüdü — üçü de ölçütü **önce** yazarak

### 2a. Hasar (ADR-0027) — **elendi**

`configs/p3_dimorphos.yaml` `damage.enabled: true` diyor;
`faz44_dart_yakinsama._malzeme()` — FAZ 4'ün **bütün** koşularının
malzemesi — `enabled=False`. ADR-0027 bunun `β`'yı küçülteceğini
`2026-08-01`'de yazmıştı.

İlk çift **geçersiz** çıktı (tesisat: `D_max = 0`). Tanı: hasar
oluşuyor ama **aktarım taşımıyor** — aşama-1'de `t₁`'de
`D_max = 0,562`, aktarımdan sonra `0`. Taşıma eklendi (`Sum m D`
hatası `0,000e+00`, altı gerileme testi).

Karar tek aşamalı kolda verildi (aktarım yok):

| | `β` | `D_max` | tam kırık |
|---|---|---|---|
| hasar **kapalı** | `1,617583208` | `0` | `0` |
| hasar **açık** | `1,617592767` | `1,0000` | `3` |

`|Δβ| / β = 5,9e-6` -> ölçütün *"`< %1` ise sebep değil"* dalı.

> ADR-0027 haklıydı ama **ölçekte değil**: `11 183` parçacığın
> **`3`'ü** tam kırılıyor, ortalama `D = 2,8e-4`. Doğrulanmış
> (32 testli) bir modül `3,5 m`'lik parçacıkta fiilen **etkisiz**.

### 2b. Aktarımın durum sıfırlaması — **iddiamı geri aldım**

*"Aktarım `rho`, `alpha`, `S`'yi sıfırlayarak hasar kolunu
kirletiyor"* demiştim. Ölçtüm: ezilme sıfırlanan kütle payı
`1,33e-3`, `rho` `%1`'den sapan `1,81e-5`, ince bölge dışında
`|S|` medyanı `1,79 Pa` (`Y0 = 1e4`). Sıfırlama **gerçek ama ince
bölgeyle sınırlı**. *"Kirletiyor"* demem fazlaydı.

### 2c. *"Mermi soğuk sekiyor"* — **çürüdü**

| | ölçülen |
|---|---|
| `u_kaçan` (kütle ağırlıklı) | `5,613e6 J/kg` = **`1,19 x u_iv`** |
| gelen özgül `KE` | `1,888e7 J/kg` |
| iç enerjiye dönen | **`%29,7`** |
| sahnedeki **en yüksek** `u` | `5,644e6` — ve o **merminin** üstünde |

Kaçan madde erime eşiğini geçmiş, yani sekme soğuk elastik bir yapay
değil. Ama merminin enerjisinin `%70`'i kinetik kalıp geri çıkıyor ve
**sahnedeki en sıcak parçacık merminin kendisi**: hedef güçlü bir şok
hiç görmüyor.

---

## 3. Karar: `β` **mermi çözünürlüğünde yakınsamamış**

Tek değişen `λ₁`:

| `λ₁` | `A1` | `β` | `n_ejekta` |
|---|---|---|---|
| tek aşamalı (`λ = 2`) | `0,215` | `1,617583` | `803` |
| `19` | `2,039` | `1,411216` | `28` |
| **`38`** | **`4,078`** | **`1,185066`** | `40` |

`Δβ = -0,226150` (**`%16,0`**) -> ölçütün `%10` dalı.

> Yön **gözlemden uzağa**. Mermi çözüldükçe sekme zayıflıyor; sekme
> `β`'nın **tamamı** olduğu için `β` düşüyor. Ardışık farklar
> `-0,206` ve `-0,226`: azalma **yavaşlamıyor**. Limit `3,2225`
> değil, **`β -> 1`**.

### Bu `G4-B1`'i düşürüyor

| tarama yönü | `Δβ` | eşik `0,1` |
|---|---|---|
| `λ₂` `2 -> 4` (**hedef**) | `0,000843` | geçti |
| `λ₁` `19 -> 38` (**mermi**) | **`0,226150`** | **düştü** (`268` kat) |

`B1`'in *"gözlenebilirler yakınsıyor"* yargısı `β`'yı **üreten**
yönde hiç sınanmamıştı.

---

## 4. A17'nin cevabı

`β = 1,41` bir fizik sonucu değil, **çözülmemiş bir çarpışmanın
artığı**. Çözünürlük arttıkça küçülüyor ve altından hedef ejektası
**çıkmıyor** — çünkü hiç yok (hedef payı her koşuda tam `0`).

Gözlemin `3,2225`'i için eksik olan bir parametre değil, hedef
maddesini fırlatan **mekanizmanın kendisi**. Ölçüm tarafı kapandı;
kalan bir **ADR kararı**.

---

## 5. Bu turda ne **yapılmadı**

- `λ₁ = 55` üçüncü noktası koşuyor; bu kayıt onsuz yazıldı.
- `boulder_Y0` hâlâ hiç taranmadı (KAYIT-050).
- A11 ve A12'ye dokunulmadı; ADR-0046'nın kapsam kararı kullanıcıda.
