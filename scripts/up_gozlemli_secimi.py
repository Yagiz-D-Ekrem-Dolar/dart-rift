"""PROTOKOL-UP §3/§4 koşucusu — gözlenebilir seçimi ve `n_yön`.

Protokol 2026-10-08'de, havuzdan **hiçbir nokta görülmeden** yazıldı. Bu
betik o protokolü *uygular*; ölçüt, eşik ve yargı tablosu burada
**tanımlanmaz** — hepsi `inference/gozlemli_secimi.py` ve
`inference/tanimlanabilirlik.py` içinde zaten kilitli
(`FISHER_ESIGI = 36`). Betik yalnız veriyi o fonksiyonlara taşır.

İki aşama, bilerek ayrı:

**A. σ'dan bağımsız geometri.** Fisher öz değerleri `1/σ²` ile ölçeklenir,
dolayısıyla "kaç yön eşiği geçti" sorusu σ seçimine bağlıdır. Ama
gradyanların *aralarındaki açı* σ'dan bağımsızdır. `e_hiz` gerçekten yeni
bir yön taşıyor mu sorusunun σ'sız cevabı budur ve önce o ölçülür.

**B. Yargı.** `secim_raporu`, PROTOKOL-UP §4'ün istediği gibi `ρ ∈
{0; 0,4; 0,8}` için üç kez ve en az beş `θ` noktasında koşulur; farklı
çıkarsa **en küçük** `n_yön` alınır (kiraz toplamamak için).

`e_hiz`'in kilitli bir ölçüm belirsizliği **yok** (`ADAYLAR` kütüğü:
"karşılığı var, sayısı henüz yok"). Havuzu gördükten sonra ona bir σ
uydurmak ön kayıt olmaz; bu yüzden B aşaması σ'yı serbest bırakıp
**ikinci yönün hangi σ'da doğduğunu** verir. Tek bir yes/no yerine
nicel bir gereksinim: "`e_hiz` şu kesinlikte ölçülürse ikinci yön açılır."

Kullanım (TRUBA, sıfır GPU):

    python scripts/up_gozlemli_secimi.py --kampanya <dizin> --cikti <json>
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from dartrift.inference.design import DART_UZAYI_S4, lhs_design  # noqa: E402
from dartrift.inference.gozlemli_secimi import (  # noqa: E402
    aday_jakobyeni,
    secim_raporu,
)
from dartrift.observables.aday_gozlemliler import (  # noqa: E402
    ADAYLAR,
    aday_hesapla,
    kacis_hizi_kalibre,
    tum_adaylar,
)

#: Havuz tasarımı — PROTOKOL-HAVUZ §3 ile aynı çağrı.
N_NOKTA = 96
TOHUM = 20260906

#: §4'ün istediği kovaryans taraması.
RHO_TARAMA = (0.0, 0.4, 0.8)

#: §4: Jakobyen en az beş `θ`'da. Birim küpte merkez + dört köşe bölgesi.
U0_NOKTALAR = (
    (0.50, 0.50, 0.50),
    (0.25, 0.25, 0.25),
    (0.75, 0.25, 0.75),
    (0.25, 0.75, 0.75),
    (0.75, 0.75, 0.25),
)


def durumlari_oku(kampanya: str) -> tuple[list[dict], list[int]]:
    """Her `.durumlar` dizinindeki `npz`'den aday sözlüğü üretir."""
    kayitlar: list[tuple[int, dict]] = []
    desen = os.path.join(kampanya, "HAVUZ_g1p0.dilim*_24.durumlar")
    for dizin in sorted(glob.glob(desen)):
        m = re.search(r"dilim(\d+)_24", dizin)
        if not m:
            raise ValueError(f"dilim numarasi okunamadi: {dizin}")
        dilim = int(m.group(1))
        for yol in sorted(glob.glob(os.path.join(dizin, "nokta_*.npz"))):
            d = np.load(yol, allow_pickle=True)
            i_ic = int(re.search(r"nokta_(\d+)_", os.path.basename(yol)).group(1))
            kuresel = dilim + 24 * i_ic
            ft = d["fizik_tani"].item() if "fizik_tani" in d else {}
            ea = ft.get("ejekta_ayrismasi", {})
            m_kacan = float(ea["M_kacan"])
            mk = d["mermi_kesri"] if "mermi_kesri" in d else None
            v_esc = kacis_hizi_kalibre(d["v"], d["m"], m_kacan, mermi_kesri=mk)
            aday = aday_hesapla(d["v"], d["m"], ehat=d["ehat"], v_esc=v_esc,
                                mermi_kesri=mk,
                                beta=float(ft["beta_hedef"]))
            # Tutarlilik kapisi (UP §2): kosunun kendi defteriyle ayni mi.
            bagil = abs(aday["M_kacan"] - m_kacan) / max(abs(m_kacan), 1e-30)
            if bagil > 1e-6:
                raise SystemExit(
                    f"TUTARSIZ nokta {kuresel}: M_kacan cevrimdisi "
                    f"{aday['M_kacan']:.6e} vs kosudan {m_kacan:.6e} "
                    f"(bagil {bagil:.2e} > 1e-6). Sessiz duzeltme yasak.")
            kayitlar.append((kuresel, aday))
    kayitlar.sort(key=lambda t: t[0])
    return [a for _, a in kayitlar], [g for g, _ in kayitlar]


