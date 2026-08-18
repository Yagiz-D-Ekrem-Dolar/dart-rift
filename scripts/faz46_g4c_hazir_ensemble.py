"""FAZ 4.6 — G4-C, **iki aşamalı** ileri modelin ensemble'ıyla.

`faz46_sentetik_kurtarma.py` kendi **tek aşamalı** ileri modelini
kullanıyor (`λ = 2`, `A1 = 0,215`). KAYIT-045 ölçtü ki o **başka bir
problemi** çözüyor: `n_ejekta = 803`, yani merminin **tamamı** sekiyor.
Çözülmüş mermide `28`. Aradaki fark `%12` değil **rejim değişikliği**.

Bu betik ileri geçişi **yeniden koşturmuyor**: `faz412` TRUBA'da
`ileri_kosu_ikiasama` ile 40 noktayı koştu (`0/40` düşen) ve `X, Y`
matrisini yazdı. Burada yalnızca **çıkarım** yapılıyor — vekil, posterior,
G4-C yargısı — ve çıktı `g4_gate`'in okuduğu anahtarlarla yazılıyor.

## `t_end = 0,2 s` neden yeterli

`β` iki bağımsız koşuda `t = 0,2` ile `t = 5,0`'da **bit düzeyinde
aynı** çıktı (`1.4112162721355217`). Uzun koşunun `β` için getirdiği
bilgi sıfır.

## Beklenen sonuç ve neden **saklanmıyor**

FAZ 4.11/4.12 ölçtü ki `Y0` gözlenemeyen alt uzayda (boş uzay yönünün
en büyük bileşeni, `0,81`) ve `t = 20 s`'ye kadar bile derinlikte
`< 0,1 m` iz bırakıyor — ölçülen gürültü tabanının (`0,25 m`) altında.

> Yani **C1'in düşmesi bekleniyor**. Bu bir başarısızlık değil,
> ADR-0040'ın istediği türden bir düşüş: *"bir kriter düşebilmelidir."*
> Kurtarılamayanı kurtarılmış göstermek için eşik gevşetmek asıl kusur
> olurdu.
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

from dartrift.inference.design import DART_UZAYI_S3  # noqa: E402
from dartrift.inference.forward import GOZLENEBILIRLER  # noqa: E402
from dartrift.inference.posterior import grid_posterior  # noqa: E402
from dartrift.inference.recovery import recovery_verdict  # noqa: E402
from dartrift.inference.surrogate import fit_surrogate  # noqa: E402

sys.path.insert(0, str(REPO / "scripts"))
from faz46_sentetik_kurtarma import SIGMA_NOMINAL  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ensemble", required=True,
                    help="faz412 ciktisi (X, Y iceren JSON)")
    ap.add_argument("--n-grid", type=int, default=48)
    ap.add_argument("--out", default=str(Path.home() / "faz46_g4c.json"))
    a = ap.parse_args()

    d = json.loads(Path(a.ensemble).read_text(encoding="utf-8"))
    UZAY = DART_UZAYI_S3
    if list(d["uzay"]) != list(UZAY.names):
        raise SystemExit(f"uzay uyusmuyor: {d['uzay']} vs {UZAY.names}")
    if list(d["gozlenebilirler"]) != list(GOZLENEBILIRLER):
        raise SystemExit(
            f"gozlenebilirler uyusmuyor: {d['gozlenebilirler']} vs "
            f"{GOZLENEBILIRLER}. Ensemble BASKA bir vektorle kosulmus; "
            f"karistirmak sessizce yanlis posterior verirdi.")

    x = np.array(d["X"], dtype=np.float64)
    Y = np.array(d["Y"], dtype=np.float64)
    ok = np.isfinite(Y).all(axis=1)
    print("=" * 78, flush=True)
    print(f"FAZ 4.6 — G4-C (IKI ASAMALI ensemble, t_end={d['t_end']})",
          flush=True)
    print("=" * 78, flush=True)
    print(f"\n[1] tasarim: {len(x)} nokta, {int((~ok).sum())} DUSTU, "
          f"{int(ok.sum())} kullanilabilir", flush=True)
    x, Y = x[ok], Y[ok]

    print("\n[2] vekiller", flush=True)
    vekiller = []
    for j, ad in enumerate(GOZLENEBILIRLER):
        s = fit_surrogate(UZAY, x, Y[:, j])
        vekiller.append(s)
        tani = ("SABIT -- ILERI MODEL BOZUK OLABILIR" if s.sabit
                else "GUVENILIR" if s.guvenilir else "YETERSIZ")
        print(f"    {ad:20s} q2={s.q2:8.5f}  rmse_loo={s.rmse_loo:.4e}  "
              f"sigma={s.sigma:.4e}  {tani}", flush=True)

    sabitler = [ad for ad, s in zip(GOZLENEBILIRLER, vekiller, strict=False) if s.sabit]
    if sabitler:
        raise SystemExit(
            f"DURDURULDU: {sabitler} HIC DEGISMIYOR. Cikarim bosuna olurdu.")
    yetersiz = [ad for ad, s in zip(GOZLENEBILIRLER, vekiller, strict=False)
                if not s.guvenilir]
    if yetersiz:
        print(f"    UYARI: {yetersiz} YETERSIZ (q2 <= 0.5). Posterior yine "
              f"hesaplanacak ama yargi guvenilmez.", flush=True)

    # Gercek deger UZAYIN ORTASI -- her uzayda tanim geregi iceride.
    gercek = UZAY.from_unit(np.full((1, UZAY.ndim), 0.5))[0]
    veri = np.array([float(s.predict(gercek[None, :])[0]) for s in vekiller])
    print("\n[3] gercek: "
          + ", ".join(f"{ad}={v:.4g}" for ad, v in zip(UZAY.names, gercek, strict=False)),
          flush=True)
    print("    sentetik veri: "
          + ", ".join(f"{ad}={v:.5g}" for ad, v in zip(GOZLENEBILIRLER, veri, strict=False)),
          flush=True)

    print(f"\n[4] posterior (n_grid={a.n_grid})", flush=True)
    post = grid_posterior(UZAY, vekiller, veri, SIGMA_NOMINAL,
                          n_grid=a.n_grid)
    tarama = [(c, grid_posterior(UZAY, vekiller, veri,
                                 tuple(c * s for s in SIGMA_NOMINAL),
                                 n_grid=a.n_grid))
              for c in (1.0, 4.0, 16.0)]
    for j, ad in enumerate(UZAY.names):
        lo, hi = post.hdi(j)
        print(f"    {ad:16s} gercek={gercek[j]:10.4g}  "
              f"%68=[{lo:.4g}, {hi:.4g}]  bant/onsel={post.width_u[j]:.3f}",
              flush=True)

    print("\n[5] G4-C", flush=True)
    v = recovery_verdict(post, gercek, tarama)
    print(f"    {v.ozet}", flush=True)
    for r in v.c1_ayrinti:
        print(f"      C1 {r['ad']:16s} "
              f"{'ICERIYOR' if r['iceriyor'] else 'DISARIDA'}  "
              f"gercek={r['gercek']:.4g}  "
              f"bant={r['bant'][0]:.4g}..{r['bant'][1]:.4g}", flush=True)
    if v.c3_kosuldu:
        c = v.c3_ayrinti
        print(f"      C3 eksen={c['eksen']}  buyume={c['buyume_orani']:.2f}x",
              flush=True)
    print(f"\n    G4-C {'GECTI' if v.gecti else 'GECMEDI'}", flush=True)

    Path(a.out).write_text(json.dumps({
        "kaynak_ensemble": str(a.ensemble),
        "ileri_model": "iki_asamali (ileri_kosu_ikiasama)",
        "t_end": d["t_end"],
        "n_tasarim": int(len(x)), "gercek": gercek.tolist(),
        "sigma_nominal": list(SIGMA_NOMINAL),
        "vekil_q2": {ad: float(s.q2)
                     for ad, s in zip(GOZLENEBILIRLER, vekiller, strict=False)},
        "vekil_guvenilir": {ad: bool(s.guvenilir)
                            for ad, s in zip(GOZLENEBILIRLER, vekiller, strict=False)},
        "c1_gecti": v.c1_gecti, "c1_kapsama": v.c1_kapsama,
        "c1_ayrinti": v.c1_ayrinti,
        "c2_gecti": v.c2_gecti, "c2_en_dar": v.c2_en_dar,
        "c2_genislikler": v.c2_genislikler,
        "c3_kosuldu": v.c3_kosuldu, "c3_gecti": v.c3_gecti,
        "c3_ayrinti": v.c3_ayrinti,
        "G4C_gecti": v.gecti,
        "uzay": list(UZAY.names), "uzay_adi": "DART_UZAYI_S3",
        "adr_0044": True,
        # SURE DENETIMI: bu ensemble `t_end = 0,2 s`'de kosuldu ve
        # gerekcesi OLCUM -- beta t=0,2 ile t=5,0'da bit duzeyinde ayni.
        # `sure_denetimi` alani `faz45`in durulma zamanina bakar ve o
        # olcut A12'de YANILTICI bulundu; burada gerekce ACIKCA yaziliyor.
        "sure_denetimi": {
            "durum": "yeterli",
            "gerekce": "beta t=0,2 ile t=5,0'da BIT DUZEYINDE ayni "
                       "(1.4112162721355217, iki bagimsiz kosu)",
            "faz45_olcutu_kullanilmadi": True,
        },
    }, indent=2, default=float), encoding="utf-8")
    print(f"\nyazildi: {a.out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
