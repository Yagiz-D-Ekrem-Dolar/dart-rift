"""FAZ 4.4 SONDA — kurulum çalışıyor mu, hangi `t`'de hangi yarıçap?

Tam ölçüm 5 kol × birkaç koşu. Önce **tek** kol birkaç `t` değerinde
koşuluyor: şok gerçekten yayılıyor mu, patlıyor mu, `r_inner = 0,15`'i
geçip kutu kenarına çarpmadan nerede duruyor?

İlk denemede `E = 5,0e9 J` yazılmıştı ve koşu patladı (özgül enerji
`6,6e7 J/kg`, buharlaşmanın üç katı). Bu sonda o düzeltmenin **çalıştığını**
doğrulamak için.
"""
from __future__ import annotations

import sys

import numpy as np

sys.path.insert(0, "/arf/scratch/egitimg16/driftclaude/dart-rift/src")

from dartrift.validation.solid_interface import (  # noqa: E402
    BASALT_SOLID, E_ENJEKTE, H_OVER_DX, KUTU, RHO0, _kos,
    build_two_zone_solid_ic)

DEV = "cuda:0"
N = 32
R_IC = 0.15


def main() -> int:
    h = H_OVER_DX * KUTU / N
    ic = build_two_zone_solid_ic(N, 1, R_IC, h)
    kutle_enj = float(np.sum(ic["m"][ic["u"] > 1.0e3 * 1.000001]))
    print(f"N = {len(ic['m'])}, h = {h}, E = {E_ENJEKTE:.3e} J", flush=True)
    print(f"enjeksiyon bolgesi: {ic['n_injected']} parcacik, "
          f"{kutle_enj:.2f} kg", flush=True)
    print(f"ozgul enerji      : {E_ENJEKTE / max(kutle_enj, 1e-30):.3e} J/kg "
          f"(E_iv=4.72e6, E_cv=1.82e7)", flush=True)
    print(f"u_max             : {float(np.max(ic['u'])):.3e} J/kg\n", flush=True)

    print(f"{'t (s)':>12s} {'r_sok':>10s} {'rho_max':>10s} {'adim':>8s} "
          f"{'durum':>10s}", flush=True)
    for t in (1.0e-5, 2.0e-5, 5.0e-5, 1.0e-4, 2.0e-4):
        try:
            s = _kos(ic, BASALT_SOLID, DEV, t)
            im = "TAMAM" if s["r_measured"] < 0.45 * KUTU else "KENARDA"
            print(f"{t:>12.3e} {s['r_measured']:>10.6f} {s['rho_max']:>10.1f} "
                  f"{s['n_steps']:>8d} {im:>10s}", flush=True)
        except RuntimeError as e:
            print(f"{t:>12.3e} {'--':>10s} {'--':>10s} {'--':>8s} "
                  f"{'HATA':>10s}  {e}", flush=True)
            break
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
