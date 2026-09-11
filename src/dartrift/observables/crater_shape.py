"""Krater sekli (P3-FR-08) — YEREL krateri KURESEL bicim degisiminden ayirir.

SORUN. Dimorphos gibi kucuk, zayif bir cisimde DART carpmasi yalnizca bir
cukur acmaz; cismin TUMUNU bir miktar deforme eder. Krater derinligini
"baslangic yaricapi - son yaricap" diye olcmek bu iki etkiyi karistirir ve
krateri sistematik olarak BUYUK gosterir; asiri uc durumda (global buzusme)
carpma olmayan yerlerde bile "krater" olcerdi.

AYRIM. Referans, cismin CARPMA ONCESI kendi sekli olmalidir:

  1. Carpma eksenine gore aci theta hesaplanir.
  2. Carpma ONCESI konumlardan (`x_reference`) AYNI kutulamayla R_0(theta)
     olculur; buna carpmadan uzak yuzeyde olculen kuresel olcek kaymasi
     eklenir.
  3. Krater derinligi, yerel yaricapin bu referanstan sapmasidir.

Boylece global buzusme referansa girer ve kraterden DUSER. Iki buyukluk ayri
ayri raporlanir: `depth` (yerel krater) ve `global_radius_change` (kuresel).

DUZELTILEN KUSUR — KURESELLIK VARSAYIMI. Onceki surum, yukaridaki 2. adimi
yapiyor gibi yazilmisti ama gercekte referansi TEK BIR SAYI (carpma disi
medyan yaricap) olarak aliyordu; yani cismi KURE kabul ediyordu. Dimorphos
kure degil: 88 x 87 x 65 m, eksenler arasi %26 fark. Olculdu — KRATERSIZ bir
Dimorphos elipsoidinde:

    carpma kisa (z) eksende : derinlik 9,04 m, cap 66,76 m   <-- tamamen hayali
    carpma uzun (x) eksende : derinlik 1,46 m, cap 0,00 m

Yani cismin kendi sekli krater diye olculuyordu. Cismin yaricapi zaten
kendiliginden ~11,5 m oynuyor; 9 m'lik bir "krater" bunun icinden geliyordu.
Bu, DART'in gercek krater olcusuyla ayni mertebede bir hata.

`x_reference` verilmezse eski (kuresel) davranis surer — kure senaryolarinda
dogrudur — ama `reference_is_spherical` tanisi ACIKCA True doner. Duzensiz
cisimde bu tani goz ardi edilemez.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

__all__ = ["CraterShape", "KraterYerdegistirme", "KraterYuzey",
           "crater_profile", "krater_yerdegistirme", "krater_yuzey",
           "krater_yuzey_durumdan", "surface_particles"]


@dataclass(frozen=True)
class CraterShape:
    """Krater olculeri; yerel ve kuresel bilesenler AYRI."""

    depth: float                    # yerel krater derinligi [m]
    diameter: float                 # kenar-kenar cap [m]
    depth_over_diameter: float
    volume: float                   # kazilan hacim [m^3]
    global_radius_change: float     # kuresel bicim degisimi [m] (kraterden ayri)
    rim_angle_deg: float            # kenarin carpma ekseninden acisi
    n_surface: int
    n_reference: int
    profile_angle_deg: np.ndarray   # theta orgusu
    profile_radius: np.ndarray      # olculen R(theta)
    profile_reference: np.ndarray   # referans R_ref(theta)
    diagnostics: dict = field(default_factory=dict)


PER_BUCKET = 12  # yon kutusu basina hedeflenen parcacik sayisi


def surface_particles(
    x: np.ndarray,
    center: np.ndarray,
    n_theta: int | None = None,
    n_phi: int | None = None,
) -> np.ndarray:
    """Yuzey parcaciklarinin indeksleri: her yon kutusunda EN UZAK olan.

    IKI TASARIM NOKTASI, ikisi de olcumle zorunlu oldu:

    1. KUTU SAYISI N'E GORE SECILIR. Sabit 60x120 kutu (=7200) kullanildiginda
       N=8000 parcacikta kutu basina ~1 parcacik dusuyordu; "kutudaki en uzak"
       o zaman rastgele bir parcaciktir ve olculen "yuzey" yaricapi 0.75R'ye
       iniyordu. Bu, kuresel buzusme testinde 41 m'lik hayali bir krater
       uretti. Kutu sayisi N/PER_BUCKET'a gore secilince yuzey gercekten
       yuzey olur.

    2. KUTULAR ESIT KATI ACILI. theta'da esit acili kutulama kutuplari asiri
       orneklerdi (sin(theta) agirligi); bunun yerine cos(theta) uzerinde
       esit araliklarla kutulanir.
    """
    x = np.ascontiguousarray(x, dtype=np.float64)
    c = np.asarray(center, dtype=np.float64).reshape(3)
    r = x - c[None, :]
    d = np.linalg.norm(r, axis=1)
    ok = d > 0.0
    if not np.any(ok):
        raise ValueError("tum parcaciklar merkezde")

    n = int(np.count_nonzero(ok))
    if n_theta is None:
        n_theta = max(4, int(np.sqrt(n / (2.0 * PER_BUCKET))))
    if n_phi is None:
        n_phi = max(4, 2 * n_theta)
    if n_theta < 2 or n_phi < 2:
        raise ValueError("n_theta ve n_phi >= 2 olmali")

    cth = np.clip(r[:, 2] / np.maximum(d, 1e-300), -1.0, 1.0)
    ph = np.arctan2(r[:, 1], r[:, 0]) + np.pi
    it = np.clip(((cth + 1.0) * 0.5 * n_theta).astype(np.int64), 0, n_theta - 1)
    ip = np.clip((ph / (2.0 * np.pi) * n_phi).astype(np.int64), 0, n_phi - 1)
    key = it * n_phi + ip
    # her kutuda maksimum d'yi veren indeks: siralayip son elemani al
    order = np.lexsort((d, key))
    k_sorted = key[order]
    last = np.ones(len(order), dtype=bool)
    last[:-1] = k_sorted[:-1] != k_sorted[1:]
    idx = order[last]
    return idx[ok[idx]]


def crater_profile(
    x: np.ndarray,
    *,
    center: np.ndarray,
    impact_direction: np.ndarray,
    reference_radius: float,
    outer_angle_deg: float = 60.0,
    n_bins: int = 20,
    depth_threshold: float = 0.05,
    min_per_bin: int = 5,
    n_theta: int | None = None,
    n_phi: int | None = None,
    x_reference: np.ndarray | None = None,
    ejekta_yaricap_carpani: float | None = None,
    kutulama: str = "kuresel",
    yuzdelik: float = 95.0,
    esik_kipi: str = "yaricap",
) -> CraterShape:
    """Yerel krateri, kuresel bicim degisiminden ayirarak olc.

    `x_reference` CARPMA ONCESI parcacik konumlaridir. Verilirse referans
    profil R_0(theta) ayni kutulamayla ondan olculur ve cismin kendi sekli
    kraterden duser. VERILMEZSE cisim KURE varsayilir (`reference_is_spherical`
    tanisi True doner) — duzensiz cisimde bu, sekli krater diye olcer: kratersiz
    bir Dimorphos elipsoidinde 9,04 m derinlik / 66,76 m cap olculdu.

    `reference_radius` carpma ONCESI ortalama yaricaptir; yalnizca kuresel
    degisimi raporlamak icin kullanilir, krater derinligine GIRMEZ.
    `outer_angle_deg` referans yuzeyin baslangic acisidir: bu acinin otesi
    "carpmadan etkilenmemis" sayilir.
    `depth_threshold` krater kenarini belirler: referanstan sapma, referans
    yaricapin bu kesrini astigi yer krater icidir.

    `ejekta_yaricap_carpani` OLCULEN yuzeyden ucustaki ejektayi eler:
    `r > carpan * reference_radius` olan parcaciklar yuzey ADAYI sayilmaz.
    Gerekli, cunku `surface_particles` kutudaki EN UZAK parcacigi alir ve
    yarıcap ust siniri YOKTUR; kraterin ustunde ucan madde hala ayni acisal
    kutudadir, yani taban yerine ejekta "yuzey" olur ve krater GORUNMEZ.
    Olculdu (DART asama-2 sahnesi, gercek 2/5/10 m krater): suzgecsiz
    2,46/4,93/7,48 yerine SABIT 1,1975 — yani derinlikten BAGIMSIZ.

    > Suzgec YALNIZCA olculen yuzeye uygulanir, `x_reference`e DEGIL.
    > Ikisine birden uygulanirsa hayatta kalan parcaciklar zaten taban
    > altinda oldugu icin referans = olcum olur ve sonuc ozdes sifirdir
    > (olculdu).

    ## `kutulama = "eksen"` — DOLU cisimde tek calisan kip

    Varsayilan `"kuresel"` kip once `surface_particles` ile yuzeyi
    cikarir. O cikarici KURESEL `cos(theta)` izgarasi kullanir ve krater
    kutupta oldugu icin koniye pay ayiramaz. Olculdu (DART, `N = 10 410`):

    | `n_theta` | "yuzey" / toplam | medyan `r` | koni (`<7 deg`) |
    |---|---|---|---|
    | 16 | 0,05 | **81,26** (gercek `81,94`) | **8** |
    | 1024 | **0,96** | 66,91 | 9 970 |

    Kucuk `n_theta`: koniye `5-14` parcacik duser, profil cikarilamaz.
    Buyuk `n_theta`: izgara parcacik sayisini gecer, her parcacik kendi
    kutusunun "en disi" olur ve **yuzey = butun cisim**. Ikisi arasinda
    calisan bir deger YOK (rapor A16).

    `"eksen"` kipi kuresel izgarayi **hic kullanmaz**: parcaciklari
    dogrudan **carpma ekseninden aciya** gore esit acili halkalara
    boler ve her halkanin yuzeyini `yuzdelik` ile kestirir. Olculdu
    (ayni sahne, `lam = 2`, hicbir cozunurluk artisi olmadan):

    | gercek | `"kuresel"` | **`"eksen"`** |
    |---|---|---|
    | 2 m | RED | **1,977** |
    | 5 m | RED | **4,793** |
    | 10 m | RED | **9,486** |

    `yuzdelik = 95` bilinen sentetik kraterle **kalibre edildi**:
    `p90` yukari (`5,3-6,2`), `p99` asagi (`3,8-4,0`) yanli. Kalan
    yanlilik `-%4`. Bu bir kalibrasyondur, turetme degil.

    Gurultu tabani olculdu: yuzey gurultusu `1 m` iken **`1,03 m`**;
    `0,2 m` iken `0,25 m`.

    ## `esik_kipi` — capin OLCULEBILMESI icin

    Kenar esigi varsayilan olarak **cismin yaricapinin** kesri:
    `thr = depth_threshold * R`. `depth_threshold = 0,05` ve `R = 82 m`
    icin bu **`4,10 m`** demek — DART kraterinin kendi derinligi
    kadar. Sonuc: kenar hep 0.-1. kutuda kalir ve cap ya `0` cikar ya da
    iki ayrik degere nicemlenir (olculdu: 82 ornekte `6,93` ve `12,00`).

    `esik_kipi = "derinlik"` esigi **kraterin kendi derinligine**
    baglar (`thr = depth_threshold * depth`), yani olcek-bagimsiz yapar.
    Paraboloid bir kraterde `dev` tepe derinligin `%10`'una
    `theta = 0,949 * theta_c`'de duser, yani olculen cap gercegin
    `~%95`'i olur — sabit ve **duzeltilebilir** bir yanlilik.

    > Varsayilan DEGISMEDI: `"yaricap"`. Eski cagrilarin sonucu aynen
    > korunuyor.
    """
    x = np.ascontiguousarray(x, dtype=np.float64)
    c = np.asarray(center, dtype=np.float64).reshape(3)
    d_imp = np.asarray(impact_direction, dtype=np.float64).reshape(3)
    dn = float(np.linalg.norm(d_imp))
    if dn == 0.0:
        raise ValueError("carpma yonu sifir uzunlukta")
    axis = -d_imp / dn                       # krater ekseni: DISA dogru
    if reference_radius <= 0.0:
        raise ValueError(f"referans yaricap pozitif olmali, {reference_radius} geldi")
    if not (0.0 < outer_angle_deg < 180.0):
        raise ValueError(f"outer_angle_deg (0,180) olmali, {outer_angle_deg} geldi")
    if n_bins < 4:
        raise ValueError("n_bins >= 4 olmali")
    if min_per_bin < 1:
        # min_per_bin=0 olsaydi bos kutuda np.median([]) sessizce NaN dondurur,
        # o NaN dev'e gecer ve gecerli kutu gibi sayilirdi. Sessiz NaN, yanlis
        # sayidan daha kotudur: nereden geldigi gorunmez.
        raise ValueError(f"min_per_bin >= 1 olmali, {min_per_bin} geldi")

    if kutulama not in ("kuresel", "eksen"):
        raise ValueError(f"kutulama 'kuresel' ya da 'eksen' olmali, "
                         f"{kutulama!r} geldi")
    if not (50.0 < yuzdelik <= 100.0):
        raise ValueError(f"yuzdelik (50,100] olmali, {yuzdelik} geldi")
    _eksen_kipi = kutulama == "eksen"

    def _ozet(a: np.ndarray) -> float:
        """Kuresel kipte medyan, eksen kipinde yuzey kestirimi (yuzdelik)."""
        return float(np.percentile(a, yuzdelik) if _eksen_kipi
                     else np.median(a))

    def _yuzey_profili(pts: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """(yaricap, aci) — carpma eksenine gore, AYNI kutulama ve ayni eksen."""
        # Eksen kipinde yuzey cikarimi YAPILMAZ: kuresel izgara koniyi
        # goremiyor (A16). Yuzey her halkada `yuzdelik` ile kestirilir.
        idx = (np.arange(len(pts)) if _eksen_kipi
               else surface_particles(pts, c, n_theta=n_theta, n_phi=n_phi))
        rr = pts[idx] - c[None, :]
        dd = np.linalg.norm(rr, axis=1)
        ca = np.clip((rr @ axis) / np.maximum(dd, 1e-300), -1.0, 1.0)
        return dd, np.degrees(np.arccos(ca))

    x_olcum = x
    n_elenen = 0
    if ejekta_yaricap_carpani is not None:
        if ejekta_yaricap_carpani <= 0.0:
            raise ValueError("ejekta_yaricap_carpani pozitif olmali, "
                             f"{ejekta_yaricap_carpani} geldi")
        tut = np.linalg.norm(x - c[None, :], axis=1) <= \
            ejekta_yaricap_carpani * reference_radius
        n_elenen = int(np.count_nonzero(~tut))
        if not np.any(tut):
            raise ValueError(
                f"ejekta suzgeci ({ejekta_yaricap_carpani} x R) TUM "
                f"parcaciklari eledi; olcecek yuzey kalmadi")
        x_olcum = x[tut]

    si = (np.arange(len(x_olcum)) if _eksen_kipi
          else surface_particles(x_olcum, c, n_theta=n_theta, n_phi=n_phi))
    rs = x_olcum[si] - c[None, :]
    rad = np.linalg.norm(rs, axis=1)
    cosang = np.clip((rs @ axis) / np.maximum(rad, 1e-300), -1.0, 1.0)
    ang = np.degrees(np.arccos(cosang))

    # --- referans: carpmadan uzak yuzey; kuresel bicim degisimini tasir ---
    ref_sel = ang > outer_angle_deg
    n_ref = int(np.count_nonzero(ref_sel))
    if n_ref < 8:
        raise ValueError(
            f"referans yuzeyde yeterli parcacik yok ({n_ref}); "
            "outer_angle_deg dusurun ya da cozunurlugu artirin")
    r_ref_global = _ozet(rad[ref_sel])

    rad0 = ang0 = None
    if x_reference is not None:
        x0 = np.ascontiguousarray(x_reference, dtype=np.float64)
        if x0.ndim != 2 or x0.shape[1] != 3:
            raise ValueError(f"x_reference (N,3) olmali, {x0.shape} geldi")
        rad0, ang0 = _yuzey_profili(x0)
        ref0_sel = ang0 > outer_angle_deg
        if int(np.count_nonzero(ref0_sel)) < 8:
            raise ValueError(
                "carpma oncesi referans yuzeyde yeterli parcacik yok; "
                "outer_angle_deg dusurun ya da cozunurlugu artirin")
        # Kuresel olcek kaymasi: carpma DISI bolgede son/onceki medyan farki.
        # Bu fark referansa EKLENIR, boylece butun cismin buzusmesi/genlemesi
        # kraterden duser — modulun tum amaci bu.
        r0_global = _ozet(rad0[ref0_sel])
        global_shift = r_ref_global - r0_global
    else:
        r0_global = float("nan")
        global_shift = 0.0

    # --- profil: kutular ESIT KATI ACILI ---
    # Esit ACILI kutulama eksene yakin kutulari yok denecek kadar az
    # parcacikla birakir (0-1.5 derece kutusu kurenin ~1.7e-4'u); o kutularin
    # medyan yaricapi asagi yanli cikar ve max(sapma) tam o gurultuyu secer.
    # Olculdu: esit acili kutularla, 20 m'lik bilinen bir cukur 40 m
    # raporlaniyordu. cos(theta)'da esit araliklar her kutuya ayni kati aciyi
    # verir. (Ayni hata sinifi: ADR-0017, orneklem gurultusunu olcmek.)
    cos_out = np.cos(np.radians(outer_angle_deg))
    # Eksen kipinde ESIT ACILI halkalar: butun parcaciklar kullanildigi
    # icin ic halkalarda da yeterli ornek var (olculdu: 20/47/81/...).
    edges_c = (np.cos(np.radians(np.linspace(0.0, outer_angle_deg, n_bins + 1)))
               if _eksen_kipi
               else np.linspace(1.0, cos_out, n_bins + 1))   # azalan
    prof_a = np.degrees(np.arccos(np.clip(0.5 * (edges_c[:-1] + edges_c[1:]), -1.0, 1.0)))

    def _kutula(rr: np.ndarray, aa: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        ca = np.cos(np.radians(aa))
        ib = np.clip(np.digitize(-ca, -edges_c) - 1, 0, n_bins - 1)
        icap = ca >= cos_out
        pr = np.full(n_bins, np.nan)
        cnt = np.zeros(n_bins, dtype=np.int64)
        for k in range(n_bins):
            sel = (ib == k) & icap
            cnt[k] = int(np.count_nonzero(sel))
            if cnt[k] >= min_per_bin:
                pr[k] = _ozet(rr[sel])
        return pr, cnt

    prof_r, counts = _kutula(rad, ang)
    if rad0 is not None:
        # Referans profil = cismin KENDI carpma oncesi sekli + kuresel kayma.
        prof_ref = _kutula(rad0, ang0)[0] + global_shift
        # Referansta bos kutu varsa oradan derinlik OKUNAMAZ (NaN yayilir ve
        # `valid` maskesiyle duser). Sessizce kuresel referansa donmek, tam da
        # duzeltilen kusuru geri getirirdi.
    else:
        prof_ref = np.full(n_bins, r_ref_global)

    dev = prof_ref - prof_r                  # pozitif = ice cokme
    valid = np.isfinite(dev)
    if not np.any(valid):
        raise ValueError(
            f"profil bos — hicbir kutuda {min_per_bin} parcacik yok "
            f"(n_bins={n_bins} dusurun ya da cozunurlugu artirin)")

    # CARPMA EKSENI KUTUSU (0) GECERSIZSE KRATER OLCULEMEZ.
    #
    # Olculdu (2026-08-09): bilinen bir krater (D = 40 m, derinlik 8 m,
    # 89 parcacik) yerlestirildi ve `depth = 0.0000` raporlandi. Sebep
    # zincirleme:
    #   surface_particles 6897 -> 512 parcacik biraktı (PER_BUCKET = 12)
    #   0. kutuya (aci 9.07 deg) yalnizca 4 parcacik dustu
    #   min_per_bin = 5 -> kutu NaN -> `valid` disi
    #   kalan kutular kraterin DISINDA, hepsi prof_r = 82.000
    #   => dev her yerde 0 => depth = 0
    #
    # Yani krater OLUSMADIGI icin degil, CIKARICI GOREMEDIGI icin sifir
    # cikiyordu -- ve sessizce, makul gorunen bir sayiyla. Krater tam
    # olarak 0. kutunun icinde oldugundan o kutu gecersizse olcum
    # ANLAMSIZDIR; `nan` dondurmek `0` dondurmekten dogrudur.
    if not bool(valid[0]):
        raise ValueError(
            f"carpma ekseni kutusunda {int(counts[0])} parcacik var "
            f"(en az {min_per_bin} gerekir). Krater TAM ORADA oldugu icin "
            f"olcum ANLAMSIZ olurdu; `0` dondurmek yaniltici olur. "
            f"Yuzey parcacigi {int(len(rad))}, n_bins={n_bins}. "
            f"Cozunurlugu artirin ya da n_bins'i dusurun.")

    depth = float(np.nanmax(dev))
    # Kenar: eksenden disa dogru giderken sapmanin esigin altina dustugu ILK
    # aci — yani BITISIK krater bolgesinin sonu.
    #
    # Onceki kod `np.max(np.nonzero(inside))` ile EN DIS esik-ustu kutuyu
    # aliyordu; kendi yorumu ise "esigin altina dustugu ilk aci" diyordu.
    # Kure uzerinde ikisi ayni sonucu verir (esik-ustu kume bitisiktir) ve
    # olculdu: %3 yuzey puruzluluguyle bile ayrismadilar. Ama duzensiz cisimde
    # ya da uzakta ikinci bir cukur varsa, en-dis kural kraterin capini o
    # gurultuye kadar SISIRIR. Bitisiklik sarti bunu imkansiz kilar.
    if esik_kipi not in ("yaricap", "derinlik"):
        raise ValueError(f"esik_kipi 'yaricap' ya da 'derinlik' olmali, "
                         f"{esik_kipi!r} geldi")
    # "yaricap": esik CISMIN yaricapina bagli -> kucuk kraterde capi
    # olculemez yapar. "derinlik": kraterin KENDI derinligine bagli,
    # olcek-bagimsiz.
    thr = (depth_threshold * depth if esik_kipi == "derinlik"
           else depth_threshold * r_ref_global)
    inside = valid & (dev > thr)
    if np.any(inside) and inside[0]:
        bitisik = int(np.argmax(~inside)) if not np.all(inside) else n_bins
        rim_ang = float(prof_a[bitisik - 1])
        # cap: kenar acisinin gerdigi yay uzerindeki kiris
        diameter = 2.0 * r_ref_global * np.sin(np.radians(rim_ang))
    else:
        rim_ang = 0.0
        diameter = 0.0

    # hacim: donel katinin dilim toplami (dev >= 0 olan bolge)
    # Kutular esit kati acili oldugu icin her kusagin alani ayni:
    # A = 2 pi R^2 (cos a0 - cos a1) = 2 pi R^2 (edges_c[k] - edges_c[k+1])
    vol = 0.0
    for k in range(n_bins):
        if not (valid[k] and dev[k] > 0.0):
            continue
        area = 2.0 * np.pi * r_ref_global**2 * (edges_c[k] - edges_c[k + 1])
        vol += area * dev[k]

    return CraterShape(
        depth=depth,
        diameter=float(diameter),
        depth_over_diameter=float(depth / diameter) if diameter > 0.0 else float("nan"),
        volume=float(vol),
        global_radius_change=float(r_ref_global - reference_radius),
        rim_angle_deg=rim_ang,
        n_surface=int(len(si)),
        n_reference=n_ref,
        profile_angle_deg=prof_a,
        profile_radius=prof_r,
        profile_reference=prof_ref,
        diagnostics={
            "reference_radius_input": float(reference_radius),
            "reference_radius_measured": r_ref_global,
            "outer_angle_deg": float(outer_angle_deg),
            "depth_threshold": float(depth_threshold),
            "esik_kipi": esik_kipi,
            "kenar_esigi_m": float(thr),
            "depth_over_reference_radius": float(depth / r_ref_global),
            "empty_bins": int(np.count_nonzero(~valid)),
            "min_per_bin": int(min_per_bin),
            "bin_counts_min": int(counts.min()),
            "bin_counts_median": float(np.median(counts)),
            "axis": axis,
            # KURESELLIK VARSAYIMI ACIKCA BILDIRILIR. True ise cisim kure
            # kabul edilmistir; duzensiz cisimde olculen "krater" sekilden
            # gelebilir (kratersiz Dimorphos elipsoidinde 9,04 m olculdu).
            "reference_is_spherical": bool(x_reference is None),
            "kutulama": kutulama,
            "yuzdelik": float(yuzdelik) if _eksen_kipi else None,
            "ejekta_suzgeci": ejekta_yaricap_carpani,
            "ejekta_elenen": n_elenen,
            "reference_radius_pre_impact": r0_global,
            "global_shift_applied": float(global_shift),
        },
    )


# ---------------------------------------------------------------------------
# YERDEGISTIRME TABANLI KRATER  (A19'un caresi)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class KraterYerdegistirme:
    """Lagrange'ci krater olcusu -- ayni parcaciklarin YER DEGISTIRMESI."""

    derinlik: float           # [m] en buyuk ICERI yer degistirme
    cap: float                # [m] kenarin gordugu daire capi
    derinlik_cap: float
    kenar_aci_deg: float
    n_yuzey: int
    n_kutu: int
    profil: np.ndarray        # (n_kutu,) kutu basina ortalama radyal yer deg.
    aci_deg: np.ndarray       # (n_kutu,) kutu merkezleri
    tani: dict = field(default_factory=dict)


