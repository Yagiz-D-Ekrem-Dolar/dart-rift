"""Ayırt edilebilirlik raporu — Protokol G.

Soru: gözlenebilir `θ = (blok α₀, matris Y₀, blok kesri)` hakkında
bilgi taşıyor mu?

Yöntem: aynı `24` nokta **iki `root_seed`** ile koşulur. `root_seed`
blok yerleşimini belirlediği için ikinci tohum, *aynı fiziğin farklı
gerçeklemesidir*. Soru şuna iner:

    theta'lar arasi degisim  >  ayni theta'nin gerceklemeleri arasi mi?

    S_theta   = Var( ortalama_tohum(y | theta) )
    S_gurultu = ortalama_theta( Var_tohum(y | theta) )
    F         = S_theta / S_gurultu

Bu, uc noktali Richardson `sigma_num`'un YERINE GECMEZ (A52 onu
imkansiz kildi); kendi basina anlamli ve OLCULEBILIR bir tabandir.

Kullanim:
    python scripts/ayirt_raporu.py --durumlar A.durumlar B.durumlar
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

# --- PROTOKOL G esikleri, SONUCLARDAN ONCE kilitlendi ---------------
F_ESIGI = 4.0             # "ayirt ediyor" icin varyans orani
RHO_ESIGI = 0.5           # Spearman |rho|
P_ESIGI = 0.05            # permutasyon sinavi
KACAN_ORANI_ESIGI = 0.80  # n_kacan_hedef >= 1 olan nokta orani
ARTIK_ESIGI = 1.0e-10
BENZERSIZ_ALPHA0 = 3      # mermi + matris + blok (A46 nobetcisi)

THETA_ADLARI = ("blok_alpha0", "matris_Y0", "blok_kesri")


def _oku(dizin: Path) -> list[tuple[dict, object]]:
    """Bir `durumlar` dizinindeki her `npz`'den kimlik alanlarını çıkar."""
    kayit = []
    for yol in sorted(dizin.glob("nokta_*.npz")):
        d = np.load(yol)
        alan = set(d.files)
        if "theta" not in alan:
            print(f"ATLANDI (theta yok): {yol.name}", file=sys.stderr)
            continue
        k = {
            "dosya": yol.name,
            "theta": np.asarray(d["theta"], dtype=np.float64).ravel(),
            "surum": str(d["surum"]) if "surum" in alan else "",
            "fizik_ozeti": str(d["fizik_ozeti"]) if "fizik_ozeti" in alan else "",
        }
        # A46 nobetcisi: sahne gercekten M1 mi (mermi + matris + blok)
        if "alpha0" in alan:
            k["n_benzersiz_alpha0"] = int(
                len(np.unique(np.round(np.asarray(d["alpha0"]), 6))))
        kayit.append((k, d))
    return kayit


def _v_esc(d) -> float:
    from dartrift.observables.momentum_transfer import escape_speed

    m = np.asarray(d["m"])
    hedef = np.asarray(d["mermi_kesri"]) < 0.5
    return float(escape_speed(float(m[hedef].sum()), float(d["R"])))


def _olcumler(k: dict, d) -> dict:
    """`npz`'den defteri post-hoc hesapla."""
    from dartrift.observables.momentum_defteri import momentum_defteri

    v_esc = float(d["v_esc"]) if "v_esc" in d.files else _v_esc(d)
    md = momentum_defteri(
        d["x"], d["v"], d["m"],
        mermi_kesri=np.asarray(d["mermi_kesri"], dtype=np.float64),
        R=float(d["R"]), v_esc=v_esc,
        ehat=np.asarray(d["ehat"], dtype=np.float64),
        p_imp=float(d["p_imp"]))
    M = md["M_ejekta"]
    k.update(
        delta_beta=md["delta_beta_hedef"],
        M_ejekta=M,
        n_kacan=md["n_kacan_hedef"],
        artik_bagil=md["artik_bagil"],
        v_ort=(md["P_ejekta_eksenel"] / M) if M > 0 else float("nan"),
    )
    return k


