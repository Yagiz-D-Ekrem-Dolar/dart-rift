#!/usr/bin/env python
"""PROTOKOL-A104 raporu — geç `β` `h`'ye mi parçacık sayısına mı bağlı (KİLİTLİ).

Kurallar `docs/truba/PROTOKOL-A104-KESKIN-CEKIRDEK.md`'de, `A104_*`
koşularından ÖNCE yazıldı. Salt okur; **beklenen** dört kolu sayar:

    kaba  A98_k_av1  (h/s = 2; h_rel = 1)
    orta  UY_orta    (h/s = 2; h_rel = 0,5)
    k15   A104_k15   (kaba merdiven, h/s = 1,5; h_rel = 0,75)
    o15   A104_o15   (orta merdiven, h/s = 1,5; h_rel = 0,375)

`h_rel`: kaba merdivenin `h`'sine oran (her kuşakta aynı).

    python scripts/a104_keskin_cekirdek_raporu.py --kok kampanya --json S_A104.json
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

KOLLAR = {"kaba": ("A98_k_av1", 1.0), "orta": ("UY_orta", 0.5),
          "k15": ("A104_k15", 0.75), "o15": ("A104_o15", 0.375)}
T_KIYAS = 300.0
H1_ESIK = 0.05     # |β_k15 − β_dogrusal(0,75)|  ve  |β_k15 − β_kaba|


def oku(kok: Path) -> dict:
    out = {}
    for anahtar, (ad, h_rel) in KOLLAR.items():
        dosyalar = sorted(glob.glob(str(kok / f"{ad}.durumlar" / "nokta_*.npz")))
        if not dosyalar:
            out[anahtar] = {"var": False, "neden": "durum yok", "h_rel": h_rel}
            continue
        z = np.load(dosyalar[-1])
        ft = json.loads(str(z["fizik_tani"]))
        gc = json.loads(str(z["gecerlilik"]))
        b = beta_aninda(ft.get("impuls_egrisi") or [], T_KIYAS)
        if not gc.get("gecerli", False):
            out[anahtar] = {"var": False, "neden": "gecersiz", "h_rel": h_rel}
        elif not math.isfinite(b):
            out[anahtar] = {"var": False, "neden": "300 s'ye ulasmamis",
                            "h_rel": h_rel}
        else:
            out[anahtar] = {"var": True, "beta": b, "h_rel": h_rel}
    return out


def yargila(s: dict) -> dict:
    eksik = {k: d["neden"] for k, d in s.items() if not d["var"]}
    b = {k: (d["beta"] if d["var"] else float("nan")) for k, d in s.items()}
    y: dict = {"beklenen": len(KOLLAR), "bulunan": len(KOLLAR) - len(eksik),
               "eksik": eksik, "beta": b,
               "h_rel": {k: d["h_rel"] for k, d in s.items()}}

    # H1 -- h mi N mi (kaba, orta, k15)
    if all(math.isfinite(b[k]) for k in ("kaba", "orta", "k15")):
        # kaba (h_rel 1) ile orta (0,5) arasi h'de dogrusal aradeger, 0,75'te
        b_lin = b["kaba"] + (1.0 - 0.75) / (1.0 - 0.5) * (b["orta"] - b["kaba"])
        y["H1_beta_dogrusal"] = b_lin
        y["H1_fark_dogrusal"] = abs(b["k15"] - b_lin)
        y["H1_fark_kaba"] = abs(b["k15"] - b["kaba"])
        if y["H1_fark_dogrusal"] <= H1_ESIK:
            y["H1"] = "SONUC ONCELIKLE h'YE BAGLI"
        elif y["H1_fark_kaba"] <= H1_ESIK:
            y["H1"] = "SONUC ONCELIKLE PARCACIK SAYISINA BAGLI"
        else:
            y["H1"] = "KARISIK"
    else:
        y["H1"] = "OKUNMAZ"

    # H2 -- ucuncu seviye: egim yariya iniyor mu (kaba, orta, o15)
    if all(math.isfinite(b[k]) for k in ("kaba", "orta", "o15")):
        s1 = (b["orta"] - b["kaba"]) / (1.0 - 0.5)
        s2 = (b["o15"] - b["orta"]) / (0.5 - 0.375)
        y["H2_egim_kaba_orta"], y["H2_egim_orta_o15"] = s1, s2
        if s1 != 0.0 and s2 / s1 <= 0.5:
            y["H2"] = "YAKINSAMA BASLIYOR"
        elif s1 != 0.0 and s2 / s1 < 1.0:
            y["H2"] = "YAVAS YAKINSAMA"
        else:
            y["H2"] = "YAKINSAMA YOK"
    else:
        y["H2"] = "OKUNMAZ"
    y["genel"] = y["H1"]
    return y


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--kok", required=True)
    ap.add_argument("--json", default=None)
    a = ap.parse_args(argv)
    y = yargila(oku(Path(a.kok)))
    print(f"PROTOKOL-A104  bulunan {y['bulunan']}/{y['beklenen']}")
    for k, n in y["eksik"].items():
        print(f"  EKSIK {k}: {n}")
    for k in KOLLAR:
        print(f"  {k:>5}: h_rel = {y['h_rel'][k]:<5}  beta(300) = {y['beta'][k]:.4f}")
    for k in ("H1", "H2"):
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
