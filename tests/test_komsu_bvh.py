"""A52 — destek kutulu BVH + sıralı CSR komşu listesi.

Kilitlenen dört şey:

1. **Eksiksiz**: her gerçek komşu (`r < h_i + h_j`) listede; liste
   üst küme olabilir ama `1 + 1e-9` payından fazlası değil.
2. **Kanonik sıra**: satırlar artan kimlik, tekrarsız, kendisi dahil.
3. **Aynı fizik**: `bvh` ile `hash` çözücüsü yalnız toplama sırası kadar
   (yuvarlama düzeyinde) ayrışır — gövdeler birebir kopya olduğu için
   bir sapma, kopyalardan birinin bozulduğu anlamına gelir.
4. **Önbellek**: adımın ikinci değerlendirmesi listeyi YENİDEN KURMAZ.
"""
from __future__ import annotations

import dataclasses

import numpy as np
import pytest

from dartrift.particles import warp_available, warp_devices

pytestmark = pytest.mark.skipif(not warp_available(), reason="warp yok")


def _bulut(n: int = 3000, tohum: int = 0):
    """Merdiven benzeri: merkezden dışa `h` dört kat büyüyor."""
    rng = np.random.default_rng(tohum)
    x = rng.uniform(-10.0, 10.0, (n, 3))
    r = np.linalg.norm(x, axis=1)
    h = np.where(r < 3, 0.35, np.where(r < 6, 0.7, np.where(r < 9, 1.4, 2.8)))
    return x, h


def _csr(x, h, device="cpu"):
    import warp as wp

    from dartrift.warp_core.komsu_bvh import BvhKomsu

    xw = wp.array(np.ascontiguousarray(x), dtype=wp.vec3d, device=device)
    hw = wp.array(np.ascontiguousarray(h), dtype=wp.float64, device=device)
    k = BvhKomsu(len(x), device)
    k.kur(xw, hw, 0)
    return k.bas.numpy(), k.nbr.numpy()[:k.toplam], k


def test_csr_gercek_komsulari_EKSIKSIZ_iceriyor():
    x, h = _bulut()
    bas, nbr, _ = _csr(x, h)
    for i in range(0, len(x), 13):
        d = np.linalg.norm(x - x[i], axis=1)
        satir = set(nbr[bas[i]:bas[i + 1]].tolist())
        gercek = set(np.flatnonzero(d < h + h[i]).tolist())
        assert gercek <= satir, f"eksik komsu: {sorted(gercek - satir)[:5]}"
        ust = set(np.flatnonzero(d < (h + h[i]) * (1.0 + 1e-9)).tolist())
        assert satir <= ust, "liste destek disindan fazla aday tasiyor"


def test_satirlar_SIRALI_tekrarsiz_ve_kendini_iceriyor():
    x, h = _bulut(1500, 1)
    bas, nbr, _ = _csr(x, h)
    for i in range(len(x)):
        s = nbr[bas[i]:bas[i + 1]]
        assert np.all(np.diff(s) > 0), f"satir {i} sirali/tekrarsiz degil"
        assert i in s


def _merdiven_kafesi():
    """Gerçek merdiven gibi: `s` içeri doğru yarıya iner, `h = 2 s`.

    İlk sürüm düzgün YOĞUNLUKTA rastgele bulut kullandı ve BVH/hash aday
    oranı yalnız `1,9` çıktı (test düştü). Sebep ölçüldü: aday patlaması
    `h` değişiminden değil, İNCE parçacıkların hem küçük `h`'li hem SIK
    olmasından geliyor -- `2 h_max` yarıçaplı küre binlerce ince
    parçacık yakalıyor. Merdivenin kendisi bu eşleşmeyi taşıyor.
    """
    from dartrift.setup.rubble_generator import lattice_points

    parca, hh = [], []
    for r_ic, r_dis, s in ((0.0, 3.0, 0.35), (3.0, 6.0, 0.7), (6.0, 12.0, 1.4)):
        p = lattice_points(np.full(3, -r_dis), np.full(3, r_dis), s, "fcc")
        r = np.linalg.norm(p, axis=1)
        p = p[(r >= r_ic) & (r < r_dis)]
        parca.append(p)
        hh.append(np.full(len(p), 2.0 * s))
    return np.vstack(parca), np.concatenate(hh)


