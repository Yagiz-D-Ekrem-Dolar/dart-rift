"""Çıkarım hattının **uçtan uca** sınavı — FAZ 4.6'nın istatistik çekirdeği.

## Mevcut testlerden farkı: **döngüsel değil**

`test_inference.py`'nin posterior testleri veriyi **vekilin kendisinden**
üretiyor (`veri = s.predict(gercek)`). Bu, posterior matematiğini sınar
ama gerçek durumu **sınamaz**: gerçekte veri **simülatörden** gelir ve
vekil onu yalnızca **yaklaşık** temsil eder.

Buradaki testler veriyi vekilin **öğrenemeyeceği** bir modelden üretiyor
(kübik + eşik terimleri). Sorulan şey:

> Vekil hatası varken hat **hâlâ** gerçeği buluyor mu, yoksa emin bir
> şekilde **yanlış** mı oluyor?

İkincisi çok daha tehlikeli: dar ama yanlış bir posterior, G4-C'nin
`C1`'ini düşürür — ama ancak `C1` **ölçülüyorsa**.

## `ensemble_kos` de burada sınanıyor

Sürücü şimdiye kadar yalnızca **kuru kip**te koştu. Analitik ileri
modelle gerçek bir uçtan uca koşu, sürdürülebilirliği (resume) ve
düşen nokta davranışını GPU harcamadan sınar.
"""
from __future__ import annotations

import numpy as np
import pytest

from dartrift.inference.design import DART_UZAYI, factorial_design, lhs_design
from dartrift.inference.ensemble import ensemble_kos, oku_tamamlananlar
from dartrift.inference.posterior import grid_posterior
from dartrift.inference.recovery import recovery_verdict
from dartrift.inference.surrogate import fit_surrogate

GERCEK = np.array([1.5, 1.0e5, 0.25])


def _gercek_model(x, dogrusalsizlik: float = 0.0):
    """**Simülatör yerine geçen** analitik model — üç gözlenebilir.

    `dogrusalsizlik = 0` iken tam ikinci derece, yani vekil onu **tam**
    öğrenebilir. Büyüdükçe kübik ve `tanh` terimleri giriyor ve vekil
    artık yaklaşık kalıyor — gerçek durum budur.
    """
    u = DART_UZAYI.to_unit(np.atleast_2d(x))
    a, b, c = u[:, 0], u[:, 1], u[:, 2]
    beta = 1.2 + 0.9 * a - 0.4 * b + 0.6 * c + 0.3 * a * c - 0.2 * b * b
    krater = 2.0 + 3.0 * a - 1.0 * b + 0.5 * c
    ejekta = 1.0 + 0.8 * c + 0.3 * a * b
    if dogrusalsizlik:
        k = float(dogrusalsizlik)
        beta = beta + k * (a ** 3 - 0.5 * np.tanh(6.0 * (c - 0.5)))
        krater = krater + k * 2.0 * np.tanh(5.0 * (a - 0.4))
        ejekta = ejekta + k * (c ** 3)
    return np.column_stack([beta, krater, ejekta])


def _hat(dogrusalsizlik=0.0, n_lhs=70, sigma=0.02, seed=99, tarama=True):
    """Tasarım → ileri model → vekil → posterior → G4-C."""
    tasarim = np.vstack([factorial_design(DART_UZAYI, 3),
                         lhs_design(DART_UZAYI, n_lhs, root_seed=seed)])
    Y = _gercek_model(tasarim, dogrusalsizlik)
    vek = [fit_surrogate(DART_UZAYI, tasarim, Y[:, k]) for k in range(3)]
    # VERI GERCEK MODELDEN, vekilden DEGIL -- dongusellik burada kirilir.
    veri = list(_gercek_model(GERCEK[None, :], dogrusalsizlik)[0])
    post = grid_posterior(DART_UZAYI, vek, veri, sigma=sigma, n_grid=44)
    tar = None
    if tarama:
        tar = [(c, grid_posterior(DART_UZAYI, vek, veri, sigma=sigma * c,
                                  n_grid=44)) for c in (1.0, 4.0, 16.0)]
    return vek, post, recovery_verdict(post, GERCEK, tar)


# ------------------------------------------------- tam ikinci derece hal

