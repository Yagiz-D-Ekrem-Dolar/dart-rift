"""Üretim posterioru — ADR-0058'in **kilitli** tarifini uçtan uca koşar.

Bu betik hiçbir karar vermez; verilmiş kararları uygular:

| adım | kaynak |
|---|---|
| Kapı 1: kayıp koşu `≤ %20` | PROTOKOL-HAVUZ §3 |
| vekil: GP + Bachoc grup-CD kalibrasyonu | ADR-0058 §4.1 |
| `θ`-grupları, 4 kat (`kat = indis % 4`) | ADR-0058 §4.1, A82 |
| olabilirlik: `grid_posterior_hetero`, `log det` korunur | ADR-0058 §4.2 |
| `R` ÖLÇÜLÜR, varsayılmaz | ADR-0058 §4.3 |
| gözlemliler `β` ve `M_ejekta`, hedefler ADR-0054 / L17 | ADR-0058 §4.4 |
| `σ_model` yalnız ÖLÇÜLMÜŞ terimlerden | PROTOKOL-HAVUZ §5, KAYIT-076 §7 |
| `β` **fırlatı geleneğinde** | ADR-0060 |
| `n_yön`: Fisher öz değeri `> 36` | ADR-0051 |

## Girdi

CSV, sütunlar: `idx,beta,ejf,kos`

* `idx` — küresel tasarım indisi (`0..95`). Havuz `jsonl`'lerindeki `i`
  alanı DİLİM İÇİ indistir; küresel indis `dilim + 24*i`'dir.
* `beta` — koşunun kendi raporladığı `β` (çarpıcı geleneğinde).
* `ejf` — fırlatı kütle kesri.
* `kos` — `cos θ`, `θ = ∠(Ê, ê_U)`; durum dosyasından (ADR-0060).

## Çıktı

Özet tablo + `--json` ile tam kayıt. **Hiçbir yargı burada yumuşatılmaz:**
bir kapı düşerse betik bunu yazar ve ilgili sonucu vermez.

    python scripts/uretim_posterior.py havuz.csv --json posterior.json
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np

from dartrift.inference.artik_korelasyonu import artik_korelasyonu
from dartrift.inference.design import DART_UZAYI_S4, lhs_design
from dartrift.inference.gp_vekil import (
    gp_grup_loo,
    gp_uydur,
    gp_varyans_kalibre,
)
from dartrift.inference.posterior import grid_posterior_hetero
from dartrift.inference.tanimlanabilirlik import (
    FISHER_ESIGI,
    fisher_yonleri,
    posterior_daralma,
    yerel_jakobyen,
)
from dartrift.inference.tarih_esleme import model_eksikligi_kaynakli

N_HAVUZ, TOHUM, KAT_SAYISI = 96, 20260906, 4

#: PROTOKOL-HAVUZ §3: kayıp bunu aşarsa havuz geçersiz, yinelenir.
KAPI1_AZAMI_KAYIP = 0.20

#: ADR-0054 — kütleye göre düzeltilmiş gözlem hedefi.
BETA_GOZ, BETA_UST, BETA_ALT = 3.5418, 0.188, 0.247
#: L17 (Lolachi ve ark. 2025) ve sahne kütlesi (ADR-0054).
M_EJEKTA_GOZ, M_EJEKTA_SIGMA, M_SAHNE = 1.6e7, 0.3e7, 4.2980e9

#: KAYIT-076 §7 — paydaya giren terimler, gözlemli başına.
TERIMLER_BETA = ("gerceklem_beta_DART", "cozunurluk_uzak",
                 "cozunurluk_yakin", "plato_olculen_DART",
                 "hedef_sekli_olculen", "carpma_yeri_olculen")
TERIMLER_MEJ = ("gerceklem_M_ejekta_DART",)


def oku(yol: Path):
    idx, beta, ejf, kos = [], [], [], []
    with open(yol, newline="", encoding="utf-8") as f:
        for s in csv.DictReader(f):
            idx.append(int(s["idx"]))
            beta.append(float(s["beta"]))
            ejf.append(float(s["ejf"]))
            kos.append(float(s["kos"]))
    return (np.array(idx), np.array(beta), np.array(ejf), np.array(kos))


def kapi1(n_okunan: int, rapor: dict) -> None:
    kayip = 1.0 - n_okunan / N_HAVUZ
    rapor["kapi1"] = {"okunan": n_okunan, "hedef": N_HAVUZ,
                      "kayip": kayip, "azami": KAPI1_AZAMI_KAYIP}
    if kayip > KAPI1_AZAMI_KAYIP:
        rapor["kapi1"]["yargi"] = "DUSTU -- havuz yinelenir"
        raise SystemExit(
            f"KAPI 1 DUSTU: kayip %{100*kayip:.1f} > %{100*KAPI1_AZAMI_KAYIP:.0f}. "
            "PROTOKOL-HAVUZ §3 geregi havuz YINELENIR; posterior kosulmaz.")
    rapor["kapi1"]["yargi"] = "GECTI"
    if n_okunan < N_HAVUZ:
        rapor["kapi1"]["uyari"] = (
            f"KISMI HAVUZ ({n_okunan}/{N_HAVUZ}). Kapi gecti ama bu "
            "MUHURLU olcum degildir.")


def vekil_kur(X, y, katlar, ad: str, rapor: dict):
    """GP + Bachoc kalibrasyonu; artıkları da döndürür (`R` için)."""
    gp = gp_uydur(DART_UZAYI_S4, X, y)
    e, var = gp_grup_loo(gp, y, katlar)
    gp_k, bilgi = gp_varyans_kalibre(gp, y, katlar)
    z = e / np.sqrt(var * gp_k.varyans_carpani)
    rapor[ad] = {
        "cd_rmse": float(np.sqrt(np.mean(e**2))),
        "q2": float(1 - np.sum(e**2) / np.sum((y - y.mean())**2)),
        "varyans_carpani": float(gp_k.varyans_carpani),
        "kapsama68_kalibre": float(np.mean(np.abs(z) <= 1.0)),
        "ell": gp.ell.tolist(),
        "bachoc": {k: (v if not isinstance(v, np.ndarray) else v.tolist())
                   for k, v in bilgi.items()},
    }
    return gp_k, e


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("havuz", type=Path)
    ap.add_argument("--n-grid", type=int, default=60)
    ap.add_argument("--json", type=Path, default=None)
    a = ap.parse_args(argv)

    idx, beta, ejf, kos = oku(a.havuz)
    rapor: dict = {"girdi": str(a.havuz), "n_grid": a.n_grid}
    kapi1(len(idx), rapor)

    X = lhs_design(DART_UZAYI_S4, N_HAVUZ, root_seed=TOHUM)[idx]
    katlar = idx % KAT_SAYISI

    # --- gözlemliler ------------------------------------------------
    # ADR-0060: model b, gozlemin gelenegine cevrilir. `1/cos^2` her
    # kosunun kendi firlati alanindan; secilen bir sayi degil.
    if np.any(np.abs(kos) < 0.30):
        raise SystemExit("ADR-0060: |cos| < 0,30 olan kosu var, 1/cos^2 iraksar")
    b_model = (beta - 1.0) / kos**2
    m_model = ejf * M_SAHNE
    rapor["gelenek_carpani"] = {
        "ortanca": float(np.median(1.0 / kos**2)),
        "aralik": [float((1.0 / kos**2).min()), float((1.0 / kos**2).max())],
    }

    gp_b, e_b = vekil_kur(X, b_model, katlar, "vekil_beta", rapor)
    gp_m, e_m = vekil_kur(X, np.log(m_model), katlar, "vekil_M_ejekta", rapor)

    # --- R ÖLÇÜLÜR (ADR-0058 §4.3) ----------------------------------
    R, r_tani = artik_korelasyonu(np.column_stack([e_b, e_m]))
    rapor["R"] = r_tani

    # --- σ_model: yalnız ölçülmüş terimler --------------------------
    b_goz = BETA_GOZ - 1.0
    sm_b = model_eksikligi_kaynakli(b_goz, list(TERIMLER_BETA))
    sm_m = model_eksikligi_kaynakli(1.0, list(TERIMLER_MEJ))
    rapor["sigma_model"] = {"beta": sm_b, "M_ejekta_bagil": sm_m}

    sigma_goz_b = 0.5 * (BETA_UST + BETA_ALT)
    sigma_goz_m = M_EJEKTA_SIGMA / M_EJEKTA_GOZ          # log uzayinda bagil

    # --- ızgarada vekil öngörüsü ------------------------------------
    eksen = np.linspace(0.0, 1.0, a.n_grid)
    U = np.column_stack([g.ravel() for g in
                         np.meshgrid(*([eksen] * 3), indexing="ij")])
    mu_b, var_b = gp_b.predict_u(U)
    mu_m, var_m = gp_m.predict_u(U)

    ort = np.column_stack([mu_b, mu_m])
    varyans = np.column_stack([
        var_b + sigma_goz_b**2 + sm_b["sigma"]**2,
        var_m + sigma_goz_m**2 + sm_m["sigma"]**2,
    ])
    veri = np.array([b_goz, math.log(M_EJEKTA_GOZ)])

    post = grid_posterior_hetero(DART_UZAYI_S4, ort, varyans, veri, R,
                                 n_grid=a.n_grid)

    # --- tanımlanabilirlik ------------------------------------------
    rapor["daralma"] = posterior_daralma(post)
    u0 = np.clip(DART_UZAYI_S4.to_unit(X).mean(0), 0.02, 0.98)

    def ileri(u):
        uu = np.atleast_2d(u)
        return np.column_stack([gp_b.predict_u(uu)[0], gp_m.predict_u(uu)[0]])[0]

    J = yerel_jakobyen(ileri, u0)
    # S = D^(1/2) R D^(1/2); D izgaradaki ortalama varyans.
    sd = np.sqrt(varyans.mean(0))
    kov = np.outer(sd, sd) * R
    fis = fisher_yonleri(J, kov)
    rapor["fisher"] = {k: (v.tolist() if isinstance(v, np.ndarray) else v)
                       for k, v in fis.items()}
    rapor["fisher_esigi"] = FISHER_ESIGI

    # --- özet --------------------------------------------------------
    print("=" * 66)
    print("URETIM POSTERIORU — ADR-0058 kilitli tarifi")
    print("=" * 66)
    k1 = rapor["kapi1"]
    print(f"Kapi 1 : {k1['yargi']}  ({k1['okunan']}/{k1['hedef']}, "
          f"kayip %{100*k1['kayip']:.1f})")
    if "uyari" in k1:
        print(f"         !! {k1['uyari']}")
    gc = rapor["gelenek_carpani"]
    print(f"ADR-0060 gelenek carpani: ortanca {gc['ortanca']:.4f} "
          f"({gc['aralik'][0]:.3f}..{gc['aralik'][1]:.3f})")
    for ad in ("vekil_beta", "vekil_M_ejekta"):
        v = rapor[ad]
        print(f"{ad:15s} rmse={v['cd_rmse']:.4f} q2={v['q2']:+.4f} "
              f"Bachoc={v['varyans_carpani']:.3f} "
              f"kapsama68={v['kapsama68_kalibre']:.3f}")
    print(f"R (olculmus)   rho_ham={r_tani['rho_ham']:+.4f}  "
          f"kuculmus={r_tani['rho_kuculmus']:+.4f}")
    print(f"sigma_model    beta={sm_b['sigma']:.5f}  "
          f"M_ejekta={sm_m['sigma']:.5f}")
    print("\n--- daralma (1 = onsel kadar genis) ---")
    for d in rapor["daralma"]:
        print(f"   {d}")
    print(f"\n--- Fisher (esik {FISHER_ESIGI}) ---")
    print(f"   ozdegerler : {np.array(fis['ozdegerler']).round(2).tolist()}")
    print(f"   n_yon      : {fis['ogrenilen_yon_sayisi']} "
          f"(ust sinir {fis['ust_sinir']})")
    print(f"   sd orani   : "
          f"{np.array(fis['yaklasik_sd_oran']).round(3).tolist()}")
    print("\n" + "=" * 66)
    print("UYARI: M_ejekta hedefi (L17) kamera gorus alanindaki kutle icin")
    print("bir UST SINIR olarak bildirilmistir; model istatistigi tanimi")
    print("geregi ayni buyukluk degildir (rapor §4.4). ADR-0058 onu")
    print("paydaya aliyor; bu uyari sonucla birlikte okunmalidir.")
    print("=" * 66)

    if a.json:
        a.json.write_text(json.dumps(rapor, indent=1, ensure_ascii=False,
                                     default=float), encoding="utf-8")
        print(f"\nyazildi: {a.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
