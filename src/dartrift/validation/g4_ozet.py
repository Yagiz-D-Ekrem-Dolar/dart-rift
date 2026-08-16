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

__all__ = ["faz44_ozet", "faz45_ozet", "esit_t_mi"]


def _ince_kol(sonuclar: dict, ek: str) -> list:
    """Verilen ekli (`_Aprime` / `_tek_h`) **tamamlanmış** kolları döndür.

    `durum == "kismi"` olan kollar **dışlanır**: `t_end`'e ulaşmamış bir
    koşunun `β`'sı sistematik olarak küçük çıkar ve tam da *"yakınsamıyor"*
    gibi görünür (ADR-0011 §3'ün dersi).
    """
    return [(ad, y) for ad, y in sonuclar.items()
            if ad.endswith(ek) and y.get("durum") == "tamam"
            and np.isfinite(y.get("beta_son", float("nan")))]


def esit_t_mi(sonuclar: dict, tol: float = 1.0e-6) -> bool:
    """Tamamlanmış kolların hepsi **aynı** `t_sim`'e mi ulaştı?

    B1 ve B3 farklı `t`'deki `β`'ları kıyaslayamaz. Bu kontrol olmadan
    özet sessizce anlamsız bir sayı üretirdi (sıkıntı A6).
    """
    ts = [y["t_sim"] for y in sonuclar.values()
          if y.get("durum") == "tamam" and "t_sim" in y]
    if len(ts) < 2:
        return False
    return bool((max(ts) - min(ts)) / max(max(ts), 1e-300) < tol)


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

    # --- A2 / A3 ve TANILAR: gecerliyse tepe duzeyde tasinir.
    for anahtar, kaynak in (("A2_r_ince_carpani", "A2_r_ince_carpani"),
                            ("A3_kutle_sapmasi", "A3_kutle_sapmasi"),
                            ("dikis_en_yakin_oran", "dikis_en_yakin_oran"),
                            ("tasarruf", "tasarruf")):
        if kaynak in ham and np.isfinite(ham[kaynak]):
            out[anahtar] = float(ham[kaynak])

    # --- B1: en ince IKI A' kolu arasindaki GORELI beta farki.
    # "En ince" = en cok parcacikli. Iki kol yoksa B1 KOSULMAMISTIR.
    #
    # ESIT t SARTI: kollar farkli t_sim'e ulastiysa B1 yakinsama OLCMEZ.
    # Bu durumda anahtar HIC YAZILMAZ ve kapi "kosulmadi" der -- yanlis
    # bir sayi yazmaktan iyidir.
    esit_t = esit_t_mi(son)
    out["esit_t_sim"] = bool(esit_t)
    if len(ap) >= 2 and esit_t:
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
    if len(eslesen) >= 2 and esit_t:
        # Referans: EN INCE kurulumun A' sonucu (en cok cozulmus olan).
        sirali = sorted(ap, key=lambda t: t[1]["N"])
        ref = sirali[-1][1]["beta_son"]
        # EN KABA kurulumda A' ve tek h'yi referansa uzakliklariyla kiyasla.
        #
        # KUSUR: burada `eslesen[0]` yaziyordu, yani SOZLUK SIRASINDAKI ilk
        # kol. Yorum "en kaba kurulumda" diyordu ama kod onu secmiyordu.
        # Python 3.7+'da sozluk sirasi EKLEME sirasidir; kosucu kollari
        # kaba->ince ekledigi icin SU AN dogru sonucu veriyordu, ama
        # kosucunun dongu sirasi degistigi anda SESSIZCE yanlis kola
        # bakardi. Bagimlilik acikca yaziliyor.
        N_kok = {ad[: -len("_Aprime")]: y["N"] for ad, y in ap}
        kok, b_ap, b_tek = min(eslesen, key=lambda t: N_kok[t[0]])
        d_ap, d_tek = abs(b_ap - ref), abs(b_tek - ref)
        out["B3_Aprime_daha_yakin"] = 1.0 if d_ap < d_tek else 0.0
        out["B3_ayrinti"] = {"kurulum": kok, "referans_beta": float(ref),
                             "Aprime_uzaklik": float(d_ap),
                             "tek_h_uzaklik": float(d_tek)}
    return out


