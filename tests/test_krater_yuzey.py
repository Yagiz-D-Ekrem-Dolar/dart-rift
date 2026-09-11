"""A73 — fiziksel yüzey operatörü (uzman yanıtı 2026-09-11).

Uzman eski çıkarıcının (`crater_profile`, eksen kipi, sayı ağırlıklı
`p95`) yüzey olmadığını üç karşı örnekle gösterdi:

| sınav | eski çıkarıcı |
|---|---|
| dış `1 m` kabuk sabit, yalnız iç noktalar taşındı | `0,49 m` |
| aynı koordinatlar 8 kat çoğaltıldı | `0,34 → 0,71 m` |
| `0,5 m` ayak izli, `1 m` derin analitik çukur | `0,0012 m` |

Bu dosya yeni operatörün (`krater_yuzey`) aynı sınavlarda ne verdiğini
kilitliyor. Sayılar ÖLÇÜLDÜ (levha, FCC `s = 0,35`, `h = 0,70`,
`N = 32 490`); eşikler o ölçümlerden ve türetilmiş gerçeklerden
geliyor, ayarlanmadı.
"""
from __future__ import annotations

import numpy as np
import pytest

from dartrift.observables.crater_shape import krater_yuzey, krater_yuzey_durumdan
from dartrift.setup.rubble_generator import lattice_points, particle_volume

S = 0.35
H = 2.0 * S          # merdivenin h/s orani (refine: h = 2 s)
RHO = 2700.0 / 1.3
#: Eski çıkarıcının uzman sınavındaki değeri (dış 1 m kabuk sabit).
ESKI_KABUK = 0.49


@pytest.fixture(scope="module")
def levha():
    x = lattice_points(np.array([-7.0, -7.0, -5.0]),
                       np.array([7.0, 7.0, 0.0]), S, "fcc")
    x = x[x[:, 2] <= 1e-9]
    m = np.full(len(x), RHO * particle_volume(S, "fcc"))
    return x, m


def _olc(x, x0, m, v=None, **kw):
    n = len(x)
    return krater_yuzey(x, x0, m=m, h=np.full(n, H), rho=np.full(n, RHO),
                        rho_reference=np.full(n, RHO),
                        impact_direction=np.array([0.0, 0.0, -1.0]),
                        v=v, merkez=np.array([0.0, 0.0, -2.5]), **kw)


def _cukur(levha, a, D, *, kopya=1, perde=False, hizli=True):
    """Paraboloit çukur: yüzeyin üstünde kalanlar ATILIR (ejekta)."""
    x0, m = levha
    x = x0.copy()
    s_yan = np.hypot(x[:, 0], x[:, 1])
    z_yuzey = np.where(s_yan < a, -D * (1.0 - (s_yan / a) ** 2), 0.0)
    sil = x[:, 2] > z_yuzey + 1e-9
    v = np.zeros_like(x)
    if perde:
        # Perde yuzeyden AYRILMIS olmali: her parcacik kendi destegini
        # (2h = 1,4 m) asacak kadar yukarida. Ilk surum 0,2 m ustune
        # koyuyordu; o konumda perde yuzeye DEGIYOR (cekirdekler ortusuyor)
        # ve ayrilmis sayilmasi fiziksel degil (bkz. ayrilma_mesafesi).
        x[sil, 2] = 2.0 + (x[sil, 2] - x[sil, 2].min())
        v[sil, 2] = 5.0 if hizli else 0.0
    else:
        x[sil, 2] += 50.0
        v[sil, 2] = 5.0
    ref, mm = x0, m
    if kopya > 1:
        x, ref, v = (np.repeat(q, kopya, axis=0) for q in (x, ref, v))
        mm = np.repeat(m, kopya) / kopya
    eksen = np.hypot(x0[:, 0], x0[:, 1]) < 0.5 * S
    gercek = x0[eksen, 2].max() - x0[eksen & ~sil, 2].max()
    return _olc(x, ref, mm, v=v), int(sil.sum()), float(gercek)


