"""Protokol N — küresel ayırt edilebilirlik taraması (kilitli, koşudan ÖNCE).

G1/G2 bozuk bir ölçü (A73), sahneye ulaşmayan bir blok ekseni (A74),
aşılan akma sınırı (A72) ve rastgele bir çarpma sahasıyla (L sonucu)
yapılmıştı. N aynı soruyu en iyi fizikle ve **koşullanmış** (matris)
çarpma sahasıyla soruyor: gözlem vektörünün her bileşeni önsel boyunca
`θ`'yı gerçekleşme gürültüsünden ayırt ediyor mu, ve **kaç eksen**
görünüyor?

Gözlem başına yargı — Protokol G'nin eşikleri AYNEN
(`ayirt_raporu.F_ESIGI`, `RHO_ESIGI`, `P_ESIGI`):
`F > 4` ve en az bir eksende `|ρ| > 0,5`, `p < 0,05` → **AYIRT EDİYOR**;
her iki varyans sıfırsa → **DEJENERE**; aksi → **AYIRT ETMİYOR**.

Eksen sayımı — ÇOKLU SINAV DÜZELTMELİ: bir eksen, AYIRT EDEN bir
gözlemde `|ρ| > 0,5` ve `p < 0,05 / (gözlem sayısı × 3)` (Bonferroni)
ise **görünür**. Toplam: 3 → ÜÇ EKSEN GÖRÜNÜR, 2 → İKİ EKSEN,
1 → TEK EKSEN, 0 → HİÇBİRİ.

Kullanim:
    python scripts/n_ayirt_raporu.py --kok kampanya --json S_N.json
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path

import numpy as np

_BURASI = Path(__file__).resolve().parent
sys.path.insert(0, str(_BURASI))
sys.path.insert(0, str(_BURASI.parent / "src"))

GOZLEMLER_N = ("d_merkez", "V_krater", "R_krater", "dV_sikisma",
               "beta_eksi_1", "M_ejekta", "mu_ejekta")
EKSENLER = ("blok_alpha0", "log10_Y0", "blok_kesri")
#: Eksen sayimi icin Bonferroni payi: gozlem sayisi x eksen sayisi.
BONFERRONI_SINAV = len(GOZLEMLER_N) * len(EKSENLER)
EKSEN_ADLARI = {3: "UC EKSEN GORUNUR", 2: "IKI EKSEN", 1: "TEK EKSEN", 0: "HICBIRI"}


def _ar():
    import ayirt_raporu as ar

    return ar


def gozlem_yargisi(tablo: dict, gozlem: str, *, n_perm: int = 20000) -> dict:
    """Tek gözlem için F, eksen korelasyonları ve Protokol G yargısı."""
    ar = _ar()
    F = ar.varyans_orani(tablo, gozlem)
    th, ort = [], []
    for anah, kayitlar in sorted(tablo.items()):
        v = np.array([k[gozlem] for k in kayitlar], float)
        v = v[np.isfinite(v)]
        if len(v):
            th.append(anah)
            ort.append(float(v.mean()))
    th = np.asarray(th, float)
    ort = np.asarray(ort, float)
    eksen = {}
    if len(ort) >= 4:
        degerler = (th[:, 0], np.log10(th[:, 1]), th[:, 2])
        for ad, d in zip(EKSENLER, degerler, strict=True):
            eksen[ad] = {"rho": ar.spearman(d, ort),
                         "p": ar.permutasyon_p(d, ort, n=n_perm)}
    if F.get("dejenere"):
        karar = "DEJENERE"
    elif (np.isfinite(F["F"]) and F["F"] > ar.F_ESIGI and any(
            abs(e["rho"]) > ar.RHO_ESIGI and e["p"] < ar.P_ESIGI
            for e in eksen.values())):
        karar = "AYIRT EDIYOR"
    else:
        karar = "AYIRT ETMIYOR"
    return {"karar": karar, "F": F, "eksen": eksen, "n_theta": int(len(ort))}


def eksen_sayimi(yargilar: dict) -> dict:
    """Bonferroni düzeltmeli görünür eksenler."""
    ar = _ar()
    esik = ar.P_ESIGI / BONFERRONI_SINAV
    gorunen = set()
    for y in yargilar.values():
        if y["karar"] != "AYIRT EDIYOR":
            continue
        for ad, e in y["eksen"].items():
            if abs(e["rho"]) > ar.RHO_ESIGI and e["p"] < esik:
                gorunen.add(ad)
    return {"gorunen": sorted(gorunen), "karar": EKSEN_ADLARI[len(gorunen)],
            "p_esigi_bonferroni": esik}


def topla(kok: Path, desen: str = "N_matris_sahne*.durumlar") -> dict:
    """Tohum başına kayıtlar → `ayirt_raporu.esle` tablosu."""
    import vekil_posterior as vp
    from gozlem_vektoru import gozlem_vektoru

    kollar: dict[str, list[dict]] = {}
    gorulen: set = set()
    # Virgulle ayrilmis birden cok desen (P-v4 havuzu: N ve N2 birlikte).
    dizinler = sorted({d for ds in desen.split(",") for d in glob.glob(str(kok / ds.strip()))})
    for dz in dizinler:
        t = vp._tohum_ayikla(dz)
        for f in sorted(glob.glob(dz + "/nokta_*.npz")):
            z = np.load(f)
            gv = gozlem_vektoru(z)
            gv["beta_eksi_1"] = gv["beta_hedef"] - 1.0
            gv["theta"] = np.asarray(z["theta"], float).ravel()
            anah = (tuple(np.round(gv["theta"], 12)), t)
            if anah in gorulen:            # A83 dolgusu: ayni (theta, tohum) bir kez
                continue
            gorulen.add(anah)
            kollar.setdefault(t, []).append(gv)
    return _ar().esle(list(kollar.values()))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kok", type=Path, required=True)
    ap.add_argument("--desen", default="N_matris_sahne*.durumlar",
                    help="aynı kilitli kuralla başka merdiven (ör. No_matris_sahne*)")
    ap.add_argument("--json", type=Path, default=None)
    a = ap.parse_args(argv)
    tablo = topla(a.kok, a.desen)
    print("=" * 78)
    print(f"PROTOKOL N -- kuresel ayirt edilebilirlik ({len(tablo)} theta)")
    print("=" * 78)
    yargilar = {}
    for g in GOZLEMLER_N:
        y = gozlem_yargisi(tablo, g)
        yargilar[g] = y
        ek = "  ".join(f"{ad}: rho={e['rho']:+.3f} p={e['p']:.4f}"
                       for ad, e in y["eksen"].items())
        print(f"  {g:>12}: F = {y['F']['F']:8.3g}   {ek}   -> {y['karar']}")
    es = eksen_sayimi(yargilar)
    print(f"\nGORUNEN EKSENLER (Bonferroni p < {es['p_esigi_bonferroni']:.4g}): "
          f"{es['gorunen']}  -> {es['karar']}")
    if a.json:
        a.json.write_text(json.dumps({"gozlem": yargilar, "eksen": es},
                                     indent=1, default=float), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
