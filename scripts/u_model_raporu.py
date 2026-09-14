"""Protokol U — model yeterliliği: hangi varyant β'yı DART gözlem bandına taşıyor? (kilitli)

Tek faktörlü tarama, merkez θ `(1,15 ; 1e5 ; 0,275)`, plato anı `0,1 s`,
üretim fiziği (kesme + taban), matris sahası, iki tohum. Varyantlar
`truba/is_U_model.slurm`'da. Önsel dışı Y₀ varyantları **çıkarım verisi
değildir** — yalnız modelin gözleme ulaşıp ulaşamadığını sorar.

Varyant başına: iki tohum ortalaması `β̄−1`; gözlenen β **o varyantın kendi
hedef kütlesiyle** (`dart_gozlem_posterior.gozlenen_beta`).

    z = (β−1_gözlem − β̄−1_sim) / σ_β

- `|z| ≤ 2` → **BANDA ULAŞIYOR**
- `z > 2` → **ALTINDA** (model az momentum aktarıyor)
- `z < −2` → **ÜSTÜNDE**

Taban (U0) ile fark: `Δ = β̄−1(Uk) − β̄−1(U0)`, tohum yarı farkı ölçeğinde.

Genel: en az bir varyant BANDA ULAŞIYOR → **MODEL GÖZLEME ULAŞABİLİYOR**
(varyant listesi); hiçbiri → **HİÇBİR VARYANT ULAŞMIYOR** (en yakın ve `z`).

Kullanim:
    python scripts/u_model_raporu.py --kok kampanya --json kampanya/S_U.json
"""
from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from pathlib import Path

import numpy as np

_BURASI = Path(__file__).resolve().parent
sys.path.insert(0, str(_BURASI))
sys.path.insert(0, str(_BURASI.parent / "src"))

VARYANTLAR = {
    "U0": "taban (uretim)",
    "U1": "Y0 = 1e1 Pa (onsel disi)",
    "U2": "Y0 = 1e0 Pa (onsel disi)",
    "U3": "mu_f = 0,2",
    "U4": "mu_f = 0,05",
    "U5": "Pe = 1e5, Ps = 1e7",
    "U6": "yigin yogunlugu 1500",
    "U8": "birlesik: Y0 1, mu_f 0,2, Pe/Ps dusuk, rho 1500",
}
Z_ESIGI = 2.0
TOHUM_TABANI = 0.005


def topla(kok: Path) -> dict:
    """`{(varyant, merdiven): [{bm1, M, p_imp}, ...]}`."""
    out = {}
    for dz in sorted(glob.glob(str(kok / "U_*_*_sahne*.durumlar"))):
        m = re.search(r"U_(U\d+)_(kaba|orta|ince)_sahne(\d+)", dz)
        if not m:
            continue
        for f in sorted(glob.glob(dz + "/nokta_*.npz")):
            z = np.load(f)
            hedef = np.asarray(z["mermi_kesri"]) < 0.5
            ft = json.loads(str(z["fizik_tani"]))
            out.setdefault((m.group(1), m.group(2)), []).append({
                "bm1": float(ft["beta_hedef"]) - 1.0,
                "M": float(np.asarray(z["m"])[hedef].sum()),
                "p_imp": float(z["p_imp"]), "tohum": m.group(3)})
    return out


def yargi(veri: dict) -> dict:
    import dart_gozlem_posterior as dg

    satirlar = {}
    for (ad, lad), kay in sorted(veri.items()):
        b = np.array([k["bm1"] for k in kay], float)
        b = b[np.isfinite(b)]
        if len(b) == 0:
            satirlar[f"{ad}:{lad}"] = {"karar": "OKUNMAZ", "n": 0}
            continue
        g = dg.gozlenen_beta(float(np.median([k["M"] for k in kay])),
                             float(np.median([k["p_imp"] for k in kay])))
        ort = float(b.mean())
        z = (g["beta_eksi_1"] - ort) / g["sigma_beta"]
        karar = ("BANDA ULASIYOR" if abs(z) <= Z_ESIGI else
                 "ALTINDA" if z > 0 else "USTUNDE")
        satirlar[f"{ad}:{lad}"] = {"varyant": ad, "merdiven": lad, "n": int(len(b)),
                                   "beta_eksi_1_sim": ort,
                                   "tohum_yari_farki": float(np.ptp(b) / 2) if len(b) > 1 else None,
                                   "beta_eksi_1_gozlem": g["beta_eksi_1"],
                                   "sigma_beta": g["sigma_beta"], "z": float(z), "karar": karar}
    for s in satirlar.values():
        if s.get("karar") == "OKUNMAZ":
            continue
        taban = satirlar.get(f"U0:{s['merdiven']}")
        if taban and taban.get("karar") != "OKUNMAZ":
            olcek = max(taban.get("tohum_yari_farki") or 0.0, s.get("tohum_yari_farki") or 0.0,
                        TOHUM_TABANI)
            s["fark_tabandan"] = s["beta_eksi_1_sim"] - taban["beta_eksi_1_sim"]
            s["fark_tohum_olcegi"] = s["fark_tabandan"] / olcek
    ulasan = sorted(k for k, s in satirlar.items() if s.get("karar") == "BANDA ULASIYOR")
    okunur = {k: s for k, s in satirlar.items() if s.get("karar") != "OKUNMAZ"}
    if ulasan:
        genel = f"MODEL GOZLEME ULASABILIYOR: {', '.join(ulasan)}"
    elif okunur:
        en = min(okunur, key=lambda k: abs(okunur[k]["z"]))
        genel = f"HICBIR VARYANT ULASMIYOR (en yakin {en}, z = {okunur[en]['z']:+.1f})"
    else:
        genel = "OKUNMAZ"
    return {"satirlar": satirlar, "genel": genel}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kok", type=Path, required=True)
    ap.add_argument("--json", type=Path, default=None)
    a = ap.parse_args(argv)
    v = topla(a.kok)
    out = yargi(v)
    print("=" * 78)
    print(f"PROTOKOL U -- model yeterliligi ({sum(len(x) for x in v.values())} kosu)")
    print("=" * 78)
    for k, s in out["satirlar"].items():
        if s.get("karar") == "OKUNMAZ":
            print(f"  {k:>10}: OKUNMAZ")
            continue
        print(f"  {k:>10} {VARYANTLAR.get(s['varyant'], ''):<45} "
              f"beta-1 sim {s['beta_eksi_1_sim']:.3f} "
              f"gozlem {s['beta_eksi_1_gozlem']:.3f}+-{s['sigma_beta']:.3f}  z {s['z']:+.1f} "
              f"-> {s['karar']}  (U0'dan {s.get('fark_tabandan', float('nan')):+.3f})")
    print(f"\nGENEL: {out['genel']}")
    if a.json:
        a.json.write_text(json.dumps(out, indent=1, default=float), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