def test_uctan_uca_ikinci_derecede_GERCEGI_buluyor():
    """Vekil modeli tam öğrenebiliyorsa hat gerçeği bulmalı."""
    vek, post, v = _hat(dogrusalsizlik=0.0)
    assert all(s.guvenilir for s in vek), [s.q2 for s in vek]
    assert all(s.q2 > 0.999 for s in vek), [s.q2 for s in vek]
    for j, ad in enumerate(DART_UZAYI.names):
        assert post.contains(j, GERCEK[j]), (ad, post.hdi(j))
    assert v.c1_gecti, v.c1_ayrinti


# ------------------------------------ VEKIL HATASI VARKEN (gercek durum)

@pytest.mark.parametrize("k", [0.05, 0.15, 0.30])
def test_vekil_hatasi_varken_EMIN_ama_YANLIS_olmuyor(k):
    """Asıl risk: dar **ama yanlış** posterior.

    Vekil kusurluyken hattın iki kabul edilebilir davranışı var:
    ya gerçeği hâlâ kapsar, ya da kapsamadığını **`C1` ile söyler**.
    Kabul edilemez olan, `C1`'in kusuru **görmemesi**.
    """
    vek, post, v = _hat(dogrusalsizlik=k)
    kapsiyor = all(post.contains(j, GERCEK[j]) for j in range(3))
    # C1, "gercek posteriorun icinde mi" sorusunun ta kendisi olmali.
    assert v.c1_gecti == kapsiyor, (k, v.c1_ayrinti, [post.hdi(j)
                                                     for j in range(3)])


def test_dogrusalsizlik_ARTINCA_q2_DUSUYOR():
    """Vekil yeterliliği kusuru **görmeli** — sessiz kalmamalı."""
    q = []
    for k in (0.0, 0.15, 0.5):
        vek, _, _ = _hat(dogrusalsizlik=k, tarama=False)
        q.append(min(s.q2 for s in vek))
    assert all(b <= a + 1e-9 for a, b in zip(q, q[1:], strict=False)), q
    assert q[0] > 0.999 and q[-1] < q[0]


#: `q2 > 0,5` eşiğini gerçekten düşüren tepki yüzeyleri — **ölçüldü**,
#: tahmin edilmedi (aşağıdaki tabloya bakın).
_SALINIMLI = 4.0 * np.pi


def test_asiri_dogrusalsizlikta_vekil_GUVENILMEZ_diyor():
    """`q2 ≤ 0,5`'te hat *"bu vekille çıkarım yapma"* demeli.

    İlk sürümde `dogrusalsizlik = 3.0` yeter sandım; **yetmedi**
    (`q2 = 0,944…0,996`). Hangi biçimin gerçekten düşürdüğü ölçüldü:

    | tepki yüzeyi | `q2` | `guvenilir` |
    |---|---|---|
    | `a³` | 0,9944 | ✔ |
    | `tanh(6(c−½))` | 0,9116 | ✔ |
    | `3(a³ − ½tanh(6(c−½)))` | 0,9437 | ✔ |
    | basamak `a > ½` | 0,6706 | ✔ |
    | `1/(0,05+a)` | 0,7812 | ✔ |
    | `\\|a−½\\|^¼` | 0,5254 | ✔ |
    | **`sin(4πa)`** | **−0,0262** | **✘** |
    | **`sin(8πa)`** | **−0,0850** | **✘** |
    """
    tasarim = np.vstack([factorial_design(DART_UZAYI, 3),
                         lhs_design(DART_UZAYI, 70, root_seed=99)])
    u = DART_UZAYI.to_unit(tasarim)
    y = 1.0 + np.sin(_SALINIMLI * u[:, 0])
    s = fit_surrogate(DART_UZAYI, tasarim, y)
    assert not s.guvenilir and s.q2 < 0.5, s.q2


