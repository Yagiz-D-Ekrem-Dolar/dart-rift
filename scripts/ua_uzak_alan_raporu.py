"""Protokol UA — uzak alan çözünürlüğü (KİLİTLİ; PROTOKOL-UA-UZAK-ALAN §4).

    b_s = beta_s - 1,   Delta(a, b) = |b_a - b_b| / b_b

- YAKINSAMIS:  Delta(3.5; 5) <= 0.05 ve Delta(3.5; 7) <= 0.10
- YAKINSIYOR:  degilse ama Delta(3.5; 5) < Delta(5; 7)
- YAKINSAMA YOK: aksi
Richardson tahmini YAKINSIYOR'da RAPORLANIR, karar degildir.

7 m kolu `W2_Y10_g0p2.durumlar`dan okunur (yeniden kosulmaz).

Kullanim:
    python scripts/ua_uzak_alan_raporu.py --kok kampanya --json kampanya/S_UA.json
"""
from __future__ import annotations

import argparse
import glob
import json
import math
from pathlib import Path

import numpy as np

KOLLAR = {7.0: "W2_Y10_g0p2", 5.0: "UA_s5p0", 3.5: "UA_s3p5"}
ESIK_INCE = 0.05       # Delta(3.5; 5)
ESIK_KABA = 0.10       # Delta(3.5; 7)
ORAN = 1.4


def _oku(kok: Path, ad: str) -> dict | None:
    dosyalar = sorted(glob.glob(str(kok / f"{ad}.durumlar" / "nokta_*.npz")))
    if not dosyalar:
        return None
    z = np.load(dosyalar[-1])
    ft = json.loads(str(z["fizik_tani"]))
    gc = json.loads(str(z["gecerlilik"]))
    b2 = ft.get("beta_iki_yontem") or {}
    return {"beta": float(ft["beta_hedef"]),
            "b": float(ft["beta_hedef"]) - 1.0,
            "gecerli": bool(gc.get("gecerli", False)),
            "n": int(len(z["m"])),
            "M_ejekta": float(ft.get("M_ejekta", float("nan"))),
            "koni_90": float(b2.get("koni_tam_acisi_derece", float("nan"))),
            "koni_kenar": float(b2.get("koni_kenar_derece", float("nan"))),
            "dondurulmus": int(ft.get("dondurulmus", 0)),
            "dosya": dosyalar[-1]}


def topla(kok: Path) -> dict:
    return {s: _oku(kok, ad) for s, ad in KOLLAR.items()}


def _delta(a: float, b: float) -> float:
    return abs(a - b) / abs(b) if b != 0.0 else float("inf")


def yargi(veri: dict) -> dict:
    eksik = [f"{s:g}" for s, k in veri.items() if k is None]
    gecersiz = [f"{s:g}" for s, k in veri.items()
                if k is not None and not k["gecerli"]]
    out: dict = {"eksik": eksik, "gecersiz": gecersiz,
                 "esikler": {"ince": ESIK_INCE, "kaba": ESIK_KABA},
                 "kollar": {f"{s:g}": k for s, k in veri.items()}}
    if eksik or gecersiz:
        out["genel"] = "OKUNMAZ (eksik ya da gecersiz kol)"
        return out
    b7, b5, b3 = veri[7.0]["b"], veri[5.0]["b"], veri[3.5]["b"]
    d35_5 = _delta(b3, b5)
    d35_7 = _delta(b3, b7)
    d5_7 = _delta(b5, b7)
    out.update(delta_35_5=d35_5, delta_35_7=d35_7, delta_5_7=d5_7)
    if d35_5 <= ESIK_INCE and d35_7 <= ESIK_KABA:
        out["genel"] = "UZAK ALAN YAKINSAMIS"
    elif d35_5 < d5_7:
        out["genel"] = "YAKINSIYOR"
        fark_kaba, fark_ince = abs(b7 - b5), abs(b5 - b3)
        if fark_ince > 0.0 and fark_kaba > fark_ince:
            p = math.log(fark_kaba / fark_ince) / math.log(ORAN)
            b_inf = b3 + (b3 - b5) / (ORAN ** p - 1.0)
            out["richardson"] = {"p": p, "b_sonsuz": b_inf,
                                 "beta_sonsuz": 1.0 + b_inf,
                                 "not": "TAHMIN, karar degil"}
    else:
        out["genel"] = "YAKINSAMA YOK"
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kok", type=Path, required=True)
    ap.add_argument("--json", type=Path, default=None)
    a = ap.parse_args(argv)
    out = yargi(topla(a.kok))
    print("=" * 72)
    print("PROTOKOL UA -- uzak alan cozunurlugu (Y0 = 10 Pa, 600 s)")
    print("=" * 72)
    for s, k in out["kollar"].items():
        if k is None:
            print(f"  taban {s:>4} m: YOK")
            continue
        print(f"  taban {s:>4} m: beta {k['beta']:.3f}  N {k['n']}  "
              f"gecerli {k['gecerli']}  koni90 {k['koni_90']:.0f}  "
              f"kenar {k['koni_kenar']:.0f}")
    for ad in ("delta_35_5", "delta_35_7", "delta_5_7"):
        if ad in out:
            print(f"  {ad}: {out[ad]:.3f}")
    if "richardson" in out:
        r = out["richardson"]
        print(f"  Richardson (tahmin): p = {r['p']:.2f}  beta_sonsuz = "
              f"{r['beta_sonsuz']:.3f}")
    print(f"GENEL: {out['genel']}")
    if a.json:
        a.json.write_text(json.dumps(out, indent=1, default=float),
                          encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
