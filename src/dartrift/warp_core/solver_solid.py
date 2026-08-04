"""Warp kati SPH cozucusu — FAZ 2 kernel sirasi (DR-RIFT-P2 §4.1).

cpu_reference/solid_ref.py ile ayni fizik ve ayni KDK + tam-trapez iskeleti;
test_solid_cross kucuk-N'de bit-yakin pariteyi sinar. Her modul (dayanim,
porozite, yercekimi) MaterialParams uzerinden acilir/kapanir (ablasyon,
P2-FR-06).
"""

from __future__ import annotations

import numpy as np
import warp as wp

from ..cpu_reference.materials import MaterialParams
from ..cpu_reference.sph_ref import RefParams
from ..invariants import InvariantViolation  # noqa: F401 (kapi betikleri yakalar)
from ..particles import _init_warp
from . import density as D
from . import eos_test as E
from . import integrator as I
from . import solid_stress as SS
from .damage_gradykipp import accumulate_damage_k, apply_damage_k, damage_rate_k
from .eos_tillotson import eos_solid, make_tillotson_wp
from .gravity_tree import GravitySolver
from .hash_grid import GridManager
from .porosity_palpha import make_porosity_wp, porosity_update_k
from .solver import _budget_row, _check_finite
from .strength_lundborg import make_strength_wp, return_mapping_k

F = wp.float64
V3 = wp.vec3d
M3 = wp.mat33d