def ana() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kampanya", required=True)
    ap.add_argument("--cikti", required=True)
    a = ap.parse_args()

    durumlar, kuresel = durumlari_oku(a.kampanya)
    if len(durumlar) != N_NOKTA:
        raise SystemExit(f"{len(durumlar)} nokta okundu, {N_NOKTA} bekleniyordu "
                         "(kural 8: eksik kampanya sessiz gecmez)")
    if kuresel != list(range(N_NOKTA)):
        raise SystemExit("kuresel indeksler 0..95 degil")

    Y = tum_adaylar(durumlar)
    eksik = float(np.sum(Y["eksik_sayisi"]))
    X = np.asarray(lhs_design(DART_UZAYI_S4, N_NOKTA, root_seed=TOHUM),
                   dtype=np.float64)

    # Kapi A: yalniz gozlenen adaylar posteriora girebilir.
    gozlenen = [c for c in ADAYLAR if c.gozlenen]
    adlar = [c.ad for c in gozlenen]
    log_al = {c.ad: bool(getattr(c, "log_al", False)) for c in gozlenen}
    gruplar = {c.ad: c.karsilik_grubu for c in gozlenen}

    rapor: dict = {
        "protokol": "PROTOKOL-UP §3/§4",
        "nokta": N_NOKTA, "tohum": TOHUM, "eksik_alan": eksik,
        "gozlenen_adaylar": adlar, "gruplar": gruplar,
        "kuresel_indeks_tam": True,
    }

    # ---------------- A. sigma'dan bagimsiz geometri ----------------
    geo = []
    for u0 in U0_NOKTALAR:
        J, jadlar = aday_jakobyeni(DART_UZAYI_S4, X, Y, u0, adlar=adlar,
                                   log_al=log_al)
        birim = J / np.linalg.norm(J, axis=1, keepdims=True)
        aci = {}
        for i in range(len(jadlar)):
            for j in range(i + 1, len(jadlar)):
                kos = float(np.clip(birim[i] @ birim[j], -1.0, 1.0))
                aci[f"{jadlar[i]}~{jadlar[j]}"] = {
                    "kosinus": kos,
                    "aci_derece": float(np.degrees(np.arccos(abs(kos)))),
                }
        tekil = np.linalg.svd(birim, compute_uv=False)
        geo.append({
            "u0": list(u0), "adlar": jadlar, "aci": aci,
            "tekil_degerler": tekil.tolist(),
            "kosul_sayisi": float(tekil[0] / max(tekil[-1], 1e-300)),
            "sayisal_rank": int(np.sum(tekil > tekil[0] * 1e-10)),
        })
    rapor["A_geometri"] = geo

    # ---------------- B. yargi, sigma taramasi ----------------
    # beta: sigma_model (tarih_esleme) ; M_kacan: L17 0,3/1,6 dex'e cevrilmis.
    # e_hiz: KILITLI DEGERI YOK -> serbest birakilir.
    from dartrift.inference.tarih_esleme import model_eksikligi_kaynakli
    URETIM = ["gerceklem_beta_DART", "cozunurluk_uzak", "cozunurluk_yakin",
              "plato_olculen_DART", "hedef_sekli_olculen", "carpma_yeri_olculen"]
    s_beta = float(model_eksikligi_kaynakli(1.0, URETIM)["sigma"]) * 3.5418
    s_mkacan = 0.3 / 1.6 / np.log(10.0)          # dex, log10 vekili icin
    taban = {"beta": s_beta, "M_kacan": float(s_mkacan)}

    # `e_hiz` sigma'sini serbest tarayip ikinci yonun dogdugu esigi bul.
    def yargi(s_ehiz: float, rho: float, u0) -> dict:
        J, ja = aday_jakobyeni(DART_UZAYI_S4, X, Y, u0, adlar=adlar,
                               log_al=log_al)
        s = np.array([taban.get(ad, s_ehiz) for ad in ja], dtype=np.float64)
        R = np.full((len(s), len(s)), float(rho))
        np.fill_diagonal(R, 1.0)
        kov = np.outer(s, s) * R
        return secim_raporu(gozlenen, J, kov, d_parametre=3)

    tarama = []
    for ue in np.logspace(-3, 1, 41):
        r = yargi(float(ue), 0.0, U0_NOKTALAR[0])
        tarama.append({"sigma_e_hiz": float(ue),
                       "ogrenilen": int(r.get("ogrenilen", 0)),
                       "ozdegerler": r.get("ozdegerler")})
    ikinci = [t for t in tarama if t["ogrenilen"] >= 2]
    rapor["B_sigma_taramasi"] = {
        "taban_sigma": taban,
        "e_hiz_sigma_araligi": [1e-3, 1e1],
        "ikinci_yon_icin_gereken_en_buyuk_sigma":
            (max(t["sigma_e_hiz"] for t in ikinci) if ikinci else None),
        "tarama": tarama,
    }

    # §4: uc rho x bes u0, EN KUCUK n_yon alinir.
    ref = (max(t["sigma_e_hiz"] for t in ikinci) if ikinci else 1.0)
    kafes = []
    for rho in RHO_TARAMA:
        for u0 in U0_NOKTALAR:
            r = yargi(ref, rho, u0)
            kafes.append({"rho": rho, "u0": list(u0),
                          "ogrenilen": int(r.get("ogrenilen", 0)),
                          "genel": r.get("genel"),
                          "ozdegerler": r.get("ozdegerler"),
                          "secilen": r.get("secilen")})
    enk = min(k["ogrenilen"] for k in kafes)
    rapor["C_kafes"] = {
        "referans_sigma_e_hiz": ref,
        "kafes": kafes,
        "en_kucuk_n_yon": enk,
        "kararli": len({k["ogrenilen"] for k in kafes}) == 1,
        "not": ("§4 geregi en kucuk n_yon alinir; en iyi noktayi secip "
                "onu raporlamak kiraz toplamaktir."),
    }

    with open(a.cikti, "w", encoding="utf-8") as f:
        json.dump(rapor, f, ensure_ascii=False, indent=2)

    print("=== A. sigma'dan BAGIMSIZ geometri (u0 = merkez) ===")
    g0 = geo[0]
    for ad, v in g0["aci"].items():
        print(f"  {ad:<18s} aci = {v['aci_derece']:6.2f} derece   "
              f"kosinus = {v['kosinus']:+.4f}")
    print("  birim-J tekil degerleri:",
          ", ".join(f"{t:.4f}" for t in g0["tekil_degerler"]))
    print(f"  kosul sayisi: {g0['kosul_sayisi']:.1f}")
    print()
    print("=== B. e_hiz sigma esigi ===")
    eb = rapor["B_sigma_taramasi"]["ikinci_yon_icin_gereken_en_buyuk_sigma"]
    print("  ikinci yon icin gereken en buyuk sigma(e_hiz):",
          f"{eb:.4g}" if eb else "HIC BIR SIGMA'DA ACILMIYOR")
    print()
    print("=== C. kafes (3 rho x 5 u0) ===")
    print(f"  en kucuk n_yon: {enk}   "
          f"kararli: {rapor['C_kafes']['kararli']}")
    print("yazildi:", a.cikti)
    return 0


if __name__ == "__main__":
    raise SystemExit(ana())
