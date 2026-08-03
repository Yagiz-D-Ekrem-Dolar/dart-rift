# Kusur kaydı — kod düzeyi: önce/sonra ve yeniden üretme

Bu belge [`KUSUR-KAYDI.md`](KUSUR-KAYDI.md)'nin **kod tarafıdır**. Orası
*ne olduğunu* anlatır; burası **tam olarak hangi satırın ne olduğunu** ve
ölçümün **nasıl tekrarlanacağını** verir.

Her kayıt üç bölümdür:

- **ÖNCE / SONRA** — gerçek kod, kısaltılmamış
- **YENİDEN ÜRET** — çalıştırılabilir ölçüm betiği
- **NEDEN BÖYLE** — alternatifler ve neden seçilmediği

> Betikler `PYTHONPATH=src` ile depo kökünden çalışır. GPU gerektirenler
> işaretlidir.

---

## K1 — Hasar, `S` durum değişkenini bozuyordu

**Dosya:** `src/dartrift/warp_core/damage_gradykipp.py`

### ÖNCE
```python
@wp.kernel
def apply_damage_k(P: wp.array(dtype=F), S: wp.array(dtype=M3),
                   D: wp.array(dtype=F), active: wp.array(dtype=wp.uint8)):
    i = wp.tid()
    if active[i] == wp.uint8(0):
        return
    d = D[i]
    if d <= F(0.0):
        return
    f = F(1.0) - d
    if P[i] < F(0.0):
        P[i] = f * P[i]        # <-- DURUMU yaziyor
    S[i] = f * S[i]            # <-- DURUMU yaziyor
```

### SONRA
```python
@wp.kernel
def apply_damage_k(P: wp.array(dtype=F), S: wp.array(dtype=M3),
                   D: wp.array(dtype=F), active: wp.array(dtype=wp.uint8),
                   P_eff: wp.array(dtype=F), S_eff: wp.array(dtype=M3)):
    i = wp.tid()
    if active[i] == wp.uint8(0):
        P_eff[i] = P[i]; S_eff[i] = S[i]; return
    d = D[i]
    if d <= F(0.0):
        P_eff[i] = P[i]; S_eff[i] = S[i]; return
    if d > F(1.0):
        d = F(1.0)
    f = F(1.0) - d
    P_eff[i] = f * P[i] if P[i] < F(0.0) else P[i]
    S_eff[i] = f * S[i]        # AYRI dizi — durum okunur, yazilmaz
```

Çağrı yerinde (`solver_solid._eval`), kuvvetler artık taşınan gerilmeyi görür:
```python
p_use = self.P_eff if self._damage else self.P
s_use = self.S_eff if self._damage else self.S
self._launch(SS.forces_solid_3d, [..., p_use, s_use, ...])
```

### YENİDEN ÜRET *(GPU)*
```python
# D sabit tut, hicbir gerinim uretme -> S DEGISMEMELI
D = np.full(n, 0.5); s.D.assign(D); s.D_cbrt.assign(np.cbrt(D))
S0 = np.zeros((n,3,3)); S0[:,0,1] = S0[:,1,0] = 1.0e7
s.S.assign(np.ascontiguousarray(S0))
for k in range(4):
    s.D.assign(D); s.D_cbrt.assign(np.cbrt(D))
    s._eval()
    print(k, s.S.numpy()[0,0,1], s.S_eff.numpy()[0,0,1])
```
Tam betik: `/arf/scratch/egitimg16/driftclaude/dbg_damage2.py`

**Beklenen (düzeltilmiş):** `S` sabit `1.000000e+07`, `S_eff` sabit
`5.000000e+06`.
**Kusurlu hâlde:** `5.0e6 / 2.5e6 / 1.25e6 / 6.25e5`.

### NEDEN BÖYLE
Alternatif 1: *`_eval()`'i adım başına bir kez çağır.* Reddedildi — KDK'nın
tam-trapez `u`/`S` güncellemesi iki değerlendirme **gerektirir** (ADR-0007).

Alternatif 2: *`S`'yi her `_eval()` başında yedekle, sonunda geri yükle.*
Reddedildi — ek kopya maliyeti ve "durum bozuluyor ama telafi ediyoruz"
mantığı; kusuru gizler.

