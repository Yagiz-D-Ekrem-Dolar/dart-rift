"""PROTOKOL-UP §5 (önsel duyarlılığı) ve §6 (tarih eşleme) koşucusu.

Her iki yargı tablosu da 2026-10-08'de, havuzdan hiçbir nokta görülmeden
yazıldı. Bu betik onları *uygular*; eşik ve sınıf sınırları burada
**tanımlanmaz**.

Vekil, `R`, `σ_model` ve ızgara öngörüsü `uretim_posterior`'dan
**aynen** alınır (modül olarak içe aktarılır) — sabitler kopyalanmaz,
yoksa iki sayı kümesi zamanla sessizce ayrışır.

### §6 — tarih eşleme (Vernon)

    I(θ) = maks_j |E_j(θ) − z_j| / sqrt( Var_j(θ) + σ_j² )

`I > 3` → `bagdasmaz`. Bu kesme alanın kuralı, bizim seçimimiz değil;
ayarlanmaz. Posteriorun taşıdığı Gauss/köşegen varsayımlarını
taşımadığı için posteriorun **yanında** durur, yerine değil.

### §5 — önsel duyarlılığı

Protokolün üç önseli: `KILITLI`, `DUZ_LOG`, `KAYDIRILMIS`. Ölçüm
sırasında ortaya çıkan bir gerçek kayda geçiriliyor: kilitli önsel
ADR-0053 ile `Y₀ ∈ [1e0, 1e5]` (log, 5 dekad), yani **`DUZ_LOG`'un ta
kendisi**. Protokolü yazarken bunu fark etmemişim; ikisi ayrı önsel
değil, aynı dağılım. Betik bunu gizlemiyor, `ayni_dagilim` bayrağıyla
bildiriyor ve gerçek sınav `KAYDIRILMIS` ile yapılıyor.

`KAYDIRILMIS`: kilitli aralık `×3` kaydırılmış, yani `Y₀ ≥ 3 Pa`.
Düşük uç kesiliyor — veri yüksek `β` yüzünden **düşük** `Y₀` istediği
için bu, önselin veriyi yenmeye çalıştığı yön.

Kullanım:

    python scripts/up_onsel_ve_tarih.py <havuz.csv> --json <cikti.json>
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "src"))

import uretim_posterior as up  # noqa: E402

from dartrift.inference.artik_korelasyonu import artik_korelasyonu  # noqa: E402
from dartrift.inference.design import DART_UZAYI_S4, lhs_design  # noqa: E402
from dartrift.inference.posterior import grid_posterior_hetero  # noqa: E402
from dartrift.inference.tarih_esleme import model_eksikligi_kaynakli  # noqa: E402

#: Vernon kesmesi — alanin kurali, ayarlanmaz (UP §6).
I_KESME = 3.0

#: §5 yargi sinirlari (UP §5, dex).
ESIK_VERIDEN, ESIK_ONSELDEN = 0.15, 0.50

#: §6 yargi siniri (UP §6).
HACIM_ORANI_ESIGI = 10.0
KUTLE_ORTUSME_ESIGI = 0.90

#: KAYDIRILMIS onsel: kilitli araligin `x3` kaydirilmisi.
KAYDIRMA_CARPANI = 3.0


def _ortak(havuz: Path, n_grid: int) -> dict:
    """`uretim_posterior` ile BIREBIR ayni vekil/R/sigma/izgara yolu."""
    idx, beta, ejf, kos = up.oku(havuz)
    rapor: dict = {}
    up.kapi1(len(idx), rapor)
    X = lhs_design(DART_UZAYI_S4, up.N_HAVUZ, root_seed=up.TOHUM)[idx]
    katlar = idx % up.KAT_SAYISI

    if np.any(np.abs(kos) < 0.30):
        raise SystemExit("ADR-0060: |cos| < 0,30 olan kosu var")
    b_model = (beta - 1.0) / kos**2
    m_model = ejf * up.M_SAHNE

    gp_b, e_b = up.vekil_kur(X, b_model, katlar, "vekil_beta", rapor)
    gp_m, e_m = up.vekil_kur(X, np.log(m_model), katlar, "vekil_M_ejekta",
                             rapor)
    R, r_tani = artik_korelasyonu(np.column_stack([e_b, e_m]))
    rapor["R"] = r_tani

    b_goz = up.BETA_GOZ - 1.0
    sm_b = model_eksikligi_kaynakli(b_goz, list(up.TERIMLER_BETA))
    sm_m = model_eksikligi_kaynakli(1.0, list(up.TERIMLER_MEJ))
    s_goz_b = 0.5 * (up.BETA_UST + up.BETA_ALT)
    s_goz_m = up.M_EJEKTA_SIGMA / up.M_EJEKTA_GOZ

    eksen = np.linspace(0.0, 1.0, n_grid)
    U = np.column_stack([g.ravel() for g in
                         np.meshgrid(*([eksen] * 3), indexing="ij")])
    mu_b, var_b = gp_b.predict_u(U)
    mu_m, var_m = gp_m.predict_u(U)

    ort = np.column_stack([mu_b, mu_m])
    varyans = np.column_stack([
        var_b + s_goz_b**2 + sm_b["sigma"]**2,
        var_m + s_goz_m**2 + sm_m["sigma"]**2,
    ])
    veri = np.array([b_goz, math.log(up.M_EJEKTA_GOZ)])
    return {"rapor": rapor, "ort": ort, "varyans": varyans, "veri": veri,
            "R": R, "eksen": eksen, "n_grid": n_grid,
            "sigma": {"beta": sm_b, "M_ejekta": sm_m,
                      "gozlem_beta": s_goz_b, "gozlem_M": s_goz_m}}


def tarih_esleme(o: dict) -> dict:
    """§6 — bağdaşmazlık `I(θ)` ve bağdaşır hacim."""
    fark = np.abs(o["ort"] - o["veri"][None, :])
    imp = np.max(fark / np.sqrt(o["varyans"]), axis=1)
    bagdasir = imp <= I_KESME
    return {"I_kesme": I_KESME,
            "I_min": float(imp.min()), "I_ortanca": float(np.median(imp)),
            "I_maks": float(imp.max()),
            "V_bagdasir": float(np.mean(bagdasir)),
            "bagdasir_dugum": int(bagdasir.sum()),
            "toplam_dugum": int(imp.size),
            "maske": bagdasir, "I": imp}


def hdr_maske(p: np.ndarray, kutle: float = 0.68):
    """En yüksek yoğunluklu bölge: kütlenin `kutle` kadarını tutan küme."""
    d = p.ravel()
    sira = np.argsort(d)[::-1]
    kum = np.cumsum(d[sira])
    kes = int(np.searchsorted(kum, kutle * d.sum()) + 1)
    m = np.zeros(d.size, dtype=bool)
    m[sira[:kes]] = True
    return m


def onsel_agirligi(ad: str, eksen: np.ndarray, n_grid: int) -> np.ndarray:
    """Izgara düğümü başına log-önsel ağırlığı (`Y₀` ekseni = 1)."""
    if ad in ("KILITLI", "DUZ_LOG"):
        return np.zeros(n_grid**3)
    if ad != "KAYDIRILMIS":
        raise ValueError(ad)
    # Kilitli aralik [1e0, 1e5] -> log10 birim kupte [0,1].
    # `x3` kaydirma: alt sinir log10(3)/5 birimine cikar.
    alt = math.log10(KAYDIRMA_CARPANI) / 5.0
    U1 = np.meshgrid(*([eksen] * 3), indexing="ij")[1].ravel()
    w = np.where(U1 >= alt, 0.0, -np.inf)
    return w


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("havuz", type=Path)
    ap.add_argument("--n-grid", type=int, default=60)
    ap.add_argument("--json", type=Path, default=None)
    a = ap.parse_args(argv)

    o = _ortak(a.havuz, a.n_grid)
    rapor = o["rapor"]
    rapor["n_grid"] = a.n_grid

    # ---------------- §6 ----------------
    te = tarih_esleme(o)
    maske_b = te.pop("maske")
    te.pop("I")
    rapor["S6_tarih_esleme"] = te

    # ---------------- §5 ----------------
    post_ham = grid_posterior_hetero(DART_UZAYI_S4, o["ort"], o["varyans"],
                                     o["veri"], o["R"], n_grid=a.n_grid)
    logp0 = np.asarray(post_ham.logp, dtype=np.float64).ravel()
    eksen = o["eksen"]
    onseller = {}
    for ad in ("KILITLI", "DUZ_LOG", "KAYDIRILMIS"):
        lp = logp0 + onsel_agirligi(ad, eksen, a.n_grid)
        if not np.any(np.isfinite(lp)):
            raise SystemExit(f"{ad}: butun izgara disarida")
        p = np.exp(lp - np.nanmax(lp[np.isfinite(lp)]))
        p[~np.isfinite(lp)] = 0.0
        p /= p.sum()
        kip = int(np.argmax(p))
        u_kip = np.column_stack([g.ravel() for g in
                                 np.meshgrid(*([eksen] * 3),
                                             indexing="ij")])[kip]
        dogal = DART_UZAYI_S4.from_unit(u_kip[None, :])[0]
        P = p.reshape((a.n_grid,) * 3)
        kenar = [P.sum(axis=tuple(j for j in range(3) if j != k))
                 for k in range(3)]
        sd_u = []
        for k in range(3):
            mu = float(np.sum(eksen * kenar[k]))
            sd_u.append(float(np.sqrt(np.sum((eksen - mu)**2 * kenar[k]))))
        onseller[ad] = {
            "kip_dogal": dogal.tolist(),
            "kip_log10_Y0": float(math.log10(dogal[1])),
            "kip_u": u_kip.tolist(),
            "sd_u": sd_u,
            "daralma": [1.0 - (s**2) / (1.0 / 12.0) for s in sd_u],
            "p": p,
        }

    kipler = {k: v["kip_log10_Y0"] for k, v in onseller.items()}
    sigma_onsel = max(abs(kipler[a1] - kipler[a2])
                      for a1 in kipler for a2 in kipler)
    # alpha_b ve f icin bagil kayma (birim kupte).
    bagil = 0.0
    for j in (0, 2):
        vals = [onseller[k]["kip_u"][j] for k in onseller]
        bagil = max(bagil, max(vals) - min(vals))

    if sigma_onsel <= ESIK_VERIDEN and bagil <= 0.10:
        yargi5 = "SONUC VERIDEN GELIYOR"
    elif sigma_onsel <= ESIK_ONSELDEN:
        yargi5 = "ONSEL ETKILI"
    else:
        yargi5 = "SONUC ONSELDEN GELIYOR"

    rapor["S5_onsel_duyarliligi"] = {
        "ayni_dagilim": {
            "KILITLI_ile_DUZ_LOG": True,
            "not": ("ADR-0053 kilitli onseli Y0 in [1e0,1e5] (log, 5 dekad) "
                    "= log10 duzgun [0,5]; protokolun DUZ_LOG'u ile BIREBIR "
                    "ayni dagilim. Protokolu yazarken fark edilmemis. "
                    "Gercek sinav KAYDIRILMIS ile yapiliyor."),
        },
        "kaydirma_carpani": KAYDIRMA_CARPANI,
        "kipler_log10_Y0": kipler,
        "sigma_onsel_dex": sigma_onsel,
        "bagil_kayma_alpha_f": bagil,
        "esikler": {"veriden": ESIK_VERIDEN, "onselden": ESIK_ONSELDEN},
        "yargi": yargi5,
        "onseller": {k: {kk: vv for kk, vv in v.items() if kk != "p"}
                     for k, v in onseller.items()},
    }

    # ---------------- §6 yargisi: iki yontem ----------------
    p_kilitli = onseller["KILITLI"]["p"]
    m68 = hdr_maske(p_kilitli, 0.68)
    v_post68 = float(np.mean(m68))
    kutle_bagdasir = float(p_kilitli[m68 & maske_b].sum() /
                           max(p_kilitli[m68].sum(), 1e-300))
    oran = (te["V_bagdasir"] / v_post68) if v_post68 > 0 else float("inf")
    if kutle_bagdasir < KUTLE_ORTUSME_ESIGI:
        yargi6 = "CELISKI"
    elif oran > HACIM_ORANI_ESIGI:
        yargi6 = "POSTERIOR DAR"
    else:
        yargi6 = "IKI YONTEM UYUSUYOR"
    rapor["S6_tarih_esleme"].update({
        "V_post68": v_post68,
        "oran_V_bagdasir_V_post68": oran,
        "post68_kutlesinin_bagdasir_orani": kutle_bagdasir,
        "esikler": {"hacim_orani": HACIM_ORANI_ESIGI,
                    "kutle_ortusme": KUTLE_ORTUSME_ESIGI},
        "yargi": yargi6,
    })

    # ---------------- ozet ----------------
    print("=" * 70)
    print("PROTOKOL-UP §5 + §6")
    print("=" * 70)
    print(f"Kapi 1 : {rapor['kapi1']['yargi']} "
          f"({rapor['kapi1']['okunan']}/{rapor['kapi1']['hedef']})")
    for ad in ("vekil_beta", "vekil_M_ejekta"):
        v = rapor[ad]
        print(f"{ad:15s} q2={v['q2']:+.4f} Bachoc={v['varyans_carpani']:.3f} "
              f"kapsama68={v['kapsama68_kalibre']:.3f}")
    print(f"R olculmus     rho_kuculmus={rapor['R']['rho_kuculmus']:+.4f}")
    print()
    print(f"--- §6 TARIH ESLEME (I kesme {I_KESME}) ---")
    t = rapor["S6_tarih_esleme"]
    print(f"  I: min {t['I_min']:.3f} | ortanca {t['I_ortanca']:.3f} | "
          f"maks {t['I_maks']:.3f}")
    print(f"  bagdasir hacim V = {100*t['V_bagdasir']:.2f}% "
          f"({t['bagdasir_dugum']}/{t['toplam_dugum']} dugum)")
    print(f"  posterior %68 hacmi      = {100*t['V_post68']:.2f}%")
    print(f"  oran V_bagdasir/V_post68 = {t['oran_V_bagdasir_V_post68']:.2f} "
          f"(esik {HACIM_ORANI_ESIGI})")
    print(f"  post68 kutlesinin bagdasir orani = "
          f"{t['post68_kutlesinin_bagdasir_orani']:.4f} "
          f"(esik {KUTLE_ORTUSME_ESIGI})")
    print(f"  YARGI: {t['yargi']}")
    print()
    print("--- §5 ONSEL DUYARLILIGI ---")
    s5 = rapor["S5_onsel_duyarliligi"]
    print("  NOT: KILITLI ile DUZ_LOG ayni dagilim (ADR-0053 = log duzgun 5 dekad)")
    for k, v in s5["kipler_log10_Y0"].items():
        print(f"    {k:14s} kip log10(Y0) = {v:+.4f}")
    print(f"  sigma_onsel = {s5['sigma_onsel_dex']:.4f} dex "
          f"(esikler {ESIK_VERIDEN} / {ESIK_ONSELDEN})")
    print(f"  alpha_b,f bagil kayma = {s5['bagil_kayma_alpha_f']:.4f}")
    print(f"  YARGI: {s5['yargi']}")
    print("=" * 70)

    if a.json:
        a.json.write_text(json.dumps(rapor, indent=1, ensure_ascii=False,
                                     default=float), encoding="utf-8")
        print(f"yazildi: {a.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
