"""Kucuk-N FP64 SPH referansi — Warp'tan bagimsiz (P1 dosya sozlesmesi).

DR-RIFT-P1 §2'deki denklemlerin dogrudan, vektorlestirilmis NumPy uygulamasi.
1B ve 3B destekler (Wendland C2, boyuta uygun normalizasyon). Butun ciftler
O(N^2) taranir; kucuk-N dogrulama icindir, uretim degildir.

Fizik sozlesmesi (GPU ile birebir ayni olmali — test_sph_cross bunu sinar):
- yogunluk: toplama (summation); sureklilik denklemi capraz-kontrol icin ayri.
- ivme:  dv_i/dt = -sum_j m_j (P_i/rho_i^2 + P_j/rho_j^2 + Pi_ij) grad_i W_ij
- enerji: du_i/dt = 0.5 sum_j m_j (ayni terim) (v_i - v_j) . grad_i W_ij
- AV: Monaghan (alpha, beta) + Balsara sinirlayici (1B'de f=1).
- KDK leapfrog; adim basina TEK kuvvet degerlendirmesi (drift sonrasi).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .adaptive_h import pair_h, per_particle_h

_PI = np.pi
AV_EPS = 0.01  # mu_ij paydasindaki eps*h^2 katsayisi (sartname §2.5)
BALSARA_EPS = 1.0e-4  # f_i paydasindaki eps*c/h olceklendirme katsayisi
ACCEL_DT_TINY = 1.0e-300


# ---------------------------------------------------------------------------
# Wendland C2 (NumPy) — warp_core/kernel_fn.py ile ayni matematik
# ---------------------------------------------------------------------------


# Sabitlerin ISLEM SIRASI warp_core/kernel_fn.py ile birebir aynidir:
# c3 = (21/(16*pi)) / (h*h*h) — GPU/CPU sonuclari son-ulp'a kadar eslessin diye.
_C3_NUM = 21.0 / (16.0 * _PI)


def kernel_w(q: np.ndarray, h: float, dim: int) -> np.ndarray:
    q = np.asarray(q, dtype=np.float64)
    t = np.maximum(1.0 - 0.5 * q, 0.0)
    if dim == 3:
        c = _C3_NUM / (h * h * h)
        w = c * t * t * t * t * (2.0 * q + 1.0)
    elif dim == 1:
        c = 0.625 / h  # 5/8h
        w = c * t * t * t * (1.5 * q + 1.0)
    else:
        raise ValueError(f"desteklenmeyen boyut: {dim}")
    return np.where(q < 2.0, w, 0.0)


def kernel_dwdq(q: np.ndarray, h: float, dim: int) -> np.ndarray:
    q = np.asarray(q, dtype=np.float64)
    t = np.maximum(1.0 - 0.5 * q, 0.0)
    if dim == 3:
        c = _C3_NUM / (h * h * h)
        d = c * (-5.0 * q) * t * t * t
    elif dim == 1:
        c = 0.625 / h
        d = c * (-3.0 * q) * t * t
    else:
        raise ValueError(f"desteklenmeyen boyut: {dim}")
    return np.where(q < 2.0, d, 0.0)


# ---------------------------------------------------------------------------
# Durum ve parametreler
# ---------------------------------------------------------------------------


@dataclass
class RefParams:
    """Cozucu parametreleri. Config'ten `from_config` ile kurulur (ADR-0006)."""

    gamma: float = 1.4
    eos: str = "ideal_gas"  # "ideal_gas" | "linear"
    c0: float = 1.0  # linear EOS ses hizi
    rho0: float = 1.0  # linear EOS referans yogunlugu
    alpha_av: float = 1.0
    beta_av: float = 2.0
    use_balsara: bool = True
    cfl: float = 0.3

    @classmethod
    def from_config(cls, cfg, **overrides) -> RefParams:
        """RunConfig.numerics'ten AV/CFL parametrelerini tuket (ADR-0006)."""
        if cfg.numerics.kernel is not None and cfg.numerics.kernel != "wendland_c2":
            raise ValueError(f"FAZ 1 yalnizca wendland_c2 destekler: {cfg.numerics.kernel!r}")
        kw = {
            "cfl": cfg.numerics.cfl if cfg.numerics.cfl is not None else 0.3,
            "alpha_av": cfg.numerics.alpha_av,
            "beta_av": cfg.numerics.beta_av,
        }
        kw.update(overrides)
        return cls(**kw)


