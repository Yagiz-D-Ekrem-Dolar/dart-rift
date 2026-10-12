"""TÜBİTAK 2204 raporunun yöntem şekilleri için veri üretir.

Neden ayrı bir üretici: rapordaki malzeme eğrileri elle çizilirse koddaki
formülden sessizce ayrışır. Buradaki her eğri, benzetimin kullandığı
FORMÜLÜN kendisinden hesaplanır ve sabitler `dartrift` içinden okunur.

    python scripts/rapor2204_veri.py

Çıktı: docs/rapor2204/veri/*.dat
"""

from __future__ import annotations

import math
from pathlib import Path

from dartrift.cpu_reference.materials import PorosityParams, StrengthParams

KOK = Path(__file__).resolve().parents[1]
VERI = KOK / "docs" / "rapor2204" / "veri"

# ÜRETİM değeri: config varsayılanı 0,8 ama hiçbir koşu onu kullanmıyor.
# truba/is_DO.slurm, is_DN.slurm, is_DC.slurm hepsi `--mu-f 0.6` geçiyor.
MU_F_URETIM = 0.6

# Pilot bağdaşım taramasının üç değeri (KAYIT-076).
Y0_PILOT = (10.0, 500.0, 5000.0)

# Üretim çıkarım aralığının uçları ve ortası (ADR-0059 §3.1).
ALPHA_B = (1.00, 1.15, 1.30)


def baslik(dosya, satirlar: list[str]) -> None:
    for s in satirlar:
        dosya.write(f"# {s}\n")


def wendland_c2_3b(q: float) -> tuple[float, float]:
    """W(q)*h^3 ve -dW/dq*h^3 — src/dartrift/warp_core/kernel_fn.py ile aynı.

        W(q)  = 21/(16 pi h^3) (1 - q/2)^4 (2q + 1)
        dW/dq = 21/(16 pi h^3) (-5q) (1 - q/2)^3
    """
    if q >= 2.0:
        return 0.0, 0.0
    c = 21.0 / (16.0 * math.pi)
    w = c * (1.0 - q / 2.0) ** 4 * (2.0 * q + 1.0)
    dw = c * (-5.0 * q) * (1.0 - q / 2.0) ** 3
    return w, -dw


def yazi_cekirdek() -> None:
    with open(VERI / "cekirdek.dat", "w", encoding="utf-8") as f:
        baslik(f, [
            "Wendland C2 cekirdegi, 3B (kernel_fn.py ile ayni ifade).",
            "q = r/h.  W ve -dW/dq, h^3 ile carpilarak boyutsuzlastirildi.",
            "Destek yaricapi q = 2, yani r = 2h.",
        ])
        f.write("q W mdWdq\n")
        n = 240
        for i in range(n + 1):
            q = 2.0 * i / n
            w, mdw = wendland_c2_3b(q)
            f.write(f"{q:.6f} {w:.8f} {mdw:.8f}\n")


def lundborg(p: float, y0: float, mu_f: float, ym: float) -> float:
    """Y(P) — warp_core/strength_lundborg.py::yield_stress ile aynı."""
    pp = max(p, 0.0)
    return y0 + mu_f * pp / (1.0 + mu_f * pp / (ym - y0))


def yazi_lundborg() -> None:
    sp = StrengthParams()
    with open(VERI / "lundborg.dat", "w", encoding="utf-8") as f:
        baslik(f, [
            "Lundborg/Collins akma yuzeyi Y(P), strength_lundborg.py formulu:",
            "    Y = Y0 + mu_f P / (1 + mu_f P / (YM - Y0))",
            f"YM = {sp.YM:.6e} Pa (materials.py), mu_f = {MU_F_URETIM} (URETIM kosusu).",
            "Sutunlar: basinc P [Pa] ve pilot taramanin uc Y0 degeri icin Y [Pa].",
        ])
        f.write("P Y10 Y500 Y5000\n")
        n = 200
        for i in range(n + 1):
            lp = 1.0 + 10.0 * i / n          # P = 1e1 .. 1e11 Pa
            p = 10.0**lp
            vals = [lundborg(p, y0, MU_F_URETIM, sp.YM) for y0 in Y0_PILOT]
            f.write(f"{p:.6e} " + " ".join(f"{v:.6e}" for v in vals) + "\n")