def krater_yerdegistirme(
    x: np.ndarray,
    x_reference: np.ndarray,
    *,
    impact_direction: np.ndarray,
    reference_radius: float,
    center: np.ndarray | None = None,
    kabuk_kalinligi: float | None = None,
    n_kutu: int = 24,
    dis_aci_deg: float = 60.0,
    en_az_parcacik: int = 5,
) -> KraterYerdegistirme:
    """Krateri **yer degistirmeden** olc -- `x` ve `x_reference` AYNI parcaciklar.

    ## Neden yeni bir olcu (A19)

    `crater_profile` mutlak yaricap dagilimina bakiyor ve bu iki yonde
    de bozuluyor (olculdu, 2026-08-21):

    | sinav | olmasi gereken | `crater_profile` |
    |---|---|---|
    | puruzlu yuzey, CARPMA YOK | `0` | `0,26 m` |
    | ensemble yolu, CARPMA YOK | `0` | `10,85 m` |
    | gercek `12 m` cukur | `~12 m` | `-0,03 m` |

    Kok neden: moloz yiginin yuzeyi **puruzlu** ve puruz, mutlak
    yaricap olcusunde kraterden ayirt edilemiyor. Raporlanan derinligin
    `%67,7`'si o tabandi.

    ## Bu olcunun degismezi

    `x is x_reference` (hicbir sey kimildamamis) ise **her kutuda** yer
    degistirme tam `0`'dir; yuzey ne kadar puruzlu olursa olsun.
    Puruz her iki tarafta da ayni oldugu icin **cikar gider**. Bu bir
    yaklasim degil, cebirsel bir ozdeslik.

    ## Tanim

    1. **Yuzey kabugu** REFERANS konfigurasyondan secilir:
       `r0 > R - kabuk_kalinligi`.
    2. Parcaciklar REFERANS kutup acisina gore kutulanir (`theta0`,
       carpma ekseninden). Kutulama referanstan yapilir ki kutu uyeligi
       carpmadan **etkilenmesin**.
    3. Her kutuda ortalama radyal yer degistirme `<r - r0>`.
    4. `derinlik` = en buyuk ICERI hareket (`-min(profil)`).
    5. `kenar` = profilin sifira dondugu ilk aci; `cap = 2 R sin(kenar)`.

    Ejekta (kacip giden madde) **disarida birakilir**: yalnizca hala
    `r < 1,05 R` olan parcaciklar sayilir, yoksa firlayan bir parcacik
    kutunun ortalamasini disari cekerdi.
    """
    x = np.asarray(x, dtype=np.float64)
    x0 = np.asarray(x_reference, dtype=np.float64)
    if x.shape != x0.shape:
        raise ValueError(f"x {x.shape} ile x_reference {x0.shape} ayni olmali")
    if x.ndim != 2 or x.shape[1] != 3:
        raise ValueError(f"x (N,3) olmali, {x.shape} geldi")
    R = float(reference_radius)
    if R <= 0.0:
        raise ValueError(f"reference_radius pozitif olmali, {R} geldi")
    if n_kutu < 2:
        raise ValueError(f"n_kutu >= 2 olmali, {n_kutu} geldi")

    c = np.zeros(3) if center is None else np.asarray(center, dtype=np.float64)
    e = np.asarray(impact_direction, dtype=np.float64)
    n = float(np.linalg.norm(e))
    if n == 0.0:
        raise ValueError("impact_direction sifir vektor olamaz")
    e = e / n
    # Mermi `e` YONUNDE gidiyor; carpma noktasi cismin `-e` tarafinda.
    eksen = -e

    d = x - c[None, :]
    d0 = x0 - c[None, :]
    r = np.linalg.norm(d, axis=1)
    r0 = np.linalg.norm(d0, axis=1)

    kal = 2.0 * R / max(n_kutu, 1) if kabuk_kalinligi is None else float(
        kabuk_kalinligi)
    kabuk = r0 > (R - kal)
    # Kacip gitmis maddeyi disla: kutu ortalamasini bozar.
    kabuk &= r < 1.05 * R
    if not np.any(kabuk):
        raise ValueError(
            f"yuzey kabugunda parcacik yok (R={R}, kalinlik={kal}) -- "
            f"kabuk_kalinligi verin")

    with np.errstate(invalid="ignore", divide="ignore"):
        cos0 = np.clip((d0 @ eksen) / np.maximum(r0, 1e-300), -1.0, 1.0)
    th0 = np.degrees(np.arccos(cos0))

    kenarlar = np.linspace(0.0, float(dis_aci_deg), n_kutu + 1)
    profil = np.full(n_kutu, np.nan)
    sayi = np.zeros(n_kutu, dtype=int)
    dr = r - r0
    for i in range(n_kutu):
        s = kabuk & (th0 >= kenarlar[i]) & (th0 < kenarlar[i + 1])
        sayi[i] = int(s.sum())
        if sayi[i] >= en_az_parcacik:
            profil[i] = float(np.mean(dr[s]))
    if not np.any(np.isfinite(profil)):
        raise ValueError(
            f"hicbir kutuda >= {en_az_parcacik} parcacik yok "
            f"(yuzey {int(kabuk.sum())}, n_kutu={n_kutu})")

    merkez = 0.5 * (kenarlar[:-1] + kenarlar[1:])
    sonlu = np.isfinite(profil)
    derinlik = float(-np.nanmin(profil))
    if derinlik <= 0.0:
        derinlik = 0.0

    # Kenar: eksenden disari giderken profilin ilk kez sifira donmesi.
    # KRATER YOKSA CAP DA YOKTUR: derinlik sifirken bir "kenar"
    # aramak, ilk kutuyu kenar sayip uydurma bir cap uretirdi.
    kenar_aci = float("nan")
    cap = float("nan")
    if derinlik > 0.0:
        esik = -0.05 * abs(np.nanmin(profil))
        for i in range(n_kutu):
            if not sonlu[i]:
                continue
            if profil[i] >= esik:
                kenar_aci = merkez[i]
                break
        if kenar_aci == kenar_aci:
            cap = 2.0 * R * math.sin(math.radians(kenar_aci))

    return KraterYerdegistirme(
        derinlik=derinlik, cap=cap,
        derinlik_cap=(derinlik / cap if cap and cap == cap and cap > 0
                      else float("nan")),
        kenar_aci_deg=kenar_aci, n_yuzey=int(kabuk.sum()),
        n_kutu=int(sonlu.sum()), profil=profil, aci_deg=merkez,
        tani={"kabuk_kalinligi_m": kal, "kutu_sayilari": sayi.tolist(),
              "dis_aci_deg": float(dis_aci_deg),
              "en_derin_kutu_deg": (float(merkez[np.nanargmin(profil)])
                                    if derinlik > 0 else float("nan"))})


