"""Protokol J — sabit `h`'de zaman adımı + `ara` akma kipi raporu.

Rapor A72 / uzman yanıtı (2026-09-11): kuvvet **geri döndürülmemiş**
deneme gerilmesini görüyor; fazlalık `~ (√3/2) G γ̇ Δt`. Sabit
uzamsal çözünürlükte `Δt` yarılanınca `x₀` kayıyor mu, ve `ara`
kipi (her kuvvet çağrısından önce akma yüzeyine dönüş) bunu
kaldırıyor mu?

Yargı kuralları `docs/truba/PROTOKOL-J-ZAMAN-ADIMI.md`'de, **koşudan
önce** yazıldı. Eşikler aşağıda kilitli.

Kullanim:
    python scripts/dt_raporu.py --kok kampanya --seri J1
    python scripts/dt_raporu.py --kok kampanya --seri J2
    python scripts/dt_raporu.py --kok kampanya --i2
    python scripts/dt_raporu.py --kok kampanya --tekrar   # J1_son_c0250 <-> G1
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path

import numpy as np

_BURASI = Path(__file__).resolve().parent
sys.path.insert(0, str(_BURASI))

# --- PROTOKOL J esikleri, SONUCLARDAN ONCE kilitlendi ------------------
#: O1 -- kol basina tamamlanan nokta / tasarim.
TAMAMLANMA_ESIGI = 0.90
#: 24 theta x 2 sahne gerceklemesi.
N_TASARIM = 48
#: Y1 / Y2 -- fark bu kadar sigmayi astiginda "etkili".
J_SIGMA = 2.0
#: Y2 -- `ara` kolunun farki `son` farkinin en fazla bu kesri olmali.
ARA_KALDIRMA_ORANI = 0.5
#: O3 -- `ara` kollarinda kuvvet aninda q/Y(P) tavani.
ARA_ORAN_TAVANI = 1.0 + 1.0e-9
#: O4 -- J1_son_c0250 <-> G1 bit-tekrar esigi (bagil, medyan).
TEKRAR_ESIGI = 1.0e-9
#: Protokol I'nin olctugu kayma (orta - kaba), `son` kipinde.
I_KAYMA = 5.950 - 6.340

#: Kol sirasi: (akma kipi, cfl etiketi, cfl).
KOLLAR = (("son", "c0250", 0.25), ("son", "c0125", 0.125),
          ("son", "c0625", 0.0625), ("ara", "c0250", 0.25),
          ("ara", "c0125", 0.125), ("ara", "c0625", 0.0625))


def _gr():
    import gecis_raporu as gr

    return gr


# --- saf yargi fonksiyonlari (sinanabilir) -----------------------------

def okunabilir(kol: dict) -> tuple[bool, str]:
    """O1 - O3. `kol` en az: ad, tamamlanma, gecerli, kip, ara_oran_max."""
    sebep = []
    if not (kol.get("tamamlanma", 0.0) >= TAMAMLANMA_ESIGI):
        sebep.append(f"{kol['ad']}: tamamlanma {kol.get('tamamlanma', 0):.2f}"
                     f" < {TAMAMLANMA_ESIGI}")
    if not kol.get("gecerli", False):
        sebep.append(f"{kol['ad']}: sigmoid GECERSIZ (R2/x0 araligi)")
    if kol.get("kip") == "ara":
        o = kol.get("ara_oran_max", float("nan"))
        if not (np.isfinite(o) and o <= ARA_ORAN_TAVANI):
            sebep.append(f"{kol['ad']}: ara kolunda kuvvet aninda "
                         f"q/Y = {o:.6g} > {ARA_ORAN_TAVANI} (UYGULAMA KUSURU)")
    return (not sebep), "; ".join(sebep)


def _fark(a: dict, b: dict) -> tuple[float, float, float]:
    d = float(b["x0"] - a["x0"])
    s = float(np.sqrt(a["sigma_x0"] ** 2 + b["sigma_x0"] ** 2))
    return d, s, (abs(d) / s if s > 0 else float("inf"))


def y1_yargi(k25: dict, k0625: dict, k0125: dict | None = None) -> dict:
    """Y1 -- `son` kipinde zaman adimi yolu var mi."""
    for k in (k25, k0625):
        ok, sebep = okunabilir(k)
        if not ok:
            return {"karar": "OKUNMAZ", "sebep": sebep}
    d, s, kat = _fark(k25, k0625)
    if kat >= J_SIGMA:
        karar = ("ZAMAN ADIMI YOLU GOSTERILDI" if d < 0
                 else "ZAMAN ADIMI ETKILI, TERS YON")
    else:
        karar = "DT YOLU GOSTERILEMEDI"
    pay = float("nan")
    if k0125 is not None and okunabilir(k0125)[0]:
        pay = float((k0125["x0"] - k25["x0"]) / I_KAYMA)
    return {"karar": karar, "delta": d, "sigma": s, "kat": kat,
            "aciklanan_pay": pay, "sebep": ""}


def y2_yargi(a25: dict, a0625: dict, y1: dict) -> dict:
    """Y2 -- `ara` kipi Delta t bagimliligini kaldiriyor mu."""
    for k in (a25, a0625):
        ok, sebep = okunabilir(k)
        if not ok:
            return {"karar": "OKUNMAZ", "sebep": sebep}
    if y1.get("karar") == "OKUNMAZ" or "delta" not in y1:
        return {"karar": "OKUNMAZ",
                "sebep": "Y1 okunmadi -- |delta_son| olmadan Y2 kurulamaz"}
    d, s, kat = _fark(a25, a0625)
    kaldiriyor = (kat < J_SIGMA
                  and abs(d) <= ARA_KALDIRMA_ORANI * abs(y1["delta"]))
    notu = ("Dt bagimliligi zaten gosterilemedi"
            if y1["karar"] == "DT YOLU GOSTERILEMEDI" else "")
    return {"karar": "ARA KALDIRIYOR" if kaldiriyor else "ARA KALDIRMIYOR",
            "delta": d, "sigma": s, "kat": kat, "not": notu, "sebep": ""}


def i2_yargi(kaba: dict, orta: dict) -> dict:
    """I2 -- Protokol I'nin AYNI kilitli tablosu, `ara` kipinde."""
    for k in (kaba, orta):
        ok, sebep = okunabilir(k)
        if not ok:
            return {"karar": "OKUNMAZ", "sebep": sebep}
    return _gr().yargi(kaba, orta)


