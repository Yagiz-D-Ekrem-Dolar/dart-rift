"""Geçiş noktası `x₀` çözünürlüğe dayanıklı mı — Protokol I.

H ölçtü (A69): krater derinliği **mutlak olarak yakınsamıyor**
(`0,36 → 0,61 m`, `%72`) ama `Y₀` ile ilişkisi iki ölçekte de aynı
(`r = −0,943` vs `−0,925`).

Fiziksel olarak anlamlı parametre derinliğin **değeri** değil,
**geçiş noktası `x₀`**: kohezyon hangi değerin üstünde krateri
sınırlamaya başlıyor. Bizim kraterimiz `0,5 m`, DART'ınki `~10 m` —
**mutlak ölçek zaten aktarılamaz.** Aktarılabilecek olan `x₀`.

Kullanim:
    python scripts/gecis_raporu.py \\
        --kaba  kampanya/G1_uretim_sahne*.dilim*_3.durumlar \\
        --orta  kampanya/I_orta_sahne*.dilim*_6.durumlar
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

# --- PROTOKOL I esikleri, SONUCLARDAN ONCE kilitlendi ---------------
#: `|x0_orta - x0_kaba|` bu kadar sigma altindaysa DAYANIKLI.
DAYANIKLI_SIGMA = 2.0
#: Bu kadar sigma ustundeyse DAYANIKSIZ; arasi ZAYIF.
DAYANIKSIZ_SIGMA = 4.0
#: Uydurma gecerlilik on kosulu.
R2_ESIGI = 0.85


def _yukle():
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import vekil_posterior as vp

    return vp


def veri_topla(desenler) -> tuple:
    """Dizin desenlerinden `(log10 Y0, krater)` — tohumlar ortalanır."""
    import glob

    vp = _yukle()
    dizinler = []
    for d in desenler:
        dizinler.extend(glob.glob(str(d)) or [str(d)])
    if not dizinler:
        raise SystemExit(f"dizin bulunamadi: {desenler}")
    return vp._veri(dizinler)


def x0_belirsizligi(x, d, *, n_ornek: int = 24, tohum: int = 0) -> dict:
    """`x₀`'ın örneklem sapması — birini dışarıda bırak.

    Her turda bir nokta çıkarılıp yeniden uydurulur; `x₀`'ların
    sapması **jackknife** ile ölçeklenir:

        sigma_jk = sqrt((n-1)/n * sum((x0_i - x0_ort)^2))

    Bootstrap değil çünkü `24` noktada tekrarlı örnekleme sigmoidin
    uçlarını boşaltıp uydurmayı patlatabiliyor.
    """
    vp = _yukle()
    x = np.asarray(x, float)
    d = np.asarray(d, float)
    n = len(x)
    x0lar = []
    for i in range(n):
        k = np.ones(n, bool)
        k[i] = False
        v = vp.uydur(x[k], d[k], tohum=tohum)
        x0lar.append(v["x0"])
    x0lar = np.asarray(x0lar)
    ort = float(x0lar.mean())
    sigma = float(np.sqrt((n - 1) / n * ((x0lar - ort) ** 2).sum()))
    return {"x0_jk_ort": ort, "sigma_x0": sigma, "n": n,
            "x0_min": float(x0lar.min()), "x0_max": float(x0lar.max())}


def olcek_raporu(ad: str, x, d) -> dict:
    vp = _yukle()
    v = vp.uydur(x, d)
    jk = x0_belirsizligi(x, d)
    gecerli = (v["R2"] > R2_ESIGI) and v["x0_veri_icinde"]
    return {
        "ad": ad, "n": int(len(x)),
        "x0": v["x0"], "w": v["w"], "R2": v["R2"],
        "d_alt": v["d_alt"], "d_ust": v["d_ust"],
        "d_alt_sinirda": v["d_alt_sinirda"],
        "x0_veri_icinde": v["x0_veri_icinde"],
        "veri_araligi": v["veri_araligi"],
        "artik_sigma": v["artik_sigma"],
        "sigma_x0": jk["sigma_x0"],
        "x0_jk_ort": jk["x0_jk_ort"],
        "gecerli": bool(gecerli),
    }


def yargi(kaba: dict, orta: dict) -> dict:
    if not (kaba["gecerli"] and orta["gecerli"]):
        sebep = []
        for o in (kaba, orta):
            if o["R2"] <= R2_ESIGI:
                sebep.append(f"{o['ad']}: R2 = {o['R2']:.3f} <= {R2_ESIGI}")
            if not o["x0_veri_icinde"]:
                sebep.append(f"{o['ad']}: x0 veri ARALIGININ DISINDA")
        return {"karar": "OKUNMAZ", "sebep": "; ".join(sebep)}
    dx = abs(orta["x0"] - kaba["x0"])
    s = float(np.sqrt(kaba["sigma_x0"] ** 2 + orta["sigma_x0"] ** 2))
    kat = dx / s if s > 0 else float("inf")
    if kat < DAYANIKLI_SIGMA:
        karar = "DAYANIKLI"
    elif kat < DAYANIKSIZ_SIGMA:
        karar = "ZAYIF"
    else:
        karar = "DAYANIKSIZ"
    return {"karar": karar, "delta_x0": dx, "sigma_birlesik": s,
            "kat": kat, "sebep": ""}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kaba", nargs="+", required=True)
    ap.add_argument("--orta", nargs="+", required=True)
    ap.add_argument("--json", type=Path, default=None)
    a = ap.parse_args(argv)

    xk, dk, _ = veri_topla(a.kaba)
    xo, do, _ = veri_topla(a.orta)
    kaba = olcek_raporu("kaba", xk, dk)
    orta = olcek_raporu("orta", xo, do)

    print("=" * 72)
    print("GECIS NOKTASI RAPORU -- Protokol I")
    print("=" * 72)
    print(f"{'olcek':>6} {'n':>4} {'x0':>8} {'sigma_x0':>9} {'w':>7} "
          f"{'R^2':>7} {'gecerli':>8}")
    for o in (kaba, orta):
        print(f"{o['ad']:>6} {o['n']:4d} {o['x0']:8.3f} {o['sigma_x0']:9.4f} "
              f"{o['w']:7.3f} {o['R2']:7.4f} {str(o['gecerli']):>8}")
        if o["d_alt_sinirda"]:
            print(f"       ! {o['ad']}: d_alt KISIT SINIRINDA "
                  f"(yuksek Y0 asimptotu veriden degil)")
        if not o["x0_veri_icinde"]:
            print(f"       ! {o['ad']}: x0 veri araliginin DISINDA "
                  f"{o['veri_araligi']}")

    y = yargi(kaba, orta)
    print("\n" + "=" * 72)
    if y["karar"] == "OKUNMAZ":
        print(f"YARGI: OKUNMAZ -- {y['sebep']}")
    else:
        print(f"  |x0_orta - x0_kaba| = {y['delta_x0']:.4f}")
        print(f"  birlesik sigma      = {y['sigma_birlesik']:.4f}")
        print(f"  kat                 = {y['kat']:.2f}"
              f"   (< {DAYANIKLI_SIGMA} dayanikli, "
              f"> {DAYANIKSIZ_SIGMA} dayaniksiz)")
        print(f"\nYARGI: {y['karar']}")
        if y["karar"] == "DAYANIKLI":
            print(f"  Gecis noktasi Y0 = {10 ** kaba['x0']:.3g} .. "
                  f"{10 ** orta['x0']:.3g} Pa araliginda ve cozunurlukten"
                  f" BAGIMSIZ.")
        print("\n  NOT: mutlak krater derinligi HALA yakinsamamis (A69).")
        print("  Bu rapor YALNIZ x0'in dayanikliligini soyluyor.")

    if a.json:
        a.json.write_text(json.dumps(
            {"kaba": kaba, "orta": orta, "yargi": y}, indent=2),
            encoding="utf-8")
        print(f"\nyazildi: {a.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
