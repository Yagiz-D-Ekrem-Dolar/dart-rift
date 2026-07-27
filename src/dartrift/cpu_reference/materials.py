"""FAZ 2 malzeme modelleri — NumPy referans uygulamalari (DR-RIFT-P2 §2).

Tek kaynak: GPU kernel'leri bu formullerle birebir ayni islem sirasini kullanir
ve test_solid_cross bunu sinar. Tum buyuklukler SI'dadir.

Iceriden disari:
- Tillotson EOS (sikismis/genlesmis/ara kollar) + FD tabanli ses hizi + taban.
- Lundborg/Collins basinca bagli dayanim Y(P) + von Mises return mapping.
- P-alpha porozite crush-curve (geri genlesme yok).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

# ---------------------------------------------------------------------------
# Parametre kaplari
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TillotsonParams:
    """Tillotson (1962) parametreleri. Varsayilan: bazalt, Benz & Asphaug (1999).

    Kaynak degerler (cgs -> SI): rho0=2.7 g/cc, A=B=2.67e11 dyn/cm^2,
    a=0.5, b=1.5, E0=4.87e12 erg/g, E_iv=4.72e10 erg/g, E_cv=1.82e11 erg/g,
    alpha=beta=5. "Bazalt" calisma varsayimidir, Dimorphos iddiasi degildir.
    """

    rho0: float = 2700.0
    A: float = 2.67e10
    B: float = 2.67e10
    a: float = 0.5
    b: float = 1.5
    u0: float = 4.87e8
    u_iv: float = 4.72e6
    u_cv: float = 1.82e7
    alpha_t: float = 5.0
    beta_t: float = 5.0
    cs_floor_frac: float = 0.05  # cs_min = frac * sqrt(A/rho0) (sayisal guvenlik)

    @property
    def cs_ref(self) -> float:
        return float(np.sqrt(self.A / self.rho0))


@dataclass(frozen=True)
class StrengthParams:
    """Lundborg/Collins tipi basinca bagli akma dayanimi (P2 §2.2).

    jaumann=False yalnizca objektiflik ablasyon testi icindir (P2-VR-01):
    donme terimleri kapatilinca rijit donmede S yanlis evrilir — testin
    gosterdigi tam olarak budur.
    """

    enabled: bool = True
    Y0: float = 1.0e5  # kohezyon [Pa] (Ek A: 1e-1..1e3 Pa taranacak; test degeri yuksek)
    mu_f: float = 0.8  # ic surtunme
    YM: float = 1.5e9  # yuksek basinc siniri [Pa]
    shear_G: float = 2.27e10  # kesme modulu [Pa] (bazalt ~22.7 GPa)
    jaumann: bool = True

    def yield_stress(self, P: np.ndarray) -> np.ndarray:
        """Y(P) = Y0 + mu*P/(1 + mu*P/(YM-Y0)); cekmede (P<0) Y0'a sabitlenir.

        Cekme zayiflamasi hasar modeliyle (STRETCH, D=0 bu fazda) gelir;
        burada negatif P icin pozitif kalan guvenli deger kullanilir.
        """
        Pp = np.maximum(np.asarray(P, dtype=np.float64), 0.0)
        return self.Y0 + self.mu_f * Pp / (1.0 + self.mu_f * Pp / (self.YM - self.Y0))


@dataclass(frozen=True)
class PorosityParams:
    """P-alpha crush-curve (P2 §2.4)."""

    enabled: bool = True
    alpha0: float = 1.5
    Pe: float = 1.0e6  # elastik esik [Pa]
    Ps: float = 1.0e8  # tam sikisma [Pa]
    n_exp: float = 2.0

    def crush_alpha(self, P: np.ndarray) -> np.ndarray:
        """Yukleme egrisi alpha(P) (henuz geri-genlesme kisiti uygulanmamis)."""
        P = np.asarray(P, dtype=np.float64)
        mid = 1.0 + (self.alpha0 - 1.0) * (
            np.clip((self.Ps - P) / (self.Ps - self.Pe), 0.0, 1.0) ** self.n_exp
        )
        return np.where(P <= self.Pe, self.alpha0, np.where(P >= self.Ps, 1.0, mid))


@dataclass(frozen=True)
class GravityParams:
    enabled: bool = False
    G: float = 6.674_30e-11
    eps: float = 0.0  # yumusatma [m]
    mode: str = "direct"  # "direct" | "barnes_hut"
    theta: float = 0.5


@dataclass(frozen=True)
class MaterialParams:
    """Bir kosunun tam malzeme tanimi. Ablasyon: her modul acilir/kapanir."""

    eos: str = "tillotson"  # "tillotson" | "ideal_gas" | "linear"
    gamma: float = 1.4
    c0: float = 1.0
    rho0_linear: float = 1.0
    tillotson: TillotsonParams = field(default_factory=TillotsonParams)
    strength: StrengthParams = field(default_factory=StrengthParams)
    porosity: PorosityParams = field(default_factory=lambda: PorosityParams(enabled=False))
    gravity: GravityParams = field(default_factory=GravityParams)

    @classmethod
    def from_config(cls, cfg) -> MaterialParams:
        """RunConfig.physics'i tuket (ADR-0006: dogrulanan alan kullanilir)."""
        ph = cfg.physics
        t = ph.tillotson
        s = ph.strength
        p = ph.porosity
        g = ph.gravity
        return cls(
            eos=ph.eos,
            gamma=ph.gamma,
            c0=ph.c0,
            rho0_linear=ph.rho0_linear,
            tillotson=TillotsonParams(
                rho0=t.rho0, A=t.A, B=t.B, a=t.a, b=t.b, u0=t.u0,
                u_iv=t.u_iv, u_cv=t.u_cv, alpha_t=t.alpha_t, beta_t=t.beta_t,
                cs_floor_frac=t.cs_floor_frac,
            ),
            strength=StrengthParams(
                enabled=s.enabled, Y0=s.Y0, mu_f=s.mu_f, YM=s.YM,
                shear_G=s.shear_G, jaumann=s.jaumann,
            ),
            porosity=PorosityParams(
                enabled=p.enabled, alpha0=p.alpha0, Pe=p.Pe, Ps=p.Ps, n_exp=p.n_exp
            ),
            gravity=GravityParams(
                enabled=g.enabled, G=g.G, eps=g.eps, mode=g.mode, theta=g.theta
            ),
        )


