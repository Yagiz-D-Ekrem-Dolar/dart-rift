"""FAZ 4.8 — **iki aşamalı koşu**: `A1`'i geçirmenin tek yolu.

G4 kapısının düşen **tek** ölçütü `A1 = 0,215` (eşik `2,0`): mermi
çözülmemiş. Tek çözüm `λ ≈ 19` ve tek uygulanabilir yol ADR-0043'ün
iki aşamalı şeması.

```
aşama-1   λ=19, r_iç=3 m    0 → t₁ = 4,767e-3 s     A1 = 2,04 ✔
   ↓      Lagrange'cı kabalaştırma (ADR-0043 §4d)
aşama-2   λ=2,  r_iç=25 m   t₁ → t_end              ensemble bedeli
```

## Ne ölçülüyor

| | |
|---|---|
| `A1` | **aşama-1'den** — mermi orada çözülmüş olmalı |
| `β` | **aşama-2'nin sonundan** |
| kütle/momentum/enerji | aktarımda korunuyor mu |
| komşu sağlığı | aşama-2 aktarılanları SPH ile ilerletebiliyor mu |

## Tek aşamalı kontrol kolu **zorunlu**

`--tek-asama` aynı `t_end`'e `λ=2` ile tek başına gider. İki koşunun
`β`'sı karşılaştırılmadan iki aşamanın *"işe yaradığı"* söylenemez —
yalnızca *"koştuğu"* söylenebilir.

> Beklenti: `β` **değişmeli**. Değişmezse mermiyi çözmek `β`'yı
> etkilemiyor demektir ve o zaman `A1` eşiğinin kendisi sorgulanmalı
> (ADR-0026'ya geri dönülür).
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
    escape_speed, momentum_transfer)
from dartrift.setup.refine import (refine_scene_local,  # noqa: E402
                                   refine_scene_ucseviye)
from dartrift.setup.scene import _build_mesh, build_scene  # noqa: E402
from dartrift.setup.two_stage import (  # noqa: E402
    asama2_sahnesi_ucseviye)

sys.path.insert(0, str(REPO / "scripts"))
from faz44_dart_yakinsama import SAHNE, _malzeme  # noqa: E402

#: FAZ 4.5'in ölçtüğü bağlanma süresi (`faz43c`, ADR-0043 §4a).
T1_OLCULEN = 4.767e-3


def _cozucu(x, v, m, u, h, alpha0, Y0, device):
    from dartrift.warp_core.solver_solid import WarpSolid3D
    return WarpSolid3D(
        np.ascontiguousarray(x), np.ascontiguousarray(v),
        np.ascontiguousarray(m), np.ascontiguousarray(u),
        np.ascontiguousarray(h), _malzeme(), RefParams(cfl=0.25),
        alpha0=np.ascontiguousarray(alpha0), Y0=np.ascontiguousarray(Y0),
        device=device, check_every=10 ** 9)


def _kos(sol, t_bas: float, t_end: float, azami: int, etiket: str) -> float:
    """`t_end`'e kadar ilerlet; son adım **kırpılır**."""
    t = float(t_bas)
    for adim in range(1, azami + 1):
        dt = sol.compute_dt()
        if t + dt > t_end:
            dt = t_end - t
        sol.step(dt)
        t += dt
        if adim % 500 == 0:
            print(f"    {etiket} adim {adim:6d}  t={t:.5e}", flush=True)
        if t >= t_end * (1.0 - 1e-12):
            break
    if not np.all(np.isfinite(sol.state_numpy()["v"])):
        raise RuntimeError(f"{etiket} PATLADI (t={t:.4e})")
    return t


