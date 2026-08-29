"""**Şok cephesi**: konumu, tepe sıkışması, şoklanan kütle.

## Neden ayrı bir araç

`sok_sinavi.py` *"şok var mı"* sorusunu yanıtlıyor — tek sayı, tek
an. Ama A24'te ortaya çıkan soru başka: cephe **ilerliyor mu**.

Ölçüldü (`2026-08-29`): `λ₂ = 20`, `r_ince = 3 m`. Cephe
`t = 1e-3 s`'de `3,41 m`'de; `t = 4,767e-3 s`'de **yine `3,41 m`**.
`3 400 m/s` ile `16 m` gitmeliydi. İki anlık görüntüden *"duruyor"*
sonucuna varmak zayıf bir çıkarım; bu araç onu **zaman serisi**
yapıyor.

## Cephe nasıl tanımlanıyor

Sıkışması eşiği aşan parçacıkların **referans** konumlarının çarpma
noktasına en büyük uzaklığı. Referans konum kullanılıyor çünkü
madde de hareket ediyor; Euler konumu kullanmak cepheyi maddenin
sürüklenmesiyle karıştırırdı.

Eşik `%1` — A23'te `λ₂ = 8` bu eşikte **tek** parçacık verirken
`λ₂ = 20` `1 306` parçacık verdi, yani eşik ayrımı yapabiliyor.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sok_sinavi import sikisma  # noqa: E402

#: Cepheyi tanimlayan sikisma esigi (kesir, yuzde degil).
ESIK = 0.01


def cephe(rho, alpha0, x_referans, carpma_noktasi, m, *,
          esik: float = ESIK) -> dict:
    """Cephe konumu ve şoklanan kütle.

    `carpma_noktasi` merminin **başlangıç** merkezidir. Bu bir kez
    `ehat`'ın ters ucundan ölçüldü ve `160 m` çıktı (cismin
    antipodu); o yüzden burada nokta **dışarıdan** veriliyor ve
    işaret seçimi çağırana bırakılmıyor.
    """
    s = sikisma(np.asarray(rho), np.asarray(alpha0))
    m = np.asarray(m, dtype=np.float64)
    xr = np.asarray(x_referans, dtype=np.float64)
    if xr.ndim != 2 or xr.shape[1] != 3:
        raise ValueError(f"x_referans (N,3) olmali, {xr.shape} geldi")
    d = np.linalg.norm(xr - np.asarray(carpma_noktasi, dtype=np.float64),
                       axis=1)
    sel = s > esik
    if not sel.any():
        return {"n": 0, "cephe_m": float("nan"), "ic_kenar_m": float("nan"),
                "kalinlik_m": float("nan"), "sikisma_max_yuzde": 100.0 * float(s.max()),
                "kutle_kg": 0.0, "esik_yuzde": 100.0 * esik}
    return {
        "n": int(sel.sum()),
        "cephe_m": float(d[sel].max()),
        "ic_kenar_m": float(d[sel].min()),
        "kalinlik_m": float(d[sel].max() - d[sel].min()),
        "sikisma_max_yuzde": 100.0 * float(s.max()),
        "kutle_kg": float(m[sel].sum()),
        "esik_yuzde": 100.0 * esik,
    }


def hiz(cephe_onceki: float, cephe_simdi: float, dt: float) -> float:
    """Cephe hızı — Hugoniot `Us` ile kıyaslanabilir olsun diye."""
    if dt <= 0.0:
        raise ValueError(f"dt pozitif olmali, {dt} geldi")
    return (cephe_simdi - cephe_onceki) / dt


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--durum", type=Path, nargs="+", required=True)
    ap.add_argument("--esik", type=float, default=ESIK)
    a = ap.parse_args()
    print(f"{'dosya':>22} {'t (s)':>10} {'cephe':>8} {'ic':>7} "
          f"{'kalinlik':>9} {'sik_max':>9} {'kutle (kg)':>12} {'n':>7}")
    onc = None
    for yol in a.durum:
        z = np.load(yol)
        h = z["hedef"].astype(bool)
        carp = z["x_referans"][~h].mean(axis=0)
        r = cephe(z["rho"][h], z["alpha0"][h], z["x_referans"][h], carp,
                  z["m"][h], esik=a.esik)
        t = float(z["t"])
        print(f"{yol.name[:22]:>22} {t:>10.3e} {r['cephe_m']:>8.2f} "
              f"{r['ic_kenar_m']:>7.2f} {r['kalinlik_m']:>9.2f} "
              f"%{r['sikisma_max_yuzde']:>8.3f} {r['kutle_kg']:>12,.0f} "
              f"{r['n']:>7}")
        if onc is not None and t > onc[0]:
            v = hiz(onc[1], r["cephe_m"], t - onc[0])
            print(f"{'':>22} -> cephe hizi {v:>8.1f} m/s "
                  f"(Hugoniot Us ~ 3 000-7 000 m/s)")
        onc = (t, r["cephe_m"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