Seçilen: **durumu hiç yazma.** Hasar kapalıyken `p_use`/`s_use` durumun
kendisidir — ek dizi yok, ek maliyet yok.

---

## K2 — Krater çıkarıcı cismi küre sanıyordu

**Dosya:** `src/dartrift/observables/crater_shape.py`

### ÖNCE
```python
r_ref_global = float(np.median(rad[ref_sel]))
...
prof_ref = np.full(n_bins, r_ref_global)     # SABIT — cisim kure varsayiliyor
dev = prof_ref - prof_r
```

### SONRA
```python
def _yuzey_profili(pts):
    idx = surface_particles(pts, c)
    rr = pts[idx] - c[None, :]
    dd = np.linalg.norm(rr, axis=1)
    ca = np.clip((rr @ axis) / np.maximum(dd, 1e-300), -1.0, 1.0)
    return dd, np.degrees(np.arccos(ca))

if x_reference is not None:
    rad0, ang0 = _yuzey_profili(x0)
    r0_global = float(np.median(rad0[ang0 > outer_angle_deg]))
    global_shift = r_ref_global - r0_global      # kuresel olcek kaymasi
    prof_ref = _kutula(rad0, ang0)[0] + global_shift
else:
    prof_ref = np.full(n_bins, r_ref_global)     # eski davranis + TANI
```

Tanı: `diagnostics["reference_is_spherical"] = (x_reference is None)`

### YENİDEN ÜRET
```python
import numpy as np
from dartrift.observables.crater_shape import crater_profile
rng = np.random.default_rng(1); n = 60000
p = rng.normal(size=(n,3)); p /= np.linalg.norm(p,axis=1)[:,None]
a,b,c = 44.0, 43.5, 32.5                       # Dimorphos 88x87x65
x0 = p * (rng.random(n)**(1/3))[:,None] * np.array([a,b,c])
ort = dict(center=np.zeros(3), impact_direction=np.array([0.,0.,-1.]),
           reference_radius=40.0, outer_angle_deg=60.0, n_bins=12)
print("kuresel referans :", crater_profile(x0, **ort).depth)              # 9.04
print("gercek referans  :", crater_profile(x0, **ort, x_reference=x0).depth)  # 0.0
```

### NEDEN BÖYLE
Alternatif: *`x_reference`'ı zorunlu yap.* Şu an reddedildi — küre
senaryolarını (birim testler, RT9) gereksiz kırardı. Yerine tanı + G3 C5'te
düzensiz cisim senaryosu şart. **FAZ 4'te zorunlu yapılmalı** (EKSIKLER §F).

---

## K7 — Kütle ile gözeneklilik tutarsızdı

**Dosya:** `src/dartrift/setup/rubble_generator.py`

### ÖNCE
```python
def build_rubble_pile(mesh, spacing, bulk_density, root_seed,
                      model_class="M0", matrix_alpha0=1.6, ...):
    x = fill_particles(mesh, spacing, packing=packing)
    v_p = particle_volume(spacing, packing)
    m = np.full(len(x), bulk_density * v_p)      # TEKDUZE — rho0'i BILMIYOR
    ...
    alpha0, y0, is_b = assign_material(x, boulders, matrix_alpha0, ...)
```

Çözücü ise (`solver_solid.__init__`):
```python
self.rho = wp.array(rho0 / a0, ...)              # PARCACIK BASINA
```

**Çelişki:** `m/rho = bulk_density·V_p·α/ρ₀ ≠ V_p`.

### SONRA
```python
def build_rubble_pile(mesh, spacing, bulk_density, root_seed, *,
                      rho0_solid,                       # ZORUNLU oldu
                      model_class="M0", matrix_alpha0=None, ...):
    ...
    # blok kesri ancak yerlestirmeden SONRA bilinir
    _, _, is_b_on = assign_material(x, boulders, 1.0, 0.0, 1.0, 0.0)
    f_parcacik = float(np.count_nonzero(is_b_on) / max(len(x), 1))
    alpha_m_cozulen = matrix_alpha0_for_bulk_density(
        bulk_density, rho0_solid, boulder_alpha0, f_parcacik)
    alpha_m = alpha_m_cozulen if matrix_alpha0 is None else float(matrix_alpha0)

    alpha0, y0, is_b = assign_material(x, boulders, alpha_m, ...)
    m = (rho0_solid / alpha0) * v_p              # KUTLE GOZENEKLILIKTEN TURER

    rho_yigin = float(np.sum(m) / (len(x) * v_p))
    if matrix_alpha0 is not None and abs(rho_yigin - bulk_density)/bulk_density > 1e-9:
        raise ValueError(f"... hedefi tutturan deger {alpha_m_cozulen:.6f} ...")
```

