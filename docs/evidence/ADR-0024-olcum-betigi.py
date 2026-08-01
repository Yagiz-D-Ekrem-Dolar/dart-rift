"""ADR-0024 kaniti: yercekimi FAZ 3/4'te nerede onemli, nerede degil?

(1) t=0'da SPH ivmesi TAM sifir mi? (kurulum denge mi?)
(2) Yercekimi, carpma suresi boyunca parcaciklari ne kadar oynatir —
    parcacik araligina gore?
(3) Kacis hizi ejekta hizlarina gore nerede? (gec faz icin yercekimi sart mi?)
(4) Agac bayatlama hatasi — DOGRU normalizasyonla (maks|g|'ye gore; yerel
    |g| merkeze yakin sifira gittigi icin ona bolmek yapay buyutur).
(5) Sonumlemeli settling penceresi: P3-VR-01 saglaniyor mu, hangi payla?
"""

import dataclasses
import sys

import numpy as np

sys.path.insert(0, r"C:\Users\yagiz\Desktop\videos\dart-rift\src")
from dartrift.cpu_reference.materials import (
    GravityParams,
    MaterialParams,
    PorosityParams,
    StrengthParams,
)
from dartrift.cpu_reference.sph_ref import RefParams
from dartrift.setup.rubble_generator import build_rubble_pile
from dartrift.setup.settling import binding_energy, settle_pile
from dartrift.setup.shape_mesh import icosphere
from dartrift.warp_core.solver_solid import WarpSolid3D

G = 6.6743e-11
G_SHEAR, RHO, Y0 = 2.27e10, 1800.0, 1.0e4
OUT = open(sys.argv[1], "w", encoding="utf-8", buffering=1)


def emit(s):
    print(s, file=OUT, flush=True)


mat = MaterialParams(
    eos="tillotson",
    strength=StrengthParams(enabled=True, Y0=Y0, mu_f=0.6, YM=1.5e9,
                            shear_G=G_SHEAR, jaumann=True),
    porosity=PorosityParams(enabled=True, alpha0=1.6, Pe=1.0e6, Ps=1.0e8, n_exp=2.0),
    gravity=GravityParams(enabled=True, G=G, eps=0.0, mode="barnes_hut", theta=0.5),
    density_method="continuity",
)
mat_ng = dataclasses.replace(mat, gravity=dataclasses.replace(mat.gravity, enabled=False))

mesh = icosphere(4, 80.0)
pile = build_rubble_pile(mesh, spacing=7.0, bulk_density=RHO, root_seed=17,
                         model_class="M0", matrix_alpha0=1.6)
n, x0 = pile.n, np.ascontiguousarray(pile.x)
kw = dict(alpha0=np.ascontiguousarray(pile.alpha0), Y0=np.ascontiguousarray(pile.Y0),
          device="cuda:0", check_every=10**9)
zer = np.zeros_like(x0)

# ---------- (1) kurulum denge mi ----------
s_n = WarpSolid3D(x0, zer, pile.m, np.zeros(n), 14.0, mat_ng, RefParams(cfl=0.25), **kw)
s_n._eval()
st = s_n.state_numpy()
a_sph = np.linalg.norm(st["a"], axis=1)
emit("(1) t=0 KURULUM DENGESI  N=%d" % n)
emit("    maks |a_SPH|  = %.6e m/s^2   (tam sifir mi: %s)"
     % (a_sph.max(), a_sph.max() == 0.0))
emit("    maks |P|      = %.6e Pa" % np.abs(st["P"]).max())
emit("    maks |S|      = %.6e Pa" % np.abs(st["S"]).max())
emit("    rho araligi   = [%.6f, %.6f]  (beklenen rho0/alpha0 = %.6f)"
     % (st["rho"].min(), st["rho"].max(), 2700.0 / 1.6))
emit("")

s_g = WarpSolid3D(x0, zer, pile.m, np.zeros(n), 14.0, mat, RefParams(cfl=0.25), **kw)
s_g._eval()
g_ref = s_g.g.numpy().astype(np.float64)
gn = np.linalg.norm(g_ref, axis=1)
emit("    maks |a_yercekimi| = %.6e m/s^2" % gn.max())
emit("    -> t=0'da TEK dengesiz kuvvet yercekimidir.")
emit("")

