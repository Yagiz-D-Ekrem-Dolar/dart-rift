# Protokol T — zamanda plato tanısı (betimleyici)

**Yazıldı:** 2026-09-13, koşudan önce. **Karar kapısı değil**; hangi
sürenin yeterli olduğunu ölçmek için.

## Neden

Bütün kampanyalar `t = 24 ms`'de okunuyor. Uzman: *"0,024–0,2 s
koşusunun saati, düşük hızlı kazı ve yeniden yerleşimin sonuna kadar
gereken saat değildir."* Önceki ölçüm (E, üretim fiziği): kazı akışı
24 ms'de `18,7 t`, 200 ms'de `93 kg` — yani akış doğup ölüyordu. En iyi
fizikte `β(t)` ne yapıyor?

## Tasarım

Merkez θ `(1,15 ; 1e5 ; 0,275)`, kaba merdiven, `t_end = 0,2 s`,
L2/M ile aynı fizik. Dört koşu:

| koşu | çarpma sahası | tohum |
|---|---|---|
| `T_matris_sahne20260906` | matris (`3 m`) | 20260906 |
| `T_matris_sahne99991111` | matris | 99991111 |
| `T_blok_sahne20260906` | blok (`4 m`) | 20260906 |
| `T_blok_sahne99991111` | blok | 99991111 |

İleri model `fizik_tani.impuls_egrisi`'ne 50 eşit aralıklı anda
`[t, P_hedef/p_imp, β_hedef, M_ejekta]` yazıyor.

## Okuma

`scripts/t_zaman_raporu.py`: `momentum_defteri.plato_gecti` (kodda
kilitli: son `%20` pencere, `%5` bağıl, `1e-4` mutlak) `β−1` ve
normalize `M_ejekta` üzerinde. Ayrıca `t = %5, %12, %25, %50, %75, %100`
anlarındaki değerler yazılır; `24 ms` (`%12`) değerinin son değere
oranı buradan okunur.
