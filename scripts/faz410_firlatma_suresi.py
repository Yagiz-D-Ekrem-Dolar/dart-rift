"""FAZ 4.10 — **fırlatma süresi**: `β` ne zaman gerçekten durulur?

FAZ 4.5 bu soruyu `β_bound` ile sordu ve **yanlış** cevap aldı
(`t = 0,0406 s`): o an merminin sekmesinin kontrol yüzeyini geçtiği
andı, ejektanın değil (rapor A12).

## Ölçüt: **balistik** `β`

Yerçekimi kapalı (`GravityParams(enabled=False)`), yani serbest
parçacık doğru çizgide gider ve bir daha yavaşlamaz. O hâlde
*"kaçacak mı"* sorusu **şimdi** cevaplanabilir; `2R`'ye varmasını
beklemeye **gerek yok**.

```
ejekta  :  v_r > v_kaçış   VE   r > R
β_bal   =  1 − p_ejekta·ê / |p_mermi|
```

`r > R` şartı **gerekli**: yoksa cismin içinde basınç dalgasıyla
dışarı doğru salınan madde de sayılır. `2R` yerine `R` kullanmak
`82 m`'lik yolculuğu (medyan **`795 s`**) ortadan kaldırıyor.

> Bu bir **eşik gevşetmesi değil**, bekleme kaldırmasıdır: aynı
> parçacıklar, sadece varışları beklenmeden sayılıyor.

## Ne aranıyor

`β_bal(t)` **durulduğunda** kazı bitmiştir. Durulma sınavı FAZ 4.5'in
kullandığıyla **aynı** (`settling_time`) — iki yerde iki ölçüt olmasın.

> `β_bal` **büyümeyi bırakmazsa** krater hâlâ kazılıyor demektir ve
> FAZ 4.6 daha uzun koşmalıdır. Cevap ne olursa olsun **ölçülmüş**
> olacak; FAZ 4.5'in `0,0406 s`'si ise ölçülmemiş bir şeyin yerine
> geçmişti.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
for _akis in (sys.stdout, sys.stderr):
    try:
        _akis.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

from dartrift.cpu_reference.sph_ref import RefParams  # noqa: E402
from dartrift.observables.momentum_transfer import (  # noqa: E402
    balistik_beta,  # noqa: E402
    escape_speed,
)
from dartrift.setup.refine import refine_scene_local  # noqa: E402
from dartrift.setup.scene import _build_mesh, build_scene  # noqa: E402
from dartrift.validation.settling_time import settling_time  # noqa: E402

sys.path.insert(0, str(REPO / "scripts"))
from faz44_dart_yakinsama import SAHNE, _malzeme  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--steps", type=int, default=45000)
    ap.add_argument("--every", type=int, default=250)
    ap.add_argument("--spacing", type=float, default=7.0)
    ap.add_argument("--lam", type=float, default=2.0)
    ap.add_argument("--r-ince", type=float, default=25.0)
    ap.add_argument("--out", default=str(REPO.parent / "faz410_sonuc.json"))
    a = ap.parse_args()

    print("=" * 78, flush=True)
    print("FAZ 4.10 — FIRLATMA SURESI (balistik beta durulmasi)", flush=True)
    print("=" * 78, flush=True)

    kaba = build_scene(spacing=a.spacing, device="cpu", **SAHNE)
    mesh = _build_mesh("icosphere", radius=SAHNE["radius"], subdiv=4)
    rs = refine_scene_local(kaba, mesh, r_ince=a.r_ince, lam=a.lam)
    hedef = ~np.asarray(rs.is_impactor, dtype=bool)
    R = float(rs.target_radius)
    v_esc = escape_speed(float(rs.target_mass), R)
    p_imp = float(np.linalg.norm(rs.impactor_momentum))
    ehat = np.asarray(rs.impactor_momentum) / p_imp
    print(f"\nN = {rs.n}, R = {R:.1f} m, v_kacis = {v_esc:.5f} m/s", flush=True)
    print("olcut: r > R  VE  v_r > v_kacis  (2R BEKLENMIYOR)", flush=True)

    iz_yolu = Path(a.out).with_suffix(".izler.jsonl")
    iz_yolu.parent.mkdir(parents=True, exist_ok=True)
    if iz_yolu.exists():
        iz_yolu.unlink()

    sol_mod = __import__("dartrift.warp_core.solver_solid", fromlist=["x"])
    sol = sol_mod.WarpSolid3D(
        np.ascontiguousarray(rs.x), np.ascontiguousarray(rs.v),
        np.ascontiguousarray(rs.m), np.zeros(rs.n), rs.h, _malzeme(),
        RefParams(cfl=0.25), alpha0=np.ascontiguousarray(rs.alpha0),
        Y0=np.ascontiguousarray(rs.Y0), device=a.device, check_every=10 ** 9)

    izler, t, t0 = [], 0.0, time.perf_counter()
    print(f"\n{'adim':>7} {'t':>11} {'beta_bal':>10} {'hedef_ej':>9} "
          f"{'kutle%':>9}", flush=True)
    for adim in range(1, a.steps + 1):
        # `dt` ADIMDAN ONCE alinir: `compute_dt()` durum degistikce
        # degisir, yani adimdan SONRA cagirmak BASKA bir sayi verir.
        dt = sol.compute_dt()
        sol.step(dt)
        t += dt
        if adim % a.every == 0 or adim == a.steps:
            st = sol.state_numpy()
            if not np.all(np.isfinite(st["v"])):
                print(f"  PATLADI adim {adim}", flush=True)
                break
            d = balistik_beta(st["x"], st["v"], st["m"], hedef=hedef, R=R,
                              v_esc=v_esc, ehat=ehat, p_imp=p_imp)
            d.update(adim=adim, t=t)
            izler.append(d)
            with iz_yolu.open("a", encoding="utf-8") as f:
                f.write(json.dumps(d) + "\n")
            if adim % (a.every * 8) == 0:
                print(f"{adim:7d} {t:11.4e} {d['beta_bal']:10.5f} "
                      f"{d['n_hedef_ejekta']:9d} "
                      f"{100 * d['hedef_ejekta_kutle_kesri']:9.4f}", flush=True)

    ts = np.array([z["t"] for z in izler])
    bs = np.array([z["beta_bal"] for z in izler])
    dd = settling_time(ts, bs, adim=np.array([z["adim"] for z in izler]))
    print(f"\nSONUC ({time.perf_counter() - t0:.1f} s duvar, {len(izler)} ornek)",
          flush=True)
    print(f"  beta_bal ilk / son  = {bs[0]:.5f} / {bs[-1]:.5f}", flush=True)
    print(f"  hedef ejekta (son)  = {izler[-1]['n_hedef_ejekta']} parcacik, "
          f"%{100 * izler[-1]['hedef_ejekta_kutle_kesri']:.4f} kutle",
          flush=True)
    print(f"  SABIT MI            = {dd.get('sabit')}", flush=True)
    print(f"  DURULDU MU          = {dd['durulmus']}"
          f"{'' if dd['durulmus'] else '  -- ' + dd.get('neden', '')}",
          flush=True)
    print(f"  FIRLATMA SURESI     = {dd['t_durulma']:.6e} s", flush=True)
    print("  (FAZ 4.5 beta_bound ile 4.056e-02 s demisti — A12)", flush=True)

    Path(a.out).write_text(json.dumps(
        {"N": rs.n, "R": R, "v_kacis": v_esc, "t_sim": t,
         "beta_bal_son": float(bs[-1]),
         "firlatma_suresi_s": dd["t_durulma"],
         "durulma_tanisi": dd, "izler": izler}, indent=2, default=float))
    print(f"\nyazildi: {a.out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
