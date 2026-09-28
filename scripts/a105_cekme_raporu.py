#!/usr/bin/env python
"""PROTOKOL-A105 raporu — çözünürlük farkını çekmesiz ayrılma mı taşıyor (KİLİTLİ).

Kurallar `docs/truba/PROTOKOL-A105-CEKME-DAYANIMI.md`'de, `A105_*`
koşularından ÖNCE yazıldı. Salt okur; **beklenen** dört kolu sayar:

    kaba0  A98_k_av1   (kaba merdiven, T_m = 0: üretim, P >= 0 kırpık)
    orta0  UY_orta     (orta merdiven, T_m = 0)
    kabaT  A105_k_T    (kaba merdiven, T_m = Y0 / mu_f)
    ortaT  A105_o_T    (orta merdiven, T_m = Y0 / mu_f)

    python scripts/a105_cekme_raporu.py --kok kampanya --json S_A105.json
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

KOLLAR = {"kaba0": "A98_k_av1", "orta0": "UY_orta",
          "kabaT": "A105_k_T", "ortaT": "A105_o_T"}
T_KIYAS = 300.0
T_ERKEN = 3.0          # gec buyume 3 s'den sonra (COZUNURLUK-DENETIMI 8.2)
C1_COGU = 0.5          # g_T / g_0 <= 0,5  -> farkin COGU
C3_ESIK = 0.10         # |beta_kabaT - beta_kaba0| > 0,1 -> beta T_m'ye duyarli


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
        b3 = beta_aninda(egri, T_ERKEN)
        if not gc.get("gecerli", False):
            out[anahtar] = {"var": False, "neden": "gecersiz"}
        elif not math.isfinite(b):
            out[anahtar] = {"var": False, "neden": "300 s'ye ulasmamis"}
        else:
            out[anahtar] = {"var": True, "beta": b, "beta_3s": b3}
    return out


def _g(b_orta: float, b_kaba: float) -> float:
    """Bagil cozunurluk farki (orta'ya gore)."""
    return (b_orta - b_kaba) / b_orta


def yargila(s: dict) -> dict:
    eksik = {k: d["neden"] for k, d in s.items() if not d["var"]}
    b = {k: (d["beta"] if d["var"] else float("nan")) for k, d in s.items()}
    b3 = {k: (d["beta_3s"] if d["var"] else float("nan")) for k, d in s.items()}
    y: dict = {"beklenen": len(KOLLAR), "bulunan": len(KOLLAR) - len(eksik),
               "eksik": eksik, "beta": b, "beta_3s": b3,
               "gec_artis": {k: b[k] - b3[k] for k in s}}

    # C1 (ana) -- bagil kaba-orta farki T_m ile ne kadar kaliyor
    if all(math.isfinite(b[k]) for k in KOLLAR):
        g0 = _g(b["orta0"], b["kaba0"])
        gT = _g(b["ortaT"], b["kabaT"])
        y["C1_g0"], y["C1_gT"] = g0, gT
        if g0 <= 0.0:
            y["C1"] = "OKUNMAZ (T_m = 0'da fark yok)"
        else:
            r = gT / g0
            y["C1_oran"] = r
            if abs(r) <= C1_COGU:
                y["C1"] = "CEKMESIZ AYRILMA COZUNURLUK FARKININ COGUNU TASIYOR"
            elif abs(r) < 1.0:
                y["C1"] = "CEKMESIZ AYRILMA COZUNURLUK FARKININ BIR KISMINI TASIYOR"
            else:
                y["C1"] = "CEKMESIZ AYRILMA COZUNURLUK FARKINI TASIMIYOR"
    else:
        y["C1"] = "OKUNMAZ"

    # C3 (tani) -- model duyarliligi: beta T_m'ye ne kadar bagli (kaba)
    if all(math.isfinite(b[k]) for k in ("kaba0", "kabaT")):
        d = b["kabaT"] - b["kaba0"]
        y["C3_delta_kaba"] = d
        y["C3"] = ("BETA CEKME DAYANIMINA DUYARLI" if abs(d) > C3_ESIK
                   else "BETA CEKME DAYANIMINA DUYARSIZ")
    else:
        y["C3"] = "OKUNMAZ"
    y["genel"] = y["C1"]
    return y


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--kok", required=True)
    ap.add_argument("--json", default=None)
    a = ap.parse_args(argv)
    y = yargila(oku(Path(a.kok)))
    print(f"PROTOKOL-A105  bulunan {y['bulunan']}/{y['beklenen']}")
    for k, n in y["eksik"].items():
        print(f"  EKSIK {k}: {n}")
    for k in KOLLAR:
        print(f"  {k:>5}: beta(3 s) = {y['beta_3s'][k]:.4f}  "
              f"beta(300 s) = {y['beta'][k]:.4f}  gec artis = {y['gec_artis'][k]:+.4f}")
    for k in ("C1", "C3"):
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
