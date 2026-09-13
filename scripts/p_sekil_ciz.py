"""Posterior figürleri — `p_sekil_verisi.py` çıktısından (yerel).

Üç panel dizisi:

1. Temsili üç vaka (düşük / orta / yüksek gerçek `Y₀`): eksen başına
   marjinal posterior + gerçek değer (dikey çizgi), doğal birimde.
2. Kalibrasyon eğrisi: nominal merkezi aralık düzeyine karşı gerçekleşen
   kapsama; köşegen = kusursuz kalibrasyon.
3. PIT histogramı eksen başına (kalibre → düz).

Kullanim:
    python scripts/p_sekil_ciz.py --veri P_sekil_kaba.json --cikti docs/sekil/posterior_kaba.png
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

ETIKET = {"blok_alpha0": r"$\alpha_b$", "log10_Y0": r"$\log_{10} Y_0$ [Pa]",
          "blok_kesri": r"$f$"}
SINIR = {"blok_alpha0": (1.00, 1.30), "log10_Y0": (3.0, 7.0), "blok_kesri": (0.05, 0.50)}


def dogal(ad: str, u):
    lo, hi = SINIR[ad]
    return lo + np.asarray(u) * (hi - lo)


def ciz(v: dict, cikti: Path, baslik: str = "") -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    eksen = np.asarray(v["eksen_u"])
    adlar = v["eksenler"]
    vak = v["vakalar"]
    y0 = np.array([c["u"][1] for c in vak])
    secim = [int(np.argmin(np.abs(y0 - q))) for q in (0.15, 0.5, 0.85)]

    fig = plt.figure(figsize=(13, 9.5))
    gs = fig.add_gridspec(4, 3, height_ratios=[1, 1, 1, 1.15], hspace=0.55, wspace=0.28)
    renk = ("#1f77b4", "#d62728", "#2ca02c")
    for sat, (idx, rk) in enumerate(zip(secim, renk, strict=True)):
        c = vak[idx]
        for j, ad in enumerate(adlar):
            ax = fig.add_subplot(gs[sat, j])
            m = np.asarray(c["marjinal"][j])
            x = dogal(ad, eksen)
            ax.fill_between(x, m / m.max(), color=rk, alpha=0.35)
            ax.plot(x, m / m.max(), color=rk, lw=1.5)
            ax.axvline(dogal(ad, c["u"][j]), color="k", lw=1.6, ls="--")
            lo, hi = dogal(ad, np.asarray(c["hdi68_u"][j]))
            ax.axvspan(lo, hi, color="0.85", zorder=0)
            ax.set_xlim(*SINIR[ad])
            ax.set_yticks([])
            if sat == 0:
                ax.set_title(ETIKET[ad], fontsize=12)
            if j == 0:
                ax.set_ylabel(f"vaka {sat + 1}\n(kat {c['kat']})", fontsize=9)
    ax = fig.add_subplot(gs[3, 0])
    nom = np.asarray(v["nominal"])
    ax.plot([0, 1], [0, 1], color="0.5", lw=1)
    for (ad, k), rk in zip(v["kapsama_egrisi"].items(), renk, strict=True):
        ax.plot(nom, k, "o-", color=rk, label=ETIKET[ad], ms=4)
    ax.set_xlabel("nominal merkezi aralık")
    ax.set_ylabel("gerçekleşen kapsama")
    ax.set_title("kalibrasyon (dış doğrulama)", fontsize=10)
    ax.legend(fontsize=8, loc="upper left")
    for j, (ad, rk) in enumerate(zip(adlar, renk, strict=True)):
        if j == 0:
            continue
        ax = fig.add_subplot(gs[3, j])
        pit = np.array([c["pit"][j] for c in vak])
        ax.hist(pit, bins=np.linspace(0, 1, 9), color=rk, alpha=0.7, edgecolor="k")
        ax.axhline(len(pit) / 8, color="k", ls="--", lw=1)
        ax.set_title(f"PIT {ETIKET[ad]}", fontsize=10)
        ax.set_xlabel("PIT")
    pit0 = np.array([c["pit"][0] for c in vak])
    fig.text(0.02, 0.01, f"PIT {ETIKET[adlar[0]]}: ortalama {pit0.mean():.2f}, "
             f"sapma {pit0.std():.2f} (düz dağılım 0,50 / 0,29)", fontsize=8)
    fig.suptitle(baslik or f"Katlı dış doğrulama posteriorları — {len(vak)} vaka, "
                 f"gözlemler: {', '.join(v.get('secilen', []))}", fontsize=10)
    cikti.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(cikti, dpi=130, bbox_inches="tight")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--veri", type=Path, required=True)
    ap.add_argument("--cikti", type=Path, required=True)
    ap.add_argument("--baslik", default="")
    a = ap.parse_args(argv)
    ciz(json.loads(a.veri.read_text(encoding="utf-8")), a.cikti, a.baslik)
    print("yazildi:", a.cikti)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
