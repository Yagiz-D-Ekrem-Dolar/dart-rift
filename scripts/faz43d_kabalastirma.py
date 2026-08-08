"""ADR-0043 gereksinim #2: **kabalaştırmanın korunum hatası.**

`tests/test_coarsen.py` operatörün *sentetik* veride korunumlu
olduğunu gösteriyor. Bu betik onu **gerçek sahnede, gerçek bir
aşama-1 durumunda** ölçüyor — ikisi aynı şey değil:

| sentetik | gerçek |
|---|---|
| rastgele hızlar, yığın akış yok | şok cephesi + yığın akış |
| `ε` civarı iç enerji | Tillotson EOS'tan gelen büyük `e` |
| uniform kütle | `α₀`'a bağlı, kaya blokları var |

## Asıl soru korunum **değil**

Korunum yapı gereği tam (bölüntü + kütle ağırlığı). Ölçülmesi gereken
iki şey başka:

1. **`ısıya dönen kinetik oran`** — aktarım kaba parçacığı ne kadar
   ısıtıyor? Büyükse aşama-2 yapay olarak sıcak başlar.
2. **Açısal momentum kaybı** — grup dönüşü siliniyor; gerçek sahnede
   ne kadar?

> Korunum hatası zaten `~1e-16` çıkacak. Onu *"başarı"* diye
> raporlamak yanıltıcı olurdu; asıl bulgu 1 ve 2.
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
from dartrift.setup.coarsen import coarsen_to_sites  # noqa: E402
from dartrift.setup.refine import refine_scene_local  # noqa: E402
from dartrift.setup.scene import _build_mesh, build_scene  # noqa: E402

sys.path.insert(0, str(REPO / "scripts"))
from faz44_dart_yakinsama import SAHNE, _malzeme  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--lam", type=float, default=19.0)
    ap.add_argument("--r-ince", type=float, default=3.0)
    ap.add_argument("--t1", type=float, nargs="+",
                    default=[1.0e-4, 1.0e-3, 5.0e-3])
    ap.add_argument("--steps", type=int, default=200000)
    ap.add_argument("--out", default=str(REPO.parent / "faz43d_sonuc.json"))
    a = ap.parse_args()

    from dartrift.warp_core.solver_solid import WarpSolid3D

    print("=" * 78, flush=True)
    print("ADR-0043 #2 — KABALASTIRMANIN KORUNUM HATASI (gercek sahne)",
          flush=True)
    print("=" * 78, flush=True)

    kaba = build_scene(spacing=7.0, device="cpu", **SAHNE)
    mesh = _build_mesh("icosphere", radius=SAHNE["radius"], subdiv=4)
    rs = refine_scene_local(kaba, mesh, r_ince=a.r_ince, lam=a.lam)
    siteler = rs.diagnostics["cikarilan_kaba_x"]
    ince = np.asarray(rs.is_fine, dtype=bool)
    print(f"\nsahne N={rs.n}, ince={int(ince.sum())} "
          f"(mermi dahil), hedef site={len(siteler)}", flush=True)
    print(f"  s_ince={rs.spacing_fine:.4f} m, s_kaba={rs.spacing_coarse:.4f} m",
          flush=True)
    if len(siteler) == 0:
        print("  HEDEF SITE YOK — kabalastirma olculemez", flush=True)
        return 1

    sol = WarpSolid3D(
        np.ascontiguousarray(rs.x), np.ascontiguousarray(rs.v),
        np.ascontiguousarray(rs.m), np.zeros(rs.n), rs.h, _malzeme(),
        RefParams(cfl=0.25), alpha0=np.ascontiguousarray(rs.alpha0),
        Y0=np.ascontiguousarray(rs.Y0), device=a.device, check_every=10 ** 9)

    kayitlar, t_sim, hedefler = [], 0.0, sorted(float(t) for t in a.t1)
    print(f"\n{'t1':>10} {'kutle':>10} {'momentum':>10} {'enerji':>10} "
          f"{'ACISAL':>10} {'ISIYA%':>8} {'grup_max':>9}", flush=True)
    print("-" * 78, flush=True)

    for hedef in hedefler:
        while t_sim < hedef * (1.0 - 1e-12):
            dt = sol.compute_dt()
            if t_sim + dt > hedef:
                dt = hedef - t_sim
            sol.step(dt)
            t_sim += dt
        st = sol.state_numpy()
        if not np.all(np.isfinite(st["v"])):
            print(f"  t1={hedef:.1e} PATLADI — atlandi", flush=True)
            continue
        # `e` cozucude yoksa sifir alinir; korunum yine TAM olur ama
        # "isiya donen oran" o zaman TOPLAM ic enerjiye gore degil,
        # yalnizca sacilima gore anlamlidir. Hangisi oldugu yazilir.
        e = st.get("e", st.get("u", None))
        e_var = e is not None
        e = np.zeros(rs.n) if not e_var else np.asarray(e, np.float64)
        out = coarsen_to_sites(st["x"][ince], st["v"][ince], rs.m[ince],
                               e[ince], siteler,
                               alpha0=rs.alpha0[ince], Y0=rs.Y0[ince],
                               is_boulder=rs.is_boulder[ince])
        k = out["korunum"]
        k["t1"] = hedef
        k["ic_enerji_cozucuden"] = bool(e_var)
        kayitlar.append(k)
        print(f"{hedef:10.1e} {k['kutle_hata']:10.2e} "
              f"{k['momentum_hata']:10.2e} {k['enerji_hata']:10.2e} "
              f"{k['acisal_momentum_hata']:10.2e} "
              f"{100 * k['ice_donen_kinetik_oran']:8.3f} "
              f"{k['grup_en_buyuk']:9d}", flush=True)

    print("-" * 78, flush=True)
    if kayitlar:
        en_kotu = max(kayitlar, key=lambda z: max(
            z["kutle_hata"], z["momentum_hata"], z["enerji_hata"]))
        gecti = (en_kotu["kutle_hata"] < 1e-12
                 and en_kotu["momentum_hata"] < 1e-12
                 and en_kotu["enerji_hata"] < 1e-12)
        print(f"\nKORUNUM (uc olcut de < 1e-12): "
              f"{'GECTI' if gecti else 'DUSTU'}", flush=True)
        print(f"  giren ince parcacik  = {kayitlar[-1]['n_giren']}", flush=True)
        print(f"  cikan kaba parcacik  = {kayitlar[-1]['n_cikan']}", flush=True)
        print(f"  bos kalan site       = {kayitlar[-1]['n_bos_site']}",
              flush=True)
        print("\nASIL BULGULAR (korunum degil):", flush=True)
        print(f"  acisal momentum kaybi = "
              f"{100 * kayitlar[-1]['acisal_momentum_hata']:.2f}%  "
              f"-- KORUNMUYOR, ADR-0043 §5'te yazili", flush=True)
        print(f"  isiya donen kinetik   = "
              f"{100 * kayitlar[-1]['ice_donen_kinetik_oran']:.3f}%  "
              f"-- asama-2 bu kadar yapay sicak baslar", flush=True)
    else:
        print("\nHICBIR t1 OLCULEMEDI — kayit bulunamadi", flush=True)

    Path(a.out).write_text(json.dumps(
        {"lam": a.lam, "r_ince": a.r_ince, "N": rs.n,
         "n_site": int(len(siteler)), "kayitlar": kayitlar}, indent=2,
        default=float))
    print(f"\nyazildi: {a.out}", flush=True)
    return 0 if kayitlar else 1


if __name__ == "__main__":
    raise SystemExit(main())
