"""AV × çözünürlük raporu — Protokol F.

Soru: `α_av`'nin kazı akışı üzerindeki etkisi **çözünürlükte
yaşıyor mu**, yoksa kaba parçacık artefaktı mı?

A53 ölçtü (tek çözünürlükte):

    taban       93,21 kg  @  -1264   m/s   (JET)
    alpha_av 0,1 12 303 kg  @  -0,397 m/s   (KAZI AKISI olcegi)

Ama kaçan `33` parçacığın **hepsi kaba seviyeden**di. Doğru sınav bir
kademe ince merdivendi; A52 yüzünden `107` saat sürerdi. Bunun yerine
**mevcut iki ölçekte** tekrarlanıyor.

Ölçülen büyüklük `⟨v⟩ = P_kacan_hedef / kutle_kacan_hedef`. Tek başına
kütle ya da tek başına `Δβ` bu mekanizmayı **gizliyor**: kütle `132`
kat artarken `Δβ` `24` kat düşüyor ve ikisi ayrı okununca çelişki gibi
görünüyor. Çelişki değil — hız `3 188` kat düşmüş.

Kullanim:
    python scripts/av_raporu.py --kollar kampanya/F_*.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

# --- PROTOKOL F esikleri, SONUCLARDAN ONCE kilitlendi ---------------
#: `<v>` `alpha_av` ile MONOTON azalmali (buyuklukce). Beraberlik
#: sayilmaz: ardisik iki nokta arasinda en az bu kadar bagil fark
#: aranir, yoksa "duz" sayilir.
MONOTON_ESIGI = 0.10
#: Bir kolda kacanlarin TAMAMI en kaba seviyedense o kol "cozulmus
#: ejekta" SAYILMAZ (A36'da konan kural).
TEK_SEVIYE_REDDI = True

OLCEKLER = ("kaba", "orta")


def _oku(yol: Path) -> dict | None:
    try:
        d = json.loads(yol.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        print(f"OKUNAMADI {yol.name}: {e}", file=sys.stderr)
        return None
    md = d.get("momentum_defteri") or {}
    M = md.get("kutle_kacan_hedef")
    P = md.get("P_kacan_hedef")
    sev = md.get("ejekta_seviyeleri") or []
    ad = yol.stem                       # F_kaba_av01 gibi
    parca = ad.split("_")
    return {
        "ad": ad,
        "olcek": parca[1] if len(parca) > 2 else "?",
        "av_etiket": parca[2] if len(parca) > 2 else "?",
        "N": d.get("N"),
        "alpha_av": d.get("alpha_av"),
        "M_kacan": M,
        "P_kacan": P,
        "v_ort": (P / M) if (M and P is not None) else float("nan"),
        "n_kacan": md.get("n_kacan_hedef"),
        "delta_beta": (md["beta_hedef"] - 1.0) if "beta_hedef" in md else None,
        "artik_bagil": md.get("artik_bagil"),
        "sok": (d.get("sok") or {}).get("yargi"),
        "n_seviye": len(sev),
        "seviyeler": sev,
    }


def _av_degeri(etiket: str) -> float:
    """`av01` -> `0,1`; `av04` -> `0,4`; `av10` -> `1,0`."""
    sayi = "".join(c for c in etiket if c.isdigit())
    return float(sayi) / 10.0 if sayi else float("nan")


def monoton_azalan(degerler) -> dict:
    """`|⟨v⟩|` `α_av` azalırken **azalıyor** mu (eşikli)."""
    v = [abs(x) for x in degerler]
    if len(v) < 2 or not all(np.isfinite(v)):
        return {"monoton": False, "sebep": "yetersiz/gecersiz nokta"}
    adimlar = []
    for a, b in zip(v, v[1:]):
        buyuk = max(abs(a), abs(b), 1e-300)
        adimlar.append((a - b) / buyuk)
    if all(x > MONOTON_ESIGI for x in adimlar):
        return {"monoton": True, "adimlar": adimlar, "sebep": ""}
    if all(x < -MONOTON_ESIGI for x in adimlar):
        return {"monoton": False, "adimlar": adimlar,
                "sebep": "ters yonde monoton"}
    return {"monoton": False, "adimlar": adimlar,
            "sebep": "duz ya da tutarsiz"}


def tek_seviye_mi(k: dict) -> bool:
    """Kaçanların **tamamı** tek (en kaba) seviyeden mi."""
    return bool(k["seviyeler"]) and len(k["seviyeler"]) == 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kollar", nargs="+", type=Path, required=True)
    ap.add_argument("--json", type=Path, default=None)
    a = ap.parse_args(argv)

    kayit = [k for k in (_oku(y) for y in a.kollar) if k]
    for k in kayit:
        k["av"] = (k["alpha_av"] if k["alpha_av"] is not None
                   else _av_degeri(k["av_etiket"]))

    print("=" * 78)
    print("AV x COZUNURLUK RAPORU -- Protokol F")
    print("=" * 78)
    print(f"\n{'kol':16} {'N':>8} {'a_av':>6} {'M_kacan kg':>13} "
          f"{'<v> m/s':>11} {'n':>5} {'sev':>4} {'sok':>7}")
    for k in sorted(kayit, key=lambda z: (z["olcek"], -(z["av"] or 0))):
        print(f"{k['ad']:16} {k['N'] or 0:8d} {k['av']:6.2f} "
              f"{k['M_kacan'] or float('nan'):13.5g} "
              f"{k['v_ort']:11.4g} {k['n_kacan'] or 0:5d} "
              f"{k['n_seviye']:4d} {str(k['sok']):>7}")

    # --- gecerlilik ---
    print("\n" + "=" * 78)
    print("GECERLILIK")
    gecersiz = []
    for k in kayit:
        if k["sok"] == "SOK_YOK":
            gecersiz.append(f"{k['ad']}: sok yargisi SOK_YOK (ADR-0049)")
        if k["artik_bagil"] is None or abs(k["artik_bagil"]) > 1e-10:
            gecersiz.append(f"{k['ad']}: defter KAPALI DEGIL "
                            f"({k['artik_bagil']})")
    if TEK_SEVIYE_REDDI:
        for k in kayit:
            if tek_seviye_mi(k):
                print(f"  ! {k['ad']}: kacanlarin TAMAMI tek seviyeden "
                      f"-> 'cozulmus ejekta' SAYILMAZ (A36)")
    for g in gecersiz:
        print(f"  X {g}")
    if not gecersiz:
        print("  tum kollar gecerli")

    # --- monotonluk, olcek basina ---
    print("\n" + "=" * 78)
    print("MONOTONLUK  (|<v>| alpha_av azalirken azaliyor mu)")
    sonuc = {}
    for olcek in OLCEKLER:
        kol = sorted([k for k in kayit if k["olcek"] == olcek],
                     key=lambda z: -(z["av"] or 0))
        if len(kol) < 2:
            print(f"  {olcek:6}: yetersiz kol ({len(kol)})")
            sonuc[olcek] = {"monoton": False, "sebep": "yetersiz kol"}
            continue
        m = monoton_azalan([k["v_ort"] for k in kol])
        sonuc[olcek] = m
        oklar = " -> ".join(f"{k['av']:.1f}:{abs(k['v_ort']):.4g}" for k in kol)
        print(f"  {olcek:6}: {oklar}")
        print(f"          {'MONOTON' if m['monoton'] else 'DEGIL'}"
              f"{'  (' + m['sebep'] + ')' if m['sebep'] else ''}")

    # --- YARGI (kilitli) ---
    print("\n" + "=" * 78)
    kaba_ok = sonuc.get("kaba", {}).get("monoton", False)
    orta_ok = sonuc.get("orta", {}).get("monoton", False)
    if gecersiz:
        yargi = "OKUNMAZ -- gecersiz kol var"
    elif kaba_ok and orta_ok:
        yargi = ("AV GERCEK BIR KONTROL PARAMETRESI -- mekanizma surekli "
                 "ve iki olcekte de duruyor")
    elif kaba_ok != orta_ok:
        gor = "kaba" if kaba_ok else "orta"
        yargi = (f"COZUNURLUK ARTEFAKTI SUPHESI -- etki yalniz '{gor}' "
                 f"olcekte gorunuyor")
    else:
        yargi = "ETKI YOK ya da TUTARSIZ -- AV aday olmaktan cikar"
    print(f"YARGI: {yargi}")

    if a.json:
        a.json.write_text(json.dumps(
            {"kollar": kayit, "monotonluk": sonuc, "gecersiz": gecersiz,
             "yargi": yargi}, indent=2, default=str), encoding="utf-8")
        print(f"\nyazildi: {a.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
