"""Protokol D — simülasyon posteriorunu GERÇEK DART gözlemine uygula (kilitli).

## Gözlem

DART'ın ölçtüğü periyot değişimi (`−33,0 ± 1,0 dk`) depodaki arayüzle
(`observables.period_interface.dart_beta_budget`) **simülasyonun kendi hedef
kütlesi ve mermi momentumu** için `β`'ya çevrilir (`β ≈ ∝ M`; yörünge hızı
toplam kütleye de bağlı, tam hesap arayüzde). Belirsizlik:

    σ_β² = (ΔT bandının yarı genişliği)² + (0,105 β)²

İkinci terim, arayüzün kendi belgesinde ölçülen dairesel-yörünge / yayımlanan
değer farkıdır (`%10,5`) — sistematik olarak eklenir, gizlenmez.

## Model

Havuzdaki koşularla `log10(β−1)` için ikinci derece vekil (P ile aynı
dönüşüm). Model belirsizliği `σ_vekil` = θ-gruplu 4-kat artık sapması
(P §4d). Çözünürlük terimi `σ_çöz` `cozunurluk_hatasi.py` çıktısından
(verilmezse `0` ve rapora **ÇÖZÜNÜRLÜK TERİMİ YOK** yazılır).

## Kilitli yargı

1. **Önsel kapsama:** `s = √(σ_gözlem² + σ_vekil² + σ_çöz²)` (log birimde).
   Izgara (40³) üzerindeki en büyük vekil tahmini `ŷ_max`, en küçüğü `ŷ_min`.
   `y_gözlem − 2s > ŷ_max` → **ÖNSEL DIŞI (YUKARI)**;
   `y_gözlem + 2s < ŷ_min` → **ÖNSEL DIŞI (AŞAĞI)**; aksi **ÖNSEL İÇİNDE**.
2. **ÖNSEL İÇİNDE** ise posterior (düzgün önsel, Gauss olabilirlik); eksen
   başına `%68` / `%95` aralık (orta nokta birikimi, A85 düzeltilmiş) ve
   bilgi oranı `genişlik68 / 0,68`. Bir eksen `bilgi oranı < 0,5` →
   **KISITLANIYOR**, aksi **KISITLANMIYOR**.
3. **ÖNSEL DIŞI** ise posterior hesaplanmaz; en yakın θ bölgesi (en büyük/
   küçük tahminin θ'sı) ve fark (σ cinsinden) raporlanır.

Kullanim:
    python scripts/dart_gozlem_posterior.py --kok kampanya \\
        --desen "Nto_matris_sahne*.durumlar+N2to_matris_sahne*.durumlar" \\
        --cozunurluk kampanya/S_cozunurluk_Mt_orta.json --json kampanya/S_DART_Qo.json
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import sys
from pathlib import Path

import numpy as np

_BURASI = Path(__file__).resolve().parent
sys.path.insert(0, str(_BURASI))
sys.path.insert(0, str(_BURASI.parent / "src"))

from dartrift.inference.design import DART_UZAYI_S3  # noqa: E402
from dartrift.observables.period_interface import dart_beta_budget  # noqa: E402

SISTEMATIK_BAGIL = 0.105
KAPSAMA_SIGMA_KATI = 2.0
BILGI_ESIGI = 0.5
N_IZGARA = 40
GOZLEM = "beta_eksi_1"
EKSENLER = ("blok_alpha0", "log10_Y0", "blok_kesri")


def gozlenen_beta(hedef_kutlesi: float, p_imp: float) -> dict:
    b = dart_beta_budget(p_imp, target_mass=hedef_kutlesi)
    s_dt = 0.5 * (b["beta_high"] - b["beta_low"])
    s_sis = SISTEMATIK_BAGIL * b["beta"]
    sigma = math.hypot(s_dt, s_sis)
    bm1 = b["beta"] - 1.0
    if bm1 <= 0:
        raise ValueError(f"gozlenen beta-1 pozitif degil: {bm1}")
    return {"beta": b["beta"], "beta_eksi_1": bm1, "sigma_beta": sigma,
            "sigma_dT": s_dt, "sigma_sistematik": s_sis,
            "y_log": math.log10(bm1), "sigma_log": sigma / (bm1 * math.log(10.0)),
            "hedef_kutlesi": float(hedef_kutlesi), "p_imp": float(p_imp)}


def sahne_buyuklukleri(kok: Path, desen: str) -> dict:
    Ms, ps = [], []
    for ds in desen.replace("+", ",").split(","):
        for f in sorted(glob.glob(str(kok / ds.strip() / "nokta_*.npz"))):
            z = np.load(f)
            hedef = np.asarray(z["mermi_kesri"]) < 0.5
            Ms.append(float(np.asarray(z["m"])[hedef].sum()))
            ps.append(float(z["p_imp"]))
    if not Ms:
        raise SystemExit(f"desende npz yok: {desen}")
    return {"hedef_kutlesi": float(np.median(Ms)), "p_imp": float(np.median(ps)),
            "hedef_kutlesi_yayilim": float(np.ptp(Ms)), "n_npz": len(Ms)}


def _orta_nokta_aralik(m: np.ndarray, eksen: np.ndarray, a: float, b: float):
    """Yamuk ağırlıklı orta nokta birikimi (A85).

    Izgara `[0, 1]`'in iki ucunu da içeriyor: uç düğümler YARIM hücre temsil
    eder. İlk sürüm (yalnız orta nokta) düz dağılımda `%16` sınırını `0,1515`
    veriyordu — sınav yakaladı; yamuk ağırlıkla tam `0,16`.

    A87 (2026-09-15): o yamuk sürümü `(cumsum(w) − w/2)` uç düğümleri İKİNCİ
    kez yarılıyordu: `F(0) = p₀/4`, `F(1) = 1 − p_N/4`. İç kantiller tamdı
    (sınav yalnız `0,16/0,84`'e bakıyordu); düz dağılımda 21 düğümde `%2,5`
    sınırı `0,025` yerine `0,0167` çıktı. Doğrusu hücre integralleri:
    `F_k = Σ_{i<k} (p_i + p_{i+1})/2`, `F_0 = 0`, `F_N = 1`.
    """
    p = np.asarray(m, float)
    kum = np.cumsum(p) - 0.5 * p[0] - 0.5 * p
    kum = kum / kum[-1]
    return float(np.interp(a, kum, eksen)), float(np.interp(b, kum, eksen))


def onsel_kapsama(tahmin: np.ndarray, y: float, s: float) -> dict:
    lo, hi = float(np.min(tahmin)), float(np.max(tahmin))
    if y - KAPSAMA_SIGMA_KATI * s > hi:
        karar = "ONSEL DISI (YUKARI)"
    elif y + KAPSAMA_SIGMA_KATI * s < lo:
        karar = "ONSEL DISI (ASAGI)"
    else:
        karar = "ONSEL ICINDE"
    return {"karar": karar, "tahmin_min": lo, "tahmin_max": hi,
            "fark_ust_sigma": (y - hi) / s, "fark_alt_sigma": (lo - y) / s}


def posterior(tahmin: np.ndarray, y: float, s: float, n_grid: int) -> dict:
    ki2 = (tahmin - y) ** 2 / s ** 2
    lp = -0.5 * ki2
    p = np.exp(lp - lp.max()).reshape((n_grid,) * 3)
    p /= p.sum()
    eksen = np.linspace(0.0, 1.0, n_grid)
    out = {}
    for j, ad in enumerate(EKSENLER):
        m = p.sum(axis=tuple(i for i in range(3) if i != j))
        a68 = _orta_nokta_aralik(m, eksen, 0.16, 0.84)
        a95 = _orta_nokta_aralik(m, eksen, 0.025, 0.975)
        g = a68[1] - a68[0]
        oran = g / 0.68
        out[ad] = {"marjinal": m.tolist(), "aralik68_u": a68, "aralik95_u": a95,
                   "genislik68_u": g, "bilgi_orani": oran,
                   "karar": "KISITLANIYOR" if oran < BILGI_ESIGI else "KISITLANMIYOR"}
    idx = np.unravel_index(int(np.argmax(p)), p.shape)
    u_map = np.array([[eksen[i] for i in idx]])
    out["MAP_dogal"] = DART_UZAYI_S3.from_unit(u_map)[0].tolist()
    return out


def uygula(X, y_sim, grup, gozlem: dict, *, sigma_coz: float = 0.0,
           n_grid: int = N_IZGARA) -> dict:
    """Saf hesap (sınanabilir): havuz `(X, log10(β−1))` → yargı + posterior."""
    import p_kalibrasyon_raporu as pr

    from dartrift.inference.surrogate import fit_surrogate

    X = np.asarray(X, float)
    y_sim = np.asarray(y_sim, float)
    v = fit_surrogate(DART_UZAYI_S3, X, y_sim)
    e = pr.kfold_artiklari(X, y_sim, grup)
    s_vekil = float(np.std(e, ddof=1))
    tahmin = pr._izgara_tasarimi(n_grid) @ v.coef
    s = math.sqrt(gozlem["sigma_log"] ** 2 + s_vekil ** 2 + sigma_coz ** 2)
    kap = onsel_kapsama(tahmin, gozlem["y_log"], s)
    u = pr._izgara_u(n_grid)
    i_max, i_min = int(np.argmax(tahmin)), int(np.argmin(tahmin))
    kap["theta_max_dogal"] = DART_UZAYI_S3.from_unit(u[i_max][None, :])[0].tolist()
    kap["theta_min_dogal"] = DART_UZAYI_S3.from_unit(u[i_min][None, :])[0].tolist()
    kap["beta_max_model"] = 1.0 + 10.0 ** kap["tahmin_max"]
    out = {"gozlem": gozlem, "sigma_vekil_log": s_vekil, "sigma_coz_log": sigma_coz,
           "sigma_toplam_log": s, "q2_vekil": v.q2, "n_kosu": int(len(y_sim)),
           "kapsama": kap}
    if kap["karar"] == "ONSEL ICINDE":
        out["posterior"] = posterior(tahmin, gozlem["y_log"], s, n_grid)
    return out


def main(argv=None) -> int:
    import p_kalibrasyon_raporu as pr

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kok", type=Path, required=True)
    ap.add_argument("--desen", required=True, help="'+' ile ayrilmis havuz desenleri (A84)")
    ap.add_argument("--cozunurluk", type=Path, default=None)
    ap.add_argument("--json", type=Path, default=None)
    a = ap.parse_args(argv)
    sahne = sahne_buyuklukleri(a.kok, a.desen)
    gozlem = gozlenen_beta(sahne["hedef_kutlesi"], sahne["p_imp"])
    kayit = pr.kayitlari_oku(a.kok, a.desen.replace("+", ","))
    X, Y = pr._matrisler(kayit, [GOZLEM])
    sigma_coz, coz_notu = 0.0, "COZUNURLUK TERIMI YOK"
    if a.cozunurluk and a.cozunurluk.exists():
        c = json.loads(a.cozunurluk.read_text(encoding="utf-8"))["gozlem"][GOZLEM]
        if np.isfinite(c.get("sigma_coz", float("nan"))):
            sigma_coz, coz_notu = float(c["sigma_coz"]), f"cozunurluk: {a.cozunurluk.name}"
    out = uygula(X, Y[:, 0], pr._gruplar(X), gozlem, sigma_coz=sigma_coz)
    out.update(sahne=sahne, desen=a.desen, cozunurluk_notu=coz_notu)
    k = out["kapsama"]
    print("=" * 78)
    print(f"PROTOKOL D -- DART gozlemi ({out['n_kosu']} kosu, {coz_notu})")
    print("=" * 78)
    print(f"  sahne hedef kutlesi {sahne['hedef_kutlesi']:.4g} kg, p_imp {sahne['p_imp']:.4g}")
    print(f"  gozlenen beta {gozlem['beta']:.3f} +- {gozlem['sigma_beta']:.3f}  "
          f"(beta-1 = {gozlem['beta_eksi_1']:.3f})")
    print(f"  sigma log: gozlem {gozlem['sigma_log']:.3f}  vekil {out['sigma_vekil_log']:.3f}  "
          f"cozunurluk {sigma_coz:.3f}  toplam {out['sigma_toplam_log']:.3f}")
    print(f"  model beta araligi: {1 + 10 ** k['tahmin_min']:.3f} .. {k['beta_max_model']:.3f}"
          f"  (en buyuk theta {np.round(k['theta_max_dogal'], 3).tolist()})")
    print(f"  ONSEL KAPSAMA: {k['karar']}  (ust fark {k['fark_ust_sigma']:+.2f} sigma)")
    if "posterior" in out:
        for ad in EKSENLER:
            d = out["posterior"][ad]
            print(f"  {ad:>12}: 68% u {np.round(d['aralik68_u'], 3).tolist()}  "
                  f"bilgi orani {d['bilgi_orani']:.2f} -> {d['karar']}")
        print(f"  MAP: {np.round(out['posterior']['MAP_dogal'], 4).tolist()}")
    if a.json:
        a.json.write_text(json.dumps(out, indent=1, default=float), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
