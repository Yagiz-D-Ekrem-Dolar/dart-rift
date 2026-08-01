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

    def yield_stress(self, P: np.ndarray, Y0: np.ndarray | None = None) -> np.ndarray:
        """Y(P) = Y0 + mu*P/(1 + mu*P/(YM-Y0)); cekmede (P<0) Y0'a sabitlenir.

        Cekme zayiflamasi hasar modeliyle (STRETCH, D=0 bu fazda) gelir;
        burada negatif P icin pozitif kalan guvenli deger kullanilir.

        `Y0` verilirse PARCACIK BASINA kohezyon kullanilir (moloz yiginlarinda
        bloklar matristen daha dayanikli, P3-FR-03/04); verilmezse skaler alan
        degeri. GPU tarafi (strength_lundborg.yield_stress) ayni sozlesmeyi
        uygular, boylece heterojen durum da capraz kontrol edilebilir.
        """
        Pp = np.maximum(np.asarray(P, dtype=np.float64), 0.0)
        y0 = self.Y0 if Y0 is None else np.asarray(Y0, dtype=np.float64)
        return y0 + self.mu_f * Pp / (1.0 + self.mu_f * Pp / (self.YM - y0))


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
class ArtificialStressParams:
    """Monaghan (2000) yapay gerilmesi — cekme (tensile) kararsizligi icin.

    Negatif basincta SPH parcaciklari kumelenir ("tensile instability");
    DR-RIFT-P1 §9 ve DR-RIFT-P2 §9 bu riski adiyla listeler ve azaltimi
    "Wendland kernel + artificial stress" olarak verir. Wendland tek basina
    yetmedi: serbest yuzeyli Taylor carpmasinda ic enerji NEGATIFE dustu
    (ADR-0014).

    R_i = -eps * P_i / rho_i^2   (yalnizca P_i < 0 iken; aksi halde 0)
    a_i += -sum_j m_j (R_i + R_j) * f_ij^n * gradW_ij,
    f_ij = W(r_ij) / W(dp),  dp = ortalama parcacik araligi.
    """

    enabled: bool = False
    eps: float = 0.3
    n_exp: float = 4.0
    dp_over_h: float = 0.5  # dp = dp_over_h * h (h/dx=2.0 icin dx = 0.5h)


@dataclass(frozen=True)
class GravityParams:
    enabled: bool = False
    G: float = 6.674_30e-11
    eps: float = 0.0  # yumusatma [m]
    mode: str = "direct"  # "direct" | "barnes_hut"
    theta: float = 0.5


@dataclass(frozen=True)
class DamageParams:
    """Grady-Kipp hasar + Weibull kusur dagilimi (Benz & Asphaug 1995).

    FIZIK. Kirilgan bir kayada cekme dayanimi, malzemenin icindeki mikro
    CATLAKLARIN (flaw) dagilimiyla belirlenir. Weibull dagilimi, birim
    hacimde aktivasyon gerinimi `eps`ten KUCUK kusur sayisini verir:

        n(eps) = k * eps^m

    `m` kucukse kusurlar genis bir gerinim araligina yayilir (heterojen,
    "zayif" kaya); buyukse hepsi ayni gerinimde acilir (homojen, "gevrek").

    HASAR. Aktive olmus kusurlardan catlaklar `c_g` hiziyla buyur; hasar
    kubuk kokuyle dogrusal ilerler:

        d(D^(1/3))/dt = n_aktif * c_g / R_s

    `R_s` parcacigin etkin yaricapi, `c_g = crack_speed_frac * c_s`.
    D ∈ [0,1]; D=1 tamamen kirilmis (cekme tasiyamaz).

    ETKI. Hasar YALNIZCA CEKMEYI zayiflatir:
      - P < 0 ise P -> (1-D) * P    (kirik kaya cekme tasimaz)
      - S -> (1-D) * S              (deviatorik dayanim da duser)
    Basma (P > 0) ETKILENMEZ: kirik kaya hala basmaya dayanir. Bu ayrim
    fiziksel olarak kritiktir; ikisini birden zayiflatmak kraterlesmeyi
    tamamen yanlis yapar.

    `k` [1/m^3] ve `m` [-] malzemeye ozgudur; bazalt icin literaturde
    k ~ 1e29..1e61 (m ile birlikte kalibre edilir), m ~ 6..12
    (Benz & Asphaug 1995, Tablo 1). Varsayilanlar bazalt icindir ve
    FAZ 5'te posterior olarak SINANIR, varsayilmaz.
    """

    enabled: bool = False
    k_weibull: float = 1.0e29   # [1/m^3]
    m_weibull: float = 9.0      # [-]
    crack_speed_frac: float = 0.4   # c_g / c_s (Benz & Asphaug: ~0.4)
    n_flaws_per_particle: float = 10.0  # ortalama kusur/parcacik (tohumlama)


