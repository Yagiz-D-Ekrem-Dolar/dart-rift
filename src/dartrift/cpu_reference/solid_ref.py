"""FAZ 2 kati SPH referansi — NumPy, Warp'tan bagimsiz (DR-RIFT-P2).

FAZ 1 hidrodinamigini tam gerilme tensorune genisletir:

    sigma = -P*I + S
    a_i    =  sum_j m_j (sigma_i/rho_i^2 + sigma_j/rho_j^2) . gradW_ij
              - sum_j m_j Pi_ij gradW_ij + g_i
    du_i   = -0.5 sum_j m_j v_ij . ((sigma_i/rho_i^2 + sigma_j/rho_j^2) . gradW_ij)
             + 0.5 sum_j m_j Pi_ij (v_ij . gradW_ij)

S = 0 ve yercekimi kapaliyken FAZ 1 formulasyonuna indirgenir (testle sabit).
Jaumann objektif hiz: dS/dt = 2G eps_dev + S.spin^T + spin.S.
P-alpha: P = P_solid(rho*alpha, u)/alpha; crush-curve geri genlesmez.
Yercekimi: dogrudan N^2 (Plummer yumusatmali), potansiyel muhasebeli.

Sayisal parametreler (AV, CFL, Balsara) RefParams'tan gelir; malzeme
parametreleri MaterialParams'tan. Ikisi ayri kaynaklardir (ADR-0006).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .materials import (
    MaterialParams,
    porosity_update,
    return_mapping,
    tillotson_pressure,
    tillotson_sound_speed,
)
from .sph_ref import AV_EPS, BALSARA_EPS, RefParams, kernel_dwdq, kernel_w

_I3 = np.eye(3)


@dataclass
class SolidState:
    """Kati SPH durumu; x/v (N, dim<=3), S tam (N,3,3) deviatorik tensor."""

    x: np.ndarray
    v: np.ndarray
    m: np.ndarray
    u: np.ndarray
    h: float
    active: np.ndarray
    S: np.ndarray = field(default=None)  # type: ignore[assignment]
    alpha: np.ndarray = field(default=None)  # type: ignore[assignment]
    # evaluate_solid doldurur:
    rho: np.ndarray = field(default=None)  # type: ignore[assignment]
    P: np.ndarray = field(default=None)  # type: ignore[assignment]
    cs: np.ndarray = field(default=None)  # type: ignore[assignment]
    L: np.ndarray = field(default=None)  # duzeltilmis hiz gradyani (N,3,3)
    grad_correction_used: np.ndarray = field(default=None)  # B tersinir mi (N,)
    divv: np.ndarray = field(default=None)  # type: ignore[assignment]
    drhodt: np.ndarray = field(default=None)  # yalnizca continuity modunda kullanilir
    a: np.ndarray = field(default=None)  # type: ignore[assignment]
    dudt: np.ndarray = field(default=None)  # type: ignore[assignment]
    dSdt: np.ndarray = field(default=None)  # type: ignore[assignment]
    g: np.ndarray = field(default=None)  # yercekimi ivmesi (N,dim)
    phi: np.ndarray = field(default=None)  # yercekimi potansiyeli (N,)
    plastic_u_total: float = 0.0  # kumulatif plastik is [J] (enerji panosu)

    def __post_init__(self) -> None:
        self.x = np.atleast_2d(np.asarray(self.x, dtype=np.float64))
        if self.x.shape[0] == 1 and self.x.shape[1] > 3:
            self.x = self.x.T
        self.v = np.asarray(self.v, dtype=np.float64).reshape(self.x.shape)
        self.m = np.asarray(self.m, dtype=np.float64)
        self.u = np.asarray(self.u, dtype=np.float64)
        self.active = np.asarray(self.active, dtype=bool)
        n = self.x.shape[0]
        if self.S is None:
            self.S = np.zeros((n, 3, 3))
        if self.alpha is None:
            self.alpha = np.ones(n)

    @property
    def n(self) -> int:
        return self.x.shape[0]

    @property
    def dim(self) -> int:
        return self.x.shape[1]


def _pair_geometry(state: SolidState):
    dx = state.x[:, None, :] - state.x[None, :, :]
    r = np.sqrt(np.sum(dx * dx, axis=2))
    q = r / state.h
    dwdq = kernel_dwdq(q, state.h, state.dim)
    with np.errstate(invalid="ignore", divide="ignore"):
        inv_r = np.where(r > 1.0e-12, 1.0 / r, 0.0)
    grad_w = (dwdq / state.h * inv_r)[:, :, None] * dx
    return dx, r, q, grad_w


def _embed3(vec: np.ndarray, dim: int) -> np.ndarray:
    """(...,dim) vektorlerini 3B'ye gom (1B testler icin x-ekseni)."""
    if dim == 3:
        return vec
    out = np.zeros(vec.shape[:-1] + (3,))
    out[..., :dim] = vec
    return out