Yeni yardımcı:
```python
def matrix_alpha0_for_bulk_density(bulk_density, rho0_solid,
                                   boulder_alpha0, boulder_particle_fraction):
    f = boulder_particle_fraction
    kalan = bulk_density - f * (rho0_solid / boulder_alpha0)
    if kalan <= 0.0:
        raise ValueError("hedef yigin yogunlugu ulasilamaz: ...")
    alpha_m = rho0_solid * (1.0 - f) / kalan
    if alpha_m < 1.0:
        raise ValueError("cozulen matris distansiyonu < 1: fiziksel degil")
    return float(alpha_m)
```

### YENİDEN ÜRET — birim bölünmesi
```python
import numpy as np
from dartrift.setup.rubble_generator import build_rubble_pile
from dartrift.setup.shape_mesh import icosphere
from dartrift.cpu_reference.sph_ref import kernel_w
rho0, s, h = 2700.0, 8.0, 16.0
p = build_rubble_pile(icosphere(3, 60.0), spacing=s, bulk_density=1800.0,
                      root_seed=5, rho0_solid=rho0, model_class="M1",
                      f_boulder=0.2, q=3.0, r_min=16.0, r_max=32.0)
rho = rho0 / p.alpha0
D = np.linalg.norm(p.x[:,None,:]-p.x[None,:,:], axis=2)
S = kernel_w(D/h, h, 3) @ (p.m/rho)              # 1.0 OLMALI
ic = np.linalg.norm(p.x, axis=1) < 30.0
print("matris:", S[ic & ~p.is_boulder].mean(), "blok:", S[ic & p.is_boulder].mean())
```
**Kusurlu hâlde:** matris 0,9519 · blok **0,8031**
**Düzeltilmiş:** ikisi de **1,0002**

> `kernel_w`'nin ilk argümanı **`q = r/h`**, ham mesafe değil. İlk ölçümümde
> bunu kaçırdım ve saçma sayılar aldım; kalibrasyonla anlaşıldı.

### NEDEN BÖYLE
Alternatif 1: *kütleleri `1/fill_ratio` ile ölçekle ki toplam kütle
`bulk_density·V_mesh` olsun.* Reddedildi — `m_i = ρ_i·V_p` bozulur, yani
K7'nin kendisi geri gelir.

Alternatif 2: *`bulk_density`'yi türetilmiş yap, `alpha`ları girdi al.*
Reddedildi — yığın yoğunluğu **gözlemsel** bir kısıttır (kütle/hacim);
gözeneklilik ise **çıkarılacak** parametredir. Türetilmesi gereken odur.

---

## K10 — Crush tavanı skalerdi

**Dosya:** `src/dartrift/warp_core/porosity_palpha.py`, `cpu_reference/materials.py`

### ÖNCE (GPU)
```python
@wp.func
def crush_alpha(P: F, pp: PorosityWp) -> F:
    if P <= pp.Pe:
        return pp.alpha0            # SKALER tavan
    ...

@wp.kernel
def porosity_update_k(alpha, rho, u, active, pp, tp):
    ...
```

### SONRA (GPU)
```python
@wp.func
def crush_alpha(P: F, a0: F, pp: PorosityWp) -> F:
    if P <= pp.Pe:
        return a0                   # PARCACIK BASINA tavan
    if P >= pp.Ps:
        return F(1.0)
    t = (pp.Ps - P) / (pp.Ps - pp.Pe)
    return F(1.0) + (a0 - F(1.0)) * wp.pow(t, pp.n_exp)

@wp.kernel
def porosity_update_k(alpha, alpha_ref, rho, u, active, pp, tp):
    i = wp.tid()
    a0 = alpha_ref[i]
    ...
```

