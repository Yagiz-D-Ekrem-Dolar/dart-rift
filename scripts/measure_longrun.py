"""Uzun kosu kararliligi + gereken simule sure — FIZIBILITE §5'in acik iki maddesi.

Kapanan iki bilinmeyen:

1. **Uzun kosu kararliligi.** Butun kapi senaryolari birkac yuz adimdir.
   Bir DART kosusu 1e4-1e5 adimdir. ADR-0020 enerji hatasinin O(dt) oldugunu
   gosterdi; 1e5 adimda ne BIRIKTIGI olculmemisti. Burada enerji ve momentum
   sapmasi adim sayisina karsi izlenir — dogrusal mi buyuyor, doyuyor mu,
   yoksa patliyor mu?

2. **Gereken simule sure.** Momentum aktariminin (beta) ne zaman duruldugu
   kosunun maliyetini 10 kat degistirir. Burada beta(t) izlenir ve
   PLATO kriteri ile durulma zamani olculur.

YONTEM NOTU. Bu bir FAZ 4 sonucu DEGILDIR; fizibilite olcumudur. Cikan beta
sayilari bilimsel iddia olarak sunulmaz — olculen sey beta'nin ZAMAN
DAVRANISI ve defterin kararliligidir. Hedef gercek Dimorphos sekli degil
analitik ikosferdir (G3 C7 KANITLANAMADI).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
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
from dartrift.observables.momentum_transfer import escape_speed, momentum_transfer  # noqa: E402
from dartrift.setup.scene import build_scene  # noqa: E402


def _impactor_radius(scene) -> float:
    """Merminin kure esdeger yaricapi (sahnedeki mermi parcaciklarindan)."""
    xi = scene.x[scene.is_impactor]
    c = xi.mean(axis=0)
    return float(np.max(np.linalg.norm(xi - c[None, :], axis=1)))


def _material(gravity: bool) -> MaterialParams:
    return MaterialParams(
        eos="tillotson",
        strength=StrengthParams(enabled=True, Y0=1.0e4, mu_f=0.6, YM=1.5e9,
                                shear_G=2.27e10, jaumann=True),
        porosity=PorosityParams(enabled=True, alpha0=1.6, Pe=1.0e6,
                                Ps=1.0e8, n_exp=2.0),
        gravity=GravityParams(enabled=gravity, G=6.6743e-11, eps=0.0,
                              mode="barnes_hut", theta=0.5),
        density_method="continuity",
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--steps", type=int, default=20000)
    ap.add_argument("--spacing", type=float, default=6.0)
    ap.add_argument("--n-impactor", type=int, default=800)
    ap.add_argument("--every", type=int, default=100)
    ap.add_argument("--gravity", action="store_true")
    ap.add_argument("--radius", type=float, default=82.0,
                    help="hedef yaricapi [m]")
    ap.add_argument("--impactor-density", type=float, default=2700.0,
                    help="mermi yogunlugu [kg/m^3]. DUSURULURSE mermi BUYUR ve "
                         "cozunur; kutle ve hiz degismedigi icin momentum ve "
                         "kinetik enerji korunur. Kararlilik olcumu icin "
                         "kullanilir (bkz. ADR-0026).")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    from dartrift.warp_core.solver_solid import WarpSolid3D

    mat = _material(args.gravity)
    scene = build_scene(radius=args.radius, spacing=args.spacing,
                        bulk_density=1800.0, root_seed=20260801,
                        model_class="M1", f_boulder=0.25, q=3.0,
                        r_min=2.0 * args.spacing, r_max=6.0 * args.spacing,
                        n_impactor=args.n_impactor,
                        impactor_density=args.impactor_density)
    n = scene.n
    h = 2.0 * scene.spacing
    across = scene.diagnostics["particles_across_impactor"]
    print(f"sahne: N={n} (hedef {scene.n_target} + mermi "
          f"{scene.diagnostics['n_impactor']}), h={h:.2f} m, "
          f"yercekimi={'ACIK' if args.gravity else 'KAPALI'}", flush=True)
    print(f"karma: {scene.digest[:16]}", flush=True)
    # KRITIK TANI (ADR-0026): merminin capi hedef ARALIGINA gore kac parcacik?
    # 1'in altindaysa mermi hedef cozunurlugunden KUCUKTUR ve erken zamanli
    # sok baglanmasi sayisal bir yapaydir — beta'ya guvenilemez.
    imp_across_target = 2.0 * _impactor_radius(scene) / args.spacing
    print(f"mermi cozunurlugu: kendi icinde {across:.2f} parcacik/cap; "
          f"HEDEF aralagina gore {imp_across_target:.3f} parcacik/cap", flush=True)
    if imp_across_target < 2.0:
        print("  UYARI: mermi hedef cozunurlugunun altinda — erken zamanli "
              "baglanma COZULMEMIS (ADR-0026)", flush=True)

    sol = WarpSolid3D(
        np.ascontiguousarray(scene.x), np.ascontiguousarray(scene.v),
        np.ascontiguousarray(scene.m), np.zeros(n), h, mat, RefParams(cfl=0.25),
        alpha0=np.ascontiguousarray(scene.alpha0),
        Y0=np.ascontiguousarray(scene.Y0),
        device=args.device, check_every=10**9,
    )

    p_imp = scene.impactor_momentum
    m_target = scene.target_mass
    r_target = scene.target_radius
    v_esc = escape_speed(m_target, r_target)

    b0 = sol.budgets()
    e0 = b0["e_tot"]
    st0 = sol.state_numpy()
    p0 = np.sum(st0["m"][:, None] * st0["v"], axis=0)
    p0n = float(np.linalg.norm(p0))
    print(f"baslangic: E_tot={e0:.6e} J  |p|={p0n:.6e} kg m/s  "
          f"v_kacis={v_esc:.4f} m/s", flush=True)

    rows = []
    t_sim = 0.0
    t0 = time.perf_counter()
    for step in range(1, args.steps + 1):
        dt = sol.compute_dt()
        sol.step(dt)
        t_sim += dt
        if step % args.every == 0 or step == args.steps:
            b = sol.budgets()
            st = sol.state_numpy()
            p = np.sum(st["m"][:, None] * st["v"], axis=0)
            try:
                mt = momentum_transfer(
                    st["x"], st["v"], st["m"], impactor_momentum=p_imp,
                    center=np.zeros(3), target_mass=m_target,
                    target_radius=r_target, control_radius=2.0 * r_target,
                    speed_threshold=v_esc)
                beta = mt.beta
                beta_bound = mt.beta_from_bound
                n_ej = mt.n_ejecta
                f_ej = mt.ejecta_fraction
            except ValueError:
                beta, beta_bound, n_ej, f_ej = float("nan"), float("nan"), 0, 0.0
            row = {
                "step": step, "t_sim": t_sim,
                "e_tot": b["e_tot"], "e_kin": b["e_kin"], "e_int": b["e_int"],
                "e_rel_err": abs(b["e_tot"] - e0) / max(abs(e0), 1e-300),
                "p_rel_err": float(np.linalg.norm(p - p0)) / max(p0n, 1e-300),
                "beta": beta, "beta_bound": beta_bound,
                "n_ejecta": n_ej, "ejecta_fraction": f_ej,
                "wall_s": time.perf_counter() - t0,
            }
            rows.append(row)
            print(f"adim {step:7d}  t={t_sim:.5f}s  E_hata={row['e_rel_err']:.4e}  "
                  f"p_hata={row['p_rel_err']:.4e}  b_bagli={beta_bound:.5f}  "
                  f"b_ejekta={beta:.4f}  ejekta={n_ej:6d}  "
                  f"duvar={row['wall_s']:.0f}s", flush=True)
            if not np.isfinite(b["e_tot"]):
                print("SONLU OLMAYAN ENERJI — kosu durduruldu", flush=True)
                break

    # --- durulma (plato) analizi ---
    # PLATO icin BAGLI KUTLE momentumundan turetilen beta kullanilir, ejektadan
    # turetilen degil. Gerekce: ejekta betasi, parcaciklarin kontrol yuzeyini
    # (2R) GECMESINI bekler; m/s mertebesindeki ejekta icin bu 100+ saniye eder
    # ve kraterlesme coktan bitmis olsa bile plato gorunmez. Bagli kutlenin
    # momentumu ise krater buyumesi durunca durulur — "momentum aktarimi
    # tamamlandi mi" sorusunun dogru gozlenebiliri budur.
    ts = np.array([r["t_sim"] for r in rows], dtype=np.float64)
    steps_arr = np.array([r["step"] for r in rows])

    def _plateau(key: str, tol: float = 0.02):
        bs = np.array([r[key] for r in rows], dtype=np.float64)
        ok = np.isfinite(bs)
        if np.count_nonzero(ok) < 5:
            return float("nan"), -1
        bb, tt, ss_ = bs[ok], ts[ok], steps_arr[ok]
        b_end = float(bb[-1])
        if abs(b_end) <= 0.0:
            return float("nan"), -1
        icinde = np.abs(bb - b_end) <= tol * abs(b_end)
        k = len(icinde) - 1
        while k > 0 and icinde[k - 1]:
            k -= 1
        return float(tt[k]), int(ss_[k])

    plateau_t, plateau_step = _plateau("beta_bound")
    plateau_ej_t, plateau_ej_step = _plateau("beta")

    # --- enerji sapmasi buyume yasasi ---
    ee = np.array([r["e_rel_err"] for r in rows], dtype=np.float64)
    ss = np.array([r["step"] for r in rows], dtype=np.float64)
    slope = float("nan")
    m_ok = (ee > 0) & (ss > 0)
    if np.count_nonzero(m_ok) >= 3:
        slope = float(np.polyfit(np.log(ss[m_ok]), np.log(ee[m_ok]), 1)[0])

    out = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "scene_digest": scene.digest,
        "n_particles": n, "spacing": args.spacing, "h": h,
        "gravity": bool(args.gravity),
        "steps_requested": args.steps, "steps_done": rows[-1]["step"] if rows else 0,
        "t_sim_end": t_sim,
        "e_rel_err_final": rows[-1]["e_rel_err"] if rows else float("nan"),
        "p_rel_err_final": rows[-1]["p_rel_err"] if rows else float("nan"),
        "energy_drift_loglog_slope": slope,
        "beta_final": rows[-1]["beta"] if rows else float("nan"),
        "beta_bound_final": rows[-1]["beta_bound"] if rows else float("nan"),
        "beta_bound_plateau_time_s": plateau_t,
        "beta_bound_plateau_step": plateau_step,
        "beta_ejecta_plateau_time_s": plateau_ej_t,
        "beta_ejecta_plateau_step": plateau_ej_step,
        "wall_s": time.perf_counter() - t0,
        "series": rows,
    }
    print("", flush=True)
    print(f"SONUC  E_hata_son={out['e_rel_err_final']:.4e}  "
          f"p_hata_son={out['p_rel_err_final']:.4e}", flush=True)
    print(f"       enerji sapmasi log-log egim={slope:.3f} "
          f"(1.0 = adim sayisiyla dogrusal, <1 = doyuyor)", flush=True)
    print(f"       beta_bagli_son={out['beta_bound_final']:.5f}  "
          f"plato t={plateau_t:.5f}s (adim {plateau_step})", flush=True)
    print(f"       beta_ejekta_son={out['beta_final']:.4f}  "
          f"plato t={plateau_ej_t:.5f}s (adim {plateau_ej_step})", flush=True)
    print(f"       duvar suresi={out['wall_s']:.0f}s "
          f"({out['wall_s'] / max(out['steps_done'], 1) * 1000:.2f} ms/adim)", flush=True)

    if args.out:
        Path(args.out).write_text(json.dumps(out, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
