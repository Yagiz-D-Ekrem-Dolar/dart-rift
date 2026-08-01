"""Ejekta katalogu (P3-FR-08).

Ejekta konisinin nicel tarifi: kutle-hiz dagilimi, firlatma acilari ve kacan
kutle. Bunlar hem beta'nin (momentum_transfer) girdisi hem de Hera/LICIACube
gozlemleriyle karsilastirilacak bagimsiz cikti.

KUTLE-HIZ DAGILIMI. Carpma kraterlesmesinde standart olcek bagintisi

    M(>v) = k m_m (v / v_*)^(-mu_e)

yani belli bir hizdan HIZLI firlayan kumulatif kutle, hizin kuvvetiyle duser.
Burada uslu yasanin US'U (mu_e) olculur ve raporlanir; literaturde bazalt/kaya
icin ~1.5-3 araligindadir. Us, kumulatif dagilima log-log dogru uydurularak
bulunur — HISTOGRAM'a degil: histogram kutu genisligi secimine baglidir,
kumulatif dagilim degildir.

Bu modul MODEL UYDURMAZ, olcer. Uydurulan tek sey uslu yasanin egimidir ve
uyum kalitesi (R^2) her zaman dondurulur; kotu uyumu iyi gibi gostermemek
icin cagiran taraf onu gormek zorundadir.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

__all__ = ["EjectaCatalog", "catalog_ejecta", "cumulative_mass_velocity"]


@dataclass(frozen=True)
class EjectaCatalog:
    """Ejekta parcaciklarinin nicel tarifi."""

    n_ejecta: int
    mass: float                        # toplam ejekta kutlesi [kg]
    mass_fraction: float               # / hedef kutlesi
    escaping_mass: float               # kacis hizini asan kutle [kg]
    escaping_fraction: float
    speed_min: float
    speed_max: float
    speed_mass_weighted_mean: float
    cone_angle_deg: float              # kutle agirlikli ortalama firlatma acisi
    cone_angle_spread_deg: float       # agirlikli standart sapma
    power_law_exponent: float          # mu_e  (M(>v) ~ v^-mu_e)
    power_law_r2: float                # uyum kalitesi — DAIMA raporlanir
    speed_bins: np.ndarray             # kumulatif dagilim: hiz eksenleri
    cumulative_mass: np.ndarray        # M(>v)
    diagnostics: dict = field(default_factory=dict)


def cumulative_mass_velocity(
    speeds: np.ndarray, masses: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """M(>v) kumulatif kutle-hiz dagilimi — kutulama YOK.

    Hizlar siralanir ve kutleler tersten toplanir; sonuc kutu genisligi
    secimine bagli degildir.
    """
    s = np.asarray(speeds, dtype=np.float64)
    m = np.asarray(masses, dtype=np.float64)
    if s.shape != m.shape:
        raise ValueError(f"hiz ve kutle sekilleri esit olmali: {s.shape}/{m.shape}")
    order = np.argsort(s)
    s_sorted = s[order]
    m_cum = np.cumsum(m[order][::-1])[::-1]
    return s_sorted, m_cum


def _fit_power_law(v: np.ndarray, mcum: np.ndarray) -> tuple[float, float]:
    """log M = a - mu log v dogrusunu uydur; (mu, R^2) dondur."""
    ok = (v > 0.0) & (mcum > 0.0)
    if np.count_nonzero(ok) < 3:
        return float("nan"), float("nan")
    lx = np.log(v[ok])
    ly = np.log(mcum[ok])
    if np.ptp(lx) <= 0.0:
        return float("nan"), float("nan")
    A = np.vstack([lx, np.ones_like(lx)]).T
    coef, *_ = np.linalg.lstsq(A, ly, rcond=None)
    pred = A @ coef
    ss_res = float(np.sum((ly - pred) ** 2))
    ss_tot = float(np.sum((ly - ly.mean()) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0.0 else float("nan")
    return float(-coef[0]), float(r2)


def catalog_ejecta(
    x: np.ndarray,
    v: np.ndarray,
    m: np.ndarray,
    *,
    center: np.ndarray,
    surface_normal: np.ndarray,
    control_radius: float,
    escape_speed: float,
    target_mass: float | None = None,
) -> EjectaCatalog:
    """Kontrol yuzeyini gecmis parcaciklari kataloglar.

    `surface_normal` carpma noktasindaki DISA dogru yuzey normalidir; firlatma
    acisi bu eksene gore olculur (0 = normal boyunca dik firlama). Ekseni
    z olarak sabitlemek duzensiz sekillerde sessizce baska bir aciyi olcerdi.
    """
    x = np.ascontiguousarray(x, dtype=np.float64)
    v = np.ascontiguousarray(v, dtype=np.float64)
    m = np.ascontiguousarray(m, dtype=np.float64)
    if not (len(x) == len(v) == len(m)):
        raise ValueError("x/v/m uzunluklari esit olmali")
    if control_radius <= 0.0:
        raise ValueError(f"kontrol yaricapi pozitif olmali, {control_radius} geldi")
    if escape_speed < 0.0:
        raise ValueError("kacis hizi negatif olamaz")

    c = np.asarray(center, dtype=np.float64).reshape(3)
    nrm = np.asarray(surface_normal, dtype=np.float64).reshape(3)
    nn = float(np.linalg.norm(nrm))
    if nn == 0.0:
        raise ValueError("yuzey normali sifir uzunlukta")
    nrm = nrm / nn

    r = x - c[None, :]
    dist = np.linalg.norm(r, axis=1)
    sel = dist > control_radius
    m_tot = float(np.sum(m)) if target_mass is None else float(target_mass)

    if not np.any(sel):
        return EjectaCatalog(
            n_ejecta=0, mass=0.0, mass_fraction=0.0,
            escaping_mass=0.0, escaping_fraction=0.0,
            speed_min=float("nan"), speed_max=float("nan"),
            speed_mass_weighted_mean=float("nan"),
            cone_angle_deg=float("nan"), cone_angle_spread_deg=float("nan"),
            power_law_exponent=float("nan"), power_law_r2=float("nan"),
            speed_bins=np.empty(0), cumulative_mass=np.empty(0),
            diagnostics={"control_radius": control_radius, "n_total": int(len(m)),
                         "reason": "kontrol yuzeyini gecen parcacik yok"},
        )

    vs, ms = v[sel], m[sel]
    sp = np.linalg.norm(vs, axis=1)
    m_ej = float(np.sum(ms))
    if m_ej <= 0.0:
        # Kutle agirlikli her buyukluk 0/0 olurdu; sessiz NaN yerine acik hata.
        raise ValueError(
            f"kontrol yuzeyi disinda {int(np.count_nonzero(sel))} parcacik var "
            "ama toplam kutleleri sifir — kutle dizisi bozuk")

    # firlatma acisi: hiz ile yuzey normali arasindaki aci
    with np.errstate(invalid="ignore", divide="ignore"):
        cosang = np.where(sp > 0.0, (vs @ nrm) / np.maximum(sp, 1e-300), 1.0)
    ang = np.degrees(np.arccos(np.clip(cosang, -1.0, 1.0)))
    w = ms / m_ej
    ang_mean = float(np.sum(w * ang))
    ang_std = float(np.sqrt(max(np.sum(w * (ang - ang_mean) ** 2), 0.0)))

    esc = sp > escape_speed
    m_esc = float(np.sum(ms[esc]))

    vb, mc = cumulative_mass_velocity(sp, ms)
    mu, r2 = _fit_power_law(vb, mc)

    return EjectaCatalog(
        n_ejecta=int(np.count_nonzero(sel)),
        mass=m_ej,
        mass_fraction=m_ej / m_tot if m_tot > 0.0 else float("nan"),
        escaping_mass=m_esc,
        escaping_fraction=m_esc / m_tot if m_tot > 0.0 else float("nan"),
        speed_min=float(sp.min()),
        speed_max=float(sp.max()),
        speed_mass_weighted_mean=float(np.sum(w * sp)),
        cone_angle_deg=ang_mean,
        cone_angle_spread_deg=ang_std,
        power_law_exponent=mu,
        power_law_r2=r2,
        speed_bins=vb,
        cumulative_mass=mc,
        diagnostics={
            "control_radius": control_radius,
            "escape_speed": escape_speed,
            "n_total": int(len(m)),
            "n_escaping": int(np.count_nonzero(esc)),
            "target_mass": m_tot,
            "surface_normal": nrm,
            "angle_min_deg": float(ang.min()),
            "angle_max_deg": float(ang.max()),
        },
    )
