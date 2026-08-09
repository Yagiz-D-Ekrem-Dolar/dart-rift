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

from dataclasses import dataclass, field

import numpy as np

__all__ = ["CraterShape", "crater_profile", "surface_particles"]


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

    def _yuzey_profili(pts: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """(yaricap, aci) — carpma eksenine gore, AYNI kutulama ve ayni eksen."""
        idx = surface_particles(pts, c, n_theta=n_theta, n_phi=n_phi)
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

    si = surface_particles(x_olcum, c, n_theta=n_theta, n_phi=n_phi)
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
    r_ref_global = float(np.median(rad[ref_sel]))

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
        r0_global = float(np.median(rad0[ref0_sel]))
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
    edges_c = np.linspace(1.0, cos_out, n_bins + 1)          # azalan
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
                pr[k] = float(np.median(rr[sel]))
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
    thr = depth_threshold * r_ref_global
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
            "ejekta_suzgeci": ejekta_yaricap_carpani,
            "ejekta_elenen": n_elenen,
            "reference_radius_pre_impact": r0_global,
            "global_shift_applied": float(global_shift),
        },
    )
