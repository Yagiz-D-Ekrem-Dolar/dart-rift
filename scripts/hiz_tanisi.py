"""Kacan maddenin hiz yapisini olcer: M(>v) dagilimi.

Neden: `r > R and v_r > v_esc` olcutu **kac** parcacik kactigini
soyluyor ama **hangi hizda** kactigini soylemiyor. Jet maddesi
(~km/s, cok az kutle) ile kazi akisi (~m/s, cok kutle) bu olcutte
ayni gorunur. Housen & Holsapple olcekleme yasalari dogrudan
M(>v) uzerinde tanimli; kiyas ancak bu dagilimla yapilabilir.

Kullanim:
    python scripts/hiz_tanisi.py kampanya/L2_taban.son_durum.npz [...]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

# H&H: M(>v) ~ v^(-3mu), mu ~ 0,4 (gozenekli) - 0,55 (kaya)
MU_GOZENEKLI = 0.40
MU_KAYA = 0.55

ESIKLER = (0.0, 0.082, 0.5, 1.0, 10.0, 100.0, 1000.0, 5000.0)


def _yukle(yol: Path) -> dict:
    d = np.load(yol)
    return {k: d[k] for k in d.files}


def hiz_yapisi(s: dict, *, yalniz_hedef: bool = True) -> dict:
    """Bir son-durum anligindan hiz yapisini cikarir."""
    x, v, m = s["x"], s["v"], s["m"]
    R = float(s["R"])
    v_esc = float(s["v_esc"])

    if yalniz_hedef:
        # hedef = mermi katkisi olmayan parcacik. `hedef` bayragi
        # kurulusta yazilir; `mermi_kesri` tasima sonrasi gercegi verir.
        secim = s["mermi_kesri"] < 0.5
    else:
        secim = np.ones(len(m), dtype=bool)

    x, v, m = x[secim], v[secim], m[secim]
    r = np.linalg.norm(x, axis=1)
    rhat = x / np.maximum(r, 1e-30)[:, None]
    v_r = np.einsum("ij,ij->i", v, rhat)
    hiz = np.linalg.norm(v, axis=1)

    disarida = r > R

    # M(>v): SADECE disarida olanlar icin (kacis olcutunun hiz kismi)
    dagilim = []
    for esik in ESIKLER:
        k = disarida & (v_r > esik)
        dagilim.append(
            {
                "v_esik": esik,
                "n": int(k.sum()),
                "M": float(m[k].sum()),
                "p_r": float((m[k] * v_r[k]).sum()),
            }
        )

    # Ic bolgede de akis var mi? (disari cikmamis ama disariya hizli)
    icerde = ~disarida
    ic_dagilim = []
    for esik in ESIKLER:
        k = icerde & (v_r > esik)
        ic_dagilim.append({"v_esik": esik, "n": int(k.sum()), "M": float(m[k].sum())})

    kacan = disarida & (v_r > v_esc)
    if kacan.any():
        hk = hiz[kacan]
        kacan_hiz = {
            "min": float(hk.min()),
            "medyan": float(np.median(hk)),
            "max": float(hk.max()),
            "kutle_agirlikli_ort": float((m[kacan] * hk).sum() / m[kacan].sum()),
        }
        # parcacik kutlesi -> inceltme seviyesi
        birim, sayim = np.unique(np.round(m[kacan], 6), return_counts=True)
        kacan_seviye = [
            {"m_p": float(b), "n": int(c)} for b, c in zip(birim, sayim)
        ]
    else:
        kacan_hiz, kacan_seviye = None, []

    # yaricap profili: her kabukta disa dogru en hizli %5
    kenar = np.linspace(0.0, R * 1.2, 13)
    profil = []
    for i in range(len(kenar) - 1):
        k = (r >= kenar[i]) & (r < kenar[i + 1])
        if k.sum() < 5:
            continue
        profil.append(
            {
                "r0": float(kenar[i]),
                "r1": float(kenar[i + 1]),
                "n": int(k.sum()),
                "v_r_medyan": float(np.median(v_r[k])),
                "v_r_p95": float(np.percentile(v_r[k], 95)),
                "v_r_max": float(v_r[k].max()),
            }
        )

    return {
        "t": float(s["t"]),
        "R": R,
        "v_esc": v_esc,
        "N_hedef": int(len(m)),
        "M_hedef": float(m.sum()),
        "m_p_min": float(m.min()),
        "m_p_max": float(m.max()),
        "dis_dagilim": dagilim,
        "ic_dagilim": ic_dagilim,
        "kacan_hiz": kacan_hiz,
        "kacan_seviye": kacan_seviye,
        "profil": profil,
    }


def egim(dagilim: list, v_alt: float, v_ust: float) -> float | None:
    """M(>v) ~ v^(-3mu) ustel yasasinin olculen egimi."""
    pts = [
        (d["v_esik"], d["M"])
        for d in dagilim
        if v_alt <= d["v_esik"] <= v_ust and d["v_esik"] > 0 and d["M"] > 0
    ]
    if len(pts) < 2:
        return None
    lv = np.log10([p[0] for p in pts])
    lm = np.log10([p[1] for p in pts])
    return float(np.polyfit(lv, lm, 1)[0])


RHO0_KATI = 2700.0


#: Kumelenme esigi: en yakin komsu / nominal aralik. Bu oranin
#: altindaki parcaciklar birbirine GECMIS demektir ve `rho`
#: fazlalari GERCEK SIKISMA DEGIL.
#:
#: `0,75` secildi cunku olculen kusurda oran `0,575` idi ve
#: `(1/0,575)^3 = 5,26` kat sahte yogunluk uretiyordu; `0,75`
#: bile `2,37` kat demek. Duzgun bir SPH paketlemesinde en yakin
#: komsu nominal araligin `~%95`'idir.
KUMELENME_ESIGI = 0.75


def _kumelenme(s: dict, secim) -> dict:
    """Seçili parçacıklar birbirine **geçmiş** mi (çekme kararsızlığı).

    A61: `E3_av_dusuk`'te `ρ_max = 2891,5` ve `8` parçacık "katı
    sıkışmış" göründü. Konumlarına bakınca en yakın komşu medyanı
    `0,2013 m`, nominal aralık `0,35 m` — **oran `0,575`**. Eşdeğer
    yoğunluk artışı `5,26` kat, ölçülen fazlayı tamamen açıklıyordu.

    Yani `ρ > ρ₀ᵏᵃᵗⁱ` tek başına *"şok var"* demeye **yetmiyor**.
    """
    n = int(np.count_nonzero(secim))
    if n < 2 or "x" not in s or "m" not in s:
        return {"kumelenme_olculdu": False}
    x = np.asarray(s["x"], dtype=np.float64)
    m = np.asarray(s["m"], dtype=np.float64)
    hedef = np.asarray(s["mermi_kesri"], dtype=np.float64) < 0.5
    xs = x[hedef][secim]
    ms = m[hedef][secim]
    if len(xs) > 4000:                       # O(n^2) korumasi
        return {"kumelenme_olculdu": False, "kumelenme_sebep": "cok parcacik"}
    D = np.linalg.norm(xs[:, None, :] - xs[None, :, :], axis=2)
    np.fill_diagonal(D, np.inf)
    en_yakin = float(np.median(D.min(axis=1)))
    # Nominal aralik parcacik kutlesinden: s = (m / rho_yigin)^(1/3)
    a0 = np.asarray(s["alpha0"], dtype=np.float64)[hedef][secim]
    rho_yigin = RHO0_KATI / np.maximum(a0, 1.0)
    aralik = float(np.median((ms / rho_yigin) ** (1.0 / 3.0)))
    oran = en_yakin / aralik if aralik > 0 else float("nan")
    return {
        "kumelenme_olculdu": True,
        "en_yakin_komsu": en_yakin,
        "nominal_aralik": aralik,
        "komsu_orani": oran,
        "sahte_yogunluk_kati": float(oran ** -3) if oran > 0 else float("nan"),
        "kumelenmis": bool(oran < KUMELENME_ESIGI),
    }


def ezilme_mi_sok_mu(s: dict) -> dict:
    """`sikisma` canli sok mu, yoksa KALICI EZILME ARTIGI mi?

    `sikisma = 100 (rho a0 / rho0_kati - 1)`. Bu buyukluk iki AYRI
    seyle yukselir:

      1. **gozenek kapanmasi** (P-alpha crush-up, GERI DONUSSUZ).
         Tavani `rho -> rho0_kati`, yani `100 (a0 - 1)`.
         Matris `a0 = 1,7564` icin **`%75,6`**.
      2. **kati maddenin sikismasi** -- ancak `rho > rho0_kati`
         olursa. Gercek soku YALNIZ bu gosterir.

    Hugoniot bandi `%45,6 - 74,3`; matrisin gozenek tavani `%75,6`.
    **Band tamamen tavanin altinda.** Yani sok kapisi, ortamda hic
    canli sok olmasa da, salt ezilme artigiyla gecilebilir.

    Bu ayrimi yapan tek olcu `rho / rho0_kati`.
    """
    rho = np.asarray(s["rho"], dtype=np.float64)
    a0 = np.asarray(s["alpha0"], dtype=np.float64)
    m = np.asarray(s["m"], dtype=np.float64)
    hedef = np.asarray(s["mermi_kesri"], dtype=np.float64) < 0.5

    rho, a0, m = rho[hedef], a0[hedef], m[hedef]
    sik = 100.0 * (rho * a0 / RHO0_KATI - 1.0)
    tavan = 100.0 * (a0 - 1.0)          # salt gozenek kapanmasi tavani
    # Kati sikismasi icin PAY sart. `alpha0 = 1` kolunda baslangic
    # yogunlugu ZATEN rho0_kati; sayisal artik (`2700,1`) `> 2700`
    # sinavini gecer ve "sok var" der. Olculen: gozeneksiz kolda
    # `16 762` parcacik boyle yanlis sayildi. `%0,1` payi bunu keser.
    KATI_PAYI = 1.001
    kati = rho > RHO0_KATI * KATI_PAYI   # gercek kati sikismasi

    i = int(np.argmax(sik))
    return {
        "sikisma_max": float(sik[i]),
        "en_sikisan": {
            "rho": float(rho[i]),
            "alpha0": float(a0[i]),
            "rho_bolu_rho0_kati": float(rho[i] / RHO0_KATI),
            "gozenek_tavani": float(tavan[i]),
            "tavanin_altinda": bool(sik[i] < tavan[i]),
        },
        "rho_max": float(rho.max()),
        "rho_max_bolu_kati": float(rho.max() / RHO0_KATI),
        "kati_payi": KATI_PAYI,
        **_kumelenme(s, kati),
        "n_kati_sikisan": int(kati.sum()),
        "M_kati_sikisan": float(m[kati].sum()),
        "kati_sikisan_pay": float(kati.sum() / len(rho)),
        # ezilme durumu: alpha = rho0_kati / rho (kati sikismasiz)
        "n_tam_ezilmis": int((rho >= RHO0_KATI * 0.999).sum()),
        "n_kismen_ezilmis": int(((rho > RHO0_KATI / a0 * 1.001) & (rho < RHO0_KATI * 0.999)).sum()),
        "n_bakir": int((rho <= RHO0_KATI / a0 * 1.001).sum()),
    }


def _kumelenme_satiri(e: dict) -> str:
    """Kümelenme denetimi — A61 sonrası ZORUNLU."""
    if not e.get("kumelenme_olculdu"):
        return "  kumelenme: OLCULMEDI (kati sikisan < 2 ya da cok fazla)"
    bayrak = ("KUMELENMIS -- rho fazlasi SAHTE olabilir"
              if e["kumelenmis"] else "duzgun paketli")
    return (f"  kumelenme: en yakin komsu {e['en_yakin_komsu']:.4f} m / "
            f"aralik {e['nominal_aralik']:.4f} m = {e['komsu_orani']:.3f}"
            f"   (esik {KUMELENME_ESIGI})" + chr(10) +
            f"     sahte yogunluk katkisi {e['sahte_yogunluk_kati']:.2f} kat"
            f"  >> {bayrak}")

def ezilme_raporu(ad: str, e: dict) -> str:
    s = e["en_sikisan"]
    yargi = (
        "SALT EZILME ARTIGI olabilir -- canli sok KANITI YOK"
        if e["n_kati_sikisan"] == 0
        else f"gercek kati sikismasi VAR ({e['n_kati_sikisan']} parcacik)"
    )
    tavan_yon = "ALTINDA" if s["tavanin_altinda"] else "USTUNDE"
    satirlar = [
        f"\n--- {ad}: ezilme mi sok mu ---",
        f"  sikisma_max = {e['sikisma_max']:.3f}%",
        f"  en sikisan parcacik: rho={s['rho']:.1f}  a0={s['alpha0']:.4f}",
        f"     rho/rho0_kati = {s['rho_bolu_rho0_kati']:.4f}   (>1 ise kati sikismis)",
        f"     salt gozenek kapanmasi tavani = {s['gozenek_tavani']:.2f}%"
        f"   -> olculen tavanin {tavan_yon}",
        f"  rho_max = {e['rho_max']:.1f}  ({e['rho_max_bolu_kati']:.4f} x rho0_kati)",
        f"  kati sikisan (rho > 2700): {e['n_kati_sikisan']} parcacik, "
        f"{e['M_kati_sikisan']:.4g} kg  ({100 * e['kati_sikisan_pay']:.3f}%)",
        f"  ezilme durumu: bakir={e['n_bakir']}  kismen={e['n_kismen_ezilmis']}  "
        f"tam={e['n_tam_ezilmis']}",
        _kumelenme_satiri(e),
        f"  >> {yargi}",
    ]
    return "\n".join(satirlar)


def rapor(ad: str, h: dict) -> str:
    L = [f"\n{'=' * 66}", f"{ad}   t={h['t']:.4g} s   R={h['R']:.4g} m   v_esc={h['v_esc']:.4g} m/s"]
    L.append(
        f"hedef N={h['N_hedef']}  M={h['M_hedef']:.4g} kg  "
        f"m_p: {h['m_p_min']:.4g} .. {h['m_p_max']:.4g} kg"
    )
    L.append("\n  M(>v)  DISARIDA (r > R)          |  ICERDE (r <= R)")
    L.append("  v_esik      n         M kg   p_r      |      n         M kg")
    for d, i in zip(h["dis_dagilim"], h["ic_dagilim"]):
        L.append(
            f"  {d['v_esik']:8.3f} {d['n']:7d} {d['M']:12.4g} {d['p_r']:9.3g}  "
            f"|  {i['n']:7d} {i['M']:12.4g}"
        )
    e = egim(h["dis_dagilim"], 0.08, 1000.0)
    if e is not None:
        L.append(f"\n  olculen egim d log M / d log v = {e:+.3f}")
        L.append(
            f"  H&H beklentisi -3mu = {-3 * MU_GOZENEKLI:+.2f} (gozenekli) "
            f".. {-3 * MU_KAYA:+.2f} (kaya)"
        )
    if h["kacan_hiz"]:
        k = h["kacan_hiz"]
        L.append(
            f"\n  kacan hiz: min={k['min']:.4g}  medyan={k['medyan']:.4g}  "
            f"max={k['max']:.4g}  <v>_m={k['kutle_agirlikli_ort']:.4g} m/s"
        )
        L.append(
            "  kacan seviye: "
            + ", ".join(f"{s['n']}x{s['m_p']:.4g}kg" for s in h["kacan_seviye"])
        )
    else:
        L.append("\n  kacan yok")
    L.append("\n  yaricap profili (v_r m/s)")
    L.append("  r0 .. r1            n    medyan       p95       max")
    for p in h["profil"]:
        L.append(
            f"  {p['r0']:7.2f}..{p['r1']:7.2f} {p['n']:7d} "
            f"{p['v_r_medyan']:9.3g} {p['v_r_p95']:9.3g} {p['v_r_max']:9.3g}"
        )
    return "\n".join(L)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("anliklar", nargs="+", type=Path)
    ap.add_argument("--json", type=Path, default=None)
    ap.add_argument("--tum-parcaciklar", action="store_true")
    a = ap.parse_args(argv)

    cikti = {}
    for yol in a.anliklar:
        if not yol.exists():
            print(f"YOK: {yol}", file=sys.stderr)
            continue
        s = _yukle(yol)
        h = hiz_yapisi(s, yalniz_hedef=not a.tum_parcaciklar)
        if "rho" in s and "alpha0" in s:
            h["ezilme"] = ezilme_mi_sok_mu(s)
        cikti[yol.stem] = h
        print(rapor(yol.stem, h))
        if "ezilme" in h:
            print(ezilme_raporu(yol.stem, h["ezilme"]))

    if a.json:
        a.json.write_text(json.dumps(cikti, indent=2), encoding="utf-8")
        print(f"\nyazildi: {a.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
