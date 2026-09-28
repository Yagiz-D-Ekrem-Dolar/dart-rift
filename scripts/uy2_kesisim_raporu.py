"""Protokol UY2 — çözünürlük × geçiş anı kesişimi (KİLİTLİ; PROTOKOL-UY2 §4).

    b = beta(300 s) - 1,  Delta_kesisim = |b_orta@1,0 - b_kaba@1,0| / b_orta@1,0

- EKSENLER BAGIMSIZ DEGIL : Delta_kesisim <= 0.05          -> uretim KABA
- AZALIYOR                : 0.05 < Delta_kesisim < DELTA_02 -> kaba + cok dogruluklu
- EKSENLER BAGIMSIZ       : Delta_kesisim >= DELTA_02       -> uretim ORTA

DELTA_02 = 0.098 (UY: ayni iki merdiven, t_gecis = 0,2 s; S_UY.json).
Kaba kol `W2_Y10_g1p0`dir (yeniden kosulmaz; beta(300 s) egrisinden okunur).

Kullanim:
    python scripts/uy2_kesisim_raporu.py --kok kampanya --json kampanya/S_UY2.json
"""
from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path

import numpy as np

KOLLAR = {"kaba": "W2_Y10_g1p0", "orta": "UY2_orta_g1p0"}
T_KIYAS = 300.0
ESIK_BAGIMSIZ_DEGIL = 0.05
DELTA_02 = 0.098          # UY'de olculen (t_gecis = 0,2 s) kaba-orta farki


def _oku(kok: Path, ad: str) -> dict | None:
    d = sorted(glob.glob(str(kok / f"{ad}.durumlar" / "nokta_*.npz")))
    if not d:
        return None
    z = np.load(d[-1])
    ft = json.loads(str(z["fizik_tani"]))
    gc = json.loads(str(z["gecerlilik"]))
    egri = ft.get("impuls_egrisi") or []
    e = np.asarray(egri, dtype=np.float64)
    if e.ndim != 2 or len(e) < 3 or e[-1, 0] < T_KIYAS * 0.99:
        return {"gecerli": False, "ulasti": False, "dosya": d[-1]}
    b = float(np.interp(np.log(T_KIYAS), np.log(e[:, 0]), e[:, 2])) - 1.0
    from dartrift.observables.impuls_sekli import impuls_sekli
    return {"b": b, "beta": 1.0 + b, "ulasti": True,
            "gecerli": bool(gc.get("gecerli", False)),
            "n": int(len(z["m"])),
            "M_ejekta": float(ft.get("M_ejekta", float("nan"))),
            "sekil": impuls_sekli(egri, t_ref=T_KIYAS),
            "dosya": d[-1]}


def topla(kok: Path) -> dict:
    return {k: _oku(kok, ad) for k, ad in KOLLAR.items()}


def yargi(veri: dict) -> dict:
    eksik = [k for k, v in veri.items() if v is None]
    kotu = [k for k, v in veri.items()
            if v is not None and not (v.get("gecerli") and v.get("ulasti"))]
    out: dict = {"eksik": eksik, "gecersiz": kotu, "t_kiyas": T_KIYAS,
                 "delta_02": DELTA_02, "esik": ESIK_BAGIMSIZ_DEGIL,
                 "kollar": veri}
    if eksik or kotu:
        out["genel"] = "OKUNMAZ (eksik, gecersiz ya da 300 s'ye ulasmamis kol)"
        out["uretim_merdiveni"] = None
        return out
    bk, bo = veri["kaba"]["b"], veri["orta"]["b"]
    d = abs(bo - bk) / abs(bo) if bo else float("inf")
    out["delta_kesisim"] = d
    if d <= ESIK_BAGIMSIZ_DEGIL:
        out["genel"] = "EKSENLER BAGIMSIZ DEGIL"
        out["uretim_merdiveni"] = "kaba"
    elif d < DELTA_02:
        out["genel"] = "AZALIYOR"
        out["uretim_merdiveni"] = "kaba + cok dogruluklu"
    else:
        out["genel"] = "EKSENLER BAGIMSIZ"
        out["uretim_merdiveni"] = "orta"
    out["sigma_cozunurluk"] = d
    # kapi olmayan: mekanizma ayni mi (KAYIT-070 §2)
    sk, so = veri["kaba"]["sekil"], veri["orta"]["sekil"]
    out["sekil"] = {"kaba": sk, "orta": so,
                    "d_s_1s": abs(so["s_1s"] - sk["s_1s"]),
                    "t50_orani": so["t50"] / sk["t50"] if sk["t50"] else float("nan")}
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kok", type=Path, required=True)
    ap.add_argument("--json", type=Path, default=None)
    a = ap.parse_args(argv)
    out = yargi(topla(a.kok))
    print("=" * 72)
    print("PROTOKOL UY2 -- cozunurluk x gecis ani kesisimi (Y0 = 10 Pa, t_gecis 1,0 s)")
    print("=" * 72)
    for k, v in out["kollar"].items():
        if v is None or not v.get("ulasti"):
            print(f"  {k:>5}: YOK / 300 s'ye ulasmadi")
            continue
        print(f"  {k:>5}: beta(300) {v['beta']:.3f}  N {v['n']}  gecerli {v['gecerli']}")
    if "delta_kesisim" in out:
        print(f"  delta_kesisim {out['delta_kesisim']:.3f}  (UY'de 0,2 s'de {DELTA_02})")
        s = out["sekil"]
        print(f"  [tani] s(1s) farki {s['d_s_1s']:.3f}  t50 orani {s['t50_orani']:.2f}")
    print(f"GENEL: {out['genel']}   uretim merdiveni: {out['uretim_merdiveni']}")
    if a.json:
        a.json.write_text(json.dumps(out, indent=1, default=float), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
