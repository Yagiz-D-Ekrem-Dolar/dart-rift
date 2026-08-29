"""**Arayüz kütle oranı**: inceltme basamakları ne kadar dik.

## Neden bu ölçü

KAYIT-053 şunu buldu: mermi (`579 kg`) kendisinden `80` kat ağır tek
bir parçacığa çarpıyordu (`μ = 80`) ve şok hedefe **giremiyordu**.
Çare `μ ≈ 1`'e inmekti.

A24'te cephe `3,41 m`'de **hızı `0,0 m/s`** ile durdu. Sebebi
ölçüldü (`2026-08-29`): o yarıçapta ince parçacıklar `46,6 kg`, hemen
dışındaki ilk parçacık **`372 834 kg`**.

> **Arayüz oranı `8 000`** — `μ = 80`'in `100` katı. Şok, mermininkiyle
> **aynı** duvara çarpıyor; yalnızca bu kez duvar ayrıklaştırmanın
> kendi ürünü.

Kütle `s³` ile gittiği için `8 000` kat kütle = **`20` kat aralık**
sıçraması (`0,35 -> 7,0 m`) — hem de **tek** basamakta. AMR
uygulamasında olağan basamak `2` katıdır (`8` kat kütle).

## Ölçü neden `μ` değil de bu

`μ` merminin hedefe bağlanmasını ölçüyordu; bu, şokun **taşınmasını**
ölçüyor. İkisi aynı büyüklüğün iki yerdeki hâli ve ikisi de aynı
soruyu soruyor: *momentum alıcıdan çok daha ağır bir şeye mi
veriliyor?*
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

#: AMR uygulamasinda olagan basamak: aralikta `2`, kutlede `2^3 = 8`.
OLAGAN_ORAN = 8.0
#: Bunun uzerinde sok gecemedigi OLCULDU (cephe hizi 0,0 m/s).
TEHLIKE_ORANI = 100.0


def basamaklar(m: np.ndarray, *, tol: float = 1e-6) -> np.ndarray:
    """Ayrık kütle **seviyeleri**, küçükten büyüğe.

    Kayan nokta gürültüsü ayrı seviye sayılmamalı — bu depoda bir kez
    `np.unique` `40` sahte seviye saydı (rapor A11).
    """
    m = np.asarray(m, dtype=np.float64)
    if m.ndim != 1 or len(m) == 0:
        raise ValueError(f"m (N,) ve bos olmayan olmali, {m.shape} geldi")
    if np.any(m <= 0.0):
        raise ValueError("kutle pozitif olmali")
    s = np.sort(m)
    kes = [s[0]]
    for v in s[1:]:
        if v > kes[-1] * (1.0 + tol):
            kes.append(v)
    return np.array(kes)


def oranlar(m: np.ndarray, *, tol: float = 1e-6) -> dict:
    """Komşu seviyeler arasındaki kütle oranları ve en dik basamak."""
    k = basamaklar(m, tol=tol)
    if len(k) == 1:
        return {"seviyeler": k, "oranlar": np.array([]),
                "en_dik": 1.0, "aralik_sicramasi": 1.0, "yargi": "TEK_SEVIYE"}
    r = k[1:] / k[:-1]
    en = float(r.max())
    return {
        "seviyeler": k, "oranlar": r, "en_dik": en,
        # kutle ~ s^3
        "aralik_sicramasi": en ** (1.0 / 3.0),
        "yargi": ("TEHLIKELI" if en >= TEHLIKE_ORANI else
                  "DIK" if en > OLAGAN_ORAN else "OLAGAN"),
    }


#: Bir kaba parcacigin destegi `2h = 4s`. Kabuk bundan INCEYSE o
#: seviye bir tampon olarak islemiyor demektir.
ASGARI_KALINLIK_S = 4.0


def kabuk_kalinligi(kademeler, spacing: float) -> list:
    """Her kabuğun kalınlığı, parçacık aralığı cinsinden.

    ## Neden kütle oranından **daha** temel

    Destekteki ince parçacık sayısı `(2h_kaba)³`, gereken kütle de
    `s_kaba³` ile gidiyor; ikisi aynı oranda büyüdüğü için pay
    **basamak boyutundan bağımsız** (`189,6×`). Yani kütle oranı tek
    başına hiçbir basamağı düşürmez.

    Düşüren şey **geometri**: kaba parçacığın desteği `4 s_kaba` ve o
    kadar ince madde **var olmalı**. Tek basamaklı şemada destek
    `28 m`, ince bölge `3 m` — `9` kat büyük. Destekte `1,5` milyon
    ince parçacık gerekiyordu; `1 828` vardı.

    `kademeler`: `(r, λ)` çiftleri **dıştan içe**
    (:func:`refine_scene_kademeli` ile aynı sıra).
    """
    k = [(float(r), float(lam)) for r, lam in kademeler]
    if len(k) < 2:
        raise ValueError(f"en az iki kademe gerekir, {len(k)} geldi")
    out = []
    for i, (r, lam) in enumerate(k):
        s = float(spacing) / lam
        ic = k[i + 1][0] if i + 1 < len(k) else 0.0
        kal = r - ic
        out.append({"r_dis": r, "r_ic": ic, "s": s, "kalinlik_m": kal,
                    "kalinlik_s": kal / s,
                    "yeterli": bool(kal / s >= ASGARI_KALINLIK_S)})
    return out


def kademe_onerisi(en_dik: float) -> int:
    """Basamağı `OLAGAN_ORAN`'a indirmek için gereken **ara seviye**."""
    if en_dik <= OLAGAN_ORAN:
        return 0
    return int(np.ceil(np.log(en_dik) / np.log(OLAGAN_ORAN))) - 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--durum", type=Path, nargs="+", required=True)
    a = ap.parse_args()
    print(f"{'dosya':>24} {'seviye':>7} {'en dik':>10} {'aralik':>8} "
          f"{'ara seviye':>11} {'yargi':>11}")
    for yol in a.durum:
        z = np.load(yol)
        h = z["hedef"].astype(bool) if "hedef" in z.files else slice(None)
        r = oranlar(z["m"][h])
        print(f"{yol.name[:24]:>24} {len(r['seviyeler']):>7} "
              f"{r['en_dik']:>10,.0f} {r['aralik_sicramasi']:>8.1f} "
              f"{kademe_onerisi(r['en_dik']):>11} {r['yargi']:>11}")
        if len(r["oranlar"]):
            print(f"{'':>24} seviyeler (kg): "
                  + " -> ".join(f"{v:,.1f}" for v in r["seviyeler"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
