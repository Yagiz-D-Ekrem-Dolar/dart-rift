"""TANI — eksende **kaç kez** `phi = esik` kesişiliyor?

## Soru

`krater_yuzey` yüzeyi `phi = 0,5` eş-yüzeyi olarak tanımlar ve **tek bir
kesişim** seçer: `distan` yukarıdan inip ilkini, `icten` (ADR-0063)
içten çıkıp ilkini alır. İki yön de "doğru kesişimi **doğrultuya**
bakarak seçmek" hatasını yapıyor (KAYIT-091 §7). Eksen boyunca
**birden çok** kesişim varsa ikisi de kör seçim yapar.

Bu betik kesişimleri **saymaz değil, sayar**: eksende merkezden dışa
`phi` örneklenir ve `phi`'nin eşiği **aşağı** doğru kestiği her yer
kaydedilir. Böylece "yüzey tek mi, yoksa iç boşluk/ayrı yığın yüzünden
birkaç tane mi" sorusu doğrudan ölçülür.

## KİLİTLİ TAHMİN ve KAPI (koşudan ÖNCE yazıldı — kural 6)

`havuz_krater_tarama_96.csv` üç küme veriyor: `66` çapraz doğrulanmış
(`EVET_*`), `13` tek tanılı (`HAYIR_tek_tani`), `17` okunamayan
(`olculmedi`).

- **H1:** çapraz doğrulanan `66` noktada son durumda eksende **tek**
  aşağı kesişim vardır.
- **H2:** `HAYIR_tek_tani` olan `13` noktada **birden çok** aşağı
  kesişim vardır; `icten`'in okuduğu ilk kesişim gerçek yüzey değildir.

**DENETİM (bu kapı olmadan sonuç okunmaz).** Referans (çarpılmamış)
durum **denetimdir**: oturmuş, kratersiz cisimde eksende kesişim **tek**
olmalıdır. `96` noktanın **en az 90**'ında referans tek kesişim
vermezse tanının kendisi kusurludur; o zaman fizik iddiası
**yazılmaz**, tanı kusuru yazılır.

**AYIRT KAPISI.** Ayırt edicilik `AUC(kesisim_sayisi; 66 vs 13)` ile
ölçülür. `AUC < 0,70` ise **H2 ÇÜRÜTÜLMÜŞ** sayılır ve bu yazılır —
KAYIT-092'deki doluluk hipotezinde olduğu gibi. Eşik şimdi, sonuç
görülmeden kondu.

Kesişim sayısı ayırt ediyorsa düzeltme **yan yana** alan olarak gelir
(`tarama="en_dis"`), varsayılan `distan` **değişmez** ve mühürlü
`uretim66` kaydına **dokunulmaz** (yeni sayı gerekirse yeni etiket).

Kullanım (sıfır GPU, yalnız kayıtlı `npz` okunur):

    python scripts/tani_krater_kesisim_sayisi.py \\
        --kampanya <dizin> --cikti tani_kesisim.json
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from dartrift.cpu_reference.sph_ref import kernel_w  # noqa: E402
from dartrift.inference.design import DART_UZAYI_S4, lhs_design  # noqa: E402

N_NOKTA, TOHUM = 96, 20260906
#: Gercek yogunluk (ADR-0022: gerilmesiz baslangic `2700/alpha0`).
RHO0_KATI = 2700.0
#: `krater_yuzey`in kendi esigi -- burada DEGISTIRILMEZ.
ESIK = 0.5
#: Eksen ornekleme adimi (m); operatorun kullandigi `adim` ile ayni mertebe.
ADIM = 0.25
#: Yuzeyin OTESINE ne kadar bakilir (m). KAYIT-090: eksende kacmamis
#: ejekta 6,50-47,99 m yukseklikte duruyor; 60 m hepsini kapsar.
PAY_M = 60.0
#: Referans denetiminin gecme esigi (docstring'deki DENETIM kapisi).
DENETIM_EN_AZ = 90
#: Ayirt kapisi (docstring'deki AYIRT KAPISI).
AUC_ESIGI = 0.70


def _phi(X, V, h, c0, eksen, zq):
    """`phi(zq) = sum_j V_j W(|p - x_j|, h_j)`, eksen boyunca."""
    d = X - c0[None, :]
    z = d @ eksen
    yan = d - z[:, None] * eksen[None, :]
    yan2 = np.einsum("ij,ij->i", yan, yan)
    dest = 2.0 * h
    sec = (yan2 < dest * dest) & (z > zq[0] - dest.max()) \
        & (z < zq[-1] + dest.max())
    if not np.any(sec):
        return np.full(len(zq), np.nan)
    zs, y2, Vs, hs = z[sec], yan2[sec], V[sec], h[sec]
    dz = zq[:, None] - zs[None, :]
    q = np.sqrt(dz * dz + y2[None, :]) / hs[None, :]
    return kernel_w(q, hs[None, :], 3) @ Vs


def _asagi_kesisimler(zq, f, esik=ESIK):
    """`f`'nin esigi AŞAĞI dogru kestigi yukseklikler (dogrusal arayla)."""
    ust = f >= esik
    gec = np.nonzero(ust[:-1] & ~ust[1:])[0]
    yer = []
    for i in gec:
        f0, f1 = float(f[i]), float(f[i + 1])
        t = 0.0 if f0 == f1 else (f0 - esik) / (f0 - f1)
        yer.append(float(zq[i] + t * (zq[i + 1] - zq[i])))
    return yer


