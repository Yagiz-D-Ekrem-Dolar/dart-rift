"""Kaçan madde **şoklanmış mı** — ölçüt `docs/A17-HASAR-OLCUTU.md` EK-2.

`β`'nın tamamı merminin geri sekmesi (hedef payı tam sıfır, iş
`1512733`). Bu betik o sekmenin fiziksel olup olmadığını tek soruyla
sınıyor: kaçan parçacıklar **şoklanmış** mı, yoksa hiç ısınmadan katı
gibi mi sekiyor?

Eşikler Tillotson bazaltın kendi sabitlerinden (`configs/p3_scene.yaml`):
`u_iv = 4,72e6`, `u_cv = 1,82e7 J/kg`. Uydurma yok.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

U_IV = 4.72e6
U_CV = 1.82e7
V_CARPMA = 6144.9


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--durum", type=Path, required=True)
    ap.add_argument("--cikti", type=Path, default=None)
    a = ap.parse_args()

    z = np.load(a.durum)
    if "u" not in z.files:
        raise SystemExit("bu npz `u` icermiyor -- kosuyu yeniden al")
    x, v, m, u = z["x"], z["v"], z["m"], z["u"]
    R, v_esc = float(z["R"]), float(z["v_esc"])
    hedef = z["hedef"].astype(bool)

    r = np.linalg.norm(x, axis=1)
    v_r = np.einsum("ij,ij->i", v, x) / np.maximum(r, 1e-30)
    kacan = (r > 2.0 * R) & (v_r > v_esc)
    mermi = ~hedef

    if not kacan.any():
        raise SystemExit("kacan parcacik yok")
    mk, uk = m[kacan], u[kacan]
    u_kacan = float((mk * uk).sum() / mk.sum())

    ke0 = 0.5 * V_CARPMA**2
    d = {
        "n_kacan": int(kacan.sum()),
        "kacan_kutle_kg": float(mk.sum()),
        "kacan_hedef_kutlesi_kg": float(m[kacan & hedef].sum()),
        "u_kacan_kutle_agirlikli": u_kacan,
        "u_kacan_medyan": float(np.median(uk)),
        "u_kacan_max": float(uk.max()),
        "u_sahne_max": float(u.max()),
        "u_mermi_max": float(u[mermi].max()) if mermi.any() else float("nan"),
        "u_iv": U_IV, "u_cv": U_CV,
        "gelen_ozgul_KE": ke0,
        "u_kacan / u_iv": u_kacan / U_IV,
        "u_kacan / gelen_KE": u_kacan / ke0,
    }
    for k, val in d.items():
        print(f"  {k:28s} = {val:.6g}", flush=True)

    if u_kacan >= U_IV:
        yargi = "kacan_madde_SOKLANMIS"
    elif u_kacan < 0.1 * U_IV:
        yargi = "kacan_madde_HIC_SOKLANMAMIS"
    else:
        yargi = "kismi"
    print(f"\n  YARGI = {yargi}", flush=True)
    d["yargi"] = yargi
    if a.cikti:
        a.cikti.write_text(json.dumps(d, ensure_ascii=False, indent=2),
                           encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
