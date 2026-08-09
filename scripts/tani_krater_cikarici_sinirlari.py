"""Krater çıkarıcısının **ölçülmüş sınırları**.

> ## ⚠ Bu betik önce YANLIŞ bir kusur bildiriyordu
>
> İlk sürümü `impact_direction`'ı kraterin **merkez yönü** olarak
> veriyordu. Oysa parametre merminin **gidiş yönü**dür, yani krater
> `-impact_direction` tarafındadır. Yanlış işaretle çıkarıcı **karşı
> kutba** bakıyor ve doğal olarak `0` buluyordu.
>
> *"Çıkarıcı 80 m'lik krateri göremiyor"* sonucu bu yüzden **yanlıştı**
> ve geri alındı. Aşağısı doğru yönelimle ölçülmüş **gerçek** sınırdır.

## Ölçülen

`R = 82 m` küre, parabolik krater, `impact_direction = -merkez_yönü`:

| `D` | derinlik | `s = 3,5 m` | `s = 2,0 m` | `s = 1,2 m` |
|---|---|---|---|---|
| 40 m | 8 m | *ölçülemedi* (koruma) | 3,51 | 3,80 |
| 20 m | 4 m | 0,000 | 0,000 | 0,000 |

**İki gerçek sınır:**

1. **`0.` kutu genişliği.** Kutu `0–12,84°` (yüzeyde `18,4 m`) ve
   **medyan** alınıyor. Parabolik bir kraterin medyanı tepe
   derinliğinin yarısı kadar → `8 m` yerine `3,5–3,8 m`.
2. **Çap eşiği.** `depth_threshold × R = 4,1 m`; ölçülen `dev` bunun
   altında kaldığı için **çap `0`** çıkıyor.

`D = 20 m` krater `0.` kutudan **küçük** (yarı açı `7° < 12,84°`), o
yüzden medyan neredeyse hiç kımıldamıyor.

> Yani çıkarıcı **çalışıyor**; küçük kraterlere karşı **muhafazakâr**.
> Bu bir kod kusuru değil, çözünürlük ve eşik sınırı.
"""
import sys

import numpy as np

sys.path.insert(0, "src")
from dartrift.observables.crater_shape import crater_profile

R = 82.0
MERKEZ = np.array([1.0, 0.0, 0.0])          # kraterin merkez yonu


def dene(D, d_kr, s):
    rng = np.random.default_rng(7)
    n = int(4 * np.pi * R * R / (s * s))
    u = rng.uniform(-1, 1, n)
    ph = rng.uniform(0, 2 * np.pi, n)
    st = np.sqrt(1 - u * u)
    yon = np.column_stack([st * np.cos(ph), st * np.sin(ph), u])
    x0 = R * yon
    ya = np.arcsin(min(D / 2 / R, 1.0))
    ca = yon @ MERKEZ
    ic = ca > np.cos(ya)
    a = np.arccos(np.clip(ca, -1, 1))
    r = np.full(n, R)
    r[ic] = R - d_kr * (1.0 - (a[ic] / ya) ** 2)
    try:
        # DIKKAT: impact_direction merminin GIDIS yonu -> kraterin TERSI
        kr = crater_profile(r[:, None] * yon, center=np.zeros(3),
                            impact_direction=-MERKEZ, reference_radius=R,
                            x_reference=x0)
        return f"derinlik {kr.depth:7.3f}  cap {kr.diameter:7.2f}", n
    except ValueError as ex:
        return f"OLCULEMEDI: {str(ex)[:46]}", n


if __name__ == "__main__":
    print(f"R = {R} m, impact_direction = merminin GIDIS yonu\n")
    print(f"{'D (m)':>6} {'derinlik':>9} {'s (m)':>6} {'N':>7}   sonuc")
    for D, d_kr in ((40.0, 8.0), (20.0, 4.0)):
        for s in (3.5, 2.0, 1.2):
            msg, n = dene(D, d_kr, s)
            print(f"{D:6.0f} {d_kr:9.1f} {s:6.1f} {n:7d}   {msg}")
        print()