@dataclass
class RefState:
    """SPH durumu. x/v sekli (N, dim); sabit h (P1 §2.6: bu fazda zorunlu)."""

    x: np.ndarray
    v: np.ndarray
    m: np.ndarray
    u: np.ndarray
    # `h` SKALER ya da parcacik basina DIZI (ADR-0041).
    h: float | np.ndarray
    active: np.ndarray  # bool: False -> donmus sinir parcacigi (integre edilmez)
    # eval() tarafindan doldurulanlar:
    rho: np.ndarray = field(default=None)  # type: ignore[assignment]
    P: np.ndarray = field(default=None)  # type: ignore[assignment]
    cs: np.ndarray = field(default=None)  # type: ignore[assignment]
    divv: np.ndarray = field(default=None)  # type: ignore[assignment]
    curlv: np.ndarray = field(default=None)  # type: ignore[assignment]
    a: np.ndarray = field(default=None)  # type: ignore[assignment]
    dudt: np.ndarray = field(default=None)  # type: ignore[assignment]
    rho_cont: np.ndarray = field(default=None)  # sureklilik yogunlugu (capraz kontrol)

    def __post_init__(self) -> None:
        self.x = np.atleast_2d(np.asarray(self.x, dtype=np.float64))
        if self.x.shape[0] == 1 and self.x.shape[1] > 3:
            self.x = self.x.T
        self.v = np.asarray(self.v, dtype=np.float64).reshape(self.x.shape)
        self.m = np.asarray(self.m, dtype=np.float64)
        self.u = np.asarray(self.u, dtype=np.float64)
        self.active = np.asarray(self.active, dtype=bool)

    @property
    def n(self) -> int:
        return self.x.shape[0]

    @property
    def dim(self) -> int:
        return self.x.shape[1]


def _pair_geometry(state: RefState):
    """Cift matrisleri: dx (N,N,dim), r, q, gradW (N,N,dim)."""
    dx = state.x[:, None, :] - state.x[None, :, :]
    r = np.sqrt(np.sum(dx * dx, axis=2))
    hij = pair_h(state.h, len(state.m))
    q = r / hij
    dwdq = kernel_dwdq(q, hij, state.dim)
    with np.errstate(invalid="ignore", divide="ignore"):
        inv_r = np.where(r > 1.0e-12, 1.0 / r, 0.0)
    grad_w = (dwdq / hij * inv_r)[:, :, None] * dx
    return dx, r, q, grad_w


def compute_eos(state: RefState, params: RefParams) -> None:
    if params.eos == "ideal_gas":
        state.P = (params.gamma - 1.0) * state.rho * state.u
        state.cs = np.sqrt(params.gamma * np.maximum(state.P, 0.0) / state.rho)
    elif params.eos == "linear":
        state.P = params.c0**2 * (state.rho - params.rho0)
        state.cs = np.full(state.n, params.c0)
    else:
        raise ValueError(f"bilinmeyen test EOS'u: {params.eos!r}")


