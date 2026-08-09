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
    koşturur ve vekil **sabit** bir yüzey öğrenir.

    ADR-0044 (KABUL EDİLDİ) sonrası `θ₀` **`boulder_alpha0`**'dır;
    `matrix_alpha0` **verilmez** ve üretici onu `ρ_yığın`dan türetir.
    """
    kw = sahne_parametreleri([1.15, 3.0e5, 0.3])
    assert kw["boulder_alpha0"] == pytest.approx(1.15)
    assert kw["matrix_Y0"] == pytest.approx(3.0e5)
    assert kw["f_boulder"] == pytest.approx(0.3)
    assert "matrix_alpha0" not in kw            # <-- TURETILECEK


def test_ESKI_esleme_hala_erisilebilir() -> None:
    """ADR-0044 geri alınabilir olmalı — eski yol **silinmedi**."""
    kw = sahne_parametreleri([1.6, 3.0e5, 0.3], secenek3=False)
    assert kw["matrix_alpha0"] == pytest.approx(1.6)
    assert "boulder_alpha0" not in kw


def test_taban_argumanlari_KORUNUYOR_ama_EZILEBILIYOR() -> None:
    kw = sahne_parametreleri([1.15, 3.0e5, 0.3],
                             {"radius": 82.0, "f_boulder": 0.99})
    assert kw["radius"] == 82.0
    assert kw["f_boulder"] == pytest.approx(0.3)     # theta kazanir


def test_FARKLI_theta_FARKLI_sahne() -> None:
    """Pozitif kontrol: eşleme gerçekten `θ`'ya bağlı mı?"""
    a = sahne_parametreleri([1.05, 1.0e4, 0.1])
    b = sahne_parametreleri([1.25, 5.0e6, 0.4])
    assert a != b
    for k in ("boulder_alpha0", "matrix_Y0", "f_boulder"):
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


def test_ERKEN_IPTAL_kodda_var() -> None:
    """Patlamayı koşu **sonunda** anlamak, pahalı bir tasarımda boşa GPU.

    Kota dolu olduğu için bu yolu koşamıyorum; yapının varlığı sınanıyor.
    Zayıf bir test ama hiç olmamasından iyi — ve niyeti kayda geçiriyor.
    """
    from pathlib import Path

    kaynak = (Path(__file__).resolve().parents[1] / "src" / "dartrift" /
              "inference" / "forward.py").read_text(encoding="utf-8")
    assert "ERKEN IPTAL" in kaynak
    assert "kosu PATLADI adim" in kaynak
    assert "BOSA harcanmadi" in kaynak


def test_TASARIMIN_TAMAMI_duserse_kok_neden_yaziliyor() -> None:
    """`fit_surrogate` "n <= p" derdi; kök neden anlaşılmazdı."""
    from pathlib import Path

    kaynak = (Path(__file__).resolve().parents[1] / "scripts" /
              "faz46_sentetik_kurtarma.py").read_text(encoding="utf-8")
    assert "TASARIMIN TAMAMI dustu" in kaynak
    assert "COK seyreldi" in kaynak


# ------------------------- krater ayarlari (olculmus kisit)

def test_KRATER_AYARLARI_DART_gercekten_isi_degistiriyor():
    """Varsayılan kutulama `16 m`'lik krateri **göremiyor**; ayarlı görüyor.

    Bu bir *"parametre ekledim"* testi değil: iki ayarın **farklı**
    sonuç verdiğini ölçüyor. Aynı sonucu verseydi ayar eklemek boşuna
    olurdu.
    """
    from dartrift.inference.forward import KRATER_AYARLARI_DART
    from dartrift.observables.crater_shape import crater_profile
    R, s, D, d_kr = 82.0, 2.0, 16.0, 3.0
    rng = np.random.default_rng(7)
    n = int(4 * np.pi * R * R / (s * s))
    u = rng.uniform(-1, 1, n)
    ph = rng.uniform(0, 2 * np.pi, n)
    q = np.sqrt(1 - u * u)
    yon = np.column_stack([q * np.cos(ph), q * np.sin(ph), u])
    merk = np.array([1.0, 0.0, 0.0])
    ya = np.arcsin(D / 2 / R)
    ca = yon @ merk
    ic = ca > np.cos(ya)
    a = np.arccos(np.clip(ca, -1, 1))
    r = np.full(n, R)
    r[ic] = R - d_kr * (1.0 - (a[ic] / ya) ** 2)
    x, x0 = r[:, None] * yon, R * yon

    ort = dict(center=np.zeros(3), impact_direction=-merk,
               reference_radius=R, x_reference=x0)
    vars_ = crater_profile(x, **ort)
    ayar = crater_profile(x, **ort, **KRATER_AYARLARI_DART)
    assert vars_.depth == 0.0, "varsayilan gormeliydi mi? olcum degisti"
    assert ayar.depth > 0.5 * d_kr, (ayar.depth, d_kr)


def test_krater_ayarlari_VARSAYILAN_davranisi_bozmuyor():
    """`krater_ayarlari=None` eski yolu **aynen** korumalı."""
    from dartrift.inference.forward import gozlenebilirleri_cikar
    import inspect
    p = inspect.signature(gozlenebilirleri_cikar).parameters
    assert p["krater_ayarlari"].default is None


def test_KRATER_AYARLARI_DART_yanlis_pozitif_URETMIYOR():
    """İnce kutulama `surface_particles`'ın uyardığı tuzağa düşüyor mu?

    Belge diyor ki kutu başına `~1` parçacık kalınca *"kutudaki en
    uzak"* rastgele bir parçacık olur ve ölçülen yüzey `0,75 R`'ye
    iner — **hayalî bir krater** üretir. `KRATER_AYARLARI_DART`
    `n_theta = 64` kullanıyor ve `s = 3,5 m`'de bu **`0,84`
    parçacık/kutu** demek, yani tam o bölge.

    Ölçüldü: **düşmüyor**, çünkü `x_reference` çıkarması yanlılığı
    götürüyor (R4'ün `x_reference`'ı zorunlu yapmasının sebebi).
    """
    from dartrift.inference.forward import KRATER_AYARLARI_DART
    from dartrift.observables.crater_shape import crater_profile
    R = 82.0
    for s in (3.5, 2.0):
        rng = np.random.default_rng(11)
        n = int(4 * np.pi * R * R / (s * s))
        u = rng.uniform(-1, 1, n)
        ph = rng.uniform(0, 2 * np.pi, n)
        q = np.sqrt(1 - u * u)
        yon = np.column_stack([q * np.cos(ph), q * np.sin(ph), u])
        x0 = R * yon
        for gur, kur in ((0.0, 0.0), (0.20, 0.0), (0.20, -0.5)):
            r = R + kur + gur * rng.normal(size=n)
            kr = crater_profile(r[:, None] * yon, center=np.zeros(3),
                                impact_direction=np.array([-1.0, 0.0, 0.0]),
                                reference_radius=R, x_reference=x0,
                                **KRATER_AYARLARI_DART)
            # KRATERSIZ cisimde derinlik GURULTU duzeyinde kalmali.
            assert kr.depth < 0.5, (s, gur, kur, kr.depth)
            assert kr.diameter == 0.0, (s, gur, kur, kr.diameter)