def compute_eos_solid(state: SolidState, mat: MaterialParams) -> None:
    """EOS + P-alpha baglantisi: P = P_solid(rho*alpha, u) / alpha."""
    if mat.eos == "tillotson":
        rho_s = state.rho * state.alpha
        p_s = tillotson_pressure(rho_s, state.u, mat.tillotson)
        state.P = p_s / state.alpha
        # guvenli taraf: bulk cs yerine kati cs kullan (daha buyuk -> kucuk dt)
        state.cs = tillotson_sound_speed(rho_s, state.u, mat.tillotson)
    elif mat.eos == "ideal_gas":
        state.P = (mat.gamma - 1.0) * state.rho * state.u
        state.cs = np.sqrt(mat.gamma * np.maximum(state.P, 0.0) / state.rho)
    elif mat.eos == "linear":
        state.P = mat.c0**2 * (state.rho - mat.rho0_linear)
        state.cs = np.full(state.n, mat.c0)
    else:
        raise ValueError(f"bilinmeyen EOS: {mat.eos!r}")


def compute_gravity_direct(
    x: np.ndarray, m: np.ndarray, G: float, eps: float
) -> tuple[np.ndarray, np.ndarray]:
    """Dogrudan N^2 yercekimi (Plummer yumusatma) + potansiyel."""
    dxji = x[None, :, :] - x[:, None, :]  # x_j - x_i
    r2 = np.sum(dxji * dxji, axis=2) + eps * eps
    # diyagonal (i==i, r2 = eps^2; eps=0'da 0) sonradan sifirlanir — uyari yok
    with np.errstate(divide="ignore", invalid="ignore"):
        inv_r = 1.0 / np.sqrt(r2)
        np.fill_diagonal(inv_r, 0.0)
        inv_r3 = inv_r / r2
    np.fill_diagonal(inv_r3, 0.0)
    inv_r3 = np.nan_to_num(inv_r3, nan=0.0, posinf=0.0)
    g = G * np.einsum("j,ijd,ij->id", m, dxji, inv_r3)
    phi = -G * (inv_r @ m)
    return g, phi


