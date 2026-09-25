"""Protokol A98 — geç evre yapay viskozitesi (KİLİTLİ; PROTOKOL-A98-GEC-EVRE-AV §4).

    b = beta(300 s) - 1

- R0 gerileme:   |beta_k_av1 - beta_W2| <= 0.01, degilse GENEL OKUNMAZ
- M1 AV payi:    E_AV,gec / (E_AV,gec + W_plastik,gec) >= 0.5 -> BASKIN
- M2 duyarlilik: |b_k01 - b_k1| / |b_k1| > 0.05 -> DUYARLI
- M3 cozunurluk: D1 = |b_UYorta - b_W2| / |b_UYorta|,
                 D01 = |b_o01 - b_k01| / |b_o01|
                 D01 <= 0.05 ve D01 <= D1/2 -> AV COZUNURLUK FARKININ ANA SEBEBI
                 D01 < D1                  -> AV KISMI SEBEP
                 aksi                      -> AV SEBEP DEGIL
- M4 AV siniri:  |b_k0 - b_k01| / |b_k0| <= 0.02 -> AV 0,1'DE IHMAL EDILEBILIR
- M5 mermi:      |b_p6400 - b_k1| / |b_p6400| <= 0.05 -> MERMI COZUNURLUGU
                 GEC BETA'YA YANSIMIYOR (ayri soru; genel = M3)

Kullanim:
    python scripts/a98_gec_av_raporu.py --kok kampanya --json kampanya/S_A98.json
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from uy_yakin_alan_raporu import beta_aninda  # noqa: E402

KOLLAR = {"W2": "W2_Y10_g0p2", "UYorta": "UY_orta",
          "k_av1": "A98_k_av1", "k_av01": "A98_k_av01",
          "o_av01": "A98_o_av01", "k_av0": "A98_k_av0",
          "k_p6400": "A98_k_p6400"}
T_KIYAS = 300.0
R0_ESIK = 0.01
M1_ESIK = 0.5
M2_ESIK = 0.05
M3_ESIK = 0.05
M4_ESIK = 0.02
M5_ESIK = 0.05


def _oku(kok: Path, ad: str) -> dict | None:
    dosyalar = sorted(glob.glob(str(kok / f"{ad}.durumlar" / "nokta_*.npz")))
    if not dosyalar:
        return None
    z = np.load(dosyalar[-1])
    ft = json.loads(str(z["fizik_tani"]))
    gc = json.loads(str(z["gecerlilik"]))
    egri = ft.get("impuls_egrisi") or []
    beta_t = beta_aninda(egri, T_KIYAS)
    av = ft.get("av_tanisi") or {}
    return {"beta_300": beta_t, "b": beta_t - 1.0,
            "gecerli": bool(gc.get("gecerli", False)),
            "n": int(len(z["m"])),
            "E_av_gec": av.get("E_av_gec_evre"),
            "W_pl_gec": av.get("plastik_is_gec_evre"),
            "gec_evre": ft.get("gec_evre"),
            "dosya": dosyalar[-1]}


def topla(kok: Path) -> dict:
    return {k: _oku(kok, ad) for k, ad in KOLLAR.items()}


def _kullanilir(v) -> bool:
    return v is not None and v["gecerli"] and bool(np.isfinite(v["b"]))


def _bagil(a: float, b: float) -> float:
    return abs(a - b) / abs(a) if a != 0.0 else float("inf")


def yargi(veri: dict) -> dict:
    out: dict = {"t_kiyas": T_KIYAS, "kollar": veri,
                 "kullanilmaz": [k for k, v in veri.items() if not _kullanilir(v)],
                 "esikler": {"R0": R0_ESIK, "M1": M1_ESIK, "M2": M2_ESIK,
                             "M3": M3_ESIK, "M4": M4_ESIK, "M5": M5_ESIK}}
    k1, w2 = veri.get("k_av1"), veri.get("W2")
    if not (_kullanilir(k1) and _kullanilir(w2)):
        out["R0"] = "OKUNMAZ"
        out["genel"] = "OKUNMAZ (R0 kollari eksik ya da gecersiz)"
        return out
    out["R0_fark"] = abs(k1["beta_300"] - w2["beta_300"])
    if out["R0_fark"] > R0_ESIK:
        out["R0"] = "DUSTU"
        out["genel"] = "OKUNMAZ (R0: tani kolu W2 fizigini uretmiyor)"
        return out
    out["R0"] = "GECTI"
    # --- M1
    E, W = k1.get("E_av_gec"), k1.get("W_pl_gec")
    if E is None or W is None or not np.isfinite(E) or not np.isfinite(W) or E + W <= 0:
        out["M1"] = "OKUNMAZ"
    else:
        out["M1_pay"] = float(E / (E + W))
        out["M1"] = ("AV GEC EVREDE BASKIN" if out["M1_pay"] >= M1_ESIK
                     else "AV GEC EVREDE IKINCIL")
    # --- M2
    k01 = veri.get("k_av01")
    if _kullanilir(k01):
        out["M2_delta"] = _bagil(k1["b"], k01["b"])
        out["M2"] = ("BETA GEC EVRE AV'SINE DUYARLI" if out["M2_delta"] > M2_ESIK
                     else "BETA GEC EVRE AV'SINE DUYARSIZ")
    else:
        out["M2"] = "OKUNMAZ"
    # --- M3 (ana yargi)
    uy, o01 = veri.get("UYorta"), veri.get("o_av01")
    if _kullanilir(uy) and _kullanilir(k01) and _kullanilir(o01):
        d1 = _bagil(uy["b"], w2["b"])
        d01 = _bagil(o01["b"], k01["b"])
        out["M3_delta_av1"] = d1
        out["M3_delta_av01"] = d01
        if d01 <= M3_ESIK and d01 <= 0.5 * d1:
            out["M3"] = "AV COZUNURLUK FARKININ ANA SEBEBI"
        elif d01 < d1:
            out["M3"] = "AV KISMI SEBEP"
        else:
            out["M3"] = "AV SEBEP DEGIL"
    else:
        out["M3"] = "OKUNMAZ"
    # --- M4
    k0 = veri.get("k_av0")
    if _kullanilir(k0) and _kullanilir(k01):
        out["M4_delta"] = _bagil(k0["b"], k01["b"])
        out["M4"] = ("AV 0,1'DE IHMAL EDILEBILIR" if out["M4_delta"] <= M4_ESIK
                     else "AV 0,1 HALA ETKILI")
    else:
        out["M4"] = "OKUNMAZ"
    # --- M5 (ayri soru)
    p64 = veri.get("k_p6400")
    if _kullanilir(p64):
        out["M5_delta"] = _bagil(p64["b"], k1["b"])
        out["M5"] = ("MERMI COZUNURLUGU GEC BETA'YA YANSIMIYOR"
                     if out["M5_delta"] <= M5_ESIK
                     else "MERMI COZUNURLUGU GEC BETA'YA YANSIYOR")
    else:
        out["M5"] = "OKUNMAZ"
    out["genel"] = out["M3"]
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kok", type=Path, required=True)
    ap.add_argument("--json", type=Path, default=None)
    a = ap.parse_args(argv)
    out = yargi(topla(a.kok))
    print("=" * 72)
    print("PROTOKOL A98 -- gec evre yapay viskozitesi (Y0 = 10 Pa, beta @ 300 s)")
    print("=" * 72)
    for k, v in out["kollar"].items():
        if v is None:
            print(f"  {k:>7}: YOK")
            continue
        print(f"  {k:>7}: beta(300) {v['beta_300']:.4f}  N {v['n']}  "
              f"gecerli {v['gecerli']}  E_av_gec {v['E_av_gec']}  "
              f"W_pl_gec {v['W_pl_gec']}")
    for ad in ("R0", "R0_fark", "M1", "M1_pay", "M2", "M2_delta", "M3",
               "M3_delta_av1", "M3_delta_av01", "M4", "M4_delta", "M5",
               "M5_delta"):
        if ad in out:
            print(f"  {ad}: {out[ad]}")
    print(f"GENEL: {out['genel']}")
    if a.json:
        a.json.write_text(json.dumps(out, indent=1, default=float),
                          encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
