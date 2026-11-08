"""ÇOK DOĞRULUKLU DÜZELTME — A116'nın kapatılması.

`src/dartrift/inference/cok_dogruluk.py` yazılmış, belgelenmiş ve
sınavlanmıştı; **hiçbir üretim yolundan çağrılmıyordu** (A116: *"yazılmış
ama bağlanmamış modül"*). Bu betik o bağlantıyı kurar: ince koşuların
`441` GPU saatlik verisi ilk kez bir sonuca dönüşür.

## Ne yapar

İki katman:

- **kaba** — üretim havuzu, `96` nokta, taban aralık `7,0 m`
- **orta** — aynı tasarımın ince koşulan alt kümesi, taban aralık `3,5 m`

Kennedy–O'Hagan AR(1):

    y_orta(x) = ρ · f_kaba(x) + δ(x)

`ρ` ızgarada aranır, `δ` fark GP'sidir. Sonuç, kaba havuzun tamamını
orta çözünürlüğe **düzeltilmiş** bir vekildir.

## Niçin gerekli — bir cümlede

`σ` yolu çözünürlük farkını posteriorun **genişliğine** katar ama
merkezini kaba öngörüde bırakır. Fark sistematik bir kaymaysa `θ` o
kaymayı **emmek zorunda kalır**: yanlış bir iç yapıya, doğru bir `β`
ürettiği için inanırız (ADR-0059 §2).

## KAPI — ADR-0059 §3.4'ten BİREBİR, burada seçilmedi

| kapı | eşik |
|---|---|
| tasarım iç içe | ince noktalar `96`'nın **alt kümesi** |
| `ρ` ızgara kenarında değil | `cok_dogruluk`'un uyarı alanı **boş** |
| ince noktalarda dışarıda-bırak-bir | `E_CD < E_SIGMA` |

ADR-0059 dördüncü bir madde daha sayıyor (*"iki yolun kipleri ayrılıyorsa
ikisi de manşette"*); o, tam posterioru iki yolla koşmayı gerektirir ve
bu betiğin kapsamı dışındadır. Bu betik **ilk üç maddeyi** ölçer ve
dördüncüsünü `OLCULMEDI` diye bildirir — geçmiş saymaz.

**Dördü de geçmeden manşet `CD` olamaz.** Bu betik hiçbir koşulda
"manşet CD" demez; yalnız kapının durumunu raporlar.

## `E_SIGMA` nedir

`σ` yolunun ince noktalardaki öngörüsü, kaba GP'nin kendi öngörüsüdür —
o yol ince veriyi hiç kullanmaz. `E_CD` ise CD vekilinin
**dışarıda-bırak-bir** hatasıdır: her ince nokta sırayla çıkarılır, CD
kalan noktalarla yeniden uydurulur ve çıkarılan noktada öngörü alınır.
İkisi aynı hedefe (`ince β`) karşı ölçülür.

Kullanım (sıfır GPU):

    python scripts/cd_duzeltme.py --cikti docs/sonuclar/cd_duzeltme.json
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from dartrift.inference.cok_dogruluk import (  # noqa: E402
    RHO_IZGARASI,
    cok_dogruluk_uydur,
)
from dartrift.inference.design import DART_UZAYI_S4, lhs_design  # noqa: E402
from dartrift.inference.gp_vekil import gp_uydur  # noqa: E402

N_NOKTA, TOHUM = 96, 20260906
HAVUZ = "docs/sonuclar/havuz_posterior_girdi.csv"
INCE = "docs/sonuclar/ince/ince_96.csv"


def _oku(yol: str, anahtar: str) -> dict:
    with open(yol, encoding="utf-8") as f:
        return {int(s["idx"]): float(s[anahtar]) for s in csv.DictReader(f)
                if s[anahtar] != ""}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--cikti", required=True)
    p.add_argument("--havuz", default=HAVUZ)
    p.add_argument("--ince", default=INCE)
    a = p.parse_args()

    tasarim = np.asarray(lhs_design(DART_UZAYI_S4, N_NOKTA, root_seed=TOHUM),
                         dtype=np.float64)
    kaba = _oku(a.havuz, "beta")
    ince = _oku(a.ince, "beta")
    if len(kaba) != N_NOKTA:
        raise SystemExit(f"KURAL 8: havuzda {N_NOKTA} beklenir, {len(kaba)}")
    eksik = sorted(set(ince) - set(kaba))
    if eksik:
        raise SystemExit(f"ince noktalar havuzda yok: {eksik}")

    idx_i = sorted(ince)
    x_kaba = tasarim
    y_kaba = np.array([kaba[i] for i in range(N_NOKTA)], dtype=np.float64)
    x_orta = tasarim[idx_i]
    y_orta = np.array([ince[i] for i in idx_i], dtype=np.float64)

    # --- 0. ham fark: yanlilik mi sacilma mi -------------------------
    fark = y_orta - y_kaba[idx_i]
    oran = y_orta / y_kaba[idx_i]
    ayni_yon = int(np.sum(fark > 0))
    # Tek tarafli isaret sinavi: hepsi ayni yonde ise p = 2^-n.
    p_isaret = 2.0 ** (-len(fark)) if ayni_yon in (0, len(fark)) else None

    # --- 1. CD uydur --------------------------------------------------
    vekil = cok_dogruluk_uydur(DART_UZAYI_S4, x_kaba, y_kaba, x_orta, y_orta)

    # --- 2. KAPI ------------------------------------------------------
    ic_ice = all(
        bool(np.any(np.all(np.isclose(x_kaba, xo[None, :], rtol=0.0,
                                      atol=1e-12), axis=1)))
        for xo in x_orta)

    kenar = float(vekil.rho) in (float(min(RHO_IZGARASI)),
                                 float(max(RHO_IZGARASI)))
    rho_temiz = (not vekil.uyarilar) and not kenar

    # Disarida-birak-bir. SIGMA yolu ince veriyi KULLANMAZ, o yuzden
    # kaba GP bir kez uydurulur ve hepsinde ayni kalir.
    kaba_gp = gp_uydur(DART_UZAYI_S4, x_kaba, y_kaba)
    e_sigma = np.abs(np.asarray(kaba_gp.predict(x_orta)).ravel() - y_orta)

    e_cd = np.empty(len(idx_i), dtype=np.float64)
    for j in range(len(idx_i)):
        tut = np.ones(len(idx_i), dtype=bool)
        tut[j] = False
        v = cok_dogruluk_uydur(DART_UZAYI_S4, x_kaba, y_kaba,
                               x_orta[tut], y_orta[tut])
        e_cd[j] = abs(float(np.asarray(v.predict(x_orta[j:j + 1])).ravel()[0])
                      - y_orta[j])

    E_CD, E_SIGMA = float(np.sqrt(np.mean(e_cd ** 2))), float(
        np.sqrt(np.mean(e_sigma ** 2)))
    loo_gecti = E_CD < E_SIGMA

    kapi = {
        "tasarim_ic_ice": ic_ice,
        "rho_izgara_kenarinda_degil": rho_temiz,
        "loo_E_CD_kucuk": loo_gecti,
        "iki_yolun_kipleri": "OLCULMEDI (tam posterior gerekir, ADR-0059 §3.4)",
    }
    uc_gecti = ic_ice and rho_temiz and loo_gecti

    yargi = ("ILK UC KAPI GECTI; dorduncu (iki yolun kipleri) OLCULMEDI. "
             "ADR-0059 dordunu birden ister -> manset hala SIGMA, CD 'kesif'."
             if uc_gecti else
             "KAPI DUSTU -> manset SIGMA, CD 'kesif' etiketiyle ek.")

    # --- 3. duzeltilmis havuz ----------------------------------------
    y_cd = np.asarray(vekil.predict(x_kaba), dtype=np.float64).ravel()

    kayit = {
        "NE": "Cok dogruluklu (Kennedy-O'Hagan AR(1)) cozunurluk duzeltmesi.",
        "girdi": {"havuz": a.havuz, "n_kaba": N_NOKTA,
                  "ince": a.ince, "n_orta": len(idx_i),
                  "ince_idx": idx_i, "tohum": TOHUM},
        "ham_fark": {
            "NOT": "ince beta eksi kaba beta, ayni theta noktasinda.",
            "ayni_yonde": f"{ayni_yon}/{len(fark)}",
            "p_isaret_sinavi_tek_tarafli": p_isaret,
            "fark_min": float(fark.min()), "fark_maks": float(fark.max()),
            "fark_ortanca": float(np.median(fark)),
            "oran_ortanca": float(np.median(oran)),
            "oran_min": float(oran.min()), "oran_maks": float(oran.max()),
            "nokta": {str(i): {"kaba": float(kaba[i]), "ince": float(ince[i]),
                               "fark": float(ince[i] - kaba[i])}
                      for i in idx_i},
        },
        "cd": {
            "rho": float(vekil.rho),
            "rho_izgara": [float(r) for r in (min(RHO_IZGARASI),
                                              max(RHO_IZGARASI))],
            "uyarilar": list(vekil.uyarilar),
        },
        "loo": {
            "E_CD_rms": E_CD, "E_SIGMA_rms": E_SIGMA,
            "iyilesme_orani": (E_SIGMA / E_CD) if E_CD > 0 else None,
            "nokta_basina": {str(i): {"e_cd": float(c), "e_sigma": float(s)}
                             for i, c, s in zip(idx_i, e_cd, e_sigma,
                                                strict=True)},
        },
        "KAPI": kapi,
        "YARGI": yargi,
        "duzeltilmis_beta": {str(i): float(v) for i, v in enumerate(y_cd)},
        "NOT": ("Kapi ADR-0059 §3.4'ten BIREBIR alindi, burada secilmedi. "
                "Dorduncu madde olculmedi ve GECMIS SAYILMADI."),
    }
    with open(a.cikti, "w", encoding="utf-8") as f:
        json.dump(kayit, f, indent=2, ensure_ascii=False)

    # ------------------------------------------------------------------
    print("=" * 70)
    print("COK DOGRULUKLU DUZELTME  (A116 kapatiliyor)")
    print("=" * 70)
    print(f"kaba: {N_NOKTA} nokta   orta (ince): {len(idx_i)} nokta "
          f"-> {idx_i}")
    print()
    print("HAM FARK (ince - kaba, ayni theta):")
    print(f"  ayni yonde      : {ayni_yon}/{len(fark)}"
          + (f"   p = {p_isaret:.5f} (tek tarafli isaret sinavi)"
             if p_isaret else ""))
    print(f"  fark            : {fark.min():+.4f} .. {fark.max():+.4f}   "
          f"ortanca {np.median(fark):+.4f}")
    print(f"  oran ince/kaba  : {oran.min():.3f} .. {oran.max():.3f}   "
          f"ortanca {np.median(oran):.3f}")
    print()
    print(f"rho = {vekil.rho:.4f}   (izgara {min(RHO_IZGARASI)}"
          f" .. {max(RHO_IZGARASI)})")
    if vekil.uyarilar:
        for u in vekil.uyarilar:
            print(f"  UYARI: {u}")
    print()
    print("DISARIDA-BIRAK-BIR (ince noktalarda, hedef = ince beta):")
    print(f"  E_SIGMA (rms) = {E_SIGMA:.4f}   <- kaba GP, ince veriyi "
          f"kullanmaz")
    print(f"  E_CD    (rms) = {E_CD:.4f}")
    if E_CD > 0:
        print(f"  iyilesme      = {E_SIGMA / E_CD:.2f} kat")
    print()
    print("KAPI (ADR-0059 §3.4):")
    for k, v in kapi.items():
        print(f"  {k:32s} {v}")
    print()
    print(f"YARGI: {yargi}")
    print(f"\nyazildi: {a.cikti}")


if __name__ == "__main__":
    main()