def faz45_ozet(ham: dict) -> dict:
    """`measure_longrun.py` çıktısı → G4-B2 ve B4 anahtarları.

    ## `B2` **sabit** seride yazılmaz

    `β_bound` bağlı parçacıkların momentumundan geliyor. Hiçbir parçacık
    kaçış eşiğini geçmediyse baştan sona **sabit** kalır ve durulma
    sınavı `durulmus = True` der — teknik olarak doğru, ama *"`β` yerleşti"*
    diye okunamaz: yerleşen bir şey yok, **ölçüm duyarsız**.

    Böyle bir seride `B2`'yi `1,0` yazmak kapıyı **boş bir kanıtla**
    geçirirdi. Anahtar hiç yazılmıyor → kapı `koşulmadı` diyor. Bu,
    `esit_t_mi`'nin `B1`/`B3` için yaptığının aynısı (sıkıntı A6).

    ## `B2` **yolda madde** varken de yazılmaz (A9)

    Serinin düz olmasının iki sebebi var ve seriden ayırt edilemezler:
    kazı bitti, ya da madde henüz `r > R`'yi geçmedi. İkincisinde `β`
    düzdür ama **yerleşmemiştir**. Ölçüldü: DART koşusunda `t = 20 s`'de
    `2786` parçacık hâlâ yolda, geçiş süresi medyan `57–75 s`.

    Ham çıktı bu tanıyı taşıyorsa kullanılır. **Taşımıyorsa** `B2` yine
    yazılır ama `B2_gecis_denetlenmedi` bayrağı kalkar — bilinmeyeni
    sessizce *"geçti"* saymak tam da A9'un şikâyetiydi.
    """
    out: dict = {}
    tani = ham.get("beta_bound_settling_diag") or {}
    sabit = bool(tani.get("sabit", False))
    out["B2_sabit_seri"] = sabit

    # --- YOLDA MADDE SINAVI (sikinti A9'un kapanisi)
    #
    # Serinin duz olmasinin IKI sebebi var ve seriden ayirt edilemezler:
    # kazi bitti, ya da madde henuz `r > R`'yi gecmedi. Ikincisinde
    # `beta` duzdur ama YERLESMEMISTIR. Olculdu: DART kosusunda
    # `t = 20 s`'de 2786 parcacik hala yolda, gecis suresi medyan 57-75 s.
    #
    # Ham cikti bu taniyi tasiyorsa kullanilir; TASIMIYORSA B2 yine
    # yazilir ama `B2_gecis_denetlenmedi` bayragi kalkar. Bilinmeyeni
    # sessizce "gecti" saymak tam da A9'un sikayetiydi.
    bek = None
    for anahtar in ("n_bekleyen_son", "n_bekleyen", "bekleyen_son"):
        if anahtar in ham:
            v = ham[anahtar]
            bek = int(v[-1]) if isinstance(v, (list, tuple)) and v else (
                int(v) if isinstance(v, (int, float)) else None)
            break
    out["B2_gecis_denetlenmedi"] = bek is None
    if bek is not None:
        out["B2_yolda_madde"] = int(bek)

    if "beta_bound_settled" in ham and not sabit:
        durulmus = bool(ham["beta_bound_settled"])
        if bek is not None and bek > 0:
            # Yolda madde VAR: seri duz olsa da B2 yazilmaz -> kapi
            # "kosulmadi" der. `esit_t_mi`nin B1/B3 icin yaptiginin aynisi.
            pass
        else:
            out["B2_durulmus"] = 1.0 if durulmus else 0.0
    egim = ham.get("energy_drift_loglog_slope")
    if egim is not None and np.isfinite(egim):
        out["B4_enerji_egim"] = float(egim)
    return out
