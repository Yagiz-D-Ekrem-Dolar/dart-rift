"""Çıkarım katmanı — **analitik haritaya karşı** doğrulanıyor (FAZ 4.6).

İleri model pahalı olduğu için çıkarım makinesi önce **bilinen** bir
haritayla sınanır. Makine bozuksa pahalı GPU koşuları boşa gider; bu
yüzden bu testler koşulardan **önce** yazıldı.
"""
from __future__ import annotations

import numpy as np
import pytest

from dartrift.inference.design import DART_UZAYI, ParamSpace, factorial_design, lhs_design
from dartrift.inference.posterior import grid_posterior
from dartrift.inference.recovery import C2_DARALMA, G4C, recovery_verdict
from dartrift.inference.surrogate import design_matrix, fit_surrogate

# --------------------------------------------------------------- tasarim


def test_birim_donusum_TERSINIR() -> None:
    """`from_unit(to_unit(x)) == x` — logaritmik eksende de."""
    x = factorial_design(DART_UZAYI, 3)
    geri = DART_UZAYI.from_unit(DART_UZAYI.to_unit(x))
    assert np.allclose(geri, x, rtol=1e-12, atol=0.0)


def test_logaritmik_eksen_GERCEKTEN_log() -> None:
    """`Y0` dört mertebe tarıyor; doğrusal örnekleme üst mertebeye yığardı."""
    x = factorial_design(DART_UZAYI, 3)
    y0 = np.unique(x[:, 1])
    assert len(y0) == 3
    # Logaritmik ise ORTA nokta geometrik ortalamadir.
    assert y0[1] == pytest.approx(np.sqrt(y0[0] * y0[2]), rel=1e-12)
    # Dogrusal olsaydi aritmetik ortalama olurdu -- ONU DEGIL.
    assert y0[1] != pytest.approx(0.5 * (y0[0] + y0[2]), rel=1e-3)


def test_carpanli_tasarim_KENARLARI_iceriyor() -> None:
    x = factorial_design(DART_UZAYI, 3)
    assert len(x) == 27
    u = DART_UZAYI.to_unit(x)
    assert u.min() == pytest.approx(0.0)
    assert u.max() == pytest.approx(1.0)


def test_lhs_her_eksende_TAM_KAPSAMA() -> None:
    """Latin hiperküp tanımı: her eksende `n` katmanın **her biri** dolu."""
    n = 20
    u = DART_UZAYI.to_unit(lhs_design(DART_UZAYI, n, root_seed=7))
    for j in range(DART_UZAYI.ndim):
        katman = np.floor(u[:, j] * n).astype(int)
        assert len(np.unique(np.clip(katman, 0, n - 1))) == n, j


def test_lhs_DETERMINISTIK() -> None:
    """ADR-0004: aynı tohum aynı tasarım, farklı tohum farklı tasarım."""
    a = lhs_design(DART_UZAYI, 12, root_seed=3)
    b = lhs_design(DART_UZAYI, 12, root_seed=3)
    c = lhs_design(DART_UZAYI, 12, root_seed=4)
    assert np.array_equal(a, b)
    assert not np.array_equal(a, c)


def test_gecersiz_uzay_REDDEDILIYOR() -> None:
    with pytest.raises(ValueError):
        ParamSpace(("a",), (1.0,), (0.5,), (False,))      # hi < lo
    with pytest.raises(ValueError):
        ParamSpace(("a",), (0.0,), (1.0,), (True,))       # log ama lo=0
    with pytest.raises(ValueError):
        ParamSpace(("a", "b"), (0.0,), (1.0,), (False,))  # uzunluk


# --------------------------------------------------------------- vekil

def _harita(x):
    """Bilinen analitik ileri harita — ikinci dereceden **tam** temsil edilir."""
    a, y, f = x[:, 0], np.log10(x[:, 1]), x[:, 2]
    return 3.0 + 1.5 * a - 0.4 * y + 2.0 * f - 0.6 * a * f + 0.05 * y * y


def test_vekil_IKINCI_DERECEYI_tam_ogreniyor() -> None:
    """Boşluk kontrolü: harita polinom uzayındaysa hata makine sıfırı olmalı."""
    x = factorial_design(DART_UZAYI, 4)
    s = fit_surrogate(DART_UZAYI, x, _harita(x))
    assert s.q2 > 1.0 - 1e-8, s.q2
    assert np.allclose(s.predict(x), _harita(x), atol=1e-8)