def olc(yol, tasarim):
    d = np.load(yol, allow_pickle=True)
    th = np.asarray(d["theta"], dtype=np.float64).ravel()
    uz = np.max(np.abs(tasarim - th) / np.maximum(np.abs(tasarim), 1e-30),
                axis=1)
    k = int(np.argmin(uz))
    if uz[k] > 1e-9:
        raise SystemExit(f"{os.path.basename(yol)}: theta eslesmedi")

    hedef = np.asarray(d["mermi_kesri"]) < 0.5
    m = np.asarray(d["m"])[hedef]
    h = np.asarray(d["h"])[hedef]
    rho = np.asarray(d["rho"])[hedef]
    a0 = np.asarray(d["alpha0"])[hedef]
    x0 = np.asarray(d["x_referans"])[hedef]
    x = np.asarray(d["x"])[hedef]
    e = np.asarray(d["ehat"], dtype=np.float64)
    eksen = -e / np.linalg.norm(e)
    c0 = (m @ x0) / m.sum()
    R = float(np.max(np.linalg.norm(x0 - c0[None, :], axis=1)))
    zq = np.arange(0.0, R + PAY_M + ADIM, ADIM)

    f_ref = _phi(x0, m / (RHO0_KATI / a0), h, c0, eksen, zq)
    f_son = _phi(x, m / rho, h, c0, eksen, zq)
    kes_ref = _asagi_kesisimler(zq, f_ref)
    kes_son = _asagi_kesisimler(zq, f_son)

    return {
        "kuresel": k, "Y0": float(th[1]),
        "theta": [float(q) for q in th], "R_m": R,
        "REF_n": len(kes_ref), "REF_yerler": kes_ref[:8],
        "SON_n": len(kes_son), "SON_yerler": kes_son[:8],
        # `icten` ILK kesisimi alir, `en_dis` SONuncusunu alirdi:
        "icten_ilk": kes_son[0] if kes_son else None,
        "en_dis_son": kes_son[-1] if kes_son else None,
        "fark_m": (kes_son[-1] - kes_son[0]) if len(kes_son) > 1 else 0.0,
    }


