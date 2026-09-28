#!/usr/bin/env python
"""PROTOKOL-A98K raporu — kontrollü kazı akışında AV ve çözünürlük (KİLİTLİ).

Kurallar `docs/truba/PROTOKOL-A98K-KAZI-AKISI.md`'de, koşulardan ÖNCE yazıldı.
Bu betik yalnız okur: `--kok` altındaki `<ad>.json` dosyalarını (a98k_kazi_akisi
çıktısı) bekler; **beklenen** her kolu sayar (eksik kol sessiz geçmez, A84/A88).

    python scripts/a98k_raporu.py --kok a98k_sonuc --json S_A98K.json
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

#: Beklenen kollar: (ad, s, kol). kol: av1 = varsayilan AV (1, 2);
#: av01 = gec AV (0,1 ; 0,2); av0 = AV yok; av01L = av01 + A101 (tr L).
ARALIKLAR = (("1", 1.0), ("0p5", 0.5), ("0p25", 0.25))
KOL_TURLERI = ("av1", "av01", "av0", "av01L")
KOLLAR = tuple((f"K_s{e}_{k}", s, k) for k in KOL_TURLERI for e, s in ARALIKLAR)

GOZLENEBILIR = "P_up_v0.1"   # |v| > 0,1 V0 ile yuzeyin ustunde yukari momentum
MOMENTUM_ESIGI = 1.0e-6      # G0: toplam momentum bagil sapmasi
K1_ESIK = 0.10               # varsayilan AV'de kaba-ince bagil fark
K3_ORAN = 1.0 / 3.0          # cozum: D_01 <= D_1 / 3
K4_ARALIK = (0.5, 1.5)       # gozlenen yakinsama mertebesi (AV ∝ h -> ~1)
K5_NN_MIN = 0.3              # en yakin komsu / s, alt sinir
K5_KESIR = 0.01              # nn < 0,5 s olan parcacik kesri, ust sinir
K2_ESIK = 0.5                # AV payi E_av / (E_av + W_pl)


def oku(kok: Path) -> dict:
    """Her beklenen kol için sonuç ya da `None` (eksik/geçersiz) ve neden."""
    out = {}
    for ad, s, kol in KOLLAR:
        yol = kok / f"{ad}.json"
        if not yol.exists():
            out[ad] = {"var": False, "neden": "dosya yok"}
            continue
        r = json.loads(yol.read_text(encoding="utf-8"))
        neden = None
        beklenen_av = {"av1": [1.0, 2.0], "av01": [0.1, 0.2], "av0": [0.0, 0.0],
                       "av01L": [0.1, 0.2]}[kol]
        beklenen_sur = "trL" if kol == "av01L" else "sph"
        if not r.get("sonlu", False):
            neden = "sonlu degil"
        elif abs(float(r["s"]) - s) > 1e-12:
            neden = f"s {r['s']} != {s}"
        elif [float(t) for t in r["av"]] != beklenen_av:
            neden = f"av {r['av']} != {beklenen_av}"
        elif r.get("sureklilik", "sph") != beklenen_sur:
            neden = f"sureklilik {r.get('sureklilik')} != {beklenen_sur}"
        elif not (float(r["momentum_bagil_sapma"]) <= MOMENTUM_ESIGI):
            neden = f"momentum sapmasi {r['momentum_bagil_sapma']:.2e}"
        if neden:
            out[ad] = {"var": False, "neden": neden}
        else:
            out[ad] = {"var": True, "Q": float(r[GOZLENEBILIR]), "r": r}
    return out


def _fark(q_kaba: float, q_ince: float) -> float:
    if not (math.isfinite(q_kaba) and math.isfinite(q_ince)) or q_ince == 0.0:
        return float("nan")
    return abs(q_kaba - q_ince) / abs(q_ince)


def _seri(sonuc: dict, kol: str) -> list:
    """Kolun üç aralıktaki Q'su (eksikse nan)."""
    return [sonuc[f"K_s{e}_{kol}"]["Q"] if sonuc[f"K_s{e}_{kol}"]["var"]
            else float("nan") for e, _ in ARALIKLAR]


def _mertebe(q: list) -> float:
    a, b = q[0] - q[1], q[1] - q[2]
    if not all(math.isfinite(t) for t in q) or a == 0.0 or b == 0.0 or a * b < 0:
        return float("nan")
    return math.log2(abs(a) / abs(b))


