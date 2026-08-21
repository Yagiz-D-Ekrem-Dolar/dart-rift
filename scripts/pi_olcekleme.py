"""**Dış kıyas**: π-grubu krater ölçeklemesi vs modelin krateri.

## Neden

Model bugüne kadar yalnızca **kendi** ölçütlerine karşı doğrulandı:
Sedov patlaması, Rankine-Hugoniot, korunum, determinizm. Bunlar
**birim** doğrulamalardır — çarpma **sonucunun** büyüklüğü hiçbir dış
standarda karşı sınanmadı.

π-grubu ölçeklemesi (Holsapple 1993; Housen & Holsapple 2011) verilen
çarpma ve hedef için krater hacmini kapalı formda verir. Bu bir uydurma
değil; sabitler laboratuvar ve patlama deneylerinden gelir ve burada
**hiçbiri uydurulmuyor**.

## Bu betiğin dürüstlük kuralı

Malzeme sabitleri tek bir aile için değil, bir **kuşak** için
raporlanıyor (kuru kum -> zayıf gözenekli -> kohezyonlu -> sert kaya).
Dimorphos'un hangi aileye düştüğü **bilinmiyor**; tek bir aile seçip
"uydu/uymadı" demek, belirsizliği gizlemek olurdu. Çıktı bir
**aralıktır**.

## İkinci ve daha keskin kıyas: krater **şekli**

Ölçekleme sabitleri tartışılabilir ama şu tartışılmaz: çarpma
kraterleri **çanak**tır. Geçici kraterde derinlik/çap oranı
literatürde `0,15 – 0,30` bandındadır (Melosh 1989). Bu oran
**boyutsuz** ve hiçbir malzeme sabitine bağlı değil.

Modelin ölçtüğü oran bu bandın dışındaysa, ölçekleme sabitleri ne
olursa olsun model **çanak açmıyor** demektir.
"""
from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass

#: Çarpma koşulları — `configs/p3_scene.yaml`.
M_MERMI = 579.4          # kg
U_CARPMA = 6144.9        # m/s
DELTA_MERMI = 2700.0     # kg/m^3, mermi yoğunluğu
RHO_HEDEF = 1800.0       # kg/m^3, yığın yoğunluğu
R_HEDEF = 82.0           # m

#: Geçici kraterde derinlik/çap oranı — literatür bandı (Melosh 1989).
#: Boyutsuz ve malzeme sabitlerinden BAGIMSIZ.
SEKIL_BANDI = (0.15, 0.30)


@dataclass(frozen=True)
class Malzeme:
    """π-ölçekleme sabitleri — **literatürden**, uydurulmadı."""

    ad: str
    mu: float
    nu: float
    K1: float
    K2: float
    Y_Pa: float
    kaynak: str


#: Housen & Holsapple (2011), *Icarus* 211, 856 — Tablo 3 malzeme
#: aileleri. Dimorphos'un hangi aileye düştüğü BILINMIYOR; bu yüzden
#: bir kuşak taranıyor ve sonuç bir ARALIK olarak veriliyor.
MALZEMELER: tuple[Malzeme, ...] = (
    Malzeme("kuru kum", 0.41, 0.40, 0.132, 1.0, 0.0, "H&H 2011 T3"),
    Malzeme("zayif gozenekli", 0.40, 0.40, 0.42, 0.30, 4.5e3, "H&H 2011 T3"),
    Malzeme("kohezyonlu toprak", 0.55, 0.40, 0.55, 0.30, 1.8e5, "H&H 2011 T3"),
    Malzeme("sert kaya", 0.55, 0.40, 0.095, 0.257, 7.6e6, "H&H 2011 T3"),
)


def yercekimi_ivmesi(rho: float = RHO_HEDEF, R: float = R_HEDEF,
                     G: float = 6.6743e-11) -> float:
    """Yüzey yerçekimi `g = G M / R²` (düzgün küre)."""
    M = rho * (4.0 / 3.0) * math.pi * R ** 3
    return G * M / R ** 2


def mermi_yaricapi(m: float = M_MERMI, delta: float = DELTA_MERMI) -> float:
    return (3.0 * m / (4.0 * math.pi * delta)) ** (1.0 / 3.0)


