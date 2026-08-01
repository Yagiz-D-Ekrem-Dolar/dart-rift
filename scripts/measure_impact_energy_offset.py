"""Carpma anindaki tek-seferlik enerji kaymasi: kesme hatasi mi, yapay mi?

OLCULEN OLGU. Uzun kosuda enerji hatasi carpmanin hemen ardindan ~%1.46'ya
sicriyor ve SONRA HIC DEGISMIYOR (2250 adim boyunca birebir sabit; log-log
egim ~0). Yani bu bir SURUKLENME degil, tek seferlik bir kayma.

AYIRT EDICI OLCUM. Iki hipotez ayni gozlemi aciklar:
  H1 — ZAMAN KESME HATASI: ilk temas adiminda cozulemeyen sok. Bu durumda
       kayma dt ile kucultulebilir; CFL yariya inince kayma ~yariya iner
       (O(dt)) ya da dorde (O(dt^2)).
  H2 — UZAY AYRIKLASTIRMA YAPAYI: parcacik araligindan kaynaklanan sabit bir
       kayip. Bu durumda CFL degistirmek HICBIR SEY degistirmez; kucultmek
       icin cozunurluk artmali.

Bu betik ikisini de tarar ve hangisinin gecerli oldugunu SAYIYLA soyler.
ADR-0020'de Sedov enerji hatasi tam bu yontemle "sizinti degil kesme hatasi"
diye ayrilmisti.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from dartrift.cpu_reference.materials import (  # noqa: E402
    GravityParams,
    MaterialParams,
    PorosityParams,
    StrengthParams,
)
from dartrift.cpu_reference.sph_ref import RefParams  # noqa: E402
from dartrift.setup.scene import build_scene  # noqa: E402


def _mat() -> MaterialParams:
    return MaterialParams(
        eos="tillotson",
        strength=StrengthParams(enabled=True, Y0=1.0e4, mu_f=0.6, YM=1.5e9,
                                shear_G=2.27e10, jaumann=True),
        porosity=PorosityParams(enabled=True, alpha0=1.6, Pe=1.0e6,
                                Ps=1.0e8, n_exp=2.0),
        gravity=GravityParams(enabled=False),
        density_method="continuity",
    )


def kosu(spacing: float, cfl: float, steps: int, device: str,
         radius: float, n_imp: int, rho_imp: float) -> dict:
    from dartrift.warp_core.solver_solid import WarpSolid3D

    sc = build_scene(radius=radius, spacing=spacing, bulk_density=1800.0,
                     root_seed=20260801, model_class="M0",
                     n_impactor=n_imp, impactor_density=rho_imp)
    n = sc.n
    sol = WarpSolid3D(
        np.ascontiguousarray(sc.x), np.ascontiguousarray(sc.v),
        np.ascontiguousarray(sc.m), np.zeros(n), 2.0 * spacing, _mat(),
        RefParams(cfl=cfl), alpha0=np.ascontiguousarray(sc.alpha0),
        Y0=np.ascontiguousarray(sc.Y0), device=device, check_every=10**9)
    e0 = sol.budgets()["e_tot"]
    t = 0.0
    for _ in range(steps):
        dt = sol.compute_dt()
        sol.step(dt)
        t += dt
    e1 = sol.budgets()["e_tot"]
    return {
        "spacing": spacing, "cfl": cfl, "n": n, "steps": steps, "t_end": t,
        "dt_mean": t / steps,
        "e_rel_err": abs(e1 - e0) / max(abs(e0), 1e-300),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--steps", type=int, default=600)
    ap.add_argument("--radius", type=float, default=20.0)
    ap.add_argument("--n-impactor", type=int, default=400)
    ap.add_argument("--impactor-density", type=float, default=20.0)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    print("=== H1 sinavi: CFL taramasi (cozunurluk SABIT) ===", flush=True)
    print(f"{'cfl':>8} {'dt_ort':>10} {'E_hata':>12} {'hata/ref':>14}", flush=True)
    cfl_rows = []
    ref = None
    for cfl in (0.25, 0.125, 0.0625):
        r = kosu(1.0, cfl, int(args.steps * 0.25 / cfl), args.device,
                 args.radius, args.n_impactor, args.impactor_density)
        if ref is None:
            ref = r["e_rel_err"]
        r["ratio_to_ref"] = r["e_rel_err"] / max(ref, 1e-300)
        cfl_rows.append(r)
        print(f"{cfl:8.4f} {r['dt_mean']:10.3e} {r['e_rel_err']:12.6e} "
              f"{r['ratio_to_ref']:14.4f}", flush=True)

    print("", flush=True)
    print("=== H2 sinavi: cozunurluk taramasi (CFL SABIT) ===", flush=True)
    print(f"{'aralik':>8} {'N':>10} {'E_hata':>12} {'hata/ref':>14}", flush=True)
    res_rows = []
    ref2 = None
    for s in (1.0, 0.7, 0.5):
        r = kosu(s, 0.25, args.steps, args.device, args.radius,
                 args.n_impactor, args.impactor_density)
        if ref2 is None:
            ref2 = r["e_rel_err"]
        r["ratio_to_ref"] = r["e_rel_err"] / max(ref2, 1e-300)
        res_rows.append(r)
        print(f"{s:8.2f} {r['n']:10d} {r['e_rel_err']:12.6e} {r['ratio_to_ref']:14.4f}", flush=True)

    # --- karar ---
    cfl_span = cfl_rows[-1]["e_rel_err"] / max(cfl_rows[0]["e_rel_err"], 1e-300)
    res_span = res_rows[-1]["e_rel_err"] / max(res_rows[0]["e_rel_err"], 1e-300)
    print("", flush=True)
    print(f"CFL 4x kucultuldugunde hata orani     : {cfl_span:.4f}", flush=True)
    print(f"Aralik 2x kucultuldugunde hata orani  : {res_span:.4f}", flush=True)
    if cfl_span < 0.6:
        karar = "H1 — zaman kesme hatasi (dt ile kuculuyor)"
    elif res_span < 0.6:
        karar = "H2 — uzay ayriklastirma yapayi (cozunurlukle kuculuyor)"
    else:
        karar = "IKISI DE DEGIL — hata ne dt ne aralik ile kuculuyor; baska kaynak"
    print(f"KARAR: {karar}", flush=True)

    if args.out:
        Path(args.out).write_text(json.dumps(
            {"cfl_sweep": cfl_rows, "resolution_sweep": res_rows,
             "cfl_span": cfl_span, "resolution_span": res_span,
             "verdict": karar}, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
