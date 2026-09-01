"""**Momentum defteri** — `β`'nın her kuruşunun nereden geldiği.

## Neden gerekli

`β = 3,2` demek tek başına hiçbir şey kanıtlamaz. Bu depoda ölçüldü ki
`β = 1,4112`'nin **tamamı mermi geri tepmesiydi**; hedef katkısı tam
`0`. Sayı güzel görünüyordu ve **yanlıştı**.

Merdiven yoluyla fizik düzelince `β` `1,379 -> 1,081`'e **düştü** —
çünkü sahte geri tepme kayboldu. Yani `β`'nın *değeri* değil,
**bileşimi** okunmalı.

## Defter

Hedef durgun başladığı için toplam momentum **merminin momentumudur**
ve korunur. `ê` merminin gidiş yönü:

    p_mermi = P_bağlı_hedef + P_kaçan_hedef
            + P_bağlı_mermi + P_kaçan_mermi + artık

`β` bu defterden **türetilir**, ayrıca hesaplanmaz:

| pay | anlamı |
|---|---|
| `β_hedef` | **gerçek** momentum artışı — kazılan madde |
| `β_mermi` | mermi geri tepmesi — **sahte**, `β` sayılmamalı |

> **Kural:** `artık` büyükse `β` **raporlanmaz**. Kapanmayan bir
> defterin türevi de kapanmaz.

## Provenance nasıl korunuyor

`mermi_kesri` kütle-ağırlıklı taşınan bir kesir. Merdiven yolunda
(tek aşama, aktarım yok) ölçüldü: ara değerli parçacık **`0`**,
toplam mermi kütlesi **`579,40 kg`** (gerçek `579,4`). Yani kimlik
hiçbir aşamada karışmıyor.

İki aşamalı yolda karışıyordu ve `two_stage` bunu **bilerek**
yapıyordu; o yüzden defter orada yalnızca kesirle anlamlı.
"""
from __future__ import annotations

import numpy as np

#: Defterin kapali sayilmasi icin azami bagil artik.
ARTIK_ESIGI = 1.0e-3


