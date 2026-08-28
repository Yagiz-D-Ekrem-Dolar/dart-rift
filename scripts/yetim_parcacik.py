"""**Yetim parçacık** tanısı: komşusu olmayan parçacıklar ve taşıdıkları enerji.

## Neden

SPH'de bir parçacık, komşusu yoksa hiçbir şeyle **etkileşemez**:
basınç gradyanı yok, `dudt` yok, iş yapamaz. İç enerjisi varsa o
enerji **donar** — gerçekte genleşip iş yapacak olan sıcak madde,
modelde hareketsiz bir depo olur.

Ölçüldü (`2026-08-21`, `λ₁ = 38`, `t = 0,2 s`): **`40` parçacık**
`14 m` içinde hiç komşusuz; toplam kütle `409,6 kg`; taşıdıkları

| | |
|---|---|
| iç enerji | `1,323e9 J` = **`%12,1`** gelen enerjinin |
| kinetik | `6,14e8 J` = `%5,6` |
| **toplam** | **`%17,7`** |

`409,6 kg`, merminin (`579,4 kg`) `%71`'i. Yani sekip dağılan mermi
maddesi, gelen enerjinin altıda birini **etkileşemez** halde
taşıyor. Gerçekte o iç enerji genleşmeyi sürer ve momentuma dönerdi;
burada donuyor.

Tek aşamalı kolda yetim **yok** (`0`): mermi `803` parçacıkla birlikte
kalıyor. Yetimler iki aşamalı aktarımın merminin `46` siteye
kabalaştırmasıyla ortaya çıkıyor.

## Bu bir "kaçak" mı

Momentum ve kütle **korunuyor** — yetimler sahnede duruyor. Kaybolan
şey enerjinin **işe dönüşebilirliği**: komşusuz bir parçacığın
`P dV`'si yok. Yani defter tutuyor, fizik tutmuyor.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

#: Çarpma kinetik enerjisi (`configs/p3_scene.yaml`).
KE_GELEN = 0.5 * 579.4 * 6144.9 ** 2


def komsu_say(x: np.ndarray, yaricap: float) -> np.ndarray:
    """Her parçacığın `yaricap` içindeki komşu sayısı (kendisi hariç).

    Izgara kutulamasıyla; `scipy` bağımlılığı **yok** (ADR-0004'ün
    kurulum kısıtı: `/arf`'a pip yok).
    """
    x = np.asarray(x, dtype=np.float64)
    if x.ndim != 2 or x.shape[1] != 3:
        raise ValueError(f"x (N,3) olmali, {x.shape} geldi")
    if yaricap <= 0.0:
        raise ValueError(f"yaricap pozitif olmali, {yaricap} geldi")
    ix = np.floor(x / yaricap).astype(np.int64)
    kutu: dict[tuple[int, int, int], list[int]] = {}
    for i, k in enumerate(map(tuple, ix)):
        kutu.setdefault(k, []).append(i)
    n = np.zeros(len(x), dtype=int)
    ofs = [(a, b, c) for a in (-1, 0, 1) for b in (-1, 0, 1)
           for c in (-1, 0, 1)]
    r2 = yaricap * yaricap
    for k, idxs in kutu.items():
        aday: list[int] = []
        for o in ofs:
            aday.extend(kutu.get((k[0] + o[0], k[1] + o[1], k[2] + o[2]), ()))
        ad = np.asarray(aday, dtype=np.int64)
        for i in idxs:
            d2 = np.sum((x[ad] - x[i]) ** 2, axis=1)
            n[i] = int(np.count_nonzero(d2 < r2)) - 1
    return n


def yetim_tanisi(x, m, u, v, *, yaricap: float) -> dict:
    """Komşusuz parçacıklar ve **donmuş** enerjileri."""
    n = komsu_say(x, yaricap)
    y = n == 0
    up = np.maximum(np.asarray(u, dtype=np.float64), 0.0)
    m = np.asarray(m, dtype=np.float64)
    v = np.asarray(v, dtype=np.float64)
    U = float(np.sum(m[y] * up[y]))
    K = 0.5 * float(np.sum(m[y] * np.einsum("ij,ij->i", v[y], v[y])))
    return {
        "yaricap_m": float(yaricap),
        "n_yetim": int(y.sum()),
        "n_toplam": int(len(m)),
        "kutle_kg": float(np.sum(m[y])),
        "ic_enerji_J": U,
        "kinetik_J": K,
        "ic_enerji_pay": U / KE_GELEN,
        "kinetik_pay": K / KE_GELEN,
        "donmus_toplam_pay": (U + K) / KE_GELEN,
        "komsu_medyan": float(np.median(n)),
        "komsu_min": int(n.min()),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--durum", type=Path, required=True)
    ap.add_argument("--yaricap", type=float, default=14.0,
                    help="komsuluk yaricapi (2h; uretimde 2*2*s2 = 14 m)")
    a = ap.parse_args()
    z = np.load(a.durum)
    for ad in ("x", "m", "u", "v"):
        if ad not in z.files:
            raise SystemExit(f"durum dosyasinda `{ad}` yok: {z.files}")
    r = yetim_tanisi(z["x"], z["m"], z["u"], z["v"], yaricap=a.yaricap)
    print("=" * 62, flush=True)
    print("YETIM PARCACIK TANISI", flush=True)
    print("=" * 62, flush=True)
    for k, v in r.items():
        print(f"  {k:>22} = {v}", flush=True)
    if r["n_yetim"]:
        print(f"\n  DONMUS ENERJI: {100 * r['donmus_toplam_pay']:.2f}% "
              f"gelen enerjinin, {r['n_yetim']} komsusuz parcacikta.",
              flush=True)
        print("  Komsusuz parcacigin P dV'si yoktur: ic enerjisi ise "
              "donusemez.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
