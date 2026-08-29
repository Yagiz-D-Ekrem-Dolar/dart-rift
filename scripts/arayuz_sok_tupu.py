"""**Arayüz şok tüpü**: şok bir çözünürlük basamağını geçebiliyor mu?

## Neden bu, sahne koşusundan iyi

A25'in sorusu — *"şok `8×` bir basamağı geçer mi, `8 000×`'i geçmez
mi"* — tüm Dimorphos sahnesini gerektirmiyor. Sahne koşusu `96 000`
parçacık ve saatler; bu düzenek **birkaç bin** parçacık ve
**saniyeler**, üstelik kalıcı bir test oluyor.

Ayrıca sahne koşusunda çok şey aynı anda değişiyor (küresel geometri,
gözeneklilik ızgarası, mermi bağlanması). Burada **tek** değişken var:
basamağın büyüklüğü.

## Düzenek

Uzun bir kutu. `x < 0` ince (`s`), `x > 0` kaba (`κ s`). Soldaki
piston `+x` yönünde `u₀` ile itiyor; şok sağa doğru yürüyor ve
arayüze çarpıyor.

Ölçülen: **kaba tarafta** sıkışan parçacık var mı. A25'in kütle
parmak izi ölçüsünün birebir aynısı — kaba parçacıkların kütlesi
belli, şoklanan var mı yok mu bakılıyor.

## Beklenen

Kabuk kalınlığı ölçütü (A25): kaba parçacığın desteği `4 κs`; kaba
bölge ondan kalın olduğu sürece geometri **engel değil**. Burada kaba
bölge kasten uzun tutuluyor, yani **yalnızca kütle basamağı**
sınanıyor.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

RHO0 = 2700.0


def tup_sahnesi(s_ince: float, kat: float, *, n_yan: int = 6,
                l_ince: float = 12.0, l_kaba: float = 12.0) -> dict:
    """İnce/kaba iki bölgeli kutu. `kat` = aralık oranı (`κ`).

    `n_yan`: enine parçacık sayısı **kaba** tarafta. Enine boyut
    kaba `2h`'den büyük olmalı ki komşuluk düzlemsel kalsın; ince
    tarafa göre ölçeklemek kaba tarafı `12` parçacığa düşürüyordu
    (ilk denemede öyle oldu ve ölçüm anlamsızlaşırdı).
    """
    if kat < 1.0:
        raise ValueError(f"kat >= 1 olmali, {kat} geldi")
    s_kaba = s_ince * kat
    yan = n_yan * s_kaba
    xs = []
    for s, x0, x1 in ((s_ince, -l_ince * s_ince, 0.0),
                      (s_kaba, 0.0, l_kaba * s_kaba)):
        nx = max(int(round((x1 - x0) / s)), 1)
        ny = max(int(round(yan / s)), 1)
        gx = x0 + (np.arange(nx) + 0.5) * s
        gy = (np.arange(ny) - (ny - 1) / 2.0) * s
        X, Y, Z = np.meshgrid(gx, gy, gy, indexing="ij")
        p = np.stack([X.ravel(), Y.ravel(), Z.ravel()], axis=1)
        xs.append((p, s))
    x = np.concatenate([p for p, _ in xs])
    s_par = np.concatenate([np.full(len(p), s) for p, s in xs])
    return {"x": x, "s": s_par, "m": RHO0 * s_par ** 3,
            # INCE/KABA ayrimi KONUMA gore: `kat = 1` denetim kolunda
            # aralik ayni oldugu icin kutle ayrimi calismaz, ama
            # "sok x > 0'a ulasti mi" sorusu orada da anlamli.
            "h": 2.0 * s_par, "ince": x[:, 0] < 0.0,
            "s_ince": s_ince, "s_kaba": s_kaba,
            "kutle_orani": float(kat ** 3)}


def kos(sahne: dict, u0: float, adim: int, *, device: str = "cuda:0",
        piston_kalinlik: float = 3.0) -> dict:
    """Pistonu `+x`'e sür, `adim` adım koş, sıkışmaları döndür."""
    from faz48_iki_asama import _cozucu

    x = sahne["x"]
    v = np.zeros_like(x)
    piston = x[:, 0] < x[:, 0].min() + piston_kalinlik * sahne["s_ince"]
    v[piston, 0] = u0
    sol = _cozucu(x, v, sahne["m"], np.zeros(len(x)), sahne["h"],
                  np.ones(len(x)), np.full(len(x), 1.0e7), device,
                  mat=_katı_malzeme())
    for _ in range(adim):
        sol.step(sol.compute_dt())
    st = sol.state_numpy()
    sik = st["rho"] / RHO0 - 1.0
    return {"sikisma": sik, "ince": sahne["ince"], "rho": st["rho"],
            "v": st["v"], "x": st["x"]}


def _katı_malzeme():
    """Gözeneksiz, hasarsız, yerçekimsiz — **tek** değişken kalsın."""
    import dataclasses

    from faz48_iki_asama import _malzeme
    m = _malzeme()
    return dataclasses.replace(
        m, porosity=dataclasses.replace(m.porosity, enabled=False))


def yargi(r: dict, *, esik: float = 0.01) -> dict:
    """Kaba tarafta şok var mı — A25'in kütle parmak izi ölçüsü."""
    s, ince = r["sikisma"], r["ince"]
    kaba = ~ince
    return {
        "n_ince": int(ince.sum()), "n_kaba": int(kaba.sum()),
        "ince_soklu": int((ince & (s > esik)).sum()),
        "kaba_soklu": int((kaba & (s > esik)).sum()),
        "ince_sik_max": 100.0 * float(s[ince].max()),
        "kaba_sik_max": 100.0 * float(s[kaba].max()) if kaba.any() else 0.0,
        "gecti": bool((kaba & (s > esik)).any()),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kat", type=float, nargs="+", default=[1.0, 2.0, 4.0, 20.0])
    ap.add_argument("--s-ince", type=float, default=0.175)
    ap.add_argument("--u0", type=float, default=600.0)
    ap.add_argument("--adim", type=int, default=400)
    ap.add_argument("--device", default="cuda:0")
    a = ap.parse_args()
    print(f"{'kat':>5} {'kutle orani':>12} {'N':>7} {'ince sik':>10} "
          f"{'kaba sik':>10} {'kaba soklu':>11} {'yargi':>8}")
    for kat in a.kat:
        sh = tup_sahnesi(a.s_ince, kat)
        r = yargi(kos(sh, a.u0, a.adim, device=a.device))
        print(f"{kat:>5.0f} {sh['kutle_orani']:>11,.0f}x {len(sh['x']):>7} "
              f"%{r['ince_sik_max']:>9.3f} %{r['kaba_sik_max']:>9.3f} "
              f"{r['kaba_soklu']:>11} "
              f"{'GECTI' if r['gecti'] else 'GECMEDI':>8}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
