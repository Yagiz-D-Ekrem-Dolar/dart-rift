"""KEŞİF — gözlenebilirlerin gradyanları tasarımın **her** noktasında
ne kadar eşdoğrusal?

## Soru ve niçin önemli

KAYIT-079 şunu ölçtü: `β`, kaçan kütle ve ejekta hız-şekli
gözlenebilirlerinin iç yapıya duyarlılıkları **neredeyse aynı yöne**
bakıyor — merkezde `4,64°`, bir köşede `0,62°`. Ve `σ`'yı `1000` kat
küçültmek ikinci öz değeri yalnız `2,35 → 4,17` taşıdı (eşik `36`),
çünkü `σ` o satırın **ağırlığını** değiştirir, **yönünü** değil.

Bu, Dimorphos hakkında değil **ileri modelin yapısı** hakkında bir
ifadedir ve genellenebilir olan kısım odur: *ölçüm hassasiyetini
artırmak ikinci bir yön açmaz; gradyanı gerçekten farklı bir
gözlenebilir gerekir.*

Ama KAYIT-079 bunu **beş** köşe noktasında ölçtü. Bu betik aynı hesabı
üretim tasarımının **96 noktasının hepsinde** yapar. Beş noktalık bir
gözlem ile tasarım boyunca ölçülmüş bir dağılım aynı şey değildir.

## Bu bir YARGI DEĞİL

`n_yön = 1` yargısı PROTOKOL-UP'a göre, belirlenen noktada, kilitli
eşikle verildi (KAYIT-079) ve **bu betik ona dokunmaz**. Burada
ölçülen şey o yargının tasarım boyunca nasıl dağıldığıdır. Eşik
(`FISHER_ESIGI = 36`), ölçüt ve yargı tablosu **değiştirilmez**.

## Kapı — koşudan ÖNCE yazıldı

KAYIT-079'un beş noktası açıları `0,62° – 29,48°` aralığında verdi.
Eşdoğrusallık hikâyesi tasarım boyunca ayakta kalıyorsa:

- **ORTANCA AÇI `< 30°`** olmalı.
- Noktaların **çoğunda** (`> %50`) `n_yön = 1` çıkmalı.

İkisinden biri tutmazsa hikâye beş köşenin işaret ettiğinden
**zayıftır** ve bu yazılır — KAYIT-092'deki doluluk hipotezi gibi.

## Kapsam

Ölçüm **DART/Dimorphos sahnesinde** yapılır (hedefin şekli ve kütlesi,
merminin kütlesi/hızı/açısı sabit). Sonuç bu sahnenin ileri modeli
hakkındadır.

Kullanım (sıfır GPU, yalnız depodaki CSV):

    python scripts/tani_esdogrusallik_96.py docs/sonuclar/havuz_posterior_girdi.csv
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK / "src"))
sys.path.insert(0, os.path.dirname(__file__))

from up_onsel_ve_tarih import _ortak  # noqa: E402

from dartrift.inference.design import DART_UZAYI_S4, lhs_design  # noqa: E402
from dartrift.inference.tanimlanabilirlik import (  # noqa: E402
    FISHER_ESIGI,
    fisher_yonleri,
    yerel_jakobyen,
)

N_HAVUZ, TOHUM = 96, 20260906
#: Kapi esikleri -- KOSUDAN ONCE konuldu (docstring).
ORTANCA_ACI_ESIGI = 30.0
N_YON1_ORAN_ESIGI = 0.50


def _aci_derece(a: np.ndarray, b: np.ndarray) -> float:
    """İki gradyan arasındaki açı; yön işareti **önemsiz** (0–90°)."""
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na < 1e-300 or nb < 1e-300:
        return float("nan")
    c = float(np.clip(abs(float(a @ b)) / (na * nb), -1.0, 1.0))
    return float(np.degrees(np.arccos(c)))


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("havuz", type=Path)
    p.add_argument("--n-grid", type=int, default=60)
    p.add_argument("--json", type=Path, default=None)
    a = p.parse_args()

    o = _ortak(a.havuz, a.n_grid)
    gp_b, gp_m = o["gp"]["beta"], o["gp"]["M_ejekta"]

    def ileri(u):
        uu = np.atleast_2d(u)
        return np.column_stack([gp_b.predict_u(uu)[0],
                                gp_m.predict_u(uu)[0]])[0]

    # `uretim_posterior` ile AYNI kovaryans: S = D^(1/2) R D^(1/2).
    sd = np.sqrt(o["varyans"].mean(0))
    kov = np.outer(sd, sd) * o["R"]

    X = np.asarray(lhs_design(DART_UZAYI_S4, N_HAVUZ, root_seed=TOHUM),
                   dtype=np.float64)
    U = DART_UZAYI_S4.to_unit(X)

    satir = []
    for k in range(N_HAVUZ):
        u = np.clip(U[k], 0.02, 0.98)
        J = yerel_jakobyen(ileri, u)
        f = fisher_yonleri(J, kov)
        oz = np.sort(np.asarray(f["ozdegerler"], dtype=float))[::-1]
        satir.append({
            "kuresel": k,
            "aci_beta_M_derece": _aci_derece(J[0], J[1]),
            # `fisher_yonleri` bu adi kullaniyor; uydurma anahtar
            # sessizce -1 dondururdu.
            "n_yon": int(f["ogrenilen_yon_sayisi"]),
            "oz1": float(oz[0]) if oz.size > 0 else float("nan"),
            "oz2": float(oz[1]) if oz.size > 1 else float("nan"),
        })

    aci = np.array([s["aci_beta_M_derece"] for s in satir], dtype=float)
    ny = np.array([s["n_yon"] for s in satir], dtype=int)
    oz2 = np.array([s["oz2"] for s in satir], dtype=float)
    aci_s = aci[np.isfinite(aci)]
    oran1 = float((ny == 1).mean())

    gecti_aci = bool(np.median(aci_s) < ORTANCA_ACI_ESIGI)
    gecti_nyon = bool(oran1 > N_YON1_ORAN_ESIGI)
    ozet = {
        "n": len(satir),
        "KAPSAM": "DART/Dimorphos sahnesi; hedef ve mermi SABIT",
        "aci_beta_M_derece": {
            "ortanca": float(np.median(aci_s)),
            "min": float(aci_s.min()), "maks": float(aci_s.max()),
            "q10": float(np.percentile(aci_s, 10)),
            "q90": float(np.percentile(aci_s, 90)),
        },
        "n_yon_dagilimi": {str(v): int((ny == v).sum())
                           for v in sorted(set(ny.tolist()))},
        "n_yon1_orani": oran1,
        "ikinci_ozdeger": {
            "ortanca": float(np.nanmedian(oz2)),
            "min": float(np.nanmin(oz2)), "maks": float(np.nanmax(oz2)),
            "esigi_gecen": int(np.nansum(oz2 >= FISHER_ESIGI)),
        },
        "esikler": {"ortanca_aci": ORTANCA_ACI_ESIGI,
                    "n_yon1_orani": N_YON1_ORAN_ESIGI,
                    "fisher": FISHER_ESIGI},
        "KAPI_aci_gecti": gecti_aci,
        "KAPI_nyon_gecti": gecti_nyon,
        "YARGI": ("ESDOGRUSALLIK TASARIM BOYUNCA AYAKTA"
                  if (gecti_aci and gecti_nyon) else
                  "ESDOGRUSALLIK BES KOSENIN GOSTERDIGINDEN ZAYIF"),
        "NOT": ("Bu bir KESIFTIR. `n_yon = 1` yargisi PROTOKOL-UP'a gore "
                "KAYIT-079'da verildi ve DEGISTIRILMEDI."),
    }

    print("=" * 70)
    print("ESDOGRUSALLIK -- tasarimin 96 noktasinda  (KESIF, yargi degil)")
    print("=" * 70)
    print(f"kapsam : {ozet['KAPSAM']}")
    print(f"okunan : {ozet['n']} / {N_HAVUZ}")
    print()
    aa = ozet["aci_beta_M_derece"]
    print("beta ~ M_ejekta gradyan acisi (derece):")
    print(f"  ortanca {aa['ortanca']:6.2f}   q10 {aa['q10']:6.2f}   "
          f"q90 {aa['q90']:6.2f}   aralik {aa['min']:.2f} .. {aa['maks']:.2f}")
    print(f"  KAPI ortanca < {ORTANCA_ACI_ESIGI}  -> "
          f"{'GECTI' if gecti_aci else 'DUSTU'}")
    print()
    print(f"n_yon dagilimi : {ozet['n_yon_dagilimi']}  "
          f"(n_yon=1 orani {oran1:.3f})")
    print(f"  KAPI oran > {N_YON1_ORAN_ESIGI}      -> "
          f"{'GECTI' if gecti_nyon else 'DUSTU'}")
    print()
    io = ozet["ikinci_ozdeger"]
    print(f"ikinci oz deger: ortanca {io['ortanca']:.3f}  "
          f"aralik {io['min']:.3f} .. {io['maks']:.3f}  "
          f"(esik {FISHER_ESIGI}, gecen {io['esigi_gecen']}/{ozet['n']})")
    print()
    print(f"YARGI: {ozet['YARGI']}")
    print(f"NOT  : {ozet['NOT']}")

    if a.json:
        a.json.write_text(json.dumps({"ozet": ozet, "noktalar": satir},
                                     indent=2, ensure_ascii=False),
                          encoding="utf-8")
        print(f"\nyazildi: {a.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
