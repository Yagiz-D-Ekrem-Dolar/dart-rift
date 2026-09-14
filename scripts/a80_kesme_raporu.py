"""A80 doğrulaması — dayanım kesmesi kararlı mı, fiziği değiştiriyor mu (kilitli).

Karşılaştırılan: Protokol M'nin kaba 12 noktası (kesmesiz, `M_kaba_t*`)
ile aynı 12 nokta kesmeyle (`K80_kaba_t*`). Ölçek: Protokol L2 matris
kolunun merkez gerçekleme sapmaları (`S_L2.json`, altı gerçekleme).

- **V1 kararlılık:** kesmeli kolda 12/12 nokta tamam → KARARLI.
- **V2 nötrlük:** her iki kolda da tamamlanmış çiftlerde, 5 gözlenebilir
  için `|Δ| ≤ 2σ` kesri: `≥ 0,90` NÖTR · `≥ 0,70` KÜÇÜK ETKİ ·
  `< 0,70` FİZİĞİ DEĞİŞTİRİYOR. `< 25` karşılaştırma → OKUNMAZ.

Kullanim:
    python scripts/a80_kesme_raporu.py --kok kampanya --json kampanya/S_A80.json
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

GOZLEMLER_K = ("d_merkez", "R_krater", "V_krater", "beta_eksi_1", "M_ejekta")
#: `beta_eksi_1`'in gerçekleme sapması `beta_hedef`inkiyle aynıdır.
SIGMA_KAYNAGI = {"beta_eksi_1": "beta_hedef"}
N_NOKTA = 12
NOTR_ESIGI = 0.90
KUCUK_ESIGI = 0.70
SAPMA_KATI = 2.0
EN_AZ_KARSILASTIRMA = 25


def sigma_oku(s_l2: dict, kol: str = "L2_matris") -> dict:
    r = s_l2[kol]
    s = dict(zip(r["gozlemler"], r["sigma"], strict=True))
    return {g: float(s[SIGMA_KAYNAGI.get(g, g)]) for g in GOZLEMLER_K}


def topla(kok: Path, onek: str) -> dict:
    """`{(k, tohum): {gözlenebilir: değer, "kesme": {...}}}` — yalnız tamamlananlar."""
    # Onbellek (scripts/gozlem_onbellek.py): anahtar kod ozeti + npz boyut/mtime;
    # degerler bit-ayni, ayni npz her raporda yeniden hesaplanmaz.
    from gozlem_onbellek import gozlem

    out = {}
    for dz in sorted(glob.glob(str(kok / f"{onek}_kaba_t*_sahne*.durumlar"))):
        m = re.search(r"_t(\d+)_sahne(\d+)", dz)
        for f in sorted(glob.glob(dz + "/nokta_*.npz")):
            z = np.load(f)
            gv = dict(gozlem(f))
            gv["beta_eksi_1"] = gv["beta_hedef"] - 1.0
            kayit = {g: float(gv[g]) for g in GOZLEMLER_K}
            if "kesme_tani" in z.files:
                kayit["kesme"] = json.loads(str(z["kesme_tani"]))
            out[(int(m.group(1)), m.group(2))] = kayit
    return out


def karsilastir(eski: dict, yeni: dict, sigma: dict) -> list[dict]:
    satir = []
    for anah in sorted(set(eski) & set(yeni)):
        for g in GOZLEMLER_K:
            a, b = eski[anah][g], yeni[anah][g]
            if np.isfinite(a) and np.isfinite(b) and sigma[g] > 0:
                satir.append({"t": anah[0], "tohum": anah[1], "gozlem": g,
                              "eski": a, "yeni": b, "fark_sigma": (b - a) / sigma[g]})
    return satir


def yargi(eski: dict, yeni: dict, sigma: dict) -> dict:
    v1 = "KARARLI" if len(yeni) >= N_NOKTA else "KARARSIZ"
    sat = karsilastir(eski, yeni, sigma)
    if len(sat) < EN_AZ_KARSILASTIRMA:
        v2 = "OKUNMAZ"
        kesir = float("nan")
    else:
        kesir = float(np.mean([abs(s["fark_sigma"]) <= SAPMA_KATI for s in sat]))
        v2 = ("NOTR" if kesir >= NOTR_ESIGI else
              "KUCUK ETKI" if kesir >= KUCUK_ESIGI else "FIZIGI DEGISTIRIYOR")
    gozlem_basina = {}
    for g in GOZLEMLER_K:
        f = [s["fark_sigma"] for s in sat if s["gozlem"] == g]
        if f:
            gozlem_basina[g] = {"n": len(f), "medyan_fark_sigma": float(np.median(f)),
                                "max_abs_fark_sigma": float(np.max(np.abs(f))),
                                "icinde_kesri": float(np.mean(np.abs(f) <= SAPMA_KATI))}
    return {"V1": v1, "n_yeni": len(yeni), "n_eski": len(eski),
            "eksik_yeni": sorted(f"t{k}_s{t}" for (k, t) in
                                 {(k, t) for k in range(6) for t in ("20260906", "99991111")}
                                 - set(yeni)),
            "V2": v2, "icinde_kesri": kesir, "n_karsilastirma": len(sat),
            "gozlem_basina": gozlem_basina,
            "kesik_kutle_kesri": [v["kesme"]["kesik_kutle_kesri"] for v in yeni.values()
                                  if "kesme" in v and v["kesme"]]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kok", type=Path, required=True)
    ap.add_argument("--json", type=Path, default=None)
    ap.add_argument("--eski-onek", default="M",
                    help="A83 dogrulamasinda K80 (kesmeli) karsilastirma tabani")
    ap.add_argument("--yeni-onek", default="K80",
                    help="A83 dogrulamasinda K83 (kesme + yogunluk tabani)")
    a = ap.parse_args(argv)
    sigma = sigma_oku(json.loads((a.kok / "S_L2.json").read_text(encoding="utf-8")))
    eski, yeni = topla(a.kok, a.eski_onek), topla(a.kok, a.yeni_onek)
    y = yargi(eski, yeni, sigma)
    print("=" * 72)
    print(f"DOGRULAMA -- {a.yeni_onek} (yeni) / {a.eski_onek} (eski)")
    print("=" * 72)
    print(f"  sigma (L2 matris merkez): {sigma}")
    print(f"  V1: {y['V1']}  (kesmeli tamam {y['n_yeni']}/{N_NOKTA}; eksik {y['eksik_yeni']})")
    for g, d in y["gozlem_basina"].items():
        print(f"  {g:>12}: n={d['n']}  medyan fark {d['medyan_fark_sigma']:+.2f} sigma  "
              f"max |fark| {d['max_abs_fark_sigma']:.2f} sigma  "
              f"2sigma icinde {d['icinde_kesri']:.2f}")
    print(f"  V2: {y['V2']}  (2 sigma icinde {y['icinde_kesri']:.3f}, "
          f"{y['n_karsilastirma']} karsilastirma)")
    if y["kesik_kutle_kesri"]:
        print(f"  kesik kutle kesri (son an): {np.round(y['kesik_kutle_kesri'], 5).tolist()}")
    if a.json:
        a.json.write_text(json.dumps(y, indent=1, default=float), encoding="utf-8")
    return 0 if y["V1"] == "KARARLI" else 3


if __name__ == "__main__":
    raise SystemExit(main())