def test_q2_esigi_ZAYIF_bir_koruma_bu_yazili_olsun():
    """`q2 > 0,5` **düşük bir çıta** — kapı ona yaslanmamalı.

    Yukarıdaki ölçüm gösteriyor ki basamak fonksiyonu, `1/x` ve kübik
    bile eşiği **geçiyor**. Yani `guvenilir` yalnızca **salınımlı** bir
    tepki yüzeyinde uyarı verir; `β(θ)` fizik gereği salınımlı olmadığı
    için pratikte **neredeyse her zaman** geçecek.

    Test bunu bir kusur diye değil, **belgelenmiş sınır** diye tutuyor:
    G4-C bu bayrağa tek başına güvenmemeli.
    """
    tasarim = np.vstack([factorial_design(DART_UZAYI, 3),
                         lhs_design(DART_UZAYI, 70, root_seed=99)])
    u = DART_UZAYI.to_unit(tasarim)
    for ad, y in (("basamak", (u[:, 0] > 0.5).astype(float)),
                  ("1/x", 1.0 / (0.05 + u[:, 0])),
                  ("kubik", u[:, 0] ** 3)):
        s = fit_surrogate(DART_UZAYI, tasarim, 1.0 + y)
        assert s.guvenilir, (ad, s.q2)      # <-- HEPSI GECIYOR


# ------------------------------------------------------- gurultu tepkisi

def test_gurultu_taramasi_uctan_uca_C3_u_gecirıyor():
    """`C3`: gürültü artınca bant genişlemeli — gerçek veriyle de."""
    _, _, v = _hat(dogrusalsizlik=0.05)
    assert v.c3_gecti, v.c3_ayrinti


# --------------------------------------------- ensemble surucusu (gercek)

def test_ensemble_kos_uctan_uca_ve_SURDURULEBILIR(tmp_path):
    """Sürücü şimdiye kadar yalnızca kuru kipte koştu."""
    yol = tmp_path / "ens.jsonl"
    tasarim = lhs_design(DART_UZAYI, 12, root_seed=5)
    cagri = {"n": 0}

    def ileri(th):
        cagri["n"] += 1
        return _gercek_model(th[None, :])[0]

    d1 = ensemble_kos(tasarim, ileri, yol, root_seed=5)
    assert d1.tamamlanan == 12 and d1.dusen == 0 and d1.atlanan == 0
    assert cagri["n"] == 12

    # IKINCI kosu: hicbir sey yeniden hesaplanmamali.
    d2 = ensemble_kos(tasarim, ileri, yol, root_seed=5)
    assert d2.atlanan == 12 and cagri["n"] == 12, "yeniden hesapladi"

    tamam, bozuk = oku_tamamlananlar(yol, root_seed=5)
    assert bozuk == 0 and len(tamam) == 12
    # Okunan degerler ileri modelin verdikleriyle BIREBIR ayni olmali.
    for i, th in enumerate(tasarim):
        np.testing.assert_allclose(tamam[i], _gercek_model(th[None, :])[0],
                                   rtol=1e-12)


def test_ensemble_dusen_nokta_VARSAYILAN_olarak_tekrar_denenmiyor(tmp_path):
    yol = tmp_path / "ens2.jsonl"
    tasarim = lhs_design(DART_UZAYI, 6, root_seed=3)
    dusenler = {2, 4}

    def ileri(th):
        i = int(np.argmin(np.linalg.norm(tasarim - th[None, :], axis=1)))
        if i in dusenler:
            raise RuntimeError(f"yapay hata {i}")
        return _gercek_model(th[None, :])[0]

    d1 = ensemble_kos(tasarim, ileri, yol, root_seed=3)
    assert d1.dusen == 2 and d1.tamamlanan == 4

    sayac = {"n": 0}

    def ileri2(th):
        sayac["n"] += 1
        return _gercek_model(th[None, :])[0]

    d2 = ensemble_kos(tasarim, ileri2, yol, root_seed=3)
    assert sayac["n"] == 0, "dusen nokta izinsiz yeniden denendi"
    assert d2.atlanan == 6

    # Ama ACIKCA istenirse denenmeli.
    d3 = ensemble_kos(tasarim, ileri2, yol, root_seed=3,
                      yeniden_dene_dusenleri=True)
    assert sayac["n"] == 2 and d3.tamamlanan == 6