def test_merdivende_aday_sayisi_hash_izgarasindan_COK_az():
    """Hash `2 h_max` yarıçapıyla arıyor; BVH yalnız kendi desteğiyle.

    Ölçülen (üç seviye, `N ≈ 10 bin`): oran `> 10`. Uzmanın beş seviyeli
    orta kayıttaki ölçümü `81`. Eşik `5` -- yalnız yönü ve mertebeyi
    kilitliyor.
    """
    x, h = _merdiven_kafesi()
    _, _, k = _csr(x, h)
    ort = k.toplam / len(x)
    R = 2.0 * h.max()
    ornek = x[::25]
    d2 = np.sum((ornek[:, None, :] - x[None, :, :]) ** 2, axis=2)
    hash_aday = float(np.mean(np.sum(d2 < R * R, axis=1)))
    assert hash_aday / ort > 5.0, (ort, hash_aday)


@pytest.mark.parametrize("device", ["cpu", "cuda:0"])
def test_bolutlu_ve_ekleme_siralamasi_AYNI_listeyi_veriyor(device):
    """Bölütlü radix sıralama (varsayılan) ile çekirdek içi ekleme
    sıralaması (yedek) birebir aynı CSR'yi vermeli.

    Ölçüldü (RTX 3050, kaba merdiven): ekleme sıralaması `256 ms/adım`
    sürüyordu -- fizik çekirdeklerinin toplamından fazla.
    """
    if device.startswith("cuda") and not any(
            d.startswith("cuda") for d in warp_devices()):
        pytest.skip("CUDA yok")
    import warp as wp

    from dartrift.warp_core.komsu_bvh import BvhKomsu

    x, h = _merdiven_kafesi()
    xw = wp.array(x, dtype=wp.vec3d, device=device)
    hw = wp.array(h, dtype=wp.float64, device=device)
    sonuc = []
    for sir in ("bolutlu", "ekleme"):
        k = BvhKomsu(len(x), device, siralama=sir)
        k.kur(xw, hw, 0)
        assert k.siralama == sir
        sonuc.append((k.bas.numpy().copy(), k.nbr.numpy()[:k.toplam].copy()))
    assert np.array_equal(sonuc[0][0], sonuc[1][0])
    assert np.array_equal(sonuc[0][1], sonuc[1][1])


def test_ayni_surumde_ikinci_kurulum_ATLANIYOR():
    import warp as wp

    from dartrift.warp_core.komsu_bvh import BvhKomsu

    x, h = _bulut(500, 3)
    xw = wp.array(x, dtype=wp.vec3d, device="cpu")
    hw = wp.array(h, dtype=wp.float64, device="cpu")
    k = BvhKomsu(len(x), "cpu")
    assert k.kur(xw, hw, 7) is True
    assert k.kur(xw, hw, 7) is False
    assert k.n_kurulum == 1
    assert k.kur(xw, hw, 8) is True


def test_refit_ve_rebuild_AYNI_listeyi_veriyor():
    """Ağaç yeniden kullanılsa da sıralı CSR ağaçtan bağımsız."""
    import warp as wp

    from dartrift.warp_core.komsu_bvh import BvhKomsu

    x, h = _bulut(800, 4)
    hw = wp.array(h, dtype=wp.float64, device="cpu")
    k = BvhKomsu(len(x), "cpu", yeniden_kurma=1)
    rng = np.random.default_rng(9)
    for s in range(4):
        x = x + rng.normal(0, 0.05, x.shape)
        k.kur(wp.array(x, dtype=wp.vec3d, device="cpu"), hw, s)
        b1, n1 = k.bas.numpy().copy(), k.nbr.numpy()[:k.toplam].copy()
        b2, n2, _ = _csr(x, h)
        assert np.array_equal(b1, b2) and np.array_equal(n1, n2), s


