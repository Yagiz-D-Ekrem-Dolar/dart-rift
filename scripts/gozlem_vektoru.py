"""Durum dosyasından **gözlem vektörü** — Protokol L'in girdisi.

Uzman (Soru 9/13): *"Skaler beta veya derinlik yerine hız–yön–boyut
dağılımı ve momentum vektörü."* Yerel, sabit kovaryanslı Gauss
olabilirlikte TEK skaler gözlem `JᵀΣ⁻¹J`'yi en çok rank 1 yapar; üç
parametre için en az üç bağımsız yönde duyarlı gözlem gerekir.

`t = 24 ms`'teki durumdan çıkarılabilen büyüklükler:

| ad | kaynak | ne ölçer |
|---|---|---|
| `d_merkez`, `d_max` | `krater_yuzey` | yüzey düşüşü (eksende / en büyük) |
| `V_krater`, `R_krater` | `krater_yuzey` | kazılan hacim, kenar yarıçapı |
| `dV_sikisma` | `krater_yuzey` | bağlı cismin hacim değişimi |
| `beta_hedef` | `momentum_defteri` | hedefe geçen eksenel momentum / `p_imp` |
| `M_ejekta` | `momentum_defteri` | kaçış hızını aşan dışa giden kütle |
| `P_ejekta` | `momentum_defteri` | ejektanın eksenel momentumu |
| `theta_ejekta` | `momentum_defteri` | ejekta momentumunun eksenden açısı |
| `mu_ejekta` | burada | `M(>v) ∝ v^(-3μ)` eğimi |

Tanımsız olan (ör. ejekta yoksa açı) `nan` döner; rapor o gözlemi o
kolda **düşürür** ve bunu yazar.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

_BURASI = Path(__file__).resolve().parent
sys.path.insert(0, str(_BURASI.parent / "src"))

GOZLEMLER = ("d_merkez", "d_max", "V_krater", "R_krater", "dV_sikisma",
             "beta_hedef", "M_ejekta", "P_ejekta", "theta_ejekta", "mu_ejekta")

#: `mu` uydurmasında eşik başına en az bu kadar parçacık.
MU_EN_AZ_PARCACIK = 10
#: En az bu kadar geçerli eşik yoksa `mu` tanımsız.
MU_EN_AZ_ESIK = 3


def ejekta_egimi(x, v, m, x0, *, v_esc: float, center=None) -> float:
    """Dışa giden, başlangıç yarıçapını aşmış, `v_r > v_esc` madde için
    `M(>v)`'nin log-log eğiminden `μ` (`M ∝ v^(-3μ)`)."""
    c = np.zeros(3) if center is None else np.asarray(center, float)
    d = x - c
    r = np.linalg.norm(d, axis=1)
    r0 = np.linalg.norm(x0 - c, axis=1)
    vr = np.einsum("ij,ij->i", v, d) / np.maximum(r, 1e-300)
    ej = (vr > v_esc) & (r > r0)
    if np.count_nonzero(ej) < MU_EN_AZ_PARCACIK * MU_EN_AZ_ESIK:
        return float("nan")
    ve, me = vr[ej], m[ej]
    esik = np.geomspace(v_esc, float(np.percentile(ve, 99.0)), 10)
    lv, lm = [], []
    for e in esik:
        s = ve > e
        if np.count_nonzero(s) >= MU_EN_AZ_PARCACIK:
            lv.append(np.log(e))
            lm.append(np.log(me[s].sum()))
    if len(lv) < MU_EN_AZ_ESIK:
        return float("nan")
    return float(-np.polyfit(lv, lm, 1)[0] / 3.0)


def gozlem_vektoru(d) -> dict:
    """`ileri_kosu_merdiven` durum dosyası → gözlemler (sözlük)."""
    from dartrift.observables.crater_shape import krater_yuzey_durumdan
    from dartrift.observables.momentum_defteri import momentum_defteri
    from dartrift.observables.momentum_transfer import escape_speed

    hedef = np.asarray(d["mermi_kesri"]) < 0.5
    m = np.asarray(d["m"], float)
    R = float(d["R"])
    v_esc = float(escape_speed(float(m[hedef].sum()), R))
    out = {k: float("nan") for k in GOZLEMLER}
    try:
        ky = krater_yuzey_durumdan(d)
        out.update(d_merkez=ky.derinlik_merkez, d_max=ky.derinlik,
                   V_krater=ky.hacim, R_krater=ky.yaricap,
                   dV_sikisma=ky.hacim_degisimi)
    except (KeyError, ValueError):
        pass
    md = momentum_defteri(
        d["x"], d["v"], m, mermi_kesri=np.asarray(d["mermi_kesri"], float),
        R=R, v_esc=v_esc, ehat=np.asarray(d["ehat"], float),
        p_imp=float(d["p_imp"]))
    out.update(beta_hedef=md["beta_hedef"], M_ejekta=md["M_ejekta"],
               P_ejekta=md["P_ejekta_eksenel"],
               theta_ejekta=md.get("theta_ejekta_derece", float("nan")))
    x = np.asarray(d["x"], float)[hedef]
    out["mu_ejekta"] = ejekta_egimi(
        x, np.asarray(d["v"], float)[hedef], m[hedef],
        np.asarray(d["x_referans"], float)[hedef], v_esc=v_esc)
    return {k: float(v) if v is not None else float("nan")
            for k, v in out.items()}