def y0_sinyali(x, d) -> dict:
    """Y3 -- `rho(krater, log Y0)` ve permutasyon p (Protokol G esikleri)."""
    import ayirt_raporu as ar

    rho = ar.spearman(x, d)
    p = ar.permutasyon_p(x, d, n=5000)
    return {"rho": rho, "p": p,
            "anlamli": bool(abs(rho) > ar.RHO_ESIGI and p < ar.P_ESIGI)}


def kol_degerlendir(ad: str, kip: str, x, d, *, n_nokta: int,
                    akma: dict | None = None) -> dict:
    """Diziden kol ozeti: sigmoid (Protokol I), sinyal, O1-O3 alanlari."""
    x = np.asarray(x, float)
    d = np.asarray(d, float)
    o = _gr().olcek_raporu(ad, x, d)
    o["kip"] = kip
    o["n_nokta"] = int(n_nokta)
    o["tamamlanma"] = float(n_nokta / N_TASARIM)
    o["sinyal"] = y0_sinyali(x, d)
    akma = akma or {}
    o["ara_oran_max"] = float(akma.get("oran_max_max", float("nan")))
    o["akma"] = akma
    return o


# --- veri yukleme ------------------------------------------------------

def _dizinler(kok: Path, seri: str, kip: str, cetik: str) -> list[str]:
    return sorted(glob.glob(str(kok / f"{seri}_{kip}_{cetik}_sahne*.durumlar")))


