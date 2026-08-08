"""İleri modelin **GPU'suz sınanabilen** parçaları (FAZ 4.6).

`ileri_kosu` üç parçaya ayrıldı ki doğrulanamayan kod yolu mümkün
olduğunca küçülsün (S9'un dersi). Bu dosya sınanabilen ikisini kapsar:
parametre→sahne eşlemesi ve gözlenebilir çıkarımı.
"""
from __future__ import annotations

import numpy as np
import pytest

from dartrift.inference.forward import (GOZLENEBILIRLER,
                                        gozlenebilirleri_cikar,
                                        sahne_parametreleri)


# ------------------------------------------------- parametre -> sahne

def test_theta_DOGRU_alanlara_yaziliyor() -> None:
    """En sinsi hata: `Y₀` yanlış alana gider, bütün tasarım aynı sahneyi
    koşturur ve vekil **sabit** bir yüzey öğrenir."""
    kw = sahne_parametreleri([1.6, 3.0e5, 0.3])
    assert kw["matrix_alpha0"] == pytest.approx(1.6)
    assert kw["matrix_Y0"] == pytest.approx(3.0e5)
    assert kw["f_boulder"] == pytest.approx(0.3)


def test_taban_argumanlari_KORUNUYOR_ama_EZILEBILIYOR() -> None:
    kw = sahne_parametreleri([1.6, 3.0e5, 0.3],
                             {"radius": 82.0, "f_boulder": 0.99})
    assert kw["radius"] == 82.0
    assert kw["f_boulder"] == pytest.approx(0.3)     # theta kazanir


def test_FARKLI_theta_FARKLI_sahne() -> None:
    """Pozitif kontrol: eşleme gerçekten `θ`'ya bağlı mı?"""
    a = sahne_parametreleri([1.2, 1.0e4, 0.1])
    b = sahne_parametreleri([1.8, 5.0e6, 0.4])
    assert a != b
    for k in ("matrix_alpha0", "matrix_Y0", "f_boulder"):
        assert a[k] != b[k], k


def test_gecersiz_theta_REDDEDILIYOR() -> None:
    with pytest.raises(ValueError, match="alpha0"):
        sahne_parametreleri([0.5, 1.0e5, 0.3])
    with pytest.raises(ValueError, match="Y0"):
        sahne_parametreleri([1.5, -1.0, 0.3])
    with pytest.raises(ValueError, match="f_boulder"):
        sahne_parametreleri([1.5, 1.0e5, 1.7])
    with pytest.raises(ValueError, match=r"\(3,\)"):
        sahne_parametreleri([1.5, 1.0e5])


# ------------------------------------------- gozlenebilir cikarimi

def _durum(n=40000, seed=3, bozuk=None):
    """Yeterince YOGUN bir kure.

    İlk fikstür `n = 800` idi ve `crater_profile` `"profil bos — hicbir
    kutuda 5 parcacik yok"` ile düştü. Bu bir kod kusuru **değil**, gerçek
    bir işletme kısıtı: krater çıkarımı `n_bins = 20` açısal kutunun her
    birinde en az `min_per_bin = 5` **yüzey** parçacığı ister. Kaba bir
    DART sahnesi (`spacing = 7 m` → ~10 000 parçacık) bu sınıra yakındır
    ve kutu sayısı düşürülmek zorunda kalabilir. Kısıt burada yazılı.
    """
    g = np.random.default_rng(seed)
    yon = g.normal(size=(n, 3))
    yon /= np.linalg.norm(yon, axis=1)[:, None]
    r = 82.0 * g.random(n) ** (1.0 / 3.0)
    x = yon * r[:, None]
    v = g.normal(0.0, 0.3, (n, 3))
    st = {"x": x, "v": v, "m": np.full(n, 1.0e6), "rho": np.full(n, 1800.0)}
    if bozuk:
        st[bozuk] = np.array(st[bozuk], dtype=np.float64)
        st[bozuk][5] = np.nan
    return st


def _cagri(st, **ek):
    n = len(st["m"])
    is_imp = np.zeros(n, bool)
    is_imp[-20:] = True
    kw = dict(impactor_momentum=np.array([0.0, 0.0, 3.56e6]),
              target_mass=float(np.sum(st["m"][~is_imp])),
              target_radius=82.0, is_impactor=is_imp,
              impact_direction=np.array([0.0, 0.0, -1.0]),
              x_reference=st["x"])
    kw.update(ek)
    return gozlenebilirleri_cikar(st, **kw)


def test_uc_gozlenebilir_SIRAYLA_donuyor() -> None:
    y = _cagri(_durum())
    assert y.shape == (len(GOZLENEBILIRLER),)
    assert np.all(np.isfinite(y))


def test_x_reference_ZORUNLU_R4() -> None:
    """R4 kapanıyor: verilmezse şekil krater diye ölçülürdü."""
    with pytest.raises(ValueError, match="R4"):
        _cagri(_durum(), x_reference=None)


@pytest.mark.parametrize("alan", ["x", "v", "m", "rho"])
def test_PATLAMIS_kosu_sessizce_sayi_DONDURMUYOR(alan) -> None:
    """S4'ün dersi: NaN'ın sessizce geçmesi fark edilmesi en zor kusurdu."""
    with pytest.raises(RuntimeError, match="PATLADI"):
        _cagri(_durum(bozuk=alan))


def test_gozlenebilir_adlari_TEK_KAYNAK() -> None:
    """Koşucu betik adları **kendi** tanımlamamalı, `forward`'dan almalı.

    İlk sürümde betiğin kendi `GOZLENEBILIRLER` demeti vardı ve bu test
    adların iki yerde de geçtiğini sınıyordu. Yanlış yaklaşımdı: 2. turun
    dersi *"aynı büyüklük iki yerde yazılıysa er geç ayrışır"* diyor.
    Doğru çözüm ayrışmayı **sınamak** değil, tek kaynağa **indirmekti**.

    Ayrışma artık imkânsız; bu test onun geri gelmemesini sağlıyor.
    """
    from pathlib import Path

    kaynak = (Path(__file__).resolve().parents[1] / "scripts" /
              "faz46_sentetik_kurtarma.py").read_text(encoding="utf-8")
    assert "from dartrift.inference.forward import GOZLENEBILIRLER" in kaynak
    assert "GOZLENEBILIRLER = (" not in kaynak, \
        "betik adlari YENIDEN tanimlamis -- iki kaynak olustu"
    assert len(GOZLENEBILIRLER) == 3