def test_ensemble_tasarimdan_vekile_KESINTIDEN_SONRA_ayni(tmp_path):
    """Kesintili koşu, kesintisiz koşuyla **aynı** vekili vermeli."""
    tasarim = np.vstack([factorial_design(DART_UZAYI, 3),
                         lhs_design(DART_UZAYI, 20, root_seed=8)])

    def ileri(th):
        return _gercek_model(th[None, :])[0]

    tam = tmp_path / "tam.jsonl"
    ensemble_kos(tasarim, ileri, tam, root_seed=8)

    # KESINTILI: once yarisi, sonra kalani.
    yarim = tmp_path / "yarim.jsonl"
    n = len(tasarim)

    def ileri_kesintili(th):
        i = int(np.argmin(np.linalg.norm(tasarim - th[None, :], axis=1)))
        if i >= n // 2:
            raise RuntimeError("kesinti")
        return _gercek_model(th[None, :])[0]

    ensemble_kos(tasarim, ileri_kesintili, yarim, root_seed=8)
    ensemble_kos(tasarim, ileri, yarim, root_seed=8,
                 yeniden_dene_dusenleri=True)

    a, _ = oku_tamamlananlar(tam, root_seed=8)
    b, _ = oku_tamamlananlar(yarim, root_seed=8)
    assert set(a) == set(b)
    for i in a:
        np.testing.assert_array_equal(a[i], b[i])

    def _vek(t):
        Y = np.array([t[i] for i in range(len(tasarim))])
        return [fit_surrogate(DART_UZAYI, tasarim, Y[:, k]) for k in range(3)]

    for s1, s2 in zip(_vek(a), _vek(b), strict=False):
        np.testing.assert_array_equal(s1.coef, s2.coef)
        assert s1.q2 == s2.q2


# ------------------------------------- posterior: SESSIZ NaN'a karsi

class _Bozuk:
    """Izgarada `nan` üreten vekil — gerçekte bozuk bir ileri modelden gelir."""

    def __init__(self, nerede="hepsi"):
        self.sigma, self._nerede = 0.1, nerede

    def predict(self, x):
        y = np.ones(len(np.atleast_2d(x)))
        if self._nerede == "hepsi":
            return y * np.nan
        y[0] = np.nan                     # TEK bir nokta bile yeter
        return y


def test_posterior_NaN_tahminde_ACIKCA_patliyor():
    """Tek bir `nan`, bütün `logp`'yi `nan` yapar ve posterior sessizce
    çöker: `contains()` her yerde `False`, G4-C *"C1 düştü"* der —
    **doğru sonuç, tamamen yanıltıcı sebep**."""
    vek, _, _ = _hat(dogrusalsizlik=0.0, tarama=False)
    veri = list(_gercek_model(GERCEK[None, :])[0])
    for nerede in ("hepsi", "tek"):
        with pytest.raises(ValueError, match="sonlu olmayan tahmin"):
            grid_posterior(DART_UZAYI, [_Bozuk(nerede), vek[1], vek[2]],
                           veri, sigma=0.02, n_grid=16)


def test_posterior_NaN_VERIDE_de_reddediliyor():
    vek, _, _ = _hat(dogrusalsizlik=0.0, tarama=False)
    with pytest.raises(ValueError, match="veri içinde sonlu olmayan"):
        grid_posterior(DART_UZAYI, vek, [1.0, np.nan, 2.0], sigma=0.02,
                       n_grid=16)


def test_posterior_gecersiz_vekil_sigmasi_reddediliyor():
    vek, _, _ = _hat(dogrusalsizlik=0.0, tarama=False)
    veri = list(_gercek_model(GERCEK[None, :])[0])

    class _KotuSigma:
        sigma = float("nan")

        def predict(self, x):
            return np.ones(len(np.atleast_2d(x)))

    with pytest.raises(ValueError, match="`sigma`sı geçersiz"):
        grid_posterior(DART_UZAYI, [_KotuSigma(), vek[1], vek[2]], veri,
                       sigma=0.02, n_grid=16)


def test_SAGLAM_vekiller_hala_calisiyor():
    """Korumalar meşru yolu bozmamalı."""
    vek, post, _ = _hat(dogrusalsizlik=0.0, tarama=False)
    assert np.all(np.isfinite(post.p))
    assert post.p.sum() == pytest.approx(1.0, rel=1e-12)


# ------------------------- ADR-0044: uzay tutarsizligi ve Secenek 3

