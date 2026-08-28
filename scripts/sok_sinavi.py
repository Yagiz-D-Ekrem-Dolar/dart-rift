"""**Şok sınavı**: model Hugoniot durumuna ulaşıyor mu?

## Neden bu ölçüt

`β` yakınsadı mı diye sormak, modelin **kendi** çıktısını kendine
sormaktır. Rankine-Hugoniot sıçrama koşulları ise **dışarıdan** ve
kesindir: verilen bir çarpma hızında şoklanmış maddenin sıkışması ve
iç enerjisi kapalı formda bellidir.

Ölçüldü (`2026-08-21`): hedefte **hiçbir parçacık** `%5`'ten fazla
sıkışmıyor; en sıcak parçacıklarda sıkışma `%0,4 – 3,7`. Hugoniot
aynı çarpma için `%46 – 74` ister.

> Model **şok üretmiyor**. Isınan az sayıdaki parçacık sıkışmadan
> ısınıyor — yani ısı şoktan değil, ayrıklaştırmanın dağıtıcı
> teriminden geliyor.

Bu, `β`'nın hedeften beslenmemesinin, kraterin `9 cm` kalmasının ve
ejektanın hiç olmamasının **tek** açıklaması.

## Ölçüt neden `β`'dan iyi

| | `β` yakınsama ölçütü | **şok sınavı** |
|---|---|---|
| referans | modelin kendi önceki koşusu | **Rankine-Hugoniot** |
| doğru cevabı biliyor muyuz | hayır | **evet, kapalı formda** |
| geçmesi neyi gösterir | duyarsızlık | **fiziğin kurulduğunu** |

`λ₂` `β`'yı `%5` oynatıp *"geçti"* demişti; aynı düğme hedefin iç
enerjisini `450` kat değiştirmişti. Şok sınavı böyle bir şeye izin
vermez: hedef **sayı** dışarıdan gelir.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

#: Bazalt icin dogrusal `Us = C0 + S up` (Melosh 1989, Tablo AII.2
#: mertebesinde). Bunlar LITERATUR degerleridir, uydurulmadi.
C0_BAZALT = 2600.0     # m/s
S_BAZALT = 1.5
RHO0_KATI = 2700.0     # kg/m^3

#: Sahne baslangic yogunluklari (`configs/p3_scene.yaml`):
#: matris `alpha0 = 1,7564`, blok `alpha0 = 1,05`.
RHO_MATRIS = RHO0_KATI / 1.7564
RHO_BLOK = RHO0_KATI / 1.05
#: Blok/matris ayrimi icin esik (ikisinin ortasi degil, bloga yakin:
#: sikismis matris blok sanilmasin diye).
BLOK_ESIGI = 2000.0


def hugoniot(up: float, *, C0: float = C0_BAZALT, S: float = S_BAZALT,
             rho0: float = RHO0_KATI) -> dict:
    """Verilen parçacık hızında şoklanmış durum.

    `Us = C0 + S up`; `rho/rho0 = Us/(Us - up)`; `P = rho0 Us up`;
    `du = ½ P (1/rho0 - 1/rho)`.
    """
    if up <= 0.0:
        raise ValueError(f"up pozitif olmali, {up} geldi")
    Us = C0 + S * up
    if Us <= up:
        raise ValueError(f"Us ({Us}) > up ({up}) olmali")
    sik = Us / (Us - up)
    P = rho0 * Us * up
    du = 0.5 * P * (1.0 / rho0 - 1.0 / (rho0 * sik))
    return {"up": up, "Us": Us, "sikisma_orani": sik,
            "sikisma_yuzde": 100.0 * (sik - 1.0), "P_Pa": P, "du_J_kg": du}


def beklenen_bant(v_carpma: float) -> dict:
    """Parçacık hızı `v/4 – v/2` aralığı için Hugoniot bandı.

    Simetrik çarpmada `up = v/2`; farklı empedanslarda daha düşük.
    Tek bir sayı yerine **bant** veriliyor — hangi `up`'ın doğru
    olduğu sahneye bağlı ve tek sayı seçmek belirsizliği gizlerdi.
    """
    alt = hugoniot(v_carpma / 4.0)
    ust = hugoniot(v_carpma / 2.0)
    return {"alt": alt, "ust": ust,
            "sikisma_bandi": (alt["sikisma_yuzde"], ust["sikisma_yuzde"]),
            "du_bandi": (alt["du_J_kg"], ust["du_J_kg"])}


def sikisma(rho: np.ndarray, alpha0: np.ndarray | None = None) -> np.ndarray:
    """Her parçacığın **kendi** başlangıç yoğunluğuna göre sıkışması.

    Blok ve matris farklı `alpha0` ile başlar; tek taban kullanmak
    blokları `%67` sıkışmış gösterirdi (bir kez öyle ölçüldü ve
    düzeltildi).

    ## `alpha0` verilirse taban **kesin**

    `taban = rho0_kati / alpha0`. Koşu bunu kaydediyorsa bu yol
    kullanılmalı.

    ## Verilmezse yoğunluk eşiğiyle **tahmin** — ve sınırı yazılı

    `rho > 2000` olanı blok saymak, **`%30`'dan fazla sıkışmış
    matrisi de blok sayar** (`1537 x 1,3 = 1998`). Yani tahmin yolu
    yalnızca sıkışmanın küçük olduğu rejimde güvenilir — ki ölçülen
    tam o rejim (`< %4`). Şok gerçekten kurulursa bu yol **yanıltır**
    ve `alpha0` zorunlu olur.
    """
    rho = np.asarray(rho, dtype=np.float64)
    if alpha0 is not None:
        a0 = np.asarray(alpha0, dtype=np.float64)
        if a0.shape != rho.shape:
            raise ValueError(f"alpha0 {a0.shape} ile rho {rho.shape} "
                             f"ayni olmali")
        if np.any(a0 <= 0.0):
            raise ValueError("alpha0 pozitif olmali")
        return rho * a0 / RHO0_KATI - 1.0
    taban = np.where(rho > BLOK_ESIGI, RHO_BLOK, RHO_MATRIS)
    return rho / taban - 1.0


def sinav(rho, u, m, *, v_carpma: float = 6144.9, alpha0=None) -> dict:
    """Şok sınavı: en yüksek sıkışma Hugoniot bandına ne kadar yakın."""
    s = sikisma(rho, alpha0)
    b = beklenen_bant(v_carpma)
    alt, ust = b["sikisma_bandi"]
    en = float(s.max())
    m = np.asarray(m, dtype=np.float64)
    return {
        "sikisma_max_yuzde": 100.0 * en,
        "sikisma_medyan_yuzde": 100.0 * float(np.median(s)),
        "hugoniot_bandi_yuzde": (alt, ust),
        "bandin_kacta_biri": (100.0 * en) / alt if alt > 0 else float("nan"),
        "n_yuzde5_ustu": int(np.count_nonzero(s > 0.05)),
        "n_bant_icinde": int(np.count_nonzero(100.0 * s >= alt)),
        "kutle_yuzde5_ustu": float(m[s > 0.05].sum()),
        "u_max": float(np.max(u)),
        "du_bandi": b["du_bandi"],
        "yargi": ("SOK_VAR" if 100.0 * en >= alt else
                  "SOK_YOK" if 100.0 * en < 0.1 * alt else "KISMI"),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--durum", type=Path, required=True)
    ap.add_argument("--v-carpma", type=float, default=6144.9)
    a = ap.parse_args()
    z = np.load(a.durum)
    for ad in ("rho", "u", "m"):
        if ad not in z.files:
            raise SystemExit(f"durumda `{ad}` yok: {z.files}")
    h = z["hedef"].astype(bool) if "hedef" in z.files else slice(None)
    a0 = z["alpha0"][h] if "alpha0" in z.files else None
    if a0 is None:
        print("  UYARI: durumda `alpha0` yok -> taban YOGUNLUK ESIGIYLE "
              "tahmin ediliyor; %30 ustu sikismada yanilir.", flush=True)
    r = sinav(z["rho"][h], z["u"][h], z["m"][h], v_carpma=a.v_carpma,
              alpha0=a0)
    print("=" * 66, flush=True)
    print("SOK SINAVI  (Rankine-Hugoniot; referans DISARIDAN)", flush=True)
    print("=" * 66, flush=True)
    alt, ust = r["hugoniot_bandi_yuzde"]
    print(f"  Hugoniot sikisma bandi : %{alt:.1f} - %{ust:.1f}", flush=True)
    print(f"  modelin EN YUKSEGI     : %{r['sikisma_max_yuzde']:.3f}",
          flush=True)
    print(f"  medyan                 : %{r['sikisma_medyan_yuzde']:.4f}",
          flush=True)
    print(f"  bandin kacta biri      : {r['bandin_kacta_biri']:.4f}",
          flush=True)
    print(f"  %5'ten fazla sikisan   : {r['n_yuzde5_ustu']} parcacik",
          flush=True)
    print(f"  banda ULASAN           : {r['n_bant_icinde']} parcacik",
          flush=True)
    print(f"\n  YARGI = {r['yargi']}", flush=True)
    if r["yargi"] == "SOK_YOK":
        print("  Model sok URETMIYOR: isinan madde sikismadan isiniyor.",
              flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
