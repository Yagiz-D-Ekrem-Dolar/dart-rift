"""Ölçüm çıktılarını **G4 kapısının anahtarlarına** çevir.

## Neden ayrı bir katman

`faz44_dart_yakinsama.py` zengin bir sözlük yazıyor (her kol için `β`
izleri, adım sayıları, tanılar). `g4_gate.degerlendir` ise **düz** ve
**adlandırılmış** ölçütler bekliyor (`A1_mermi_parcacik_cap`, …).

İkisini doğrudan bağlamak iki sorun yaratırdı:

1. Koşucu betiği kapının şemasını **bilmek** zorunda kalırdı; kapı
   değişince koşucu bozulurdu.
2. Özetleme mantığı (hangi kol A1'i verir, `B1` hangi iki çözünürlük
   arasındaki fark) betiğin içinde **sınanamaz** biçimde gömülü kalırdı
   — tam olarak `measure_longrun`'daki plato mantığının başına gelen şey.

Bu modül o mantığı dışarı alır ve sınanabilir yapar.

## `B1` nasıl tanımlanıyor

*"Ardışık çözünürlükte `β` farkı"* — en ince iki A′ kolu arasındaki
**göreli** fark. Mutlak fark değil, çünkü `β` mertebesi kurulumla
değişir; kapı eşiği (`%10`) göreli.

## `B3` nasıl tanımlanıyor

A′ kolu, tek-`h` kolundan **tekdüze ince** sonuca daha yakın olmalı.
KAYIT-037 küp geometrisinde `%67,1` vs `%9,1` ölçtü; burada aynı yönün
DART geometrisinde de tuttuğu sınanıyor.

> `B3` bir **oran** değil, bir **evet/hayır**tır: `1,0` ya da `0,0`.
> Eşik keyfî olmasın diye böyle; yön tutuyorsa geçer.
"""
from __future__ import annotations

import numpy as np

__all__ = ["faz44_ozet", "faz45_ozet"]


def _ince_kol(sonuclar: dict, ek: str) -> list:
    """Verilen ekli (`_Aprime` / `_tek_h`) **tamamlanmış** kolları döndür."""
    return [(ad, y) for ad, y in sonuclar.items()
            if ad.endswith(ek) and y.get("durum") == "tamam"
            and np.isfinite(y.get("beta_son", float("nan")))]


def faz44_ozet(ham: dict) -> dict:
    """`faz44_dart_yakinsama.py` çıktısı → G4-A ve G4-B anahtarları.

    Eksik/koşulamamış ölçütler **yazılmaz** — kapı onları `koşulmadı`
    sayar. Bir anahtarı `nan` ile doldurmak da aynı sonucu verir ama
    hiç yazmamak niyeti daha açık gösterir.
    """
    out: dict = {}
    son = ham.get("sonuclar", {})
    ap = _ince_kol(son, "_Aprime")
    if not ap:
        return out

    # --- A1: mermi capi / yerel aralik. Butun kollarda ayni olmali;
    # EN KOTUSU alinir (kapi en zayif halkadan gecer).
    a1 = [y["mermi_parcacik_cap"] for _, y in ap
          if np.isfinite(y.get("mermi_parcacik_cap", float("nan")))]
    if a1:
        out["A1_mermi_parcacik_cap"] = float(min(a1))

    # --- A2 / A3: gecerliyse tepe duzeyde tasinir.
    for anahtar, kaynak in (("A2_r_ince_carpani", "A2_r_ince_carpani"),
                            ("A3_kutle_sapmasi", "A3_kutle_sapmasi")):
        if kaynak in ham and np.isfinite(ham[kaynak]):
            out[anahtar] = float(ham[kaynak])

    # --- B1: en ince IKI A' kolu arasindaki GORELI beta farki.
    # "En ince" = en cok parcacikli. Iki kol yoksa B1 KOSULMAMISTIR.
    if len(ap) >= 2:
        sirali = sorted(ap, key=lambda t: t[1]["N"])
        b1, b2 = sirali[-2][1]["beta_son"], sirali[-1][1]["beta_son"]
        payda = max(abs(b2), 1e-300)
        out["B1_beta_farki"] = float(abs(b2 - b1) / payda)
        out["B1_kollar"] = [sirali[-2][0], sirali[-1][0]]

    # --- B3: A' tekduze inceye tek h'den DAHA YAKIN mi?
    # Karsilastirma AYNI kurulumda yapilir; eslesmeyen kollar atlanir.
    eslesen = []
    for ad, y in ap:
        kok = ad[: -len("_Aprime")]
        esi = son.get(kok + "_tek_h")
        if esi and esi.get("durum") == "tamam" and np.isfinite(
                esi.get("beta_son", float("nan"))):
            eslesen.append((kok, y["beta_son"], esi["beta_son"]))
    if len(eslesen) >= 2:
        # Referans: EN INCE kurulumun A' sonucu (en cok cozulmus olan).
        sirali = sorted(ap, key=lambda t: t[1]["N"])
        ref = sirali[-1][1]["beta_son"]
        # En kaba kurulumda A' ve tek h'yi referansa uzakliklariyla kiyasla.
        kok, b_ap, b_tek = eslesen[0]
        d_ap, d_tek = abs(b_ap - ref), abs(b_tek - ref)
        out["B3_Aprime_daha_yakin"] = 1.0 if d_ap < d_tek else 0.0
        out["B3_ayrinti"] = {"kurulum": kok, "referans_beta": float(ref),
                             "Aprime_uzaklik": float(d_ap),
                             "tek_h_uzaklik": float(d_tek)}
    return out


def faz45_ozet(ham: dict) -> dict:
    """`measure_longrun.py` çıktısı → G4-B2 ve B4 anahtarları."""
    out: dict = {}
    if "beta_bound_settled" in ham:
        out["B2_durulmus"] = 1.0 if bool(ham["beta_bound_settled"]) else 0.0
    egim = ham.get("energy_drift_loglog_slope")
    if egim is not None and np.isfinite(egim):
        out["B4_enerji_egim"] = float(egim)
    return out
