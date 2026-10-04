"""Protokol DO — `Y₀` önselinin DART sahnesinde sınanması (KİLİTLİ; §4–§5).

Üç DART-sahnesi noktası (`DY2` = `10 Pa`, `DO1` = `500 Pa`, `DO2` = `5000 Pa`)
ile `b = β − 1 = C · Y₀^p` uydurulur, gözlem (`β = 3,12`) tersine çevrilir ve
üretim önseli (`1e3 – 1e7 Pa`) `onsel_denetimi.onsel_denetle` ile sınanır.

Yargılar (§5.1): `ONSEL GOZLEMI ICERMIYOR` / `GOZLEM ONSEL KENARINDA` /
`ONSEL GOZLEMI ICERIYOR`. Bir kol geçersiz ya da `600 s`'ye ulaşmamışsa
genel **OKUNMAZ** ve hiçbir sayı yazılmaz.

Uydurma kalitesi kapısı (§5.1): en büyük bağıl artık `> ESIK_ARTIK` ise güç
yasası bu aralıkta uygun değil sayılır ve yargı, gözlemi **kuşatan** iki
noktanın yerel eğiminden okunur (`uydurma = "UYGUN DEGIL, YEREL EGIM"`).

§5.2: `M_ejekta`'nın `Y₀`'yu `β`'dan ne kadar iyi sıkıştırdığı
(`M_EJEKTA TANIMLAYICI` / `M_EJEKTA KAZANCI KUCUK` / `KAZANC YOK`).

Payda, DY2 ile **aynı** model eksikliği terimlerinden kurulur, ama `β − 1`
yerine **gözlemin** `b`'si (`3,12 − 1`) üzerinden: burada sorulan soru
"model gözleme uyuyor mu" değil, "gözlemin `Y₀`'su önselin içinde mi"
olduğu için ölçek gözlem noktasında alınır. Koşudan önce kilitli.

Kullanim:
    python scripts/do_onsel_raporu.py --kok kampanya --json kampanya/S_DO.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

# PROTOKOL-DO §2 (kilitli): kol adi -> Y0 [Pa]
KOLLAR: dict[str, float] = {
    "DY2_dart_g1p0": 10.0,
    "DO1_Y500_g1p0": 500.0,
    "DO2_Y5000_g1p0": 5000.0,
}
BETA_GOZLEM = 3.12                 # PROTOKOL-U §1
SIGMA_GOZLEM = 0.34
ONSEL_LO, ONSEL_HI = 1.0e3, 1.0e7  # ADR-0044 DART_UZAYI_S3
ESIK_ARTIK = 0.15                  # §5.1 uydurma kalitesi kapisi
#: `M_ejekta`'nin toplam bagil sd'si: L17 gozlemi (`0,3/1,6`) + gerceklem
#: (`0,15`, KAYIT-070). Sekil terimi **dahil degil** (yalniz `β` icin olculdu).
SIGMA_M_BAGIL = float(np.hypot(0.3 / 1.6, 0.15))


def oku(kok: Path, ad: str) -> dict | None:
    """`dy_dart_raporu.oku` ile **aynı** geçerlilik kapısı (600 s + `gecerli`)."""
    import dy_dart_raporu as DY
    return DY.oku(kok, ad)


def topla(kok: Path) -> dict:
    return {ad: oku(kok, ad) for ad in KOLLAR}


def _noktalar(kollar: dict) -> list[tuple[float, float, float]]:
    """`(Y₀, β, M_ejekta)`, `Y₀`'ya göre sıralı. Eksik/geçersiz kol → `[]`."""
    out = []
    for ad, y0 in KOLLAR.items():
        k = kollar.get(ad)
        if k is None or not (k["gecerli"] and k["ulasti"]):
            return []
        out.append((y0, k["beta"], k["M_ejekta"]))
    return sorted(out)


def _kusatan_cift(noktalar, beta_hedef: float):
    """`β_hedef`'i kuşatan komşu `(Y₀, β)` çifti; yoksa uçtaki komşu çift."""
    for (y1, b1, _), (y2, b2, _) in zip(noktalar, noktalar[1:], strict=False):
        if (b1 - beta_hedef) * (b2 - beta_hedef) <= 0.0:
            return (y1, b1), (y2, b2)
    ilk, son = noktalar[0], noktalar[-1]
    if abs(ilk[1] - beta_hedef) < abs(son[1] - beta_hedef):
        return (ilk[0], ilk[1]), (noktalar[1][0], noktalar[1][1])
    return (noktalar[-2][0], noktalar[-2][1]), (son[0], son[1])


