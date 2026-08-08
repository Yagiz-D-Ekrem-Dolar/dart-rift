"""`β` ne zaman **duruluyor**? (FAZ 4.5 — EKSİKLER §D)

## Neden ayrı bir modül

Plato mantığı `scripts/measure_longrun.py` içinde gömülüydü ve **hiç
sınanmamıştı**. Okununca gerçek bir kusur görüldü:

```python
b_end = float(bb[-1])
icinde = np.abs(bb - b_end) <= tol * abs(b_end)
k = len(icinde) - 1
while k > 0 and icinde[k - 1]:
    k -= 1
return float(tt[k]), int(ss_[k])
```

> **Bu ölçüt her zaman bir sayı döndürür.** Platoyu **son değere** göre
> tanımlıyor; koşu hâlâ tırmanıyorsa son değer plato değildir, ama son
> birkaç nokta birbirine yakın olduğu için yine bir "durulma zamanı"
> raporlanır.

Uç durumda: `β` doğrusal artıyorsa ve örnekleme sık ise, komşu noktalar
`%2` içinde kalır ve ölçüt **koşunun başını** durulma anı ilan eder —
tam ters sonuç.

Bu, KAYIT-017'nin (3. tur) dersinin aynısıdır: *"bir kriter 'GEÇTİ'
diyorsa, geçme sebebi ölçülmüş olmalıdır."* Burada geçme sebebi
ölçülmüyordu.

## Eklenen şey: **durulmuşluk** önce sınanır

Plato zamanı ancak seri gerçekten durulduysa anlamlıdır. İki sınav:

1. **Eğilim sınavı.** Son pencerede `β`'nın **eğimi**, pencere boyunca
   ürettiği kayma `β`'ya oranlanarak ölçülür. Hâlâ tek yönlü tırmanıyorsa
   durulmamıştır.
2. **Yarım-pencere sınavı.** Son pencerenin ilk yarısının ortalaması ile
   ikinci yarısının ortalaması tolerans içinde olmalı.

> ### İkincisi **bağımsız değil** — ölçüldü
>
> İlk yazdığımda "iki bağımsız sınav" dedim. **Yanlış.** Altı şekilde
> ölçüldü ve yarım-pencere sınavı **hiçbirinde tek başına** yakalamadı:
>
> | şekil | eğilim kayması | yarım-pencere | yalnız yarım yakalar mı |
> |---|---|---|---|
> | doğrusal | %4,97 | %2,51 | hayır |
> | basamak (ortada) | %8,42 | %5,66 | hayır |
> | basamak (sonda) | %3,03 | %1,13 | hayır |
> | V / ters V | %0,03 | %0,02 | hayır |
> | üstel oturan | %0,00 | %0,00 | hayır |
>
> Doğrusal sürüklenmede oran **tam 2**'dir ve bu cebirseldir: pencere
> genişliği `w` ve eğim `s` için kayma `s·w`, yarım-pencere farkı
> `s·w/2`. Yani eğilim sınavı **her zaman** iki kat duyarlı.
>
> Sınav **kaldırılmadı** — ucuz ve `neden` metninde şeklin ne olduğunu
> gösteriyor. Ama *"bağımsız ikinci güvence"* diye **sunulmuyor**.

İkisi de geçmezse `durulmus=False` olur ve **zaman raporlanmaz** —
`nan` yazılır.
"""
from __future__ import annotations

import numpy as np

__all__ = ["settling_time", "is_settled"]


def is_settled(t, b, pencere_frac: float = 0.3, tol: float = 0.02) -> dict:
    """Seri gerçekten duruldu mu? **Plato zamanından önce** sorulur.

    Parameters
    ----------
    t, b
        Zaman ve `β` dizileri (aynı uzunluk). `nan`'lar atılır.
    pencere_frac
        Son pencerenin, serinin **zaman aralığına** oranı. Nokta sayısına
        değil zamana bağlanıyor: örnekleme sıklığı değişirse yargı
        değişmesin.
    tol
        Göreli tolerans.
    """
    t = np.asarray(t, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    if t.shape != b.shape:
        raise ValueError(f"t ve b aynı şekilde olmalı: {t.shape} vs {b.shape}")
    ok = np.isfinite(t) & np.isfinite(b)
    t, b = t[ok], b[ok]
    if len(b) < 6:
        return {"durulmus": False, "neden": f"yalnızca {len(b)} geçerli nokta "
                                            f"(en az 6 gerekir)"}
    if not (0.0 < pencere_frac < 1.0):
        raise ValueError(f"pencere_frac (0,1) içinde olmalı, {pencere_frac}")

    t_son = float(t[-1])
    t_bas = float(t[0])
    esik = t_son - pencere_frac * (t_son - t_bas)
    pen = t >= esik
    if int(pen.sum()) < 4:
        return {"durulmus": False,
                "neden": f"son pencerede {int(pen.sum())} nokta (en az 4)"}
    tp, bp = t[pen], b[pen]
    olcek = max(abs(float(b[-1])), 1e-300)

    # 1) EGILIM: son pencerede egim, olcege gore ne kadar kaydiriyor?
    egim = float(np.polyfit(tp, bp, 1)[0])
    kayma = abs(egim * (tp[-1] - tp[0])) / olcek

    # 2) YARIM PENCERE: ilk yari vs ikinci yari ortalamasi.
    yari = len(bp) // 2
    ilk, son = float(np.mean(bp[:yari])), float(np.mean(bp[yari:]))
    fark = abs(son - ilk) / olcek

    durulmus = bool(kayma < tol and fark < tol)
    return {"durulmus": durulmus,
            "pencere_nokta": int(pen.sum()),
            "pencere_t": [float(tp[0]), float(tp[-1])],
            "egim_kaymasi": kayma, "yarim_pencere_farki": fark,
            "tol": float(tol), "beta_son": float(b[-1]),
            "neden": "" if durulmus else
                     (f"eğilim {kayma:.3%}" if kayma >= tol else "") +
                     (" ve " if kayma >= tol and fark >= tol else "") +
                     (f"yarım-pencere {fark:.3%}" if fark >= tol else "") +
                     f" (tolerans {tol:.1%})"}


def settling_time(t, b, adim=None, pencere_frac: float = 0.3,
                  tol: float = 0.02) -> dict:
    """`β`'nın durulduğu **an** — ama önce durulduğu **doğrulanır**.

    Durulmadıysa `t_durulma` **`nan`**'dır. Bir sayı uydurmaktansa
    "ölçülemedi" demek doğrudur (RULES.txt).
    """
    d = is_settled(t, b, pencere_frac=pencere_frac, tol=tol)
    sonuc = dict(d)
    sonuc["t_durulma"] = float("nan")
    sonuc["adim_durulma"] = -1
    if not d["durulmus"]:
        return sonuc

    t = np.asarray(t, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    ok = np.isfinite(t) & np.isfinite(b)
    tt, bb = t[ok], b[ok]
    ss = (np.asarray(adim)[ok] if adim is not None
          else np.arange(len(t))[ok])
    b_son = float(bb[-1])
    icinde = np.abs(bb - b_son) <= tol * abs(b_son)
    k = len(icinde) - 1
    while k > 0 and icinde[k - 1]:
        k -= 1
    sonuc["t_durulma"] = float(tt[k])
    sonuc["adim_durulma"] = int(ss[k])
    # Durulma ANI son pencerenin BASINDAN once olmali; degilse "durulma"
    # yalnizca son birkac noktanin yakinligidir, gercek bir plato degil.
    sonuc["plato_penceredern_genis"] = bool(tt[k] <= d["pencere_t"][0])
    return sonuc
