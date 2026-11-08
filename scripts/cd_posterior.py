"""ADR-0059'un **DÖRDÜNCÜ** kapısı: iki yolun kipleri ayrılıyor mu?

[KAYIT-099](../docs/defter/KAYIT-099_2026-11-08_cok-dogruluklu-duzeltme-baglandi.md)
ADR-0059 §3.4'ün ilk üç maddesini ölçtü ve geçti. Dördüncü madde tam
posterioru **iki yolla** koşmayı gerektiriyordu:

| yol | tarif |
|---|---|
| `SIGMA` | ADR-0058'in kilitli tarifi, **değişmeden** |
| `CD` | aynı tarif, vekil orta çözünürlüğe **düzeltilmiş** |

Bu betik ikisini **tek koşuda** hesaplar. Niçin tek koşuda: iki yol ayrı
betiklerde hesaplanırsa aradaki fark vekilden mi yoksa tarifteki bir
kaymadan mı geldiği söylenemez. Burada tasarım, gözlenebilir dönüşümü,
`R`, `σ_model`, ızgara ve olabilirlik **aynı nesnelerdir**; değişen tek
şey vekilin ortalamasıdır.

## Nasıl kurulur — tek değişken ilkesi

`SIGMA` yolunun vekili `vekil_kur`'un döndürdüğü **Bachoc kalibreli**
GP'dir. `CD` yolu için `cok_dogruluk_uydur` çağrılır, sonra dönen
vekilin `kaba` katmanı **o aynı kalibreli GP ile değiştirilir**.

Bunun sebebi: `gp_varyans_kalibre` yalnız **varyansı** ölçekler,
ortalamayı değiştirmez. Dolayısıyla `ρ` ve `δ` kalibresiz ortalamaya
göre uydurulmuş olsa da geçerli kalır, ve iki yol **yalnız düzeltmede**
ayrışır. Aksi hâlde `CD` hem düzeltme hem kalibrasyon bakımından farklı
olurdu ve kipler arasındaki farkı hangisinin ürettiği bilinemezdi.

## VARSAYIM — açıkça

ADR-0060 gereği vekil `β`'ya değil `(β−1)/cos²`'ye uyduruluyor. İnce
koşuların `kos` sütunu **kaydedilmedi** (ince `jsonl` yalnız üç
gözlenebilir taşıyor). Bu yüzden ince noktaların dönüşümünde **kaba
koşunun `kos`'u** kullanılır.

Bu bir varsayımdır: `kos` çözünürlükle değişebilir. Karşılaştırmayı
bozmaz — iki yol da aynı `kos`'u kullanır — ama `CD`'nin **mutlak**
değerine girer ve sonuçla birlikte okunmalıdır.

## KAPI — ADR-0059 §3.4, burada SEÇİLMEDİ

> *"İki yolun kipleri `≥ 1σ` ayrılırsa bu bir **bulgu**dur, gizlenmez."*

Ölçüt: her eksende `|kip_CD − kip_SIGMA|`, o eksenin `SIGMA`
posteriorundaki standart sapmasına bölünür. Herhangi bir eksende
`≥ 1` ise kipler **AYRILIYOR**.

Kullanım (sıfır GPU):

    python scripts/cd_posterior.py docs/sonuclar/havuz_posterior_girdi.csv \\
        --ince docs/sonuclar/ince/ince_96.csv --json docs/sonuclar/cd_posterior.json
"""
from __future__ import annotations

import argparse
import csv
import dataclasses
import json
import math
import os
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))

from uretim_posterior import (  # noqa: E402
    BETA_ALT,
    BETA_GOZ,
    BETA_UST,
    KAT_SAYISI,
    M_EJEKTA_GOZ,
    M_EJEKTA_SIGMA,
    M_SAHNE,
    N_HAVUZ,
    TERIMLER_BETA,
    TERIMLER_MEJ,
    TOHUM,
    oku,
    vekil_kur,
)

from dartrift.inference.artik_korelasyonu import artik_korelasyonu  # noqa: E402
from dartrift.inference.cok_dogruluk import cok_dogruluk_uydur  # noqa: E402
from dartrift.inference.design import DART_UZAYI_S4, lhs_design  # noqa: E402
from dartrift.inference.posterior import grid_posterior_hetero  # noqa: E402
from dartrift.inference.tarih_esleme import (  # noqa: E402
    model_eksikligi_kaynakli,
)


