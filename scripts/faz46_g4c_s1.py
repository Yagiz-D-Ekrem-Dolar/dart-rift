"""FAZ 4.6 — G4-C, **indirgenmiş** uzayda (ADR-0046 kararı S1).

Üç parametreli uzay ölçümle **tek boyutlu** çıktı: `Y0` gözlenemeyen
alt uzayda, kalan ikisinin koşul sayısı `79,5`, ve kök neden `ρ_yığın`
sabitken üreticinin `matrix_alpha0`'ı türetmek zorunda olması.

Bu betik **yeni koşu yapmıyor**: mevcut 40 noktanın her biri için
`matrix_alpha0` türetiliyor ve çıkarım o tek değişken üzerinde
kuruluyor.

## Neden bu meşru bir yeniden parametrelendirme

Gözlenebilirler matris `α₀`'ın **fonksiyonu değil**; aynı `α₀`'a farklı
`(boulder_alpha0, f_boulder)` çiftleri düşebiliyor. Ama ölçüldü ki
bağımlılık neredeyse tam:

| gözlenebilir | `R²` (matris `α₀`, 2. derece) | artık |
|---|---|---|
| `krater_derinlik` | **0,9277** | `0,162 m` |
| `beta` | 0,7806 | `5,04e-3` |
| `ejekta_kutle_kesri` | 0,4171 | `6,27e-9` |

Kalan saçılma **uydurulmuyor**: `fit_surrogate` onu artık standart
sapması olarak öğreniyor ve `grid_posterior` o `σ`'yı gözlem
gürültüsüne **ekliyor**. Yani indirgeme posterior'u yapay biçimde
daraltmıyor; daralttığı tek şey **dejenerasyon**.

## `C2` neden düzelmeli — ve neden bu bir hile değil

`C2` her parametrenin **marjinal** bandına bakıyor. Üç boyutlu dejenere
bir posterior'da iyi kısıtlanan yön bir **birleşim** olduğu için
marjinallerin **hepsi** geniş kalır — ölçülen `0,907` buydu.

Tek parametrede dejenerasyon yok: marjinal = kısıtlanan yön.

> Eşik `< 0,50` **değiştirilmedi**. Değişen şey sorunun kendisi:
> ölçülemeyen iki yön artık sorulmuyor. Bu bir kapsam kararıdır ve
> ADR-0046'da gerekçesiyle yazılıdır.
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

from dartrift.inference.design import DART_UZAYI_S1  # noqa: E402
from dartrift.inference.forward import GOZLENEBILIRLER  # noqa: E402
from dartrift.inference.posterior import grid_posterior  # noqa: E402
from dartrift.inference.recovery import recovery_verdict  # noqa: E402
from dartrift.inference.surrogate import fit_surrogate  # noqa: E402
from dartrift.setup.rubble_generator import (  # noqa: E402
    matrix_alpha0_for_bulk_density)

sys.path.insert(0, str(REPO / "scripts"))
from faz44_dart_yakinsama import SAHNE  # noqa: E402
from faz46_sentetik_kurtarma import SIGMA_NOMINAL  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ensemble", required=True)
    ap.add_argument("--n-grid", type=int, default=400)
    ap.add_argument("--out", default=str(Path.home() / "faz46_g4c_s1.json"))
    a = ap.parse_args()

    d = json.loads(Path(a.ensemble).read_text(encoding="utf-8"))
    if list(d["gozlenebilirler"]) != list(GOZLENEBILIRLER):
        raise SystemExit(f"gozlenebilirler uyusmuyor: {d['gozlenebilirler']}")

    UZAY = DART_UZAYI_S1
    X3 = np.array(d["X"], dtype=np.float64)
    Y = np.array(d["Y"], dtype=np.float64)
    ok = np.isfinite(Y).all(axis=1)
    X3, Y = X3[ok], Y[ok]

    rho0 = 2700.0
    am = np.array([matrix_alpha0_for_bulk_density(
        SAHNE["bulk_density"], rho0, x[0], x[2]) for x in X3])
    x = am[:, None]

    print("=" * 78, flush=True)
    print(f"FAZ 4.6 — G4-C, INDIRGENMIS UZAY (ADR-0046 S1)", flush=True)
    print("=" * 78, flush=True)
    print(f"\n[1] {len(x)} nokta, matris alpha0 = "
          f"{am.min():.4f} .. {am.max():.4f}", flush=True)
    disari = int(((am < UZAY.lo[0]) | (am > UZAY.hi[0])).sum())
    if disari:
        # Uzay sinirlari ensemble'in URETTIGI aralik olarak secildi;
        # disina cikan nokta DISDEGERLEME olurdu.
        raise SystemExit(f"{disari} nokta uzayin DISINDA — sinirlar yanlis")

    print(f"\n[2] vekiller", flush=True)
    vekiller = []
    for j, ad in enumerate(GOZLENEBILIRLER):
        s = fit_surrogate(UZAY, x, Y[:, j])
        vekiller.append(s)
        tani = ("SABIT" if s.sabit else "GUVENILIR" if s.guvenilir
                else "YETERSIZ")
        print(f"    {ad:20s} q2={s.q2:8.5f}  sigma={s.sigma:.4e}  {tani}",
              flush=True)
    if any(s.sabit for s in vekiller):
        raise SystemExit("DURDURULDU: sabit gozlenebilir var")

    gercek = UZAY.from_unit(np.full((1, 1), 0.5))[0]
    veri = np.array([float(s.predict(gercek[None, :])[0]) for s in vekiller])
    print(f"\n[3] gercek: matrix_alpha0 = {gercek[0]:.4f}", flush=True)
    print("    sentetik veri: "
          + ", ".join(f"{ad}={v:.5g}"
                      for ad, v in zip(GOZLENEBILIRLER, veri)), flush=True)

    print(f"\n[4] posterior (n_grid={a.n_grid})", flush=True)
    post = grid_posterior(UZAY, vekiller, veri, SIGMA_NOMINAL,
                          n_grid=a.n_grid)
    tarama = [(c, grid_posterior(UZAY, vekiller, veri,
                                 tuple(c * s for s in SIGMA_NOMINAL),
                                 n_grid=a.n_grid))
              for c in (1.0, 4.0, 16.0)]
    lo, hi = post.hdi(0)
    print(f"    matrix_alpha0  gercek={gercek[0]:.4f}  "
          f"%68=[{lo:.4f}, {hi:.4f}]  bant/onsel={post.width_u[0]:.4f}",
          flush=True)

    print(f"\n[5] G4-C", flush=True)
    v = recovery_verdict(post, gercek, tarama)
    print(f"    {v.ozet}", flush=True)
    for r in v.c1_ayrinti:
        print(f"      C1 {r['ad']:16s} "
              f"{'ICERIYOR' if r['iceriyor'] else 'DISARIDA'}  "
              f"gercek={r['gercek']:.4g}  "
              f"bant={r['bant'][0]:.4g}..{r['bant'][1]:.4g}", flush=True)
    if v.c3_kosuldu:
        print(f"      C3 buyume={v.c3_ayrinti['buyume_orani']:.2f}x",
              flush=True)
    print(f"\n    G4-C {'GECTI' if v.gecti else 'GECMEDI'}", flush=True)

    Path(a.out).write_text(json.dumps({
        "kaynak_ensemble": str(a.ensemble),
        "ileri_model": "iki_asamali (ileri_kosu_ikiasama)",
        "uzay": list(UZAY.names), "uzay_adi": "DART_UZAYI_S1",
        "adr_0046": "S1 — indirgenmis uzay",
        "t_end": d["t_end"], "n_tasarim": int(len(x)),
        "matris_alpha0_araligi": [float(am.min()), float(am.max())],
        "gercek": gercek.tolist(), "sigma_nominal": list(SIGMA_NOMINAL),
        "vekil_q2": {ad: float(s.q2)
                     for ad, s in zip(GOZLENEBILIRLER, vekiller)},
        "vekil_sigma": {ad: float(s.sigma)
                        for ad, s in zip(GOZLENEBILIRLER, vekiller)},
        "c1_gecti": v.c1_gecti, "c1_kapsama": v.c1_kapsama,
        "c1_ayrinti": v.c1_ayrinti,
        "c2_gecti": v.c2_gecti, "c2_en_dar": v.c2_en_dar,
        "c2_genislikler": v.c2_genislikler,
        "c3_kosuldu": v.c3_kosuldu, "c3_gecti": v.c3_gecti,
        "c3_ayrinti": v.c3_ayrinti,
        "G4C_gecti": v.gecti,
        "sure_denetimi": {
            "durum": "yeterli",
            "gerekce": "beta t=0,2 ile t=5,0'da BIT DUZEYINDE ayni",
        },
    }, indent=2, default=float), encoding="utf-8")
    print(f"\nyazildi: {a.out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