def _beta(st, sahne_gibi, p_imp, m_hedef, R) -> dict:
    mt = momentum_transfer(
        st["x"], st["v"], st["m"], impactor_momentum=p_imp,
        center=np.zeros(3), target_mass=m_hedef, target_radius=R,
        control_radius=2.0 * R, speed_threshold=escape_speed(m_hedef, R))
    return {"beta": float(mt.beta), "beta_bound": float(mt.beta_from_bound),
            "n_ejekta": int(mt.n_ejecta),
            "momentum_kapanis": float(mt.momentum_closure)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--lam1", type=float, default=19.0)
    ap.add_argument("--r-ince1", type=float, default=3.0)
    ap.add_argument("--lam2", type=float, default=2.0)
    ap.add_argument("--r-ince2", type=float, default=25.0)
    ap.add_argument("--t1", type=float, default=T1_OLCULEN)
    ap.add_argument("--t-end", type=float, default=0.20)
    ap.add_argument("--azami-adim", type=int, default=200000)
    ap.add_argument("--tek-asama", action="store_true",
                    help="kontrol kolu: lam=2 ile TEK BASINA t_end'e git")
    ap.add_argument("--out", default=str(REPO.parent / "faz48_sonuc.json"))
    a = ap.parse_args()

    print("=" * 78, flush=True)
    print("FAZ 4.8 — IKI ASAMALI KOSU (ADR-0043)", flush=True)
    print("=" * 78, flush=True)

    kaba = build_scene(spacing=7.0, device="cpu", **SAHNE)
    mesh = _build_mesh("icosphere", radius=SAHNE["radius"], subdiv=4)
    R = float(kaba.target_radius)
    t0 = time.perf_counter()

    a2 = refine_scene_local(kaba, mesh, r_ince=a.r_ince2, lam=a.lam2)
    p_imp = a2.impactor_momentum
    m_hedef = a2.target_mass

    # ---------------------------------------------------- KONTROL KOLU
    if a.tek_asama:
        print(f"\nKONTROL KOLU: tek asama, lam={a.lam2}, N={a2.n}", flush=True)
        sol = _cozucu(a2.x, a2.v, a2.m, np.zeros(a2.n), a2.h,
                      a2.alpha0, a2.Y0, a.device)
        t = _kos(sol, 0.0, a.t_end, a.azami_adim, "tek")
        b = _beta(sol.state_numpy(), a2, p_imp, m_hedef, R)
        print(f"\n  t_sim = {t:.5e}  beta = {b['beta']:.6f}", flush=True)
        Path(a.out).write_text(json.dumps(
            {"kip": "tek_asama", "lam": a.lam2, "N": a2.n, "t_sim": t,
             "duvar_s": time.perf_counter() - t0, **b}, indent=2))
        print(f"\nyazildi: {a.out}", flush=True)
        return 0

    # ---------------------------------------------------------- ASAMA 1
    # UC SEVIYELI (ADR-0043 §4f). Iki seviyelide t1'de momentumun %69'u
    # ince bolgenin DISINDA kaliyor ve aktarimda ATILIYORDU
    # (momentum kapanisi 0.690 OLCULDU).
    a1 = refine_scene_ucseviye(kaba, mesh, r1=a.r_ince1, lam1=a.lam1,
                               r2=a.r_ince2, lam2=a.lam2)
    ince1 = np.asarray(a1.is_fine, dtype=bool)
    mermi = np.asarray(a1.is_impactor, dtype=bool)
    cap = 2.0 * float(np.max(np.linalg.norm(
        a1.x[mermi] - a1.x[mermi].mean(axis=0)[None, :], axis=1)))
    A1 = cap / a1.spacing_fine
    print(f"\nASAMA-1: lam={a.lam1}, r_ic={a.r_ince1} m, N={a1.n} "
          f"(ince {int(ince1.sum())})", flush=True)
    print(f"  s_ince = {a1.spacing_fine:.4f} m", flush=True)
    print(f"  A1 = {A1:.4f}  ({'COZULMUS' if A1 >= 2.0 else 'COZULMEMIS'}) "
          f"-- esik 2.0", flush=True)

    sol1 = _cozucu(a1.x, a1.v, a1.m, np.zeros(a1.n), a1.h,
                   a1.alpha0, a1.Y0, a.device)
    t = _kos(sol1, 0.0, a.t1, a.azami_adim, "a1")
    print(f"  asama-1 bitti: t = {t:.5e} s "
          f"({time.perf_counter() - t0:.1f} s duvar)", flush=True)
    st1 = sol1.state_numpy()

    # ------------------------------------------------------ KABALASTIR
    sahne = asama2_sahnesi_ucseviye(a1, st1)
    d = sahne.diagnostics
    print(f"\nAKTARIM (Lagrange'ci, UC SEVIYELI):", flush=True)
    print(f"  {d['n_asama1_ince']} cekirdek -> {d['n_aktarilan']} parcacik",
          flush=True)
    print(f"  birebir kopyalanan = {d['n_kopyalanan']}   "
          f"atilan = {d['n_asama2_atilan']}", flush=True)
    print(f"  SAHNE momentum hatasi = {d['sahne_momentum_hatasi']:.3e}  "
          f"kutle = {d['sahne_kutle_hatasi']:.3e}", flush=True)
    print(f"  toplam N = {d['n_toplam']}", flush=True)
    print(f"  korunum: kutle {d['kutle_hata']:.2e}  "
          f"momentum {d['momentum_hata']:.2e}  enerji {d['enerji_hata']:.2e}",
          flush=True)
    print(f"  atama mesafesi = {d['atama_mesafe_max'] / d['s_asama2']:.3f} "
          f"hucre", flush=True)
    print(f"  isiya donen = {100 * d['ice_donen_kinetik_oran']:.3f}%",
          flush=True)
    print(f"  komsu medyan = {d['komsu']['komsu_medyan']:.0f}  "
          f"(<30 orani {d['komsu']['yalniz_oran']:.3f})", flush=True)

    # ---------------------------------------------------------- ASAMA 2
    print(f"\nASAMA-2: lam={a.lam2}, N={sahne.n}, t {t:.4e} -> {a.t_end}",
          flush=True)
    sol2 = _cozucu(sahne.x, sahne.v, sahne.m, sahne.e, sahne.h,
                   sahne.alpha0, sahne.Y0, a.device)
    t2 = _kos(sol2, t, a.t_end, a.azami_adim, "a2")
    b = _beta(sol2.state_numpy(), sahne, p_imp, m_hedef, R)

    print(f"\nSONUC ({time.perf_counter() - t0:.1f} s duvar)", flush=True)
    print(f"  A1        = {A1:.4f}  "
          f"({'GECTI' if A1 >= 2.0 else 'DUSTU'})", flush=True)
    print(f"  t_sim     = {t2:.5e} s", flush=True)
    print(f"  beta      = {b['beta']:.6f}", flush=True)
    print(f"  n_ejekta  = {b['n_ejekta']}", flush=True)
    print(f"  momentum kapanisi = {b['momentum_kapanis']:.3e}", flush=True)
    print("\n  KARSILASTIRMA icin: --tek-asama kolunu da kos.", flush=True)

    Path(a.out).write_text(json.dumps(
        {"kip": "iki_asama", "lam1": a.lam1, "r_ince1": a.r_ince1,
         "lam2": a.lam2, "r_ince2": a.r_ince2, "t1": a.t1, "t_sim": t2,
         "A1": A1, "A1_gecti": bool(A1 >= 2.0),
         "N_asama1": a1.n, "N_asama2": sahne.n,
         "aktarim": {k: v for k, v in d.items() if k != "atama"},
         "duvar_s": time.perf_counter() - t0, **b}, indent=2, default=float))
    print(f"\nyazildi: {a.out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
