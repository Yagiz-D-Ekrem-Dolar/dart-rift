"""Protokol M2 — θ-kontrastlarının çözünürlük kararlılığı (kilitli, koşudan ÖNCE).

Protokol M'nin kilitli yargısı: beş gözlenebilirin **mutlak** değeri üç
çözünürlükte YAKINSAMIYOR (fark inceldikçe büyüyor). Koşudan SONRA
yapılan keşif: iki θ arasındaki **fark** (kontrast) çok daha kararlı —
`β−1(Y₀ = 3e6) − β−1(Y₀ = 1e5)`: `−0,242 / −0,237 / −0,215` iken mutlak
`β−1` `%62` kaydı. Keşif aynı veriden geldiği için kanıt değil; M2 onu
**yeni θ'larla** sınar.

## Tasarım

Taban `θ_b = (1,10 ; 3e4 Pa ; 0,20)` ve tek eksende kaydırılmış üç nokta:
`θ_Y = (1,10 ; 1e6 ; 0,20)`, `θ_a = (1,25 ; 3e4 ; 0,20)`,
`θ_f = (1,10 ; 3e4 ; 0,40)`. İki sahne tohumu, üç merdiven, matris sahası,
en iyi fizik + `--dayanim-kesme` (A80).

## Kontrast

- `β−1` ve `d_merkez`: fark `c = ȳ(θ_j) − ȳ(θ_b)`.
- `V_krater`, `M_ejekta`: log oran `c = ln ȳ(θ_j) − ln ȳ(θ_b)`.
- `ȳ` iki tohum ortalaması; `σ_c² = σ̄_j² + σ̄_b²` (ortalamanın sapması).

## Yargı (kontrast × gözlenebilir başına)

- **SİNYAL YOK:** `|c_ince| ≤ 2 σ_c,ince`.
- **KARARLI:** sinyal var **ve** üç seviyede işaret aynı **ve**
  `|c_ince − c_orta| ≤ max(0,25 |c_ince|, 2 σ_c)`.
- **KARARSIZ:** diğer.

## Hipotez yargısı

`H_Y`: `Y₀` kontrastı `{β−1, ln V, ln M_ej}` üçlüsünün **en az ikisinde**
KARARLI → **Y₀ KONTRASTI ÇÖZÜNÜRLÜĞE DAYANIKLI**; biri → KISMİ; hiçbiri →
DAYANIKSIZ. `α_b` ve `f` kontrastları aynı kuralla ayrıca yazılır.

Kullanim:
    python scripts/m2_kontrast_raporu.py --kok kampanya --tasarim-yaz
    python scripts/m2_kontrast_raporu.py --kok kampanya --json kampanya/S_M2.json
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

TETALAR = {"b": (1.10, 3.0e4, 0.20), "Y": (1.10, 1.0e6, 0.20),
           "a": (1.25, 3.0e4, 0.20), "f": (1.10, 3.0e4, 0.40)}
TOHUMLAR = (20260906, 99991111)
MERDIVENLER = ("kaba", "orta", "ince")
FARK = ("beta_eksi_1", "d_merkez")
LOG_ORAN = ("V_krater", "M_ejekta")
GOZLEMLER_M2 = FARK + LOG_ORAN
BAGIL_TOLERANS = 0.25
SIGMA_KATI = 2.0
HIPOTEZ_KUMESI = ("beta_eksi_1", "V_krater", "M_ejekta")


def tasarim_yaz(kok: Path) -> list[Path]:
    kok.mkdir(parents=True, exist_ok=True)
    out = []
    for ad, th in TETALAR.items():
        p = kok / f"M2_tasarim_{ad}.json"
        p.write_text(json.dumps({"theta": [list(th)]}), encoding="utf-8")
        out.append(p)
    return out


def _ozet(v) -> tuple[float, float]:
    v = np.asarray([x for x in v if np.isfinite(x)], float)
    if len(v) < 2:
        return float("nan"), float("nan")
    return float(v.mean()), float(v.std(ddof=1) / np.sqrt(len(v)))


def kontrast(gozlem: str, taban, hedef) -> tuple[float, float]:
    """`(c, σ_c)` — taban/hedef: tohum değerleri listesi."""
    (mb, sb), (mj, sj) = _ozet(taban), _ozet(hedef)
    if gozlem in LOG_ORAN:
        if not (mb > 0 and mj > 0):
            return float("nan"), float("nan")
        return float(np.log(mj) - np.log(mb)), float(np.hypot(sj / mj, sb / mb))
    return mj - mb, float(np.hypot(sj, sb))


def kontrast_yargisi(c: dict) -> dict:
    """`c = {merdiven: (c, σ)}` → yargı."""
    if not all(m in c and np.isfinite(c[m][0]) and np.isfinite(c[m][1])
               for m in MERDIVENLER):
        return {"karar": "OKUNMAZ"}
    (ck, _), (co, so), (ci, si) = (c[m] for m in MERDIVENLER)
    if abs(ci) <= SIGMA_KATI * si:
        return {"karar": "SINYAL YOK", "c": [ck, co, ci], "sigma_ince": si}
    ayni_isaret = np.sign(ck) == np.sign(co) == np.sign(ci)
    tol = max(BAGIL_TOLERANS * abs(ci), SIGMA_KATI * float(np.hypot(si, so)))
    kararli = bool(ayni_isaret and abs(ci - co) <= tol)
    return {"karar": "KARARLI" if kararli else "KARARSIZ", "c": [ck, co, ci],
            "sigma_ince": si, "tolerans": tol, "ayni_isaret": bool(ayni_isaret)}


def hipotez(yargilar: dict, eksen: str = "Y") -> str:
    n = sum(yargilar[(eksen, g)]["karar"] == "KARARLI" for g in HIPOTEZ_KUMESI)
    return {3: "DAYANIKLI", 2: "DAYANIKLI", 1: "KISMI", 0: "DAYANIKSIZ"}[n]


def topla(kok: Path) -> dict:
    """`{(ad, merdiven): {gozlem: [tohum değerleri]}}`."""
    from gozlem_vektoru import gozlem_vektoru

    veri = {}
    for ad in TETALAR:
        for m in MERDIVENLER:
            d = {g: [] for g in GOZLEMLER_M2}
            for f in sorted(glob.glob(str(kok / f"M2_{m}_{ad}_sahne*.durumlar"
                                          / "nokta_*.npz"))):
                gv = gozlem_vektoru(np.load(f))
                gv["beta_eksi_1"] = gv["beta_hedef"] - 1.0
                for g in GOZLEMLER_M2:
                    d[g].append(float(gv[g]))
            veri[(ad, m)] = d
    return veri


def rapor(veri: dict) -> dict:
    yargilar = {}
    for eksen in ("Y", "a", "f"):
        for g in GOZLEMLER_M2:
            c = {m: kontrast(g, veri[("b", m)][g], veri[(eksen, m)][g])
                 for m in MERDIVENLER}
            yargilar[(eksen, g)] = kontrast_yargisi(c)
    return {"yargilar": {f"{e}:{g}": v for (e, g), v in yargilar.items()},
            "H_Y": hipotez(yargilar, "Y"), "H_a": hipotez(yargilar, "a"),
            "H_f": hipotez(yargilar, "f")}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kok", type=Path, required=True)
    ap.add_argument("--tasarim-yaz", action="store_true")
    ap.add_argument("--json", type=Path, default=None)
    a = ap.parse_args(argv)
    if a.tasarim_yaz:
        for p in tasarim_yaz(a.kok):
            print("yazildi:", p)
        return 0
    out = rapor(topla(a.kok))
    print("=" * 78)
    print("PROTOKOL M2 -- theta kontrastlarinin cozunurluk kararliligi")
    print("=" * 78)
    for k, v in out["yargilar"].items():
        c = np.round(v.get("c", []), 4).tolist()
        print(f"  {k:>16}: kaba/orta/ince {c}  -> {v['karar']}")
    print(f"\nH_Y (Y0 kontrasti): {out['H_Y']}   H_a: {out['H_a']}   H_f: {out['H_f']}")
    if a.json:
        a.json.write_text(json.dumps(out, indent=1, default=float), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
