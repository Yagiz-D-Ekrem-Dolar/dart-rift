"""KRATER CIKARICISI KUSURU -- en kucuk yeniden uretim.

Bilinen bir krater yerlestiriliyor ve `crater_profile` `0.0` donduruyor.
"""
import sys
import numpy as np
sys.path.insert(0, "src")
from dartrift.observables.crater_shape import crater_profile

rng = np.random.default_rng(7)
R, s = 82.0, 3.5
n = int(4 * np.pi * R * R / (s * s))
u = rng.uniform(-1, 1, n); ph = rng.uniform(0, 2 * np.pi, n)
st = np.sqrt(1 - u * u)
yon = np.column_stack([st * np.cos(ph), st * np.sin(ph), u])
x0 = R * yon                                  # bozulmamis kure

print(f"kure: {n} parcacik, R = {R} m, aralik {s} m\n")
print(f"{'D (m)':>7} {'derinlik (m)':>13} {'OLCULEN derinlik':>17} {'OLCULEN cap':>12}")
for e in (np.array([0., 0, 1]), np.array([1., 0, 0])):
    for D, d_kr in ((20., 4.), (40., 8.), (60., 12.), (80., 16.)):
        ya = np.arcsin(min(D / 2 / R, 1.0))
        ca = yon @ e
        ic = ca > np.cos(ya)
        aci = np.arccos(np.clip(ca, -1, 1))
        r = np.full(n, R)
        r[ic] = R - d_kr * (1.0 - (aci[ic] / ya) ** 2)
        try:
            kr = crater_profile(r[:, None] * yon, center=np.zeros(3),
                                impact_direction=e, reference_radius=R,
                                x_reference=x0)
            print(f"{D:7.1f} {d_kr:13.1f} {kr.depth:17.4f} {kr.diameter:12.3f}")
        except ValueError as ex:
            print(f"{D:7.1f} {d_kr:13.1f}   HATA: {str(ex)[:50]}")
    print()
print("BEKLENEN: olculen derinlik ~ gercek derinlik.")
print("GORULEN : hepsi 0.0000 -- cikarici krateri GORMUYOR.")