CPU tarafı (`PorosityParams.crush_alpha`) `alpha_ref=None` ile geriye dönük;
`SolidState.alpha_ref` yoksa `__post_init__` `alpha`nın kopyasını alır.

### YENİDEN ÜRET *(GPU)*
```python
# ayni yigin, IKI farkli malzeme tavani
for mat_alpha0 in (1.6, 1.7273):
    ...   # bkz. /arf/scratch/egitimg16/driftclaude/dbg_alpha.py
```
**Beklenen:** tavan 1,6 iken adım 1'de α **1,600000**'a ezilir, adım 2'de
`P = −1,1389e+09 Pa`; tavan 1,7273 iken α **sabit**, `P ~ 1e-3 Pa`.
KE oranı **8,587e+17**.

### NEDEN BÖYLE
Alternatif: *`material.porosity.alpha0 >= max(pile.alpha0)` diye doğrula ve
hata ver.* Reddedildi — heterojen gözeneklilik **fiziksel olarak doğru**;
onu yasaklamak modeli kısıtlar. Doğru olan tavanı parçacık başına yapmaktı.

---

## K13 — Blok kesri kütle olarak ölçülüyordu

**Dosya:** `src/dartrift/validation/scene_checks.py`

### ÖNCE
```python
f_meas = float(np.sum(boul.m[boul.is_boulder]) / np.sum(boul.m))   # KUTLE
...
"boulder_fraction_target": 0.30,                                    # HACIM
"boulder_fraction_rel_err": abs(f_meas - 0.30) / 0.30,
```

### SONRA
```python
f_meas = float(boul.boulder_volume_fraction)                        # HACIM
f_mass = float(np.sum(boul.m[boul.is_boulder]) / np.sum(boul.m))    # ayri ad
...
"boulder_mass_fraction": f_mass,
"boulder_mass_over_volume_fraction": f_mass / max(f_meas, 1e-300),
```

### YENİDEN ÜRET
```python
p = build_rubble_pile(icosphere(4, 80.0), spacing=7.0, bulk_density=1800.0,
                      rho0_solid=2700.0, root_seed=17, model_class="M1",
                      f_boulder=0.30, q=3.0, r_min=14.0, r_max=42.0)
f_h = p.boulder_volume_fraction
f_m = float(np.sum(p.m[p.is_boulder]) / np.sum(p.m))
r   = float(p.m[p.is_boulder][0] / p.m[~p.is_boulder][0])
print(f_h, f_m, r, f_h*r/(f_h*r + 1 - f_h))     # kapali form dogrulamasi
```
**Ölçülen:** `0.3034  0.4335  1.7565  0.433483` — kapalı form **6 hane** tutuyor.

---

## K15 — İç bölge ölçülen büyüklükle seçiliyordu

**Dosya:** `src/dartrift/validation/scene_checks.py`

### ÖNCE
```python
"coordination_interior_mean": float(np.mean(cn[cn >= np.median(cn)])),
```

### SONRA
```python
r_dis = float(np.max(np.linalg.norm(plain.x, axis=1)))
ic_maske = np.linalg.norm(plain.x, axis=1) < r_dis - 2.5 * spacing
if not np.any(ic_maske):
    raise ValueError("ic bolge bos: ... daha ince aralik gerekir")
...
"coordination_interior_mean": float(np.mean(cn[ic_maske])),
"coordination_interior_n": int(np.count_nonzero(ic_maske)),
"coordination_selfselected_mean": float(np.mean(cn[cn >= np.median(cn)])),
```

### YENİDEN ÜRET — kafesi kademeli boz
```python
from dartrift.setup.rubble_generator import fill_particles, coordination_number
from dartrift.setup.shape_mesh import icosphere
mesh, s = icosphere(4, 100.0), 10.0
x = fill_particles(mesh, spacing=s); rng = np.random.default_rng(0)
for kesir in (0.0, 0.25, 0.50, 0.75):
    xx = x.copy()
    if kesir:
        k = rng.random(len(xx)) < kesir
        xx[k] += rng.normal(scale=0.35*s, size=(int(k.sum()), 3))
    cn = coordination_number(xx, s)
    kendi = np.mean(cn[cn >= np.median(cn)])
    ic = np.linalg.norm(xx, axis=1) < 100.0 - 2.5*s
    print(kesir, round(kendi,2), round(np.mean(cn[ic]),2))
```
**Ölçülen:** `0.0 → 12.00/12.00` · `0.25 → 11.19/10.25` · `0.50 → 9.73/9.05`
· `0.75 → 9.35/8.45`