def yargila(sonuc: dict) -> dict:
    """Kilitli yargılar (PROTOKOL-A98K §4)."""
    eksik = [ad for ad, d in sonuc.items() if not d["var"]]
    q1, q01, q0, q01L = (_seri(sonuc, k) for k in KOL_TURLERI)
    D = {k: _fark(q[0], q[2]) for k, q in
         (("av1", q1), ("av01", q01), ("av0", q0), ("av01L", q01L))}
    y: dict = {"beklenen": len(KOLLAR), "bulunan": len(KOLLAR) - len(eksik),
               "eksik": {ad: sonuc[ad]["neden"] for ad in eksik},
               "Q": {"av1": q1, "av01": q01, "av0": q0, "av01L": q01L},
               "D": D}

    # K1 -- varsayilan AV'de cozunurluk bagimliligi uretildi mi
    if not math.isfinite(D["av1"]):
        y["K1"] = "OKUNMAZ"
    else:
        monoton = q1[0] < q1[1] < q1[2]
        y["K1_monoton"] = bool(monoton)
        y["K1"] = ("VARSAYILAN AV'DE COZUNURLUK BAGIMLILIGI VAR"
                   if (D["av1"] >= K1_ESIK and monoton) else
                   "VARSAYILAN AV'DE COZUNURLUK BAGIMLILIGI URETILMEDI")

    # K2 -- AV payi (varsayilan AV, kaba ve ince)
    paylar = {}
    for e, _ in ARALIKLAR:
        d = sonuc[f"K_s{e}_av1"]
        paylar[e] = float(d["r"]["av_payi"]) if d["var"] else float("nan")
    y["K2_av_payi"] = paylar
    y["K2"] = ("OKUNMAZ" if not math.isfinite(paylar["1"]) else
               "AV KABADA BASKIN" if paylar["1"] >= K2_ESIK else
               "AV KABADA IKINCIL")

    # K3 -- ANA YARGI: gec AV kucultme cozunurluk bagimliligini kaldiriyor mu
    if not (math.isfinite(D["av1"]) and math.isfinite(D["av01"])):
        y["K3"] = "OKUNMAZ"
    elif D["av01"] <= K3_ORAN * D["av1"]:
        y["K3"] = "GEC AV KUCULTME COZUNURLUK BAGIMLILIGINI BUYUK OLCUDE KALDIRIYOR"
    elif D["av01"] < D["av1"]:
        y["K3"] = "GEC AV KUCULTME COZUNURLUK BAGIMLILIGINI KISMEN KALDIRIYOR"
    else:
        y["K3"] = "GEC AV KUCULTME COZUNURLUK BAGIMLILIGINI KALDIRMIYOR"

    # K4 -- varsayilan AV'de gozlenen mertebe
    p = _mertebe(q1)
    y["K4_p"] = p
    y["K4"] = ("OKUNMAZ" if not math.isfinite(p) else
               "BIRINCI MERTEBE (AV ∝ h ILE TUTARLI)"
               if K4_ARALIK[0] <= p <= K4_ARALIK[1] else
               "BIRINCI MERTEBE DEGIL")

    # K5 -- dusuk AV'de ic ice gecme (cozumun yan etkisi)
    saglik = {}
    for kol in ("av01", "av0", "av01L"):
        for e, _ in ARALIKLAR:
            d = sonuc[f"K_s{e}_{kol}"]
            if d["var"]:
                sg = d["r"]["saglik"]
                saglik[f"{kol}_s{e}"] = {
                    "nn_min": sg["nn_min"], "kesir_nn_lt_0p5": sg["kesir_nn_lt_0p5"],
                    "gecti": bool(sg["nn_min"] >= K5_NN_MIN
                                  and sg["kesir_nn_lt_0p5"] <= K5_KESIR)}
    y["K5_ayrinti"] = saglik
    av01_saglik = [v["gecti"] for k, v in saglik.items() if k.startswith("av01_")]
    y["K5"] = ("OKUNMAZ" if len(av01_saglik) < len(ARALIKLAR) else
               "AV 0,1'DE IC ICE GECME YOK" if all(av01_saglik) else
               "AV 0,1'DE IC ICE GECME VAR")

    # K6 -- A101 (tr L) cozum paketine zarar veriyor mu
    if not (math.isfinite(D["av01"]) and math.isfinite(D["av01L"])):
        y["K6"] = "OKUNMAZ"
    else:
        y["K6"] = ("A101 COZUNURLUK FARKINI BUYUTMUYOR" if D["av01L"] <= D["av01"]
                   else "A101 COZUNURLUK FARKINI BUYUTUYOR")
    y["genel"] = y["K3"]
    return y


def _yaz(satir: str) -> None:
    """ASCII olmayan karakter konsolda yazılamazsa raporu **düşürme**.

    K4 yargısı `AV ∝ h` içeriyor; Windows konsolu (cp1254) bunu kodlayamıyor
    ve rapor `UnicodeEncodeError` ile çöküyordu — yargı doğru hesaplanmış
    olsa bile. JSON her zaman `utf-8` yazılır; burada yalnız **ekran** çıktısı
    sadeleşir. (Kilitli yargı metinleri değişmez.)
    """
    try:
        print(satir)
    except UnicodeEncodeError:
        print(satir.encode("ascii", "replace").decode("ascii"))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--kok", required=True)
    ap.add_argument("--json", default=None)
    a = ap.parse_args(argv)
    y = yargila(oku(Path(a.kok)))
    _yaz(f"PROTOKOL-A98K  bulunan {y['bulunan']}/{y['beklenen']}")
    for ad, n in y["eksik"].items():
        _yaz(f"  EKSIK {ad}: {n}")
    for k, q in y["Q"].items():
        _yaz(f"  {k:>6}: Q(s=1, 0,5, 0,25) = " +
             ", ".join(f"{t:.5e}" for t in q) + f"   D = {y['D'][k]:.4f}")
    for k in ("K1", "K2", "K3", "K4", "K5", "K6"):
        _yaz(f"  {k}: {y[k]}")
    _yaz(f"  K2 AV payi: {y['K2_av_payi']}   K4 p = {y['K4_p']:.3f}")
    _yaz(f"  GENEL: {y['genel']}")
    if a.json:
        out = Path(a.json)
        if out.exists():
            raise SystemExit(f"{out} zaten var (uzerine yazilmaz)")
        out.write_text(json.dumps(y, indent=1, ensure_ascii=False),
                       encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
