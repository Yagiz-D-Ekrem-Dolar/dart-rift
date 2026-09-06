# Protokol H — krater derinliğinin çözünürlük direnci

**Yazıldı:** 2026-09-06, **koşudan önce** · **Dayanak:** G1 sonucu, A52

---

## Neden

`G1` ölçtü: krater derinliği `θ`'yı **ayırt ediyor** —
`F = 1006`, `matris_Y0` ile `ρ = −0,9417` (`p < 0,0001`).
Ama **tek çözünürlükte** (kaba, `N = 17 201`).

`β`'nın yakınsaması A52 yüzünden imkânsız (`R3` için `224` saat).
Krater için **değil**: kaba ve orta merdivenlerin ikisi de
karşılanabilir (`~1` dk ve `~35` dk / nokta).

## Tasarım

Aynı LHS tasarımının **aynı** noktaları, iki çözünürlükte, iki sahne
gerçeklemesiyle.

| görev | merdiven | dilim | sahne tohumu |
|---|---|---|---|
| `0` | kaba | `0/8` | `20260906` |
| `1` | kaba | `0/8` | `99991111` |
| `2` | orta | `0/8` | `20260906` |
| `3` | orta | `0/8` | `99991111` |
| `4` | orta | `1/8` | `20260906` |
| `5` | orta | `1/8` | `99991111` |

`0/8` → nokta `0, 8, 16`; `1/8` → nokta `1, 9, 17`. Kaba kol
`1/8` için `G1`'in mevcut verisinden okunur (aynı tasarım tohumu,
aynı merdiven) — yeni koşu gerekmiyor.

## Yargı — **şimdi kilitleniyor**

Her `θ` için:

```
cozunurluk_farki = |d_orta - d_kaba| / d_orta
gurultu          = |d(tohum A) - d(tohum B)| / d_ortalama
```

| gözlenen | sonuç |
|---|---|
| `çözünürlük_farkı < 3 × gürültü` (her `θ`'da) | **KORUNUYOR.** Krater derinliğinin `θ`-tepkisi bu iki ölçek arasında dirençli; `G1`'in sonucu tek ölçeğe bağlı değil. |
| `3 ×` ile `10 ×` arası | **ZAYIF.** Fark var ama işaret ve sıralama korunuyorsa `G1` şartlı bildirilir. |
| `> 10 × gürültü`, ya da **sıralama bozuluyor** | **KORUNMUYOR.** `G1`'in sonucu tek ölçeğe bağlı kalır ve öyle bildirilir. |

### Ek şart — sıralama

`Y₀` ile azalan ilişki **her iki ölçekte de** aynı işarette olmalı.
İşaret değişirse üstteki tablo **uygulanmaz**, sonuç doğrudan
`KORUNMUYOR`.

## Bu ne DEĞİL

**Richardson derecesi değil.** İki nokta ile `p` hesaplanmaz ve
`σ_num` üretilmez. Bu bir **direnç sınavı**: *"ölçeği `4` kat
değiştirince bulgu ayakta kalıyor mu"*.

Üç noktalı yakınsama A52 çözülmeden mümkün değil ve bu belge onun
yerine geçmiyor.

## Maliyet

Kaba `~1` dk/nokta, orta `~35` dk/nokta (ölçüldü: `E2a` `00:35:40`).
`6` görev, `3` nokta/görev → orta kollar `~1,8` saat.
