"""SPH'de çözülen ölçeği `h` mi belirliyor, parçacık aralığı `dx` mi?

**Neden bu ölçüm FAZ 4.2'nin kararını belirliyor**

Kod tabanının tamamında `h` **skalerdir**:

```
warp_core/solver.py:179        self.h = float(h)
warp_core/solver_solid.py:299  self.h = float(h)
cpu_reference/solid_ref.py:46  h: float
```

Yani A yaklaşımı (değişken kütle bölgeleri) bu kodda ancak **tek global `h`**
ile uygulanabilir — [`mass_ratio`][dartrift.validation.mass_ratio] modülünün
ölçtüğü şey tam olarak budur.

Eğer SPH'de çözülen ölçek `h` ise, bir bölgeye 8 kat parçacık koyup `h`'yi
kaba tutmak **çözünürlüğü artırmaz**; yalnızca aynı çekirdek içindeki
örnekleme sıklığını artırır. O zaman A, ADR-0026'nın sorununu (DART mermisini
çapı boyunca 6 parçacıkla çözmek) **çözemez**.

Bu önemli bir iddiadır ve **ölçülmeden yazılmaz**. Sınav Sedov'un **tam
analitik** çözümüne dayanır — iki koşuyu birbiriyle kıyaslamaktan güçlüdür:

- **(a) olağan yakınsama:** `h/dx` sabit → `h`, `dx` ile birlikte küçülür.
  Hata **küçülmeli**.
- **(b) bu sınav:** `h` **sabit** → yalnızca `dx` küçülür.
  - çözünürlüğü `h` belirliyorsa hata bir **tabana oturur**
  - çözünürlüğü `dx` belirliyorsa hata **küçülmeye devam eder**

**Boşluk kontrolü (ADR-0040):** (a) kolunun gerçekten küçüldüğü görülmelidir.
Küçülmüyorsa sınav hiçbir şey ayırt etmiyordur ve (b)'nin düzleşmesi
anlamsızdır.
"""
from __future__ import annotations

import numpy as np

from ..cpu_reference.sph_ref import RefParams
from .sedov import (GAMMA, H_OVER_DX, T_END_DEFAULT, build_sedov_ic,
                    measure_shock_radius, shock_radius_exact)

__all__ = ["run_single", "run_resolution_scaling"]


def run_single(n_side: int, h_absolute: float | None, device: str,
               t_end: float = T_END_DEFAULT) -> dict:
    """Tek bir Sedov koşusu. `h_absolute` None ise olağan `h = H_OVER_DX·dx`."""
    from ..warp_core.solver import WarpSPH3D

    ic = build_sedov_ic(n_side)
    h = float(h_absolute) if h_absolute is not None else float(ic["h"])
    solver = WarpSPH3D(ic["x"], ic["v"], ic["m"], ic["u"], h,
                       RefParams(gamma=GAMMA), device=device)
    diag = solver.run(t_end, max_steps=500_000)
    # Kismi kosu SESSIZCE gecerli sayilmaz (ADR-0011): t_end'e ulasilmadan
    # olculen yaricap sistematik olarak KUCUK cikar ve "cozunurlukle kotulesen
    # hata" gibi gorunur.
    if diag["t_end"] < t_end * (1.0 - 1.0e-9):
        raise RuntimeError(
            f"Sedov t_end'e ULASILAMADI: {diag['t_end']:.6g} < {t_end:.6g} "
            f"({diag['n_steps']} adim). Olcum gecersiz.")
    st = solver.state_numpy()
    r_olc = measure_shock_radius(st["x"], st["rho"])
    r_tam = shock_radius_exact(t_end)
    return {"n_side": n_side, "N": int(len(ic["m"])), "dx": float(ic["dx"]),
            "h": h, "h_over_dx": h / float(ic["dx"]),
            "r_measured": float(r_olc), "r_exact": float(r_tam),
            "rel_err": float(abs(r_olc - r_tam) / r_tam),
            "n_steps": int(diag["n_steps"])}


def run_resolution_scaling(
    sides: tuple[int, ...] = (32, 40, 48, 56, 64),
    device: str = "cuda:0",
    t_end: float = T_END_DEFAULT,
) -> dict:
    """İki kolu da koştur ve yargıyı ver.

    Sabit `h` kolu, **en kaba** kafesin `h`'sini kullanır: böylece o kafeste
    iki kol **birebir aynı** koşudur ve fark yalnızca `dx`'ten gelir.
    """
    if len(sides) < 3:
        raise ValueError(f"en az 3 çözünürlük gerekir, {len(sides)} geldi")
    if sorted(sides) != list(sides):
        raise ValueError(f"çözünürlükler artan olmalı: {sides}")

    h_sabit = H_OVER_DX / float(sides[0])
    olagan = [run_single(n, None, device, t_end) for n in sides]
    sabit = [run_single(n, h_sabit, device, t_end) for n in sides]

    hs = np.array([d["rel_err"] for d in olagan])
    hf = np.array([d["rel_err"] for d in sabit])
    ns = np.array(sides, dtype=np.float64)

    # BOSLUK KONTROLU: olagan kol gercekten kuculuyor mu? Kuculmuyorsa sinav
    # hicbir sey ayirt etmiyordur ve sabit-h kolunun duzlesmesi anlamsizdir.
    olagan_yakinsiyor = bool(hs[-1] < 0.5 * hs[0])
    sabit_duzlesiyor = bool(hf[-1] > 0.7 * hf[0])

    p_std = float(-np.polyfit(np.log(ns), np.log(hs), 1)[0])
    p_fix = float(-np.polyfit(np.log(ns), np.log(hf), 1)[0])

    if not olagan_yakinsiyor:
        yargi = "inconclusive"
    elif sabit_duzlesiyor:
        yargi = "h_sets_resolution"
    else:
        yargi = "dx_also_contributes"

    return {
        "standard": olagan, "fixed_h": sabit,
        "h_fixed_value": h_sabit, "h_over_dx_ref": H_OVER_DX, "t_end": t_end,
        "standard_converges": olagan_yakinsiyor,
        "fixed_h_plateaus": sabit_duzlesiyor,
        "order_standard": p_std, "order_fixed_h": p_fix,
        # En kaba kafeste iki kol AYNI kosu olmali — duzenegin kendi denetimi.
        "coarsest_arms_identical": bool(
            abs(olagan[0]["rel_err"] - sabit[0]["rel_err"]) < 1.0e-12),
        "verdict": yargi,
    }