def test_vekil_YETERSIZSE_q2_dusuyor() -> None:
    """Pozitif kontrol: ölçüt gerçekten düşebiliyor mu?

    Yüksek frekanslı bir harita ikinci dereceyle temsil edilemez.
    `q2` düşmüyorsa ölçüt boş bir doğruyu sınıyordur.
    """
    x = lhs_design(DART_UZAYI, 40, root_seed=1)
    u = DART_UZAYI.to_unit(x)
    y = np.sin(12.0 * u[:, 0]) * np.cos(11.0 * u[:, 2])
    s = fit_surrogate(DART_UZAYI, x, y)
    assert s.q2 < 0.5, s.q2
    assert s.guvenilir is False


def test_LOO_kapali_formu_ELLE_hesapla_ayni() -> None:
    """`e_loo = e/(1−h)` gerçekten `n` kez yeniden çözmekle aynı mı?

    Kapalı form bir **iddiadır**; sayıyla doğrulanıyor.
    """
    x = lhs_design(DART_UZAYI, 24, root_seed=5)
    y = _harita(x) + 0.05 * np.sin(30.0 * x[:, 2])
    s = fit_surrogate(DART_UZAYI, x, y)

    elle = []
    for i in range(len(x)):
        tut = np.ones(len(x), bool)
        tut[i] = False
        si = fit_surrogate(DART_UZAYI, x[tut], y[tut])
        elle.append(y[i] - float(si.predict(x[i:i + 1])[0]))
    ss_elle = float(np.sum(np.square(elle)))
    rmse_elle = np.sqrt(ss_elle / len(x))
    assert s.rmse_loo == pytest.approx(rmse_elle, rel=1e-6)


def test_az_nokta_ile_vekil_REDDEDILIYOR() -> None:
    """`n <= p` iken LOO anlamsızdır: her nokta TAM uyar, hata 0 görünür."""
    x = lhs_design(DART_UZAYI, 8, root_seed=2)
    with pytest.raises(ValueError, match="katsayı öğrenilemez"):
        fit_surrogate(DART_UZAYI, x, _harita(x))


def test_tasarim_matrisi_TERIM_SAYISI() -> None:
    A = design_matrix(np.zeros((5, 3)))
    assert A.shape == (5, 10)          # 1 + 3 + 6


def test_sonlu_olmayan_y_REDDEDILIYOR() -> None:
    x = lhs_design(DART_UZAYI, 20, root_seed=9)
    y = _harita(x)
    y[3] = np.nan
    with pytest.raises(ValueError, match="sonlu olmayan"):
        fit_surrogate(DART_UZAYI, x, y)


# --------------------------------------------------------------- posterior

def _vekiller(seed=11, n=60):
    """Üç gözlenebilir için üç vekil — hepsi aynı analitik aileden."""
    x = np.vstack([factorial_design(DART_UZAYI, 3),
                   lhs_design(DART_UZAYI, n, root_seed=seed)])
    u = DART_UZAYI.to_unit(x)
    yy = [
        _harita(x),                                     # beta benzeri
        2.0 + 3.0 * u[:, 0] - 1.0 * u[:, 1] + 0.5 * u[:, 2],   # krater capi
        1.0 + 0.8 * u[:, 2] + 0.3 * u[:, 0] * u[:, 1],         # ejekta kutlesi
    ]
    return [fit_surrogate(DART_UZAYI, x, y) for y in yy]


def test_posterior_GERCEGI_geri_buluyor() -> None:
    """Uçtan uca boşluk kontrolü: gürültüsüz veri → dar ve doğru posterior."""
    vek = _vekiller()
    gercek = np.array([1.5, 1.0e5, 0.25])
    veri = [float(s.predict(gercek[None, :])[0]) for s in vek]
    post = grid_posterior(DART_UZAYI, vek, veri, sigma=0.02, n_grid=48)
    for j, ad in enumerate(DART_UZAYI.names):
        assert post.contains(j, gercek[j]), (ad, post.hdi(j), gercek[j])


def test_posterior_GURULTU_artinca_GENISLIYOR() -> None:
    """C3'ün çekirdeği: çıkarım veriyi gerçekten kullanıyor mu?"""
    vek = _vekiller()
    gercek = np.array([1.5, 1.0e5, 0.25])
    veri = [float(s.predict(gercek[None, :])[0]) for s in vek]
    gen = []
    for sg in (0.01, 0.05, 0.25, 1.0):
        p = grid_posterior(DART_UZAYI, vek, veri, sigma=sg, n_grid=40)
        gen.append(p.width_u.min())
    assert all(b >= a - 1e-12 for a, b in zip(gen, gen[1:], strict=False)), gen
    assert gen[-1] > 2.0 * gen[0], gen