def momentum_defteri(x, v, m, *, mermi_kesri, R, v_esc, ehat,
                     p_imp: float) -> dict:
    """Momentumu **provenance** ve **kaçış** ile dört kutuya ayır.

    Parameters
    ----------
    mermi_kesri
        Her parçacığın mermi kütle kesri (`0 – 1`).
    R, v_esc
        Kaçış ölçütü: `r > R` **ve** `v_r > v_esc`. Yerçekimi kapalıyken
        bu parçacık bir daha yavaşlamaz (rapor A12).
    ehat
        Merminin gidiş yönü (birim). Momentum bu eksene izdüşürülür.
    p_imp
        Merminin başlangıç momentumunun **büyüklüğü**.
    """
    x = np.asarray(x, dtype=np.float64)
    v = np.asarray(v, dtype=np.float64)
    m = np.asarray(m, dtype=np.float64)
    f = np.asarray(mermi_kesri, dtype=np.float64)
    e = np.asarray(ehat, dtype=np.float64)
    if not (len(x) == len(v) == len(m) == len(f)):
        raise ValueError(
            f"x {len(x)}, v {len(v)}, m {len(m)}, mermi_kesri {len(f)} "
            f"ayni uzunlukta olmali")
    if np.any(f < -1e-12) or np.any(f > 1.0 + 1e-12):
        raise ValueError("mermi_kesri [0,1] araliginda olmali")
    if p_imp <= 0.0:
        raise ValueError(f"p_imp pozitif olmali, {p_imp} geldi")

    r = np.linalg.norm(x, axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        v_r = np.einsum("ij,ij->i", v, x) / np.maximum(r, 1e-300)
    kacan = (r > R) & (v_r > v_esc)

    # P_ejekta EKSENEL izdusum: `beta` carpma dogrultusundaki
    # momentumdan geliyor, buyuklukten degil. Tam VEKTOR de
    # kaydediliyor -- cozunurlukle ejekta YON dagilimi degisirse
    # (`beta` ayni kalip aci degisirse) o degisiklik ancak vektorde
    # gorunur.
    pe = m * (v @ e)                         # ê eksenine izdusum
    kutu = {
        "P_bagli_hedef": float(pe[(~kacan)] @ (1.0 - f[~kacan])),
        "P_kacan_hedef": float(pe[kacan] @ (1.0 - f[kacan])),
        "P_bagli_mermi": float(pe[(~kacan)] @ f[~kacan]),
        "P_kacan_mermi": float(pe[kacan] @ f[kacan]),
    }
    toplam = sum(kutu.values())
    artik = p_imp - toplam

    # `beta` DEFTERDEN TURETILIYOR, ayrica hesaplanmiyor. Kacan madde
    # `-ê` yonunde gittigi icin izdusumu NEGATIF; `beta`ya katkisi
    # eksi isaretiyle giriyor.
    beta_hedef = 1.0 - kutu["P_kacan_hedef"] / p_imp
    beta_mermi = -kutu["P_kacan_mermi"] / p_imp
    return {
        **kutu,
        "P_toplam": toplam, "p_imp": float(p_imp),
        "artik": float(artik),
        "artik_bagil": float(abs(artik) / p_imp),
        "kapandi": bool(abs(artik) / p_imp <= ARTIK_ESIGI),
        "beta_hedef": float(beta_hedef),
        "beta_mermi": float(beta_mermi),
        "beta_toplam": float(beta_hedef + beta_mermi),
        # P_ejekta VEKTORU (hedef maddesi, kacan). Yakinsama
        # calismasinda `beta` sabit kalirken acinin kaymasi
        # yakalanabilsin diye.
        "P_ejekta_vektor": [float(x) for x in
                            (m[kacan] * (1.0 - f[kacan])) @ v[kacan]],
        "P_ejekta_eksenel": float(kutu["P_kacan_hedef"]),
        "P_ejekta_buyukluk": float(np.linalg.norm(
            (m[kacan] * (1.0 - f[kacan])) @ v[kacan])),
        "M_ejekta": float(m[kacan] @ (1.0 - f[kacan])),
        # DELTA BETA: `beta`nin kendisi degil, `beta - 1` yakinsamali.
        # `beta = 1,030` ile `1,040` arasinda bagil fark %1 gorunur;
        # gercek ejekta katkisi `0,030 -> 0,040`, yani %33. `beta ~ 1`
        # rejiminde `beta` uzerinden esik koymak COK GEVSEK olur.
        "delta_beta_hedef": float(beta_hedef - 1.0),
        "n_kacan_hedef": int(np.count_nonzero(kacan & (f < 0.5))),
        "n_kacan_mermi": int(np.count_nonzero(kacan & (f >= 0.5))),
        "kutle_kacan_hedef": float(m[kacan] @ (1.0 - f[kacan])),
        "kutle_kacan_mermi": float(m[kacan] @ f[kacan]),
    }


def defter_satiri(d: dict) -> str:
    """Defteri tek bakışta okunur biçimde yaz."""
    return (
        f"  p_mermi          = {d['p_imp']:>14,.1f} kg m/s\n"
        f"  P_bagli_hedef    = {d['P_bagli_hedef']:>14,.1f}\n"
        f"  P_kacan_hedef    = {d['P_kacan_hedef']:>14,.1f}"
        f"   ({d['n_kacan_hedef']} parcacik, "
        f"{d['kutle_kacan_hedef']:,.1f} kg)\n"
        f"  P_bagli_mermi    = {d['P_bagli_mermi']:>14,.1f}\n"
        f"  P_kacan_mermi    = {d['P_kacan_mermi']:>14,.1f}"
        f"   ({d['n_kacan_mermi']} parcacik, "
        f"{d['kutle_kacan_mermi']:,.1f} kg)\n"
        f"  --------------------------------------------\n"
        f"  ARTIK            = {d['artik']:>14,.1f}"
        f"   (bagil {d['artik_bagil']:.2e})  "
        f"{'KAPANDI' if d['kapandi'] else 'KAPANMADI -- beta RAPORLANMAZ'}\n"
        f"  beta_hedef       = {d['beta_hedef']:>14.6f}   <- GERCEK\n"
        f"  beta_mermi       = {d['beta_mermi']:>14.6f}   <- geri tepme\n"
        f"  beta_toplam      = {d['beta_toplam']:>14.6f}")