def akma_ozeti(dizinler) -> dict:
    """npz'lerdeki `akma_tani` (JSON) alanlarinin kol ozeti."""
    oranlar, p99, asan, n = [], [], [], 0
    for dz in dizinler:
        for yol in sorted(Path(dz).glob("nokta_*.npz")):
            z = np.load(yol)
            n += 1
            if "akma_tani" not in z.files:
                continue
            t = json.loads(str(z["akma_tani"]))
            if not t:
                continue
            oranlar.append(float(t["oran_max"]))
            p99.append(float(t["oran_p99"]))
            asan.append(float(t["asan_kutle_kesri"]))
    if not oranlar:
        return {"n_npz": n, "n_tanili": 0}
    return {"n_npz": n, "n_tanili": len(oranlar),
            "oran_max_max": float(np.max(oranlar)),
            "oran_p99_medyan": float(np.median(p99)),
            "asan_kutle_kesri_medyan": float(np.median(asan))}


def kol_yukle(kok: Path, seri: str, kip: str, cetik: str) -> dict | None:
    import vekil_posterior as vp

    dz = _dizinler(kok, seri, kip, cetik)
    ad = f"{seri}_{kip}_{cetik}"
    if not dz:
        return None
    akma = akma_ozeti(dz)
    x, d, _ = vp._veri(dz)
    return kol_degerlendir(ad, kip, x, d, n_nokta=akma["n_npz"], akma=akma)


def tekrar_kontrolu(kok: Path) -> dict:
    """O4 -- J1_son_c0250 <-> G1: eslesen theta'larda krater bagil farki."""
    import ayirt_raporu as ar

    def _tablo(desen):
        t = {}
        for dz in sorted(glob.glob(str(kok / desen))):
            tohum = _tohum(dz)
            for k, z in ar._oku(Path(dz)):
                t[(tohum, tuple(np.round(k["theta"], 12)))] = z
        return t

    j = _tablo("J1_son_c0250_sahne*.durumlar")
    g = _tablo("G1_uretim_sahne*.durumlar")
    ortak = sorted(set(j) & set(g))
    if not ortak:
        return {"karar": "OKUNMAZ", "sebep": "eslesen nokta yok", "n": 0}
    farklar, bit_ayni = [], 0
    for a in ortak:
        dj, dg = ar._krater(j[a]), ar._krater(g[a])
        farklar.append(abs(dj - dg) / max(abs(dg), 1e-300))
        bit_ayni += int(np.array_equal(np.asarray(j[a]["x"]),
                                       np.asarray(g[a]["x"])))
    med = float(np.median(farklar))
    return {"karar": "BIT-TEKRAR" if med <= TEKRAR_ESIGI
            else "TEKRAR EDILEMEDI",
            "n": len(ortak), "bagil_fark_medyan": med,
            "bagil_fark_max": float(np.max(farklar)),
            "x_bit_ayni": int(bit_ayni)}


def _tohum(ad: str) -> str:
    import vekil_posterior as vp

    return vp._tohum_ayikla(ad)


# --- rapor -------------------------------------------------------------

def seri_raporu(kollar: dict) -> dict:
    """`kollar`: {(kip, cetik): kol_ozeti}. Y1, Y2 ve Y3."""
    g = kollar.get
    y1 = (y1_yargi(g(("son", "c0250")), g(("son", "c0625")),
                   g(("son", "c0125")))
          if g(("son", "c0250")) and g(("son", "c0625"))
          else {"karar": "OKUNMAZ", "sebep": "son kollari eksik"})
    y2 = (y2_yargi(g(("ara", "c0250")), g(("ara", "c0625")), y1)
          if g(("ara", "c0250")) and g(("ara", "c0625"))
          else {"karar": "OKUNMAZ", "sebep": "ara kollari eksik"})
    mekanizma = {}
    s25, s0625 = g(("son", "c0250")), g(("son", "c0625"))
    if s25 and s0625:
        a, b = s25["akma"], s0625["akma"]
        if a.get("oran_p99_medyan") and b.get("oran_p99_medyan"):
            mekanizma["p99_orani_0625_0250"] = (b["oran_p99_medyan"]
                                                / a["oran_p99_medyan"])
    return {"Y1": y1, "Y2": y2, "Y3_mekanizma": mekanizma}


