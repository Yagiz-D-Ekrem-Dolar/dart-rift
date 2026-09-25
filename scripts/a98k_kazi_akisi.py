#!/usr/bin/env python
"""A98K — kontrollü geç evre kazı akışı: yapay viskozite sonucu çözünürlüğe bağlıyor mu?

## Neden

A98 (`docs/COZUNURLUK-DENETIMI.md` §1) geç evrede Monaghan yapay viskozitesinin
(AV) `q ~ ρ α c h |∇v|` gerilmesinin kohezyonu (`Y₀ = 10 Pa`) çok aştığını ve
`h` ile doğrusal ölçeklendiğini gösterdi. Tam DART sahnesi (PROTOKOL-A98) saatler
sürüyor ve içinde başka mekanizmalar da var (temas oranı A100, yüzey diverjansı
A101, erken evre şoku). Bu betik **yalnız geç evreyi** kontrollü bir başlangıç
değer problemi olarak kurar; aynı fiziği farklı `h`'lerde koşar ve AV'nin
payını doğrudan ölçer.

## Problem (Maxwell Z-modeli kazı akışı)

- Yarı uzay bloğu `|x|, |y| ≤ L`, `−D ≤ z ≤ 0` (üst yüzey serbest, `z = 0`);
  merkezde `r < r₀` yarım küre boşluk (geçici krater).
- Malzeme: üretimin **geç evre** malzemesi — bazalt Tillotson, geçişte
  `A → 1e5 Pa`, `a = b = B = 0`; kayma modülü aynı oranda; `Y₀ = 10 Pa`,
  `μ_f = 0,6`; P-α `α₀ = 2700/1600`; matris çekmesi kırpık; A80 dayanım kesmesi,
  A83 yoğunluk tabanı; `akma_kipi = "ara"`. Yerçekimi kapalı (geç evrede
  `g ~ 3e-5 m/s²`: 30 s'de `Δv ~ 1e-3 m/s`, akış hızlarının `%1`'inden az).
- Başlangıç hızı (Maxwell 1977; Z = 3 sıkışmaz): `u_r = V₀ (r₀/r)^Z`,
  `u_θ = u_r (Z−2) sin θ / (1 + cos θ)` (θ aşağı düşeyden). Yüzeyde akış
  45° yukarı-dışa: madde kraterden fırlar.
- Gözlenebilir (β'nın benzeri): özgün yüzeyin **üstündeki** maddenin yukarı
  momentumu `P_up = Σ_{z>0, v_z>0} m v_z` ve hızlı kısmı
  `P_up(|v| > v_c)`. Akış kohezyon ve AV ile durdukça fırlama biter.

Parametreler geç evreye göre seçildi: Mach `V₀/c ≈ 0,05`, `r₀/h = 2 / 4 / 8`
(kaba merdivende krater yarıçapı / `h` bu aralıkta).

## Kullanım

    python scripts/a98k_kazi_akisi.py --s 1.0 --av 1 2 --t-end 30 \\
        --device cuda:0 --out sonuc.json

Fiziğe dokunmaz; yalnız okur ve koşar. Karar kuralları:
`docs/truba/PROTOKOL-A98K-KAZI-AKISI.md` (koşudan ÖNCE kilitli).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK / "src"))

from dartrift.cpu_reference.materials import (  # noqa: E402
    DamageParams,
    GravityParams,
    MaterialParams,
    PorosityParams,
    StrengthParams,
)
from dartrift.cpu_reference.sph_ref import RefParams  # noqa: E402

RHO0 = 2700.0          # bazalt Tillotson referans yogunlugu
YIGIN = 1600.0         # L1/UY yigin yogunlugu
ALFA0 = RHO0 / YIGIN   # P-alpha baslangic distansiyonu
Y0 = 10.0              # L1/UY kohezyonu [Pa]
MU_F = 0.6
A_GEC = 1.0e5          # ADR-0050 gec evre hacim modulu (UY/W2/A98 ile ayni)
DAYANIM_KESME_ETA = 0.5    # forward.DAYANIM_KESME_ETA ile ayni (A80)
YOGUNLUK_TABANI_ETA = 0.01  # forward.YOGUNLUK_TABANI_ETA ile ayni (A83)


def malzeme() -> MaterialParams:
    """Uretim malzemesi (faz44 `_malzeme`, `mu_f = 0,6`); Y0 parcacik basina."""
    return MaterialParams(
        eos="tillotson",
        strength=StrengthParams(enabled=True, Y0=Y0, mu_f=MU_F, YM=1.5e9,
                                shear_G=2.27e10, jaumann=True),
        porosity=PorosityParams(enabled=True, alpha0=ALFA0, Pe=1.0e6,
                                Ps=1.0e8, n_exp=2.0),
        gravity=GravityParams(enabled=False),
        damage=DamageParams(enabled=False),
        density_method="continuity")


def kafes(s: float, L: float, D: float, r0: float) -> np.ndarray:
    """Kubik kafes, hucre merkezleri; ust katman `z = -s/2`; `r < r0` bos.

    Merkezler `(i + 1/2) s`: butun cozunurluklerde ayni simetri (eksen
    uzerinde parcacik yok, `±s/2`'de).
    """
    nx = int(round(L / s))
    nz = int(round(D / s))
    g = (np.arange(-nx, nx) + 0.5) * s
    gz = -(np.arange(nz) + 0.5) * s
    x = np.stack(np.meshgrid(g, g, gz, indexing="ij"), -1).reshape(-1, 3)
    r = np.linalg.norm(x, axis=1)
    return np.ascontiguousarray(x[r >= r0])


def z_modeli(x: np.ndarray, *, V0: float, r0: float, Z: float) -> np.ndarray:
    """Maxwell Z-modeli hiz alani (merkez orijinde, θ asagi duseyden)."""
    r = np.linalg.norm(x, axis=1)
    cos_t = np.clip(-x[:, 2] / r, -1.0, 1.0)
    sin_t = np.sqrt(np.maximum(0.0, 1.0 - cos_t * cos_t))
    rho_h = np.linalg.norm(x[:, :2], axis=1)
    rho_hat = np.zeros_like(x)
    ok = rho_h > 1e-12 * r
    rho_hat[ok, :2] = x[ok, :2] / rho_h[ok, None]
    r_hat = x / r[:, None]
    th_hat = cos_t[:, None] * rho_hat
    th_hat[:, 2] += sin_t
    u_r = V0 * (r0 / r) ** Z
    u_t = u_r * (Z - 2.0) * sin_t / (1.0 + cos_t)
    return np.ascontiguousarray(u_r[:, None] * r_hat + u_t[:, None] * th_hat)


def gozlem(x, v, m, *, V0: float) -> dict:
    """Yuzeyin ustundeki maddenin yukari momentumu (beta'nin benzeri)."""
    ust = x[:, 2] > 0.0
    yuk = ust & (v[:, 2] > 0.0)
    hiz = np.linalg.norm(v, axis=1)
    out = {
        "P_up": float(np.sum(m[yuk] * v[yuk, 2])),
        "M_up": float(np.sum(m[yuk])),
        "M_ust": float(np.sum(m[ust])),
    }
    for k in (0.1, 0.2):
        sec = yuk & (hiz > k * V0)
        out[f"P_up_v{k:g}"] = float(np.sum(m[sec] * v[sec, 2]))
        out[f"M_up_v{k:g}"] = float(np.sum(m[sec]))
    return out


def saglik(x: np.ndarray, s: float) -> dict:
    """Parcacik ic ice gecme gostergesi: en yakin komsu mesafesi / s."""
    from scipy.spatial import cKDTree

    d, _ = cKDTree(x).query(x, k=2)
    nn = d[:, 1] / s
    return {"nn_min": float(nn.min()), "nn_p01": float(np.percentile(nn, 1)),
            "nn_medyan": float(np.median(nn)),
            "kesir_nn_lt_0p5": float(np.mean(nn < 0.5)),
            "kesir_nn_lt_0p3": float(np.mean(nn < 0.3))}


def _surum() -> str:
    try:
        return subprocess.check_output(["git", "-C", str(KOK), "rev-parse", "HEAD"],
                                       text=True).strip()
    except Exception:  # noqa: BLE001 -- surum kaydi kapi degil
        return "bilinmiyor"


def kos(*, s: float, alpha_av: float | None, beta_av: float | None,
        t_end: float, r0: float, V0: float, Z: float, L_kat: float,
        D_kat: float, device: str, komsu: str, her: int, n_ornek: int,
        azami_adim: int, bildir: int = 0, sureklilik_trL: bool = False) -> dict:
    """Bir kolu kos; `alpha_av = None` -> AV varsayilan (1, 2), degismez.

    `sureklilik_trL` (A101): gecisle birlikte yogunluk `-rho tr(L)` ile.
    """
    from dartrift.warp_core.solver_solid import WarpSolid3D

    L, D = L_kat * r0, D_kat * r0
    x = kafes(s, L, D, r0)
    v = z_modeli(x, V0=V0, r0=r0, Z=Z)
    n = len(x)
    m = np.full(n, YIGIN * s ** 3)
    sol = WarpSolid3D(
        x, v, m, np.zeros(n), 2.0 * s, malzeme(),
        RefParams(cfl=0.25, alpha_av=1.0, beta_av=2.0, akma_kipi="ara"),
        alpha0=np.full(n, ALFA0), Y0=np.full(n, Y0), device=device,
        check_every=10 ** 9, cekme_kirp_maske=np.ones(n, dtype=bool),
        komsu_arama=komsu, dayanim_kesme={"eta_kes": DAYANIM_KESME_ETA},
        yogunluk_tabani=YOGUNLUK_TABANI_ETA)
    av_kw = {}
    if alpha_av is not None:
        av_kw = {"alpha_av": float(alpha_av), "beta_av": float(beta_av)}
    gec = sol.gec_evreye_gec(A_GEC, t=0.0, duzeltilmis_sureklilik=bool(
        sureklilik_trL), **av_kw)
    sol.hazirla()
    P0 = m @ v
    e0 = sol.budgets()
    t_ornek = np.linspace(0.0, t_end, n_ornek + 1)
    satirlar = []
    E_av = 0.0
    son_av = None

    def _pl() -> float:
        pl = float(sol.plastic_u_total)
        if getattr(sol, "_akma_ara", False):
            pl += float(np.sum(sol.m.numpy() * sol.plastic_cum_ara.numpy()))
        return pl

    def _ornek(t: float) -> None:
        xs = sol.x.numpy().astype(np.float64)
        vs = sol.v.numpy().astype(np.float64)
        g = gozlem(xs, vs, m, V0=V0)
        b = sol.budgets()
        satirlar.append({"t": float(t), **g, "e_kin": float(b["e_kin"]),
                         "e_int": float(b["e_int"]), "E_av": float(E_av),
                         "W_pl": _pl()})

    _ornek(0.0)
    k = 1
    t = 0.0
    dt_list = []
    t0 = time.time()
    for adim in range(1, azami_adim + 1):
        dt = sol.compute_dt()
        if t + dt > t_end:
            dt = t_end - t
        sol.step(dt)
        t += dt
        dt_list.append(dt)
        if adim % her == 0 or t >= t_end * (1.0 - 1e-12):
            d = sol.av_tanisi()
            if son_av is not None:
                E_av += 0.5 * (son_av[1] + d["P_av"]) * (t - son_av[0])
            son_av = (t, d["P_av"])
        while k < len(t_ornek) and t >= t_ornek[k] * (1.0 - 1e-12):
            _ornek(t_ornek[k])
            k += 1
        if bildir and adim % bildir == 0:
            print(f"    adim {adim:>7}  t = {t:8.3f}  dt = {dt:.3e}  "
                  f"P_up = {satirlar[-1]['P_up']:.4e}", flush=True)
        if t >= t_end * (1.0 - 1e-12):
            break
    else:
        raise RuntimeError(f"ADIM SINIRI: t = {t} < {t_end}")
    duvar = time.time() - t0
    xs = sol.x.numpy().astype(np.float64)
    vs = sol.v.numpy().astype(np.float64)
    son = satirlar[-1]
    e1 = sol.budgets()
    P1 = m @ vs
    dt_a = np.asarray(dt_list)
    return {
        "s": float(s), "h": 2.0 * float(s), "n": int(n),
        "av": list(gec["av_sonra"]), "sureklilik": gec["sureklilik"],
        "t_end": float(t_end),
        "r0": float(r0), "V0": float(V0), "Z": float(Z), "L": L, "D": D,
        "r0_bolu_h": float(r0 / (2.0 * s)),
        "adim": int(adim), "duvar_s": float(duvar),
        "dt_min": float(dt_a.min()), "dt_medyan": float(np.median(dt_a)),
        "dt_max": float(dt_a.max()),
        "P_up": son["P_up"], "P_up_v0.1": son["P_up_v0.1"],
        "P_up_v0.2": son["P_up_v0.2"], "M_up": son["M_up"],
        "e_kin_bas": float(e0["e_kin"]), "e_kin_son": float(e1["e_kin"]),
        "E_av": float(E_av), "W_pl": _pl(),
        "av_payi": (float(E_av / (E_av + _pl())) if (E_av + _pl()) > 0 else
                    float("nan")),
        "enerji_bagil_sapma": float((e1["e_tot"] - e0["e_tot"])
                                    / max(abs(e0["e_tot"]), 1e-300)),
        "momentum_bagil_sapma": float(np.linalg.norm(P1 - P0)
                                      / max(float(np.sum(m * np.linalg.norm(
                                          v, axis=1))), 1e-300)),
        "sonlu": bool(np.all(np.isfinite(xs)) and np.all(np.isfinite(vs))),
        "saglik": saglik(xs, s),
        "satirlar": satirlar,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--s", type=float, required=True, help="parcacik araligi [m]")
    ap.add_argument("--av", type=float, nargs=2, default=None,
                    metavar=("ALFA", "BETA"),
                    help="gecisten sonraki AV; verilmezse varsayilan (1, 2)")
    ap.add_argument("--t-end", type=float, default=30.0)
    ap.add_argument("--r0", type=float, default=4.0)
    ap.add_argument("--V0", type=float, default=0.5)
    ap.add_argument("--Z", type=float, default=3.0)
    ap.add_argument("--L-kat", type=float, default=3.0)
    ap.add_argument("--D-kat", type=float, default=2.5)
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--komsu", choices=("bvh", "hash"), default="bvh")
    ap.add_argument("--her", type=int, default=10, help="AV tanisi her N adimda")
    ap.add_argument("--n-ornek", type=int, default=30)
    ap.add_argument("--azami-adim", type=int, default=2_000_000)
    ap.add_argument("--bildir", type=int, default=0)
    ap.add_argument("--sureklilik-trL", action="store_true",
                    help="A101: yogunluk -rho tr(L) ile (duzeltilmis sureklilik)")
    ap.add_argument("--etiket", default="")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    if a.s <= 0 or a.t_end <= 0 or a.r0 <= 0 or a.V0 <= 0:
        ap.error("s, t_end, r0, V0 pozitif olmali")
    if a.av is not None and not all(np.isfinite(a.av)) or (
            a.av is not None and min(a.av) < 0):
        ap.error("--av sonlu ve >= 0 olmali")
    out = Path(a.out)
    if out.exists():
        ap.error(f"{out} zaten var (uzerine yazilmaz)")
    al, be = (None, None) if a.av is None else (a.av[0], a.av[1])
    print(f"A98K  etiket={a.etiket!r}  s={a.s}  av={a.av or 'varsayilan'}  "
          f"sureklilik={'trL' if a.sureklilik_trL else 'sph'}  "
          f"t_end={a.t_end}  device={a.device}  kod={_surum()}", flush=True)
    r = kos(s=a.s, alpha_av=al, beta_av=be, t_end=a.t_end, r0=a.r0, V0=a.V0,
            Z=a.Z, L_kat=a.L_kat, D_kat=a.D_kat, device=a.device,
            komsu=a.komsu, her=a.her, n_ornek=a.n_ornek,
            azami_adim=a.azami_adim, bildir=a.bildir,
            sureklilik_trL=a.sureklilik_trL)
    r["etiket"] = a.etiket
    r["kod"] = _surum()
    r["device"] = a.device
    tmp = out.with_suffix(out.suffix + ".tmp")
    tmp.write_text(json.dumps(r, indent=1))
    tmp.replace(out)
    print(f"  n={r['n']}  adim={r['adim']}  duvar={r['duvar_s']:.1f} s  "
          f"P_up={r['P_up']:.5e}  E_av={r['E_av']:.4e}  W_pl={r['W_pl']:.4e}  "
          f"av_payi={r['av_payi']:.3f}  nn_min={r['saglik']['nn_min']:.3f}",
          flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
