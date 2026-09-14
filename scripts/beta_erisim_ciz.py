"""β erişilebilirlik figürü — model β aralıkları ile DART gözlem bandı (Protokol D + U).

Yeni hesap yapmaz; `S_DART_*.json` (Protokol D) ve `S_U.json` (Protokol U)
çıktılarını tek bir figürde gösterir:

- Her havuz için modelin önsel boyunca ürettiği `β` aralığı (yatay çubuk),
  gözlenen `β` ve `±2σ` bandı (dikey şerit, havuzun kendi hedef kütlesiyle).
- U varyantları için simülasyon `β` (nokta) ve o varyantın gözlem bandı.

Kullanim:
    python scripts/beta_erisim_ciz.py --kok kampanya --cikti docs/sekil/beta_erisim.png
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

HAVUZLAR = (("S_DART_kesif_k72.json", "kaba-72, 24 ms (keşif)"),
            ("S_DART_kesif_o72.json", "orta-72, 24 ms (keşif)"),
            ("S_DART_kesif_i48.json", "ince-48, 24 ms (keşif)"),
            ("S_DART_Qk.json", "Q2 kaba, 0,1 s"),
            ("S_DART_Qo.json", "Q3 orta, 0,1 s"),
            ("S_DART_i72.json", "ince-72, 24 ms"))


def satirlar(kok: Path) -> list[dict]:
    """Çizilecek satırlar (sınanabilir saf kısım)."""
    out = []
    for dosya, ad in HAVUZLAR:
        p = kok / dosya
        if not p.exists():
            continue
        d = json.loads(p.read_text(encoding="utf-8"))
        k, g = d["kapsama"], d["gozlem"]
        out.append({"ad": ad, "tur": "havuz", "b_min": 1.0 + 10.0 ** k["tahmin_min"],
                    "b_max": k["beta_max_model"], "gozlem": g["beta"],
                    "sigma": g["sigma_beta"], "karar": k["karar"]})
    p = kok / "S_U.json"
    if p.exists():
        u = json.loads(p.read_text(encoding="utf-8"))
        for anah, r in sorted(u.get("satirlar", {}).items()):
            if r.get("karar") == "OKUNMAZ":
                continue
            out.append({"ad": f"U {anah}", "tur": "varyant",
                        "b_sim": 1.0 + r["beta_eksi_1_sim"],
                        "gozlem": 1.0 + r["beta_eksi_1_gozlem"], "sigma": r["sigma_beta"],
                        "karar": r["karar"]})
    return out


def ciz(sat: list[dict], cikti: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(9, 0.45 * max(len(sat), 4) + 1.5))
    for i, s in enumerate(sat):
        y = len(sat) - 1 - i
        ax.fill_betweenx([y - 0.4, y + 0.4], s["gozlem"] - 2 * s["sigma"],
                         s["gozlem"] + 2 * s["sigma"], color="0.85", zorder=0)
        ax.plot([s["gozlem"]] * 2, [y - 0.4, y + 0.4], color="k", lw=1.2)
        if s["tur"] == "havuz":
            ax.plot([s["b_min"], s["b_max"]], [y, y], color="#1f77b4", lw=6,
                    solid_capstyle="butt")
        else:
            ax.plot(s["b_sim"], y, "o", color="#d62728", ms=7)
    ax.set_yticks(range(len(sat)))
    ax.set_yticklabels([f"{s['ad']}  [{s['karar']}]" for s in reversed(sat)], fontsize=8)
    ax.set_xlabel("β  (mavi: model aralığı · kırmızı: varyant · gri: gözlem ±2σ)")
    ax.set_title("DART β'sı modelin erişebildiği aralıkta mı?", fontsize=10)
    cikti.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(cikti, dpi=130, bbox_inches="tight")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kok", type=Path, required=True)
    ap.add_argument("--cikti", type=Path, required=True)
    a = ap.parse_args(argv)
    sat = satirlar(a.kok)
    if not sat:
        print("cizilecek JSON yok")
        return 1
    ciz(sat, a.cikti)
    print("yazildi:", a.cikti, f"({len(sat)} satir)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
