"""**Kademe sınavı**: ara basamak eklemek şokun duvarı aşmasını sağlıyor mu?

## Soru

A25 ölçtü: `λ₂ = 20`'de ince parçacık `46,6 kg`, hemen dışındaki
`372 834 kg` — **arayüz oranı `8 000`** — ve cephe orada
**`0,0 m/s`** ile duruyor.

Bu betik, aynı ince çekirdeği **ara basamakla** koşuyor ve cephenin
duvarı aşıp aşmadığına bakıyor. Aktarım devrede **değil** (tek
aşama), böylece ölçülen şey yalnızca **kademe**.

| şema | basamaklar | en dik |
|---|---|---|
| bugün (tek basamak) | `0,35 -> 7,0` | **`8 000`** |
| üç seviyeli `λ₂ = 8` | `0,35 -> 0,875 -> 7,0` | `512` |
| **üç seviyeli `λ₂ = 4`** | `0,35 -> 1,75 -> 7,0` | **`125`** |

`λ₂ = 4` iki basamağı **dengeliyor** (`125` ve `64`); `λ₂ = 8`
ikinciyi `512`'de bırakıyor. Denge, en dik basamağı en aza indirmenin
doğru yolu.

## Neden `faz48` yetmiyor

`--tek-asama` yalnızca **iki** seviye kurabiliyor
(`refine_scene_local`), iki aşamalı yol ise araya **aktarımı**
sokuyor. Bu betik üç seviyeli sahneyi kurup **aktarımsız** koşuyor.
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
sys.path.insert(0, str(REPO / "scripts"))

from arayuz_orani import oranlar  # noqa: E402
from faz48_iki_asama import (  # noqa: E402
    SAHNE,
    _cozucu,
    _kos,
    _mat,
    _sahne_kolu,
)
from sok_cephesi import cephe  # noqa: E402
from sok_sinavi import sinav  # noqa: E402

from dartrift.setup.refine import (  # noqa: E402
    kademe_ayristir,
    refine_scene_kademeli,
    refine_scene_ucseviye,
)
from dartrift.setup.scene import _build_mesh, build_scene  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lam1", type=float, default=20.0)
    ap.add_argument("--r1", type=float, default=3.0)
    ap.add_argument("--lam2", type=float, default=4.0)
    ap.add_argument("--r2", type=float, default=12.0)
    ap.add_argument("--t-end", type=float, default=4.767e-3)
    ap.add_argument("--azami-adim", type=int, default=200000)
    ap.add_argument("--device", default="cuda:0")
    # MERDIVEN: `r:lam` ciftleri, DISTAN ICE. Ornek:
    #   --kademeler 48:2.8 24:1.4 12:0.7 6:0.35 3:0.175   (r:s, METRE)
    # Uc seviyeli yol bir ara basamak ekler; merdiven gerekeni kadar.
    ap.add_argument("--kademeler", nargs="+", default=None,
                    help="r:s ciftleri, ikisi de METRE (distan ice); "
                         "verilirse uc seviyeli yol yerine MERDIVEN kurulur")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    t0 = time.perf_counter()
    kaba = build_scene(spacing=3.5, device="cpu", **_sahne_kolu(False))
    mesh = _build_mesh("icosphere", radius=SAHNE["radius"], subdiv=4)
    if a.kademeler:
        kad = kademe_ayristir(a.kademeler, kaba.spacing)
        s = refine_scene_kademeli(kaba, mesh, kad)
        etiket = "MERDIVEN " + " ".join(a.kademeler)
    else:
        s = refine_scene_ucseviye(kaba, mesh, r1=a.r1, lam1=a.lam1,
                                  r2=a.r2, lam2=a.lam2)
        etiket = f"UC SEVIYE lam1={a.lam1} (r<{a.r1}) lam2={a.lam2} (r<{a.r2})"
    hedef = ~np.asarray(s.is_impactor, dtype=bool)
    ar = oranlar(np.asarray(s.m)[hedef])
    print(f"KADEME SINAVI  {etiket}  N={s.n}", flush=True)
    print("  seviyeler (kg): "
          + " -> ".join(f"{v:,.1f}" for v in ar["seviyeler"]), flush=True)
    print(f"  EN DIK BASAMAK: {ar['en_dik']:,.0f}x  ({ar['yargi']})",
          flush=True)

    sol = _cozucu(s.x, s.v, s.m, np.zeros(s.n), s.h,
                  np.asarray(s.alpha0), np.asarray(s.Y0), a.device,
                  mat=_mat())
    t = _kos(sol, 0.0, a.t_end, a.azami_adim, "kademe")
    st = sol.state_numpy()

    mp = np.asarray(kaba.impact_point, dtype=np.float64)
    c = cephe(st["rho"][hedef], np.asarray(s.alpha0)[hedef],
              np.asarray(s.x)[hedef], mp, st["m"][hedef])
    sv = sinav(st["rho"][hedef], st["u"][hedef], st["m"][hedef],
               alpha0=np.asarray(s.alpha0)[hedef])
    print(f"\n  t_sim = {t:.5e}", flush=True)
    r_ic0 = float(a.kademeler[-1].split(":")[0]) if a.kademeler else a.r1
    print(f"  CEPHE   = {c['cephe_m']:.2f} m  (en ince bolge siniri "
          f"{r_ic0:.1f} m)  kalinlik {c['kalinlik_m']:.2f} m", flush=True)
    print(f"  sikisma = %{sv['sikisma_max_yuzde']:.3f}  [{sv['yargi']}]  "
          f"soklanan {c['kutle_kg']:,.0f} kg", flush=True)
    r_ic = float(a.kademeler[-1].split(":")[0]) if a.kademeler else a.r1
    gecti = c["cephe_m"] > r_ic * 1.05
    print(f"\n  DUVARI ASTI MI: {'EVET' if gecti else 'HAYIR'}", flush=True)

    Path(a.out).write_text(json.dumps({
        "sema": etiket, "kademeler": a.kademeler,
        "lam1": a.lam1, "r1": a.r1, "lam2": a.lam2, "r2": a.r2,
        "N": s.n, "t_sim": t, "en_dik_basamak": ar["en_dik"],
        "seviyeler_kg": [float(v) for v in ar["seviyeler"]],
        "cephe": c, "sok": {k: sv[k] for k in
                            ("sikisma_max_yuzde", "yargi", "n_yuzde5_ustu")},
        "duvari_asti": bool(gecti),
        "duvar_s": time.perf_counter() - t0,
    }, indent=2))
    np.savez_compressed(
        Path(a.out).with_suffix(".son_durum.npz"),
        x=st["x"], v=st["v"], m=st["m"],
        x_referans=np.asarray(s.x, dtype=np.float64), hedef=hedef,
        u=st["u"], rho=st["rho"],
        alpha0=np.asarray(s.alpha0, dtype=np.float64), t=t)
    print(f"\nyazildi: {a.out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