def test_VEKIL_HATASI_posteriora_giriyor() -> None:
    """Vekil hatası yok sayılırsa posterior **yapay** biçimde daralır."""
    vek = _vekiller()
    gercek = np.array([1.5, 1.0e5, 0.25])
    veri = [float(s.predict(gercek[None, :])[0]) for s in vek]

    class _Gurultusuz:
        def __init__(self, s):
            self._s, self.sigma = s, 0.0

        def predict(self, x):
            return self._s.predict(x)

    class _Gurultulu(_Gurultusuz):
        def __init__(self, s):
            super().__init__(s)
            self.sigma = 0.5

    dar = grid_posterior(DART_UZAYI, [_Gurultusuz(s) for s in vek], veri,
                         sigma=0.02, n_grid=40)
    genis = grid_posterior(DART_UZAYI, [_Gurultulu(s) for s in vek], veri,
                           sigma=0.02, n_grid=40)
    assert genis.width_u.min() > dar.width_u.min()


def test_posterior_gecersiz_girdi_REDDEDILIYOR() -> None:
    vek = _vekiller()
    with pytest.raises(ValueError):
        grid_posterior(DART_UZAYI, vek, [1.0, 2.0], sigma=0.1)     # uzunluk
    with pytest.raises(ValueError):
        grid_posterior(DART_UZAYI, vek, [1.0] * 3, sigma=-1.0)     # negatif
    with pytest.raises(ValueError):
        grid_posterior(DART_UZAYI, [], [], sigma=0.1)              # bos


# --------------------------------------------------------------- G4-C

def _kurtarma(sigma_nominal=0.02, taramali=True):
    vek = _vekiller()
    gercek = np.array([1.5, 1.0e5, 0.25])
    veri = [float(s.predict(gercek[None, :])[0]) for s in vek]
    post = grid_posterior(DART_UZAYI, vek, veri, sigma=sigma_nominal, n_grid=44)
    tarama = None
    if taramali:
        tarama = [(c, grid_posterior(DART_UZAYI, vek, veri,
                                     sigma=sigma_nominal * c, n_grid=44))
                  for c in (1.0, 4.0, 16.0)]
    return recovery_verdict(post, gercek, tarama)


def test_G4C_temiz_durumda_GECIYOR() -> None:
    v = _kurtarma()
    assert v.c1_gecti, v.c1_ayrinti
    assert v.c2_gecti, v.c2_genislikler
    assert v.c3_gecti, v.c3_ayrinti
    assert v.gecti


def test_G4C_tarama_YOKSA_GECEMEZ() -> None:
    """C3 sessizce atlanmaz — koşulmadıysa yargı geçemez."""
    v = _kurtarma(taramali=False)
    assert v.c3_kosuldu is False
    assert v.c3_gecti is False
    assert v.gecti is False
    assert "C3 KOSULMADI" in v.ozet


def test_G4C_C1_yanlis_gercekle_DUSUYOR() -> None:
    """Pozitif kontrol: gerçek değer uzaktaysa C1 **düşmeli**."""
    vek = _vekiller()
    gercek = np.array([1.5, 1.0e5, 0.25])
    veri = [float(s.predict(gercek[None, :])[0]) for s in vek]
    post = grid_posterior(DART_UZAYI, vek, veri, sigma=0.02, n_grid=44)
    yanlis = np.array([1.15, 5.0e6, 0.48])
    v = recovery_verdict(post, yanlis, [(1.0, post), (4.0, post)])
    assert v.c1_gecti is False
    assert v.c1_kapsama < 1.0
    assert v.gecti is False


def test_G4C_C2_bilgisiz_veride_DUSUYOR() -> None:
    """Gürültü çok büyükse posterior önseldir; C2 düşmeli."""
    vek = _vekiller()
    gercek = np.array([1.5, 1.0e5, 0.25])
    veri = [float(s.predict(gercek[None, :])[0]) for s in vek]
    post = grid_posterior(DART_UZAYI, vek, veri, sigma=1.0e4, n_grid=40)
    v = recovery_verdict(post, gercek, [(1.0, post), (4.0, post)])
    assert v.c2_gecti is False
    assert v.c2_en_dar > C2_DARALMA