@dataclass(frozen=True)
class MaterialParams:
    """Bir kosunun tam malzeme tanimi. Ablasyon: her modul acilir/kapanir."""

    eos: str = "tillotson"  # "tillotson" | "ideal_gas" | "linear"
    gamma: float = 1.4
    c0: float = 1.0
    rho0_linear: float = 1.0
    # "summation": rho = sum_j m_j W_ij  (akiskan/sok senaryolari, FAZ 1)
    # "continuity": rho baslangicta malzeme yogunlugudur ve drho/dt ile evrilir
    #   (SERBEST YUZEYLI kati senaryolari). Summation, yuzeyde kernel
    #   eksikligi nedeniyle rho'yu ~%39'a dusurur ve lineer EOS'ta -0.61K'lik
    #   YAPAY cekme uretir; bu cozunurlukle GECMEZ (ADR-0015).
    density_method: str = "summation"
    tillotson: TillotsonParams = field(default_factory=TillotsonParams)
    strength: StrengthParams = field(default_factory=StrengthParams)
    porosity: PorosityParams = field(default_factory=lambda: PorosityParams(enabled=False))
    gravity: GravityParams = field(default_factory=GravityParams)
    damage: DamageParams = field(default_factory=DamageParams)
    artificial_stress: ArtificialStressParams = field(
        default_factory=ArtificialStressParams
    )

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
            damage=DamageParams(
                enabled=ph.damage.enabled,
                k_weibull=ph.damage.k_weibull,
                m_weibull=ph.damage.m_weibull,
                crack_speed_frac=ph.damage.crack_speed_frac,
                n_flaws_per_particle=ph.damage.n_flaws_per_particle,
            ),
            artificial_stress=ArtificialStressParams(
                enabled=ph.artificial_stress.enabled,
                eps=ph.artificial_stress.eps,
                n_exp=ph.artificial_stress.n_exp,
                dp_over_h=ph.artificial_stress.dp_over_h,
            ),
            density_method=ph.density_method,
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
    S: np.ndarray,
    P: np.ndarray,
    rho: np.ndarray,
    sp: StrengthParams,
    Y0: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """S_trial'i Y(P) akma yuzeyine cek; plastik isi yogunlugunu dondur.

    S: (N,3,3) deviatorik gerilme. Donen: (S_new, delta_u) — delta_u [J/kg],
    delta_u = f(1-f) (S_t:S_t) / (2 G rho)  (S_son : eps_plastik / rho).
    """
    S = np.asarray(S, dtype=np.float64)
    j2 = 0.5 * np.einsum("nij,nij->n", S, S)
    vm = np.sqrt(3.0 * j2)
    Y = np.broadcast_to(sp.yield_stress(P, Y0), vm.shape)
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


def solve_alpha_implicit(
    alpha_old: np.ndarray, rho: np.ndarray, u: np.ndarray, mat, n_iter: int = 40
) -> np.ndarray:
    """P-alpha distansiyonunu ORTUK coz: alpha = crush_alpha(P_kati(alpha*rho,u)/alpha).

    NEDEN ORTUK (ADR-0023): `porosity_update` bu denklemi ACIK cozuyordu —
    bir onceki adimin P'sinden alpha'yi okuyup dogrudan yaziyordu. Tillotson
    gibi sert bir EOS ile crush egrisi cok dar bir basinc araliginda asiliyor
    ve acik guncelleme ASIRI ATIYOR: olcumde alpha, sikistirma hizindan
    BAGIMSIZ olarak 1.5'ten 1.0'a TEK ADIMDA cokuyordu (maks |dalpha| ~ 0.5).

    Sonucu: alpha bir anda 1 olunca rho_s = alpha*rho aniden dusuyor, kati
    sahte bir cekmeye giriyor, ic enerji NEGATIFE dusuyor ve enerji defteri
    patliyordu (v=5 m/s'lik yavas sikistirmada %8127 hata).

    Ortuk cozumle (bisection, [1, alpha_eski] araliginda; kalinti monoton):
        hata %8127 -> %0.46,  u_min -1.8e5 -> +1.6,  maks|dalpha| 0.47 -> 0.0006
    ve alpha artik sikistirmayi IZLIYOR (v=5'te 1.494, v=500'de 1.051) —
    eskiden her durumda 1.000'e cokuyordu.

    Geri genlesme yasak: sonuc her zaman <= alpha_old.
    """
    alpha_old = np.asarray(alpha_old, dtype=np.float64)
    rho = np.asarray(rho, dtype=np.float64)
    u = np.asarray(u, dtype=np.float64)
    pp = mat.porosity
    if mat.eos != "tillotson":
        # Diger EOS'larda basinc alpha'ya baglanmiyor (compute_eos_solid),
        # dolayisiyla ortuk denklem yok; acik form dogrudur.
        p_now = np.zeros_like(alpha_old)
        return porosity_update(alpha_old, p_now, pp)[0]

    lo = np.ones_like(alpha_old)
    hi = alpha_old.copy()

    def _residual(a: np.ndarray) -> np.ndarray:
        p = tillotson_pressure(a * rho, u, mat.tillotson) / a
        target = np.maximum(1.0, np.minimum(alpha_old, pp.crush_alpha(p)))
        return a - target

    for _ in range(n_iter):
        mid = 0.5 * (lo + hi)
        neg = _residual(mid) < 0.0
        lo = np.where(neg, mid, lo)
        hi = np.where(neg, hi, mid)
    return np.minimum(alpha_old, 0.5 * (lo + hi))
