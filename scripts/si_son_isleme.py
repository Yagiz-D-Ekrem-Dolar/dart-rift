"""PROTOKOL-SI son işleme — kaydedilmiş durumlardan, **sıfır GPU**.

Protokol 2026-10-08'de, ölçümler yapılmadan ÖNCE kilitlendi. Bu betik
yalnız onu **uygular**; hiçbir eşik burada seçilmez.

## Hangi ölçümler koşuyor

| § | ölçüm | durum |
|---|---|---|
| 2 | iki kaçış ölçütü (`b_sistem`) | **BLOKE** — Didymos kütlesi/`a` teyitsiz |
| 3 | yörünge hızına projeksiyon | **BLOKE** — aynı |
| 4 | balistik son işleme | **BLOKE** — aynı |
| 5 | spin / açısal momentum | koşuyor (yargı periyot teyidine bağlı) |
| 6 | yoğunluk / sıkışma | koşuyor |
| 7 | şekil değişimi | koşuyor |

Protokolün ortak künye kuralı: *"teyit edilmemiş sabitle koşulan ölçüm
OKUNMAZ sayılır."* §2–§4 Didymos kütlesini ve yörünge yarı eksenini
ister; ikisi de "teyit bekliyor" satırında. §5–§7 yalnız cismin **kendi**
durumunu kullandığı için blokeli değildir. §5'in sayısı (`|L|`, `ω`)
koşar; yüzde cinsinden **yargısı** çarpma öncesi dönme periyodunu
gerektirdiğinden teyide kadar `TEYIT_BEKLIYOR` olarak işaretlenir.

## Kaçış hızı neden geri çözülüyor

Etkin yarıçap koşunun içindeki bir ayrıntı ve `npz`'de yok; tahmin etmek
bütün ölçümleri sessizce kaydırır. Bunun yerine koşunun kendi yazdığı
`fizik_tani["ejekta_ayrismasi"]["M_kacan"]`'dan ikiye bölmeyle geri
çözülür. Çözüm **kendi kendini doğrular**: bulunan eşikle hesaplanan
kütle `M_kacan`'ı makine hassasiyetinde vermiyorsa kayıt OKUNMAZ.

Çerçeve ve ağırlık ampirik olarak belirlendi (2026-10-13): kütle merkezi
çerçevesi + **mermi hariç** hedef kütlesi, bağıl hata `2,6e-16`. Lab
çerçevesi ya da mermi dahil ağırlık `1e-5`–`1e-4` sapma veriyor.

NOT: Depoda `observables/aday_gozlemliler.kacis_hizi_kalibre` aynı işi
yapıyor; TRUBA çalışma ağacı `SABIT_COMMIT`'e sabitli olduğu ve o modül
daha sonra yazıldığı için burada bağımsız, kendi kendini doğrulayan bir
çözüm kullanılıyor. Ağaç ilerletilince o fonksiyona geçilmelidir.

    python scripts/si_son_isleme.py "<glob>" [--json cikti.json]
"""

from __future__ import annotations

import argparse
import glob as globmod
import json
import math
from pathlib import Path

import numpy as np

#: Geri çözümün kabul edilen bağıl hatası. Üstündeyse kayıt OKUNMAZ.
KACIS_TOLERANS = 1e-9

#: §5 ve §6 kilitli yargı eşikleri (PROTOKOL-SI).
ESIK_SPIN_PERIYOT = 0.01      # periyot değişimi > %1 -> OLCULEBILIR
ESIK_SIKISMA = 0.01           # |Δρ/ρ| > %1 -> OLCULEBILIR
ASGARI_BAGLI = 1000           # altındaysa OKUNMAZ

#: Çarpma öncesi dönme periyodu — PROTOKOL-SI ortak künyesinde
#: "TEYIT BEKLIYOR". Yalnız bilgi amaçlı; yargı bununla VERILMEZ.
P_KILITLI_TEYITSIZ_S = 11.92 * 3600.0