# --- degismezler ---------------------------------------------------------

def test_hareketsiz_cisimde_profil_TAM_sifir(levha):
    x0, m = levha
    k = _olc(x0.copy(), x0, m)
    assert np.all(k.profil == 0.0)
    assert k.derinlik == 0.0


def test_rijit_oteleme_duzeltme_ACIKKEN_sifir(levha):
    x0, m = levha
    k = _olc(x0 + np.array([0.3, -0.2, 0.5]), x0, m, rijit_duzeltme=True)
    assert np.nanmax(np.abs(k.profil)) < 1e-12
    np.testing.assert_allclose(k.rijit_kayma, [0.3, -0.2, 0.5], atol=1e-12)


def test_rijit_duzeltme_varsayilan_KAPALI_ve_kayma_RAPORLANIYOR(levha):
    """Kapalıyken ötelemenin dikey bileşeni yüzeyde görünür (beklenen)."""
    x0, m = levha
    k = _olc(x0 + np.array([0.3, -0.2, 0.5]), x0, m)
    assert k.tani["rijit_duzeltme"] is False
    assert k.derinlik_merkez == pytest.approx(-0.5, abs=0.01)
    np.testing.assert_allclose(k.rijit_kayma, [0.3, -0.2, 0.5], atol=1e-12)


def test_destekten_KALIN_kabuk_sabitken_ic_hareket_yuzeyi_DEGISTIRMIYOR(levha):
    """Kabuk ≥ `2h`: iç parçacıklar yüzeydeki dolululuğa hiç katkı vermez.

    Ölçülen `8e-8 m` — çekirdek desteğinin sınırındaki kuyruk; kütle
    merkezi `0,375 m` kaydığı halde (düzeltme kapalı).
    """
    x0, m = levha
    x = x0.copy()
    x[x[:, 2] < -(2.0 * H + 1e-6), 2] -= 0.5
    k = _olc(x, x0, m)
    assert abs(k.rijit_kayma[2]) > 0.3, "sinav bos: ic kutle kaymadi"
    assert np.nanmax(np.abs(k.profil)) < 1e-6


def test_uzman_sinavi_1m_kabuk_ESKI_cikaricidan_100_kat_kucuk(levha):
    """Uzmanın kurulumu: dış `1 m` (< `2h = 1,4 m`) sabit, iç `-0,5 m`.

    Eski çıkarıcı `0,49 m`; yeni operatör `8,9e-4 m` ölçtü (kabuktan
    ince destek payı içindeki parçacıkların kuyruğu).
    """
    x0, m = levha
    x = x0.copy()
    x[x[:, 2] < -1.0, 2] -= 0.5
    k = _olc(x, x0, m)
    assert np.nanmax(np.abs(k.profil)) < ESKI_KABUK / 100.0


def test_yeniden_ornekleme_8_kopya_SONUCU_DEGISTIRMIYOR(levha):
    k1, _, _ = _cukur(levha, 2.0, 1.0)
    k8, _, _ = _cukur(levha, 2.0, 1.0, kopya=8)
    assert abs(k1.derinlik - k8.derinlik) < 1e-12
    np.testing.assert_allclose(k1.profil, k8.profil, atol=1e-12)


# --- bilinen cukurlar ----------------------------------------------------

def test_genis_cukur_AYRIK_GERCEGI_veriyor(levha):
    """`a = 5 m`: kafesin ayrık derinliği (`0,9899`) ile aynı."""
    k, n_sil, gercek = _cukur(levha, 5.0, 1.0)
    assert k.n_ayrilan == n_sil
    assert abs(k.derinlik - gercek) < 1e-3, (k.derinlik, gercek)


