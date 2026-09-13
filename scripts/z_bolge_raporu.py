"""Protokol Z — merdivenin ince bölge yarıçapı M'nin yakınsamamasını açıklıyor mu (kilitli).

M: mutlak gözlenebilirler YAKINSAMIYOR. Bütün seviyelerde en ince bölge
`3 m`, bir üstü `6 m`. İnce seviyede krater derinliği `3,9 m`: krater en
ince bölgeden **taşıyor**, kaba seviyede (`2,6 m`) taşmıyor. Krater
bölgeye göre farklı yerde durduğu için seviyeler aynı şeyi ölçmüyor
olabilir.

Sınama: **en ince iki aralığın** bölge yarıçapı iki katı (en ince aralık
ve dış bölgeler aynı; aradaki bir kademe böylece kalkıyor).

| merdiven | standart (M) | geniş (Z) |
|---|---|---|
| kaba | `48:5.6 24:2.8 12:1.4 6:0.7 3:0.35` | `48:5.6 24:2.8 12:0.7 6:0.35` |
| orta | `48:2.8 24:1.4 12:0.7 6:0.35 3:0.175` | `48:2.8 24:1.4 12:0.35 6:0.175` |

θ: M'nin t0 (`Y₀ = 1e5`) ve t2 (`Y₀ = 3e6`), iki tohum; fizik M ile
**aynı** (kesme yok — karşılaştırma M'nin kendi koşularıyla).

Ölçü: `Δ = (ȳ_geniş − ȳ_standart) / |ȳ_standart|`, gözlenebilir × θ ×
merdiven. Yargı (`β−1` ve `V_krater`, iki θ, iki merdiven = 8 değer):

- hepsinde `|Δ| ≤ tol / 2` → **BÖLGE ETKİSİZ** (yakınsamama içsel)
- en az yarısında `|Δ| > tol` → **BÖLGE ETKİLİ** (merdiven tasarımı yapıtı)
- aksi → **KISMİ**

`tol`: M'nin toleransları (`β−1` `0,25`, `V_krater` `0,20`).
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

GENIS = {"kaba": ("48:5.6", "24:2.8", "12:0.7", "6:0.35"),
         "orta": ("48:2.8", "24:1.4", "12:0.35", "6:0.175")}
TETALAR = (0, 2)
GOZLEMLER_Z = ("beta_eksi_1", "V_krater", "d_merkez", "M_ejekta")
TOLERANS = {"beta_eksi_1": 0.25, "V_krater": 0.20, "d_merkez": 0.10, "M_ejekta": 0.30}
YARGI_GOZLEMLERI = ("beta_eksi_1", "V_krater")


def bagil_fark(standart, genis) -> float:
    s = np.nanmean(standart) if len(standart) else np.nan
    g = np.nanmean(genis) if len(genis) else np.nan
    return float((g - s) / abs(s)) if np.isfinite(s) and s != 0 and np.isfinite(g) else float("nan")


def yargi(farklar: dict) -> dict:
    """`farklar[(gozlem, merdiven, t)] = Δ`."""
    d = [(g, abs(farklar[(g, m, t)])) for g in YARGI_GOZLEMLERI for m in GENIS
         for t in TETALAR if np.isfinite(farklar.get((g, m, t), np.nan))]
    if len(d) < 8:
        return {"karar": "OKUNMAZ", "n": len(d)}
    buyuk = sum(v > TOLERANS[g] for g, v in d)
    kucuk = all(v <= TOLERANS[g] / 2 for g, v in d)
    karar = ("BOLGE ETKISIZ" if kucuk else
             "BOLGE ETKILI" if buyuk >= len(d) / 2 else "KISMI")
    return {"karar": karar, "n": len(d), "tolerans_asan": buyuk}


def topla(kok: Path) -> dict:
    from gozlem_vektoru import gozlem_vektoru

    def oku(desen):
        out = {g: [] for g in GOZLEMLER_Z}
        for f in sorted(glob.glob(str(kok / desen / "nokta_*.npz"))):
            gv = gozlem_vektoru(np.load(f))
            gv["beta_eksi_1"] = gv["beta_hedef"] - 1.0
            for g in GOZLEMLER_Z:
                out[g].append(float(gv[g]))
        return out

    farklar, ham = {}, {}
    for m in GENIS:
        for t in TETALAR:
            s = oku(f"M_{m}_t{t}_sahne*.durumlar")
            z = oku(f"Z_{m}_t{t}_sahne*.durumlar")
            for g in GOZLEMLER_Z:
                farklar[(g, m, t)] = bagil_fark(s[g], z[g])
                ham[f"{g}:{m}:t{t}"] = {"standart": s[g], "genis": z[g]}
    return {"farklar": farklar, "ham": ham}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kok", type=Path, required=True)
    ap.add_argument("--json", type=Path, default=None)
    a = ap.parse_args(argv)
    v = topla(a.kok)
    y = yargi(v["farklar"])
    print("=" * 78)
    print("PROTOKOL Z -- ince bolge yaricapi")
    print("=" * 78)
    for (g, m, t), d in sorted(v["farklar"].items()):
        h = v["ham"][f"{g}:{m}:t{t}"]
        print(f"  {g:>12} {m} t{t}: standart {np.round(h['standart'], 4).tolist()}  "
              f"genis {np.round(h['genis'], 4).tolist()}  Delta {d:+.1%}")
    print(f"\nYARGI: {y}")
    if a.json:
        a.json.write_text(json.dumps({"yargi": y, "ham": v["ham"],
                                      "farklar": {f"{g}:{m}:t{t}": d for (g, m, t), d
                                                  in v["farklar"].items()}},
                                     indent=1, default=float), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
