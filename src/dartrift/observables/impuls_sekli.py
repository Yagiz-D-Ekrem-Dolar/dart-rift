"""`β(t)` eğrisinin **şekli** — fiziği sayısaldan ayıran tanı (KAYIT-070).

## Neden

`β`'nın son değeri, fizik farkını sayısal farktan **ayıramıyor**. Ölçüldü
(L1 kıyas sahnesi, `t_geçiş = 0,2 s`, `β(300 s)`):

| iki koşu | `β` |
|---|---|
| `Y₀ = 1 Pa`, kaba merdiven | **4,023** |
| `Y₀ = 10 Pa`, keskin çekirdek | **4,023** |

Kohezyonu 10 kat düşürmek ile çekirdeği keskinleştirmek **aynı sayıyı**
veriyor. Ama normalize birikim eğrisi ayırıyor: momentumun yarısına ulaşma
anı `1,60 s`'ye karşı `0,62 s`.

En ayırt edici ölçü `s(1 s)` (1 saniyede biriken kesir):

| değişen | `Δs(1 s)` |
|---|---|
| **fizik:** `Y₀` 10 → 1 Pa | **0,059** |
| sayısal: kaba → orta merdiven | 0,014 |
| sayısal: keskin çekirdek | 0,012 |
| sayısal: mermi 800 → 6400 parçacık | 0,003 |
| sayısal: uzak alan 7 → 3,5 m | 0,002 |

Yani `s(1 s)`'te fizik sinyali sayısal gürültünün `~4–5` katı. `β`'nın
kendisinde bu oran `~1`'dir (fizik `%12,5`, sayısal `%10,9`).

## Ne işe yarar, ne işe yaramaz

- **Yarar:** bir sayısal ayarın literatürü *doğru sebeple* mi tutturduğunu
  sınamak. Aynı `β`, farklı şekil → aynı sayı, farklı mekanizma.
- **Yaramaz:** gerçek DART'ta `s(t)` **ölçülemez** (yörüngeden yalnız son
  `β` gelir). Bu yüzden çıkarımdaki dejenereliği tek başına kırmaz.
"""
from __future__ import annotations

import numpy as np

__all__ = ["impuls_sekli", "SEKIL_ANLARI"]

#: `s(t)`'nin raporlandığı anlar [s].
SEKIL_ANLARI = (1.0, 10.0, 100.0)


def impuls_sekli(egri, *, t_ref: float, kesirler=(0.5, 0.9),
                 anlar=SEKIL_ANLARI) -> dict:
    """`impuls_egrisi` satırlarından normalize birikim şekli.

    Parameters
    ----------
    egri
        `[[t, _, beta, M], ...]` — `forward.ileri_kosu_merdiven`'in yazdığı
        `fizik_tani["impuls_egrisi"]`.
    t_ref
        Normalizasyon anı; `s(t) = (β(t) − 1) / (β(t_ref) − 1)`. Eğri bu ana
        ulaşmıyorsa `ValueError`. Değer log-zamanda aradeğerle okunur —
        eğride `t_ref` düğümü **olmak zorunda değil**.
    kesirler
        Hangi birikim kesirlerine ulaşma anları raporlansın (`t50`, `t90`…).

    Döner: `beta_ref`, `t_kesir_*`, `s_*` ve kullanılan anlar.
    """
    e = np.atleast_2d(np.asarray(egri, dtype=np.float64))
    if e.ndim != 2 or e.shape[1] < 3 or len(e) < 3:
        raise ValueError("egri (n >= 3, sutun >= 3) olmali")
    t, b = e[:, 0], e[:, 2] - 1.0
    if np.any(t <= 0.0) or np.any(np.diff(t) <= 0.0):
        raise ValueError("t pozitif ve artan olmali")
    if not np.all(np.isfinite(b)):
        raise ValueError("beta sonlu olmali")
    if t_ref <= t[0] or t_ref > t[-1] * (1.0 + 1e-6):
        raise ValueError(f"t_ref {t_ref} egrinin disinda ({t[0]:.3g}–{t[-1]:.3g})")
    lt = np.log(t)
    b_ref = float(np.interp(np.log(t_ref), lt, b))
    if not (b_ref > 0.0):
        raise ValueError(f"beta(t_ref) - 1 pozitif olmali, {b_ref} geldi")
    s = b / b_ref

    out: dict = {"t_ref": float(t_ref), "beta_ref": 1.0 + b_ref}
    for k in kesirler:
        if not 0.0 < k < 1.0:
            raise ValueError(f"kesir (0,1) icinde olmali: {k}")
        i = int(np.argmax(s >= k))
        if s[0] >= k:                    # ilk noktada zaten asilmis
            out[f"t{int(k * 100)}"] = float(t[0])
        elif i == 0:                     # hic asilmamis
            out[f"t{int(k * 100)}"] = float("nan")
        else:
            out[f"t{int(k * 100)}"] = float(
                np.exp(np.interp(k, [s[i - 1], s[i]], [lt[i - 1], lt[i]])))
    for a in anlar:
        out[f"s_{a:g}s"] = (float(np.interp(np.log(a), lt, s))
                            if t[0] <= a <= t[-1] else float("nan"))
    return out
