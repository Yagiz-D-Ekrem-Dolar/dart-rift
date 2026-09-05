r"""`R1/R2/R3` yakınsama raporu — **donmuş ölçütü makinece uygular**.

## Neden sonuçlardan **önce** yazıldı

Bu betik `R2` ve `R3` bitmeden yazıldı. Ölçütü sonuca uydurmayı
imkânsız kılan şey budur: eşikler Protokol v2'den (`c94d74e`) geliyor,
buradan değil.

## Uyguladığı kurallar (hiçbiri burada tanımlanmıyor)

| kapı | kaynak |
|---|---|
| şok | `observables/sok.py` — yalnız **alt** sınır sert |
| defter | `momentum_defteri` — `\|artık\|/p ≤ 1e-3` |
| zamansal plato | `plato_gecti()` |
| uzamsal yakınsama | `Δβ`, `M_ejekta`, `P_ejekta,∥` **üçü birden** |

`A1 < 0,20` (aday) · `A2 < 0,10` (nihai). `A2` sağlanmazsa fark
`σ_sayısal` olarak raporlanır — **atılmaz**.

## `σ_num`: monotonluk **veriden önce** karara bağlandı

| davranış | yöntem |
|---|---|
| monoton | gözlenen mertebe `p` (`r = 2`) -> süreklilik-limiti hatası |
| monoton değil | muhafazakâr zarf `max\|Rᵢ − Rⱼ\|` |

Her nicelik için **ayrı**.

## Tanı (kapı **değil**)

`n_kaçan` · `θ_ejekta` · `β_mermi` · `ejekta_seviyeleri` ·
`en_agir_1_pay` — momentum bir-iki kaba parçacıkta yoğunlaşıyorsa
gözlenebilir yakınsasa bile **kırılgandır**.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from dartrift.observables.momentum_defteri import (  # noqa: E402
    momentum_defteri,
    plato_gecti,
)
from dartrift.observables.sok import sok_yargisi_ayrintili  # noqa: E402

#: Protokol v2 esikleri -- BURADA TANIMLANMIYOR, tekrarlaniyor.
A1_ESIK, A2_ESIK = 0.20, 0.10
NICELIKLER = ("delta_beta_hedef", "M_ejekta", "P_ejekta_eksenel")


def kol_oku(json_yolu: Path) -> dict:
    d = json.loads(json_yolu.read_text(encoding="utf-8"))
    z = np.load(json_yolu.with_suffix(".son_durum.npz"))
    md = momentum_defteri(z["x"], z["v"], z["m"],
                          mermi_kesri=z["mermi_kesri"], R=float(z["R"]),
                          v_esc=float(z["v_esc"]), ehat=z["ehat"],
                          p_imp=float(z["p_imp"]))
    sk = sok_yargisi_ayrintili(z["rho"][z["hedef"].astype(bool)],
                               z["alpha0"][z["hedef"].astype(bool)])
    iz = d.get("izler", [])
    plato = None
    if len(iz) >= 3:
        t = np.array([r["t"] for r in iz], dtype=np.float64)
        # `beta_bal` iz boyunca; `Delta` icin 1 cikariliyor
        db = np.array([r["beta_bal"] - 1.0 for r in iz], dtype=np.float64)
        plato = plato_gecti(t, db)
    return {"ad": json_yolu.stem, "N": d.get("N"), "defter": md,
            "sok": sk, "plato": plato,
            "krater": d.get("krater", {}).get("derinlik_m", float("nan"))}


def bagil_fark(a: float, b: float) -> float:
    """`|b − a| / |b|` — payda **sonraki** (daha ince) çözünürlük."""
    if not np.isfinite(a) or not np.isfinite(b) or abs(b) < 1e-300:
        return float("nan")
    return abs(b - a) / abs(b)


def monoton(dizi) -> bool:
    d = np.asarray(dizi, dtype=np.float64)
    if not np.all(np.isfinite(d)) or len(d) < 3:
        return False
    fark = np.diff(d)
    return bool(np.all(fark > 0) or np.all(fark < 0))


def sigma_num(dizi) -> tuple[float, str]:
    """Monotonsa mertebe tahmini, değilse **zarf** (kural v2'de sabit)."""
    d = np.asarray(dizi, dtype=np.float64)
    if not np.all(np.isfinite(d)) or len(d) < 3:
        return float("nan"), "hesaplanamadi"
    if not monoton(d):
        return float(np.max(d) - np.min(d)), "zarf (monoton DEGIL)"
    # r = 2 (aralik tam yariya iniyor); gozlenen mertebe
    f1, f2 = d[1] - d[0], d[2] - d[1]
    if abs(f2) < 1e-300 or f1 / f2 <= 0:
        return float(abs(f2)), "son fark (mertebe cikarilamadi)"
    p = float(np.log2(abs(f1 / f2)))
    # MERTEBE POZITIF DEGILSE YAKINSAMA YOK. Monoton olmak yetmiyor:
    # `[0, 0,033, 0,070]` monoton ama farklar BUYUYOR (`p = -0,17`) ve
    # Richardson formulu `3,7e10` gibi anlamsiz bir sayi verirdi.
    # Iraksayan diziye mertebe atfetmek yaniltir; zarfa dusulur.
    if p <= 0.0:
        return (float(np.max(d) - np.min(d)),
                f"zarf (IRAKSIYOR, gozlenen p = {p:.2f})")
    hata = float(abs(f2) / (2.0 ** p - 1.0))
    return hata, f"mertebe p = {p:.2f}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kollar", nargs="+", required=True,
                    help="R1.json R2.json R3.json (SIRAYLA kabadan inceye)")
    a = ap.parse_args()
    kollar = [kol_oku(Path(k)) for k in a.kollar]

    print("=" * 74)
    print("YAKINSAMA RAPORU -- Protokol v2 (c94d74e)")
    print("=" * 74)
    print(f"\n{'kol':>10} {'N':>9} {'sok':>16} {'defter':>9} {'plato':>7}")
    for k in kollar:
        pl = "--" if k["plato"] is None else ("GECTI" if k["plato"]["gecti"]
                                              else "DUSTU")
        print(f"{k['ad']:>10} {k['N']:>9} {k['sok']['yargi']:>16} "
              f"{'KAPALI' if k['defter']['kapandi'] else 'ACIK':>9} {pl:>7}")

    print(f"\n{'nicelik':>20}" + "".join(f"{k['ad']:>14}" for k in kollar)
          + f"{'A1':>8}{'A2':>8}")
    yakinsadi = True
    for ad in NICELIKLER:
        d = [k["defter"][ad] for k in kollar]
        farklar = [bagil_fark(d[i], d[i + 1]) for i in range(len(d) - 1)]
        son = farklar[-1] if farklar else float("nan")
        a1 = "gecti" if son < A1_ESIK else "DUSTU"
        a2 = "gecti" if son < A2_ESIK else "DUSTU"
        if not (son < A1_ESIK):
            yakinsadi = False
        print(f"{ad:>20}" + "".join(f"{v:>14.6g}" for v in d)
              + f"{a1:>8}{a2:>8}")
        s, yontem = sigma_num(d)
        print(f"{'':>20}  sigma_num = {s:.6g}   ({yontem})")

    print(f"\n{'TANI':>20}" + "".join(f"{k['ad']:>14}" for k in kollar))
    for ad, bic in (("n_kacan_hedef", "d"), ("theta_ejekta_derece", ".1f"),
                    ("beta_mermi", ".5f"), ("en_agir_1_pay", ".3f"),
                    ("m_ej_medyan", ".2f")):
        print(f"{ad:>20}" + "".join(
            f"{k['defter'][ad]:>14{bic}}" if np.isfinite(
                float(k['defter'][ad] or np.nan)) else f"{'--':>14}"
            for k in kollar))

    print("\n" + "=" * 74)
    print(f"UZAMSAL YAKINSAMA (A1, uc nicelik BIRDEN): "
          f"{'GECTI' if yakinsadi else 'DUSTU'}")
    print("Dort kapi birden yesil degilse beta_hedef gozlenebilir olarak")
    print("KULLANILMAZ (Protokol v2).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
