"""Protokol DY — DART sahnesinin geç evre modeliyle ilk koşusu (KİLİTLİ; §4).

    I = |beta_model - 3,12| / sqrt(sigma_gozlem^2 + sigma_model^2)

- MODEL GOZLEME ULASIYOR : I < 3  ve  beta >= 3,12 - 0,34
- MODEL ASIYOR           : I >= 3 ve  beta > 3,12
- MODEL ULASMIYOR        : I >= 3 ve  beta < 3,12
- OKUNMAZ                : kosu gecersiz ya da 600 s'ye ulasmamis (beta yazilmaz)

sigma_model, `beta - 1` uzerinden OLCULMUS terimlerden kurulur
(tarih_esleme.model_eksikligi_kaynakli): gerceklem_beta, cozunurluk_uzak,
plato, carpma_yeri.

Kullanim:
    python scripts/dy_dart_raporu.py --kok kampanya --json kampanya/S_DY.json
"""
from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path

import numpy as np

AD = "DY_dart_g1p0"
T_END = 600.0
BETA_GOZLEM = 3.12            # PROTOKOL-U §1 (kilitli hedef)
SIGMA_GOZLEM = 0.34
KESME = 3.0
TERIMLER = ("gerceklem_beta", "cozunurluk_uzak", "plato", "carpma_yeri")


def oku(kok: Path) -> dict | None:
    d = sorted(glob.glob(str(kok / f"{AD}.durumlar" / "nokta_*.npz")))
    if not d:
        return None
    z = np.load(d[-1])
    ft = json.loads(str(z["fizik_tani"]))
    gc = json.loads(str(z["gecerlilik"]))
    e = np.asarray(ft.get("impuls_egrisi") or [], dtype=np.float64)
    t_son = float(e[-1, 0]) if e.ndim == 2 and len(e) else float("nan")
    b2 = ft.get("beta_iki_yontem") or {}
    return {"beta": float(ft["beta_hedef"]), "t_son": t_son,
            "gecerli": bool(gc.get("gecerli", False)),
            "ulasti": bool(t_son >= T_END * 0.999),
            "n": int(len(z["m"])), "M_ejekta": float(ft.get("M_ejekta", float("nan"))),
            "beta_km": float(b2.get("beta_km", float("nan"))),
            "egri": ft.get("impuls_egrisi") or [], "dosya": d[-1]}


def yargi(v: dict | None) -> dict:
    from dartrift.inference.tarih_esleme import model_eksikligi_kaynakli
    out: dict = {"gozlem": {"beta": BETA_GOZLEM, "sigma": SIGMA_GOZLEM},
                 "kesme": KESME, "terimler": list(TERIMLER)}
    if v is None or not (v["gecerli"] and v["ulasti"]):
        out["genel"] = "OKUNMAZ (kosu yok, gecersiz ya da 600 s'ye ulasmamis)"
        out["kol"] = None if v is None else {k: v[k] for k in
                                             ("gecerli", "ulasti", "t_son", "n")}
        return out
    beta = v["beta"]
    sm = model_eksikligi_kaynakli(beta - 1.0, TERIMLER)
    payda = float(np.hypot(SIGMA_GOZLEM, sm["sigma"]))
    uygunsuzluk = abs(beta - BETA_GOZLEM) / payda
    if uygunsuzluk < KESME and beta >= BETA_GOZLEM - SIGMA_GOZLEM:
        genel = "MODEL GOZLEME ULASIYOR"
    elif beta > BETA_GOZLEM:
        genel = "MODEL ASIYOR"
    else:
        genel = "MODEL ULASMIYOR"
    out.update(beta=beta, beta_km=v["beta_km"], M_ejekta=v["M_ejekta"], n=v["n"],
               sigma_model=sm["sigma"], sigma_model_terimleri=sm["terimler"],
               payda=payda, I=uygunsuzluk, genel=genel, dosya=v["dosya"])
    if v["egri"]:
        from dartrift.observables.impuls_sekli import impuls_sekli
        out["sekil"] = impuls_sekli(v["egri"], t_ref=T_END)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kok", type=Path, required=True)
    ap.add_argument("--json", type=Path, default=None)
    a = ap.parse_args(argv)
    out = yargi(oku(a.kok))
    print("=" * 72)
    print("PROTOKOL DY -- DART sahnesi, gec evre modeli (ilk kosu)")
    print("=" * 72)
    if "beta" in out:
        print(f"  beta = {out['beta']:.3f}   (beta_km {out['beta_km']:.3f}, N {out['n']})")
        print(f"  gozlem {BETA_GOZLEM} +- {SIGMA_GOZLEM};  sigma_model {out['sigma_model']:.3f}"
              f"  -> payda {out['payda']:.3f}")
        print(f"  I = {out['I']:.2f}  (kesme {KESME})")
        print(f"  M_ejekta {out['M_ejekta']:.3e} kg  (gozlem 1,6 +- 0,3e7)")
    print(f"GENEL: {out['genel']}")
    if a.json:
        a.json.write_text(json.dumps(out, indent=1, default=float), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
