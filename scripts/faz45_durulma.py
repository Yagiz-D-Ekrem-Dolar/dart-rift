"""FAZ 4.5 — gereken simüle süre: `β` ne zaman **duruluyor**?

`measure_longrun.py` zaten `β(t)` izliyor ve (yeni ölçütle) durulmuşluğu
raporluyor. Bu betik onu **A′ sahnesinde** koşturur ve çıktısını G4
anahtarlarına çevirir.

## `measure_longrun`'dan farkı

| | `measure_longrun` | bu betik |
|---|---|---|
| sahne | tekdüze `spacing` | **A′** (yerel incelme) |
| `h` | skaler | **parçacık başına** |
| amaç | fizibilite (uzun koşu kararlılığı) | **G4-B2 / B4** |

## Neden A′ sahnesinde

ADR-0028 ölçtü ki çözülemeyen bir mermiyle *"β durdu"* ölçümü merminin
**geri sıçramasını** ölçer, ejektayı değil. Durulma zamanı ancak mermi
çözüldüğünde anlamlıdır — yani A′ ile.
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
from dartrift.observables.momentum_transfer import escape_speed, momentum_transfer  # noqa: E402
from dartrift.setup.refine import refine_scene  # noqa: E402
from dartrift.setup.scene import build_scene  # noqa: E402
from dartrift.validation.g4_ozet import faz45_ozet  # noqa: E402
from dartrift.validation.settling_time import settling_time  # noqa: E402

sys.path.insert(0, str(REPO / "scripts"))
from faz44_dart_yakinsama import SAHNE, _malzeme, _mermi_yaricapi  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--steps", type=int, default=20000)
    ap.add_argument("--every", type=int, default=100)
    ap.add_argument("--spacing", type=float, default=7.0)
    ap.add_argument("--lam", type=int, default=2)
    ap.add_argument("--r-ince", type=float, default=25.0)
    ap.add_argument("--out", default=str(REPO.parent / "faz45_sonuc.json"))
    a = ap.parse_args()

    from dartrift.warp_core.solver_solid import WarpSolid3D

    print("=" * 78, flush=True)
    print("FAZ 4.5 — GEREKEN SIMULE SURE (A′ sahnesinde)", flush=True)
    print("=" * 78, flush=True)

    kaba = build_scene(spacing=a.spacing, device="cpu", **SAHNE)
    ince = build_scene(spacing=a.spacing / a.lam, device="cpu", **SAHNE)
    rs = refine_scene(kaba, ince, r_ince=a.r_ince)
    n = rs.n
    mat = _malzeme()
    r_mermi = _mermi_yaricapi(rs.x, rs.is_impactor)
    print(f"\nsahne: N={n} (ince {rs.diagnostics['n_ince']}, "
          f"kaba {rs.diagnostics['n_kaba']}, mermi {rs.diagnostics['n_mermi']}), "
          f"tasarruf {rs.diagnostics['tasarruf']:.2f}x", flush=True)
    print(f"mermi: capi {2 * r_mermi:.3f} m, yerel aralik "
          f"{rs.spacing_fine:.3f} m -> {2 * r_mermi / rs.spacing_fine:.3f} "
          f"parcacik/cap", flush=True)

    sol = WarpSolid3D(
        np.ascontiguousarray(rs.x), np.ascontiguousarray(rs.v),
        np.ascontiguousarray(rs.m), np.zeros(n), rs.h, mat,
        RefParams(cfl=0.25), alpha0=np.ascontiguousarray(rs.alpha0),
        Y0=np.ascontiguousarray(rs.Y0), device=a.device, check_every=10 ** 9)

    p_imp = rs.impactor_momentum
    m_hedef = rs.target_mass
    v_kacis = escape_speed(m_hedef, rs.target_radius)
    e0 = sol.budgets()["e_tot"]

    # Kesintiye dayanikli iz dosyasi. Onceki kosunun izi varsa USTUNE
    # eklenmesin diye bastan siliniyor -- iki kosunun izi karisirsa
    # `settling_time` iki farkli seriyi tek seri sanardi.
    iz_yolu = Path(a.out).with_suffix(".izler.jsonl")
    iz_yolu.parent.mkdir(parents=True, exist_ok=True)
    if iz_yolu.exists():
        iz_yolu.unlink()

    izler, t_sim, t0 = [], 0.0, time.perf_counter()
    for adim in range(1, a.steps + 1):
        dt = sol.compute_dt()
        sol.step(dt)
        t_sim += dt
        if adim % a.every == 0 or adim == a.steps:
            st = sol.state_numpy()
            if not np.all(np.isfinite(st["v"])):
                print(f"  PATLADI adim {adim}", flush=True)
                break
            b = sol.budgets()
            try:
                mt = momentum_transfer(
                    st["x"], st["v"], st["m"], impactor_momentum=p_imp,
                    center=np.zeros(3), target_mass=m_hedef,
                    target_radius=rs.target_radius,
                    control_radius=2.0 * rs.target_radius,
                    speed_threshold=v_kacis)
                beta_b = float(mt.beta_from_bound)
            except Exception:                              # noqa: BLE001
                beta_b = float("nan")
            izler.append({"adim": adim, "t": t_sim, "beta_bound": beta_b,
                          "e_rel_err": abs(b["e_tot"] - e0) / max(abs(e0), 1e-300)})
            # IZ HEMEN DISKE. Onceki surum HICBIR SEY yazmiyordu; kosu
            # kesilirse (kota, cokme, elektrik) saatlerce sureli is
            # tamamen kayboluyordu. `ensemble_kos` zaten bu dersi
            # ogrenmisti (her nokta hemen yazilir); burada eksikti.
            #
            # Ayri bir `.izler.jsonl`: ana cikti yalnizca kosu BITINCE
            # yazilir ve yarim bir JSON'un "sonuc" sanilma riski olmaz.
            with iz_yolu.open("a", encoding="utf-8") as f:
                f.write(json.dumps(izler[-1]) + "\n")
            if adim % (a.every * 20) == 0:
                print(f"  adim {adim:6d}  t={t_sim:.5e}  beta_b={beta_b:.6f}",
                      flush=True)

    ts = np.array([z["t"] for z in izler])
    bs = np.array([z["beta_bound"] for z in izler])
    ss = np.array([z["adim"] for z in izler])
    d = settling_time(ts, bs, adim=ss)

    # Enerji sapmasi buyume yasasi (B4)
    ee = np.array([z["e_rel_err"] for z in izler])
    m_ok = (ee > 0) & (ss > 0)
    egim = (float(np.polyfit(np.log(ss[m_ok]), np.log(ee[m_ok]), 1)[0])
            if int(m_ok.sum()) >= 3 else float("nan"))

    print(f"\nSONUC ({time.perf_counter() - t0:.1f} s duvar, "
          f"{len(izler)} ornek)", flush=True)
    print(f"  beta_bound son      = {bs[-1] if len(bs) else float('nan'):.6f}",
          flush=True)
    print(f"  DURULDU MU          = {d['durulmus']}"
          f"{'' if d['durulmus'] else '  -- ' + d['neden']}", flush=True)
    print(f"  durulma zamani      = {d['t_durulma']:.6e} s "
          f"(adim {d['adim_durulma']})", flush=True)
    print(f"  enerji log-log egim = {egim:.4f}", flush=True)

    ham = {"n_particles": n, "spacing": a.spacing, "lam": a.lam,
           "r_ince": a.r_ince, "steps_done": int(ss[-1]) if len(ss) else 0,
           "t_sim_end": float(t_sim),
           "beta_bound_final": float(bs[-1]) if len(bs) else float("nan"),
           "beta_bound_settled": bool(d["durulmus"]),
           "beta_bound_settling_time_s": float(d["t_durulma"]),
           "beta_bound_settling_diag": d,
           "energy_drift_loglog_slope": egim,
           "series": izler}
    ham.update(faz45_ozet(ham))
    Path(a.out).write_text(json.dumps(ham, indent=2))
    print(f"\nyazildi: {a.out}", flush=True)
    print("\nG4 ANAHTARLARI", flush=True)
    for k in ("B2_durulmus", "B4_enerji_egim"):
        print(f"    {k:20s} = {ham.get(k, 'KOSULMADI')}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