# ---------------------------------------------------------------------------
# FIZIKSEL YUZEY OPERATORU  (uzman yaniti 2026-09-11, rapor A73)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class KraterYuzey:
    """Bagli cismin YUZEYINDEN olculen krater -- sabit fiziksel olcekte.

    Butun uzunluklar metre. `profil[k]`, carpma ekseninden `s[k]` yanal
    uzaklikta yuzeyin DUSUSU (pozitif = yuzey alcaldi), azimut ortalamasi.
    """

    derinlik: float            # en buyuk halka-ortalama dusus
    derinlik_merkez: float     # eksen uzerinde (s = 0) dusus
    yaricap: float             # profilin derinligin %10'una indigi ilk s
    hacim: float               # kazilan hacim (dusus > 0 olan halkalar)
    rijit_kayma: np.ndarray    # (3,) bagli kutle merkezinin yer degistirmesi
    hacim_degisimi: float      # bagli cismin toplam m/rho degisimi (sikisma < 0)
    kuresel_dusus: float       # carpmadan uzak kabugun ortalama radyal dususu
    n_ayrilan: int             # yuzeyden ayrilmis sayilan (ejekta) parcacik
    s: np.ndarray              # (K,) yanal uzaklik
    profil: np.ndarray         # (K,)
    profil_std: np.ndarray     # (K,) azimutlar arasi sapma
    tani: dict = field(default_factory=dict)


