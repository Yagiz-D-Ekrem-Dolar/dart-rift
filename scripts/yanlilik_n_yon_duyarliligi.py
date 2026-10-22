"""Çözünürlük yanlılığı `n_yön`'ü değiştiriyor mu? — **KEŞİF**, yargı değil.

KAYIT-085 iç içe koşunun 7 noktasında `b_ince/b_kaba` oranının 7/7
aynı yönde olduğunu ölçtü (ortanca `%+23,3`). Bu kayma `n_yön = 1`
sonucunu da bozar mı?

Soru iki parçaya ayrılır ve ikisinin cevabı farklı:

1. **Kayma sabit mi, `θ`'ya bağlı mı?** Sabitse Jakobyen satırı sabit
   bir çarpanla ölçeklenir: gradyan **yönleri değişmez**, yalnız öz
   değerler `c²` ile büyür. `θ`'ya bağlıysa gradyanlar **döner** ve
   yargı gerçekten değişebilir.

2. **Döndürme yargıyı eşiğin üstüne taşır mı?** İkinci öz değer `0,82`
   ve eşik `36` --- yani 44 kat yer var.

### Bu bir yargı DEĞİL

ADR-0059'un kilitli kapısı ilk maddesinden düştü (12 nokta istiyordu,
7 var). Dolayısıyla buradaki düzeltme **yayımlanabilir bir sonuç
değildir**; yalnız `n_yön = 1`'in bu kaymaya karşı dayanıklı olup
olmadığını sınar. Eşiğe, ölçüte ya da yargı tablosuna dokunulmaz.

7 noktayla 3 boyutlu bir yüzey öğrenilemez; bu yüzden en basit model
kullanılıyor: `log r = a0 + a·u`. Dört katsayı, yedi nokta. Katsayıların
belirsizliği de raporlanıyor --- küçük örneklem gizlenmiyor.

Kullanım:

    python scripts/yanlilik_n_yon_duyarliligi.py <havuz.csv> \\
        --kampanya <dizin> --json <cikti>
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "src"))

import uretim_posterior as up  # noqa: E402

from dartrift.inference.design import DART_UZAYI_S4, lhs_design  # noqa: E402
from dartrift.inference.tanimlanabilirlik import (  # noqa: E402
    FISHER_ESIGI,
    fisher_yonleri,
    yerel_jakobyen,
)
from dartrift.observables.aday_gozlemliler import (  # noqa: E402
    kacis_hizi_kalibre,
)
from dartrift.observables.beta_gelenegi import (  # noqa: E402
    firlati_dogrultusu,
    gelenek_carpani,
)

#: UP §4'un istedigi bes theta noktasi -- ayni kafes.
U0_NOKTALAR = ((0.50, 0.50, 0.50), (0.25, 0.25, 0.25), (0.75, 0.25, 0.75),
               (0.25, 0.75, 0.75), (0.75, 0.75, 0.25))


def ince_oranlar(kampanya: str, kaba: dict) -> tuple[np.ndarray, np.ndarray]:
    """İnce koşunun tamamlanan noktalarında `b_ince / b_kaba`."""
    idx, oran = [], []
    for dz in sorted(glob.glob(os.path.join(
            kampanya, "HAVUZ_INCE_g1p0.dilim*_96.durumlar"))):
        i = int(re.search(r"dilim(\d+)_96", dz).group(1))
        dosyalar = sorted(glob.glob(os.path.join(dz, "nokta_*.npz")))
        if not dosyalar:
            continue
        d = np.load(dosyalar[0], allow_pickle=True)
        ft = json.loads(str(d["fizik_tani"]))
        ea = ft["ejekta_ayrismasi"]
        mk = np.asarray(d["mermi_kesri"]).ravel()
        ve = kacis_hizi_kalibre(d["v"], d["m"], float(ea["M_kacan"]),
                                mermi_kesri=mk)
        hiz = np.linalg.norm(np.asarray(d["v"]), axis=1)
        E, _ = firlati_dogrultusu(d["v"], d["m"], (~(mk > 0.5)) & (hiz > ve))
        kos_i = float(np.sqrt(1.0 / gelenek_carpani(E, d["ehat"])))
        b_i = (float(ft["beta_hedef"]) - 1.0) / kos_i ** 2
        bk, ck = kaba[i]
        idx.append(i)
        oran.append(b_i / ((bk - 1.0) / ck ** 2))
    return np.array(idx, dtype=int), np.array(oran, dtype=np.float64)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("havuz", type=Path)
    ap.add_argument("--kampanya", required=True)
    ap.add_argument("--json", type=Path, default=None)
    a = ap.parse_args(argv)

    idx, beta, ejf, kos = up.oku(a.havuz)
    kaba = {int(i): (float(b), float(k))
            for i, b, k in zip(idx, beta, kos, strict=True)}
    X = lhs_design(DART_UZAYI_S4, up.N_HAVUZ, root_seed=up.TOHUM)[idx]
    U = DART_UZAYI_S4.to_unit(np.asarray(X, dtype=np.float64))
    katlar = idx % up.KAT_SAYISI

    ince_i, oran = ince_oranlar(a.kampanya, kaba)
    n = ince_i.size
    if n < 4:
        raise SystemExit(f"{n} ince nokta; dogrusal model icin en az 4 gerek")

    # --- 1) Kayma sabit mi, theta'ya bagli mi? ------------------------
    Ui = DART_UZAYI_S4.to_unit(
        np.asarray(lhs_design(DART_UZAYI_S4, up.N_HAVUZ,
                              root_seed=up.TOHUM))[ince_i])
    A = np.column_stack([np.ones(n), Ui])
    y = np.log(oran)
    kats, artik, *_ = np.linalg.lstsq(A, y, rcond=None)
    tahmin = A @ kats
    sse = float(np.sum((y - tahmin) ** 2))
    sd = float(np.sqrt(sse / max(n - A.shape[1], 1)))
    try:
        kov = sd ** 2 * np.linalg.inv(A.T @ A)
        se = np.sqrt(np.diag(kov))
    except np.linalg.LinAlgError:
        se = np.full(A.shape[1], np.nan)
    tdeg = kats / se

    rapor = {
        "KESIF": ("ADR-0059 kapisi 1. maddeden dustu (12 nokta istiyordu, "
                  f"{n} var). Bu bir YARGI DEGIL, dayaniklilik sinavi."),
        "n_ince": int(n), "noktalar": ince_i.tolist(),
        "oran": {"degerler": oran.tolist(),
                 "ortanca": float(np.median(oran)),
                 "ortalama": float(oran.mean()),
                 "sd": float(oran.std(ddof=1))},
        "dogrusal_model": {
            "biçim": "log r = a0 + a1*u_alpha + a2*u_logY0 + a3*u_f",
            "katsayilar": kats.tolist(),
            "standart_hata": se.tolist(),
            "t": tdeg.tolist(),
            "artik_sd": sd,
            "yorum": None,
        },
    }
    egim_anlamli = bool(np.any(np.abs(tdeg[1:]) > 2.0))
    rapor["dogrusal_model"]["yorum"] = (
        "EN AZ BIR EGIM |t| > 2: kayma theta'ya bagli, gradyanlar doner."
        if egim_anlamli else
        "HICBIR EGIM |t| > 2: kayma pratikte SABIT; sabit carpan gradyan "
        "YONLERINI degistirmez, yalniz ozdegerleri c^2 ile olcekler.")

    # --- 2) Duzeltilmis b ile Fisher ---------------------------------
    b_kaba = (beta - 1.0) / kos ** 2
    duzeltme = np.exp(np.column_stack([np.ones(U.shape[0]), U]) @ kats)
    b_duz = b_kaba * duzeltme
    m_model = ejf * up.M_SAHNE

    sonuc = {}
    for ad, bv in (("kaba", b_kaba), ("yanlilik_duzeltilmis", b_duz)):
        gp_b, _ = up.vekil_kur(X, bv, katlar, f"vekil_{ad}", sonuc)
        gp_m, _ = up.vekil_kur(X, np.log(m_model), katlar, f"vekilM_{ad}",
                               sonuc)

        def ileri(u, _b=gp_b, _m=gp_m):
            uu = np.atleast_2d(u)
            return np.column_stack([_b.predict_u(uu)[0],
                                    _m.predict_u(uu)[0]])[0]

        oz, nyon = [], []
        for u0 in U0_NOKTALAR:
            J = yerel_jakobyen(ileri, np.asarray(u0, dtype=np.float64))
            sdv = np.array([bv.std(ddof=1), np.log(m_model).std(ddof=1)])
            kovm = np.diag(sdv ** 2)
            f = fisher_yonleri(J, kovm)
            oz.append([float(x) for x in f["ozdegerler"]])
            nyon.append(int(f["ogrenilen_yon_sayisi"]))
        sonuc[ad] = {"ozdegerler": oz, "n_yon": nyon,
                     "en_kucuk_n_yon": int(min(nyon))}

    rapor["fisher"] = {k: v for k, v in sonuc.items()
                       if k in ("kaba", "yanlilik_duzeltilmis")}
    rapor["fisher_esigi"] = FISHER_ESIGI

    print("=" * 70)
    print("KESIF: cozunurluk yanliligi n_yon'u degistiriyor mu?")
    print("=" * 70)
    print(rapor["KESIF"])
    print()
    print(f"oran: n={n}  ortanca {np.median(oran):.4f}  sd {oran.std(ddof=1):.4f}")
    print()
    print("log r = a0 + a*u  dogrusal modeli:")
    adlar = ["a0 (sabit)", "a1 (alpha_b)", "a2 (log Y0)", "a3 (f)"]
    for ad_, k_, s_, t_ in zip(adlar, kats, se, tdeg, strict=True):
        print(f"   {ad_:14s} {k_:+.4f}  +- {s_:.4f}   t = {t_:+.2f}")
    print(f"   artik sd {sd:.4f}")
    print(f"   -> {rapor['dogrusal_model']['yorum']}")
    print()
    print(f"--- Fisher (esik {FISHER_ESIGI}) ---")
    for ad in ("kaba", "yanlilik_duzeltilmis"):
        v = sonuc[ad]
        ikinci = [o[1] for o in v["ozdegerler"]]
        print(f"   {ad:22s} n_yon {v['n_yon']}  en kucuk {v['en_kucuk_n_yon']}")
        print(f"   {'':22s} ikinci ozdegerler: "
              + ", ".join(f"{x:.2f}" for x in ikinci))
    ayni = (sonuc["kaba"]["en_kucuk_n_yon"]
            == sonuc["yanlilik_duzeltilmis"]["en_kucuk_n_yon"])
    print()
    print("SONUC: n_yon " + ("DEGISMIYOR" if ayni else "DEGISIYOR"))
    print("=" * 70)

    if a.json:
        a.json.write_text(json.dumps(rapor, indent=1, ensure_ascii=False,
                                     default=float), encoding="utf-8")
        print(f"yazildi: {a.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