def krater_hacmi(mal: Malzeme, *, g: float, a: float, U: float = U_CARPMA,
                 rho: float = RHO_HEDEF, delta: float = DELTA_MERMI,
                 m: float = M_MERMI) -> dict:
    """Geçici krater hacmi — π-grubu birleşik (yerçekimi + mukavemet).

    `π₂ = 3,22 g a / U²`, `π₃ = Y / (ρ U²)`, `π_V = ρ V / m` ve
    (Housen & Holsapple 2011, denk. 17):

        π_V = K1 { π₂ (ρ/δ)^((6ν-2-μ)/(3μ))
                   + [K2 π₃ (ρ/δ)^((6ν-2)/(3μ))]^((2+μ)/2) }^(-3μ/(2+μ))
    """
    pi2 = 3.22 * g * a / U ** 2
    pi3 = mal.Y_Pa / (rho * U ** 2)
    rd = rho / delta
    mu, nu, K1, K2 = mal.mu, mal.nu, mal.K1, mal.K2

    yer = pi2 * rd ** ((6.0 * nu - 2.0 - mu) / (3.0 * mu))
    muk = (K2 * pi3 * rd ** ((6.0 * nu - 2.0) / (3.0 * mu))) ** ((2.0 + mu) / 2.0)
    piV = K1 * (yer + muk) ** (-3.0 * mu / (2.0 + mu))
    V = piV * m / rho
    # Yerçekimi mi mukavemet mi baskin -- hangi terim buyukse o.
    return {"malzeme": mal.ad, "pi2": pi2, "pi3": pi3, "piV": piV,
            "V_m3": V, "yercekimi_terimi": yer, "mukavemet_terimi": muk,
            "rejim": "yercekimi" if yer > muk else "mukavemet"}


def hacimden_cap(V: float, derinlik_cap: float) -> float:
    """Çanak krater hacmi `V = (π/8) k D³`, `k = derinlik/çap`.

    Paraboloid çanak: `V = (π/8) D² d` ve `d = k D`.
    """
    if V <= 0.0 or derinlik_cap <= 0.0:
        raise ValueError("V ve derinlik/cap pozitif olmali")
    return (8.0 * V / (math.pi * derinlik_cap)) ** (1.0 / 3.0)


def sekil_yargisi(derinlik: float, cap: float) -> dict:
    """Derinlik/çap oranı literatür bandında mı — **malzemeden bağımsız**."""
    if cap <= 0.0:
        return {"oran": float("nan"), "yargi": "olculemedi"}
    k = derinlik / cap
    alt, ust = SEKIL_BANDI
    if k < alt:
        y = "COK_SIG"
    elif k > ust:
        y = "COK_DERIN"
    else:
        y = "canak"
    return {"oran": k, "bant": SEKIL_BANDI, "yargi": y,
            "banda_oran": k / ust if k > ust else (k / alt if k < alt else 1.0)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model-derinlik", type=float, default=15.28,
                    help="modelin olctugu krater derinligi (m)")
    ap.add_argument("--model-cap", type=float, default=7.4916,
                    help="modelin olctugu krater capi (m)")
    ap.add_argument("--cikti", type=str, default=None)
    a = ap.parse_args()

    g = yercekimi_ivmesi()
    rm = mermi_yaricapi()
    print("=" * 72, flush=True)
    print("PI-OLCEKLEME DIS KIYASI  (Holsapple 1993; Housen & Holsapple 2011)",
          flush=True)
    print("=" * 72, flush=True)
    print(f"  mermi {M_MERMI} kg, yaricap {rm:.4f} m, hiz {U_CARPMA} m/s",
          flush=True)
    print(f"  hedef rho {RHO_HEDEF} kg/m3, R {R_HEDEF} m, g {g:.4e} m/s2",
          flush=True)

    print(f"\n  {'malzeme':>18} {'rejim':>11} {'V (m3)':>12} "
          f"{'cap (m)':>10}  (k = 0,20 canak)", flush=True)
    print("  " + "-" * 62, flush=True)
    sonuc = []
    for mal in MALZEMELER:
        r = krater_hacmi(mal, g=g, a=rm)
        D = hacimden_cap(r["V_m3"], 0.20)
        r["cap_m"] = D
        sonuc.append(r)
        print(f"  {mal.ad:>18} {r['rejim']:>11} {r['V_m3']:>12.4e} "
              f"{D:>10.2f}", flush=True)

    caplar = [r["cap_m"] for r in sonuc]
    print(f"\n  PI-OLCEKLEME ARALIGI: cap {min(caplar):.2f} - "
          f"{max(caplar):.2f} m", flush=True)
    print(f"  MODELIN OLCTUGU:      cap {a.model_cap:.2f} m, "
          f"derinlik {a.model_derinlik:.2f} m", flush=True)

    s = sekil_yargisi(a.model_derinlik, a.model_cap)
    print("\n  SEKIL KIYASI (malzemeden BAGIMSIZ)", flush=True)
    print(f"    derinlik/cap = {s['oran']:.3f}   literatur bandi "
          f"{SEKIL_BANDI[0]} - {SEKIL_BANDI[1]}   -> {s['yargi']}", flush=True)
    if s["yargi"] == "COK_DERIN":
        print(f"    bandin ust sinirinin {s['banda_oran']:.1f} KATI -- "
              f"model canak acmiyor, DELIK aciyor", flush=True)

    d = {"g": g, "mermi_yaricapi": rm, "olcekleme": sonuc,
         "model": {"derinlik_m": a.model_derinlik, "cap_m": a.model_cap},
         "sekil": s}
    if a.cikti:
        with open(a.cikti, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
