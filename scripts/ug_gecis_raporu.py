"""Protokol UG — geç evreye geçiş anı yakınsaması (KİLİTLİ; PROTOKOL-UG-GECIS-ANI §4).

    b_g = beta_g(600 s) - 1,   Delta(a; b) = |b_a - b_b| / b_b

- GECIS YAKINSAMIS: Delta(5,0; 2,5) <= 0.05
- YAKINSIYOR:       degilse ama Delta(5,0; 2,5) < Delta(2,5; 1,0)
- YAKINSAMA YOK:    aksi

Uretim gecis ani: {0,2; 1,0; 2,5} icinden Delta(t; 5,0) <= 0.05 olan EN KUCUK t;
hicbiri degilse YAKINSIYOR'da 5,0, YAKINSAMA YOK'ta belirlenemedi.

Kullanim:
    python scripts/ug_gecis_raporu.py --kok kampanya --json kampanya/S_UG.json
"""
from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path

import numpy as np

KOLLAR = {0.2: "W2_Y10_g0p2", 1.0: "W2_Y10_g1p0",
          2.5: "UG_Y10_g2p5", 5.0: "UG_Y10_g5p0"}
ESIK = 0.05
BETA_L1 = 4.18          # L1 Tablo 2, Y0 = 10 Pa, f = 0,6 (yalniz tani)
T_END = 600.0


def _oku(kok: Path, ad: str) -> dict | None:
    dosyalar = sorted(glob.glob(str(kok / f"{ad}.durumlar" / "nokta_*.npz")))
    if not dosyalar:
        return None
    z = np.load(dosyalar[-1])
    ft = json.loads(str(z["fizik_tani"]))
    gc = json.loads(str(z["gecerlilik"]))
    b2 = ft.get("beta_iki_yontem") or {}
    ge = ft.get("gec_evre") or {}
    egri = ft.get("impuls_egrisi") or []
    t_son = float(np.asarray(egri, dtype=np.float64)[-1, 0]) if egri else float("nan")
    beta = float(ft["beta_hedef"])
    return {"beta": beta, "b": beta - 1.0,
            "gecerli": bool(gc.get("gecerli", False)),
            "t_son": t_son,
            "t_gecis": float(ge.get("t_gecis", float("nan"))),
            "e_kin_gecis": float((ge.get("enerji_once") or {}).get("e_kin",
                                                                   float("nan"))),
            "beta_km": float(b2.get("beta_km", float("nan"))),
            "M_ejekta": float(ft.get("M_ejekta", float("nan"))),
            "L1_orani": beta / BETA_L1,
            "dosya": dosyalar[-1]}


def topla(kok: Path) -> dict:
    return {g: _oku(kok, ad) for g, ad in KOLLAR.items()}


def _delta(a: float, b: float) -> float:
    return abs(a - b) / abs(b) if b != 0.0 else float("inf")


def yargi(veri: dict) -> dict:
    eksik = [f"{g:g}" for g, v in veri.items() if v is None]
    gecersiz = [f"{g:g}" for g, v in veri.items()
                if v is not None and not v["gecerli"]]
    kisa = [f"{g:g}" for g, v in veri.items()
            if v is not None and not (v["t_son"] >= T_END * (1.0 - 1e-6))]
    out: dict = {"eksik": eksik, "gecersiz": gecersiz, "kisa": kisa,
                 "esik": ESIK, "kollar": {f"{g:g}": v for g, v in veri.items()}}
    if eksik or gecersiz or kisa:
        out["genel"] = "OKUNMAZ (eksik, gecersiz ya da 600 s'ye ulasmamis kol)"
        out["uretim_t_gecis"] = None
        return out
    b = {g: v["b"] for g, v in veri.items()}
    d_5_25 = _delta(b[5.0], b[2.5])
    d_25_1 = _delta(b[2.5], b[1.0])
    d_1_02 = _delta(b[1.0], b[0.2])
    out.update(delta_5_25=d_5_25, delta_25_1=d_25_1, delta_1_02=d_1_02,
               delta_t_5={f"{g:g}": _delta(b[g], b[5.0]) for g in (0.2, 1.0, 2.5)})
    if d_5_25 <= ESIK:
        out["genel"] = "GECIS YAKINSAMIS"
    elif d_5_25 < d_25_1:
        out["genel"] = "YAKINSIYOR"
    else:
        out["genel"] = "YAKINSAMA YOK"
    uretim = None
    for g in (0.2, 1.0, 2.5):
        if _delta(b[g], b[5.0]) <= ESIK:
            uretim = g
            break
    if uretim is None and out["genel"] == "YAKINSIYOR":
        uretim = 5.0
    out["uretim_t_gecis"] = uretim
    if out["genel"] != "GECIS YAKINSAMIS":
        out["sigma_gecis"] = d_5_25
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kok", type=Path, required=True)
    ap.add_argument("--json", type=Path, default=None)
    a = ap.parse_args(argv)
    out = yargi(topla(a.kok))
    print("=" * 72)
    print("PROTOKOL UG -- gecis ani yakinsamasi (Y0 = 10 Pa, 600 s)")
    print("=" * 72)
    for g, v in out["kollar"].items():
        if v is None:
            print(f"  t_gecis {g:>4} s: YOK")
            continue
        print(f"  t_gecis {g:>4} s: beta {v['beta']:.3f}  (L1 orani "
              f"{v['L1_orani']:.2f})  gecerli {v['gecerli']}")
    for ad in ("delta_1_02", "delta_25_1", "delta_5_25"):
        if ad in out:
            print(f"  {ad}: {out[ad]:.3f}")
    print(f"GENEL: {out['genel']}   uretim t_gecis: {out['uretim_t_gecis']}")
    if a.json:
        a.json.write_text(json.dumps(out, indent=1, default=float),
                          encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
