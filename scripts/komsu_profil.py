"""A52 — gerçek merdiven sahnesinde `hash` ↔ `bvh` adım süresi.

Uzman (Soru 6): "Aday sayısından 100 kat çözücü hızlanması vaat etmem."
Bu betik vaat etmiyor, **ölçüyor**: aynı sahne, aynı malzeme, aynı `dt`
dizisi; önce ısınma, sonra `wp.synchronize` ile zamanlanmış adımlar.
Ayrıca iki kipin durumunu karşılaştırır (yalnız toplama sırası farkı
beklenir).

Kullanim:
    python scripts/komsu_profil.py --kademeler kaba --adim 50 --json p.json
    python scripts/komsu_profil.py --kademeler orta --adim 50
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


def sahne(kademeler: str, spacing: float = 7.0, tohum: int = 20260906):
    from faz5_ensemble_merdiven import MERDIVEN, MERDIVEN_KABA
    from faz48_iki_asama import SAHNE

    from dartrift.inference.design import DART_UZAYI_S3, lhs_design
    from dartrift.inference.forward import sahne_parametreleri
    from dartrift.setup.refine import kademe_ayristir, refine_scene_kademeli
    from dartrift.setup.scene import _build_mesh, build_scene

    th = lhs_design(DART_UZAYI_S3, 24, root_seed=20260906)[0]
    kaba = build_scene(spacing=spacing, device="cpu",
                       **sahne_parametreleri(th, {**SAHNE, "root_seed": tohum}))
    mesh = _build_mesh("icosphere", radius=float(kaba.target_radius), subdiv=4)
    kad = kademe_ayristir(MERDIVEN_KABA if kademeler == "kaba" else MERDIVEN,
                          spacing)
    return refine_scene_kademeli(kaba, mesh, kad), th


def kos(rs, komsu: str, device: str, n_isinma: int, n_adim: int) -> dict:
    import warp as wp
    from faz48_iki_asama import _mat

    from dartrift.cpu_reference.sph_ref import RefParams
    from dartrift.warp_core.solver_solid import WarpSolid3D

    sol = WarpSolid3D(
        np.ascontiguousarray(rs.x), np.ascontiguousarray(rs.v),
        np.ascontiguousarray(rs.m), np.zeros(rs.n), np.ascontiguousarray(rs.h),
        _mat(), RefParams(cfl=0.25), alpha0=np.ascontiguousarray(rs.alpha0),
        Y0=np.ascontiguousarray(rs.Y0), device=device, check_every=10 ** 9,
        komsu_arama=komsu)
    dts = []
    for _ in range(n_isinma):
        dt = sol.compute_dt()
        dts.append(dt)
        sol.step(dt)
    wp.synchronize()
    t0 = time.perf_counter()
    for _ in range(n_adim):
        dt = sol.compute_dt()
        dts.append(dt)
        sol.step(dt)
    wp.synchronize()
    sure = time.perf_counter() - t0
    return {"komsu": komsu, "n": int(rs.n), "s_adim": sure / n_adim,
            "tani": sol.komsu_tanisi(), "st": sol.state_numpy(),
            "dt_ort": float(np.mean(dts))}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kademeler", choices=("kaba", "orta"), default="kaba")
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--isinma", type=int, default=5)
    ap.add_argument("--adim", type=int, default=50)
    ap.add_argument("--json", type=Path, default=None)
    a = ap.parse_args(argv)

    rs, th = sahne(a.kademeler)
    print(f"sahne: {a.kademeler}  N = {rs.n}  h_min {rs.h.min():.3f}  "
          f"h_max {rs.h.max():.3f}  theta {np.round(th, 4)}", flush=True)
    s = {}
    for k in ("hash", "bvh"):
        s[k] = kos(rs, k, a.device, a.isinma, a.adim)
        print(f"  {k:>4}: {s[k]['s_adim'] * 1e3:9.2f} ms/adim   "
              f"{s[k]['tani']}", flush=True)
    fark = {}
    for f in ("x", "v", "u", "rho", "S"):
        A, B = s["hash"]["st"][f], s["bvh"]["st"][f]
        fark[f] = float(np.max(np.abs(A - B)) / (np.max(np.abs(A)) + 1e-300))
    hiz = s["hash"]["s_adim"] / s["bvh"]["s_adim"]
    print(f"  HIZLANMA: {hiz:.2f}x   durum farki (bagil, {a.isinma + a.adim} adim): "
          + "  ".join(f"{k}={v:.2e}" for k, v in fark.items()), flush=True)
    if a.json:
        a.json.write_text(json.dumps({
            "kademeler": a.kademeler, "n": int(rs.n), "device": a.device,
            "adim": a.adim, "hash_s_adim": s["hash"]["s_adim"],
            "bvh_s_adim": s["bvh"]["s_adim"], "hizlanma": hiz,
            "bvh_tani": s["bvh"]["tani"], "durum_farki": fark}, indent=2),
            encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