def test_G4C_C3_tepkisiz_cikarimda_DUSUYOR() -> None:
    """KAYIT-030'un dersi: aynı posterior tekrarlanırsa C3 **düşmeli**."""
    vek = _vekiller()
    gercek = np.array([1.5, 1.0e5, 0.25])
    veri = [float(s.predict(gercek[None, :])[0]) for s in vek]
    post = grid_posterior(DART_UZAYI, vek, veri, sigma=0.02, n_grid=40)
    v = recovery_verdict(post, gercek, [(1.0, post), (4.0, post), (16.0, post)])
    assert v.c3_kosuldu is True
    assert v.c3_gecti is False           # genislemedi
    assert v.c3_ayrinti["toplamda_buyudu"] is False


def test_G4C_tarama_SIRASIZ_ise_patliyor() -> None:
    vek = _vekiller()
    gercek = np.array([1.5, 1.0e5, 0.25])
    veri = [float(s.predict(gercek[None, :])[0]) for s in vek]
    post = grid_posterior(DART_UZAYI, vek, veri, sigma=0.02, n_grid=32)
    with pytest.raises(ValueError, match="ARTAN"):
        recovery_verdict(post, gercek, [(4.0, post), (1.0, post)])


def test_G4C_esikleri_BELGE_ile_tutarli() -> None:
    """Eşikler iki yerde yazılı; ayrışırlarsa test kırılsın (2. turun dersi)."""
    from pathlib import Path

    m = (Path(__file__).resolve().parents[1] / "docs" /
         "G4-OLCUTLERI.md").read_text(encoding="utf-8")
    assert "3/3" in m                       # C1
    assert "%50" in m                       # C2
    assert C2_DARALMA == 0.50
    assert "genişlemeli" in m               # C3


def test_G4C_ozet_UCUNU_de_yaziyor() -> None:
    v = _kurtarma()
    for p in ("C1", "C2", "C3"):
        assert p in v.ozet
    assert isinstance(v, G4C)


def test_onsel_genisligi_BILGISIZ_POSTERIORLA_ayni() -> None:
    """`prior_width` **ölçülen** bilgisiz genişlikle uyuşmalı.

    Bulunan kusur: `prior_width` `1,0` döndürüyordu ama C2 posteriorun
    `%68` aralığını ölçüyor. Düzgün dağılımın `16–84` yüzdelikleri arası
    `0,68`'dir. Yanlış payda C2'yi **belgede yazandan zayıf** yapıyordu.

    Mevcut testlerin hiçbiri bunu yakalamamıştı — payda hiçbir yerde
    ölçülen bir şeyle karşılaştırılmıyordu.
    """
    class _Duz:
        sigma = 0.0

        def predict(self, x):
            return np.zeros(len(x))

    p = grid_posterior(DART_UZAYI, [_Duz()], [0.0], sigma=1.0, n_grid=200)
    olculen = float(np.mean(p.width_u))
    assert olculen == pytest.approx(0.68, abs=0.01), olculen
    assert np.allclose(DART_UZAYI.prior_width(), 0.68)
    # Ve bilgisiz posterior C2'yi GECMEMELI (oran ~1.0, esik 0.50).
    oran = p.width_u / DART_UZAYI.prior_width()
    assert float(np.min(oran)) > C2_DARALMA, oran


def test_C2_bilgisiz_posteriorda_ESIGE_UZAK() -> None:
    """Eski paydayla bilgisiz posterior eşiğe `%37` yaklaşıyordu.

    Doğru paydayla `%100` uzak olmalı — ölçütün ayırt gücü buradan gelir.
    """
    class _Duz:
        sigma = 0.0

        def predict(self, x):
            return np.zeros(len(x))

    p = grid_posterior(DART_UZAYI, [_Duz()], [0.0], sigma=1.0, n_grid=120)
    eski_oran = float(np.min(p.width_u / 1.0))          # KUSURLU payda
    yeni_oran = float(np.min(p.width_u / 0.68))         # DUZELTILMIS
    assert eski_oran < 0.7 and yeni_oran > 0.95, (eski_oran, yeni_oran)


class _Eksen:
    """Tek eksene bağlı vekil — kenara çakılma sınamak için."""

    sigma = 0.0

    def __init__(self, j):
        self.j = j

    def predict(self, x):
        return DART_UZAYI.to_unit(x)[:, self.j]