def test_VARSAYILAN_uzayin_KUTUSU_rho_yiginla_TUTARSIZ():
    """ADR-0044 §1 — ölçüm, iddianın kendisi.

    `ρ_yığın` sabitken `matrix_alpha0`, `f_boulder`'ın fonksiyonudur.
    Tasarım kutusu ikisini bağımsız ilan ediyor, yani kutunun neredeyse
    tamamı **uygulanamaz**.
    """
    from dartrift.setup.rubble_generator import matrix_alpha0_for_bulk_density as g
    rng = np.random.default_rng(0)
    n = 4000
    a0 = rng.uniform(DART_UZAYI.lo[0], DART_UZAYI.hi[0], n)
    fb = rng.uniform(DART_UZAYI.lo[2], DART_UZAYI.hi[2], n)
    tutarli = np.array([g(1800.0, 2700.0, 1.05, float(f)) for f in fb])
    sapma = np.abs(a0 - tutarli) / tutarli
    assert np.mean(sapma < 1e-9) == 0.0            # TAM uyum: hicbiri
    assert np.mean(sapma < 0.10) < 0.35            # %10 tolerans bile az


def test_SECENEK3_kutusunun_TAMAMI_uygulanabilir():
    """ADR-0044 §6 madde 1 — ölçüldü, `0/36` yasak."""
    from dartrift.inference.design import DART_UZAYI_S3
    from dartrift.setup.rubble_generator import matrix_alpha0_for_bulk_density as g
    for b in np.linspace(DART_UZAYI_S3.lo[0], DART_UZAYI_S3.hi[0], 6):
        for f in np.linspace(DART_UZAYI_S3.lo[2], DART_UZAYI_S3.hi[2], 6):
            a = g(1800.0, 2700.0, float(b), float(f))
            assert np.isfinite(a) and a >= 1.0, (b, f, a)


def test_SECENEK3_eslemesi_matrix_alpha0_VERMIYOR():
    """Türetilmesi gereken şeyi elle vermek çatışmayı geri getirirdi."""
    from dartrift.inference.forward import sahne_parametreleri
    taban = {"bulk_density": 1800.0, "matrix_alpha0": 1.5}
    kw = sahne_parametreleri(np.array([1.05, 3.0e5, 0.30]), taban,
                             secenek3=True)
    assert "matrix_alpha0" not in kw          # <-- uretici turetecek
    assert kw["boulder_alpha0"] == 1.05
    assert kw["f_boulder"] == 0.30
    # ADR-0044 KABUL EDILDI: varsayilan artik Secenek 3.
    kvar = sahne_parametreleri(np.array([1.05, 3.0e5, 0.30]), taban)
    assert "matrix_alpha0" not in kvar and kvar["boulder_alpha0"] == 1.05
    # Eski yol SILINMEDI (karar geri alinabilsin).
    kes = sahne_parametreleri(np.array([1.5, 3.0e5, 0.30]), taban,
                              secenek3=False)
    assert kes["matrix_alpha0"] == 1.5 and "boulder_alpha0" not in kes


def test_SECENEK3_ile_yigin_GERCEKTEN_kuruluyor():
    """Asıl sınav: varsayılanın **düştüğü** yerde Seçenek 3 kuruyor mu."""
    from dartrift.inference.forward import sahne_parametreleri
    from dartrift.setup.scene import build_scene
    taban = dict(radius=82.0, bulk_density=1800.0, root_seed=20260801,
                 model_class="M1", q=3.0, n_impactor=800,
                 r_min=14.0, r_max=42.0)
    th = np.array([1.05, 3.0e5, 0.30])

    # ESKI esleme (ADR-0044 oncesi): rho_yigin catismasi -> ValueError
    with pytest.raises(ValueError, match="sapiyor"):
        build_scene(spacing=14.0, device="cpu",
                    **sahne_parametreleri(np.array([1.55, 3.0e5, 0.30]),
                                          taban, secenek3=False))

    # Secenek 3: KURULUYOR ve yogunluk hedefi tutuyor.
    sahne = build_scene(spacing=14.0, device="cpu",
                        **sahne_parametreleri(th, taban))   # varsayilan
    assert sahne.n > 0
    rho = sahne.target_mass / sahne.mesh_volume
    assert abs(rho - 1800.0) / 1800.0 < 0.05, rho
