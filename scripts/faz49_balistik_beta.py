"""A12'nin acik sorusu: hedef maddesi kacis hizini asiyor mu, ve
kontrol yuzeyini NE ZAMAN gececek?

## Neden UCUZ olarak cevaplanabilir

Yercekimi KAPALI (`GravityParams(enabled=False)`). Serbest kalmis bir
parcacik dogru cizgide gider. Yani TEK BIR DURUMDAN, her parcacigin
`r = 2R` yuzeyini ne zaman gececegi **tam olarak** hesaplanabilir:

    |x + v t| = r_ctrl   ->   t = ikinci derece denklemin koku

Buradan `beta(t)` GELECEGE dogru, ek simulasyon KOSMADAN cikarilir.

> Yaklasim: parcaciklar hala basinc/mukavemet altinda hizlanabilir.
> Bu yuzden hesaplanan gecis zamani bir **UST SINIR** degil, serbest
> ucus varsayimi altinda bir kestirimdir. Ama "hic gecmez mi, yoksa
> gec mi gecer" sorusunu KESIN ayirir.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

# REPO dosyanin KENDISINDEN turetiliyor. Once `sys.path.insert(0, "src")`
# yaziliydi -- goreli yol, yani betik yalnizca depo kokunden cagrildiginda
# calisiyordu ve SLURM isinde sessizce ImportError veriyordu.
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

# UTF-8 KORUMASI: `faz47_g4_kapi.py` bir kez `UnicodeEncodeError` ile
# dustu ve urettigi raporu yok etti. SLURM isi `PYTHONIOENCODING=utf-8`
# veriyor ama betik elle de kosulabiliyor.
for _akis in (sys.stdout, sys.stderr):
    try:
        _akis.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

from faz44_dart_yakinsama import SAHNE, _malzeme  # noqa: E402

from dartrift.cpu_reference.sph_ref import RefParams  # noqa: E402
from dartrift.observables.momentum_transfer import escape_speed  # noqa: E402
from dartrift.setup.refine import refine_scene_local  # noqa: E402
from dartrift.setup.scene import _build_mesh, build_scene  # noqa: E402
from dartrift.warp_core.solver_solid import WarpSolid3D  # noqa: E402

ADIM = int(sys.argv[1]) if len(sys.argv) > 1 else 1500
kaba = build_scene(spacing=7.0, device="cpu", **SAHNE)
mesh = _build_mesh("icosphere", radius=SAHNE["radius"], subdiv=4)
rs = refine_scene_local(kaba, mesh, r_ince=25.0, lam=2.0)
imp = np.asarray(rs.is_impactor, bool)
hedef = ~imp
R = float(rs.target_radius)
M = float(rs.target_mass)
v_esc = escape_speed(M, R)
r_ctrl = 2.0 * R
p_imp = float(np.linalg.norm(rs.impactor_momentum))
ehat = np.asarray(rs.impactor_momentum) / p_imp

sol = WarpSolid3D(np.ascontiguousarray(rs.x), np.ascontiguousarray(rs.v),
    np.ascontiguousarray(rs.m), np.zeros(rs.n), rs.h, _malzeme(),
    RefParams(cfl=0.25), alpha0=np.ascontiguousarray(rs.alpha0),
    Y0=np.ascontiguousarray(rs.Y0), device="cuda:0", check_every=10**9)
t = 0.0
for _ in range(ADIM):
    dt = sol.compute_dt()
    sol.step(dt)
    t += dt
st = sol.state_numpy()
x, v, m = st["x"], st["v"], st["m"]
print(f"t = {t:.5e} s,  v_kacis = {v_esc:.5f} m/s,  r_ctrl = {r_ctrl:.0f} m\n")

r = np.linalg.norm(x, axis=1)
vr = np.einsum("ij,ij->i", v, x / np.maximum(r, 1e-300)[:, None])
h_kacan = hedef & (vr > v_esc)
print(f"  HEDEF parcacigi              : {int(hedef.sum())}")
print(f"  v_r > v_kacis olan HEDEF     : {int(h_kacan.sum())} "
      f"({100*h_kacan.sum()/hedef.sum():.1f}%)")
print(f"  bunlarin kutlesi             : {m[h_kacan].sum():.4e} kg "
      f"({100*m[h_kacan].sum()/m[hedef].sum():.3f}% hedefin)")
print(f"  v_r dagilimi (kacanlar)      : "
      f"medyan {np.median(vr[h_kacan]):.3f}  p90 {np.percentile(vr[h_kacan],90):.3f}"
      f"  max {vr[h_kacan].max():.3f} m/s")

# BALISTIK gecis zamani: |x + v t| = r_ctrl
a_ = np.einsum("ij,ij->i", v, v)
b_ = 2.0 * np.einsum("ij,ij->i", x, v)
c_ = r**2 - r_ctrl**2
disk = b_**2 - 4*a_*c_
gecer = (a_ > 0) & (disk >= 0)
t_gec = np.full(len(x), np.inf)
kok = (-b_[gecer] + np.sqrt(disk[gecer])) / (2*a_[gecer])
t_gec[gecer] = np.where(kok > 0, kok, np.inf)
onemli = hedef & np.isfinite(t_gec) & (vr > v_esc)
print("\n  BALISTIK gecis zamani (hedef, v_r > v_kacis):")
if onemli.any():
    tg = t_gec[onemli]
    for q in (10, 25, 50, 75, 90):
        print(f"    p{q:<3d} = {np.percentile(tg, q):10.3f} s")
    print(f"    min  = {tg.min():10.3f} s")
    # beta(t) gelecege dogru
    print("\n  beta(t) KESTIRIMI (serbest ucus varsayimi):")
    p_ej0 = np.sum(m[imp & (r > r_ctrl)][:, None] * v[imp & (r > r_ctrl)], axis=0)
    for T in (0.2, 1.0, 5.0, 10.0, 30.0, 100.0, np.inf):
        sec = (t_gec <= T) | (r > r_ctrl)
        sec &= (vr > v_esc)
        p_ej = np.sum(m[sec][:, None] * v[sec], axis=0)
        beta = 1.0 - float(np.dot(p_ej, ehat)) / p_imp
        print(f"    t = {T:8.1f} s -> beta = {beta:9.5f}  "
              f"(ejekta {int(sec.sum()):6d} parcacik)")
