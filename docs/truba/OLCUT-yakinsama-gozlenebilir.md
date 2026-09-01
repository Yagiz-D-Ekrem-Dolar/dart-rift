# ÖLÇÜT — Gözlenebilirler çözünürlükle yakınsıyor mu (koşulardan **önce**)

**Tarih:** 2026-09-01 · **Öncül:** A30 · **Durum:** kampanya bekliyor

---

## 1. İki hata, ikisi de yapılmıştı

**(a) Kontrol değişkeni sonucun kendisi olamaz.** *"`~500`, `~2 000`,
`~8 000` kaçan parçacıkta aynı `β`"* diye yazmıştım. **Yanlış**:
`n_kaçan` bir **çıktı**, bağımsız değişken değil. Onu "artırmak" için
zaten sonucu değiştirmiş olursun.

> **Doğru kontrol değişkeni:** parçacık kütlesi `m_p` (eşdeğer olarak
> aralık `h`). `m_p` düşürülür; `n_kaçan` **sonuç olarak** ne
> yapıyorsa o ölçülür.

**(b) Tek gözlenebilirin yakınsaması yetmez.** `β_hedef` tesadüfen
sabit kalırken ejekta kütlesi ve hız dağılımı **birbirini telafi**
ediyor olabilir — `β ~ M·v` olduğu için `M` iki katına çıkıp `v`
yarıya inerse `β` kımıldamaz ve fizik tamamen değişmiş olur.

> **Üçü birden** yakınsamalı:
> `β_hedef`, `M_ejekta`, `P_ejekta`.

## 2. Tarama

Kontrol değişkeni: en ince seviyenin aralığı. Merdiven öz-benzer
kalıyor (`s/r` sabit), yani **yalnızca** çözünürlük değişiyor.

| kol | `s_min` | `m_p` | `N` (yaklaşık) | maliyet |
|---|---|---|---|---|
| **R1** | `0,350 m` | `46,6 kg` | `~14 000` | `0,3×` |
| **R2** | `0,175 m` | `5,83 kg` | `~76 700` | `5,4×` |
| **R3** | `0,0875 m` | `0,73 kg` | `~430 000` | `~61×` |

`R3` H100'de `~49 saat`. Pahalı ama **tek noktalık** — ensemble değil.

Ortak: `t_end = 0,2 s`, üretim malzemesi, tek aşama (aktarım yok),
şok kapısı açık.

## 3. Ölçülen nicelik `β` **değil**, `Δβ = β − 1`

Bu, gevşek bir eşiği sıkı sanmayı önlüyor. `β ≈ 1` rejiminde:

| | `R_a` | `R_b` | `β`'nın bağıl farkı | **`Δβ`'nın bağıl farkı** |
|---|---|---|---|---|
| örnek | `1,030` | `1,040` | `%0,97` | **`%33`** |

`β` üzerinden `%20` eşiği koymak, gerçek ejekta katkısı **üç katına**
çıksa bile *"yakınsadı"* der. Ölçülen nicelik **fiziksel artış**
olmalı:

> `Δβ_hedef = β_hedef − 1` — ve bu, momentum defterinden doğrudan
> geliyor: `Δβ_hedef = −P_kaçan_hedef / p_mermi`.

## 4. Üç nicelik + biri **yalnızca tanı**

| nicelik | tanım | rolü |
|---|---|---|
| **`Δβ_hedef`** | `β_hedef − 1` | gerçek momentum artışı |
| **`M_ejekta`** | `Σ mᵢ(1−fᵢ)`, kaçanlar | kaçan hedef kütlesi |
| **`P_ejekta,∥`** | `Σ mᵢ(vᵢ·ê)`, kaçan hedef | `β`'ya **gerçekten** katkı veren eksenel momentum |
| `n_kaçan` | sayı | **yalnızca çözünürlük tabanı tanısı** — yargı ölçütü değil |
| `P_ejekta` vektörü | tam vektör | `β` sabitken **açı kayması** görünsün diye kaydedilir |

`n_kaçan` bir **çıktı**; kontrol değişkeni olamaz. Kontrol değişkeni
`m_p` (eşdeğer olarak `h`).

## 5. Yargı — **iki kapı, ikisi de geçilmeli**

### Kapı A: **uzamsal** yakınsama (`m_p` ile)

Ardışık çözünürlükler arasında bağıl fark:

| aşama | eşik | ne için |
|---|---|---|
| **A1 · tarama** | `< 0,20` | gözlenebilir **aday** olur |
| **A2 · nihai** | `< 0,10` | Dimorphos sonucu için |

`A2` sağlanamazsa sonuç **çöpe gitmez**: ölçülen fark
`σ_sayısal` olarak **posteriora taşınır** —
`Δβ = 0,15 ± 0,04_sayısal` gibi. Belirsizlik saklanmaz, **bütçeye
yazılır**.

### Kapı B: **zamansal** plato

Uzamsal yakınsama tek başına yeter **görünebilir** ama ejekta hâlâ
gelişiyorsa ölçüm **erken** alınmıştır. Her çözünürlükte
`Δβ_hedef(t)` tutuluyor ve son pencerede:

    |Δβ(t₂) − Δβ(t₁)| / |Δβ(t₂)| < 0,05     (t₁ = 0,8·t_end)

`K4`'ün izi bunun ölçülebilir olduğunu gösterdi: `β_bal` `t = 0,09 s`
sonrasında beşinci ondalığa kadar sabit kaldı.

> **Yakınsadı** denir ancak ve ancak: `Δβ_hedef`, `M_ejekta` ve
> `P_ejekta,∥` **üçü birden** Kapı A'yı **ve** Kapı B'yi geçerse.
> Biri geçmezse **hiçbiri** yakınsamış sayılmaz.

## 6. Beklenen ve **ne anlama gelir**

| sonuç | anlamı |
|---|---|
| üçü de yakınsıyor | gözlenebilirler **ölçülebilir**; çıkarıma geçilebilir |
| `Δβ` yakınsıyor ama `M`/`P` yakınsamıyor | **telafi** var — `M` iki katına çıkıp `v` yarıya inerse `Δβ` kımıldamaz ve fizik tamamen değişmiştir |
| üçü yakınsıyor ama **açı** kayıyor | `P_ejekta` vektörü yakalar; `β` aynı kalıp yön dağılımı değişmiştir |
| hiçbiri yakınsamıyor | `R3` bile yetersiz; çözünürlük tek başına çare değil |
| `n_kaçan` `R3`'te hâlâ `< 50` | gözlenebilir bu mimaride **ölçülemez** — sonuç budur ve yazılır |

Son satır bir başarısızlık değil, **sınırlayıcı bulgu**: *"DART'ın
`β`'sı bu ileri modelde mevcut hesap bütçesiyle tanımlanabilir
değildir."*

## 7. `n ≥ 50` nerede duruyor

`n_kaçan ≥ 50` bir **mühendislik güvenlik kapısı** — *"ölçmeye
başlanabilir"*. Yakınsama ise *"ölçüm geçerli"*. İkisi ayrı ve
sıralı; kapı geçilmeden yakınsama sorulmaz, yakınsama olmadan
çıkarım yapılmaz.
