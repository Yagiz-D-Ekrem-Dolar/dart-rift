"""A′ **mukavemetli malzemede** de duruyor mu? (FAZ 4.4 — ADR-0041 §5 boşluk 3)

## Kapatılan boşluk

ADR-0041 kilitlenirken tek bir madde açık bırakıldı ve bu **hangi seçenek
seçilirse seçilsin** açıktı:

> **§5 boşluk 3** — Sedov gerilmesiz ve tek malzemeli; mukavemet,
> gözeneklilik ve hasarla etkileşim ölçülmedi.

A′ hakkında bilinen her şey — arayüzdeki `3,2–6,5×` yapay kuvvet
(KAYIT-024), o gürültünün şok geçişine **etkisizliği** (KAYIT-026, taşma
`%0,000`) — **ideal gaz** Sedov'unda ölçüldü. Basalt farklıdır: sapma
gerilmesi taşır, gözenek çöker, hasar birikir. Arayüz gürültüsü orada da
zararsız mı?

## İki fark, ikisi de kasıtlı

[`shock_interface`][dartrift.validation.shock_interface] üç kolu **tek**
bir `h` ile koşturuyordu — çünkü o ölçüm yapıldığında `h` skalerdi ve A′
henüz yoktu. Bu modül iki şeyi değiştiriyor:

1. **Malzeme**: Tillotson basalt + mukavemet + gözeneklilik + hasar.
2. **`h` politikası**: iki bölgeli kol artık **parçacık başına `h`**
   kullanıyor — ince bölgede `h/λ`, kaba bölgede `h`. Yani ölçülen şey
   A′'nın **gerçekte kullanılacağı** biçim, onun bir vekili değil.

> İkincisi bu ölçümü FAZ 4.4'ün asıl işi yapıyor: KAYIT-026 A′'yı değil,
> A′'nın *arayüz geometrisini* ölçmüştü.

## Yargı biçimi: **parantez**, mutlak hata değil

`shock_interface`'ten devralınan mantık: iki bölgeli kol, iki tekdüze
kolun **arasına** düşmeli. Neden mutlak hata değil — çünkü ADR-0011
ölçtü ki bu kurulumda `%3,9`'luk bir model-form tabanı var ve sıfıra
gitmiyor. Parantez ölçütü o tabanı **iki taraftan da** eleyerek yalnızca
arayüzün bedelini yalıtıyor.

Üç ön koşul aynen korunuyor (biri düşerse yargı `belirsiz`):

| ön koşul | neden |
|---|---|
| iki tekdüze kol **ayırt edilebilir** olmalı | parantez sıfır genişlikteyse ölçüt boştur |
| enjekte enerji üç kolda **aynı** | değilse farklı bir problem çözülmüş olur |
| kütle uyuşmazlığı **ihmal edilebilir** | küre sınırı iki kafesle mükemmel döşenmez |
"""
from __future__ import annotations

import numpy as np

from ..cpu_reference.materials import (DamageParams, GravityParams,
                                       MaterialParams, PorosityParams,
                                       StrengthParams)
from ..cpu_reference.sph_ref import RefParams

__all__ = ["BASALT_SOLID", "build_two_zone_solid_ic", "judge",
           "run_solid_interface"]

RHO0 = 2700.0          #: basalt referans yoğunluğu (ADR-0009)
U_ARKA = 1.0e3         #: arka plan iç enerjisi (J/kg) — soğuk ama sıfır değil

#: Enjekte edilen toplam enerji (J). İlk denemede `5,0e9` yazdım ve koşu
#: **patladı** (`overflow encountered in reduce`). Nedeni ölçüldü: enjeksiyon
#: bölgesinin kütlesi ~76 kg, yani özgül enerji `6,6e7 J/kg` — Tillotson
#: basaltın buharlaşma enerjisinin (`E_cv = 1,82e7`) **üç katı**. Malzeme
#: tümüyle gaz oluyor, ses hızı fırlıyor, `dt` çöküyor.
#:
#: Doğru mertebe **hesaplandı**, tahmin edilmedi: `r = 0,3`'e kadarki kütle
#: `4/3·π·0,3³·2700 ≈ 305 kg`; `%5` sıkışma için gereken basınç
#: `K·0,05 ≈ 1,3e9 Pa`, enerji yoğunluğu `~3e7 J/m³`, hacim `0,113 m³`
#: ⇒ `~3,4e6 J`. `1,0e7` bunun üç katı — şok sürer ama yoğuşmuş kalır
#: (özgül enerji `1,3e5 J/kg`, `E_iv = 4,72e6`'nın çok altında).
E_ENJEKTE = 1.0e7
KUTU = 1.0             #: kenar uzunluğu (m)
H_OVER_DX = 2.0        #: nominal düzleştirme oranı