# ---------------------------------------------------------------------------
# Tillotson EOS
# ---------------------------------------------------------------------------


def tillotson_pressure(rho: np.ndarray, u: np.ndarray, p: TillotsonParams) -> np.ndarray:
    """Tillotson basinci; kollar: sikismis/soguk, genlesmis-sicak, ara enterpolasyon."""
    rho = np.asarray(rho, dtype=np.float64)
    u = np.maximum(np.asarray(u, dtype=np.float64), 0.0)
    eta = rho / p.rho0
    mu_t = eta - 1.0
    omega = u / (p.u0 * eta * eta) + 1.0

    p_cold = (p.a + p.b / omega) * rho * u + p.A * mu_t + p.B * mu_t * mu_t

    ex = np.exp(-p.beta_t * (1.0 / eta - 1.0))
    ex2 = np.exp(-p.alpha_t * (1.0 / eta - 1.0) ** 2)
    p_hot = p.a * rho * u + (p.b * rho * u / omega + p.A * mu_t * ex) * ex2

    expanded = eta < 1.0
    hot = expanded & (u >= p.u_cv)
    mid = expanded & (u > p.u_iv) & (u < p.u_cv)

    out = p_cold.copy()
    out[hot] = p_hot[hot]
    if np.any(mid):
        w = (u[mid] - p.u_iv) / (p.u_cv - p.u_iv)
        out[mid] = (1.0 - w) * p_cold[mid] + w * p_hot[mid]
    return out


