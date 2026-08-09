"""Momentum aktarim katsayisi beta (P3-FR-08, P3-VR-03).

TANIM. Merminin getirdigi momentum p_m; hedefin kazandigi momentum p_h.
Ejekta geri tepmesi olmasaydi p_h = p_m olurdu (beta = 1). Kacan ejekta ters
yonde momentum tasidigi icin:

    beta = 1 + |p_ejekta| / |p_mermi|          (mermi yonune izdusum)

Iki yoldan da hesaplanir:
    beta_ejekta = 1 - (p_ejekta . e) / |p_mermi|
    beta_bagli  =     (p_bagli  . e) / |p_mermi|
DIKKAT: bu ikisi BAGIMSIZ olcumler DEGILDIR. Momentum tam korunuyorsa
p_bagli + p_ejekta = p_mermi olur ve iki ifade cebirsel olarak ozdestir.
Dolayisiyla farklari yeni bir fizik dogrulamaz; farkları MOMENTUM DEFTERININ
KAPANMA HATASIDIR ve tam olarak o ad altinda raporlanir. (Bunu "bagimsiz
capraz kontrol" diye sunmak, hicbir sey sinamayan bir kontrolu sinama gibi
gostermek olurdu.)

KONTROL YUZEYI DUYARLILIGI (P3-VR-03). "Kacan" tanimi bir esige baglidir:
hangi parcacik ejektadir? Tek bir esik secip beta'yi tek sayi olarak vermek,
kesin olmayan bir seyi kesin gostermektir. Bu yuzden beta, kontrol yuzeyi
yaricapi ve hiz esigi taramasi uzerinde raporlanir ve duyarliligi ciktinin
parcasidir.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

__all__ = ["BetaResult", "escape_speed", "estimate_target_radius",
           "momentum_transfer", "beta_sensitivity", "kacis_bekleyenler",
           "balistik_beta", "bekleyen_profili"]

# Duzgun dolu bir kurede yaricapin medyan uzakliga orani. r < R kabugundaki
# kutle ~ (r/R)^3 oldugundan medyan uzaklik R/2^(1/3)'tur.
_MEDIAN_TO_RADIUS = 2.0 ** (1.0 / 3.0)


@dataclass(frozen=True)
class BetaResult:
    """beta ve onu ureten butun ara buyukluklerle birlikte."""

    beta: float
    p_impactor: float                 # |p_mermi| [kg m/s]
    p_ejecta_axial: float             # ejekta momentumunun mermi eksenindeki bileseni
    p_ejecta_vec: np.ndarray          # (3,) ejekta momentum vektoru
    ejecta_mass: float                # kacan kutle [kg]
    ejecta_fraction: float            # kacan kutle / hedef kutlesi
    n_ejecta: int
    beta_from_bound: float            # ayni beta, bagli kutlenin momentumundan
    momentum_closure: float           # |p_bagli + p_ejekta - p_mermi| / |p_mermi|
    criteria: dict = field(default_factory=dict)
    diagnostics: dict = field(default_factory=dict)


def escape_speed(mass: float, radius: float, G: float = 6.6743e-11) -> float:
    """sqrt(2 G M / R) — kacis hizi."""
    if mass <= 0.0 or radius <= 0.0:
        raise ValueError("kutle ve yaricap pozitif olmali")
    return float(np.sqrt(2.0 * G * mass / radius))


def estimate_target_radius(dist: np.ndarray) -> float:
    """Merkeze uzakliklardan hedef yaricapini kestir.

    ONCEKI HALI KUSURLUYDU: dogrudan `median(dist)` yaricap sayiliyordu.
    Duzgun dolu bir kurede medyan uzaklik R DEGIL, R/2^(1/3) = 0,794 R'dir —
    yani yaricap sistematik olarak **%21 kucuk** cikiyordu. Olculdu (300k
    parcacik, R = 100 m duzgun dolu kure):

        median(dist) = 79,294 m   (kuramsal 79,370)
        v_kacis      = %12,3 BUYUK   (v ~ 1/sqrt(R))
        r_kontrol    = 2*medyan = 1,59 R   (2,00 R saniliyordu)

    Ikisi de ejekta olcutunu SIKILASTIRIR: daha yuksek hiz esigi, daha dar
    kontrol yuzeyi. Ikisi de beta'yi kaydirir ve hicbir uyari vermezdi.
    Kusur gorunmez kalmisti cunku gercek cagiranlarin HEPSI `target_radius`
    veriyor; varsayilan yol hic kosulmuyordu.

    MEDYAN NEDEN: carpma sonrasi anlik goruntude uzaga savrulmus ejekta
    vardir. Medyan bu aykiri degerlere duyarsizdir; RMS yaricap (`sqrt(5/3
    <r^2>)`, duzgun kure icin yine tam R verir) degildir — birkac uzak
    parcacik onu buyuk gosterir. Bu yuzden medyan + kapali form duzeltme.

    VARSAYIM ACIKTIR: duzgun DOLU cisim. Ici bos bir kabuk icin yanlistir
    (kabukta medyan ~ R olur, bu tahmin R'yi %26 buyuk verir). Bilinen bir
    yaricap varsa `target_radius` ile verin — o zaman bu fonksiyon hic
    kullanilmaz.
    """
    d = np.asarray(dist, dtype=np.float64)
    if d.size == 0:
        raise ValueError("bos uzaklik dizisi")
    return float(np.median(d)) * _MEDIAN_TO_RADIUS


def momentum_transfer(
    x: np.ndarray,
    v: np.ndarray,
    m: np.ndarray,
    *,
    impactor_momentum: np.ndarray,
    center: np.ndarray | None = None,
    target_mass: float | None = None,
    target_radius: float | None = None,
    control_radius: float | None = None,
    speed_threshold: float | None = None,
    G: float = 6.6743e-11,
) -> BetaResult:
    """beta'yi kacan ejektanin momentumundan hesapla.

    Bir parcacik EJEKTA sayilir eger:
      (a) kontrol yuzeyinin disindaysa (|x - merkez| > control_radius), VE
      (b) radyal hizi kacis hizini asiyorsa (v_r > speed_threshold).

    (b) sart: kontrol yuzeyini gecmek tek basina kacmak degildir — yavas
    ejekta geri duser ve momentumu hedefe geri verir. Yalnizca (a) kullanmak
    beta'yi sistematik olarak BUYUK gosterirdi.
    """
    x = np.ascontiguousarray(x, dtype=np.float64)
    v = np.ascontiguousarray(v, dtype=np.float64)
    m = np.ascontiguousarray(m, dtype=np.float64)
    if not (len(x) == len(v) == len(m)):
        raise ValueError(f"x/v/m uzunluklari esit olmali: {len(x)}/{len(v)}/{len(m)}")
    if len(m) == 0:
        raise ValueError("bos durum")

    p_imp = np.asarray(impactor_momentum, dtype=np.float64).reshape(3)
    p_imp_mag = float(np.linalg.norm(p_imp))
    if p_imp_mag <= 0.0:
        raise ValueError("mermi momentumu sifir olamaz")
    ehat = p_imp / p_imp_mag

    m_tot = float(np.sum(m))
    if m_tot <= 0.0:
        # Kutle merkezi ve butun kesirler 0/0 olurdu; sessiz NaN yerine acik hata.
        raise ValueError(f"toplam kutle pozitif olmali, {m_tot} geldi")
    c = (np.sum(m[:, None] * x, axis=0) / m_tot) if center is None else \
        np.asarray(center, dtype=np.float64).reshape(3)

    r = x - c[None, :]
    dist = np.linalg.norm(r, axis=1)
    m_target = m_tot if target_mass is None else float(target_mass)
    r_kestirim = target_radius is None
    r_target = estimate_target_radius(dist) if r_kestirim else float(target_radius)
    r_ctrl = 2.0 * r_target if control_radius is None else float(control_radius)
    v_esc = escape_speed(m_target, r_target, G)
    v_thr = v_esc if speed_threshold is None else float(speed_threshold)

    with np.errstate(invalid="ignore", divide="ignore"):
        rhat = np.where(dist[:, None] > 0.0, r / np.maximum(dist, 1e-300)[:, None], 0.0)
    v_rad = np.einsum("ij,ij->i", v, rhat)

    is_ejecta = (dist > r_ctrl) & (v_rad > v_thr)
    p_ej = np.sum(m[is_ejecta, None] * v[is_ejecta], axis=0)
    p_ej_ax = float(np.dot(p_ej, ehat))

    # beta = 1 - (p_ejekta . e) / |p_mermi|
    # Ejekta mermiye TERS yonde firlar, yani p_ej_ax < 0 beklenir; bu beta'yi
    # 1'in USTUNE cikarir. Ters isaret fiziksel olarak anlamsizdir ve mutlak
    # deger alinarak GIZLENMEZ — `ejecta_direction_ok` tanisi olarak raporlanir.
    beta = 1.0 - p_ej_ax / p_imp_mag

    p_bound = np.sum(m[~is_ejecta, None] * v[~is_ejecta], axis=0)
    beta_b = float(np.dot(p_bound, ehat)) / p_imp_mag
    # Momentum defteri kapaniyor mu: p_bagli + p_ejekta =? p_mermi
    closure = float(np.linalg.norm(p_bound + p_ej - p_imp)) / p_imp_mag

    m_ej = float(np.sum(m[is_ejecta]))
    return BetaResult(
        beta=float(beta),
        p_impactor=p_imp_mag,
        p_ejecta_axial=p_ej_ax,
        p_ejecta_vec=p_ej,
        ejecta_mass=m_ej,
        ejecta_fraction=m_ej / m_tot,
        n_ejecta=int(np.count_nonzero(is_ejecta)),
        beta_from_bound=beta_b,
        momentum_closure=closure,
        criteria={
            "control_radius": r_ctrl,
            "speed_threshold": v_thr,
            "escape_speed": v_esc,
            "target_radius": r_target,
            "target_mass": m_target,
            "center": c,
        },
        diagnostics={
            "n_total": int(len(m)),
            "total_mass": m_tot,
            "max_distance": float(dist.max()),
            "max_radial_speed": float(v_rad.max()),
            # Yaricap VERILDI mi yoksa KESTIRILDI mi — beta'yi okuyan bilmeli.
            # Kestirim duzgun dolu cisim varsayar (estimate_target_radius).
            "target_radius_estimated": bool(r_kestirim),
            "ejecta_direction_ok": bool(p_ej_ax < 0.0),
            "p_ejecta_transverse": float(
                np.linalg.norm(p_ej - p_ej_ax * ehat)),
        },
    )


def beta_sensitivity(
    x: np.ndarray,
    v: np.ndarray,
    m: np.ndarray,
    *,
    impactor_momentum: np.ndarray,
    control_radii: np.ndarray | list[float],
    speed_factors: np.ndarray | list[float] = (0.5, 1.0, 2.0),
    **kw,
) -> dict:
    """beta'nin kontrol yuzeyi ve hiz esigine duyarliligi (P3-VR-03).

    Donen sozlukte `beta_grid` (len(r) x len(f)) ve tarama uzerindeki
    yayilim yer alir. Yayilim, beta'nin RAPORLANAN belirsizliginin alt
    siniridir: tanim secimi bile bu kadar oynatiyorsa, daha dar bir hata
    cubugu iddia edilemez.
    """
    rr = np.asarray(control_radii, dtype=np.float64).ravel()
    ff = np.asarray(speed_factors, dtype=np.float64).ravel()
    if rr.size < 2:
        raise ValueError("duyarlilik icin en az 2 kontrol yaricapi gerekir")
    if np.any(rr <= 0.0) or np.any(ff <= 0.0):
        raise ValueError("yaricap ve carpanlar pozitif olmali")
    # `control_radius`/`speed_threshold` tarama degiskenleridir; kw ile de
    # gelirlerse asagidaki cagrida ayni argüman iki kez verilir ve TypeError
    # olur. Sessiz ezmek yerine ACIK reddediliyor: tarama yapan bir fonksiyona
    # sabit bir tarama degeri vermek, cagiranin niyetinin belirsiz oldugunu
    # gosterir.
    cakisan = {"control_radius", "speed_threshold"} & set(kw)
    if cakisan:
        raise ValueError(
            f"{sorted(cakisan)} tarama degiskenidir, kw ile verilemez; "
            "control_radii / speed_factors kullanin")

    base = momentum_transfer(x, v, m, impactor_momentum=impactor_momentum, **kw)
    v_esc = base.criteria["escape_speed"]
    grid = np.empty((rr.size, ff.size), dtype=np.float64)
    frac = np.empty_like(grid)
    for i, rc in enumerate(rr):
        for j, f in enumerate(ff):
            b = momentum_transfer(
                x, v, m, impactor_momentum=impactor_momentum,
                control_radius=float(rc), speed_threshold=float(f * v_esc), **kw)
            grid[i, j] = b.beta
            frac[i, j] = b.ejecta_fraction
    # EKSEN BASINA yayilim — toplam yayilim tek basina YANILTIR. Bir eksen
    # hic is gormuyorsa (o boyutta hicbir parcacik siniflandirmasi degismiyorsa)
    # toplam yayilim yine de pozitif cikar ve "iki boyutlu duyarlilik olculdu"
    # sanilir. Olculdu: scene_checks sentetik sahnesinde ejekta hizlari
    # 0,2 m/s'den baslar, kacis hizi 0,0183 m/s'dir; 2*v_kacis = 0,037 m/s
    # bile en yavas ejektanin besde biri. Yani HIZ EKSENI TAMAMEN OLUYDU —
    # toplam yayilimin hepsi yaricap ekseninden geliyordu.
    yay_r = float(np.max(grid.max(axis=0) - grid.min(axis=0)))  # sabit f, r degisiyor
    yay_f = float(np.max(grid.max(axis=1) - grid.min(axis=1)))  # sabit r, f degisiyor
    return {
        "control_radii": rr,
        "speed_factors": ff,
        "escape_speed": v_esc,
        "beta_grid": grid,
        "ejecta_fraction_grid": frac,
        "beta_min": float(grid.min()),
        "beta_max": float(grid.max()),
        "beta_median": float(np.median(grid)),
        "beta_spread": float(grid.max() - grid.min()),
        "beta_relative_spread": float(
            (grid.max() - grid.min()) / max(abs(np.median(grid)), 1e-300)),
        "beta_spread_radius_axis": yay_r,
        "beta_spread_speed_axis": yay_f,
        "radius_axis_active": bool(yay_r > 0.0),
        "speed_axis_active": bool(yay_f > 0.0),
        "base": base,
    }


def kacis_bekleyenler(
    x: np.ndarray,
    v: np.ndarray,
    m: np.ndarray,
    *,
    hedef: np.ndarray,
    R: float,
    v_esc: float,
) -> dict:
    """Ejekta olmaya ADAY madde: iceride ama disari dogru yeterince hizli.

    ## Ne sorunun cevabi

    `n_hedef_ejekta` sabit kalinca iki ihtimal var: madde yolda, ya da
    kazi hic olmuyor. Bu fonksiyon `r < R` olup `v_r > v_kacis` giden
    parcacigi sayar.

    > ### DUZELTME — bu sayi TEK BASINA kaziyi gostermez
    >
    > Ilk yazdigimda *"beklemekle ayirt edilemez ama olcmekle edilir"*
    > dedim. **Yetersizdi.** DART kosusunun son durumunda `n_bekleyen =
    > 2671` (hedefin `%26`'si) cikti ve dagilimi olcunce:
    >
    > | carpma noktasina uzaklik | bekleyen orani |
    > |---|---|
    > | 0-20 m | **%11,7** |
    > | 40-60 m | %25,6 |
    > | 80-120 m | **%31,5** |
    >
    > Oran carpma noktasinda **en dusuk**. Kazi bunun TERSINI verirdi.
    > O parcaciklar kazi degil, **cismin cinlamasi**.
    >
    > Ayirt eden sey sayinin kendisi degil **uzaysal dagilimi**:
    > `bekleyen_profili` kullanin.

    ## `t_gecis` neyin tahmini, neyin degil

    Yercekimi kapali (`GravityParams(enabled=False)`), yani parcaciga
    baska kuvvet binmiyorsa `(R - r) / v_r` saniye sonra yuzeyi gecer.
    Ama bu madde hala CISMIN ICINDE, yani basinc altinda: hizlanabilir
    de yavaslayabilir de.

    > Bu yuzden `t_gecis` bir **kestirim degil, buyukluk mertebesi**.
    > "3 saniye" ile "3000 saniye" arasindaki farki soyler; "3,4 mu
    > 3,8 mi" sorusuna cevap vermez. Kesinmis gibi rapor edilmemeli.

    ## `v_kacis` esiginin kendi kusuru

    Yercekimi kapaliyken `v_r < v_kacis` olan bir parcacik geri
    DUSMEZ, oylece surukler. Yani esik, simule EDILMEYEN bir fizigin
    yerine gecen bir vekil. Bu ADR-0028'de kilitli bir secim; burada
    yalnizca hatirlatiliyor, yeniden tartisilmiyor.

    Donenler
    --------
    ``n_kacti``      : `r > R` ve `v_r > v_kacis` — zaten ejekta.
    ``n_bekleyen``   : `r <= R` ve `v_r > v_kacis` — yolda.
    ``n_yavas_disi`` : `r > R` ama `v_r <= v_kacis` — cikti, yavas.
    ``t_gecis_*``    : bekleyenlerin gecis suresi yuzdelikleri; bekleyen
                       yoksa **NaN** (uydurma sayi yok).
    """
    x = np.asarray(x, dtype=np.float64)
    v = np.asarray(v, dtype=np.float64)
    m = np.asarray(m, dtype=np.float64)
    hedef = np.asarray(hedef, dtype=bool)
    if not (len(x) == len(v) == len(m) == len(hedef)):
        raise ValueError("x, v, m, hedef ayni uzunlukta olmali")
    if R <= 0.0:
        raise ValueError("R pozitif olmali")

    r = np.linalg.norm(x, axis=1)
    # r = 0'da radyal yon tanimsiz; boyle bir parcacik ne cikiyor ne
    # giriyor sayilir (v_r = 0), yani hicbir kovaya dusmez.
    guvenli = np.maximum(r, 1e-300)
    vr = np.einsum("ij,ij->i", v, x / guvenli[:, None])

    hizli = vr > v_esc
    disarida = r > R
    kacti = hedef & disarida & hizli
    bekleyen = hedef & (~disarida) & hizli
    yavas_disi = hedef & disarida & (~hizli)

    hedef_kutle = float(m[hedef].sum())
    d: dict = {
        "n_kacti": int(kacti.sum()),
        "n_bekleyen": int(bekleyen.sum()),
        "n_yavas_disi": int(yavas_disi.sum()),
        "bekleyen_kutle_kesri": float(m[bekleyen].sum()
                                      / max(hedef_kutle, 1e-300)),
        # BEKLEYENIN MOMENTUMU: `balistik_beta` bunu SAYMIYOR, cunku
        # olcutu `r > R`. Olculdu (DART, t = 0,07 s): bekleyen 37,
        # sayilan 28 -- ayni mertebede. Yani `beta_bal` sistematik olarak
        # DUSUK ve ne kadar dusuk oldugu buradan okunur.
        "bekleyen_p": np.sum(m[bekleyen, None] * v[bekleyen], axis=0).tolist(),
        "v_kacis": float(v_esc),
        "R": float(R),
    }

    if not bekleyen.any():
        d.update(t_gecis_min=float("nan"), t_gecis_medyan=float("nan"),
                 t_gecis_p90=float("nan"),
                 yargi="bekleyen_yok")
        return d

    tg = (R - r[bekleyen]) / vr[bekleyen]
    d.update(
        t_gecis_min=float(np.min(tg)),
        t_gecis_medyan=float(np.median(tg)),
        t_gecis_p90=float(np.percentile(tg, 90.0)),
        yargi="bekleyen_var",
    )
    return d


def balistik_beta(
    x: np.ndarray,
    v: np.ndarray,
    m: np.ndarray,
    *,
    hedef: np.ndarray,
    R: float,
    v_esc: float,
    ehat: np.ndarray,
    p_imp: float,
) -> dict:
    """`beta`, ejektanin `2R`'ye VARMASI beklenmeden.

    `momentum_transfer`in olcutu `d > 2R` istiyor; hedef maddesinin oraya
    varmasi medyan **795 s** suruyor (rapor A12) ve o sure simule
    EDILMIYOR. Yercekimi kapali oldugu icin (`GravityParams(enabled=
    False)`) serbest bir parcacik duz gider ve bir daha yavaslamaz, yani
    "kacacak mi" sorusu SIMDI cevaplanabilir:

        ejekta :  r > R  VE  v_r > v_kacis
        beta   =  1 - (p_ejekta . e) / |p_mermi|

    > Bu bir **esik gevsetmesi degil, bekleme kaldirmasidir**: ayni
    > parcaciklar, sadece varislari beklenmeden sayiliyor. Capraz kontrol
    > gecti — balistik `1,61758`, bagimsiz kontrol kolu `1,617583`.

    `r > R` sarti **gerekli**: yoksa cismin icinde basinc dalgasiyla
    disari salinan madde de sayilir.

    ## TEK KAYNAK

    Bu olcut daha once `faz48_iki_asama.py` ve `faz410_firlatma_
    suresi.py` icinde AYRI AYRI yaziliydi. Uc kopya (ucuncusu
    `kacis_bekleyenler`) birbirinden kayabilir ve kayma sessiz olur --
    iki betik ayni sahnede farkli `beta` verirdi. Tek yere alindi.

    ## Mermi HER ZAMAN kacmis sayilir

    `~hedef` kosulsuz eklenir: mermi zaten disaridan geliyor ve gectigi
    yol sorgulanmiyor. Iki asamali sahnede `is_impactor` hicbir
    parcacikta yoktur (mermi cekirdekle kabalastirildi), yani orada bu
    terim bostur ve `n_hedef_ejekta` KACAN HER SEY demektir.
    """
    x = np.asarray(x, dtype=np.float64)
    v = np.asarray(v, dtype=np.float64)
    m = np.asarray(m, dtype=np.float64)
    hedef = np.asarray(hedef, dtype=bool)
    if p_imp <= 0.0:
        raise ValueError(f"|p_mermi| pozitif olmali, {p_imp} geldi")
    r = np.linalg.norm(x, axis=1)
    vr = np.einsum("ij,ij->i", v, x / np.maximum(r, 1e-300)[:, None])
    kacan = (~hedef) | (hedef & (r > R) & (vr > v_esc))
    p_ej = np.sum(m[kacan, None] * v[kacan], axis=0)
    h_kac = hedef & kacan
    return {
        "beta_bal": 1.0 - float(np.dot(p_ej, np.asarray(ehat))) / p_imp,
        "n_ejekta": int(kacan.sum()),
        "n_hedef_ejekta": int(h_kac.sum()),
        "hedef_ejekta_kutle": float(m[h_kac].sum()),
        "hedef_ejekta_kutle_kesri": float(m[h_kac].sum()
                                          / max(m[hedef].sum(), 1e-300)),
    }


def bekleyen_profili(
    x: np.ndarray, v: np.ndarray, m: np.ndarray, *,
    hedef: np.ndarray, R: float, v_esc: float,
    carpma_noktasi: np.ndarray,
    kenarlar=(0.0, 20.0, 40.0, 60.0, 80.0, 120.0, 200.0),
) -> dict:
    """Bekleyen maddenin **carpma noktasina gore** dagilimi.

    ## Neden sayi yetmiyor

    `kacis_bekleyenler`in `n_bekleyen`i tek basina yaniltici: yercekimi
    kapali oldugu icin (`GravityParams(enabled=False)`) cisim carpma
    sonrasi **cinlar** ve salinimin disa giden yarisi `v_r > v_kacis`
    sinavini gecer. Olculdu: DART kosusunda `2671` parcacik, hedefin
    `%26`'si.

    Kaziyi cinlamadan ayiran sey dagilimdir:

        KAZI ise     -> oran carpma yakininda YUKSEK, uzakta DUSUK
        CINLAMA ise  -> oran her kusakta benzer ya da uzakta daha yuksek

    ## `v_kacis`in kendi kusuru burada da gecerli

    Yercekimi simule EDILMIYOR, yani `v_kacis` var olmayan bir fizigin
    vekili. `0,082 m/s` gibi kucuk bir esik neredeyse her disa hareketi
    yakalar. Bu ADR-0028'de kilitli bir secim; burada yalnizca sonucu
    olculuyor.

    Donen ``kusaklar`` her kusak icin ``(alt, ust, n_toplam, n_bekleyen,
    oran)``; ``yargi`` ise ``"kazi_benzeri"`` / ``"cinlama_benzeri"`` /
    ``"belirsiz"``.
    """
    x = np.asarray(x, dtype=np.float64)
    hedef = np.asarray(hedef, dtype=bool)
    mp = np.asarray(carpma_noktasi, dtype=np.float64).reshape(3)
    r = np.linalg.norm(x, axis=1)
    vr = np.einsum("ij,ij->i", v, x / np.maximum(r, 1e-300)[:, None])
    bek = hedef & (r <= R) & (vr > v_esc)
    d_mp = np.linalg.norm(x - mp[None, :], axis=1)

    kusaklar = []
    for a, b in zip(kenarlar[:-1], kenarlar[1:]):
        msk = hedef & (d_mp >= a) & (d_mp < b)
        n_t = int(msk.sum())
        if n_t == 0:
            continue
        n_b = int((msk & bek).sum())
        kusaklar.append({"alt": float(a), "ust": float(b), "n_toplam": n_t,
                         "n_bekleyen": n_b, "oran": n_b / n_t})

    if len(kusaklar) < 2:
        return {"kusaklar": kusaklar, "yargi": "belirsiz",
                "neden": "iki kusaktan az veri"}

    yakin, uzak = kusaklar[0]["oran"], kusaklar[-1]["oran"]
    if yakin > 1.5 * max(uzak, 1e-12):
        yargi = "kazi_benzeri"
    elif uzak > 1.5 * max(yakin, 1e-12):
        yargi = "cinlama_benzeri"
    else:
        yargi = "belirsiz"
    return {"kusaklar": kusaklar, "yakin_oran": yakin, "uzak_oran": uzak,
            "yargi": yargi, "n_bekleyen": int(bek.sum())}