def _sira(a):
    """Beraberliklerde ortalama sıra."""
    a = np.asarray(a, float)
    n = len(a)
    duz = np.argsort(a, kind="stable")
    r = np.empty(n, float)
    r[duz] = np.arange(1, n + 1, dtype=float)
    for v in np.unique(a):
        k = a == v
        if k.sum() > 1:
            r[k] = r[k].mean()
    return r


def spearman(a, b) -> float:
    """Sıra korelasyonu — scipy'siz."""
    ra, rb = _sira(a), _sira(b)
    ra = ra - ra.mean()
    rb = rb - rb.mean()
    payda = np.sqrt((ra * ra).sum() * (rb * rb).sum())
    return float((ra * rb).sum() / payda) if payda > 0 else float("nan")


def permutasyon_p(a, b, *, n: int = 20000, tohum: int = 0) -> float:
    """İki yanlı permütasyon sınavı — dağılım varsayımı yok."""
    rng = np.random.default_rng(tohum)
    gozlenen = abs(spearman(a, b))
    if not np.isfinite(gozlenen):
        return float("nan")
    b = np.asarray(b, float).copy()
    sayac = 0
    for _ in range(n):
        rng.shuffle(b)
        if abs(spearman(a, b)) >= gozlenen:
            sayac += 1
    return (sayac + 1) / (n + 1)


def esle(kollar: list[list[dict]]) -> dict:
    """Aynı `θ`'yı farklı tohumlarda eşle."""
    tablo: dict[tuple, list[dict]] = {}
    for kol in kollar:
        for k in kol:
            anahtar = tuple(np.round(k["theta"], 12))
            tablo.setdefault(anahtar, []).append(k)
    return tablo


def varyans_orani(tablo: dict, nicelik: str) -> dict:
    """`F = S_theta / S_gurultu`."""
    ort, ic = [], []
    for _, kayitlar in sorted(tablo.items()):
        v = np.array([k[nicelik] for k in kayitlar], dtype=float)
        v = v[np.isfinite(v)]
        if len(v) == 0:
            continue
        ort.append(v.mean())
        if len(v) > 1:
            ic.append(v.var(ddof=1))
    if len(ort) < 2 or not ic:
        return {"F": float("nan"), "S_theta": float("nan"),
                "S_gurultu": float("nan"), "n_theta": len(ort),
                "n_tekrarli": len(ic)}
    S_t = float(np.var(ort, ddof=1))
    S_g = float(np.mean(ic))
    return {"F": (S_t / S_g) if S_g > 0 else float("inf"),
            "S_theta": S_t, "S_gurultu": S_g,
            "n_theta": len(ort), "n_tekrarli": len(ic)}