def tillotson_sound_speed(rho: np.ndarray, u: np.ndarray, p: TillotsonParams) -> np.ndarray:
    """cs^2 = dP/drho|_u + (P/rho^2) dP/du|_rho — merkezli sonlu farkla.

    FD adimlari goreli ve deterministiktir; GPU ayni formulu kullanir.
    Taban: cs >= cs_floor_frac * sqrt(A/rho0) (negatif/patlayan cs'e karsi).
    """
    rho = np.asarray(rho, dtype=np.float64)
    u = np.asarray(u, dtype=np.float64)
    d_rho = 1.0e-6 * np.maximum(rho, 1.0e-3 * p.rho0)
    d_u = 1.0e-6 * np.maximum(np.abs(u), 1.0e-6 * p.u0)
    P0 = tillotson_pressure(rho, u, p)
    dP_drho = (tillotson_pressure(rho + d_rho, u, p) - tillotson_pressure(rho - d_rho, u, p)) / (
        2.0 * d_rho
    )
    dP_du = (tillotson_pressure(rho, u + d_u, p) - tillotson_pressure(rho, u - d_u, p)) / (
        2.0 * d_u
    )
    cs2 = dP_drho + P0 / (rho * rho) * dP_du
    cs_min = p.cs_floor_frac * p.cs_ref
    return np.sqrt(np.maximum(cs2, cs_min * cs_min))


# ---------------------------------------------------------------------------
# Dayanim: von Mises return mapping (P2 §2.2, §5.2)
# ---------------------------------------------------------------------------


def return_mapping(
    S: np.ndarray, P: np.ndarray, rho: np.ndarray, sp: StrengthParams
) -> tuple[np.ndarray, np.ndarray]:
    """S_trial'i Y(P) akma yuzeyine cek; plastik isi yogunlugunu dondur.

    S: (N,3,3) deviatorik gerilme. Donen: (S_new, delta_u) — delta_u [J/kg],
    delta_u = f(1-f) (S_t:S_t) / (2 G rho)  (S_son : eps_plastik / rho).
    """
    S = np.asarray(S, dtype=np.float64)
    j2 = 0.5 * np.einsum("nij,nij->n", S, S)
    vm = np.sqrt(3.0 * j2)
    Y = sp.yield_stress(P)
    # f yalnizca akan parcaciklarda hesaplanir; np.where her iki dali da
    # degerlendirdigi icin bolme akmayanlarda tasma uretiyordu (Y=1e12,
    # vm=0 -> inf). Maske ile yalnizca gecerli girdilerde bol.
    f = np.ones_like(vm)
    yielding = (vm > Y) & (vm > 0.0)
    f[yielding] = Y[yielding] / vm[yielding]
    S_new = S * f[:, None, None]
    ss = 2.0 * j2  # S:S
    du = f * (1.0 - f) * ss / (2.0 * sp.shear_G * np.asarray(rho, dtype=np.float64))
    return S_new, du


# ---------------------------------------------------------------------------
# P-alpha porozite (nokta modeli — SPH baglantisi solid_ref icinde)
# ---------------------------------------------------------------------------


def porosity_update(
    alpha: np.ndarray, P: np.ndarray, pp: PorosityParams
) -> tuple[np.ndarray, np.ndarray]:
    """alpha_new = min(alpha_eski, alpha(P)) (>=1, geri genlesme yok).

    Donen: (alpha_new, compaction_work_per_mass) — nokta-model isi:
    w = P * (alpha_eski - alpha_yeni) / (alpha_eski * rho_bulk) yerine burada
    rho'suz NORMALIZE is (P * dalpha / alpha) dondurulur; SPH baglantisinda
    enerji cift-terimli PdV isinde zaten muhasebe edildiginden AYRICA
    eklenmez (cifte sayim olurdu; bkz. ADR-0008). Nokta-model testleri bu
    buyuklugun pozitifligini ve monotonlugunu sinar.
    """
    alpha = np.asarray(alpha, dtype=np.float64)
    a_curve = pp.crush_alpha(P)
    a_new = np.minimum(alpha, np.maximum(1.0, a_curve))
    w_norm = np.asarray(P, dtype=np.float64) * (alpha - a_new) / alpha
    return a_new, np.maximum(w_norm, 0.0)
