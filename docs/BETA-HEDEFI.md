# `β` hedefi — tek sayı değil, aralık

**Yazıldı:** 2026-09-06 · **Kaynak:** dış uzman incelemesi (2026-09-05)

---

## Depo boyunca `β = 3,22` koşulsuz hedef gibi kullanıldı

Uzmanın uyarısı:

> *"`β = 3,22` ve `10⁶ kg` değerlerini koşulsuz hedef yapmayın.
> `β` yoğunluk ve yön varsayımlarına bağlıdır."*

Gözlemsel çalışmada (Cheng ve diğerleri, 2023, `arXiv:2303.03464`)
`2400 kg/m³` varsayımıyla **`β ≈ 3,61`**; daha geniş yoğunluk
aralığında **`2,2 – 4,9`**.

## Ne değişiyor

| | eski | yeni |
|---|---|---|
| hedef | `β = 3,22` | **`β ∈ [2,2 ; 4,9]`** |
| türetilmiş ejekta kütlesi | `~10⁶ kg` | **hız dağılımına bağlı, tek sayı değil** |

`β = 3,22` yaklaşık `7,9e6 kg·m/s` ejekta momentumu ister. **Gereken
kütle hız dağılımına bağlıdır** — `1000 m/s`'lik jet ile `1 m/s`'lik
kazı akışı aynı momentumu bin kat farklı kütleyle taşır.

## Sonuç: kıyas `M(>v)` üzerinden olmalı

Tek bir `β` sayısını tutturmak, dağılımı yanlış olan bir modelde de
mümkündür. Housen & Holsapple ölçekleme yasaları zaten `M(>v)`
üzerinde tanımlı:

```
M(>v) ~ v^(-3μ),   μ ≈ 0,40 (gözenekli) … 0,55 (kaya)
```

kümülatif eğim `−1,2 … −1,65`. Ölçüm aracı yazıldı:
`scripts/hiz_tanisi.py`.

> **Uyarı (uzman):** *"On altı parçacığa güç yasası uydurup eksik
> milyon kilogramı ekstrapolasyonla tamamlamak savunulamaz."*
> `M(>v)` **kıyas** için, **ekstrapolasyon** için değil.

## Nerede geçerli

Bu belge `docs/adr/ADR-0047`, `ADR-0049` ve `docs/defter/KAYIT-051`
içindeki `3,22` kullanımlarını **bağlamlandırır**; o belgeler
silinmiyor (depo kuralı), ama hedefi tek sayı sayan her okuma bu
belgeye tabidir.
