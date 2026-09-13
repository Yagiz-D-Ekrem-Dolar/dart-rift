"""A82 tanısı — dış örneklemde posterior neden aşırı güvenli? (KEŞİF, yargı değil)

Protokol P2 kilitli yargısı KALİBRASYON DÜŞTÜ (kuadratik `Y₀` kapsama68
`0,48`, GP `0,26`). Bu betik **yalnız N → N2 yönünü** kullanır; ters yön
(N2 → N) sonradan seçilecek bir düzeltmenin **doğrulaması** için saklıdır.

Ölçülenler:

1. Sınama gözleminin **gerçek θ'daki** vekil tahmininden sapması,
   eğitim kovaryansının köşegeniyle standartlaştırılmış (`z`). Kalibre
   bir gürültü modelinde `z ~ N(0, 1)`: ortalama `≈ 0`, sapma `≈ 1`,
   `|z| > 3` kesri `≈ 0,003`. Ortalama kayması → N ile N2 arasında
   dağılım farkı; sapma `> 1` → gürültü hafife alınmış; ağır kuyruk →
   rejim sıçraması.
2. Mahalanobis `χ² = rᵀ S⁻¹ r` (tam kovaryans) — `k` serbestlik
   derecesinde beklenen ortalama `k`.
3. Varyantlar: `λ ∈ {0,3 ; 0 ; 1}`, gözlenebilir alt kümeleri, kovaryans
   `×2, ×4` — `Y₀` kapsama ve genişlik.

Kullanim:
    python scripts/p_tani_raporu.py --kok kampanya --s-n kampanya/S_N.json \\
        --onbellek kampanya/P_tani_kayit.json --json kampanya/S_P_tani.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

_BURASI = Path(__file__).resolve().parent
sys.path.insert(0, str(_BURASI))
sys.path.insert(0, str(_BURASI.parent / "src"))

import p_kalibrasyon_raporu as pr  # noqa: E402

from dartrift.inference.design import DART_UZAYI_S3  # noqa: E402
from dartrift.inference.posterior import grid_posterior_kovaryans  # noqa: E402
from dartrift.inference.surrogate import design_matrix  # noqa: E402


def kayit_yukle(kok: Path, desen: str, onbellek: Path | None) -> list[dict]:
    if onbellek is not None and onbellek.exists():
        ham = json.loads(onbellek.read_text(encoding="utf-8")).get(desen)
        if ham is not None:
            return [{**k, "theta": np.asarray(k["theta"], float)} for k in ham]
    kay = pr.kayitlari_oku(kok, desen)
    if onbellek is not None:
        tum = json.loads(onbellek.read_text(encoding="utf-8")) if onbellek.exists() else {}
        tum[desen] = [{**k, "theta": np.asarray(k["theta"]).tolist()} for k in kay]
        onbellek.write_text(json.dumps(tum, default=float), encoding="utf-8")
    return kay


def z_tanisi(Xe, Ye, Xt, Yt, adlar, lam=pr.KUCULTME) -> dict:
    C, _ = pr._egit(Xe, Ye)
    grup = pr._gruplar(Xe)
    from dartrift.inference.surrogate import loo_artiklari

    E = np.column_stack([loo_artiklari(DART_UZAYI_S3, Xe, Ye[:, i], gruplar=grup)
                         for i in range(Ye.shape[1])])
    S = pr.kuculmus_kov(E, lam)
    tah = design_matrix(DART_UZAYI_S3.to_unit(Xt)) @ C
    r = Yt - tah
    z = r / np.sqrt(np.diag(S))[None, :]
    chi2 = np.einsum("ij,jk,ik->i", r, np.linalg.inv(S), r)
    egit_z = E / np.sqrt(np.diag(S))[None, :]
    return {
        "gozlem": {a: {"z_ort": float(z[:, i].mean()), "z_sapma": float(z[:, i].std(ddof=1)),
                       "abs_z_gt3": float(np.mean(np.abs(z[:, i]) > 3)),
                       "egitim_loo_z_sapma": float(egit_z[:, i].std(ddof=1))}
                   for i, a in enumerate(adlar)},
        "chi2_ort": float(chi2.mean()), "chi2_medyan": float(np.median(chi2)),
        "chi2_beklenen": int(Yt.shape[1]),
        "en_kotu_5": [{"theta": Xt[j].tolist(), "chi2": float(chi2[j])}
                      for j in np.argsort(chi2)[::-1][:5]],
        "korelasyon": np.corrcoef(E, rowvar=False).round(3).tolist(),
    }


def varyant(Xe, Ye, Xt, Yt, *, lam, carpan=1.0, n_grid=32) -> dict:
    C, _ = pr._egit(Xe, Ye)
    grup = pr._gruplar(Xe)
    from dartrift.inference.surrogate import loo_artiklari

    E = np.column_stack([loo_artiklari(DART_UZAYI_S3, Xe, Ye[:, i], gruplar=grup)
                         for i in range(Ye.shape[1])])
    S = carpan * pr.kuculmus_kov(E, lam)
    tahmin = pr._izgara_tasarimi(n_grid) @ C
    U = DART_UZAYI_S3.to_unit(Xt)
    kap, gen = [], []
    for r in range(len(Xt)):
        post = grid_posterior_kovaryans(DART_UZAYI_S3, tahmin, Yt[r], S, n_grid)
        lo, hi = post.hdi_u[1]
        kap.append(lo <= U[r, 1] <= hi)
        gen.append(hi - lo)
    return {"Y0_kapsama68": float(np.mean(kap)), "Y0_medyan_genislik": float(np.median(gen))}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kok", type=Path, required=True)
    ap.add_argument("--s-n", type=Path, default=None)
    ap.add_argument("--onbellek", type=Path, default=None)
    ap.add_argument("--json", type=Path, default=None)
    a = ap.parse_args(argv)
    s_n = json.loads(a.s_n.read_text(encoding="utf-8")) if a.s_n else None
    egit = kayit_yukle(a.kok, "N_matris_sahne*.durumlar", a.onbellek)
    test = kayit_yukle(a.kok, "N2_matris_sahne*.durumlar", a.onbellek)
    secilen, _ = pr.gozlem_sec(egit, s_n)
    Xe, Ye = pr._matrisler(egit, secilen)
    Xt, Yt = pr._matrisler(test, secilen)
    print("=" * 78)
    print(f"A82 TANISI (KESIF) -- N -> N2, gozlenebilirler {secilen}")
    print(f"  egitim {len(Xe)} kosu, sinama {len(Xt)} kosu")
    print("=" * 78)
    zt = z_tanisi(Xe, Ye, Xt, Yt, secilen)
    for g, d in zt["gozlem"].items():
        print(f"  {g:>12}: z ort {d['z_ort']:+.2f}  z sapma {d['z_sapma']:.2f}  "
              f"|z|>3 {d['abs_z_gt3']:.2f}  (egitim LOO z sapma {d['egitim_loo_z_sapma']:.2f})")
    print(f"  chi2 ortalama {zt['chi2_ort']:.1f}  medyan {zt['chi2_medyan']:.1f}  "
          f"(beklenen {zt['chi2_beklenen']})")
    print("  en kotu 5:", [(np.round(e['theta'], 3).tolist(), round(e['chi2'], 1))
                           for e in zt["en_kotu_5"]])
    sonuc = {"z": zt, "varyant": {}}
    denemeler = [("lam0.3", dict(lam=0.3)), ("lam0", dict(lam=0.0)),
                 ("lam1_kosegen", dict(lam=1.0)), ("lam0.3_x2", dict(lam=0.3, carpan=2.0)),
                 ("lam0.3_x4", dict(lam=0.3, carpan=4.0)), ("lam0_x2", dict(lam=0.0, carpan=2.0))]
    for ad, kw in denemeler:
        v = varyant(Xe, Ye, Xt, Yt, **kw)
        sonuc["varyant"][ad] = v
        print(f"  varyant {ad:>14}: Y0 kapsama68 {v['Y0_kapsama68']:.2f}  "
              f"genislik {v['Y0_medyan_genislik']:.3f}")
    for alt in (["beta_eksi_1"], ["beta_eksi_1", "V_krater"],
                [g for g in secilen if g != "R_krater"]):
        idx = [secilen.index(g) for g in alt if g in secilen]
        if not idx:
            continue
        v = varyant(Xe, Ye[:, idx], Xt, Yt[:, idx], lam=0.3)
        sonuc["varyant"]["+".join(alt)] = v
        print(f"  alt kume {'+'.join(alt)}: Y0 kapsama68 {v['Y0_kapsama68']:.2f}  "
              f"genislik {v['Y0_medyan_genislik']:.3f}")
    if a.json:
        a.json.write_text(json.dumps(sonuc, indent=1, default=float), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