def evaluate_solid(state: SolidState, mat: MaterialParams, num: RefParams) -> None:
    """Tam alan degerlendirmesi: rho, EOS, L, dS/dt, yercekimi, a, du/dt."""
    dx, r, q, grad_w = _pair_geometry(state)
    w = kernel_w(q, state.h, state.dim)
    if mat.density_method == "summation":
        state.rho = w @ state.m
    elif mat.density_method == "continuity":
        # rho durumun bir parcasidir; burada YENIDEN HESAPLANMAZ, yalnizca
        # degisim hizi uretilir ve integratör tarafindan ilerletilir.
        if state.rho is None:
            raise ValueError("continuity modunda baslangic rho'su verilmelidir")
    else:
        raise ValueError(f"bilinmeyen yogunluk yontemi: {mat.density_method!r}")

    compute_eos_solid(state, mat)

    vji = _embed3(state.v[None, :, :] - state.v[:, None, :], state.dim)
    gw3 = _embed3(grad_w, state.dim)

    # (a) AV/Balsara icin div v VE curl v: FAZ 1 ile BIREBIR ayni
    #     ayriklastirma, (1/rho_i) sum_j m_j (...). Bu buyuklukler asagidaki
    #     duzeltilmis L'den TUREMEZ; karisik form Balsara faktorunu degistirir
    #     ve kati cozucu, moduller kapaliyken bile FAZ 1'e indirgenmez
    #     (test_solid_cross iki kez bunu yakaladi).
    state.divv = np.einsum("j,nj->n", state.m, np.sum(vji * gw3, axis=2)) / state.rho
    curl_vec = np.einsum("j,nja->na", state.m, np.cross(vji, gw3)) / state.rho[:, None]
    curl_mag = np.sqrt(np.sum(curl_vec * curl_vec, axis=1))
    # Sureklilik denklemi: drho/dt = -rho div v. Summation modunda da uretilir
    # (capraz kontrol icin, P1-FR-02) ama orada rho'yu ILERLETMEZ.
    state.drhodt = -state.rho * state.divv

    # (b) Gerilme evrimi icin hiz gradyani: Randles-Libersky duzeltmesi
    #     L = [sum_j V_j (v_j-v_i) x gradW] . B^-1,
    #     B = sum_j V_j (x_j-x_i) x gradW.
    #     Duzeltme, LINEER hiz alanlarini TAM yeniden urettirir; rijit donme
    #     (v = omega x r) tam da lineer bir alandir, dolayisiyla objektiflik
    #     testi ancak bu duzeltmeyle gecer (duzeltmesiz ~%10 hata; ADR-0009).
    #     Serbest yuzeyde B tekillesirse duzeltmesiz forma dusulur.
    xji = _embed3(-dx, state.dim)  # dx = x_i - x_j
    vol_j = state.m / state.rho
    # optimize=True SECICI kullanilir — hepsine eklemek YAVASLATIR.
    # Olculdu (N=700): uc-operandli kasilmalar ve (n,3,3)x(n,n,3) carpimlari
    # BLAS yoluna dusunce 1.9-6.5x hizlaniyor; buna karsilik "j,nja->na",
    # "nja,nja->nj" ve "nj,nja,nja->n" gibi imzalar optimize=True ile
    # 0.4-0.7x, yani 1.5-2.5 KAT YAVASLIYOR. Karar her imza icin ayri
    # olculmustur (ADR-0018); "tutarlilik olsun" diye hepsine eklemeyin.
    l_raw = np.einsum("j,nja,njb->nab", vol_j, vji, gw3, optimize=True)
    b_mat = np.einsum("j,nja,njb->nab", vol_j, xji, gw3, optimize=True)
    det = np.linalg.det(b_mat)
    ok = np.abs(det) > 1.0e-6
    state.L = l_raw.copy()
    if np.any(ok):
        state.L[ok] = l_raw[ok] @ np.linalg.inv(b_mat[ok])
    state.grad_correction_used = ok

    # gerilme evrimi icin spin, DUZELTILMIS L'den (Balsara icin degil)
    spin = 0.5 * (state.L - np.transpose(state.L, (0, 2, 1)))
    if num.use_balsara and state.dim == 3:
        fbal = np.abs(state.divv) / (
            np.abs(state.divv) + curl_mag + BALSARA_EPS * state.cs / state.h
        )
    else:
        fbal = np.ones(state.n)

    # deviatorik gerilme hizi (dayanim aciksa); Jaumann terimleri ablasyonlu
    if mat.strength.enabled:
        eps_dot = 0.5 * (state.L + np.transpose(state.L, (0, 2, 1)))
        # iz, DUZELTILMIS L'den alinir (AV'nin divv'siyle karistirilmaz)
        tr_l = np.trace(state.L, axis1=1, axis2=2)
        eps_dev = eps_dot - (tr_l / 3.0)[:, None, None] * _I3
        G_sh = mat.strength.shear_G
        state.dSdt = 2.0 * G_sh * eps_dev
        if mat.strength.jaumann:
            state.dSdt = (
                state.dSdt
                + np.einsum("nab,ncb->nac", state.S, spin)  # S . spin^T
                + np.einsum("nab,nbc->nac", spin, state.S)  # spin . S
            )
    else:
        state.dSdt = np.zeros((state.n, 3, 3))

    # yercekimi
    if mat.gravity.enabled:
        x3 = np.zeros((state.n, 3))
        x3[:, : state.dim] = state.x
        g3, phi = compute_gravity_direct(x3, state.m, mat.gravity.G, mat.gravity.eps)
        state.g = g3[:, : state.dim]
        state.phi = phi
    else:
        state.g = np.zeros_like(state.x)
        state.phi = np.zeros(state.n)

    # tam-tensor cift kuvveti: T = (-P I + S)/rho^2
    T = (-state.P[:, None, None] * _I3 + state.S) / (state.rho**2)[:, None, None]

    # yapay viskozite (FAZ 1 ile ayni)
    vij3 = -vji
    vr = np.einsum("nja,nja->nj", vij3, _embed3(dx, state.dim))
    mu = state.h * vr / (r * r + AV_EPS * state.h**2)
    c_bar = 0.5 * (state.cs[:, None] + state.cs[None, :])
    rho_bar = 0.5 * (state.rho[:, None] + state.rho[None, :])
    pi_av = np.where(
        vr < 0.0,
        (-num.alpha_av * c_bar * mu + num.beta_av * mu * mu) / rho_bar,
        0.0,
    )
    pi_av *= 0.5 * (fbal[:, None] + fbal[None, :])

    # yapay gerilme (Monaghan 2000): cekme bolgesinde kumelenmeyi onler.
    # R_i = -eps P_i/rho_i^2 (yalnizca P_i<0), itme terimi f^n ile olceklenir.
    ast = mat.artificial_stress
    if ast.enabled:
        r_i = np.where(state.P < 0.0, -ast.eps * state.P / state.rho**2, 0.0)
        dp = ast.dp_over_h * state.h
        w_dp = float(kernel_w(np.array([dp / state.h]), state.h, state.dim)[0])
        f_ij = kernel_w(q, state.h, state.dim) / max(w_dp, 1.0e-300)
        r_pair = (r_i[:, None] + r_i[None, :]) * f_ij**ast.n_exp
    else:
        r_pair = None

    m_j = state.m[None, :]
    ones = np.ones_like(r)
    # a_i = T_i.(sum_j m_j gW) + sum_j m_j T_j.gW - sum_j m_j Pi gW + g
    s1 = np.einsum("nj,njb->nb", m_j * ones, gw3, optimize=True)
    a1 = np.einsum("nab,nb->na", T, s1)
    a2 = np.einsum("j,jab,njb->na", state.m, T, gw3, optimize=True)
    a_av = np.einsum("nj,njb->nb", m_j * pi_av, gw3, optimize=True)
    a_tot = a1 + a2 - a_av
    if r_pair is not None:
        a_tot = a_tot - np.einsum("nj,njb->nb", m_j * r_pair, gw3, optimize=True)
    state.a = a_tot[:, : state.dim] + state.g

    # du_i = -0.5 sum m_j v_ij.((T_i+T_j).gW) + 0.5 sum m_j Pi (v_ij.gW)
    ti_gw = np.einsum("nab,njb->nja", T, gw3, optimize=True)
    tj_gw = np.einsum("jab,njb->nja", T, gw3, optimize=True)
    du_t = -0.5 * np.einsum("nj,nja,nja->n", m_j * ones, vij3, ti_gw + tj_gw)
    du_av = 0.5 * np.einsum("nj,nja,nja->n", m_j * pi_av, vij3, gw3)
    state.dudt = du_t + du_av
    if r_pair is not None:
        # yapay gerilme SANAL bir kuvvettir (sayisal duzeltme); yaptigi is de
        # enerji defterine ayni tutarlilikla girer, yoksa E_tot korunmaz.
        state.dudt = state.dudt + 0.5 * np.einsum(
            "nj,nja,nja->n", m_j * r_pair, vij3, gw3
        )


