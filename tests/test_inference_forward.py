"""İleri modelin **GPU'suz sınanabilen** parçaları (FAZ 4.6).

`ileri_kosu` üç parçaya ayrıldı ki doğrulanamayan kod yolu mümkün
olduğunca küçülsün (S9'un dersi). Bu dosya sınanabilen ikisini kapsar:
parametre→sahne eşlemesi ve gözlenebilir çıkarımı.
"""
from __future__ import annotations

import numpy as np
import pytest

from dartrift.inference.forward import GOZLENEBILIRLER, gozlenebilirleri_cikar, sahne_parametreleri

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


# ------------------- krater ayarlari (UC KEZ yazildi, bkz. A13/A16)

def _kraterli_dolu_kure(derinlik, R=82.0, D=20.0, s=3.5, tohum=5, gurultu=0.0):
    """DOLU kure + paraboloid krater.

    **KABUK KULLANMIYOR.** A16'nin dersi tam buydu: kabukta her parcacik
    zaten yuzeydedir, yani yuzey cikariminin bozuk olmasi GORUNMEZ.
    Kabuk fiksturuyle `n_theta = 1024`'un dejenere oldugunu hic
    goremedim.
    """
    rng = np.random.default_rng(tohum)
    k = int(R // s)
    g = np.arange(-k, k + 1) * s
    X, Y, Z = np.meshgrid(g, g, g, indexing="ij")
    p3 = np.column_stack([X.ravel(), Y.ravel(), Z.ravel()])
    p3 = p3 + rng.normal(scale=0.25 * s, size=p3.shape)
    r0 = np.linalg.norm(p3, axis=1)
    ic = (r0 > 0.0) & (r0 <= R)
    x0, r0 = p3[ic], r0[ic]
    yon = x0 / r0[:, None]
    eh = np.array([0.0, 0.0, 1.0])
    th = np.arccos(np.clip(yon @ eh, -1, 1))
    thc = np.arcsin(D / (2 * R))
    taban = R - derinlik * (1.0 - (th / thc) ** 2)
    r = np.where(th < thc, np.minimum(r0, taban), r0)
    if gurultu:
        r = r + gurultu * rng.normal(size=len(r))
    return r[:, None] * yon, x0, eh, R


def test_KRATER_AYARLARI_DART_eksen_kipinde():
    """Ayarlar `kutulama = "eksen"` kullanmali ve `n_theta` TASIMAMALI.

    `n_theta` iki kez yanlis secildi (A13: `64` krateri goremiyor;
    A16: `1024` izgarayi parcacik sayisinin ustune cikarip *"yuzey =
    butun cisim"* yapiyor). Eksen kipinde o parametre KULLANILMIYOR;
    birakmak "ayarlanmis" izlenimi verirdi.
    """
    from dartrift.inference.forward import KRATER_AYARLARI_DART as K
    assert K["kutulama"] == "eksen"
    assert "n_theta" not in K and "n_phi" not in K
    assert K["ejekta_yaricap_carpani"] == 1.05
    # Esik acikca ayarlanmis OLMAMALI: hayali cap denetimi ona bagli.
    assert "depth_threshold" not in K


def test_krater_ayarlari_VARSAYILAN_davranisi_bozmuyor():
    """`krater_ayarlari=None` eski yolu **aynen** korumali."""
    import inspect

    from dartrift.inference.forward import gozlenebilirleri_cikar
    p = inspect.signature(gozlenebilirleri_cikar).parameters
    assert p["krater_ayarlari"].default is None


def test_KRATER_AYARLARI_DART_derinligi_GERCEKTEN_izliyor():
    """Uretim ayarlariyla derinlik gercek derinlikle degismeli.

    A13'un `n_theta = 64`'u ayni sahnede **sabit `1,1975`** veriyordu;
    A16'nin `1024`'u yuzey yerine butun cismi olcuyordu. Eksen kipinde
    olculdu (uretim sahnesi, `nb = 8`): `2 -> 2,015`, `5 -> 4,882`,
    `10 -> 9,660`.
    """
    from dartrift.inference.forward import KRATER_AYARLARI_DART
    from dartrift.observables.crater_shape import crater_profile

    olculen = []
    for derin in (2.0, 5.0, 10.0):
        x, x0, eh, R = _kraterli_dolu_kure(derin)
        kr = crater_profile(x, center=np.zeros(3), impact_direction=-eh,
                            reference_radius=R, x_reference=x0,
                            **KRATER_AYARLARI_DART)
        olculen.append(kr.depth)
    assert olculen[0] < olculen[1] < olculen[2], olculen


def test_KRATER_AYARLARI_DART_yanlis_pozitif_URETMIYOR():
    """Kratersiz DOLU cisimde ne derinlik ne cap uydurulmali."""
    from dartrift.inference.forward import KRATER_AYARLARI_DART
    from dartrift.observables.crater_shape import crater_profile

    for gur in (0.05, 0.2):
        x, x0, eh, R = _kraterli_dolu_kure(0.0, gurultu=gur, tohum=3)
        kr = crater_profile(x, center=np.zeros(3), impact_direction=-eh,
                            reference_radius=R, x_reference=x0,
                            **KRATER_AYARLARI_DART)
        assert kr.depth < 1.5, (gur, kr.depth)
        assert kr.diameter == 0.0, (gur, kr.diameter)


def test_kuresel_kip_DOLU_cisimde_yuzeyi_bulamiyor():
    """A16'nin cekirdegi: `n_theta = 64` DOLU cisimde REDDETMIYOR.

    Ilk yazdigimda "reddediyor" varsaydim — **yanlis**. Kabukta
    reddediyor (koniye 1 parcacik duser), dolu cisimde ise sessizce bir
    sayi donduruyor. Sessiz yanlis sayi, reddetmekten **daha kotudur**.

    Olculebilir ifade: cikarilan "yuzey" kumesinin medyan yaricapi
    gercek yuzeyden cok asagida. Olculdu (`N = 10 410`, `R = 81,94`):

    | `n_theta` | "yuzey"/toplam | medyan `r` |
    |---|---|---|
    | 16 | 0,05 | 81,26 |
    | 64 | 0,58 | 72,18 |
    | 1024 | 0,96 | 66,91 |
    """
    from dartrift.observables.crater_shape import surface_particles

    x, x0, eh, R = _kraterli_dolu_kure(0.0)
    onceki = None
    for nth in (16, 64, 1024):
        idx = surface_particles(x0, np.zeros(3), n_theta=nth, n_phi=2 * nth)
        med = float(np.median(np.linalg.norm(x0[idx], axis=1)))
        oran = len(idx) / len(x0)
        if nth == 16:
            assert med > 0.95 * R, f"n_theta=16 yuzey bulamadi: {med}"
        if nth == 1024:
            assert oran > 0.9, f"dejenerasyon beklenirdi, oran {oran}"
            assert med < 0.9 * R, f"medyan {med}, R {R}"
        if onceki is not None:
            assert med < onceki, "n_theta buyudukce medyan DUSMELI"
        onceki = med


def test_ejekta_suzgeci_hepsini_elerse_hata():
    """Suzgec her seyi elerse hata; `0,1 x R` DOLU cismi bosaltmaz.

    Ilk halinde `0,1` yazdim ve "TUM parcaciklari eledi" hatasini
    bekledim — kabuk aliskanligi. Dolu cisimde merkeze yakin parcaciklar
    kaliyor ve baska bir hata (`profil bos`) cikiyor.
    """
    from dartrift.observables.crater_shape import crater_profile
    x, x0, eh, R = _kraterli_dolu_kure(2.0)
    with pytest.raises(ValueError, match="TUM"):
        crater_profile(x, center=np.zeros(3), impact_direction=-eh,
                       reference_radius=R, x_reference=x0,
                       ejekta_yaricap_carpani=1.0e-4)


def test_iki_ileri_kosu_yolu_krateri_AYNI_olcuyor():
    """`ileri_kosu` ve `ileri_kosu_ikiasama` aynı ayarları kullanmalı.

    Bulundu: iki aşamalı yol `KRATER_AYARLARI_DART` geçiriyordu, tek
    aşamalı yol **hiç geçirmiyordu** (varsayılan kaba kutulama). Aynı
    kurulumun iki kolu krateri farklı ölçerse aralarındaki fark fizik
    değil **ayar farkı** olur — ve karşılaştırma sessizce anlamsızlaşır.
    """
    import inspect

    from dartrift.inference import forward as F

    a = inspect.signature(F.ileri_kosu).parameters["krater_ayarlari"].default
    b = inspect.signature(
        F.ileri_kosu_ikiasama).parameters["krater_ayarlari"].default
    assert a == b == F.KRATER_AYARLARI_DART
