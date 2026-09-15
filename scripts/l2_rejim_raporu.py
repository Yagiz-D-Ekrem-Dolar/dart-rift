"""Protokol L2 — rejim tekrar sınavı (L'nin koşu SONRASI bulgusunun ön kaydı).

L ölçtü (koşudan sonra, betimleyici): 24 ms'deki `β`'yı çarpma noktası
altındaki blok belirliyor — bloğa çarpma `β−1 ≈ 0,03`, matrise çarpma
`≈ 0,5`, oran `~17`. L2 bunu **önceden kayıtlı** bir ölçütle sınıyor:
çarpma sahası koşullanmış iki kolun merkez gerçekleşmelerinde

    oran = medyan(β−1 | matris) / medyan(β−1 | blok)

Kilitli tablo (koşudan ÖNCE):

| oran | yargı |
|---|---|
| `≥ 5` | **REPLİKE** |
| `2 – 5` | **BELİRSİZ** |
| `< 2` | **REPLİKE DEĞİL** |

Blok kolunda `β−1 ≤ 0` ise oran tanımsız: matris kolu `β−1 ≥ 0,05` ise
REPLİKE, değilse BELİRSİZ.

Kullanim:
    python scripts/l2_rejim_raporu.py --kok kampanya
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

# --- kilitli esikler (koşudan ÖNCE) ---
REPLIKE_ORANI = 5.0
BELIRSIZ_ORANI = 2.0
BLOK_SIFIR_MATRIS_ESIGI = 0.05


def rejim_yargisi(dbeta_matris, dbeta_blok) -> dict:
    """`β−1` dizilerinden (merkez gerçekleşmeleri) kilitli yargı."""
    dm = float(np.median(np.asarray(dbeta_matris, float)))
    db = float(np.median(np.asarray(dbeta_blok, float)))
    if db <= 0.0:
        karar = "REPLIKE" if dm >= BLOK_SIFIR_MATRIS_ESIGI else "BELIRSIZ"
        return {"karar": karar, "oran": float("inf") if dm > 0 else float("nan"),
                "dbeta_matris_medyan": dm, "dbeta_blok_medyan": db}
    oran = dm / db
    karar = ("REPLIKE" if oran >= REPLIKE_ORANI
             else "BELIRSIZ" if oran >= BELIRSIZ_ORANI else "REPLIKE DEGIL")
    return {"karar": karar, "oran": oran, "dbeta_matris_medyan": dm,
            "dbeta_blok_medyan": db}


def _merkez_dbeta(kok: Path, kol: str) -> list[float]:
    import duyarlilik_raporu as dr

    from dartrift.observables.momentum_defteri import momentum_defteri
    from dartrift.observables.momentum_transfer import escape_speed

    merkez = tuple(np.round(np.asarray(dr.tasarim()["merkez"], float), 9))
    out = []
    for f in sorted(glob.glob(str(kok / f"{kol}_sahne*.durumlar" / "nokta_*.npz"))):
        z = np.load(f)
        if tuple(np.round(z["theta"], 9)) != merkez:
            continue
        m = np.asarray(z["m"], float)
        hed = np.asarray(z["mermi_kesri"]) < 0.5
        R = float(z["R"])
        md = momentum_defteri(z["x"], z["v"], m, mermi_kesri=z["mermi_kesri"], R=R,
                              v_esc=escape_speed(float(m[hed].sum()), R),
                              ehat=z["ehat"], p_imp=float(z["p_imp"]))
        out.append(md["beta_hedef"] - 1.0)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kok", type=Path, required=True)
    ap.add_argument("--json", type=Path, default=None)
    a = ap.parse_args(argv)
    dm = _merkez_dbeta(a.kok, "L2_matris")
    db = _merkez_dbeta(a.kok, "L2_blok")
    print(f"L2_matris merkez beta-1: {np.round(dm, 4).tolist()}")
    print(f"L2_blok   merkez beta-1: {np.round(db, 4).tolist()}")
    if not dm or not db:
        y = {"karar": "OKUNMAZ", "sebep": "merkez gerceklesmesi yok"}
    else:
        y = rejim_yargisi(dm, db)
    print(f"REJIM TEKRAR SINAVI: {y}")
    if a.json:
        a.json.write_text(json.dumps({"matris": dm, "blok": db, "yargi": y},
                                     indent=1, default=float), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