def _auc(pozitif, negatif):
    """Mann-Whitney U / (n*m): baglar 0,5 sayilir."""
    p = np.asarray(pozitif, dtype=float)
    n = np.asarray(negatif, dtype=float)
    if p.size == 0 or n.size == 0:
        return float("nan")
    buyuk = (p[:, None] > n[None, :]).sum()
    bag = (p[:, None] == n[None, :]).sum()
    return float((buyuk + 0.5 * bag) / (p.size * n.size))


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--kampanya", required=True)
    p.add_argument("--tarama-csv", required=True,
                   help="havuz_krater_tarama_96.csv (kume etiketleri)")
    p.add_argument("--cikti", required=True)
    p.add_argument("--beklenen", type=int, default=N_NOKTA)
    a = p.parse_args()

    with open(a.tarama_csv, encoding="utf-8") as fh:
        kume = {int(r["kuresel"]): r["capraz_dogrulandi"]
                for r in csv.DictReader(fh)}
    if len(kume) != a.beklenen:
        raise SystemExit(f"KURAL 8: tarama CSV'de {a.beklenen} BEKLENIYORDU, "
                         f"{len(kume)} var")

    tasarim = np.asarray(lhs_design(DART_UZAYI_S4, N_NOKTA, root_seed=TOHUM),
                         dtype=np.float64)
    desen = os.path.join(a.kampanya, "HAVUZ_g1p0.dilim*_24.durumlar")
    dizinler = sorted(glob.glob(desen))
    if not dizinler:
        raise SystemExit(f"BOSLUK: {desen} hicbir dizine uymadi")

    satirlar, gorulen = [], set()
    for dizin in dizinler:
        for yol in sorted(glob.glob(os.path.join(dizin, "nokta_*.npz"))):
            s = olc(yol, tasarim)
            if s["kuresel"] in gorulen:
                raise SystemExit(f"tekrar eden nokta: {s['kuresel']}")
            gorulen.add(s["kuresel"])
            s["kume"] = kume[s["kuresel"]]
            satirlar.append(s)
    if len(satirlar) != a.beklenen:
        raise SystemExit(f"KURAL 8: {a.beklenen} BEKLENIYORDU, "
                         f"{len(satirlar)} okundu")
    satirlar.sort(key=lambda s: s["kuresel"])

    # --- DENETIM KAPISI: referansta kesisim TEK olmali ------------------
    ref_tek = sum(1 for s in satirlar if s["REF_n"] == 1)
    denetim = ref_tek >= DENETIM_EN_AZ

    iyi = [s for s in satirlar if s["kume"].startswith("EVET")]
    kotu = [s for s in satirlar if s["kume"] == "HAYIR_tek_tani"]
    yok = [s for s in satirlar if s["kume"] == "olculmedi"]
    auc = _auc([s["SON_n"] for s in kotu], [s["SON_n"] for s in iyi])
    ayirt = (not np.isnan(auc)) and auc >= AUC_ESIGI

    ozet = {
        "n": len(satirlar),
        "DENETIM_referans_tek_kesisim": f"{ref_tek}/{len(satirlar)}",
        "DENETIM_gecti": bool(denetim),
        "DENETIM_esigi": DENETIM_EN_AZ,
        "kume_n": {"EVET": len(iyi), "HAYIR_tek_tani": len(kotu),
                   "olculmedi": len(yok)},
        "SON_n_ortanca": {
            "EVET": float(np.median([s["SON_n"] for s in iyi])) if iyi else None,
            "HAYIR_tek_tani": float(np.median([s["SON_n"] for s in kotu]))
            if kotu else None,
            "olculmedi": float(np.median([s["SON_n"] for s in yok]))
            if yok else None,
        },
        "cok_kesisim_orani": {
            "EVET": sum(s["SON_n"] > 1 for s in iyi) / len(iyi) if iyi else None,
            "HAYIR_tek_tani": sum(s["SON_n"] > 1 for s in kotu) / len(kotu)
            if kotu else None,
            "olculmedi": sum(s["SON_n"] > 1 for s in yok) / len(yok)
            if yok else None,
        },
        "AUC_SON_n_kotu_vs_iyi": auc,
        "AUC_esigi": AUC_ESIGI,
        "H2_AYIRT_EDIYOR": bool(ayirt),
        "YARGI": ("TANI KUSURLU -- referans denetimi dustu, fizik iddiasi "
                  "YAZILMAZ" if not denetim else
                  ("H2 DESTEKLENDI: kesisim sayisi ayirt ediyor" if ayirt
                   else "H2 CURUTULDU: kesisim sayisi ayirt ETMIYOR")),
    }

    with open(a.cikti, "w", encoding="utf-8") as fh:
        json.dump({"ozet": ozet, "noktalar": satirlar}, fh, indent=2,
                  ensure_ascii=False)

    print(f"okunan: {len(satirlar)} / {a.beklenen}")
    print(f"DENETIM (referansta TEK kesisim): {ref_tek}/{len(satirlar)} "
          f"-> {'GECTI' if denetim else 'DUSTU'} (esik {DENETIM_EN_AZ})")
    print()
    print("  kume              n   SON_n ortanca   >1 kesisim orani")
    for ad, kms in (("EVET (66)", iyi), ("HAYIR_tek_tani", kotu),
                    ("olculmedi", yok)):
        if not kms:
            continue
        med = float(np.median([s["SON_n"] for s in kms]))
        oran = sum(s["SON_n"] > 1 for s in kms) / len(kms)
        print(f"  {ad:<16} {len(kms):>3}   {med:>13.1f}   {oran:>16.3f}")
    print()
    print(f"AUC(SON_n; HAYIR vs EVET) = {auc:.3f}  (esik {AUC_ESIGI})")
    print(f"YARGI: {ozet['YARGI']}")
    print()
    print("  13 TEK TANILI NOKTA -- kesisimler")
    print(f"  {'idx':>4} {'Y0':>9} {'REF_n':>5} {'SON_n':>5} "
          f"{'icten_ilk':>10} {'en_dis':>10} {'fark_m':>8}")
    for s in kotu:
        il = s["icten_ilk"]
        ed = s["en_dis_son"]
        print(f"  {s['kuresel']:>4} {s['Y0']:>9.2f} {s['REF_n']:>5} "
              f"{s['SON_n']:>5} "
              f"{(f'{il:.2f}' if il is not None else '-'):>10} "
              f"{(f'{ed:.2f}' if ed is not None else '-'):>10} "
              f"{s['fark_m']:>8.2f}")
    print(f"\nyazildi: {a.cikti}")


if __name__ == "__main__":
    main()