def _ince_oku(yol: Path) -> dict:
    with open(yol, encoding="utf-8") as f:
        return {int(s["idx"]): (float(s["beta"]),
                                float(s["ejekta_kutle_kesri"]))
                for s in csv.DictReader(f)}


def _kip_ve_sd(post, space):
    """Izgara posteriorunun kipi ve eksen basina standart sapmasi.

    Sapma posteriorun KENDI `std_u`'sudur, burada yeniden hesaplanmaz:
    iki yol da ayni tanimla olculsun diye.
    """
    # `grid_u` eksen basina dugum dizisi, `p` ise (n,)*d bir dizi --
    # duz bir nokta listesi DEGIL. Kip, cok boyutlu indisten okunur.
    p = np.asarray(post.p, dtype=np.float64)
    yer = np.unravel_index(int(np.argmax(p)), p.shape)
    kip_u = np.array([np.asarray(post.grid_u[j], dtype=np.float64)[yer[j]]
                      for j in range(len(yer))], dtype=np.float64)
    return kip_u, np.asarray(post.std_u, dtype=np.float64).ravel()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("havuz", type=Path)
    ap.add_argument("--ince", type=Path, required=True)
    ap.add_argument("--n-grid", type=int, default=60)
    ap.add_argument("--json", type=Path, default=None)
    a = ap.parse_args(argv)

    idx, beta, ejf, kos = oku(a.havuz)
    if len(idx) != N_HAVUZ:
        raise SystemExit(f"KURAL 8: {N_HAVUZ} beklenir, {len(idx)} okundu")
    ince = _ince_oku(a.ince)
    eksik = sorted(set(ince) - set(int(i) for i in idx))
    if eksik:
        raise SystemExit(f"ince noktalar havuzda yok: {eksik}")

    X = lhs_design(DART_UZAYI_S4, N_HAVUZ, root_seed=TOHUM)[idx]
    katlar = idx % KAT_SAYISI
    b_model = (beta - 1.0) / kos ** 2
    m_model = ejf * M_SAHNE

    # --- SIGMA yolu: ADR-0058, DEGISMEDEN -----------------------------
    rapor: dict = {"girdi": str(a.havuz), "ince": str(a.ince),
                   "n_grid": a.n_grid}
    gp_b, e_b = vekil_kur(X, b_model, katlar, "vekil_beta", rapor)
    gp_m, e_m = vekil_kur(X, np.log(m_model), katlar, "vekil_M_ejekta", rapor)

    R, r_tani = artik_korelasyonu(np.column_stack([e_b, e_m]))
    b_goz = BETA_GOZ - 1.0
    sm_b = model_eksikligi_kaynakli(b_goz, list(TERIMLER_BETA))
    sm_m = model_eksikligi_kaynakli(1.0, list(TERIMLER_MEJ))
    sigma_goz_b = 0.5 * (BETA_UST + BETA_ALT)
    sigma_goz_m = M_EJEKTA_SIGMA / M_EJEKTA_GOZ

    # --- CD yolu: AYNI tarif, yalniz vekilin ortalamasi duzeltilmis ---
    i_ince = sorted(ince)
    yer = {int(v): k for k, v in enumerate(idx)}
    x_orta = X[[yer[i] for i in i_ince]]
    kos_orta = kos[[yer[i] for i in i_ince]]          # VARSAYIM: kaba kos
    b_orta = np.array([ince[i][0] for i in i_ince]) - 1.0
    b_orta = b_orta / kos_orta ** 2
    m_orta = np.log(np.array([ince[i][1] for i in i_ince]) * M_SAHNE)

    cd_b = cok_dogruluk_uydur(DART_UZAYI_S4, X, b_model, x_orta, b_orta)
    cd_m = cok_dogruluk_uydur(DART_UZAYI_S4, X, np.log(m_model),
                              x_orta, m_orta)
    # Kaba katmani KALIBRELI GP ile degistir: ortalama ayni, varyans
    # ADR-0058'inki. Tek degisken ilkesi (belge basligi).
    cd_b = dataclasses.replace(cd_b, kaba=gp_b)
    cd_m = dataclasses.replace(cd_m, kaba=gp_m)
    rapor["cd"] = {"rho_beta": float(cd_b.rho), "rho_M": float(cd_m.rho),
                   "uyarilar_beta": list(cd_b.uyarilar),
                   "uyarilar_M": list(cd_m.uyarilar),
                   "n_ince": len(i_ince), "ince_idx": i_ince}

    # --- iki posterior, AYNI izgara ve AYNI olabilirlik ---------------
    eksen = np.linspace(0.0, 1.0, a.n_grid)
    U = np.column_stack([g.ravel() for g in
                         np.meshgrid(*([eksen] * 3), indexing="ij")])
    veri = np.array([b_goz, math.log(M_EJEKTA_GOZ)])

    sonuc = {}
    for ad, vb, vm in (("SIGMA", gp_b, gp_m), ("CD", cd_b, cd_m)):
        mu_b, var_b = vb.predict_u(U)
        mu_m, var_m = vm.predict_u(U)
        ort = np.column_stack([mu_b, mu_m])
        varyans = np.column_stack([
            var_b + sigma_goz_b ** 2 + sm_b["sigma"] ** 2,
            var_m + sigma_goz_m ** 2 + sm_m["sigma"] ** 2,
        ])
        post = grid_posterior_hetero(DART_UZAYI_S4, ort, varyans, veri, R,
                                     n_grid=a.n_grid)
        kip_u, sd_u = _kip_ve_sd(post, DART_UZAYI_S4)
        sonuc[ad] = {"kip_u": kip_u, "sd_u": sd_u,
                     "kip": np.asarray(DART_UZAYI_S4.from_unit(kip_u[None, :])
                                       ).ravel()}

    # --- KAPI 4 -------------------------------------------------------
    d_u = np.abs(sonuc["CD"]["kip_u"] - sonuc["SIGMA"]["kip_u"])
    sigma_birim = sonuc["SIGMA"]["sd_u"]
    kayma = d_u / np.where(sigma_birim > 0, sigma_birim, np.nan)
    ayriliyor = bool(np.any(kayma >= 1.0))

    adlar = list(DART_UZAYI_S4.names)
    rapor["kapi4"] = {
        "olcut": "|kip_CD - kip_SIGMA| / sd_SIGMA, birim kupte, eksen basina",
        "esik": 1.0,
        "eksen": adlar,
        "kayma_sigma": [float(x) for x in kayma],
        "AYRILIYOR": ayriliyor,
    }
    for ad in ("SIGMA", "CD"):
        rapor[f"kip_{ad}"] = {
            "birim_kup": [float(x) for x in sonuc[ad]["kip_u"]],
            "dogal": {k: float(v) for k, v in
                      zip(adlar, sonuc[ad]["kip"], strict=True)},
            "sd_birim_kup": [float(x) for x in sonuc[ad]["sd_u"]],
        }
    rapor["VARSAYIM"] = ("Ince kosularin `kos` sutunu kaydedilmedi; ince "
                         "noktalarin ADR-0060 donusumunde KABA kosunun "
                         "`kos`'u kullanildi. Iki yol da ayni `kos`'u "
                         "kullanir, karsilastirma bozulmaz; CD'nin MUTLAK "
                         "degerine girer.")
    rapor["YARGI"] = (
        "KIPLER AYRILIYOR -> ADR-0059 §3.5: bu bir BULGUDUR, gizlenmez; "
        "iki yol da mansette." if ayriliyor else
        "KIPLER AYRILMIYOR (hepsi 1 sigma altinda) -> cozunurluk duzeltmesi "
        "kip kestirimini kaydirmıyor.")

    # ------------------------------------------------------------------
    print("=" * 70)
    print("ADR-0059 KAPI 4 — iki yolun kipleri")
    print("=" * 70)
    print(f"ince nokta: {len(i_ince)}  -> {i_ince}")
    print(f"rho  beta = {cd_b.rho:.4f}    log M = {cd_m.rho:.4f}")
    for u in list(cd_b.uyarilar) + list(cd_m.uyarilar):
        print(f"  UYARI: {u}")
    print()
    print(f"{'eksen':<16}{'SIGMA':>14}{'CD':>14}{'kayma/sigma':>14}")
    print("-" * 70)
    for j, ad in enumerate(adlar):
        print(f"{ad:<16}{sonuc['SIGMA']['kip'][j]:>14.4g}"
              f"{sonuc['CD']['kip'][j]:>14.4g}{kayma[j]:>14.3f}")
    print("-" * 70)
    print(f"esik 1.0 -> AYRILIYOR: {ayriliyor}")
    print()
    print(f"YARGI: {rapor['YARGI']}")

    if a.json:
        a.json.write_text(json.dumps(rapor, indent=1, ensure_ascii=False,
                                     default=float), encoding="utf-8")
        print(f"\nyazildi: {a.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
