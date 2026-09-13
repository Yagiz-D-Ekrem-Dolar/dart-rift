"""Protokol T — `β(t)` ve ejekta kütlesi zamanda platoya oturuyor mu (TANI).

`t = 24 ms` erken bir anlık görüntü. Uzman: *"0,024–0,2 s koşusunun
saati, düşük hızlı kazı ve yeniden yerleşimin sonuna kadar gereken saat
değildir."* Bu rapor, ileri modelin `fizik_tani.impuls_egrisi` alanındaki
`[t, P_hedef/p_imp, β_hedef, M_ejekta]` örneklerini okuyup
`momentum_defteri.plato_gecti` (kodda kilitli: son `%20` pencere,
`%5` bağıl, `1e-4` mutlak) ile yargılar.

> **BETİMLEYİCİ.** Karar kapısı değil; hangi sürenin yeterli olduğunu
> ölçmek için.

Kullanim:
    python scripts/t_zaman_raporu.py --kok kampanya --json S_T.json
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path

import numpy as np

_BURASI = Path(__file__).resolve().parent
sys.path.insert(0, str(_BURASI.parent / "src"))


def egri_ozeti(egri) -> dict:
    """İmpuls eğrisinden plato yargıları ve seçilmiş anlar."""
    from dartrift.observables.momentum_defteri import plato_gecti

    e = np.asarray(egri, dtype=np.float64)
    if e.ndim != 2 or e.shape[1] < 4 or len(e) < 3:
        return {"hata": "egri eksik ya da eski bicim (4 sutun gerekir)"}
    t, beta, M = e[:, 0], e[:, 2], e[:, 3]
    pb = plato_gecti(t, beta - 1.0)
    pm = plato_gecti(t, M / max(float(np.max(M)), 1e-300))
    secim = np.unique(np.clip(np.searchsorted(t, t[-1] * np.array(
        [0.05, 0.12, 0.25, 0.5, 0.75, 1.0])), 0, len(t) - 1))
    return {"beta_plato": pb, "M_plato": pm,
            "anlar": [[float(t[i]), float(beta[i] - 1.0), float(M[i])] for i in secim]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kok", type=Path, required=True)
    ap.add_argument("--json", type=Path, default=None)
    a = ap.parse_args(argv)
    cikti = {}
    for dz in sorted(glob.glob(str(a.kok / "T_*_sahne*.durumlar"))):
        ad = Path(dz).name.replace(".durumlar", "")
        for f in sorted(glob.glob(dz + "/nokta_*.npz")):
            z = np.load(f)
            ft = json.loads(str(z["fizik_tani"]))
            oz = egri_ozeti(ft.get("impuls_egrisi", []))
            cikti[ad] = oz
            print(f"== {ad}")
            if "hata" in oz:
                print("   ", oz["hata"])
                continue
            for tt, db, M in oz["anlar"]:
                print(f"   t = {tt:.4f} s   beta-1 = {db:+.5f}   M_ejekta = {M:.4g} kg")
            print(f"   beta plato: {'GECTI' if oz['beta_plato']['gecti'] else 'DUSTU'}"
                  f"  (sapma {oz['beta_plato']['sapma']:.3g}, tol {oz['beta_plato']['tolerans']:.3g})")
            print(f"   M_ej plato: {'GECTI' if oz['M_plato']['gecti'] else 'DUSTU'}")
    if a.json:
        a.json.write_text(json.dumps(cikti, indent=1, default=float), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