def kacis_hizi_geri_coz(v: np.ndarray, m: np.ndarray, mermi_kesri: np.ndarray,
                        m_kacan: float) -> tuple[float, float, np.ndarray]:
    """`v_esc`'i koşunun kendi `M_kacan`'ından geri çöz.

    Kural `observables/aday_gozlemliler.kacis_hizi_kalibre` ile BİREBİR
    aynıdır (o modül TRUBA'daki sabit commit'te yok; ağaç ilerletilince
    doğrudan o fonksiyon çağrılmalı):

    * `mermi_kesri > 0,5` olan parçacıklar **tamamen atılır** — kütleyle
      ağırlıklandırılmaz. Hedef maddesi ölçülüyor.
    * Hız **lab çerçevesinde**; kütle merkezi ÇIKARILMAZ.
    * Kalan parçacıkların tam kütlesi kullanılır.

    Bu bileşim 2026-10-13'te 72 durum dosyasının 72'sinde `M_kacan`'ı
    `3,4e-14` azami bağıl hatayla veriyor. Üç yanlış aday denendi ve
    hepsi bir kısım dosyada `1e-5`–`3e-2` sapma verdi: kütle merkezi
    çerçevesi, `m(1-mermi_kesri)` ağırlığı, ve öz-tutarlı (yinelemeli)
    kütle merkezi. Ölçütü tahmin etmek bütün ölçümleri sessizce kaydırır.

    Dönen: `(v_esc, bağıl_hata, hedef_maskesi)`.
    """
    hedef = ~(mermi_kesri > 0.5)
    hiz = np.linalg.norm(v[hedef], axis=1)
    mh = m[hedef]
    s = np.argsort(hiz)[::-1]
    kum = np.cumsum(mh[s])
    hs = hiz[s]
    k = int(np.searchsorted(kum, m_kacan * (1.0 - KACIS_TOLERANS)))
    if k >= kum.size:
        return float("nan"), float("inf"), hedef
    hata = abs(float(kum[k]) - m_kacan) / m_kacan
    # `hs` azalan sırada; eşik [hs[k+1], hs[k]) aralığında olmalı ki tam
    # 0..k parçacığı geçsin.
    alt = float(hs[k + 1]) if (k + 1) < hs.size else 0.0
    return 0.5 * (alt + float(hs[k])), hata, hedef