def _yaz_kol(o: dict) -> None:
    s = o["sinyal"]
    ak = o.get("akma", {})
    print(f"{o['ad']:>16} {o['n_nokta']:>3} {o['x0']:8.3f} "
          f"{o['sigma_x0']:8.4f} {o['w']:6.3f} {o['R2']:7.4f} "
          f"{s['rho']:+7.3f} {s['p']:7.4f} "
          f"{ak.get('oran_p99_medyan', float('nan')):10.4g} "
          f"{ak.get('oran_max_max', float('nan')):10.4g} "
          f"{str(o['gecerli']):>6}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kok", type=Path, required=True)
    ap.add_argument("--seri", choices=("J1", "J2"), default=None)
    ap.add_argument("--i2", action="store_true")
    ap.add_argument("--tekrar", action="store_true")
    ap.add_argument("--json", type=Path, default=None)
    a = ap.parse_args(argv)

    cikti: dict = {}
    if a.seri:
        kollar = {}
        for kip, cetik, _ in KOLLAR:
            k = kol_yukle(a.kok, a.seri, kip, cetik)
            if k is not None:
                kollar[(kip, cetik)] = k
        print("=" * 100)
        print(f"PROTOKOL J -- seri {a.seri}")
        print("=" * 100)
        print(f"{'kol':>16} {'n':>3} {'x0':>8} {'sig_x0':>8} {'w':>6} "
              f"{'R^2':>7} {'rho':>7} {'p':>7} {'q/Y p99':>10} "
              f"{'q/Y max':>10} {'gecer':>6}")
        for kip, cetik, _ in KOLLAR:
            if (kip, cetik) in kollar:
                _yaz_kol(kollar[(kip, cetik)])
            else:
                print(f"{a.seri + '_' + kip + '_' + cetik:>16}   -- YOK")
        r = seri_raporu(kollar)
        print()
        for ad in ("Y1", "Y2"):
            y = r[ad]
            satir = f"{ad}: {y['karar']}"
            if "kat" in y:
                satir += (f"   delta = {y['delta']:+.4f}  sigma = "
                          f"{y['sigma']:.4f}  kat = {y['kat']:.2f}")
            if y.get("sebep"):
                satir += f"   ({y['sebep']})"
            if y.get("not"):
                satir += f"   NOT: {y['not']}"
            print(satir)
        if np.isfinite(r["Y1"].get("aciklanan_pay", float("nan"))):
            print(f"    I'daki kaymanin Delta t ile aciklanan payi: "
                  f"{100 * r['Y1']['aciklanan_pay']:.0f}%")
        if r["Y3_mekanizma"]:
            print(f"Y3: son kipinde p99(q/Y) orani (0,0625/0,25) = "
                  f"{r['Y3_mekanizma']['p99_orani_0625_0250']:.3f}"
                  f"  (kusur baskinsa ~0,25)")
        cikti[a.seri] = {"kollar": {f"{k[0]}_{k[1]}": v
                                    for k, v in kollar.items()},
                         "rapor": r}
    if a.i2:
        kaba = kol_yukle(a.kok, "J1", "ara", "c0250")
        orta = kol_yukle(a.kok, "I2", "ara", "c0250")
        print("=" * 72)
        print("I2 -- ara kipinde x0 cozunurluge dayanikli mi (Protokol I tablosu)")
        print("=" * 72)
        if kaba is None or orta is None:
            y = {"karar": "OKUNMAZ", "sebep": "kol eksik"}
        else:
            _yaz_kol(kaba)
            _yaz_kol(orta)
            y = i2_yargi(kaba, orta)
        print(f"\nI2 YARGI: {y['karar']}  "
              + (f"kat = {y['kat']:.2f}" if "kat" in y else y.get("sebep", "")))
        print("  (son kipindeki Protokol I: 2,44 sigma, ZAYIF)")
        print("  NOT: DAYANIKLI, YAKINSAMA kaniti degildir (uzman, Soru 18).")
        cikti["I2"] = y
    if a.tekrar:
        t = tekrar_kontrolu(a.kok)
        print(f"O4 tekrar: {t}")
        cikti["O4"] = t
    if a.json:
        a.json.write_text(json.dumps(cikti, indent=2, default=str),
                          encoding="utf-8")
        print(f"\nyazildi: {a.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
