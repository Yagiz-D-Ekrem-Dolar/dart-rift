"""`β` **iki bağımsız yolla** ve ejekta koni açısı (ADR-0050).

## Neden

Raducan & Jutzi 2022 (*PSJ* 3, 128) `β`'yı iki yolla hesaplayıp
tutarlılığını sınıyor (`docs/LITERATUR-DART-SIMULASYONLARI.md` L1):

1. **Kaçan momentum:** kaçış hızını aşan maddenin momentumu. Depodaki
   karşılığı `momentum_defteri` (`r > R` ve `v_r > v_esc`).
2. **Kütle merkezi:** yeniden toplanmadan sonra cisimde **bağlı kalan**
   bütün maddenin momentumu (Bruck Syal ve diğ. 2016).

Hedef başta durgun ve toplam momentum korunduğu için ikisi ancak
**sınıflama** farkıyla ayrışır: (1) sabit yarıçap + sabit kaçış hızı,
(2) bağlı kütlenin öz-potansiyelinde enerji (`kacis.kacis_siniflari`).
Kısa koşuda fark büyüktür (yavaş madde henüz sınıflanmamış); uzun,
yerçekimli koşuda küçülmelidir. Fark bir **tanıdır**, kapı değil.

## Koni açısı

LICIACube ejekta konisini **140 ± 4°** açıklıkta gördü (Dotto ve diğ. 2024;
L17). Modelde koni: kaçan hedef maddesinin hız yönlerinin, ejekta
eksenine (kütle ağırlıklı ortalama yön) göre açılarının kütle ağırlıklı
`kesir` yüzdeliği; **tam açıklık** = 2 × bu yarı-açı.
"""
from __future__ import annotations

import numpy as np

from .gecerlilik import kutle_agirlikli_yuzdelik
from .kacis import G_SI, kacis_siniflari
from .momentum_defteri import momentum_defteri

__all__ = ["beta_kutle_merkezi", "beta_iki_yontem", "ejekta_koni_acisi"]


def beta_kutle_merkezi(x, v, m, *, R: float, ehat, p_imp: float,
                       G: float = G_SI, mermi_kesri=None) -> dict:
    """Yöntem 2 — bağlı kalan maddenin eksenel momentumu / `p_imp`.

    Bağlı küme `kacis_siniflari` ile (yinelemeli, öz-potansiyel). Mermi
    maddesi de bağlıysa cismin parçasıdır ve sayılır.

    > **Bu sayı ancak GEÇ zamanda anlamlıdır.** Ölçüldü (kaba sahne,
    > `t = 4e-4 s`): mermi hâlâ `~6 km/s` gittiği için enerjice **bağsız**
    > sayılıyor ve `β_km = 0,0004` çıkıyor — oysa kaçan-momentum yöntemi
    > `1,0` diyor. Yani erken zamanda fark, fizik değil **sınıflamadır**.
    > `mermi_bagsiz_kesri` bunu görünür kılar: `1`'e yakınsa `β_km`
    > okunmamalıdır. Literatürde de yöntem 2 yeniden toplanmadan SONRA
    > kullanılıyor (L1).
    """
    x = np.asarray(x, dtype=np.float64)
    v = np.asarray(v, dtype=np.float64)
    m = np.asarray(m, dtype=np.float64)
    if p_imp <= 0.0:
        raise ValueError(f"p_imp pozitif olmali, {p_imp} geldi")
    e = np.asarray(ehat, dtype=np.float64)
    e = e / np.linalg.norm(e)
    try:
        ks = kacis_siniflari(x, v, m, R=R, G=G)
    except ValueError as hata:
        # Baglilik siniflamasi TANIDIR, kapi degil: cozumsuz kaldiginda
        # (ornegin oz-yercekimi yaninda hizlarin buyuk oldugu kucuk cisim,
        # "bagli kume bosaldi") kosu DUSURULMEZ; sayi `nan` ve GEREKCE yazilir.
        return {"beta_km": float("nan"), "M_bagli": float("nan"),
                "P_bagli_vektor": [float("nan")] * 3, "yakinsadi": False,
                "n_tur": 0, "hata": str(hata)}
    bagli = ~np.asarray(ks["bagsiz_maske"], dtype=bool)
    P_bagli = m[bagli] @ v[bagli]
    out = {
        "beta_km": float(P_bagli @ e) / float(p_imp),
        "M_bagli": float(m[bagli].sum()),
        "P_bagli_vektor": [float(t) for t in P_bagli],
        "yakinsadi": bool(ks["yakinsadi"]),
        "n_tur": int(ks["n_tur"]),
    }
    if mermi_kesri is not None:
        f = np.asarray(mermi_kesri, dtype=np.float64)
        m_mermi = float((m * f).sum())
        out["mermi_bagsiz_kesri"] = (
            float((m * f)[~bagli].sum() / m_mermi) if m_mermi > 0.0
            else float("nan"))
    return out


