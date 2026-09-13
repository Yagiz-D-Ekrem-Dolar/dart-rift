"""Protokol M — üç çözünürlükte yakınsama raporu (kilitli, koşudan ÖNCE).

Uzman (Soru 18/21): *"Üçüncü nokta araya değil daha inceye konmalı"*,
*"4–6 temsilî θ'da eşleşmiş üç çözünürlük"*, *"bilimsel tolerans önceden
seçilmeli; sayısal farkın belirsizlik aralığı bu toleransın içine
girmeli"*.

Her `(θ, gözlem)` için kaba / orta / ince merdivendeki iki tohum
ortalaması ile `scripts/richardson_raporu.py`'nin Richardson + tolerans
kapısı uygulanır. Tolerans ince seviyedeki değere göre **bağıl**:

| gözlem | tolerans |
|---|---|
| `d_merkez` | `0,10` |
| `R_krater` | `0,15` |
| `V_krater` | `0,20` |
| `beta_eksi_1` | `0,25` |
| `M_ejekta` | `0,30` |

Gözlem başına yargı (6 θ üzerinden):
`YAKINSAMIŞ` sayısı `≥ 4` → **YAKINSIYOR**; `≤ 1` → **YAKINSAMIYOR**;
arası → **KISMİ**.

Kullanim:
    python scripts/m_yakinsama_raporu.py --kok kampanya --tasarim-yaz
    python scripts/m_yakinsama_raporu.py --kok kampanya --json S_M.json
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

# --- PROTOKOL M: kilitli tasarim ve esikler (koşudan ÖNCE) ---
TETALAR = ((1.15, 1.0e5, 0.275),   # t0 merkez
           (1.15, 1.0e3, 0.275),   # t1 zayif matris
           (1.15, 3.0e6, 0.275),   # t2 guclu matris
           (1.05, 1.0e5, 0.10),    # t3 az blok, sert blok
           (1.25, 1.0e5, 0.45),    # t4 cok blok, gozenekli blok
           (1.15, 1.0e4, 0.45))    # t5 cok blok, zayif matris
TOHUMLAR = (20260906, 99991111)
MERDIVENLER = ("kaba", "orta", "ince")
GOZLEMLER_M = ("d_merkez", "R_krater", "V_krater", "beta_eksi_1", "M_ejekta")
TOLERANS = {"d_merkez": 0.10, "R_krater": 0.15, "V_krater": 0.20,
            "beta_eksi_1": 0.25, "M_ejekta": 0.30}
YAKINSIYOR_EN_AZ = 4
YAKINSAMIYOR_EN_COK = 1


def _rr():
    import richardson_raporu as rr

    return rr


def tasarim_yaz(kok: Path) -> list[Path]:
    kok.mkdir(parents=True, exist_ok=True)
    out = []
    for k, th in enumerate(TETALAR):
        p = kok / f"M_tasarim_t{k}.json"
        p.write_text(json.dumps({"theta": [list(th)]}), encoding="utf-8")
        out.append(p)
    return out


def seviye_ozeti(degerler) -> tuple[float, float]:
    """İki tohum ortalaması ve ortalamanın sapması (`n = 2`: `|a − b| / 2`)."""
    d = np.asarray([v for v in degerler if np.isfinite(v)], dtype=np.float64)
    if len(d) < 2:
        return float("nan"), float("nan")
    return float(d.mean()), float(d.std(ddof=1) / np.sqrt(len(d)))


def teta_yargisi(kaba, orta, ince, tolerans_bagil: float) -> dict:
    """`(ort, σ)` üçlüsünden Richardson + tolerans kapısı."""
    rr = _rr()
    (xc, sc), (xm, sm), (xf, sf) = kaba, orta, ince
    if not all(np.isfinite(v) for v in (xc, xm, xf, sc, sm, sf)):
        return {"karar": "OKUNMAZ", "sebep": "eksik seviye ya da tohum"}
    if xf == 0.0:
        return {"karar": "OKUNMAZ", "sebep": "ince deger sifir (bagil tolerans tanimsiz)"}
    r = rr.richardson(xc, xm, xf, s_c=sc, s_m=sm, s_f=sf)
    y = rr.yakinsama_yargisi(r, tolerans_bagil * abs(xf), sf)
    y["durum"] = r["durum"]
    y["p"] = r["p"]
    y["x_yildiz"] = r["x_yildiz"]
    return y


def gozlem_yargisi(sonuclar: list[dict]) -> dict:
    n_yak = sum(s["karar"] == "YAKINSAMIS" for s in sonuclar)
    sayac = {}
    for s in sonuclar:
        anah = s["karar"] if s["karar"] != "OKUNMAZ" else f"OKUNMAZ:{s.get('sebep', '?')}"
        sayac[anah] = sayac.get(anah, 0) + 1
    if n_yak >= YAKINSIYOR_EN_AZ:
        karar = "YAKINSIYOR"
    elif n_yak <= YAKINSAMIYOR_EN_COK:
        karar = "YAKINSAMIYOR"
    else:
        karar = "KISMI"
    return {"karar": karar, "n_yakinsamis": n_yak, "sayac": sayac}


def topla(kok: Path) -> dict:
    """`{gozlem: {k: {merdiven: [tohum degerleri]}}}`."""
    from gozlem_vektoru import gozlem_vektoru

    veri = {g: {k: {m: [] for m in MERDIVENLER} for k in range(len(TETALAR))}
            for g in GOZLEMLER_M}
    for lad in MERDIVENLER:
        for k in range(len(TETALAR)):
            for f in sorted(glob.glob(str(kok / f"M_{lad}_t{k}_sahne*.durumlar"
                                          / "nokta_*.npz"))):
                gv = gozlem_vektoru(np.load(f))
                gv["beta_eksi_1"] = gv["beta_hedef"] - 1.0
                for g in GOZLEMLER_M:
                    veri[g][k][lad].append(float(gv[g]))
    return veri


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
    veri = topla(a.kok)
    cikti = {}
    print("=" * 78)
    print("PROTOKOL M -- uc cozunurlukte yakinsama")
    print("=" * 78)
    for g in GOZLEMLER_M:
        sonuclar = []
        print(f"\n-- {g}  (tolerans {TOLERANS[g]:.2f} x |ince|)")
        for k in range(len(TETALAR)):
            oz = [seviye_ozeti(veri[g][k][m]) for m in MERDIVENLER]
            y = teta_yargisi(*oz, TOLERANS[g])
            sonuclar.append(y)
            print(f"   t{k} " + "  ".join(f"{m}={o[0]:.4g}+-{o[1]:.2g}"
                                         for m, o in zip(MERDIVENLER, oz, strict=True))
                  + f"   -> {y['karar']} ({y.get('durum', y.get('sebep', ''))})")
        gy = gozlem_yargisi(sonuclar)
        print(f"   YARGI {g}: {gy['karar']}  (YAKINSAMIS {gy['n_yakinsamis']}/6; {gy['sayac']})")
        cikti[g] = {"teta": sonuclar, "yargi": gy}
    if a.json:
        a.json.write_text(json.dumps(cikti, indent=1, default=float), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
