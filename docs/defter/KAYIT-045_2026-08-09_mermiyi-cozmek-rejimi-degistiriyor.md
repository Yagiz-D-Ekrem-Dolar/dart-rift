# KAYIT-045 — Mermiyi çözmek **rejimi** değiştiriyor (2026-08-09)

**Kapsam:** ADR-0043 §4f/§4g · FAZ 4.8 · rapor A11/A12
**Durum:** `A1` artık **geçilebilir** ve geçmenin **fark yarattığı** ölçüldü
**Öncül:** [KAYIT-044](KAYIT-044_2026-08-09_gate-6-7-ve-iki-asama-kuruldu.md)

---

## 1. Ana sonuç

Üç kol, aynı `t_end = 0,2 s`, aynı tohum:

| kol | `A1` | `β` | **`n_ejekta`** | momentum kapanışı |
|---|---|---|---|---|
| tek aşama (`λ=2`) | 0,2146 | 1,617583 | **803** | 1,36e-14 |
| iki seviyeli *(geçersiz)* | 2,0391 | 1,412659 | 32 | **6,90e-01** |
| **üç seviyeli** | **2,0391** | **1,411216** | **28** | **1,31e-14** |

**`803` merminin parçacık sayısının tamamı.** Çözülmemiş mermide
**bütün mermi sekip kaçıyor**; çözülmüşte yalnızca `28` — mermi
**gömülüyor**.

> `%12,8`'lik bir `β` farkı değil, **rejim değişikliği**:
> *"tamamen seken top"* → *"gömülen mermi"*.

`A1 ≥ 2` eşiği böylece **ölçümle** desteklendi: altında ve üstünde
farklı fizik var. ADR-0043 §6'nın *"eşiği düşürmek eşiği boşaltmaktır"*
gerekçesi artık gerekçeden fazlası.

---

## 2. `A1`'in doğru ifadesi: `h` merminin `9,3` katı

| | `λ = 2` | `λ = 19` |
|---|---|---|
| mermi çapı | 0,7512 m | 0,7512 m |
| mermi `h` | **7,0000 m** | 0,7368 m |
| **`h` / çap** | **9,32** | **0,98** |

`λ = 2`'de bütün mermi **tek bir yumuşatma uzunluğunun içinde**. SPH
onu katı mermi değil, çapının `9` katına yayılmış **seyrek bulut**
gibi görüyor; temas basıncı `~10³` kat düşük kalıyor.

ADR-0028 bu davranışı *"mermi `20 kg/m³`, köpük top gibi sıçrıyor"*
diye açıklamıştı. Mermi artık **`2610 kg/m³`** — gerçekçi — ve **aynı
şey** oluyor. **Sebep yoğunluk değil, çözünürlük.**

---

## 3. Şemanın kendi kusuru: `r_iç` ile `t₁` çelişiyordu

İlk iki seviyeli koşu **momentum kapanışı `0,690`** verdi. Kök neden
ölçüldü — `t₁ = 4,767e-3 s`'de:

| bölge | momentum |
|---|---|
| tüm sahne | `1,000 × p_mermi` ✔ |
| ince (`r < 3 m`) — aktarılan | **0,310** |
| kaba — **atılan** | **0,690** |

Bozulma `t₁`'de `~35–48 m`'ye yayılmış; `r_iç = 3 m` bunun onda biri.

**Bu bir uygulama kusuru değil, tasarım kusuruydu:** aşama-1'in kaba
bölgesi (`7 m`) aşama-2'nin orta bölgesinden (`3,5 m`) **daha kaba**;
kabadan inceye geçiş iyi tanımlı değil.

### Çözüm: üç seviyeli aşama-1

```
r < 3 m        lam=19   (mermi cozulmus)
3 < r < 25 m   lam=2    (asama-2 ile AYNI)
r > 25 m       kaba
```

| | iki seviyeli | **üç seviyeli** |
|---|---|---|
| atılan | 805 | **0** |
| birebir kopyalanan | — | **10 366** |
| **momentum kapanışı** | **0,690** | **5,10e-15** |
| `N` | 10 418 | 12 705 (**1,136×** aşama-2) |

`dt` zaten `λ₁` çekirdeğinden geliyor; orta seviye zaman adımını
**değiştirmiyor**.

---

## 4. En önemli ders: **tanı sonuçtan çok şey söyledi**

İki seviyelinin `β`'sı (`1,412659`) üç seviyelininkine (`1,411216`)
neredeyse **eşit** çıktı. Ama sahne **bozuktu**.

Sebebi: `β` ejekta momentumundan hesaplanıyor; atılan `%69` **bağlı**
kütlenin momentumuydu ve `β`'ya yansımadı.

> **Momentum kapanışı olmasaydı bozuk sahne *"doğrulanmış"*
> sayılacaktı.** Makul bir sonuç, doğru bir hesabın kanıtı değil.

---

## 5. Hâlâ açık: gözlenebilirlerin ikisi ölü

`t = 0,2 s`'de (rapor A11/A12):

| | ölçülen |
|---|---|
| kaçan kütle (`λ=2`) | `579,44 kg` = **merminin kendisi** (`579,40`) |
| krater derinliği | `0,035 m` = parçacık aralığının **`%1`**'i |
| hedef ejektası (`r > R`, `v_r > v_kaçış`) | **0** |

`β` ejekta olmak için `2R = 164 m`'yi geçmeyi istiyor; hedef maddesi
`82 m` yol almalı ve balistik geçiş süresi **medyan `795 s`**.

**İki ayrı sorun:**

1. **Geçiş beklemesi — çözüldü.** Yerçekimi kapalı olduğu için
   balistik hesaplanıyor; simüle etmeye gerek yok. Çapraz kontrol
   geçti: balistik `1,61758`, bağımsız kontrol kolu `1,617583`.
2. **Fırlatma — açık.** Krater oluşmadan ejekta yok. O süre
   **ölçülmedi**; şimdi **çözülmüş** mermiyle ölçülüyor
   (`faz48 --t-end 5 --iz-every 1000`, `~5,5` saat).

FAZ 4.5'in `t = 0,0406 s` cevabı **yanıltıcıydı**: `β_bound`'a baktı ve
o merminin sekmesine kilitlendi. Ayrıca `β_bound ≡ β` (momentum
korunumu), yani ADR-0028'in *"bağlı kütleyi kullan"* çaresi hiçbir şey
kazandırmıyor.

---

## 6. Durum

| | |
|---|---|
| G4 kapısı | `A1` düştü; A2/A3/B1/B2/B3/B4 geçti; C koşulmadı |
| `A1` | artık **geçilebilir** (2,0391) ve fark yarattığı **ölçüldü** |
| ADR-0043 | §4f kusuru **düzeltildi**; madde 3 (`λ=19` arayüz) hâlâ açık |
| ADR-0044 | **KABUL EDİLDİ**, uygulandı |
| FAZ 4.6 | **durduruldu** — çözülmüş mermiyle yeniden tasarlanmalı |
| açık sıkıntı | 7 |