def test_dar_cukurda_yanit_COZUNURLUKLE_sinirli_ve_monoton(levha):
    """Destek `2h = 1,4 m`; dar çukur yumuşar — ama KAYBOLMAZ.

    Ölçülen: `a = 5 / 2 / 1 / 0,5 m` → `0,990 / 0,922 / 0,694 / 0,259`.
    Eski çıkarıcı `a = 0,5`'te `0,0012` veriyordu (`%0,1`).
    """
    d = [_cukur(levha, a, 1.0)[0].derinlik for a in (5.0, 2.0, 1.0, 0.5)]
    assert d[0] > d[1] > d[2] > d[3] > 0.0
    assert d[3] > 100 * 0.0012, "dar cukur eski cikarici gibi kayboldu"


def test_ejekta_perdesi_DISLANIYOR(levha):
    k_yok, _, _ = _cukur(levha, 2.0, 1.0)
    k_perde, n, _ = _cukur(levha, 2.0, 1.0, perde=True)
    assert k_perde.n_ayrilan == n
    assert abs(k_perde.derinlik - k_yok.derinlik) < 1e-12


def test_hizsiz_perde_dislanamaz_ve_krateri_DOLDURUR(levha):
    """Ayrılma ölçütü hıza dayanıyor; hız yoksa perde yüzey sayılır.

    Bu bir sınır, kusur değil: ölçülen `0,92 → 0,40 m`. Durum
    dosyası `v` taşıdığı sürece ayrım yapılır.
    """
    k_yok, _, _ = _cukur(levha, 2.0, 1.0)
    k_q, _, _ = _cukur(levha, 2.0, 1.0, perde=True, hizli=False)
    assert k_q.n_ayrilan == 0
    assert k_q.derinlik < 0.6 * k_yok.derinlik


def test_stres_dalgasi_yuzey_hareketi_EJEKTA_SAYILMIYOR(levha):
    """Gerçek DART durumunda ölçülen yapıt: yüzey parçacıkları stres
    dalgasıyla `~0,2 m/s` dışa gidiyor, yalnız `mm` yer değiştirmiş.
    Kaçış hızı `8,2 cm/s` olduğu için ilk ölçüt onları ejekta sayıp
    siliyordu ve `2,75 m`'lik SAHTE halka doğuyordu."""
    x0, m = levha
    x = x0.copy()
    v = np.zeros_like(x)
    ust = x0[:, 2] > x0[:, 2].max() - 0.5
    x[ust, 2] += 0.005                     # 5 mm
    v[ust, 2] = 0.2                        # dalga hizi, kacis hizinin ustunde
    k = _olc(x, x0, m, v=v, ayrilma_hizi=0.082)
    assert k.n_ayrilan == 0
    assert np.nanmax(np.abs(k.profil)) < 0.01


def test_hacim_ve_yaricap_mertebesi(levha):
    k, _, _ = _cukur(levha, 5.0, 1.0)
    assert 4.0 <= k.yaricap <= 5.2
    assert 0.8 * (np.pi * 25.0 / 2.0) < k.hacim < 1.05 * (np.pi * 25.0 / 2.0)


# --- durum dosyasi yolu --------------------------------------------------

def test_durumdan_okuyucu_alan_EKSIKSE_acik_hata():
    with pytest.raises(KeyError, match="'h'"):
        krater_yuzey_durumdan({"x": 0, "x_referans": 0, "m": 0, "rho": 0,
                               "alpha0": 0, "ehat": 0, "R": 1.0,
                               "mermi_kesri": 0})


def test_durumdan_okuyucu_mermiyi_DISLIYOR(levha):
    x0, m = levha
    n = len(x0)
    mermi = np.array([[0.0, 0.0, 1.0]])
    d = {"x": np.vstack([x0, mermi]), "x_referans": np.vstack([x0, mermi]),
         "m": np.concatenate([m, [500.0]]), "rho": np.full(n + 1, RHO),
         "alpha0": np.full(n + 1, 1.3), "h": np.full(n + 1, H),
         "ehat": np.array([0.0, 0.0, -1.0]), "R": 82.0,
         "v": np.zeros((n + 1, 3)),
         "mermi_kesri": np.concatenate([np.zeros(n), [1.0]])}
    k = krater_yuzey_durumdan(d, s_max=1.0)
    assert k.derinlik == 0.0