def evaluate(state: RefState, params: RefParams) -> None:
    """Tam alan degerlendirmesi: rho, P, cs, div/curl, Balsara, a, du/dt."""
    dx, r, q, grad_w = _pair_geometry(state)
    w = kernel_w(q, pair_h(state.h, len(state.m)), state.dim)

    # 1) summation yogunlugu (P1-FR-02)
    state.rho = w @ state.m

    # 2) EOS
    compute_eos(state, params)

    # 3) div v ve curl v (Balsara icin)
    vji = state.v[None, :, :] - state.v[:, None, :]  # v_j - v_i
    mw = state.m[None, :]
    div_pair = np.sum(vji * grad_w, axis=2)  # (N,N)
    state.divv = np.sum(mw * div_pair, axis=1) / state.rho
    if state.dim == 3:
        cr = np.cross(vji, grad_w)
        curl = np.sum(mw[:, :, None] * cr, axis=1) / state.rho[:, None]
        state.curlv = np.sqrt(np.sum(curl * curl, axis=1))
    else:
        state.curlv = np.zeros(state.n)

    if params.use_balsara and state.dim == 3:
        fbal = np.abs(state.divv) / (
            np.abs(state.divv) + state.curlv + BALSARA_EPS * state.cs / state.h
        )
    else:
        fbal = np.ones(state.n)

    # 4) yapay viskozite (Monaghan) — yaklasan ciftler
    vij = -vji  # v_i - v_j
    vr = np.sum(vij * dx, axis=2)  # v_ij . r_ij
    mu = state.h * vr / (r * r + AV_EPS * state.h**2)
    c_bar = 0.5 * (state.cs[:, None] + state.cs[None, :])
    rho_bar = 0.5 * (state.rho[:, None] + state.rho[None, :])
    pi_av = np.where(
        vr < 0.0,
        (-params.alpha_av * c_bar * mu + params.beta_av * mu * mu) / rho_bar,
        0.0,
    )
    pi_av *= 0.5 * (fbal[:, None] + fbal[None, :])

    # 5) antisimetrik kuvvet + tutarli enerji (P1 §2.3, KRITIK)
    p_over = state.P / state.rho**2
    term = p_over[:, None] + p_over[None, :] + pi_av  # (N,N) simetrik
    contrib = (state.m[None, :] * term)[:, :, None] * grad_w
    state.a = -np.sum(contrib, axis=1)
    state.dudt = 0.5 * np.sum(state.m[None, :] * term * np.sum(vij * grad_w, axis=2), axis=1)


def compute_continuity_rate(state: RefState) -> np.ndarray:
    """d(rho)/dt = sum_j m_j (v_i - v_j) . grad_i W_ij (capraz kontrol icin)."""
    dx, r, q, grad_w = _pair_geometry(state)
    vij = state.v[:, None, :] - state.v[None, :, :]
    return np.sum(state.m[None, :] * np.sum(vij * grad_w, axis=2), axis=1)


def compute_timestep(state: RefState, params: RefParams) -> tuple[float, dict]:
    """dt = C_cfl * min(CFL-viskoz, ivme) — kisit istatistigiyle (P1-FR-07)."""
    visc = state.cs + 1.2 * (
        params.alpha_av * state.cs + params.beta_av * state.h * np.abs(state.divv)
    )
    dt_cfl = state.h / np.maximum(visc, 1.0e-300)
    amag = np.sqrt(np.sum(state.a * state.a, axis=1))
    dt_acc = np.sqrt(state.h / np.maximum(amag, ACCEL_DT_TINY))
    act = state.active
    dt_all = np.minimum(dt_cfl, dt_acc)
    dt = params.cfl * float(np.min(dt_all[act]))
    n_act = int(np.count_nonzero(act))
    frac_cfl = float(np.count_nonzero(dt_cfl[act] <= dt_acc[act])) / max(n_act, 1)
    winner = "cfl_viscous" if bool(
        dt_cfl[act].min() <= dt_acc[act].min()
    ) else "acceleration"
    stats = {
        "dt": dt,
        "binding_criterion": winner,
        "pct_cfl_viscous": 100.0 * frac_cfl,
        "pct_acceleration": 100.0 * (1.0 - frac_cfl),
    }
    return dt, stats