def crush(p: float, a0: float, pe: float, ps: float, n_exp: float) -> float:
    """alpha(P) yukleme egrisi — porosity_palpha.py::crush_alpha ile aynı."""
    if p <= pe:
        return a0
    if p >= ps:
        return 1.0
    t = (ps - p) / (ps - pe)
    return 1.0 + (a0 - 1.0) * t**n_exp


def yazi_crush() -> None:
    pp = PorosityParams()
    with open(VERI / "crush.dat", "w", encoding="utf-8") as f:
        baslik(f, [
            "P-alpha ezilme egrisi, porosity_palpha.py::crush_alpha formulu:",
            "    P <= Pe        -> alpha = alpha0",
            "    Pe < P < Ps    -> alpha = 1 + (alpha0-1) ((Ps-P)/(Ps-Pe))^n",
            "    P >= Ps        -> alpha = 1",
            f"Pe = {pp.Pe:.6e} Pa, Ps = {pp.Ps:.6e} Pa, n = {pp.n_exp} (materials.py).",
            f"Matris: alpha0 = {pp.alpha0} (malzeme varsayilani).",
            "Blok: alpha_b uretim cikarim araliginin uclari ve ortasi.",
            "Sutunlar: P [Pa], matris, sonra alpha_b = 1,00 / 1,15 / 1,30.",
        ])
        f.write("P matris ab100 ab115 ab130\n")
        n = 400
        for i in range(n + 1):
            lp = 4.0 + 5.0 * i / n           # P = 1e4 .. 1e9 Pa
            p = 10.0**lp
            sut = [crush(p, pp.alpha0, pp.Pe, pp.Ps, pp.n_exp)]
            sut += [crush(p, a0, pp.Pe, pp.Ps, pp.n_exp) for a0 in ALPHA_B]
            f.write(f"{p:.6e} " + " ".join(f"{v:.6f}" for v in sut) + "\n")


# --------------------------------------------------------------------------
# Dejenerasyon şekli — ŞEMATİK
# --------------------------------------------------------------------------
# DİKKAT: aşağıdaki yüzey ÖLÇÜLMÜŞ DEĞİLDİR. Elimizde yalnız sabit
# (alpha_b, f) = (1,15; 0,25) noktasında üç bağdaşım koşusu var; alpha_b ve
# f yönlerinde ölçülmüş bir yanıt yok. Dejenerasyon ifadesi literatürden
# gelir (Senel ve ark., 2025). Burada üretilen şey, o ifadeyi tek bir
# tutarlı ilişkiden üç panelde göstermeye yarayan bir TEMSİLDİR; sayıları
# sonuç olarak aktarılamaz ve rapor altyazısında da böyle yazılıdır.
#
#     log10 Y0 = L(beta) - KA (alpha_b - 1) - KF (f - 0,275)
#
# İşaretler fiziksel olarak savunulabilir yöndedir: Y0 artarsa beta düşer
# (ÖLÇÜLDÜ, KAYIT-076); alpha_b artarsa gözenek ezilmesine giden enerji
# artar ve beta düşer, dolayısıyla sabit beta için Y0 azalmalıdır. f'nin
# yönü ölçülmemiştir, bu yüzden katsayısı küçük tutuldu.
SEMA_KA = 12.0
SEMA_KF = 1.2
SEMA_F0 = 0.275