def _apply_strength_and_porosity(state: SolidState, mat: MaterialParams) -> None:
    """Return mapping + P-alpha guncellemesi (adim sonunda).

    ENERJI MUHASEBESI (ADR-0012): plastik is `u`'ya EKLENMEZ. `dudt` zaten
    TAM gerilme tensorunun isini (-P I + S) tasir; deviatorik is orada
    sayilmistir. Return mapping S'yi kucultunce depolanmis elastik deviatorik
    enerji azalir ve fark isiya doner — bu, u sabit kalarak zaten gerceklesen
    bir IC DAGILIM degisikligidir. Ayrica eklemek ayni enerjiyi ikinci kez
    saymaktir; olculdu: Taylor barda plastik is 1001 J cikiyordu, oysa
    baslangic kinetik enerjisi 352 J idi (fiziksel olarak imkansiz).
    Plastik is yalnizca TANI olarak biriktirilir.
    """
    if mat.strength.enabled:
        S_new, du_pl = return_mapping(state.S, state.P, state.rho, mat.strength)
        act = state.active
        state.S[act] = S_new[act]
        state.plastic_u_total += float(np.sum(state.m[act] * du_pl[act]))
    if mat.porosity.enabled:
        a_new, _ = porosity_update(state.alpha, state.P, mat.porosity)
        state.alpha[state.active] = a_new[state.active]


