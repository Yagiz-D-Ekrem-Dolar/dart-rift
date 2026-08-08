"""ADR-0043 gereksinim #1: **`t₁` gerçekte ne kadar?**

Aşama-1 (pahalı, `λ ≈ 19`) ancak **bağlanma bittikten** sonra
kesilebilir. ADR `t₁ ≈ 1e-3 s` **önerdi** ama bu bir tahmindi; burada
ölçülüyor.

## Ölçüt: mermi hedefle **aynı hıza** geldi mi

Bağlanma, merminin momentumunun hedefe aktarılmasıdır. Bittiğinde mermi
parçacıkları artık hedeften ayrı bir hızda değildir.

```
u(t) = |<v>_mermi − <v>_yakın hedef| / v_çarpma
```

`u → 0` bağlanmanın bittiğini gösterir. Durulma ölçütü FAZ 4.5'inkiyle
**aynı** (`settling_time`) — iki yerde iki ölçüt yazmamak için.

> `u`'nun **sıfıra** gitmesi beklenmiyor; sıçrama ve saçılma bir kalıntı
> bırakır. Ölçülen şey `u`'nun **durulduğu** an.
"""
from __future__ import annotations

import argparse
import json
import sys
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
from dartrift.setup.refine import refine_scene_local  # noqa: E402
from dartrift.setup.scene import _build_mesh, build_scene  # noqa: E402
from dartrift.validation.settling_time import settling_time  # noqa: E402

sys.path.insert(0, str(REPO / "scripts"))
from faz44_dart_yakinsama import SAHNE, _malzeme  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--lam", type=float, default=19.0)
    ap.add_argument("--r-ince", type=float, default=3.0)
    ap.add_argument("--t-end", type=float, default=2.0e-3)
    ap.add_argument("--steps", type=int, default=40000)
    ap.add_argument("--every", type=int, default=20)
    ap.add_argument("--out", default=str(REPO.parent / "faz43c_sonuc.json"))
    a = ap.parse_args()

    from dartrift.warp_core.solver_solid import WarpSolid3D

    print("=" * 78, flush=True)
    print("ADR-0043 #1 — BAGLANMA SURESI t1 OLCULUYOR", flush=True)
    print("=" * 78, flush=True)

    kaba = build_scene(spacing=7.0, device="cpu", **SAHNE)
    mesh = _build_mesh("icosphere", radius=SAHNE["radius"], subdiv=4)
    rs = refine_scene_local(kaba, mesh, r_ince=a.r_ince, lam=a.lam)
    n = rs.n
    imp = np.asarray(rs.is_impactor, dtype=bool)
    mermi_capi = 2.0 * float(np.max(np.linalg.norm(
        rs.x[imp] - rs.x[imp].mean(axis=0)[None, :], axis=1)))
    a1 = mermi_capi / rs.spacing_fine
    print(f"\nsahne: N={n} (ince {rs.diagnostics['n_ince']}, "
          f"kaba {rs.diagnostics['n_kaba']}, mermi {rs.diagnostics['n_mermi']})",
          flush=True)
    print(f"  s_ince = {rs.spacing_fine:.4f} m, A1 = {a1:.3f} "
          f"({'COZULMUS' if a1 >= 2.0 else 'COZULMEMIS'})", flush=True)
    print(f"  kutle sapmasi = {rs.diagnostics['hedef_kutle_sapmasi']:.3e}",
          flush=True)

    # Carpma hizi: merminin baslangic hizinin buyuklugu.
    v_carpma = float(np.linalg.norm(rs.v[imp].mean(axis=0)))
    # YAKIN hedef: ince bolgedeki hedef parcaciklari.
    yakin = np.asarray(rs.is_fine, dtype=bool) & ~imp
    print(f"  v_carpma = {v_carpma:.1f} m/s, yakin hedef = {int(yakin.sum())}",
          flush=True)

    sol = WarpSolid3D(
        np.ascontiguousarray(rs.x), np.ascontiguousarray(rs.v),
        np.ascontiguousarray(rs.m), np.zeros(n), rs.h, _malzeme(),
        RefParams(cfl=0.25), alpha0=np.ascontiguousarray(rs.alpha0),
        Y0=np.ascontiguousarray(rs.Y0), device=a.device, check_every=10 ** 9)

    izler, t_sim = [], 0.0
    for adim in range(1, a.steps + 1):
        dt = sol.compute_dt()
        if t_sim + dt > a.t_end:
            dt = a.t_end - t_sim
        sol.step(dt)
        t_sim += dt
        son_mu = adim == a.steps or t_sim >= a.t_end * (1.0 - 1e-12)
        if adim % a.every == 0 or son_mu:
            st = sol.state_numpy()
            if not np.all(np.isfinite(st["v"])):
                print(f"  PATLADI adim {adim}", flush=True)
                break
            v_m = st["v"][imp].mean(axis=0)
            v_h = st["v"][yakin].mean(axis=0)
            u = float(np.linalg.norm(v_m - v_h) / v_carpma)
            izler.append({"adim": adim, "t": t_sim, "u": u})
            if adim % (a.every * 50) == 0:
                print(f"  adim {adim:6d}  t={t_sim:.4e}  u={u:.5f}", flush=True)
        if son_mu:
            break

    ts = np.array([z["t"] for z in izler])
    us = np.array([z["u"] for z in izler])
    d = settling_time(ts, us, adim=np.array([z["adim"] for z in izler]))
    print(f"\nSONUC ({len(izler)} ornek, t_sim = {t_sim:.4e} s)", flush=True)
    print(f"  u(baslangic) = {us[0]:.5f}", flush=True)
    print(f"  u(son)       = {us[-1]:.5f}", flush=True)
    print(f"  DURULDU MU   = {d['durulmus']}"
          f"{'' if d['durulmus'] else '  -- ' + d['neden']}", flush=True)
    print(f"  t1 (olculen) = {d['t_durulma']:.6e} s", flush=True)
    print(f"  ADR-0043 tahmini = 1.0e-03 s", flush=True)

    Path(a.out).write_text(json.dumps(
        {"lam": a.lam, "r_ince": a.r_ince, "N": n, "A1": a1,
         "v_carpma": v_carpma, "t_sim": t_sim,
         "t1_olculen": d["t_durulma"], "durulmus": bool(d["durulmus"]),
         "durulma_tanisi": d, "izler": izler}, indent=2))
    print(f"\nyazildi: {a.out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
