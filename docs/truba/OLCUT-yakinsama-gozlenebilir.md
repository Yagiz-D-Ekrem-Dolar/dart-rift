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

## 3. Yargı (kilitli)

Her gözlenebilir için bağıl fark, ardışık kollar arasında:

| ölçü | yakınsama koşulu |
|---|---|
| `β_hedef − 1` | `\|Δ\| / değer < 0,20` |
| `M_ejekta` | `< 0,20` |
| `P_ejekta` | `< 0,20` |

**Yakınsadı** denir ancak ve ancak **üçü birden** `R2 -> R3`
geçişinde eşiği sağlarsa. Biri sağlamazsa **hiçbiri** yakınsamış
sayılmaz.

`n_kaçan` bir yargı ölçütü **değil**; yalnızca raporlanır — çünkü
sonuçtur, girdi değil.

## 4. Beklenen ve **ne anlama gelir**

| sonuç | anlamı |
|---|---|
| üçü de yakınsıyor | gözlenebilirler **ölçülebilir**; çıkarıma geçilebilir |
| `β` yakınsıyor ama `M`/`P` yakınsamıyor | **telafi** var — `β` tesadüfen sabit, fizik oturmamış |
| hiçbiri yakınsamıyor | `R3` bile yetersiz; çözünürlük tek başına çare değil |
| `n_kaçan` `R3`'te hâlâ `< 50` | gözlenebilir bu mimaride **ölçülemez** — sonuç budur ve yazılır |

Son satır bir başarısızlık değil, **sınırlayıcı bulgu**: *"DART'ın
`β`'sı bu ileri modelde mevcut hesap bütçesiyle tanımlanabilir
değildir."*

## 5. `n ≥ 50` nerede duruyor

`n_kaçan ≥ 50` bir **mühendislik güvenlik kapısı** — *"ölçmeye
başlanabilir"*. Yakınsama ise *"ölçüm geçerli"*. İkisi ayrı ve
sıralı; kapı geçilmeden yakınsama sorulmaz, yakınsama olmadan
çıkarım yapılmaz.