Kapının bandı `[11,0 ; 12,01]` → **%25 bozuk kafes geçiyordu**.

---

## K17 — Kenar-manifold ters sarımı göremiyordu

**Dosya:** `src/dartrift/setup/shape_mesh.py`

### MEVCUT (değişmedi — doğru ama yetersiz)
```python
def is_edge_manifold(self) -> bool:
    e = np.concatenate([self.f[:,[0,1]], self.f[:,[1,2]], self.f[:,[2,0]]])
    e = np.sort(e, axis=1)                 # (a,b) ile (b,a) AYNI sayilir
    _, counts = np.unique(e, axis=0, return_counts=True)
    return bool(np.all(counts == 2))
```

### EKLENEN
```python
def is_consistently_oriented(self) -> bool:
    e = np.concatenate([self.f[:,[0,1]], self.f[:,[1,2]], self.f[:,[2,0]]])
    _, counts = np.unique(e, axis=0, return_counts=True)   # SIRALAMA YOK
    return bool(np.all(counts == 1))
```

### YENİDEN ÜRET
```python
m = icosphere(3, 100.0); rng = np.random.default_rng(0); V0 = m.volume
for k in (1, 5, 20, 100):
    f = m.f.copy(); idx = rng.choice(len(f), size=k, replace=False)
    f[idx] = f[idx][:, ::-1]
    mm = TriMesh(v=m.v, f=f)
    print(k, mm.is_edge_manifold(), mm.is_consistently_oriented(),
          round(100*abs(mm.volume/V0 - 1), 3))
```
**Ölçülen:** `1 True False 0.109` · `5 True False 0.764` · `20 True False 3.112`
· `100 True False 15.545`

### İki kontrolün bağımsızlığı (ölçüldü)
| bozulma | `is_edge_manifold()` | `is_consistently_oriented()` |
|---|---|---|
| delik (bir yüz silinmiş) | **False** | True |
| ters sarım | True | **False** |

### NEDEN BÖYLE
Alternatif: *yüz başına sarımı otomatik onar (BFS ile yayarak).* Reddedildi —
projenin kuralı "sessizce onarma, açıkça reddet". Onarım ayrı bir karardır ve
girdinin gerçekten bozuk olduğunu gizler.

---

## K18 — Krater ölçütü yanlılık ile sinyali karıştırıyordu

**Dosya:** `src/dartrift/validation/scene_checks.py`

### ÖNCE
```python
"crater_separates_global": bool(abs(cs.global_radius_change) < 5.0),
```

### SONRA
```python
cs_ref    = crater_profile(x_t, **_ort)              # DEFORMASYONSUZ taban
cs_shrink = crater_profile(0.9 * x_t, **_ort)        # POZITIF kontrol
global_bias   = float(cs_ref.global_radius_change)
global_excess = float(cs.global_radius_change) - global_bias
shrink_excess = float(cs_shrink.global_radius_change) - global_bias
...
"crater_global_bias": global_bias,
"crater_global_excess": global_excess,
"crater_separates_global": bool(abs(global_excess) < 0.5),
"crater_detects_real_shrink": bool(shrink_excess < -5.0),
```

### YENİDEN ÜRET
```python
rng = np.random.default_rng(23); n_t = 40000
p = rng.normal(size=(n_t,3)); p /= np.linalg.norm(p,axis=1)[:,None]
x0 = p * (80.0*rng.uniform(0,1,n_t)**(1/3))[:,None]
ort = dict(center=np.zeros(3), impact_direction=np.array([0.,0.,-1.]),
           reference_radius=80.0, outer_angle_deg=60.0, n_bins=12)
print("deformasyonsuz:", crater_profile(x0, **ort).global_radius_change)   # -1.5335
print("%10 buzusme   :", crater_profile(0.9*x0, **ort).global_radius_change) # -9.3802
```

---

## K20 — G1 C7 bir özdeşliği sınıyordu

**Dosya:** `scripts/run_g1_gate.py`

