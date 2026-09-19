"""Protokol UY — yakın/orta alan çözünürlüğü (KİLİTLİ; PROTOKOL-UY-YAKIN-ALAN §4).

    b = beta(300 s) - 1,   Delta_orta = |b_orta - b_kaba| / b_orta

- IKI NOKTADA FARK KUCUK:     Delta_orta <= 0.05
- COZUNURLUK TERIMI GEREKLI:  0.05 < Delta_orta <= 0.15
- COZUNURLUGE DUYARLI:        Delta_orta > 0.15

Kaba kol `W2_Y10_g0p2`dir (600 s koşusu); `beta(300 s)` onun `impuls_egrisi`
satırlarından log-zamanda doğrusal aradeğerle okunur. Orta ve iç kollar 300 s'de
biter; son değerleri kullanılır.

Kullanim:
    python scripts/uy_yakin_alan_raporu.py --kok kampanya --json kampanya/S_UY.json
"""
from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path

import numpy as np

KOLLAR = {"kaba": "W2_Y10_g0p2", "orta": "UY_orta", "ic": "UY_ic"}
T_KIYAS = 300.0
ESIK_KUCUK = 0.05
ESIK_DUYARLI = 0.15
#: Kolun `t_kiyas`'a ulaştığını kabul etmek için bağıl tolerans.
T_TOLERANS = 1e-3


def beta_aninda(egri, t: float) -> float:
    """`impuls_egrisi` satırlarından (`[t, _, beta, M]`) `t` anındaki `beta`.

    Log-zamanda doğrusal aradeğer. `t` eğrinin dışındaysa `nan` (kırpma YOK:
    KAYIT-030 sınıfı sessiz uç değer uydurmasını önler).
    """
    e = np.asarray(egri, dtype=np.float64)
    if e.ndim != 2 or e.shape[1] < 3 or len(e) < 2:
        return float("nan")
    ts, bs = e[:, 0], e[:, 2]
    if not (ts[0] <= t <= ts[-1] * (1.0 + T_TOLERANS)):
        return float("nan")
    if t >= ts[-1]:
        return float(bs[-1])
    return float(np.interp(np.log(t), np.log(ts), bs))


def _oku(kok: Path, ad: str) -> dict | None:
    dosyalar = sorted(glob.glob(str(kok / f"{ad}.durumlar" / "nokta_*.npz")))
    if not dosyalar:
        return None
    z = np.load(dosyalar[-1])
    ft = json.loads(str(z["fizik_tani"]))
    gc = json.loads(str(z["gecerlilik"]))
    b2 = ft.get("beta_iki_yontem") or {}
    egri = ft.get("impuls_egrisi") or []
    beta_t = beta_aninda(egri, T_KIYAS)
    t_son = float(np.asarray(egri, dtype=np.float64)[-1, 0]) if egri else float("nan")
    return {"beta_300": beta_t,
            "b": beta_t - 1.0,
            "beta_son": float(ft["beta_hedef"]),
            "t_son": t_son,
            "gecerli": bool(gc.get("gecerli", False)),
            "n": int(len(z["m"])),
            "M_ejekta_son": float(ft.get("M_ejekta", float("nan"))),
            "beta_km_son": float(b2.get("beta_km", float("nan"))),
            "koni_90": float(b2.get("koni_tam_acisi_derece", float("nan"))),
            "dosya": dosyalar[-1]}


def topla(kok: Path) -> dict:
    return {k: _oku(kok, ad) for k, ad in KOLLAR.items()}


def yargi(veri: dict) -> dict:
    eksik = [k for k, v in veri.items() if v is None]
    gecersiz = [k for k, v in veri.items()
                if v is not None and not v["gecerli"]]
    erken = [k for k, v in veri.items()
             if v is not None and not np.isfinite(v["b"])]
    out: dict = {"eksik": eksik, "gecersiz": gecersiz, "t_kiyas": T_KIYAS,
                 "ulasmadi": erken,
                 "esikler": {"kucuk": ESIK_KUCUK, "duyarli": ESIK_DUYARLI},
                 "kollar": veri}
    if eksik or gecersiz or erken:
        out["genel"] = "OKUNMAZ (eksik, gecersiz ya da 300 s'ye ulasmamis kol)"
        return out
    bk, bo, bi = veri["kaba"]["b"], veri["orta"]["b"], veri["ic"]["b"]
    d_orta = abs(bo - bk) / abs(bo) if bo != 0.0 else float("inf")
    out["delta_orta"] = d_orta
    if d_orta <= ESIK_KUCUK:
        out["genel"] = "IKI NOKTADA FARK KUCUK"
    elif d_orta <= ESIK_DUYARLI:
        out["genel"] = "COZUNURLUK TERIMI GEREKLI"
    else:
        out["genel"] = "COZUNURLUGE DUYARLI"
    out["sigma_cozunurluk"] = d_orta
    # --- kapi olmayan tanilar
    out["delta_ic"] = abs(bi - bk) / abs(bi) if bi != 0.0 else float("inf")
    if abs(bo - bk) > 1e-3:
        out["ic_payi"] = (bi - bk) / (bo - bk)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kok", type=Path, required=True)
    ap.add_argument("--json", type=Path, default=None)
    a = ap.parse_args(argv)
    out = yargi(topla(a.kok))
    print("=" * 72)
    print("PROTOKOL UY -- yakin/orta alan cozunurlugu (Y0 = 10 Pa, beta @ 300 s)")
    print("=" * 72)
    for k, v in out["kollar"].items():
        if v is None:
            print(f"  {k:>5}: YOK")
            continue
        print(f"  {k:>5}: beta(300) {v['beta_300']:.3f}  N {v['n']}  "
              f"gecerli {v['gecerli']}  t_son {v['t_son']:.0f}")
    for ad in ("delta_orta", "delta_ic", "ic_payi"):
        if ad in out:
            print(f"  {ad}: {out[ad]:.3f}")
    print(f"GENEL: {out['genel']}")
    if a.json:
        a.json.write_text(json.dumps(out, indent=1, default=float),
                          encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