# ---------- (2) carpma suresince yercekimi ne kadar oynatir ----------
emit("(2) YERCEKIMI KAYMASI vs PARCACIK ARALIGI")
emit("    s = 0.5 |g| t^2 (ust sinir; gercekte basinc gradyani karsi koyar)")
emit("%10s %14s %14s %14s" % ("t_sim[s]", "kayma[m]", "kayma/aralik", "kayma/aralik_DART"))
for t_sim in (1.0, 10.0, 100.0, 1000.0):
    s_kay = 0.5 * gn.max() * t_sim**2
    emit("%10.1f %14.4e %14.4e %14.4e" % (t_sim, s_kay, s_kay / 7.0, s_kay / 1.0))
emit("")

# ---------- (3) kacis hizi ----------
m_tot = float(np.sum(pile.m))
r_eff = float((3.0 * pile.mesh_volume / (4.0 * np.pi)) ** (1.0 / 3.0))
v_kac = np.sqrt(2.0 * G * m_tot / r_eff)
emit("(3) KACIS HIZI")
emit("    test yigini : M=%.4e kg  R=%.1f m  v_kac=%.4e m/s" % (m_tot, r_eff, v_kac))
emit("    Dimorphos   : M=4.3e9 kg  R=82 m  v_kac=%.4e m/s"
     % np.sqrt(2.0 * G * 4.3e9 / 82.0))
emit("    -> ejekta icin yercekimi BELIRLEYICI (cm/s mertebesi), hedef")
emit("       govdesinin sok fazi dinamigi icin degil.")
emit("")

# ---------- (4) agac bayatlama, dogru normalizasyon ----------
emit("(4) AGAC BAYATLAMA HATASI  (norm: maks|g| = %.4e)" % gn.max())
emit("%6s %13s %13s %13s %13s" % ("K", "kayma[m]", "maks_dg/gmax", "ort_dg/gmax", "kayma/aralik"))
c_long = np.sqrt((4.0 / 3.0) * G_SHEAR / RHO)
dt = 0.25 * 14.0 / c_long
rng = np.random.default_rng(7)
yon = rng.normal(size=(n, 3))
yon /= np.linalg.norm(yon, axis=1)[:, None]
for K, v_tip in ((1, 0.05), (10, 0.05), (100, 0.05), (1000, 0.05),
                 (100, 5.0), (100, 500.0)):
    kayma = v_tip * K * dt
    x_yeni = np.ascontiguousarray(x0 + kayma * yon)
    s_t = WarpSolid3D(x_yeni, zer, pile.m, np.zeros(n), 14.0, mat, RefParams(cfl=0.25), **kw)
    s_t._eval()
    g_taze = s_t.g.numpy().astype(np.float64)
    s_b = WarpSolid3D(x0, zer, pile.m, np.zeros(n), 14.0, mat, RefParams(cfl=0.25), **kw)
    s_b._eval()
    s_b.x.assign(x_yeni)
    s_b._eval()                       # _x_version artmadi -> agac YENIDEN KURULMAZ
    d = np.linalg.norm(g_taze - s_b.g.numpy().astype(np.float64), axis=1)
    emit("%6d %13.4e %13.4e %13.4e %13.4e"
         % (K, kayma, d.max() / gn.max(), d.mean() / gn.max(), kayma / 7.0))
emit("")

# ---------- (5) settling penceresi ----------
emit("(5) SONUMLEMELI SETTLING PENCERESI (P3-VR-01)")
e_bind = binding_energy(m_tot, r_eff)
emit("    E_baglanma = %.6e J,  esik = 1e-3 * E_bag = %.6e J" % (e_bind, 1e-3 * e_bind))
for K in (1, 100):
    r = settle_pile(pile, mat, damping=0.02, max_steps=200, report_every=200,
                    gravity_rebuild_every=K)
    emit("    K=%4d: adim=%d  t=%.4e s  KE_son=%.4e J  KE/E_bag=%.4e  yakinsadi=%s"
         % (K, r.n_steps, r.t_end, r.ke_final, r.ke_final / e_bind, r.converged))
    emit("            rho=[%.4f,%.4f] alpha=[%.4f,%.4f]"
         % (r.diagnostics["rho_min"], r.diagnostics["rho_max"],
            r.diagnostics["alpha_min"], r.diagnostics["alpha_max"]))