def olc(yol: str) -> dict:
    d = np.load(yol, allow_pickle=False)
    ad = Path(yol).name
    out: dict = {"dosya": ad, "theta": [float(t) for t in d["theta"]],
                 "t": float(d["t"])}

    gec = json.loads(str(d["gecerlilik"]))
    if not gec.get("gecerli", False):
        out["genel"] = "OKUNMAZ (kosu gecersiz)"
        return out

    x, v, m = d["x"], d["v"], d["m"]
    xr, al, al0 = d["x_referans"], d["alpha"], d["alpha0"]
    mk = d["mermi_kesri"]
    ft = json.loads(str(d["fizik_tani"]))
    m_kacan = float(ft["ejekta_ayrismasi"]["M_kacan"])

    # --- kaçış hızı: geri çöz ve DOĞRULA -------------------------------
    v_esc, hata, hedef = kacis_hizi_geri_coz(v, m, mk, m_kacan)
    out["v_esc"] = v_esc
    out["kacis_geri_cozum_hatasi"] = hata
    if not (hata <= KACIS_TOLERANS):
        out["genel"] = f"OKUNMAZ (kacis geri cozumu tutmadi: {hata:.2e})"
        return out

    # Bağlı = hedef maddesi (mermi ayıklanmış) VE lab hızı eşiğin altında.
    bagli = hedef & (np.linalg.norm(v, axis=1) <= v_esc)
    n_bagli = int(bagli.sum())
    vkm = ((m[bagli, None] * v[bagli]).sum(0) / m[bagli].sum()
           if n_bagli else np.zeros(3))
    out["n_bagli"] = n_bagli
    if n_bagli < ASGARI_BAGLI:
        out["genel"] = f"OKUNMAZ (bagli parcacik {n_bagli} < {ASGARI_BAGLI})"
        return out

    # Spin BAĞLI malzemenin kendi çerçevesinde ölçülür: kaçan madde
    # cismin dönmesine değil, sistemin momentumuna gider.
    mb = m[bagli]
    Mb = float(mb.sum())
    rkm = (mb[:, None] * x[bagli]).sum(0) / Mb
    rb = x[bagli] - rkm
    vb = v[bagli] - vkm

    # --- §5 spin / açısal momentum -------------------------------------
    L = (mb[:, None] * np.cross(rb, vb)).sum(0)
    r2 = (rb ** 2).sum(1)
    eylem = (np.einsum("i,jk->jk", mb * r2, np.eye(3))
             - np.einsum("i,ij,ik->jk", mb, rb, rb))
    w = np.linalg.solve(eylem, L)
    w_buy = float(np.linalg.norm(w))
    out["spin"] = {
        "L_buyukluk": float(np.linalg.norm(L)),
        "L_yon": (L / np.linalg.norm(L)).tolist(),
        "omega": w_buy,
        "I_ozdegerleri": np.linalg.eigvalsh(eylem).tolist(),
        # Teyitsiz sabitle hesaplanan BILGI; yargi bununla verilmez.
        "periyot_degisimi_TEYITSIZ":
            w_buy / (2.0 * math.pi / P_KILITLI_TEYITSIZ_S),
        "yargi": "TEYIT_BEKLIYOR (carpma oncesi donme periyodu)",
    }

    # --- §6 yoğunluk / sıkışma -----------------------------------------
    d_alpha = float(np.average(al[bagli] / al0[bagli] - 1.0, weights=mb))
    # Hacim p99,5 kabuğundan; protokol iki yüzdelikle duyarlılık istiyor.
    hacimler = {}
    for yuzde in (99.0, 99.5):
        Rk = float(np.percentile(np.linalg.norm(rb, axis=1), yuzde))
        hacimler[f"p{yuzde}"] = {"R": Rk,
                                 "rho": Mb / (4.0 / 3.0 * math.pi * Rk ** 3)}
    out["sikisma"] = {
        "d_alpha_kutle_agirlikli": d_alpha,
        "hacim_duyarliligi": hacimler,
        "yargi": ("SIKISMA OLCULEBILIR" if abs(d_alpha) > ESIK_SIKISMA
                  else "SIKISMA KUCUK"),
    }

    # --- §7 şekil --------------------------------------------------------
    yer = np.linalg.norm((x - xr)[bagli], axis=1)
    out["sekil"] = {
        "yerdegistirme_ortanca": float(np.median(yer)),
        "yerdegistirme_p90": float(np.percentile(yer, 90)),
        "yerdegistirme_p99": float(np.percentile(yer, 99)),
        "yerdegistirme_azami": float(yer.max()),
        "yari_eksenler_son": sorted(
            float(np.sqrt(5.0 / 2.0 * (ldeg / Mb)))
            for ldeg in np.linalg.eigvalsh(eylem))[::-1],
    }

    out["genel"] = "OLCULDU"
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("desen", help="npz glob deseni")
    ap.add_argument("--json", type=Path, default=None)
    a = ap.parse_args(argv)

    yollar = sorted(globmod.glob(a.desen))
    if not yollar:
        print(f"dosya yok: {a.desen}")
        return 2

    kayitlar = [olc(y) for y in yollar]
    okunan = [k for k in kayitlar if k.get("genel") == "OLCULDU"]

    print(f"durum dosyasi : {len(kayitlar)}")
    print(f"okunan        : {len(okunan)}")
    for k in kayitlar:
        if k.get("genel") != "OLCULDU":
            print(f"  ATLANDI {k['dosya']}: {k.get('genel')}")

    if okunan:
        print(f"\n{'alpha_b':>8s} {'Y0':>9s} {'f':>6s} {'bagli':>6s} "
              f"{'omega':>10s} {'dP/P*':>7s} {'d_alpha':>9s} {'yer_med':>8s}")
        for k in okunan:
            t = k["theta"]
            s, si, se = k["spin"], k["sikisma"], k["sekil"]
            print(f"{t[0]:8.4f} {t[1]:9.2f} {t[2]:6.3f} {k['n_bagli']:6d} "
                  f"{s['omega']:10.3e} "
                  f"{100 * s['periyot_degisimi_TEYITSIZ']:6.1f}% "
                  f"{si['d_alpha_kutle_agirlikli']:+9.2e} "
                  f"{se['yerdegistirme_ortanca']:8.3f}")
        print("\n* dP/P TEYITSIZ sabitle hesaplandi (carpma oncesi periyot);")
        print("  PROTOKOL-SI ortak kunye kurali geregi YARGI DEGILDIR.")

    if a.json:
        a.json.write_text(json.dumps(kayitlar, indent=1, ensure_ascii=False),
                          encoding="utf-8")
        print(f"\nyazildi: {a.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
