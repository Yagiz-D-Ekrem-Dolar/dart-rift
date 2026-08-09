"""`β` durulma ölçütü — **eski ölçütün kusuru dahil** sınanıyor (FAZ 4.5)."""
from __future__ import annotations

import numpy as np
import pytest

from dartrift.validation.settling_time import is_settled, settling_time


def _eski_plato(t, b, tol=0.02):
    """`measure_longrun.py`'deki **eski** mantık — kusuru göstermek için."""
    bb = np.asarray(b, dtype=np.float64)
    tt = np.asarray(t, dtype=np.float64)
    icinde = np.abs(bb - bb[-1]) <= tol * abs(bb[-1])
    k = len(icinde) - 1
    while k > 0 and icinde[k - 1]:
        k -= 1
    return float(tt[k])


def test_duran_seri_DURULMUS() -> None:
    t = np.linspace(0.0, 1.0, 40)
    b = 0.5 + 1e-4 * np.sin(20.0 * t)          # gurultulu ama duruyor
    d = is_settled(t, b)
    assert d["durulmus"] is True, d


def test_tirmanan_seri_DURULMAMIS() -> None:
    """Hâlâ tırmanan bir seri durulmuş sayılamaz."""
    t = np.linspace(0.0, 1.0, 40)
    b = 0.5 + 0.4 * t
    d = is_settled(t, b)
    assert d["durulmus"] is False
    assert "eğilim" in d["neden"]


def test_ESKI_OLCUT_tirmanan_seride_YANLIS_cevap_veriyor() -> None:
    """Düzeltilen kusurun **gerçekten** kusur olduğunu gösteren test.

    Bir düzeltmenin gerekli olduğunu iddia etmek yetmez; düzeltilen şeyin
    bozuk olduğu **ölçülür**.

    Kusur, eski ölçütün **"durulmadı" diyememesidir**: açıkça tırmanan
    bir seride bile sonlu bir "durulma zamanı" döndürür ve çağıran onu
    gerçek bir plato sanar.

    İlk yazdığım iddia *"çok erken bir anı durulma ilan eder"* idi ve
    **ölçünce yanlış çıktı** (eğim `0,4` için `0,9574` döndü, erken bir
    an değil). Kusur erkenlik değil, **hiç reddedememektir**.
    """
    t = np.linspace(0.0, 1.0, 400)
    for egim in (0.4, 0.1):
        b = 0.5 + egim * t                     # hic durulmuyor
        eski = _eski_plato(t, b)
        assert np.isfinite(eski), "eski olcut sayi dondurmeli (kusur bu)"
        yeni = settling_time(t, b)
        assert yeni["durulmus"] is False, egim
        assert np.isnan(yeni["t_durulma"]), egim


def test_durulmamis_seride_ZAMAN_RAPORLANMIYOR() -> None:
    t = np.linspace(0.0, 1.0, 40)
    b = 0.5 + 0.4 * t
    s = settling_time(t, b)
    assert np.isnan(s["t_durulma"])
    assert s["adim_durulma"] == -1


def test_duran_seride_ZAMAN_makul() -> None:
    """Erken durulan seride durulma anı **geçişin** yakınında olmalı."""
    t = np.linspace(0.0, 1.0, 200)
    b = 0.6 * (1.0 - np.exp(-t / 0.05))        # ~0.15'te oturuyor
    s = settling_time(t, b)
    assert s["durulmus"] is True
    assert 0.05 < s["t_durulma"] < 0.40, s


def test_az_nokta_DURULMUS_SAYILMIYOR() -> None:
    assert is_settled([0, 1, 2], [1, 1, 1])["durulmus"] is False


def test_nan_lar_ATILIYOR() -> None:
    t = np.linspace(0.0, 1.0, 40)
    b = np.full(40, 0.5)
    b[::7] = np.nan
    assert is_settled(t, b)["durulmus"] is True


def test_pencere_ZAMANA_bagli_ORNEKLEMEYE_degil() -> None:
    """Örnekleme sıklığı değişince yargı değişmemeli.

    Ölçüt nokta sayısına bağlansaydı, aynı fizik iki farklı `--every`
    değerinde farklı yargı verirdi.
    """
    for n in (40, 120, 400):
        t = np.linspace(0.0, 1.0, n)
        b = 0.5 + 0.4 * t
        assert is_settled(t, b)["durulmus"] is False, n
        b2 = 0.5 + 1e-5 * np.sin(30.0 * t)
        assert is_settled(t, b2)["durulmus"] is True, n


def test_YAVAS_SURUKLENME_yakalaniyor() -> None:
    """Gürültü küçük ama ortalama kayıyorsa **durulmamıştır**."""
    t = np.linspace(0.0, 1.0, 200)
    b = 0.5 + 0.05 * t + 0.001 * np.sin(50.0 * t)
    d = is_settled(t, b)
    assert d["durulmus"] is False
    assert d["egim_kaymasi"] > 0.02