def _solid(komsu, device="cpu", n_adim=10):
    from dartrift.cpu_reference import sph_ref as R
    from dartrift.cpu_reference.materials import (
        GravityParams,
        MaterialParams,
        PorosityParams,
        StrengthParams,
    )
    from dartrift.validation.gravity import _uniform_sphere
    from dartrift.warp_core.solver_solid import WarpSolid3D

    n = 400
    x = _uniform_sphere(n, 1.0, seed=616161)
    v = -30.0 * x
    h0 = 1.3 * (4.0 * np.pi / 3.0 / n) ** (1.0 / 3.0)
    r = np.linalg.norm(x, axis=1)
    h = np.where(r < 0.5, h0, 2.0 * h0)          # iki seviyeli h
    pp = PorosityParams(enabled=True, alpha0=1.3, Pe=1e6, Ps=1e9, n_exp=2.0)
    m = np.full(n, (2700.0 / pp.alpha0) * (4.0 / 3.0) * np.pi / n)
    mat = MaterialParams(
        eos="tillotson", density_method="continuity",
        strength=StrengthParams(enabled=True, Y0=1e6, mu_f=0.8, YM=1.5e9,
                                shear_G=2.27e10),
        porosity=pp,
        gravity=GravityParams(enabled=True, G=6.6743e-4, eps=0.05, mode="direct"))
    sol = WarpSolid3D(x.copy(), v.copy(), m, np.zeros(n), h, mat,
                      R.RefParams(cfl=0.2), alpha0=np.full(n, pp.alpha0),
                      device=device, komsu_arama=komsu)
    for _ in range(n_adim):
        sol.step(5.0e-7)
    return sol


def test_bvh_ve_hash_FIZIGI_yuvarlama_duzeyinde_ayni():
    a = _solid("hash").state_numpy()
    b = _solid("bvh").state_numpy()
    for k in ("x", "v", "u", "rho", "P", "S", "alpha"):
        olcek = np.max(np.abs(a[k])) + 1e-300
        assert np.max(np.abs(a[k] - b[k])) / olcek < 1e-10, k


def test_bvh_cozucu_listeyi_adim_basina_BIR_kez_kuruyor():
    sol = _solid("bvh", n_adim=5)
    t = sol.komsu_tanisi()
    # ilk degerlendirme (surum 0) + 5 adim x 1 kurulum
    assert t["n_kurulum"] == 6, t
    assert t["ortalama_komsu"] > 1.0


def test_bilinmeyen_komsu_arama_REDDEDILIYOR():
    with pytest.raises(ValueError, match="komsu_arama"):
        _solid("kdtree", n_adim=0)


@pytest.mark.gpu
def test_cuda_csr_cpu_ile_BIREBIR():
    if not any(d.startswith("cuda") for d in warp_devices()):
        pytest.skip("CUDA yok")
    x, h = _bulut(3000, 5)
    b1, n1, _ = _csr(x, h, "cpu")
    b2, n2, _ = _csr(x, h, "cuda:0")
    assert np.array_equal(b1, b2) and np.array_equal(n1, n2)


@pytest.mark.gpu
def test_cuda_bvh_cozucusu_TEKRARDA_bit_esit():
    if not any(d.startswith("cuda") for d in warp_devices()):
        pytest.skip("CUDA yok")
    a = _solid("bvh", "cuda:0").state_numpy()
    b = _solid("bvh", "cuda:0").state_numpy()
    for k in ("x", "v", "u", "S"):
        assert np.array_equal(a[k], b[k]), k
    assert dataclasses  # kullanilmayan import uyarisi olmasin
