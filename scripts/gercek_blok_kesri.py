"""Kampanya noktalarının **gerçekleşen** blok hacim kesri (rapor A74).

v1 yerleştirici hedef kesre ulaşamayınca sessizce doyuyor: aynı
tohumla `f = 0,43` ve `0,55` AYNI geometriyi veriyor (ölçüldü, üç
tohum). G1/G2'nin `f` ekseni `[0,05 , 0,50]` olduğundan, doygunluğun
üstündeki noktalar sahnede **aynı** kesri taşıyor ama analize nominal
değerleriyle girdi.

Bu betik her `(θ, sahne tohumu)` için v1 sahnesini **yeniden kurmadan**
(yalnız yerleştiriciyi koşturarak — deterministik) gerçek hacim kesrini
Monte Carlo ile ölçüyor. `--durumlar` verilirse krater derinliğini de
okuyup `ρ(derinlik, f_nominal)` ile `ρ(derinlik, f_gercek)`'i yan yana
yazıyor.

> **BETİMLEYİCİ.** Protokol G'nin kilitli yargısı değişmez.

Kullanim:
    python scripts/gercek_blok_kesri.py --tasarim-tohumu 20260906 --n-lhs 24 \\
        --sahne-tohum 20260906 99991111 --json gercek_f.json \\
        [--durumlar 'kampanya/G1_uretim_sahne*.durumlar']
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path

import numpy as np

_BURASI = Path(__file__).resolve().parent
sys.path.insert(0, str(_BURASI))
sys.path.insert(0, str(_BURASI.parent / "src"))


def gercek_kesir(f_nominal: float, sahne_tohum: int, *, r_min=14.0,
                 r_max=42.0, q=3.0, radius=82.0, n_mc=200_000) -> dict:
    from dartrift.setup.rubble_generator import blok_hacim_kesri, place_boulders
    from dartrift.setup.scene import _build_mesh

    mesh = _build_mesh("icosphere", radius=radius, subdiv=4)
    bf = place_boulders(mesh, f_nominal, q, r_min, r_max, sahne_tohum)
    mc = blok_hacim_kesri(mesh, bf, root_seed=sahne_tohum, n_ornek=n_mc)
    return {"f_nominal": float(f_nominal), "f_gercek": mc["f"],
            "f_se": mc["se"], "n_blok": int(len(bf.radii)),
            "kure_kesri": float(bf.volume / mesh.volume),
            "doydu": bool(bf.volume < 0.9 * f_nominal * mesh.volume)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tasarim-tohumu", type=int, default=20260906)
    ap.add_argument("--n-lhs", type=int, default=24)
    ap.add_argument("--sahne-tohum", type=int, nargs="+",
                    default=[20260906, 99991111])
    ap.add_argument("--durumlar", nargs="*", default=[])
    ap.add_argument("--json", type=Path, default=None)
    a = ap.parse_args(argv)

    from dartrift.inference.design import DART_UZAYI_S3, lhs_design

    tas = lhs_design(DART_UZAYI_S3, a.n_lhs, root_seed=a.tasarim_tohumu)
    tablo = []
    for st in a.sahne_tohum:
        for th in tas:
            g = gercek_kesir(float(th[2]), st)
            g.update(theta=[float(v) for v in th], sahne_tohum=int(st))
            tablo.append(g)
            print(f"  tohum {st}  f_nom {th[2]:.4f} -> gercek {g['f_gercek']:.4f}"
                  f"  ({g['n_blok']} blok{'  DOYDU' if g['doydu'] else ''})",
                  flush=True)
    n_doy = sum(g["doydu"] for g in tablo)
    print(f"\n{len(tablo)} nokta, {n_doy} doymus "
          f"({100 * n_doy / len(tablo):.0f}%)")

    sonuc = {"tablo": tablo}
    if a.durumlar:
        import ayirt_raporu as ar
        import vekil_posterior as vp

        derin: dict = {}
        for des in a.durumlar:
            for dz in sorted(glob.glob(des)):
                t = vp._tohum_ayikla(dz)
                for k, z in ar._oku(Path(dz)):
                    derin[(t, tuple(np.round(k["theta"], 12)))] = ar._krater(z)
        fn, fg, d = [], [], []
        for g in tablo:
            anah = (str(g["sahne_tohum"]), tuple(np.round(g["theta"], 12)))
            if anah in derin and np.isfinite(derin[anah]):
                fn.append(g["f_nominal"])
                fg.append(g["f_gercek"])
                d.append(derin[anah])
        if d:
            r_n, r_g = ar.spearman(fn, d), ar.spearman(fg, d)
            p_n = ar.permutasyon_p(fn, d, n=5000)
            p_g = ar.permutasyon_p(fg, d, n=5000)
            print(f"\neslesen {len(d)} nokta:")
            print(f"  rho(krater, f_nominal) = {r_n:+.4f}  p = {p_n:.4f}")
            print(f"  rho(krater, f_gercek)  = {r_g:+.4f}  p = {p_g:.4f}")
            sonuc["korelasyon"] = {"n": len(d), "rho_nominal": r_n,
                                   "p_nominal": p_n, "rho_gercek": r_g,
                                   "p_gercek": p_g}
    if a.json:
        a.json.write_text(json.dumps(sonuc, indent=1), encoding="utf-8")
        print(f"yazildi: {a.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