def step_kdk_solid(state: SolidState, mat: MaterialParams, num: RefParams, dt: float) -> None:
    """KDK + tam-trapez u/S guncellemesi (sph_ref.step_kdk ile ayni iskelet)."""
    act = state.active
    cont = mat.density_method == "continuity"
    state.v[act] += 0.5 * dt * state.a[act]
    state.u[act] += 0.5 * dt * state.dudt[act]
    state.S[act] += 0.5 * dt * state.dSdt[act]
    if cont:
        state.rho[act] += 0.5 * dt * state.drhodt[act]
    state.x[act] += dt * state.v[act]
    evaluate_solid(state, mat, num)  # (x1, v_half)
    state.v[act] += 0.5 * dt * state.a[act]
    evaluate_solid(state, mat, num)  # (x1, v1)
    state.u[act] += 0.5 * dt * state.dudt[act]
    state.S[act] += 0.5 * dt * state.dSdt[act]
    if cont:
        state.rho[act] += 0.5 * dt * state.drhodt[act]
    _apply_strength_and_porosity(state, mat)


def compute_timestep_solid(state: SolidState, mat: MaterialParams, num: RefParams) -> float:
    """CFL (boyuna elastik hizla) + ivme + gerinim kriterleri (P2 §4.1)."""
    if mat.strength.enabled:
        c_long = np.sqrt(state.cs**2 + (4.0 / 3.0) * mat.strength.shear_G / state.rho)
    else:
        c_long = state.cs
    visc = c_long + 1.2 * (num.alpha_av * c_long + num.beta_av * state.h * np.abs(state.divv))
    dt_cfl = state.h / np.maximum(visc, 1.0e-300)
    amag = np.sqrt(np.sum(state.a * state.a, axis=1))
    dt_acc = np.sqrt(state.h / np.maximum(amag, 1.0e-300))
    lnorm = np.sqrt(np.einsum("nab,nab->n", state.L, state.L))
    dt_strain = 0.5 / np.maximum(lnorm, 1.0e-300)
    act = state.active
    return num.cfl * float(np.min(np.minimum(np.minimum(dt_cfl, dt_acc), dt_strain)[act]))


def deviatoric_energy(state: SolidState, mat: MaterialParams) -> float:
    """Deviatorik gerilmede DEPOLANMIS elastik enerji: S:S/(4 G rho) [J].

    TANI amaclidir; `e_tot`'a EKLENMEZ. `u` zaten tam gerilme tensorunun
    isini tasidigi icin bu enerji orada sayilidir (ADR-0012). Ayri raporlanir
    ki return mapping'in elastik->isi donusumu izlenebilsin.
    """
    if not mat.strength.enabled or state.S is None:
        return 0.0
    ss = np.einsum("nab,nab->n", state.S, state.S)
    return float(np.sum(state.m * ss / (4.0 * mat.strength.shear_G * state.rho)))


def budgets_solid(state: SolidState, mat: MaterialParams | None = None) -> dict:
    """Enerji panosu: kinetik + ic + yercekimi potansiyeli + plastik kumulatif."""
    ke = 0.5 * float(np.sum(state.m * np.sum(state.v * state.v, axis=1)))
    ie = float(np.sum(state.m * state.u))
    ep = 0.5 * float(np.sum(state.m * state.phi)) if state.phi is not None else 0.0
    mom = state.v.T @ state.m
    row = {
        "mass": float(np.sum(state.m)),
        "momentum": [float(p) for p in mom],
        "mom_scale": float(np.sum(state.m * np.sqrt(np.sum(state.v * state.v, axis=1)))),
        "e_kin": ke,
        "e_int": ie,
        "e_pot": ep,
        "e_tot": ke + ie + ep,
        "plastic_cum": state.plastic_u_total,
    }
    if mat is not None:
        row["e_dev_stored"] = deviatoric_energy(state, mat)  # tani, toplama dahil DEGIL
    return row


def run_solid(
    state: SolidState,
    mat: MaterialParams,
    num: RefParams,
    t_end: float,
    max_steps: int = 200_000,
    budget_every: int = 10,
) -> dict:
    if mat.density_method == "continuity" and state.rho is None:
        rho0 = mat.rho0_linear if mat.eos == "linear" else mat.tillotson.rho0
        state.rho = np.full(state.n, float(rho0))
    evaluate_solid(state, mat, num)
    t = 0.0
    n_steps = 0
    series = [dict(t=t, **budgets_solid(state, mat))]
    while t < t_end and n_steps < max_steps:
        dt = compute_timestep_solid(state, mat, num)
        dt = min(dt, t_end - t)
        step_kdk_solid(state, mat, num, dt)
        t += dt
        n_steps += 1
        if n_steps % budget_every == 0 or t >= t_end:
            series.append(dict(t=t, **budgets_solid(state, mat)))
    return {"t_end": t, "n_steps": n_steps, "budget_series": series}