def _dik_taban(a: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    t = np.array([1.0, 0.0, 0.0]) if abs(a[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
    e1 = t - (t @ a) * a
    e1 /= np.linalg.norm(e1)
    return e1, np.cross(a, e1)


def _doluluk_kesisimi(x, V, h, *, taban, a, z_ust, z_alt, adim, esik,
                      n_bolme: int = 48) -> float:
    """Tek dogru uzerinde `phi = sum V_j W(|p - x_j|, h_j)`'nin esigi
    DISTAN ICE ilk kez astigi yukseklik (`taban`'dan `a` boyunca).

    Kesisim yoksa ya da pencerenin tepesi zaten doluysa `nan` -- sessiz
    bir sayi yerine.
    """
    from ..cpu_reference.sph_ref import kernel_w

    d = x - taban[None, :]
    z = d @ a
    yan = d - z[:, None] * a[None, :]
    yan2 = np.einsum("ij,ij->i", yan, yan)
    dest = 2.0 * h
    sec = (yan2 < dest * dest) & (z > z_alt - dest) & (z < z_ust + dest)
    if not np.any(sec):
        return float("nan")
    zs, y2, Vs, hs = z[sec], yan2[sec], V[sec], h[sec]

    def phi(zq: np.ndarray) -> np.ndarray:
        dz = zq[:, None] - zs[None, :]
        q = np.sqrt(dz * dz + y2[None, :]) / hs[None, :]
        return kernel_w(q, hs[None, :], 3) @ Vs

    n = int(np.ceil((z_ust - z_alt) / adim)) + 1
    zq = z_ust - adim * np.arange(n)
    f = phi(zq)
    dolu = np.nonzero(f >= esik)[0]
    if len(dolu) == 0 or dolu[0] == 0:
        return float("nan")
    ust, alt = float(zq[dolu[0] - 1]), float(zq[dolu[0]])
    for _ in range(n_bolme):
        orta = 0.5 * (ust + alt)
        if phi(np.array([orta]))[0] >= esik:
            alt = orta
        else:
            ust = orta
    return 0.5 * (ust + alt)


def krater_yuzey(
    x: np.ndarray,
    x_reference: np.ndarray,
    *,
    m: np.ndarray,
    h,
    rho: np.ndarray,
    rho_reference: np.ndarray,
    impact_direction: np.ndarray,
    v: np.ndarray | None = None,
    merkez: np.ndarray | None = None,
    reference_radius: float | None = None,
    s_max: float = 6.0,
    ds: float = 0.2,
    n_azimut: int = 8,
    esik: float = 0.5,
    ayrilma_hizi: float | None = None,
    adim: float | None = None,
    arama_derinligi: float = 10.0,
    dis_aci_deg: float = 60.0,
    kabuk_kalinligi: float | None = None,
    rijit_duzeltme: bool = False,
) -> KraterYuzey:
    """Krateri bagli cismin **yuzeyinden**, sabit fiziksel olcekte olc.

    ## Neden (uzman yaniti 2026-09-11, rapor A73)

    `crater_profile(kutulama="eksen")` acisal halkalardaki BUTUN hacim
    parcaciklarinin SAYI agirlikli `p95`'ini kullaniyor; bu bir yuzey
    degil. Uzman olctu: dis `1 m` kabuk SABITKEN yalniz ic noktalar
    tasininca `0,49 m` "derinlik"; ayni koordinatlar 8 kat
    cogaltilinca `0,34 -> 0,71 m`; `0,5 m` ayak izli `1 m`'lik cukurda
    `0,0012 m`.

    ## Tanim

    1. **Doluluk** `phi(p) = sum_j (m_j/rho_j) W(|p - x_j|, h_j)` --
       SPH birim bolunmesi; cismin icinde `~1`, disinda `0`. Yuzey
       `phi = esik` (varsayilan `0,5`) es-yuzeyi. Hacim `m/rho` ile
       agirlanir: bir parcacigi 8 kopyaya `m/8` ile bolmek `phi`'yi
       DEGISTIRMEZ.
    2. **Isinlar** carpma eksenine PARALEL, eksenden sabit FIZIKSEL
       yanal uzakliklarda (`s = 0, ds, 2 ds, ... s_max`), her halkada
       `n_azimut` isin. Aci degil metre: olcek cozunurlukten bagimsiz.
    3. Yuzey yuksekligi her isinda disaridan iceri ilk `phi >= esik`
       gecisi (bolmeyle inceltilir). **Ayni operator** referansa
       (`x_reference`, `rho_reference`) ve son duruma uygulanir;
       `profil = z_ref - z_son`.
    4. **Ayrilan ejekta** (`v` verilirse): bir parcacik, baslangic
       yaricapinin DISINA cikmis VE disa dogru `ayrilma_hizi`'ndan
       (varsayilan kacis hizi) hizli gidiyorsa yuzeyden sayilmaz.
       Iceri giden krater tabani korunur.
    5. **Rijit kayma** (bagli kutle merkezinin yer degistirmesi),
       **kuresel dusus** (carpmadan `dis_aci_deg` uzaktaki kabuk) ve
       **hacim degisimi** (sikisma) AYRI raporlanir, derinlige
       karistirilmaz.

    ## `rijit_duzeltme` neden varsayilan KAPALI

    Ilk surum kutle merkezi kaymasini ONCE cikariyordu. Olculdu (levha,
    dis `1,4 m` kabuk SABIT, ic `-0,5 m`): **`-0,375 m`** "derinlik".
    Ic kutlenin yer degistirmesi kutle merkezini kaydiriyor ve operator
    bunu rijit hareket sanip SABIT yuzeyi yukari tasiyordu -- tam da
    ayrilmasi gereken iki seyi karistiriyordu. DART'ta `24 ms`'de rijit
    kayma `~1e-4 m` (momentum aktarimi `~mm/s`), krater `~0,3-0,6 m`;
    cikarmamak ihmal edilebilir hata, yanlis cikarmak `0,4 m`. Kayma
    her durumda `rijit_kayma` olarak RAPORLANIR.

    ## Degismezler (sinanir: `tests/test_krater_yuzey.py`)

    - `x is x_reference` -> profil tam sifir.
    - Butun cismin rijit otelemesi -> sifir.
    - Destek kalinligindan (`2 h`) kalin dis kabuk sabitken ic hareket
      -> sifir.
    - Yeniden ornekleme (kopya + `m/k`) -> ayni sonuc.
    """
    x = np.ascontiguousarray(x, dtype=np.float64)
    x0 = np.ascontiguousarray(x_reference, dtype=np.float64)
    if x.shape != x0.shape or x.ndim != 2 or x.shape[1] != 3:
        raise ValueError(f"x {x.shape} ve x_reference {x0.shape} (N,3) olmali")
    n = len(x)
    m = np.asarray(m, dtype=np.float64).reshape(n)
    h = np.broadcast_to(np.asarray(h, dtype=np.float64), (n,)).copy()
    rho = np.asarray(rho, dtype=np.float64).reshape(n)
    rho0 = np.asarray(rho_reference, dtype=np.float64).reshape(n)
    if np.any(h <= 0) or np.any(rho <= 0) or np.any(rho0 <= 0) or np.any(m <= 0):
        raise ValueError("m, h, rho, rho_reference pozitif olmali")
    if ds <= 0 or s_max < 0 or n_azimut < 1:
        raise ValueError("ds > 0, s_max >= 0, n_azimut >= 1 olmali")
    e = np.asarray(impact_direction, dtype=np.float64).reshape(3)
    en = float(np.linalg.norm(e))
    if en == 0.0:
        raise ValueError("impact_direction sifir vektor olamaz")
    a = -e / en                                  # disa dogru krater ekseni
    c0 = (m @ x0) / m.sum() if merkez is None else np.asarray(
        merkez, dtype=np.float64).reshape(3)

    # --- ayrilan ejekta + rijit kayma (iki gecis: kayma kucuk ama tutarli)
    r0 = np.linalg.norm(x0 - c0[None, :], axis=1)
    R_ref = float(reference_radius) if reference_radius is not None else float(r0.max())
    ayrilan = np.zeros(n, dtype=bool)
    v_ayr = float("nan")
    if v is not None:
        v = np.asarray(v, dtype=np.float64).reshape(n, 3)
        if ayrilma_hizi is None:
            from .momentum_transfer import escape_speed

            v_ayr = float(escape_speed(float(m.sum()), R_ref))
        else:
            v_ayr = float(ayrilma_hizi)
    kayma = np.zeros(3)
    kayma_olc = np.zeros(3)
    for _ in range(2 if rijit_duzeltme else 1):
        xk = x - kayma[None, :]
        if v is not None:
            dr = xk - c0[None, :]
            r = np.linalg.norm(dr, axis=1)
            vr = np.einsum("ij,ij->i", v, dr) / np.maximum(r, 1e-300)
            ayrilan = (vr > v_ayr) & (r > r0)
        b = ~ayrilan
        if not np.any(b):
            raise ValueError("butun parcaciklar ayrilmis sayildi -- olcecek cisim yok")
        mb = m[b]
        kayma_olc = (mb @ x[b] - mb @ x0[b]) / mb.sum()
        if rijit_duzeltme:
            kayma = kayma_olc
    xk = x - kayma[None, :]
    bagli = ~ayrilan

    # --- isin penceresi: eksen cevresindeki en yuksek nokta (iki durum)
    e1, e2 = _dik_taban(a)
    ust_z = []
    h_eksen = float("nan")
    for ad, xx, sec in (("ref", x0, np.ones(n, bool)), ("son", xk, bagli)):
        d = xx[sec] - c0[None, :]
        z = d @ a
        yan = np.linalg.norm(d - z[:, None] * a[None, :], axis=1)
        yakin = yan < s_max + 2.0 * h[sec]
        if not np.any(yakin):
            raise ValueError("carpma ekseni cevresinde parcacik yok")
        ust_z.append(float(np.max(z[yakin] + 2.0 * h[sec][yakin])))
        if ad == "ref":
            h_eksen = float(np.min(h[sec][yakin]))
    adim = 0.25 * h_eksen if adim is None else float(adim)
    z_ust = max(ust_z) + adim
    z_alt = z_ust - float(arama_derinligi)

    V0, V = m / rho0, m / rho
    K = int(np.floor(s_max / ds + 1e-9)) + 1
    s = ds * np.arange(K)
    fi = 2.0 * np.pi * np.arange(n_azimut) / n_azimut
    z_ref = np.full((K, n_azimut), np.nan)
    z_son = np.full((K, n_azimut), np.nan)
    ortak = dict(a=a, z_ust=z_ust, z_alt=z_alt, adim=adim, esik=esik)
    xb, Vb, hb = xk[bagli], V[bagli], h[bagli]
    for k in range(K):
        for j in range(n_azimut if k > 0 else 1):
            taban = c0 + s[k] * (np.cos(fi[j]) * e1 + np.sin(fi[j]) * e2)
            z_ref[k, j] = _doluluk_kesisimi(x0, V0, h, taban=taban, **ortak)
            z_son[k, j] = _doluluk_kesisimi(xb, Vb, hb, taban=taban, **ortak)
        if k == 0:
            z_ref[0, :], z_son[0, :] = z_ref[0, 0], z_son[0, 0]
    dusus = z_ref - z_son
    if np.any(np.isfinite(dusus)):
        with np.errstate(invalid="ignore"), _sessiz_nan():
            profil = np.nanmean(dusus, axis=1)
            profil_std = np.nanstd(dusus, axis=1)
    else:
        profil = np.full(K, np.nan)
        profil_std = np.full(K, np.nan)
    if not np.isfinite(profil[0]):
        raise ValueError(
            "eksen isininda yuzey bulunamadi (pencere: "
            f"{z_alt:.3f}..{z_ust:.3f} m) -- arama_derinligi'ni artirin")
    derinlik = float(np.nanmax(profil))
    yaricap = float("nan")
    if derinlik > 0.0:
        k_max = int(np.nanargmax(profil))
        for k in range(k_max, K):
            if np.isfinite(profil[k]) and profil[k] < 0.1 * derinlik:
                yaricap = float(s[k])
                break
    alan = 2.0 * np.pi * s * ds
    alan[0] = np.pi * (0.5 * ds) ** 2
    hacim = float(np.nansum(alan * np.maximum(profil, 0.0)))

    kuresel = float("nan")
    if reference_radius is not None:
        kal = 2.0 * float(np.max(h)) if kabuk_kalinligi is None else float(
            kabuk_kalinligi)
        d0 = x0 - c0[None, :]
        cos0 = (d0 @ a) / np.maximum(r0, 1e-300)
        kab = bagli & (r0 > R_ref - kal) & (cos0 < np.cos(np.radians(dis_aci_deg)))
        if np.any(kab):
            r_son = np.linalg.norm(xk[kab] - c0[None, :], axis=1)
            kuresel = float(-np.mean(r_son - r0[kab]))

    return KraterYuzey(
        derinlik=derinlik, derinlik_merkez=float(profil[0]), yaricap=yaricap,
        hacim=hacim, rijit_kayma=kayma_olc,
        hacim_degisimi=float(V[bagli].sum() - V0[bagli].sum()),
        kuresel_dusus=kuresel, n_ayrilan=int(ayrilan.sum()),
        s=s, profil=profil, profil_std=profil_std,
        tani={"z_ust": z_ust, "z_alt": z_alt, "adim": adim, "esik": esik,
              "h_eksen": h_eksen, "ayrilma_hizi": v_ayr,
              "rijit_duzeltme": bool(rijit_duzeltme),
              "n_bos_isin_ref": int(np.isnan(z_ref).sum()),
              "n_bos_isin_son": int(np.isnan(z_son).sum()),
              "merkez": c0, "eksen": a})


class _sessiz_nan:
    """`nanmean` bos satir uyarisini sustur -- bos satir `nan` kalir."""

    def __enter__(self):
        import warnings

        self._w = warnings.catch_warnings()
        self._w.__enter__()
        warnings.simplefilter("ignore", RuntimeWarning)

    def __exit__(self, *a):
        return self._w.__exit__(*a)


#: Hedef kati yogunlugu (Tillotson bazalt) -- `rho_ref = RHO0 / alpha0`.
_RHO0_KATI = 2700.0


def krater_yuzey_durumdan(d, **kw) -> KraterYuzey:
    """`ileri_kosu_merdiven` durum dosyasindan (`npz`) yuzey krateri.

    Hedef = `mermi_kesri < 0,5`. Referans yogunluk `2700 / alpha0`
    (gerilmesiz baslangic, ADR-0022). `h` alani ZORUNLU (A50'den once
    kaydedilmiyordu; o dosyalardan bu olcu cikarilamaz).
    """
    alan = set(getattr(d, "files", None) or d.keys())
    for k in ("x", "x_referans", "m", "rho", "alpha0", "h", "ehat", "R",
              "mermi_kesri"):
        if k not in alan:
            raise KeyError(f"durum dosyasinda '{k}' yok -- yuzey olculemez")
    hedef = np.asarray(d["mermi_kesri"]) < 0.5
    v = np.asarray(d["v"])[hedef] if "v" in alan else None
    return krater_yuzey(
        np.asarray(d["x"])[hedef], np.asarray(d["x_referans"])[hedef],
        m=np.asarray(d["m"])[hedef], h=np.asarray(d["h"])[hedef],
        rho=np.asarray(d["rho"])[hedef],
        rho_reference=_RHO0_KATI / np.asarray(d["alpha0"])[hedef],
        impact_direction=np.asarray(d["ehat"], dtype=np.float64),
        v=v, merkez=np.zeros(3), reference_radius=float(d["R"]), **kw)
