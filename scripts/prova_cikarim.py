"""Çıkarım hattının **PROVASI** — havuz koşmadan, 0 GPU-saat (ADR-0051/0053).

**BU BİR SONUÇ DEĞİL.** Dimorphos hakkında hiçbir şey söylemez. Yaptığı tek
şey, `~650 GPU-saat`'lik havuz başlamadan önce **hattın kendisini** sınamak:
tasarım → vekil → iki gözlemli posterior → SBC kalibrasyonu →
tanımlanabilirlik. Bir kusur varsa havuzdan **önce** çıksın.

## Sentetik ileri model — hangi kısmı ölçülmüş, hangisi varsayım

    y1 = log10(β − 1) = log10(C_β) + p_β·log10(Y₀) + a_αβ·(α_b−ᾱ) + a_fβ·(f−f̄)
    y2 = log10(M_ejekta) = log10(C_M) + p_M·log10(Y₀) + a_αM·(α_b−ᾱ) + a_fM·(f−f̄)

| parça | kaynak |
|---|---|
| `p_β = −0,0760`, `C_β = 3,4649` | **ÖLÇÜLDÜ** (W2 `Y₀` serisi, KAYIT-073) |
| `p_M = −0,3206` | **ÖLÇÜLDÜ** (aynı seri) |
| `σ_gerçeklem(β) = %3,3`, `σ_gerçeklem(M) = %15` | **ÖLÇÜLDÜ** (KAYIT-070 §1) |
| `a_αβ, a_fβ, a_αM, a_fM` | **VARSAYIM** — `α_b` ve `f` eksenlerinde hiç ölçülmedi |

Varsayılan katsayılar iki **senaryoda** veriliyor:

- `ayrik`: `α_b` ve `f`, iki gözlemliyi **farklı** oranlarda değiştiriyor.
- `dejenere`: ikisi de gözlemlileri **neredeyse aynı** birleşimle değiştiriyor
  (gerçekçi kaygı — `f`'yi büyütmek ile `α_b`'yi büyütmek benzer etki yapabilir).

Hattın işi, `dejenere` senaryoda bunu **söylemek**; "üç parametreyi çözdük"
dememek. İki gözlemliyle en çok iki yön öğrenilir (ADR-0051 §2c) — bu,
senaryodan bağımsız **aritmetik**.

Kullanim:
    python scripts/prova_cikarim.py --senaryo ayrik --json kampanya/S_PROVA.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

_BURASI = Path(__file__).resolve().parent
sys.path.insert(0, str(_BURASI.parent / "src"))

from dartrift.inference.design import DART_UZAYI_S4_ONERI, lhs_design  # noqa: E402
from dartrift.inference.gp_vekil import (  # noqa: E402
    gp_grup_loo,
    gp_uydur,
    gp_varyans_kalibre,
)
from dartrift.inference.posterior import grid_posterior_hetero  # noqa: E402

# --- OLCULEN sabitler (KAYIT-073, KAYIT-070, ADR-0053) ----------------------
C_BETA, P_BETA = 3.4649, -0.0760
P_M = -0.3206
C_M = 3.0290e7 / (10.0 ** P_M)          # Y0 = 10 Pa'da 3,029e7 kg (W2)
SIGMA_GERCEKLEM_BETA = 0.033            # b uzerinden bagil
SIGMA_GERCEKLEM_M = 0.15
#: ADR-0054: gozlenen beta (sahne kutlesine eslenmis Cheng) ve ust 1 sigma.
BETA_GOZLEM, SIGMA_BETA_GOZLEM = 3.5418, 0.188
#: L17 Lolachi: ejekta kutlesi.
M_GOZLEM, SIGMA_M_GOZLEM = 1.6e7, 0.3e7

#: ÜÇÜNCÜ gözlemli: ejektanın yönelimi (`kos_ort`). `Y₀` üssü **ÖLÇÜLDÜ**
#: (`+0,0585`, KAYIT-073); `α_b`/`f` katsayıları **VARSAYIM**. DART karşılığı
#: **A95** yüzünden kıyaslanabilir değil — bu yüzden varsayılan olarak KAPALI.
#: `--ucuncu` ile açılır ve A95'i kapatmanın **ne kazandıracağını** ölçer.
P_KOS = 0.0585
C_KOS = 0.71922 / (10.0 ** P_KOS)       # Y0 = 10 Pa'da 0,71922 (W2)
SIGMA_KOS_BAGIL = 0.10                  # VARSAYIM: gozlem+gerceklem birlikte

#: VARSAYIM — `α_b` ve `f` katsayilari (olculmedi). Iki senaryo.
SENARYOLAR: dict[str, dict[str, float]] = {
    # ayrik: iki gozemli farkli oranlarda degisiyor -> 2 yon ogrenilebilir
    "ayrik": {"a_ab": -0.45, "a_fb": +0.30, "a_aM": +0.20, "a_fM": +0.90,
              "a_aK": +0.35, "a_fK": -0.15},
    # dejenere: ikisi de ayni birlesimle degisiyor -> yonler ayrismaz
    "dejenere": {"a_ab": -0.40, "a_fb": +0.80, "a_aM": -0.20, "a_fM": +0.40,
                 "a_aK": -0.10, "a_fK": +0.20},
}
ORTA_AB, ORTA_F = 1.15, 0.275           # uzayin ortasina yakin referans


def ileri(theta: np.ndarray, kat: dict, *, ucuncu: bool = False) -> np.ndarray:
    """Sentetik `(log10(β−1), log10(M_ejekta)[, log10(kos_ort)])`. Gürültüsüz."""
    t = np.atleast_2d(np.asarray(theta, dtype=np.float64))
    ab, y0, f = t[:, 0], t[:, 1], t[:, 2]
    if np.any(y0 <= 0.0):
        raise ValueError("Y0 > 0 olmali")
    ly = np.log10(y0)
    y1 = (np.log10(C_BETA) + P_BETA * ly
          + kat["a_ab"] * (ab - ORTA_AB) + kat["a_fb"] * (f - ORTA_F))
    y2 = (np.log10(C_M) + P_M * ly
          + kat["a_aM"] * (ab - ORTA_AB) + kat["a_fM"] * (f - ORTA_F))
    if not ucuncu:
        return np.column_stack([y1, y2])
    y3 = (np.log10(C_KOS) + P_KOS * ly
          + kat["a_aK"] * (ab - ORTA_AB) + kat["a_fK"] * (f - ORTA_F))
    return np.column_stack([y1, y2, y3])


def _log_sigma(bagil: float) -> float:
    """Bağıl sd → `log10` birimindeki sd (küçük gürültü yaklaşımı)."""
    return float(bagil / np.log(10.0))


def prova(senaryo: str, *, n_tasarim: int = 96, n_grid: int = 40,
          n_sbc: int = 60, tohum: int = 20261004, ucuncu: bool = False,
          vekil_kipi: str = "ikinci") -> dict:
    from dartrift.inference.kalibrasyon import (
        kapsama_egrisi,
        ks_duzgunluk,
        sbc_calistir,
    )
    from dartrift.inference.posterior import grid_posterior
    from dartrift.inference.surrogate import fit_surrogate, loo_artiklari
    from dartrift.inference.tanimlanabilirlik import (
        fisher_yonleri,
        tanimlanabilirlik_ozeti,
        yerel_jakobyen,
    )
    if senaryo not in SENARYOLAR:
        raise ValueError(f"senaryo {sorted(SENARYOLAR)} olmali, {senaryo!r} geldi")
    kat = SENARYOLAR[senaryo]
    uzay = DART_UZAYI_S4_ONERI
    rng = np.random.default_rng(tohum)

    # --- 1) tasarim + sentetik havuz (gerceklem gurultusuyle)
    X = lhs_design(uzay, n_tasarim, root_seed=tohum)
    Y0 = ileri(X, kat, ucuncu=ucuncu)
    k_gozlemli = Y0.shape[1]
    olcek = [_log_sigma(SIGMA_GERCEKLEM_BETA), _log_sigma(SIGMA_GERCEKLEM_M)]
    if ucuncu:
        olcek.append(_log_sigma(SIGMA_KOS_BAGIL))
    Y = Y0 + rng.normal(scale=olcek, size=Y0.shape)

    # --- 2) vekil (gozlemli basina) + LOO artigi
    #
    # A115: ikinci derece vekil yolunda vekil hatasi i.i.d. gurultu gibi
    # paydaya eklenir; ama hata theta'nin DUZGUN bir fonksiyonu, yani
    # korelasyonlu -> posterior gereginden genis cikiyor (SBC ASIRI TEMKINLI).
    # `gp` kipi ADR-0051 S2b'nin yolunu kullanir: GP ongoru varyansi
    # (theta'ya BAGLI) + Bachoc grup-CV kalibrasyonu + grid_posterior_hetero.
    gp_bilgi = None
    if vekil_kipi == "tam":
        # TANI KIPI: vekil YOK. Izgarada gercek ileri model kullanilir, yani
        # PIT'te kalan her sapma POSTERIOR MAKINESININ kusurudur (vekilin degil).
        vekiller, loo = [], [0.0] * k_gozlemli
    elif vekil_kipi == "gp":
        gpler, gp_bilgi = [], []
        gruplar = np.arange(n_tasarim) % 4          # 4 kat grup-CV
        for k in range(k_gozlemli):
            v = gp_uydur(uzay, X, Y[:, k])
            v, bil = gp_varyans_kalibre(v, Y[:, k], gruplar)
            gpler.append(v)
            gp_bilgi.append({"varyans_carpani": float(v.varyans_carpani),
                             **{a: float(bil[a]) for a in bil
                                if isinstance(bil[a], (int, float))}})
        vekiller = gpler
        loo = [float(np.sqrt(np.mean(gp_grup_loo(gpler[k], Y[:, k], gruplar)[0] ** 2)))
               for k in range(k_gozlemli)]
    else:
        vekiller = [fit_surrogate(uzay, X, Y[:, k]) for k in range(k_gozlemli)]
        loo = [float(np.std(loo_artiklari(uzay, X, Y[:, k]), ddof=1))
               for k in range(k_gozlemli)]

    # --- 3) gozlem ve toplam sd (log birimde)
    veri = [np.log10(BETA_GOZLEM - 1.0), np.log10(M_GOZLEM)]
    sg = [_log_sigma(SIGMA_BETA_GOZLEM / (BETA_GOZLEM - 1.0)),
          _log_sigma(SIGMA_M_GOZLEM / M_GOZLEM)]
    if ucuncu:
        # A95 kapansa gozlem sd'si ne olurdu -> VARSAYIM (olculmedi)
        veri.append(float(np.log10(C_KOS * 10.0 ** (P_KOS * 2.0))))
        sg.append(_log_sigma(SIGMA_KOS_BAGIL))
    veri = np.asarray(veri, dtype=np.float64)
    sigma = [float(np.sqrt(sg[k] ** 2 + loo[k] ** 2)) for k in range(k_gozlemli)]

    if vekil_kipi == "tam":
        eksen = np.linspace(0.0, 1.0, n_grid)
        Ug = np.column_stack([g.ravel() for g in
                              np.meshgrid(*([eksen] * uzay.ndim), indexing="ij")])
        ORT = ileri(uzay.from_unit(Ug), kat, ucuncu=ucuncu)
        VAR = np.tile(np.square(sg), (ORT.shape[0], 1))
        Rkor = np.eye(k_gozlemli)
        sigma = [float(v) for v in sg]

        def _post(v):
            return grid_posterior_hetero(uzay, ORT, VAR, v, Rkor, n_grid)
    elif vekil_kipi == "gp":
        # Izgarayi BIR kez degerlendir: SBC dongusunde yalniz `veri` degisir.
        eksen = np.linspace(0.0, 1.0, n_grid)
        Ug = np.column_stack([g.ravel() for g in
                              np.meshgrid(*([eksen] * uzay.ndim), indexing="ij")])
        ort_g, var_g = [], []
        for k in range(k_gozlemli):
            m, v2 = vekiller[k].predict_u(Ug)
            ort_g.append(np.asarray(m, float).ravel())
            # Gozlem varyansi theta'dan bagimsiz; GP varyansi theta'ya bagli.
            var_g.append(np.asarray(v2, float).ravel() + sg[k] ** 2)
        ORT = np.column_stack(ort_g)
        VAR = np.column_stack(var_g)
        Rkor = np.eye(k_gozlemli)

        def _post(v):
            return grid_posterior_hetero(uzay, ORT, VAR, v, Rkor, n_grid)
    else:
        def _post(v):
            return grid_posterior(uzay, vekiller, v, sigma, n_grid=n_grid)

    post = _post(veri)
    ozet = tanimlanabilirlik_ozeti(post)

    # --- 4) Fisher: 2 gozlemli / 3 parametre -> rank en cok 2 (ARITMETIK)
    # `post.mean` DOGAL birimde; jakobyen BIRIM kupte aliniyor (log eksenler
    # `to_unit` ile dogru donusuyor), cunku daralma ve onsel de orada tanimli.
    u0 = np.clip(np.asarray(post.mean_u, dtype=np.float64), 1e-3, 1 - 1e-3)
    J = yerel_jakobyen(
        lambda u: ileri(uzay.from_unit(np.atleast_2d(u)), kat, ucuncu=ucuncu)[0], u0)
    fis = fisher_yonleri(J, np.diag(np.square(sigma)))

    # --- 5) SBC (ayni gurultu modeli; sapma HATTIN kusuru olur)
    def uret(x, r):
        # SBC'nin degismezi: URETICI ile OLABILIRLIK ayni gurultuyu kullanmali.
        # Ilk surumde uretici yalniz GERCEKLEM gurultusunu (`olcek`) ekliyordu,
        # olabilirlik ise gozlem belirsizligini de iceren `sigma`'yi kullaniyordu
        # (beta ekseninde 2,24 kat genis) -> PIT zorunlu olarak ASIRI TEMKINLI
        # cikiyordu. Bu bir hat kusuru DEGILDI, provanin kurgu hatasiydi (A115).
        y = ileri(x[None, :], kat, ucuncu=ucuncu)[0]
        return y + r.normal(scale=sigma)

    def cikarim(v):
        return _post(v)

    sbc = sbc_calistir(uzay, uret, cikarim, n_sbc, tohum=tohum + 1)
    ks = [ks_duzgunluk(sbc.pit[:, j]) for j in range(uzay.ndim)]
    kaps = [kapsama_egrisi(sbc.pit[:, j]) for j in range(uzay.ndim)]

    # --- 6) yargi (PROVA tanisi; kilitli protokol DEGIL)
    kalibre = all(t["tani"] in ("DUZGUN", "KALIBRE") for t in sbc.tanilar)
    hat = "HAT CALISIYOR" if kalibre else "HAT KALIBRE DEGIL"
    return {
        "UYARI": "PROVA -- sentetik veri; Dimorphos hakkinda sonuc DEGIL",
        "senaryo": senaryo, "ucuncu_gozlemli": bool(ucuncu),
        "vekil_kipi": vekil_kipi, "gp_bilgi": gp_bilgi,
        "varsayilan_katsayilar": kat,
        "olculen_sabitler": {"p_beta": P_BETA, "p_M": P_M,
                             "sigma_gerceklem_beta": SIGMA_GERCEKLEM_BETA,
                             "sigma_gerceklem_M": SIGMA_GERCEKLEM_M},
        "uzay": {"adlar": list(uzay.names), "lo": list(uzay.lo),
                 "hi": list(uzay.hi)},
        "n_tasarim": n_tasarim, "n_grid": n_grid, "n_sbc": n_sbc,
        "vekil_loo_sd": loo, "sigma_toplam_log": sigma,
        "gozlem": {"beta": BETA_GOZLEM, "M_ejekta": M_GOZLEM},
        "eksenler": ozet["eksenler"], "yonler": ozet["yonler"],
        "fisher": {"ogrenilen_yon_sayisi": int(fis["ogrenilen_yon_sayisi"]),
                   "ust_sinir": int(fis["ust_sinir"]),
                   "ozdegerler": fis["ozdegerler"], "esik": fis["esik"],
                   "yaklasik_sd_oran": fis["yaklasik_sd_oran"]},
        "gozlemli_sayisi": int(k_gozlemli), "parametre_sayisi": int(uzay.ndim),
        "sbc": {"adlar": list(sbc.adlar),
                "tanilar": [t["tani"] for t in sbc.tanilar],
                "ks": [{"D": float(d), "p": float(pp)} for d, pp in ks],
                "kapsama": kaps},
        "genel": hat,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--senaryo", default="ayrik", choices=sorted(SENARYOLAR))
    ap.add_argument("--n-tasarim", type=int, default=96)
    ap.add_argument("--n-grid", type=int, default=40)
    ap.add_argument("--n-sbc", type=int, default=60)
    ap.add_argument("--vekil", default="ikinci", choices=("ikinci", "gp", "tam"),
                    help="A115: 'gp' -> GP + Bachoc + hetero; 'tam' -> vekil YOK (tani)")
    ap.add_argument("--ucuncu", action="store_true",
                    help="ejekta yonelimini (kos_ort) UCUNCU gozlemli yap "
                         "-- A95 kapanirsa ne kazanilir")
    ap.add_argument("--json", type=Path, default=None)
    a = ap.parse_args(argv)
    out = prova(a.senaryo, n_tasarim=a.n_tasarim, n_grid=a.n_grid,
                n_sbc=a.n_sbc, ucuncu=a.ucuncu, vekil_kipi=a.vekil)
    print("=" * 72)
    print(f"CIKARIM HATTI PROVASI -- senaryo: {a.senaryo}"
          f"{'  + UCUNCU GOZLEMLI (A95 kapali varsayimi)' if a.ucuncu else ''}")
    print("  UYARI: sentetik veri. Dimorphos hakkinda SONUC DEGIL.")
    print("=" * 72)
    print(f"  vekil kipi: {out['vekil_kipi']}"
          + (f"  varyans carpani {[round(g['varyans_carpani'], 2) for g in out['gp_bilgi']]}"
             if out["gp_bilgi"] else ""))
    print(f"  vekil LOO sd (log10): {[round(v, 4) for v in out['vekil_loo_sd']]}")
    print(f"  toplam sd (log10):    {[round(v, 4) for v in out['sigma_toplam_log']]}")
    f = out["fisher"]
    print(f"  gozlemli {out['gozlemli_sayisi']} / parametre "
          f"{out['parametre_sayisi']}  -> ogrenilen yon "
          f"{f['ogrenilen_yon_sayisi']} (ust sinir {f['ust_sinir']}, "
          f"esik {f['esik']:.0f})")
    print(f"  Fisher ozdegerleri: {[round(v, 1) for v in f['ozdegerler']]}")
    for d in out["eksenler"]:
        print(f"    {d['ad']:16s} daralma {d['daralma']:+.3f}  "
              f"{d['daralma_sinifi']:12s} profil {d['profil']:16s} -> {d['genel']}")
    for ad, t, k in zip(out["sbc"]["adlar"], out["sbc"]["tanilar"],
                        out["sbc"]["ks"], strict=True):
        print(f"    SBC {ad:16s} {t:16s} KS D={k['D']:.3f} p={k['p']:.3f}")
    print(f"GENEL: {out['genel']}")
    if a.json:
        a.json.write_text(json.dumps(out, indent=1, default=float),
                          encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