def step_kdk(state: RefState, params: RefParams, dt: float) -> None:
    """Kick-Drift-Kick; state.a/dudt (x_n, v_n)'de gecerli olmali.

    Enerji tutarliligi (P1 §2.3 "enerji formu momentumla tutarli"):
    u tam trapezle guncellenir — D(x_n, v_n) ve D(x_{n+1}, v_{n+1})
    oranlarinin ortalamasi. Bu, adim basina IKI cift-degerlendirmesi
    gerektirir; tek-degerlendirmeli varyant enerji hatasinda O(dt)
    sistematik sapma birakiyordu (olculdu: 1.19% -> 0.02%, ADR-0007).
    Ikinci degerlendirme ayni zamanda bir SONRAKI adimin kick1'i icin
    (x,v)-tutarli a/dudt onbellegini kurar.
    """
    act = state.active
    state.v[act] += 0.5 * dt * state.a[act]
    state.u[act] += 0.5 * dt * state.dudt[act]  # D(x_n, v_n)
    state.x[act] += dt * state.v[act]
    # sureklilik yogunlugu capraz-kontrolu (zaman-merkezli v_half ile)
    if state.rho_cont is not None:
        state.rho_cont[act] += dt * compute_continuity_rate(state)[act]
    evaluate(state, params)  # (x_{n+1}, v_half) -> kick2 icin a
    state.v[act] += 0.5 * dt * state.a[act]
    evaluate(state, params)  # (x_{n+1}, v_{n+1}) -> tutarli onbellek
    state.u[act] += 0.5 * dt * state.dudt[act]  # D(x_{n+1}, v_{n+1})


def budgets(state: RefState) -> dict:
    """Korunum butcesi: kutle, momentum, enerji (sabit sirali toplamlar)."""
    ke = 0.5 * np.sum(state.m * np.sum(state.v * state.v, axis=1))
    ie = np.sum(state.m * state.u)
    mom = state.v.T @ state.m  # (dim,)
    return {
        "mass": float(np.sum(state.m)),
        "momentum": [float(p) for p in mom],
        "mom_scale": float(np.sum(state.m * np.sqrt(np.sum(state.v * state.v, axis=1)))),
        "e_kin": float(ke),
        "e_int": float(ie),
        "e_tot": float(ke + ie),
    }


def run_sph(
    state: RefState,
    params: RefParams,
    t_end: float,
    max_steps: int = 200_000,
    budget_every: int = 10,
    track_continuity: bool = False,
) -> dict:
    """Cozucuyu t_end'e kadar kosturur; korunum/timestep tanilarini dondurur."""
    evaluate(state, params)
    if track_continuity:
        state.rho_cont = state.rho.copy()
    t = 0.0
    n_steps = 0
    series = [dict(t=t, **budgets(state))]
    ts_stats: list[dict] = []
    while t < t_end and n_steps < max_steps:
        dt, stats = compute_timestep(state, params)
        dt = min(dt, t_end - t)
        step_kdk(state, params, dt)
        t += dt
        n_steps += 1
        ts_stats.append(stats)
        if n_steps % budget_every == 0:
            series.append(dict(t=t, **budgets(state)))
    series.append(dict(t=t, **budgets(state)))
    return {
        "t_end": t,
        "n_steps": n_steps,
        "budget_series": series,
        "timestep_stats": ts_stats,
    }


def conservation_errors(diag: dict) -> dict:
    """run_sph ciktisindan korunum hatalarini cikar (P1-VR-01..03)."""
    s = diag["budget_series"]
    m0 = s[0]["mass"]
    e0 = s[0]["e_tot"]
    p0 = np.array(s[0]["momentum"])
    p_scale = max(max(row["mom_scale"] for row in s), 1.0e-300)
    mass_err = max(abs(row["mass"] - m0) for row in s) / abs(m0)
    mom_err = max(
        float(np.max(np.abs(np.array(row["momentum"]) - p0))) for row in s
    ) / p_scale
    e_err = max(abs(row["e_tot"] - e0) for row in s) / abs(e0)
    return {"mass_rel": mass_err, "momentum_rel": mom_err, "energy_rel": e_err}
