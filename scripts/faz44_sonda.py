"""FAZ 4.4 SONDA — kurulum çalışıyor mu, hangi `t`'de hangi yarıçap?

Bu betik **tanılayıcıdır**, geçer/kalır değil: her `t` için ne olduğunu
yazar ve devam eder. İlk sürümü ilk hatada `break` ediyordu ve `t = 1e-5`
sonucundan sonrasını hiç görmedim — oysa basaltta ses `r = 0,3`'e
`0,3/3162 ≈ 9,5e-5 s`'de varır, yani ilgilenilen ölçek **on kat** ötedeydi.
"""
from __future__ import annotations

import sys

import numpy as np

from pathlib import Path  # noqa: E402

# Depo koku __file__'DAN turetiliyor, sabit yazilmiyor: depo
# tasindiginda ya da baska bir kullaniciyla kosuldugunda sabit
# yol SESSIZCE yanlis src'yi bulur (ya da hic bulmaz).
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from dartrift.cpu_reference.sph_ref import RefParams  # noqa: E402
from dartrift.validation.solid_interface import (  # noqa: E402
    BASALT_SOLID, CEPHE_ESIKLERI, E_ENJEKTE, H_OVER_DX, KUTU, RHO0,
    build_two_zone_solid_ic, cephe_yaricapi)

DEV = "cuda:0"
N = 32
R_IC = 0.15


def main() -> int:
    from dartrift.warp_core.solver_solid import WarpSolid3D

    h = H_OVER_DX * KUTU / N
    ic = build_two_zone_solid_ic(N, 1, R_IC, h)
    sicak = ic["u"] > 1.0e3 * 1.000001
    print(f"N = {len(ic['m'])}, h = {h}, E = {E_ENJEKTE:.3e} J", flush=True)
    print(f"enjeksiyon: {ic['n_injected']} parcacik, "
          f"{float(np.sum(ic['m'][sicak])):.2f} kg, "
          f"ozgul {E_ENJEKTE / float(np.sum(ic['m'][sicak])):.3e} J/kg", flush=True)
    print(f"basaltta ses ~3162 m/s -> r=0.3'e ~9.5e-5 s\n", flush=True)

    sol = WarpSolid3D(ic["x"], ic["v"], ic["m"], ic["u"], ic["h"],
                      BASALT_SOLID, RefParams(cfl=0.2), device=DEV)
    sol._eval()
    st0 = sol.state_numpy()
    print(f"BASLANGIC: rho ortanca={float(np.median(st0['rho'])):.2f} "
          f"(rho0={RHO0}, gozeneklilik acikken rho0/alpha0={RHO0 / 1.5:.0f} "
          f"BEKLENIR), P en buyuk={float(np.max(st0['P'])):.3e}", flush=True)

    bas = "  ".join(f"{'r@' + format(e, '.2f'):>7s}" for e in CEPHE_ESIKLERI)
    print(f"\n{'t (s)':>11s} {'rho_max':>9s} {'v_max':>9s} {'adim':>7s}  {bas}",
          flush=True)
    for t in (2.0e-5, 5.0e-5, 1.0e-4, 2.0e-4, 4.0e-4):
        sol = WarpSolid3D(ic["x"], ic["v"], ic["m"], ic["u"], ic["h"],
                          BASALT_SOLID, RefParams(cfl=0.2), device=DEV)
        tani = sol.run(t, max_steps=500_000)
        st = sol.state_numpy()
        if not np.all(np.isfinite(st["rho"])):
            print(f"{t:>11.3e}  PATLADI (rho sonlu degil)", flush=True)
            break
        rmax = float(np.max(st["rho"]))
        vmax = float(np.max(np.linalg.norm(st["v"], axis=1)))
        yaricaplar = []
        for e in CEPHE_ESIKLERI:
            try:
                yaricaplar.append(f"{cephe_yaricapi(st['x'], st['v'], e):.4f}")
            except RuntimeError:
                yaricaplar.append("  --  ")
        print(f"{t:>11.3e} {rmax:>9.1f} {vmax:>9.2f} "
              f"{tani['n_steps']:>7d}  " + "  ".join(f"{v:>7s}" for v in yaricaplar),
              flush=True)
        if tani["t_end"] < t * (1.0 - 1e-9):
            print(f"            (t_end'e ulasilamadi: {tani['t_end']:.3e})",
                  flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