# L(beta) tek bir dogrusal kuraldan gelir; boylece es-beta egrileri, gozlem
# koridoru ve Fisher elipsi birbiriyle TUTARLI olur.
#     L(beta) = L0 - KB (beta - BETA_GOZ)
SEMA_L0 = 3.86
SEMA_KB = 1.2
BETA_GOZ = 3.5418
BETA_GOZ_UST = 0.188          # KAYIT/ADR-0054: asimetrik aralik
BETA_GOZ_ALT = 0.247

# Grafikte gosterilecek komsu beta duzeyleri.
SEMA_BETALAR = (2.0, 2.5, 3.0, 4.0, 4.5)


def sema_lvl(beta: float) -> float:
    return SEMA_L0 - SEMA_KB * (beta - BETA_GOZ)


def sema_logy0(alpha_b: float, f: float, lvl: float) -> float:
    return lvl - SEMA_KA * (alpha_b - 1.0) - SEMA_KF * (f - SEMA_F0)


def yazi_dejenerasyon() -> None:
    uyari = [
        "SEMATIK -- OLCUM DEGILDIR. Gerekce icin scripts/rapor2204_veri.py",
        "icindeki aciklamaya bakiniz. Dejenerasyon ifadesi literaturden",
        "gelir (Senel ve ark., 2025); buradaki yuzey onu tek bir tutarli",
        "iliskiden gostermeye yarayan bir temsildir.",
        f"log10 Y0 = L - {SEMA_KA} (alpha_b - 1) - {SEMA_KF} (f - {SEMA_F0})",
    ]

    # Es-beta duzey egrileri + gozlem koridoru, f = 0,275 kesitinde.
    # Koridor, beta_goz'un asimetrik 1-sigma araligindan gelir.
    with open(VERI / "dejenerasyon_egri.dat", "w", encoding="utf-8") as f:
        baslik(f, uyari + [
            "Kesit: f = 0,275.",
            "Sutunlar: alpha_b; komsu beta duzeyleri b20..b45 [Pa];",
            "gozlenen beta egrisi bgoz ve 1-sigma koridorunun alt/ust siniri.",
            f"beta_goz = {BETA_GOZ} +{BETA_GOZ_UST} -{BETA_GOZ_ALT}",
        ])
        ad = " ".join(f"b{str(b).replace('.', '')}" for b in SEMA_BETALAR)
        f.write(f"alphab {ad} bgoz kor_alt kor_ust\n")
        n = 160
        for i in range(n + 1):
            ab = 1.0 + 0.30 * i / n
            ys = [10.0 ** sema_logy0(ab, SEMA_F0, sema_lvl(b))
                  for b in SEMA_BETALAR]
            orta = 10.0 ** sema_logy0(ab, SEMA_F0, sema_lvl(BETA_GOZ))
            # Buyuk beta -> kucuk Y0, bu yuzden ust beta koridorun ALT siniri.
            alt = 10.0 ** sema_logy0(ab, SEMA_F0,
                                     sema_lvl(BETA_GOZ + BETA_GOZ_UST))
            ust = 10.0 ** sema_logy0(ab, SEMA_F0,
                                     sema_lvl(BETA_GOZ - BETA_GOZ_ALT))
            f.write(f"{ab:.5f} " + " ".join(f"{y:.6e}" for y in ys)
                    + f" {orta:.6e} {alt:.6e} {ust:.6e}\n")


def main() -> None:
    VERI.mkdir(parents=True, exist_ok=True)
    yazi_cekirdek()
    yazi_lundborg()
    yazi_crush()
    yazi_dejenerasyon()
    sp, pp = StrengthParams(), PorosityParams()
    print(f"yazildi -> {VERI}")
    print("  cekirdek.dat   Wendland C2, destek q=2")
    print(f"  lundborg.dat   YM={sp.YM:.3e} Pa, mu_f={MU_F_URETIM} (uretim)")
    print(f"  crush.dat      Pe={pp.Pe:.3e} Ps={pp.Ps:.3e} n={pp.n_exp} "
          f"alpha0_matris={pp.alpha0}")


if __name__ == "__main__":
    main()
