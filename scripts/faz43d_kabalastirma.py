"""ADR-0043 gereksinim #2: **kabalaştırmanın korunum hatası.**

`tests/test_coarsen.py` operatörün *sentetik* veride korunumlu
olduğunu gösteriyor. Bu betik onu **gerçek sahnede, gerçek bir
aşama-1 durumunda** ölçüyor — ikisi aynı şey değil:

| sentetik | gerçek |
|---|---|
| rastgele hızlar, yığın akış yok | şok cephesi + yığın akış |
| `ε` civarı iç enerji | Tillotson EOS'tan gelen büyük `e` |
| uniform kütle | `α₀`'a bağlı, kaya blokları var |

## Asıl soru korunum **değil**

Korunum yapı gereği tam (bölüntü + kütle ağırlığı). Ölçülmesi gereken
iki şey başka:

1. **`ısıya dönen kinetik oran`** — aktarım kaba parçacığı ne kadar
   ısıtıyor? Büyükse aşama-2 yapay olarak sıcak başlar.
2. **Açısal momentum kaybı** — grup dönüşü siliniyor; gerçek sahnede
   ne kadar?

> Korunum hatası zaten `~1e-16` çıkacak. Onu *"başarı"* diye
> raporlamak yanıltıcı olurdu; asıl bulgu 1 ve 2.

## `ısıya dönen oran` aslında **`t₁` için daha keskin bir ölçüt**

Ön uçuşta (`λ=6`, `t₁=1e-6 s`) `%99,9` çıktı. Sebebi açık: o anda mermi
hâlâ hedefe göre `6 km/s` gidiyor, yani hız alanı site ölçeğinde
**çözülemez**. Ortalamak her şeyi ısıya çevirir.

> `faz43c`'nin `u` ölçütü *"momentum alışverişi bitti mi"* diye
> soruyor; bu ise doğrudan *"bu durum kabalaştırılabilir mi"* diye
> soruyor. İkincisi `t₁` kararı için daha yakın bir soru. `t₁` ikisine
> **birden** bakılarak seçilmeli.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
for _akis in (sys.stdout, sys.stderr):
    try:
        _akis.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

from dartrift.cpu_reference.sph_ref import RefParams  # noqa: E402
from dartrift.setup.coarsen import coarsen_to_sites  # noqa: E402
from dartrift.setup.refine import refine_scene_local  # noqa: E402
from dartrift.setup.scene import _build_mesh, build_scene  # noqa: E402

sys.path.insert(0, str(REPO / "scripts"))
from faz44_dart_yakinsama import SAHNE, _malzeme  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--lam", type=float, default=19.0)
    ap.add_argument("--r-ince", type=float, default=3.0)
    ap.add_argument("--t1", type=float, nargs="+",
                    # 4.767e-3 = faz43c'nin OLCTUGU t1 (ADR tahmini 1e-3'tu).
                    default=[1.0e-4, 1.0e-3, 4.767e-3, 1.0e-2])
    # ASAMA-2'nin kendi parametreleri: hedef siteler ORADAN geliyor.
    ap.add_argument("--lam2", type=float, default=2.0)
    ap.add_argument("--r-ince2", type=float, default=25.0)
    ap.add_argument("--steps", type=int, default=200000)
    ap.add_argument("--out", default=str(REPO.parent / "faz43d_sonuc.json"))
    a = ap.parse_args()

    from dartrift.warp_core.solver_solid import WarpSolid3D

    print("=" * 78, flush=True)
    print("ADR-0043 #2 — KABALASTIRMANIN KORUNUM HATASI (gercek sahne)",
          flush=True)
    print("=" * 78, flush=True)

    kaba = build_scene(spacing=7.0, device="cpu", **SAHNE)
    mesh = _build_mesh("icosphere", radius=SAHNE["radius"], subdiv=4)
    rs = refine_scene_local(kaba, mesh, r_ince=a.r_ince, lam=a.lam)
    ince = np.asarray(rs.is_fine, dtype=bool)

    # HEDEF SITELER: asama-2'nin KENDI INCE kafesi -- kaba kafes DEGIL.
    #
    # Ilk surumde `diagnostics["cikarilan_kaba_x"]`, yani cikarilan 7 m'lik
    # KABA parcaciklar hedef aliniyordu. YANLIS: asama-2 `lam=2` kullaniyor,
    # yani o bolgede araligi 3,5 m. Aktarim asama-2'nin GERCEKTEN sahip
    # olacagi kafese yapilmali; yoksa olculen sey kurulacak semanin hatasi
    # degildir. On ucus yakaladi: 7 m kafeste r_ic=6 m icinde yalnizca
    # 2 site vardi.
    a2 = refine_scene_local(kaba, mesh, r_ince=a.r_ince2, lam=a.lam2)
    hedef2 = np.asarray(a2.is_fine, bool) & ~np.asarray(a2.is_impactor, bool)
    mp = np.asarray(kaba.impact_point, dtype=np.float64)
    d2 = np.linalg.norm(a2.x - mp[None, :], axis=1)
    siteler = a2.x[hedef2 & (d2 < a.r_ince)]
    s2 = float(a2.spacing_fine)

    print(f"\nASAMA-1: N={rs.n}, ince={int(ince.sum())} (mermi dahil), "
          f"s_ince={rs.spacing_fine:.4f} m", flush=True)
    print(f"ASAMA-2: lam={a.lam2}, s_ince={s2:.4f} m -> "
          f"r_ic={a.r_ince} m icinde {len(siteler)} SITE", flush=True)
    if len(siteler) == 0:
        print("  HEDEF SITE YOK — kabalastirma olculemez", flush=True)
        return 1
    print(f"  sikistirma = {int(ince.sum()) / len(siteler):.0f} "
          f"ince parcacik / site", flush=True)

    sol = WarpSolid3D(
        np.ascontiguousarray(rs.x), np.ascontiguousarray(rs.v),
        np.ascontiguousarray(rs.m), np.zeros(rs.n), rs.h, _malzeme(),
        RefParams(cfl=0.25), alpha0=np.ascontiguousarray(rs.alpha0),
        Y0=np.ascontiguousarray(rs.Y0), device=a.device, check_every=10 ** 9)

    kayitlar, t_sim, hedefler = [], 0.0, sorted(float(t) for t in a.t1)
    print(f"\n{'t1':>10} {'kutle':>10} {'momentum':>10} {'enerji':>10} "
          f"{'ACISAL':>10} {'ISIYA%':>8} {'d_max/s':>8}", flush=True)
    print("-" * 78, flush=True)

    for hedef in hedefler:
        while t_sim < hedef * (1.0 - 1e-12):
            dt = sol.compute_dt()
            if t_sim + dt > hedef:
                dt = hedef - t_sim
            sol.step(dt)
            t_sim += dt
        st = sol.state_numpy()
        if not np.all(np.isfinite(st["v"])):
            print(f"  t1={hedef:.1e} PATLADI — atlandi", flush=True)
            continue
        # `u` = OZGUL ic enerji (solver_solid.state_numpy sozlesmesi).
        # Anahtar adini varsaymak yerine dogrulaniyor: sessizce sifir
        # almak "enerji korundu" yanilsamasi uretirdi.
        if "u" not in st:
            raise KeyError("state_numpy 'u' (ozgul ic enerji) dondurmedi — "
                           f"anahtarlar: {sorted(st)}")
        e = np.asarray(st["u"], np.float64)
        out = coarsen_to_sites(st["x"][ince], st["v"][ince], rs.m[ince],
                               e[ince], siteler,
                               alpha0=rs.alpha0[ince], Y0=rs.Y0[ince],
                               is_boulder=rs.is_boulder[ince])
        k = out["korunum"]
        k["t1"] = hedef
        k["ic_enerji_cozucuden"] = True
        kayitlar.append(k)
        print(f"{hedef:10.1e} {k['kutle_hata']:10.2e} "
              f"{k['momentum_hata']:10.2e} {k['enerji_hata']:10.2e} "
              f"{k['acisal_momentum_hata']:10.2e} "
              f"{100 * k['ice_donen_kinetik_oran']:8.3f} "
              f"{k['atama_mesafe_max'] / s2:8.2f}", flush=True)

    print("-" * 78, flush=True)
    if kayitlar:
        en_kotu = max(kayitlar, key=lambda z: max(
            z["kutle_hata"], z["momentum_hata"], z["enerji_hata"]))
        gecti = (en_kotu["kutle_hata"] < 1e-12
                 and en_kotu["momentum_hata"] < 1e-12
                 and en_kotu["enerji_hata"] < 1e-12)
        print(f"\nKORUNUM (uc olcut de < 1e-12): "
              f"{'GECTI' if gecti else 'DUSTU'}", flush=True)
        print(f"  giren ince parcacik  = {kayitlar[-1]['n_giren']}", flush=True)
        print(f"  cikan kaba parcacik  = {kayitlar[-1]['n_cikan']}", flush=True)
        print(f"  bos kalan site       = {kayitlar[-1]['n_bos_site']}",
              flush=True)
        print("\nASIL BULGULAR (korunum degil):", flush=True)
        print(f"  acisal momentum kaybi = "
              f"{100 * kayitlar[-1]['acisal_momentum_kayip_olcekli']:.2f}%  "
              f"(ULASILABILIR olcege gore; ham oran L0~0 oldugu icin "
              f"anlamsiz)", flush=True)
        print(f"  atama mesafesi (max)  = "
              f"{kayitlar[-1]['atama_mesafe_max']:.2f} m = "
              f"{kayitlar[-1]['atama_mesafe_max'] / s2:.2f} "
              f"s_asama2  -- 1'i cok asarsa madde ISINLANIYOR", flush=True)
        print(f"  isiya donen kinetik   = "
              f"{100 * kayitlar[-1]['ice_donen_kinetik_oran']:.3f}%  "
              f"-- asama-2 bu kadar yapay sicak baslar", flush=True)
    else:
        print("\nHICBIR t1 OLCULEMEDI — kayit bulunamadi", flush=True)

    Path(a.out).write_text(json.dumps(
        {"lam": a.lam, "r_ince": a.r_ince, "N": rs.n,
         "lam2": a.lam2, "r_ince2": a.r_ince2, "s_asama2": s2,
         "n_site": int(len(siteler)),
         "sikistirma": int(ince.sum()) / max(len(siteler), 1),
         "kayitlar": kayitlar}, indent=2,
        default=float))
    print(f"\nyazildi: {a.out}", flush=True)
    return 0 if kayitlar else 1


if __name__ == "__main__":
    raise SystemExit(main())