def _malzeme(mukavemet: bool, gozenek: bool, hasar: bool) -> MaterialParams:
    """Kolları **aynı** malzeme nesnesiyle koşturmak için tek kaynak."""
    return MaterialParams(
        eos="tillotson",
        strength=StrengthParams(enabled=mukavemet, Y0=1.0e5, mu_f=0.8,
                                YM=1.5e9, shear_G=2.27e10, jaumann=True),
        porosity=PorosityParams(enabled=gozenek),
        gravity=GravityParams(enabled=False),
        damage=DamageParams(enabled=hasar),
        density_method="continuity")


#: Ölçümün ana kolu: **üçü de açık**.
BASALT_SOLID = _malzeme(True, True, True)


def _kafes(n_side: int) -> tuple:
    dx = KUTU / n_side
    eksen = (np.arange(n_side) + 0.5) * dx - 0.5 * KUTU
    xx, yy, zz = np.meshgrid(eksen, eksen, eksen, indexing="ij")
    return np.column_stack([xx.ravel(), yy.ravel(), zz.ravel()]), dx


def build_two_zone_solid_ic(n_coarse: int, lam: int, r_inner: float,
                            h_coarse: float, per_particle_h: bool = True,
                            h_inject_over_dx: float = 3.0) -> dict:
    """İki bölgeli basalt küpü; `r < r_inner` içinde `lam` kat ince.

    `per_particle_h=True` ise ince bölge `h_coarse/lam` alır — **A′**.
    `False` ise üç kol da tek `h` kullanır — eski (skaler) davranış, ve
    A′'nın katkısını yalıtmak için gereken kontrol kolu.

    Kütle **yerel** hücre hacminden gelir (`m = ρ₀·dx³`), ADR-0030.
    """
    if lam < 1 or int(lam) != lam:
        raise ValueError(f"lam pozitif TAM sayı olmalı, {lam} geldi")
    lam = int(lam)
    if not (0.0 < r_inner < 0.5 * KUTU):
        raise ValueError(f"r_inner (0, {0.5 * KUTU}) içinde olmalı")

    x_k, dx_k = _kafes(n_coarse)
    dis = np.linalg.norm(x_k, axis=1) >= r_inner

    if lam == 1:
        x = x_k
        m = np.full(len(x), RHO0 * dx_k ** 3)
        h = np.full(len(x), h_coarse)
    else:
        x_i, dx_i = _kafes(n_coarse * lam)
        icte = np.linalg.norm(x_i, axis=1) < r_inner
        if icte.sum() == 0 or dis.sum() == 0:
            raise ValueError(
                f"bölgelerden biri boş: ince={int(icte.sum())}, "
                f"kaba={int(dis.sum())}")
        x = np.concatenate([x_i[icte], x_k[dis]])
        m = np.concatenate([np.full(int(icte.sum()), RHO0 * dx_i ** 3),
                            np.full(int(dis.sum()), RHO0 * dx_k ** 3)])
        h_ince = h_coarse / lam if per_particle_h else h_coarse
        h = np.concatenate([np.full(int(icte.sum()), h_ince),
                            np.full(int(dis.sum()), h_coarse)])

    n = len(m)
    u = np.full(n, U_ARKA)
    # Enjeksiyon cekirdegi KABA dx'e baglidir -> uc kolda AYNI fiziksel bolge.
    h_inj = h_inject_over_dx * dx_k
    q = np.linalg.norm(x, axis=1) / h_inj
    t = np.maximum(1.0 - 0.5 * q, 0.0)
    w = np.where(q < 2.0, t ** 4 * (2.0 * q + 1.0), 0.0)
    wsum = float(np.sum(m * w))
    if wsum <= 0.0:
        raise ValueError(f"enjeksiyon bölgesi boş: h_inject={h_inj}")
    u += E_ENJEKTE * w / wsum
    return {"x": x, "v": np.zeros_like(x), "m": m, "u": u, "h": h,
            "total_mass": float(np.sum(m)),
            "energy_injected": float(np.sum(m * (u - U_ARKA))),
            "n_injected": int(np.count_nonzero(w > 0.0)),
            "dx_coarse": float(dx_k), "h_coarse": float(h_coarse),
            "h_min": float(np.min(h)), "h_max": float(np.max(h)),
            "per_particle_h": bool(per_particle_h),
            "mass_ratio": float(lam ** 3), "r_inner": float(r_inner)}