class WarpSolid3D:
    """3B kati cozucu: yogunluk -> EOS(P-alpha) -> L -> dS/dt -> yercekimi -> kuvvet."""

    def __init__(
        self,
        x: np.ndarray,
        v: np.ndarray,
        m: np.ndarray,
        u: np.ndarray,
        h: float,
        mat: MaterialParams,
        num: RefParams | None = None,
        S0: np.ndarray | None = None,
        alpha0: np.ndarray | None = None,
        Y0: np.ndarray | None = None,
        active: np.ndarray | None = None,
        device: str = "cuda:0",
        check_every: int = 50,
        gravity_rebuild_every: int = 1,
        gravity_drift_tol: float = 0.25,
        damage_seed: int = 0,
    ):
        _init_warp()
        self.mat = mat
        self.num = num or RefParams()
        self.device = device
        self.check_every = check_every
        n = len(m)
        self.n = n
        # ADR-0041: `h` PARCACIK BASINA. Skaler verilirse yayilir ve
        # `h_ij = (h_i+h_j)/2` TAM OLARAK skaleri verir -> bit uyumu korunur.
        # `self.h` skaler ozeti tutar (dt/tani/API icin); cekirdekler DIZIYI
        # alir. Komsu arama yaricapi EN BUYUK h'ye gore (KAYIT-031/033).
        _h = np.asarray(h, dtype=np.float64)
        if _h.ndim == 0:
            self.h = float(_h)
            _h = np.full(len(m), self.h)
        else:
            if _h.shape != (len(m),):
                raise ValueError(f"h sekli {_h.shape}, ({len(m)},) olmali")
            if np.any(_h <= 0.0):
                raise ValueError(f"h pozitif olmali; en kucuk {float(_h.min())}")
            self.h = float(_h.max())
        self.h_min = float(_h.min())
        self._h_np = _h
        self.support = 2.0 * self.h
        dev = device
        self.h_arr = wp.array(_h, dtype=F, device=dev)
        self.x = wp.array(np.asarray(x, np.float64), dtype=V3, device=dev)
        self.v = wp.array(np.asarray(v, np.float64), dtype=V3, device=dev)
        self.m = wp.array(np.asarray(m, np.float64), dtype=F, device=dev)
        self.u = wp.array(np.asarray(u, np.float64), dtype=F, device=dev)
        act = np.ones(n, np.uint8) if active is None else np.asarray(active, np.uint8)
        self.active = wp.array(act, dtype=wp.uint8, device=dev)
        s0 = np.zeros((n, 3, 3)) if S0 is None else np.asarray(S0, np.float64)
        self.S = wp.array(s0, dtype=M3, device=dev)
        a0 = (
            np.full(n, mat.porosity.alpha0 if mat.porosity.enabled else 1.0)
            if alpha0 is None
            else np.asarray(alpha0, np.float64)
        )
        self.alpha = wp.array(a0, dtype=F, device=dev)
        # BASLANGIC distansiyonu — crush egrisinin TAVANI (ADR-0031).
        # Tavan PARCACIK BASINA olmali: gozeneklilik parcacik basinadir
        # (bloklar gozeneksiz, matris gozenekli). Skaler tavan, onu ASAN
        # parcaciklari ilk adimda EZIYOR ve -1,14 GPa yapay cekme doguruyordu.
        self.alpha_ref = wp.array(a0, dtype=F, device=dev)
        # Kohezyon PARCACIK BASINA: moloz yiginlarinda bloklar matristen daha
        # dayanikli (P3-FR-03/04). Homojen kosularda skaler deger dizi olarak
        # doldurulur — tek kod yolu, sonuc bit-ayni kalir.
        y0 = (
            np.full(n, mat.strength.Y0)
            if Y0 is None
            else np.asarray(Y0, np.float64)
        )
        if y0.shape != (n,):
            raise ValueError(f"Y0 sekli (n,)={n} olmali, {y0.shape} geldi")
        if mat.strength.enabled and np.any(y0 >= mat.strength.YM):
            # Y(P) formulunde (YM - Y0) paydada: esitlik sonsuza gider.
            raise ValueError("Y0 < YM olmali (Lundborg paydasi)")
        self.Y0 = wp.array(y0, dtype=F, device=dev)
        for name in ("rho", "P", "cs", "divv", "fbal", "dudt", "phi",
                     "drhodt", "plastic_du", "dt_cfl", "dt_acc"):
            setattr(self, name, wp.zeros(n, dtype=F, device=dev))
        self._continuity = mat.density_method == "continuity"
        if self._continuity:
            # rho artik bir DURUM degiskeni ve baslangici GOZENEKLILIGE
            # BAGLIDIR. P-alpha modelinde basinc P = P_kati(rho*alpha, u)/alpha
            # ile hesaplanir; gerilmesiz baslangic icin rho*alpha = rho0_kati,
            # yani rho = rho0_kati / alpha0 olmalidir.
            #
            # alpha0'a bolmeden (eski hali) malzeme daha t=0'da sikismis
            # sayiliyordu: alpha0=1.5 icin rho*alpha = 4050 ve P = 1.335e10 Pa
            # — durgun bir cisimde 13 GPa'lik hayali basinc. Bu, carpma
            # senaryosunda enerji defterini %92.9 hatayla bozuyordu (porozite
            # kapatilinca %0.56). Kombinasyon (sureklilik + porozite) hicbir
            # testte kosulmadigi icin gorulmemisti (ADR-0022).
            rho0 = mat.rho0_linear if mat.eos == "linear" else mat.tillotson.rho0
            self.rho = wp.array(np.asarray(rho0 / a0, np.float64), dtype=F, device=dev)
        elif mat.density_method != "summation":
            raise ValueError(f"bilinmeyen yogunluk yontemi: {mat.density_method!r}")
        self.a = wp.zeros(n, dtype=V3, device=dev)
        self.g = wp.zeros(n, dtype=V3, device=dev)
        self.L = wp.zeros(n, dtype=M3, device=dev)
        self.dSdt = wp.zeros(n, dtype=M3, device=dev)
        self.gridman = GridManager(n, dev)
        self._radius32 = 0.0
        self._tp = make_tillotson_wp(mat.tillotson)
        self._sp = make_strength_wp(mat.strength)
        self._pp = make_porosity_wp(mat.porosity)
        # --- Grady-Kipp hasar (P2 §1.3 STRETCH; ADR-0027) ---
        self._damage = mat.damage.enabled
        if self._damage:
            from ..cpu_reference.damage_ref import seed_flaws, youngs_modulus
            from .damage_gradykipp import make_damage_wp

            if not mat.strength.enabled:
                raise ValueError(
                    "hasar modeli dayanim ister: damage.enabled=True iken "
                    "strength.enabled=False anlamsizdir (deviatorik gerilme yok)")
            # IKI FARKLI HACIM — karistirilmasi olculmus bir kusurdu:
            #
            #  * KUSUR YOGUNLUGU icin KATI hacim (V_kati = m/rho0). Kusurlar
            #    katı malzemedeki mikro catlaklardir; gozenek hacmi kusur
            #    tasimaz. Parcacik BASINA verilir: ADR-0030'dan sonra moloz
            #    yiginlarinda bu hacim gercekten degisir (olculdu: blok 344.8
            #    vs matris 209.6 m^3, %56 yayilim). Eskiden `mean(m)` ile TEK
            #    degere indirgeniyordu.
            #
            #  * CATLAK YOLU icin GEOMETRIK hacim (V_geom = m*alpha/rho0).
            #    `damage_ref.damage_rate` r_s'yi "catlagin kat etmesi gereken
            #    uzunluk" diye tanimlar; catlak gozenekler dahil TUM parcacigi
            #    gecer. Eskiden r_s KATI hacimden hesaplaniyordu. Olculdu
            #    (alpha=1.5): r_s = 3.8624 m yerine 4.4214 m olmali, yani
            #    %12,6 kucuk; dD/dt ~ 1/r_s oldugundan hasar hizi %14,5 HIZLI
            #    calisiyordu.
            rho_mat = mat.rho0_linear if mat.eos == "linear" else mat.tillotson.rho0
            m64 = np.asarray(m, np.float64)
            v_kati = m64 / rho_mat                     # (N,) kusur hacmi
            v_geom = m64 * np.asarray(a0, np.float64) / rho_mat   # (N,) catlak yolu
            r_s = float(np.mean((3.0 * v_geom / (4.0 * np.pi)) ** (1.0 / 3.0)))
            e_min, n_fl = seed_flaws(n, v_kati, mat.damage, damage_seed)
            self.eps_min = wp.array(e_min, dtype=F, device=dev)
            self.n_flaws = wp.array(n_fl, dtype=F, device=dev)
            k_bulk = mat.c0**2 * mat.rho0_linear if mat.eos == "linear" \
                else mat.tillotson.A
            self._dp = make_damage_wp(
                mat.damage, r_s, youngs_modulus(k_bulk, mat.strength.shear_G))
            self.D = wp.zeros(n, dtype=F, device=dev)
            self.D_cbrt = wp.zeros(n, dtype=F, device=dev)
            self.dDdt_cbrt = wp.zeros(n, dtype=F, device=dev)
            self.strain = wp.zeros(n, dtype=F, device=dev)
            # TASINAN gerilme — DURUMDAN AYRI. `S` elastik durumdur ve
            # yalnizca `kick_S_3d` ile evrilir; hasar onu asla yazmaz.
            self.P_eff = wp.zeros(n, dtype=F, device=dev)
            self.S_eff = wp.zeros(n, dtype=M3, device=dev)
            self._damage_diag = {
                # IKI hacim de raporlanir: hangisinin nereye girdigi gorunsun.
                "flaw_volume_mean": float(np.mean(v_kati)),
                "flaw_volume_min": float(np.min(v_kati)),
                "flaw_volume_max": float(np.max(v_kati)),
                "crack_volume_mean": float(np.mean(v_geom)),
                "r_s": r_s,
                "n_flaws_total": float(n_fl.sum()),
                "eps_min_median": float(np.median(e_min[np.isfinite(e_min)]))
                if np.any(np.isfinite(e_min)) else float("nan"),
                "particles_without_flaw": int(np.count_nonzero(~np.isfinite(e_min))),
            }
        self._gravity = GravitySolver(mat.gravity, dev) if mat.gravity.enabled else None
        # yapay gerilme normalizasyonu W(dp): CPU referansiyla ayni deger
        from ..cpu_reference.sph_ref import kernel_w as _kw

        # Kafes referansi: degisken h'de EN KUCUK h (en siki paketleme).
        _dp = mat.artificial_stress.dp_over_h * self.h_min
        self._ast_w_dp = max(
            float(_kw(np.array([_dp / self.h_min]), self.h_min, 3)[0]), 1.0e-300)
        self._evaluated = False
        self._step_count = 0
        self._x_version = 0
        # Yercekimi agaci her K konum degisiminde bir yenilenir (ADR-0024).
        # K=1 tam dogruluk. K>1 agac kurulumunu (CPU'da Python; olculdu:
        # yercekimli degerlendirmenin %99.8'i) K kat ucuzlatir, ama
        # YAKLASIKLIKTIR. Olculen bagimlilik ADIM SAYISI degil SURUKLENME:
        #   suruklenme <= 0.06 aralik -> hata %0.96 (K=1 tabani %0.92 ile ayni)
        #   suruklenme  = 6.1 aralik  -> hata %542 (kullanilamaz)
        # Bu yuzden K>1 secildiginde suruklenme DENETLENIR; denetlenmeyen bir
        # yaklasiklik, olmayan bir yaklasikliktir.
        if gravity_rebuild_every < 1:
            raise ValueError('gravity_rebuild_every >= 1 olmali')
        self.gravity_rebuild_every = int(gravity_rebuild_every)
        if gravity_drift_tol <= 0.0:
            raise ValueError('gravity_drift_tol pozitif olmali')
        self.gravity_drift_tol = float(gravity_drift_tol)
        # Izleme yalnizca K>1 ve yercekimi acikken: her adimda v'yi CPU'ya
        # cekmek K=1'de bos maliyettir (orada zaten yaklasiklik yok).
        self._track_drift = (self.gravity_rebuild_every > 1
                             and self._gravity is not None)
        self._tree_drift = 0.0
        self._tree_drift_max = 0.0
        self._drift_exceeded = 0
        self.plastic_u_total = 0.0

    def _launch(self, kernel, inputs):
        wp.launch(kernel, dim=self.n, inputs=inputs, device=self.device)

    def _eval(self) -> None:
        self._radius32 = self.gridman.build(self.x, self.support)
        gid = self.gridman.id
        r32 = wp.float32(self._radius32)
        h = self.h_arr
        if not self._continuity:
            self._launch(D.density_3d, [gid, self.gridman.x32, self.x, self.m, h, r32, self.rho])
        if self.mat.eos == "tillotson":
            self._launch(eos_solid, [self.rho, self.u, self.alpha, self._tp, self.P, self.cs])
        elif self.mat.eos == "ideal_gas":
            self._launch(E.eos_ideal_gas, [self.rho, self.u, F(self.mat.gamma), self.P, self.cs])
        elif self.mat.eos == "linear":
            self._launch(
                E.eos_linear, [self.rho, F(self.mat.c0), F(self.mat.rho0_linear), self.P, self.cs]
            )
        else:
            raise ValueError(f"bilinmeyen EOS: {self.mat.eos!r}")
        self._launch(
            SS.velocity_gradient_3d,
            [gid, self.gridman.x32, self.x, self.v, self.m, self.rho, self.cs, h, r32,
             1 if self.num.use_balsara else 0, self.L, self.divv, self.fbal],
        )
        if self._continuity:
            self._launch(I.continuity_rate_3d, [self.rho, self.divv, self.drhodt])
        if self.mat.strength.enabled:
            self._launch(
                SS.stress_rate_3d,
                [self.L, self.S, F(self.mat.strength.shear_G),
                 1 if self.mat.strength.jaumann else 0, self.dSdt],
            )
        else:
            self.dSdt.zero_()
        if self._damage:
            # YER: gerilme hizindan SONRA, kuvvetlerden ONCE.
            #   - dSdt HAM S'den hesaplanmali (hasar, elastik evrimi degil
            #     TASINAN gerilmeyi zayiflatir);
            #   - kuvvetler ise ZAYIFLATILMIS P ve S'yi gormeli, yoksa hasarin
            #     dinamige hicbir etkisi olmaz.
            # SIRA: once hiz (ham gerilmeden), sonra uygulama. Tersi, hasarin
            # kendi tetigini zayiflatmasina ve buyumenin yapay yavaslamasina
            # yol acardi.
            self._launch(damage_rate_k,
                         [self.P, self.S, self.eps_min, self.n_flaws, self.cs,
                          self.active, self._dp, self.dDdt_cbrt, self.strain])
            # AYRI dizilere yazar; `S` durumuna DOKUNMAZ (bkz. apply_damage_k
            # basligindaki olcum: yerinde carpim S'yi adim basina (1-D)^2 ile
            # kuculterek 5 adimda 1000 kat sapma uretiyordu).
            self._launch(apply_damage_k,
                         [self.P, self.S, self.D, self.active,
                          self.P_eff, self.S_eff])
        if self._gravity is not None:
            # x_version: agac onbellegi icin. Konumlar yalnizca drift'te
            # degisir; step() icindeki ikinci _eval() ayni konumlari gorur ve
            # agac yeniden KURULMAZ (ADR-0021). Onbellek isabetinde GPU->CPU
            # kopyasi da atlanir.
            gver = self._x_version // self.gravity_rebuild_every
            hit = (self._gravity._cache_version == gver
                   and self._gravity._cache_arrays is not None
                   and self.mat.gravity.mode == "barnes_hut")
            if self._track_drift and not hit:
                # agac yenileniyor: birikmis suruklenme sifirlanir; asilan
                # tolerans SAYILIR ve budgets() ile raporlanir
                if self._tree_drift > self.gravity_drift_tol * self.h:
                    self._drift_exceeded += 1
                self._tree_drift = 0.0
            x_np = None if hit else self.x.numpy().astype(np.float64)
            m_np = None if hit else self.m.numpy()
            self._gravity.compute(self.x, self.m, self.g, self.phi, x_np, m_np,
                                  x_version=gver)
        else:
            self.g.zero_()
            self.phi.zero_()
        ast = self.mat.artificial_stress
        # Kuvvetler TASINAN gerilmeyi gorur. Hasar kapaliyken bunlar durumun
        # kendisidir (ek dizi yok, ek maliyet yok).
        p_use = self.P_eff if self._damage else self.P
        s_use = self.S_eff if self._damage else self.S
        self._launch(
            SS.forces_solid_3d,
            [gid, self.gridman.x32, self.x, self.v, self.m, self.rho, p_use, s_use,
             self.cs, self.fbal, self.g, h, r32, F(self.num.alpha_av), F(self.num.beta_av),
             1 if ast.enabled else 0, F(ast.eps), F(ast.n_exp), F(self._ast_w_dp),
             self.a, self.dudt],
        )

    # -- KDK + tam trapez (solid_ref.step_kdk_solid ile ayni sira) ----------
    def step(self, dt: float) -> None:
        if not self._evaluated:
            self._eval()
            self._evaluated = True
        half = F(dt * 0.5)
        self._launch(I.kick_v_3d, [self.v, self.a, self.active, half])
        self._launch(I.kick_u_3d, [self.u, self.dudt, self.active, half])
        self._launch(SS.kick_S_3d, [self.S, self.dSdt, self.active, half])
        if self._continuity:
            self._launch(I.accumulate_scalar_3d, [self.rho, self.drhodt, self.active, half])
        self._launch(I.drift_3d, [self.x, self.v, self.active, F(dt)])
        self._x_version += 1          # konumlar degisti -> agac gecersiz
        if self._track_drift:
            # Agac bayatlama DENETIMI (ADR-0024). Olculen bagimlilik: hata
            # parcacik ARALIGINA gore surukleneye baglidir, adim sayisina
            # degil. Ust sinir global maks hizla biriktirilir — kesin
            # surukleneden buyuk oldugu icin guvenli taraftadir.
            vmax = float(np.sqrt(np.max(np.sum(
                self.v.numpy().astype(np.float64) ** 2, axis=1))))
            self._tree_drift += abs(dt) * vmax
            self._tree_drift_max = max(self._tree_drift_max, self._tree_drift)
        self._eval()  # (x1, v_half)
        self._launch(I.kick_v_3d, [self.v, self.a, self.active, half])
        self._eval()  # (x1, v1)
        self._launch(I.kick_u_3d, [self.u, self.dudt, self.active, half])
        self._launch(SS.kick_S_3d, [self.S, self.dSdt, self.active, half])
        if self._continuity:
            self._launch(I.accumulate_scalar_3d, [self.rho, self.drhodt, self.active, half])
        if self.mat.strength.enabled:
            self._launch(
                return_mapping_k,
                [self.S, self.P, self.rho, self.active, self.Y0, self._sp,
                 self.plastic_du],
            )
            self.plastic_u_total += float(
                np.sum(self.m.numpy() * self.plastic_du.numpy())
            )
        if self.mat.porosity.enabled:
            # ORTUK cozum (ADR-0023): alpha, P'den ACIK okunamaz — cekirdek
            # rho ve u alir ve alpha = crush(P_kati(alpha*rho,u)/alpha)
            # denklemini bisection ile cozer.
            self._launch(
                porosity_update_k,
                [self.alpha, self.alpha_ref, self.rho, self.u, self.active,
                 self._pp, self._tp],
            )
        if self._damage:
            # Hasar TAM adimda ilerletilir (yariya bolunmez): D monoton ve
            # [0,1]'e kisik oldugu icin trapez yolunun bir anlami yok, ustelik
            # iki yarim adim monotonluk kisitlamasiyla birlesince tekrarlanabilir
            # olmayan bir sira dogururdu.
            self._launch(accumulate_damage_k,
                         [self.D_cbrt, self.dDdt_cbrt, self.D, self.active, F(dt)])
        self._step_count += 1

    def compute_dt(self, cfl: float | None = None) -> float:
        """CFL (boyuna elastik hiz) + ivme + gerinim (solid_ref ile ayni)."""
        cs = self.cs.numpy()
        rho = self.rho.numpy()
        if self.mat.strength.enabled:
            c_long = np.sqrt(cs**2 + (4.0 / 3.0) * self.mat.strength.shear_G / rho)
        else:
            c_long = cs
        divv = self.divv.numpy()
        visc = c_long + 1.2 * (
            self.num.alpha_av * c_long
            + self.num.beta_av * self._h_np * np.abs(divv)
        )
        dt_cfl = self._h_np / np.maximum(visc, 1e-300)
        a = self.a.numpy().astype(np.float64)
        amag = np.sqrt(np.sum(a * a, axis=1))
        dt_acc = np.sqrt(self._h_np / np.maximum(amag, 1e-300))
        lm = self.L.numpy().astype(np.float64).reshape(self.n, 9)
        lnorm = np.sqrt(np.sum(lm * lm, axis=1))
        dt_strain = 0.5 / np.maximum(lnorm, 1e-300)
        act = self.active.numpy().astype(bool)
        c = cfl if cfl is not None else self.num.cfl
        return c * float(np.min(np.minimum(np.minimum(dt_cfl, dt_acc), dt_strain)[act]))

    def budgets(self) -> dict:
        s = self.state_numpy()
        row = _budget_row(0.0, s["m"], s["v"], s["u"])
        ep = 0.5 * float(np.sum(s["m"] * s["phi"])) if self._gravity is not None else 0.0
        row["e_pot"] = ep
        row["e_tot"] = row["e_kin"] + row["e_int"] + ep
        row["plastic_cum"] = self.plastic_u_total
        # K21: rho <= 0 ASLA fizik degildir (sureklilikte drho/dt = -rho*div v
        # ustel azalir, sifiri ancak dt fazla buyukse gecer). EOS artik orada
        # NaN yerine sonlu bir deger dondurur — ama bu, sorunu MASKELEMEK
        # olmamali. Sayac sifirdan buyukse o kosu GECERSIZDIR.
        akt = self.active.numpy().astype(bool)
        row["nonpositive_density_count"] = int(
            np.count_nonzero(s["rho"][akt] <= 0.0))
        row["rho_min"] = (float(np.min(s["rho"][akt])) if akt.any()
                          else float("nan"))
        # Sessiz NaN'a karsi ikinci koruma: defterin kendisi sonlu mu?
        row["state_is_finite"] = bool(
            np.all(np.isfinite(s["rho"])) and np.all(np.isfinite(s["v"]))
            and np.all(np.isfinite(s["u"])))
        if self._damage:
            d = self.D.numpy()
            row["damage_mean"] = float(np.mean(d))
            row["damage_max"] = float(np.max(d))
            row["damage_fully_broken"] = int(np.count_nonzero(d >= 0.999))
            row["strain_max"] = float(np.max(self.strain.numpy()))
        if self._track_drift:
            # Yaklasikligin denetim kaydi (ADR-0024): kac kez tolerans asildi
            # ve en kotu suruklenme neydi. Sifir olmayan bir sayac, K'nin o
            # kosu icin fazla buyuk secildigi anlamina gelir.
            row["gravity_tree_drift_max_over_h"] = self._tree_drift_max / self.h
            row["gravity_tree_drift_exceeded"] = self._drift_exceeded
        if self.mat.strength.enabled:
            # TANI: deviatorik depolanmis elastik enerji (e_tot'a dahil DEGIL,
            # ADR-0012 — `u` bu isi zaten tasiyor)
            ss = np.einsum("nab,nab->n", s["S"], s["S"])
            row["e_dev_stored"] = float(
                np.sum(s["m"] * ss / (4.0 * self.mat.strength.shear_G * s["rho"]))
            )
            if self._damage:
                # `e_dev_stored` HAM S'den hesaplanir; hasarli malzemede
                # kuvvetlerin gordugu gerilme (1-D) S'dir. Yani dinamik olarak
                # ERISILEBILIR deviatorik enerji (1-D)^2 katidir. Ikisini de
                # yazmak zorunlu: yalnizca hamini raporlamak, var olmayan bir
                # enerjiyi varmis gibi gostermek olurdu.
                f2 = (1.0 - np.clip(self.D.numpy(), 0.0, 1.0)) ** 2
                row["e_dev_effective"] = float(
                    np.sum(s["m"] * f2 * ss
                           / (4.0 * self.mat.strength.shear_G * s["rho"]))
                )
        return row

    def run(self, t_end: float, max_steps: int = 500_000, budget_every: int = 10) -> dict:
        if not self._evaluated:
            self._eval()
            self._evaluated = True
        t = 0.0
        n_steps = 0
        row = self.budgets()
        row["t"] = t
        series = [row]
        while t < t_end and n_steps < max_steps:
            dt = self.compute_dt()
            dt = min(dt, t_end - t)
            self.step(dt)
            t += dt
            n_steps += 1
            if n_steps % budget_every == 0 or t >= t_end:
                row = self.budgets()
                row["t"] = t
                series.append(row)
            if n_steps % self.check_every == 0:
                s = self.state_numpy()
                _check_finite(n_steps, rho=s["rho"], u=s["u"], v=s["v"], x=s["x"])
        return {"t_end": t, "n_steps": n_steps, "budget_series": series}

    def state_numpy(self) -> dict:
        return {
            "x": self.x.numpy().astype(np.float64),
            "v": self.v.numpy().astype(np.float64),
            "m": self.m.numpy(),
            "u": self.u.numpy(),
            "rho": self.rho.numpy(),
            "P": self.P.numpy(),
            "cs": self.cs.numpy(),
            "S": self.S.numpy().astype(np.float64),
            "alpha": self.alpha.numpy(),
            "phi": self.phi.numpy(),
            "a": self.a.numpy().astype(np.float64),
            "D": self.D.numpy() if self._damage else np.zeros(self.n),
            "strain": self.strain.numpy() if self._damage else np.zeros(self.n),
        }