### ÖNCE
```python
ts_ok = all(
    m["timestep_summary"]["n_steps"] > 0
    and abs(m["timestep_summary"]["binding_cfl_viscous_pct"]
            + m["timestep_summary"]["binding_acceleration_pct"] - 100.0) < 1e-9
    for m in ...)
```

Üreten kod (`warp_core/timestep.py`):
```python
"binding_cfl_viscous_pct":  100.0 * n_cfl / n,
"binding_acceleration_pct": 100.0 * (n - n_cfl) / n,     # toplam == 100, HEP
```

### SONRA
```python
def _ts_gecerli(m) -> tuple[bool, str]:
    t = m.get("timestep_summary", {})
    gereken = ("n_steps", "binding_cfl_viscous_pct", "binding_acceleration_pct",
               "mean_pct_particles_cfl", "dt_min", "dt_max")
    eksik = [k for k in gereken if k not in t]
    if eksik:                     return False, f"eksik alan {eksik}"
    if t["n_steps"] <= 0:         return False, "n_steps <= 0"
    for k in ("binding_cfl_viscous_pct", "binding_acceleration_pct",
              "mean_pct_particles_cfl"):
        if not (0.0 <= t[k] <= 100.0):
            return False, f"{k}={t[k]} [0,100] disinda"
    if not (0.0 < t["dt_min"] <= t["dt_max"] < float("inf")):
        return False, f"dt araligi bozuk: [{t['dt_min']}, {t['dt_max']}]"
    if t["dt_max"] <= t["dt_min"]:
        return False, "dt sabit — kisit logu bilgi tasimiyor"
    return True, ""
```

### NEDEN BÖYLE
Alternatif: *özdeşliği tut, yanına başka şart ekle.* Reddedildi — özdeşlik
**yapısal** bir doğrulamadır ve kanıt olarak sayılmamalıdır (ADR-0040). Onu
kriterin içinde bırakmak, listeyi uzatıp gücünü artırmıyor gibi gösterir.

---

## B1 — `dt` çapraz kontrolü

**Dosya:** `tests/test_solid_cross.py`

### EKLENEN
```python
@needs_warp
class TestTimestepCross:
    @staticmethod
    def _durumlar():
        x, v, m, h, mat, num, pp = _full_physics_setup()
        return [("h/2, cfl=0.2",  0.5*h, 0.2),
                ("h,   cfl=0.2",  1.0*h, 0.2),
                ("2h,  cfl=0.2",  2.0*h, 0.2),
                ("h,   cfl=0.05", 1.0*h, 0.05)], (x, v, m, mat, num, pp)

    def _dogrula(self, satir):
        for ad, c, g in satir:
            assert g == pytest.approx(c, rel=1e-12)
        dts = [c for _, c, _ in satir]
        assert max(dts)/min(dts) > 1.5      # BOSLUK KONTROLU
```

### S3 — bu testin ilk hâli yanlış varsayıyordu
İlk sürüm `dt`'yi **hız** ile oynatmaya çalışıyordu:
```
hiz carpani   0,05      1        1        5
dt          5,320e-06 5,402e-06 5,402e-06 5,421e-06     yayilim %1,9
```
CFL kısıtı **ses hızına** bağlı (~5000 m/s); parçacık hızları (1,5–150 m/s)
onun yanında ihmal edilebilir. `dt_cfl = cfl·h/visc` — sınav `h` ve `cfl` ile
kuruldu.

---

## Ölçüm betiklerinin yeri

TRUBA `/arf/scratch/egitimg16/driftclaude/`:

| betik | ne ölçer | iş no |
|---|---|---|
| `dbg_damage.py` | K1 kusurlu hâli | 1446269 |
| `dbg_damage2.py` | K1 düzeltilmiş hâli | 1446277+ |
| `dbg_y0.py` | S1 — plastik iş ↔ Y0 (3 kol) | 1448928 |
| `dbg_settle.py` | K10 — settling yakınsaması | 1449843 |
| `dbg_alpha.py` | K10 — karşı-kontrollü α ezilmesi | 1449888 |

Hepsi tek başına çalışır ve SLURM sarmalayıcısı `*_job.sh` dosyalarındadır.
Warp sağlık kontrolü (`exit 75` = düğüm arızası, sonuç değil) her birinde var.