def ejekta_koni_acisi(v, m, *, kesir: float = 0.9, eksen=None) -> dict:
    """Ejekta konisinin **tam** açıklığı [derece].

    `eksen` verilmezse kütle ağırlıklı ortalama hız yönü. Her parçacığın
    hız yönünün eksene açısı alınır; kütle ağırlıklı `kesir` yüzdeliği
    yarı-açıdır. Tek yönlü akışta `0`, yarım küreye düzgün yayılmada
    `kesir = 0,9` için ~`2 · 84°`.
    """
    v = np.asarray(v, dtype=np.float64)
    m = np.asarray(m, dtype=np.float64)
    if not (0.0 < kesir < 1.0):
        raise ValueError(f"kesir (0,1) olmali, {kesir} geldi")
    hiz = np.linalg.norm(v, axis=1)
    sec = (hiz > 0.0) & (m > 0.0)
    if not np.any(sec):
        return {"koni_tam_acisi_derece": float("nan"), "eksen": None,
                "kesir": float(kesir), "n": 0}
    u = v[sec] / hiz[sec, None]
    w = m[sec]
    if eksen is None:
        ort = w @ u
        if np.linalg.norm(ort) == 0.0:
            return {"koni_tam_acisi_derece": float("nan"), "eksen": None,
                    "kesir": float(kesir), "n": int(sec.sum())}
        eksen = ort / np.linalg.norm(ort)
    else:
        eksen = np.asarray(eksen, dtype=np.float64)
        eksen = eksen / np.linalg.norm(eksen)
    aci = np.degrees(np.arccos(np.clip(u @ eksen, -1.0, 1.0)))
    yari = kutle_agirlikli_yuzdelik(aci, w, 100.0 * kesir)
    return {"koni_tam_acisi_derece": float(2.0 * yari),
            "eksen": [float(t) for t in eksen], "kesir": float(kesir),
            "n": int(sec.sum())}


def beta_iki_yontem(x, v, m, *, mermi_kesri, R: float, v_esc: float, ehat,
                    p_imp: float, yari_eksenler=None, G: float = G_SI,
                    koni_kesri: float = 0.9) -> dict:
    """İki yöntem yan yana + fark + koni açısı + kaçan kütle."""
    f = np.asarray(mermi_kesri, dtype=np.float64)
    d = momentum_defteri(x, v, m, mermi_kesri=f, R=R, v_esc=v_esc, ehat=ehat,
                         p_imp=p_imp, yari_eksenler=yari_eksenler)
    km = beta_kutle_merkezi(x, v, m, R=R, ehat=ehat, p_imp=p_imp, G=G,
                            mermi_kesri=f)
    x = np.asarray(x, dtype=np.float64)
    v = np.asarray(v, dtype=np.float64)
    m = np.asarray(m, dtype=np.float64)
    r = np.linalg.norm(x, axis=1)
    vr = np.einsum("ij,ij->i", v, x) / np.maximum(r, 1e-300)
    if yari_eksenler is None:
        disarida = r > R
    else:
        from .momentum_defteri import disarida_maskesi

        disarida = disarida_maskesi(x, R=R, yari_eksenler=yari_eksenler)
    kacan = disarida & (vr > v_esc)
    koni = ejekta_koni_acisi(v[kacan], m[kacan] * (1.0 - f[kacan]),
                             kesir=koni_kesri)
    # GOZLEMLE ADIL KIYAS: LICIACube/HST koninin gorunen KENARINI olcuyor;
    # kutle yuzdeligi (%90) daha dar bir tanim. Kenar icin %99.
    kenar = ejekta_koni_acisi(v[kacan], m[kacan] * (1.0 - f[kacan]),
                              kesir=0.99)
    return {
        "beta_kacan": d["beta_toplam"],
        "beta_kacan_hedef": d["beta_hedef"],
        "beta_km": km["beta_km"],
        "fark_km_eksi_kacan": km["beta_km"] - d["beta_toplam"],
        "M_ejekta_hedef": d["M_ejekta"],
        "M_bagli": km["M_bagli"],
        "km_yakinsadi": km["yakinsadi"],
        "km_hatasi": km.get("hata"),
        # `1`'e yakinsa `beta_km` HENUZ okunamaz (mermi bagsiz sayiliyor).
        "mermi_bagsiz_kesri": km.get("mermi_bagsiz_kesri", float("nan")),
        "koni_tam_acisi_derece": koni["koni_tam_acisi_derece"],
        "koni_kesri": float(koni_kesri),
        "koni_kenar_derece": kenar["koni_tam_acisi_derece"],
        "defter_kapandi": bool(d["kapandi"]),
    }
