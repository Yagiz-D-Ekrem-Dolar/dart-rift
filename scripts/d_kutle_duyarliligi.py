"""Protokol D kütle duyarlılığı — gözlem hangi hedef kütlesinde model aralığına girer?

Kilitli D yargısını DEĞİŞTİRMEZ; `S_DART_*.json` çıktısından türetir.

Gözlenen `β` hedef kütlesiyle (yaklaşık) orantılı ve `σ_β`'nın baskın terimi
bağıl sistematik (`0,105 β`): `β_gözlem(M) ≈ β₀ · M / M₀`,
`σ(M) ≈ σ_rel · β_gözlem(M)`, `σ_rel = σ₀ / β₀`. Gözlem bandının `2σ` alt
ucu modelin en büyük `β`'sına eşit olduğu kütle:

    M* = M₀ · β_max / (β₀ · (1 − 2 σ_rel))

Karşılık gelen yığın yoğunluğu (hacim sabit): `ρ* = ρ₀ · M* / M₀`.
`M* ≥ M₀` → gözlem zaten bandın içinde (kütle azaltmaya gerek yok).
`1 − 2 σ_rel ≤ 0` → band sıfıra iner; eşik tanımsız.

**Varsayım (öz denetim, 2026-09-15):** `β_max` (modelin önsel boyunca en
büyük `β`'sı) kütleden bağımsız tutulur. Gerçekte hedef yoğunluğu değişince
sahne ve modelin `β`'sı da değişir; bu betik yalnız **gözlenen** `β`'nın
kütleye duyarlılığını verir, modelin tepkisini değil (o Protokol U'nun
yoğunluk varyantıyla ölçülür).

Kullanim:
    python scripts/d_kutle_duyarliligi.py --json docs/olcumler/D_kesif/S_DART_*.json --rho0 1800
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def esik(d: dict, rho0: float) -> dict:
    g, k = d["gozlem"], d["kapsama"]
    beta0, sig0, M0 = float(g["beta"]), float(g["sigma_beta"]), float(g["hedef_kutlesi"])
    bmax = float(k["beta_max_model"])
    s_rel = sig0 / beta0
    payda = 1.0 - 2.0 * s_rel
    if payda <= 0:
        return {"karar": "TANIMSIZ", "sigma_rel": s_rel}
    M_yildiz = M0 * bmax / (beta0 * payda)
    oran = M_yildiz / M0
    return {"karar": "BANDA GIRMEK ICIN KUTLE AZALMALI" if oran < 1 else "ZATEN BANDA",
            "beta_gozlem": beta0, "beta_max_model": bmax, "sigma_rel": s_rel,
            "M0": M0, "M_esik": M_yildiz, "kutle_orani": oran,
            "rho0": rho0, "rho_esik": rho0 * oran}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", type=Path, nargs="+", required=True)
    ap.add_argument("--rho0", type=float, default=1800.0, help="sahne yigin yogunlugu (SAHNE)")
    a = ap.parse_args(argv)
    for p in a.json:
        r = esik(json.loads(p.read_text(encoding="utf-8")), a.rho0)
        if r["karar"] == "TANIMSIZ":
            print(f"{p.name}: TANIMSIZ (sigma_rel {r['sigma_rel']:.3f})")
            continue
        print(f"{p.name}: beta gozlem {r['beta_gozlem']:.2f}, "
              f"model max {r['beta_max_model']:.2f} -> "
              f"M* / M0 = {r['kutle_orani']:.3f}  (rho* = {r['rho_esik']:.0f} kg/m3)  {r['karar']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