def on_kosullar(tablo: dict) -> dict:
    hepsi = [k for v in tablo.values() for k in v]
    n = len(hepsi)
    kacanli = sum(1 for k in hepsi if k.get("n_kacan", 0) >= 1)
    defter = all(abs(k.get("artik_bagil", 1.0)) < ARTIK_ESIGI for k in hepsi)
    m1 = [k.get("n_benzersiz_alpha0") for k in hepsi]
    m1_tamam = all(v is None or v >= BENZERSIZ_ALPHA0 for v in m1)
    oran = kacanli / n if n else 0.0
    return {
        "n_kosu": n,
        "kacan_orani": oran,
        "kacan_gecti": bool(oran >= KACAN_ORANI_ESIGI),
        "defter_gecti": bool(defter),
        "M1_gecti": bool(m1_tamam),
        "alpha0_benzersiz": sorted({v for v in m1 if v is not None}),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--durumlar", nargs="+", type=Path, required=True)
    ap.add_argument("--nicelik", default="delta_beta",
                    choices=("delta_beta", "M_ejekta", "v_ort"))
    ap.add_argument("--json", type=Path, default=None)
    a = ap.parse_args(argv)

    kollar = []
    for dz in a.durumlar:
        ham = _oku(dz)
        kollar.append([_olcumler(k, d) for k, d in ham])
        print(f"{dz.name}: {len(ham)} nokta")

    tablo = esle(kollar)
    ok = on_kosullar(tablo)
    print("\n" + "=" * 68)
    print("ON KOSULLAR")
    print(f"  kosu sayisi           : {ok['n_kosu']}")
    print(f"  n_kacan >= 1 orani    : {ok['kacan_orani']:.3f}  "
          f"[{'GECTI' if ok['kacan_gecti'] else 'DUSTU'}]  "
          f"(esik {KACAN_ORANI_ESIGI})")
    print(f"  defter kapali         : "
          f"[{'GECTI' if ok['defter_gecti'] else 'DUSTU'}]")
    print(f"  sahne M1 (alpha0 >= 3): "
          f"[{'GECTI' if ok['M1_gecti'] else 'DUSTU'}]  "
          f"benzersiz={ok['alpha0_benzersiz']}")

    v = varyans_orani(tablo, a.nicelik)
    print("\n" + "=" * 68)
    print(f"VARYANS ORANI  ({a.nicelik})")
    print(f"  theta sayisi          : {v['n_theta']}  "
          f"(tekrarli: {v['n_tekrarli']})")
    print(f"  S_theta               : {v['S_theta']:.6g}")
    print(f"  S_gurultu             : {v['S_gurultu']:.6g}")
    print(f"  F                     : {v['F']:.4g}   (esik {F_ESIGI})")

    print("\n" + "=" * 68)
    print("SIRA KORELASYONU (theta bileseni <-> nicelik)")
    korel = {}
    anahtarlar = sorted(tablo.items())
    ths = np.array([np.mean([k["theta"] for k in kk], axis=0)
                    for _, kk in anahtarlar])
    ys = np.array([np.mean([k[a.nicelik] for k in kk]) for _, kk in anahtarlar])
    gecerli = np.isfinite(ys)
    for j, ad in enumerate(THETA_ADLARI):
        if gecerli.sum() < 4:
            korel[ad] = {"rho": float("nan"), "p": float("nan")}
            print(f"  {ad:14} yetersiz nokta ({int(gecerli.sum())})")
            continue
        rho = spearman(ths[gecerli, j], ys[gecerli])
        p = permutasyon_p(ths[gecerli, j], ys[gecerli])
        korel[ad] = {"rho": rho, "p": p}
        bayrak = "ANLAMLI" if (abs(rho) > RHO_ESIGI and p < P_ESIGI) else ""
        print(f"  {ad:14} rho = {rho:+.4f}   p = {p:.4f}   {bayrak}")

    anlamli = [ad for ad, c in korel.items()
               if abs(c["rho"]) > RHO_ESIGI and c["p"] < P_ESIGI]
    print("\n" + "=" * 68)
    if not (ok["kacan_gecti"] and ok["defter_gecti"] and ok["M1_gecti"]):
        yargi = "OKUNMAZ -- on kosul dustu"
    elif v["F"] > F_ESIGI and anlamli:
        yargi = f"AYIRT EDIYOR  (F = {v['F']:.3g}, eksen: {', '.join(anlamli)})"
    elif v["F"] > F_ESIGI:
        yargi = (f"BILGI VAR ama tek eksene inmiyor (F = {v['F']:.3g}); "
                 "bilesik parametre aranmali")
    elif v["F"] > 1.0:
        yargi = f"ZAYIF (F = {v['F']:.3g}) -- bildirilir, cikarim kurulmaz"
    else:
        yargi = f"AYIRT ETMIYOR (F = {v['F']:.3g})"
    print(f"YARGI: {yargi}")

    if a.json:
        a.json.write_text(json.dumps(
            {"on_kosullar": ok, "varyans": v, "korelasyon": korel,
             "yargi": yargi, "nicelik": a.nicelik}, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
