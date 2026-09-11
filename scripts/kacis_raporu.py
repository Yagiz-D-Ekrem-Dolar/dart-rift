"""Kampanya durumlarına **enerji tabanlı kaçış sınıflaması** (uzman Soru 10).

`momentum_defteri` kaçışı `r > R` ve `v_r > v_esc` ile tanımlıyor;
`24 ms`'de kazılan maddenin çoğu henüz `R`'nin içinde ve sayılmıyor.
`observables/kacis.py` bağlı kalan kütleden yinelemeli `ε` ölçütü
kullanıyor. Bu betik iki tanımı **yan yana** yazıyor ve θ eksenleriyle
ilişkilerine bakıyor.

> **BETİMLEYİCİ.** Hiçbir kilitli protokolün yargısı değişmez.

Kullanim:
    python scripts/kacis_raporu.py --kol G2 'kampanya/G2_kirpik_sahne*.durumlar' \\
        --json kacis.json
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


def nokta(z) -> dict:
    from dartrift.observables.kacis import kacis_siniflari
    from dartrift.observables.momentum_defteri import momentum_defteri
    from dartrift.observables.momentum_transfer import escape_speed

    m = np.asarray(z["m"], float)
    f = np.asarray(z["mermi_kesri"], float)
    R = float(z["R"])
    hedef = f < 0.5
    v_esc = float(escape_speed(float(m[hedef].sum()), R))
    md = momentum_defteri(z["x"], z["v"], m, mermi_kesri=f, R=R, v_esc=v_esc,
                          ehat=np.asarray(z["ehat"], float),
                          p_imp=float(z["p_imp"]))
    ks = kacis_siniflari(z["x"], z["v"], m, R=R, x0=z["x_referans"],
                         mermi_kesri=f, ehat=z["ehat"], p_imp=float(z["p_imp"]))
    return {"theta": np.asarray(z["theta"], float).ravel().tolist(),
            "beta_defter": md["beta_hedef"], "M_defter": md["M_ejekta"],
            "beta_enerji": ks["beta_enerji"],
            "M_bagsiz_hedef": ks["M_bagsiz_hedef"],
            "M_bagsiz_iceride_hedef": ks["M_bagsiz_iceride_hedef"],
            "M_ayrilmis_hedef": ks.get("M_ayrilmis_hedef", float("nan")),
            "yakinsadi": ks["yakinsadi"], "n_tur": ks["n_tur"],
            "n_sinirda": ks["n_sinirda"]}


def main(argv=None) -> int:
    import ayirt_raporu as ar
    import vekil_posterior as vp

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kol", nargs=2, action="append", metavar=("AD", "DESEN"),
                    required=True)
    ap.add_argument("--json", type=Path, default=None)
    a = ap.parse_args(argv)
    cikti = {}
    for ad, desen in a.kol:
        satirlar = []
        for dz in sorted(glob.glob(desen)):
            t = vp._tohum_ayikla(dz)
            for yol in sorted(Path(dz).glob("nokta_*.npz")):
                k = nokta(np.load(yol))
                k["tohum"] = t
                satirlar.append(k)
                print(f"  [{ad}] {yol.name[:26]} beta defter {k['beta_defter']:.5f}"
                      f"  enerji {k['beta_enerji']:.5f}  M_bagsiz {k['M_bagsiz_hedef']:.4g}"
                      f" (iceride {k['M_bagsiz_iceride_hedef']:.4g})", flush=True)
        oz = {"n": len(satirlar)}
        if len(satirlar) >= 4:
            th = np.array([s["theta"] for s in satirlar])
            for nic in ("beta_defter", "beta_enerji", "M_bagsiz_hedef"):
                y = np.array([s[nic] for s in satirlar])
                oz[nic] = {e: {"rho": ar.spearman(d, y),
                               "p": ar.permutasyon_p(d, y, n=5000)}
                           for e, d in (("blok_alpha0", th[:, 0]),
                                        ("matris_Y0", np.log10(th[:, 1])),
                                        ("blok_kesri", th[:, 2]))}
                print(f"  {ad} {nic:>15}: " + "  ".join(
                    f"{e} rho={v['rho']:+.3f} p={v['p']:.4f}"
                    for e, v in oz[nic].items()), flush=True)
        cikti[ad] = {"ozet": oz, "noktalar": satirlar}
        if a.json:
            a.json.write_text(json.dumps(cikti, indent=1, default=float),
                              encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