def yargi(kollar: dict) -> dict:
    from dartrift.inference import onsel_denetimi as OD
    out: dict = {"gozlem": {"beta": BETA_GOZLEM, "sigma": SIGMA_GOZLEM},
                 "onsel": [ONSEL_LO, ONSEL_HI], "esik_artik": ESIK_ARTIK,
                 "kollar": {ad: (None if k is None else
                                 {a: k[a] for a in ("gecerli", "ulasti", "t_son", "n")})
                            for ad, k in kollar.items()}}
    nk = _noktalar(kollar)
    if not nk:
        out["genel"] = "OKUNMAZ (kol yok, gecersiz ya da 600 s'ye ulasmamis)"
        return out
    Y = [n[0] for n in nk]
    uy = OD.guc_yasasi_uydur(Y, [n[1] for n in nk])
    kullanilan, etiket = uy, "GUC YASASI"
    if uy.artik_en_buyuk > ESIK_ARTIK:
        (y1, b1), (y2, b2) = _kusatan_cift(nk, BETA_GOZLEM)
        kullanilan = OD.guc_yasasi_uydur([y1, y2], [b1, b2])
        etiket = "UYGUN DEGIL, YEREL EGIM"
    payda = float(np.hypot(SIGMA_GOZLEM,
                           (BETA_GOZLEM - 1.0) * _sigma_model_bagil()))
    d = OD.onsel_denetle(kullanilan, beta_gozlem=BETA_GOZLEM,
                         sigma_toplam=payda, onsel_lo=ONSEL_LO, onsel_hi=ONSEL_HI)
    out.update(noktalar=[{"Y0": a, "beta": b, "M_ejekta": m} for a, b, m in nk],
               uydurma=etiket, p=kullanilan.p, C=kullanilan.C,
               artik_uc_nokta=uy.artik_en_buyuk, payda=payda,
               onsel_denetimi=d, genel=d["genel"])

    # --- §5.2: M_ejekta kazanci (DART sahnesinde)
    gozlemliler = [
        OD.Gozlemli("beta", dict(zip(Y, [n[1] for n in nk], strict=True)),
                    payda / (BETA_GOZLEM - 1.0), True, eksi_bir=True),
        OD.Gozlemli("M_ejekta", dict(zip(Y, [n[2] for n in nk], strict=True)),
                    SIGMA_M_BAGIL, True),
    ]
    t = OD.duyarlilik_tablosu(gozlemliler)
    r = {s["ad"]: s for s in t["satirlar"]}
    cm, cb = r["M_ejekta"]["carpan_1sigma"], r["beta"]["carpan_1sigma"]
    out["M_ejekta_kazanci"] = {
        "carpan_M": cm, "carpan_beta": cb, "kazanc": cb / cm,
        "p_M": r["M_ejekta"]["p"], "sigma_M_bagil": SIGMA_M_BAGIL,
        "esik": OD.ESIK_CARPAN_TANIMLI,
        "genel": ("M_EJEKTA TANIMLAYICI" if cm < OD.ESIK_CARPAN_TANIMLI else
                  "M_EJEKTA KAZANCI KUCUK" if cm < cb / 2.0 else "KAZANC YOK")}
    return out


def _sigma_model_bagil() -> float:
    """`β` paydasının model eksikliği payı — DY2 ile **aynı** terimler."""
    from dartrift.inference.tarih_esleme import model_eksikligi_kaynakli
    return model_eksikligi_kaynakli(1.0, ["gerceklem_beta", "cozunurluk_uzak",
                                          "plato", "carpma_yeri"])["sigma"]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kok", type=Path, required=True)
    ap.add_argument("--json", type=Path, default=None)
    a = ap.parse_args(argv)
    out = yargi(topla(a.kok))
    print("=" * 72)
    print("PROTOKOL DO -- Y0 onselinin DART sahnesinde sinanmasi")
    print("=" * 72)
    for n in out.get("noktalar", []):
        print(f"  Y0 = {n['Y0']:8.1f} Pa   beta = {n['beta']:.4f}   "
              f"M_ejekta = {n['M_ejekta']:.3e}")
    if "p" in out:
        d = out["onsel_denetimi"]
        print(f"  uydurma: {out['uydurma']}   p = {out['p']:+.4f}   "
              f"artik(3 nokta) = {out['artik_uc_nokta']:.3f}")
        print(f"  gozlem beta {BETA_GOZLEM} -> Y0 = {d['Y0_gozlem']:.1f} Pa"
              f"   (onsel {ONSEL_LO:.0e} - {ONSEL_HI:.0e})")
        print(f"  alt kenara {d['dekad_alt_kenara']:+.3f} dekad, "
              f"ust kenara {d['dekad_ust_kenara']:+.3f} dekad")
        print(f"  1 sigma -> Y0 carpani x{d['Y0_carpani_1sigma']:.2f}")
        m = out["M_ejekta_kazanci"]
        print(f"  [M_ejekta] p = {m['p_M']:+.4f}  carpan x{m['carpan_M']:.2f} "
              f"(beta x{m['carpan_beta']:.2f}) -> kazanc {m['kazanc']:.1f} kat"
              f"  :: {m['genel']}")
    print(f"GENEL: {out['genel']}")
    if a.json:
        a.json.write_text(json.dumps(out, indent=1, default=float), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
