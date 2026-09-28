#!/usr/bin/env python
"""PROTOKOL-A103 raporu — geç `β` farkını merdivenin dış kuşağı mı taşıyor (KİLİTLİ).

Kurallar `docs/truba/PROTOKOL-A103-DIS-KUSAK.md`'de, `A103_dis2` koşusundan
ÖNCE yazıldı. Salt okur; **beklenen** dört kolu sayar (A84/A88):

    kaba  A98_k_av1   (48:5.6 24:2.8 12:1.4 6:0.7 3:0.35; R0'da W2 ile aynı)
    ic    UY_ic       (iç 12 m 2× ince)
    orta  UY_orta     (48 m içi 2× ince)
    dis2  A103_dis2   (12–48 m 2× ince, iç 12 m kaba ile aynı)

    python scripts/a103_dis_kusak_raporu.py --kok kampanya --json S_A103.json
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from uy_yakin_alan_raporu import beta_aninda  # noqa: E402

KOLLAR = {"kaba": "A98_k_av1", "ic": "UY_ic", "orta": "UY_orta",
          "dis2": "A103_dis2"}
T_KIYAS = 300.0
R_HEDEF = 75.0
G = 6.67430e-11
KUSAK = (12.0, 36.0)       # dis kusak: carpma noktasina baslangic uzakligi [m]
Y1_ESIK = 0.05             # toplamsallik: |Δ_dis2 − (β_o − β_ic)|
Y2_ESIK = 0.5              # dis kusak payi: Δ_dis2 / (β_o − β_k)
Y3_ESIK = 0.10             # dis kusak momentumu orta'ya bagil yakinlik


def kusak_momentumu(x, v, m, x0, f, *, R: float = R_HEDEF,
                    kusak=KUSAK) -> dict:
    """Kaçan hedef maddesinin eksenel momentumu, başlangıç uzaklığına göre.

    Kaçış `momentum_defteri` ile aynı (`r > R`, `v_r > v_esc`). Çarpma noktası
    mermi parçacıklarının başlangıç kütle merkezinin yüzeydeki izi; `ê` mermi
    gidiş yönü (merkeze doğru). Momentum `−Σ m v·ê` (kaçan madde `−ê` yönünde).
    """
    x, v, m, x0, f = (np.asarray(a, dtype=np.float64) for a in (x, v, m, x0, f))
    hedef = f < 0.5
    Mt = float(m[hedef].sum())
    v_esc = math.sqrt(2.0 * G * Mt / R)
    xi = (m[~hedef] @ x0[~hedef]) / m[~hedef].sum()
    e = -xi / np.linalg.norm(xi)
    xc = -e * R
    r = np.linalg.norm(x, axis=1)
    vr = np.einsum("ij,ij->i", v, x) / np.maximum(r, 1e-300)
    kac = hedef & (r > R) & (vr > v_esc)
    rho0 = np.linalg.norm(x0 - xc, axis=1)
    pe = -m * (v @ e)
    ic = kac & (rho0 < kusak[0])
    dis = kac & (rho0 >= kusak[0]) & (rho0 < kusak[1])
    return {"P_kac": float(pe[kac].sum()), "P_ic": float(pe[ic].sum()),
            "P_dis": float(pe[dis].sum()), "M_dis": float(m[dis].sum()),
            "v_esc": v_esc}


def oku(kok: Path) -> dict:
    out = {}
    for anahtar, ad in KOLLAR.items():
        dosyalar = sorted(glob.glob(str(kok / f"{ad}.durumlar" / "nokta_*.npz")))
        if not dosyalar:
            out[anahtar] = {"var": False, "neden": "durum yok"}
            continue
        z = np.load(dosyalar[-1])
        ft = json.loads(str(z["fizik_tani"]))
        gc = json.loads(str(z["gecerlilik"]))
        egri = ft.get("impuls_egrisi") or []
        b = beta_aninda(egri, T_KIYAS)
        if not gc.get("gecerli", False):
            out[anahtar] = {"var": False, "neden": "gecersiz"}
            continue
        if not math.isfinite(b):
            out[anahtar] = {"var": False, "neden": "300 s'ye ulasmamis"}
            continue
        km = kusak_momentumu(z["x"], z["v"], z["m"], z["x_referans"],
                             z["mermi_kesri"])
        t_son = float(np.asarray(egri, dtype=np.float64)[-1, 0])
        out[anahtar] = {"var": True, "beta": b, "t_son": t_son, **km}
    return out


def yargila(s: dict) -> dict:
    eksik = {k: d["neden"] for k, d in s.items() if not d["var"]}
    y: dict = {"beklenen": len(KOLLAR), "bulunan": len(KOLLAR) - len(eksik),
               "eksik": eksik,
               "beta": {k: (d["beta"] if d["var"] else float("nan"))
                        for k, d in s.items()},
               "P_dis": {k: (d["P_dis"] if d["var"] else float("nan"))
                         for k, d in s.items()}}
    b = y["beta"]
    tum = all(math.isfinite(b[k]) for k in KOLLAR)
    if not tum:
        for k in ("Y1", "Y2", "Y3"):
            y[k] = "OKUNMAZ"
        y["genel"] = "OKUNMAZ"
        return y
    d_dis = b["dis2"] - b["kaba"]
    d_komp = b["orta"] - b["ic"]
    d_top = b["orta"] - b["kaba"]
    y["Delta_dis2"], y["Delta_tumleyen"], y["Delta_toplam"] = d_dis, d_komp, d_top
    y["Y1"] = ("KUSAK KATKILARI YEREL VE TOPLAMSAL"
               if abs(d_dis - d_komp) <= Y1_ESIK else "TOPLAMSAL DEGIL")
    y["Y2_pay"] = d_dis / d_top if d_top != 0 else float("nan")
    y["Y2"] = ("DIS KUSAK (12-48 m) FARKIN COGUNU TASIYOR"
               if (math.isfinite(y["Y2_pay"]) and y["Y2_pay"] >= Y2_ESIK)
               else "DIS KUSAK FARKIN AZINI TASIYOR")
    p = y["P_dis"]
    y["Y3_bagil"] = abs(p["dis2"] - p["orta"]) / abs(p["orta"])
    y["Y3"] = ("DIS KUSAK EJEKTASI ORTA ILE AYNI" if y["Y3_bagil"] <= Y3_ESIK
               else "DIS KUSAK EJEKTASI ORTADAN FARKLI")
    y["genel"] = y["Y2"]
    return y


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--kok", required=True)
    ap.add_argument("--json", default=None)
    a = ap.parse_args(argv)
    y = yargila(oku(Path(a.kok)))
    print(f"PROTOKOL-A103  bulunan {y['bulunan']}/{y['beklenen']}")
    for k, n in y["eksik"].items():
        print(f"  EKSIK {k}: {n}")
    for k in KOLLAR:
        print(f"  {k:>5}: beta(300) = {y['beta'][k]:.4f}   "
              f"P_kac(12-36 m) = {y['P_dis'][k]:.4e}")
    for k in ("Y1", "Y2", "Y3"):
        print(f"  {k}: {y[k]}")
    print(f"  GENEL: {y['genel']}")
    if a.json:
        out = Path(a.json)
        if out.exists():
            raise SystemExit(f"{out} zaten var (uzerine yazilmaz)")
        out.write_text(json.dumps(y, indent=1, ensure_ascii=False),
                       encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