def _sok_yaricapi(x: np.ndarray, rho: np.ndarray, rho0: float = RHO0,
                  esik: float = 1.05) -> float:
    """Sıkışmanın **en dış** eriştiği yarıçap.

    Eşik `1,05·ρ₀`: gürültü tabanının üstünde ama şok cephesinin
    (Tillotson'da `~2×`) çok altında — yani cephenin **yeri** ölçülür,
    genliği değil.
    """
    sikisan = rho > esik * rho0
    if not np.any(sikisan):
        raise RuntimeError(f"hiçbir parçacık {esik}·ρ₀ üstünde sıkışmamış")
    return float(np.max(np.linalg.norm(x[sikisan], axis=1)))


def _kos(ic: dict, mat: MaterialParams, device: str, t_end: float) -> dict:
    from ..warp_core.solver_solid import WarpSolid3D

    sol = WarpSolid3D(ic["x"], ic["v"], ic["m"], ic["u"], ic["h"], mat,
                      RefParams(cfl=0.2), device=device)
    tani = sol.run(t_end, max_steps=500_000)
    if tani["t_end"] < t_end * (1.0 - 1.0e-9):
        raise RuntimeError(
            f"t_end'e ULASILAMADI: {tani['t_end']:.6g} < {t_end:.6g} "
            f"({tani['n_steps']} adım). Ölçüm geçersiz.")
    st = sol.state_numpy()
    # PATLAMA SESSIZ GECMEZ. S4'te donmus ozdes degerler NaN'in imzasiydi ve
    # fark edilmesi uzun surdu. Burada uc imza da aciktan sinaniyor.
    for ad in ("rho", "P", "u", "x", "v"):
        d = st[ad]
        if not np.all(np.isfinite(d)):
            raise RuntimeError(
                f"kosu PATLADI: `{ad}` sonlu degil "
                f"({int(np.count_nonzero(~np.isfinite(d)))} / {d.size} parçacık)")
    if float(np.max(np.abs(st["x"]))) > 5.0 * KUTU:
        raise RuntimeError(
            f"kosu PATLADI: parçacıklar kutunun {float(np.max(np.abs(st['x']))) / KUTU:.1f} "
            f"katı uzağa savruldu")
    return {"N": int(len(ic["m"])), "h_min": ic["h_min"], "h_max": ic["h_max"],
            "total_mass": ic["total_mass"],
            "energy_injected": ic["energy_injected"],
            "n_injected": ic["n_injected"],
            "r_measured": _sok_yaricapi(st["x"], st["rho"]),
            "rho_max": float(np.max(st["rho"])),
            "n_steps": int(tani["n_steps"])}


def judge(a: dict, b: dict, c: dict, lam: int, r_inner: float,
          t_end: float, etiket: str = "") -> dict:
    """`shock_interface.judge` ile **aynı** mantık — kasıtlı olarak.

    Ölçüt değiştirilmiyor ki iki sonuç (ideal gaz vs mukavemetli basalt)
    **karşılaştırılabilir** olsun. Değişen tek şey fizik.
    """
    lo = min(a["r_measured"], c["r_measured"])
    hi = max(a["r_measured"], c["r_measured"])
    aralik = hi - lo
    bolen = max(abs(lo), 1e-300)
    ayirt_ediyor = bool(aralik / bolen > 2.0e-3)
    icinde = bool(lo - 0.1 * aralik <= b["r_measured"] <= hi + 0.1 * aralik)
    e = [k["energy_injected"] for k in (a, b, c)]
    enerji_ayni = bool((max(e) - min(e)) / max(e) < 1.0e-3)
    kutle = [k["total_mass"] for k in (a, b, c)]
    kutle_sapmasi = float((max(kutle) - min(kutle)) / max(kutle))
    # Sedov olceklemesi r ~ (E/rho)^(1/5) -> kutle hatasinin yaricaba
    # etkisi BESTE BIRIDIR. Tillotson tam Sedov degil ama mertebe aynidir;
    # bu bir ust sinir olarak kullaniliyor.
    yaricap_etkisi = kutle_sapmasi / 5.0
    kutle_ihmal = bool(yaricap_etkisi < 0.2 * aralik / bolen)

    if not ayirt_ediyor or not enerji_ayni or not kutle_ihmal:
        yargi = "belirsiz"
    elif icinde:
        yargi = "arayuz_zararsiz"
    else:
        yargi = "arayuz_bedelli"

    return {
        "etiket": etiket, "tekduze_kaba": a, "iki_bolgeli": b,
        "tekduze_ince": c, "lam": int(lam), "kutle_orani": float(lam ** 3),
        "r_inner": float(r_inner), "t_end": float(t_end),
        "parantez": [lo, hi], "parantez_genisligi_rel": float(aralik / bolen),
        "kollar_ayirt_edilebilir": ayirt_ediyor,
        "enerji_esit": enerji_ayni,
        "kutle_sapmasi_rel": kutle_sapmasi,
        "kutle_etkisi_rel": yaricap_etkisi,
        "kutle_ihmal_edilebilir": kutle_ihmal,
        "iki_bolgeli_parantez_icinde": icinde,
        "tasma_rel": float(max(0.0, lo - b["r_measured"],
                               b["r_measured"] - hi) / bolen),
        "yargi": yargi,
    }