def test_KENARA_CAKILMA_yakalaniyor() -> None:
    """Gerçek değer önsel aralığın **dışındaysa** posterior sınıra dayanır.

    Bulunan kusur: o durumda bant **çok dar** çıkıyor ve C2 onu "son
    derece bilgilendirici" sayıyordu. Doğru okuma tersidir — parametre
    aralığı yanlış seçilmiş.

    Ayrım keskin ve parametresiz: mod en dış kutuda mı?
    """
    ic = grid_posterior(DART_UZAYI, [_Eksen(0)], [0.5], sigma=0.02, n_grid=100)
    dis = grid_posterior(DART_UZAYI, [_Eksen(0)], [1.5], sigma=0.02, n_grid=100)
    assert ic.pinned(0) is False
    assert dis.pinned(0) is True
    # SAHTE KESINLIK: disaridaki bant ICERIDEKINDEN DAR
    assert dis.width_u[0] < ic.width_u[0]


def test_cakili_eksen_C2_yi_GECIREMEZ() -> None:
    """Çakılı eksenin dar bandı "bilgilendirici" sayılmamalı."""
    dis = grid_posterior(DART_UZAYI, [_Eksen(0)], [1.5], sigma=0.02, n_grid=80)
    v = recovery_verdict(dis, np.array([1.5, 1.0e5, 0.25]),
                         [(1.0, dis), (4.0, dis)])
    assert v.c2_cakili[0] is True
    assert v.c2_gecti is False, v.c2_en_dar
    assert v.gecti is False


def test_ic_bolgedeki_dar_bant_C2_yi_GECIRIYOR() -> None:
    """Pozitif kontrol: koruma **meşru** dar bantları engellememeli."""
    vek = _vekiller()
    gercek = np.array([1.5, 1.0e5, 0.25])
    veri = [float(s.predict(gercek[None, :])[0]) for s in vek]
    post = grid_posterior(DART_UZAYI, vek, veri, sigma=0.02, n_grid=44)
    v = recovery_verdict(post, gercek, [(1.0, post), (4.0, post)])
    assert not any(v.c2_cakili), v.c2_cakili
    assert v.c2_gecti is True


def test_SABIT_gozlenebilir_ayri_tani() -> None:
    """"Sabit" ile "çok dalgalı" **farklı tanılar**, farklı eylemler.

    Sabit bir gözlenebilir vekilin yetersizliği değil, **ileri modelin
    bozukluğu** işaretidir: `θ` sahneye ulaşmıyor demektir. İkisi de
    `guvenilir = False` verir ve `q2` ayırt edemez (sabit `y`'de `nan`).
    """
    x = lhs_design(DART_UZAYI, 40, root_seed=1)
    u = DART_UZAYI.to_unit(x)

    sbt = fit_surrogate(DART_UZAYI, x, np.full(len(x), 3.0))
    assert sbt.sabit is True
    assert np.isnan(sbt.q2)
    assert sbt.guvenilir is False

    dalgali = fit_surrogate(DART_UZAYI, x,
                            np.sin(12.0 * u[:, 0]) * np.cos(11.0 * u[:, 2]))
    assert dalgali.sabit is False          # sabit DEGIL
    assert dalgali.guvenilir is False      # ama yine de yetersiz

    saglikli = fit_surrogate(DART_UZAYI, x, 3.0 + 2.0 * u[:, 0])
    assert saglikli.sabit is False and saglikli.guvenilir is True


def test_kosucu_SABIT_taniyinca_DURUYOR() -> None:
    """Sabit gözlenebilirle devam etmek bütün koşuyu boşa harcar."""
    from pathlib import Path

    kaynak = (Path(__file__).resolve().parents[1] / "scripts" /
              "faz46_sentetik_kurtarma.py").read_text(encoding="utf-8")
    assert "DURDURULDU" in kaynak
    assert "if sabitler:" in kaynak


def test_sedov_kutusu_BIRIM_dx_bire_bolu_n() -> None:
    """`n_sides_for_swing` `dx = 1/n` **varsayıyor** — varsayım pinlendi.

    Sedov kutusu değişirse türetilen `n` listesi sessizce yanlış olurdu:
    tarama ne kapsardı ne de iç nokta verirdi, ve `judge` "belirsiz"
    döndüğünde nedeni anlaşılmazdı.
    """
    from dartrift.validation.sedov import build_sedov_ic

    for n in (32, 64):
        assert build_sedov_ic(n)["dx"] == pytest.approx(1.0 / n, rel=1e-12), n
