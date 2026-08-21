"""A17 — çarpma noktasındaki **kütle oranı** `μ = m_hedef / m_mermi`.

## Hipotez

Bugüne kadar `β` için bakılan bütün çözünürlük ölçütleri **uzunluk**
ölçütüydü. `A1 = mermi çapı / yerel aralık ≥ 2` geçiyor (`2,039`) ve
o ölçüt merminin **aşama-1 ızgarasında** çözülüp çözülmediğini
soruyor.

Ama aktarımdan sonra mermi, aşama-2 ızgarasının içinde ilerliyor ve
orada ölçülmesi gereken şey uzunluk değil **kütle**:

| | |
|---|---|
| merminin kütlesi | `579,4 kg` |
| çarpma bölgesindeki hedef parçacığı (`λ₂ = 2`) | `≈ 4,66e4 kg` |
| **oran `μ`** | **`≈ 80`** |

> Mermi, kendisinden `80` kat ağır **tek** bir parçacığa çarpıyor.
> Böyle bir çarpışmada momentumun büyük kısmının geri sekmesi
> beklenen davranıştır — ve ölçülen tam bu (`β`'nın tamamı sekme,
> hedef payı `0`).

Bu, `λ₁` taramasının neden `β`'yı **düşürdüğünü** de açıklıyor:
`λ₁` mermiyi inceltiyor, hedefi değil; oran daha da bozuluyor.

## Bu betiğin işi

Gerçek sahneden `μ(λ₂)`'yi ölçmek ve `μ = 1` için gereken `λ₂`'yi
vermek. Sahne kurulumu — GPU koşusu **değil**, saniyeler sürer.

Sonuç bir **tahmin üretir**, kanıt değil: `μ ≈ 1` çözünürlüğünde
`β` ölçülmeden hiçbir şey doğrulanmış olmaz.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from faz44_dart_yakinsama import SAHNE  # noqa: E402

from dartrift.setup.refine import refine_scene_local  # noqa: E402
from dartrift.setup.scene import _build_mesh, build_scene  # noqa: E402

#: Çarpma anındaki DART kütlesi (`configs/p3_scene.yaml`).
M_MERMI_KG = 579.4
#: Krater ölçeği — bölge yarıçapı olarak kullanılıyor (rapor A17).
BOLGE_R_M = 15.0


def olc(lam2: float, *, spacing: float, r_ince2: float) -> dict:
    kaba = build_scene(spacing=spacing, device="cpu", **SAHNE)
    mesh = _build_mesh("icosphere", radius=SAHNE["radius"], subdiv=4)
    sc = (kaba if lam2 <= 1.0
          else refine_scene_local(kaba, mesh, r_ince=r_ince2, lam=lam2))
    hedef = ~np.asarray(sc.is_impactor, bool)
    d = np.linalg.norm(np.asarray(sc.x) - np.asarray(sc.impact_point)[None, :],
                       axis=1)
    b = hedef & (d <= BOLGE_R_M)
    m = np.asarray(sc.m)[b]
    if m.size == 0:
        raise SystemExit(f"lam2={lam2}: bolgede hedef parcacigi yok")
    med = float(np.median(m))
    return {
        "lam2": float(lam2),
        "s_ince_m": float(spacing / lam2),
        "n_bolge": int(m.size),
        "m_parcacik_medyan_kg": med,
        "mu": med / M_MERMI_KG,
        "N_toplam": int(sc.n),
    }


def gereken_lam2(o1: dict, spacing: float) -> float:
    """`μ = 1` için `λ₂`. `m ~ s³ ~ λ₂⁻³` olduğundan kapalı form."""
    return float(o1["lam2"] * o1["mu"] ** (1.0 / 3.0))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lam2", type=float, nargs="+",
                    default=[2.0, 4.0, 6.0, 8.0])
    ap.add_argument("--spacing", type=float, default=7.0)
    ap.add_argument("--r-ince2", type=float, default=25.0)
    ap.add_argument("--cikti", type=Path, default=None)
    a = ap.parse_args()

    print("=" * 70, flush=True)
    print("A17 — CARPMA BOLGESINDE KUTLE ORANI  mu = m_hedef / m_mermi",
          flush=True)
    print(f"  mermi = {M_MERMI_KG} kg, bolge r <= {BOLGE_R_M} m", flush=True)
    print("=" * 70, flush=True)
    print(f"  {'lam2':>6} {'s_ince':>9} {'n_bolge':>8} "
          f"{'m_parcacik':>12} {'mu':>10} {'N':>9}", flush=True)
    print("  " + "-" * 60, flush=True)
    sonuc = []
    for lam in a.lam2:
        o = olc(lam, spacing=a.spacing, r_ince2=a.r_ince2)
        sonuc.append(o)
        print(f"  {o['lam2']:>6.1f} {o['s_ince_m']:>9.4f} "
              f"{o['n_bolge']:>8d} {o['m_parcacik_medyan_kg']:>12.4e} "
              f"{o['mu']:>10.3f} {o['N_toplam']:>9d}", flush=True)

    hedef = gereken_lam2(sonuc[0], a.spacing)
    print(f"\n  mu = 1 icin gereken lam2 ~ {hedef:.2f}  "
          f"(s_ince ~ {a.spacing / hedef:.3f} m)", flush=True)
    gecen = [o for o in sonuc if o["mu"] <= 1.0]
    print(f"  taranan degerlerden mu <= 1 olan: "
          f"{[o['lam2'] for o in gecen] or 'YOK'}", flush=True)

    if a.cikti:
        a.cikti.write_text(json.dumps(
            {"m_mermi_kg": M_MERMI_KG, "bolge_r_m": BOLGE_R_M,
             "olcumler": sonuc, "gereken_lam2_mu1": hedef},
            ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