def calibrate_t_end(n_coarse: int, r_inner: float, device: str,
                    r_hedef: float = 0.30, t_tahmin: float = 5.0e-5,
                    tur: int = 6) -> dict:
    """`t_end`'i **ölçerek** seç — tahmin etmeyerek.

    S4'ün dersi: bir zaman ölçeğini elle kestirmek (`c = √(P/ρ)` diye
    hesaplayıp 316 m/s bulmak, kodun 10150 kullandığını görmemek) koşuyu
    patlattı. Burada ölçek **koşunun kendisinden** okunuyor.

    Şok yarıçapı `r_hedef`'e ulaşana kadar `t` ikiye katlanır, sonra
    ikili arama ile daraltılır. Hedef `r_inner` ile kutu yarısı arasında
    olmalı: arayüzü **geçmeli** ama kenara **çarpmamalı**.
    """
    if not (r_inner < r_hedef < 0.45 * KUTU):
        raise ValueError(
            f"r_hedef ({r_hedef}) r_inner ({r_inner}) ile {0.45 * KUTU} arasında olmalı")
    h_k = H_OVER_DX * KUTU / float(n_coarse)
    ic = build_two_zone_solid_ic(n_coarse, 1, r_inner, h_k)
    izler = []

    def _r(t: float) -> float:
        s = _kos(ic, BASALT_SOLID, device, float(t))
        izler.append({"t": float(t), "r": s["r_measured"]})
        return s["r_measured"]

    t_lo, t_hi = 0.0, float(t_tahmin)
    r = _r(t_hi)
    kat = 0
    while r < r_hedef and kat < tur:
        t_lo, t_hi = t_hi, t_hi * 2.0
        r = _r(t_hi)
        kat += 1
    if r < r_hedef:
        raise RuntimeError(
            f"{tur} katlamada r_hedef'e ulaşılamadı: son r={r:.4f} @ t={t_hi:.3e}")
    for _ in range(tur):
        t_or = 0.5 * (t_lo + t_hi)
        if _r(t_or) < r_hedef:
            t_lo = t_or
        else:
            t_hi = t_or
    return {"t_end": float(t_hi), "r_hedef": float(r_hedef),
            "r_ulasilan": float(izler[-1]["r"]), "izler": izler,
            "n_kosu": len(izler)}


def run_solid_interface(n_coarse: int = 32, lam: int = 2,
                        r_inner: float = 0.15, device: str = "cuda:0",
                        t_end: float = 2.0e-4,
                        mat: MaterialParams | None = None,
                        per_particle_h: bool = True,
                        etiket: str = "basalt-tam") -> dict:
    """Üç kol: tekdüze kaba, iki bölgeli (**A′**), tekdüze ince."""
    mat = BASALT_SOLID if mat is None else mat
    h_k = H_OVER_DX * KUTU / float(n_coarse)

    a = _kos(build_two_zone_solid_ic(n_coarse, 1, r_inner, h_k), mat,
             device, t_end)
    b = _kos(build_two_zone_solid_ic(n_coarse, lam, r_inner, h_k,
                                     per_particle_h=per_particle_h),
             mat, device, t_end)
    c = _kos(build_two_zone_solid_ic(n_coarse * lam, 1, r_inner, h_k / lam),
             mat, device, t_end)
    return judge(a, b, c, lam, r_inner, t_end, etiket=etiket)