def test_yarim_pencere_sinavi_BAGIMSIZ_DEGIL() -> None:
    """Ölçüldü: yarım-pencere sınavı **hiçbir şekilde tek başına** yakalamıyor.

    Modül başlığında bunu "iki bağımsız sınav" diye yazmıştım; yanlıştı.
    Doğrusal sürüklenmede oran **tam 2**'dir ve cebirseldir: pencere
    genişliği `w`, eğim `s` için kayma `s·w`, yarım-pencere farkı `s·w/2`.

    Bu test o iddianın geri gelmesini engelliyor.
    """
    t = np.linspace(0.0, 1.0, 400)
    sekiller = {
        "dogrusal": 0.5 + 0.1 * t,
        "basamak_orta": np.where(t < 0.85, 0.50, 0.53),
        "basamak_sonda": np.where(t < 0.97, 0.50, 0.53),
        "V": 0.5 + 0.05 * np.abs(t - 0.85),
        "ters_V": 0.5 - 0.05 * np.abs(t - 0.85),
    }
    for ad, b in sekiller.items():
        d = is_settled(t, b)
        yalniz = d["yarim_pencere_farki"] >= 0.02 > d["egim_kaymasi"]
        assert not yalniz, f"{ad}: yarim-pencere TEK BASINA yakaladi — "                            f"modul basligindaki tablo guncellenmeli"
        assert d["egim_kaymasi"] >= d["yarim_pencere_farki"] - 1e-12, ad


def test_dogrusal_surukelenmede_oran_TAM_IKI() -> None:
    """Cebirsel iddia sayıyla doğrulanıyor: `s·w / (s·w/2) = 2`."""
    t = np.linspace(0.0, 1.0, 400)
    d = is_settled(t, 0.5 + 0.1 * t)
    oran = d["egim_kaymasi"] / d["yarim_pencere_farki"]
    assert oran == pytest.approx(2.0, rel=0.02), oran


def test_gecersiz_girdi_REDDEDILIYOR() -> None:
    with pytest.raises(ValueError):
        is_settled([0, 1, 2], [1, 1])
    with pytest.raises(ValueError):
        is_settled(np.linspace(0, 1, 40), np.full(40, 0.5), pencere_frac=1.5)


def test_measure_longrun_YENI_OLCUTU_kullaniyor() -> None:
    """Modülü çıkarmanın anlamı, asıl kullanıcısına **bağlanmasıdır**.

    Eski yerel mantık dosyada kalsaydı iki ölçüt yan yana yaşardı ve
    hangisinin raporlandığı belirsizleşirdi (2. turun dersi: aynı
    büyüklük iki yerde yazılıysa er geç ayrışır).
    """
    from pathlib import Path

    kod = (Path(__file__).resolve().parents[1] / "scripts" /
           "measure_longrun.py").read_text(encoding="utf-8")
    assert "from dartrift.validation.settling_time import settling_time" in kod
    assert "beta_bound_settled" in kod, "durulmusluk bayragi ciktida yok"
    # Eski yerel mantigin imzasi GERI GELMEMELI.
    assert "icinde = np.abs(bb - b_end)" not in kod, \
        "eski yerel plato mantigi geri gelmis"


# ------------------------------------- SABIT gozlenebilir (ayri tani)

def test_bastan_sona_SABIT_seri_ayri_tani_veriyor():
    """Hiç değişmeyen gözlenebilir *"duruldu"* der ama bu **boş** bir cümle.

    `beta_from_bound` bağlı parçacıkların momentumundan geliyor; hiçbir
    parçacık kaçış eşiğini geçmediyse baştan sona sabit kalır ve
    `t_durulma = t[0]` çıkar — *"β 0,01 s'de duruldu"* diye okunur, oysa
    hiçbir şey olmamıştır. `Surrogate.sabit` ile aynı kalıp.
    """
    import numpy as np

    from dartrift.validation.settling_time import is_settled, settling_time
    t = np.linspace(0.0, 1.0, 40)
    b = np.full(40, 1.583620)
    d = is_settled(t, b)
    assert d["durulmus"] is True          # teknik olarak DOGRU
    assert d["sabit"] is True             # ama BILGI TASIMIYOR
    assert d["yayilim_rel"] == 0.0
    s = settling_time(t, b)
    assert s["t_durulma_anlamli"] is False
    assert "SABİT" in s["neden"]


def test_GERCEK_platoda_sabit_bayragi_KALKMIYOR():
    """Gerçekten yerleşen bir seri `sabit` olmamalı — ayrım korunmalı."""
    import numpy as np

    from dartrift.validation.settling_time import is_settled, settling_time
    t = np.linspace(0.0, 1.0, 40)
    b = 1.0 + 0.5 * np.exp(-8.0 * t)      # duser, sonra duzlesir
    d = is_settled(t, b)
    assert d["sabit"] is False
    assert d["yayilim_rel"] > 1e-3
    s = settling_time(t, b)
    assert s["t_durulma_anlamli"] is True


def test_sabit_esigi_MIKRO_degisimi_sabit_saymiyor():
    """`1e-12` makine düzeyi; fiziksel olarak küçük ama gerçek bir
    değişim `sabit` sayılmamalı."""
    import numpy as np

    from dartrift.validation.settling_time import is_settled
    t = np.linspace(0.0, 1.0, 40)
    assert is_settled(t, 1.0 + 1e-9 * np.linspace(0, 1, 40))["sabit"] is False
    assert is_settled(t, 1.0 + 1e-15 * np.linspace(0, 1, 40))["sabit"] is True
