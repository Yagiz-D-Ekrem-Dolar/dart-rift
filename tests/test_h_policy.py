"""`h` politikası ölçümü — `Ω`'nın çelişkisini çözen ölçüm (FAZ 4.3b)."""
from __future__ import annotations

import numpy as np
import pytest

from dartrift.validation.h_policy import OMEGA_IS_UNITY_WHEN_H_FIXED, judge, neighbour_count
from dartrift.validation.kernel_margin import SUPPORT_OVER_H


def test_komsu_sayisi_kuresel_hacim() -> None:
    """`N = (4/3)π(2h)³·ρ/m` — elle hesaplanan bir değere karşı."""
    beklenen = (4.0 / 3.0) * np.pi * (SUPPORT_OVER_H * 0.05) ** 3 * 1.0 / 1e-4
    assert neighbour_count(1.0, 0.05, 1e-4) == pytest.approx(beklenen, rel=1e-14)


def test_komsu_sayisi_yogunlukla_DOGRUSAL() -> None:
    """Sabit `h` ve `m`'de `N_komşu ∝ ρ` — çelişkinin sayısal çekirdeği.

    Şok 4 kat sıkıştırırsa komşu sayısı **4 katına** çıkar. Bu bir modelleme
    tercihi değil, sabit `h`'nin doğrudan sonucudur.
    """
    tek = neighbour_count(1.0, 0.05, 1e-4)
    dort = neighbour_count(4.0, 0.05, 1e-4)
    assert dort / tek == pytest.approx(4.0, rel=1e-14)


def test_komsu_sayisi_h_kupu_ile() -> None:
    """`N ∝ h³` — `dx` taraması bu yüzden komşu sayısını **küpsel** değiştirir."""
    oran = neighbour_count(1.0, 0.10, 1e-4) / neighbour_count(1.0, 0.05, 1e-4)
    assert oran == pytest.approx(8.0, rel=1e-14)


def test_omega_sabit_h_de_BIRIMDIR() -> None:
    """Türetim gereği: `∂h/∂ρ = 0` çarpanı `Ω`'yı **tam** 1 yapar.

    Bu bir ölçüm değil, bir **cebir**. Sabiti burada sabitliyoruz ki
    ileride biri `Ω`'yı sabit `h` yolunda hesaplamaya kalkarsa test
    kırılsın — o an ADR-0041 madde 4 de kırılmış olur.
    """
    assert OMEGA_IS_UNITY_WHEN_H_FIXED is True


def test_yargi_az_nokta_ile_BELIRSIZ() -> None:
    """İki nokta bir plato gösteremez (KAYIT-030'un dersi)."""
    s = [{"r_measured": 0.25, "N_komsu": 10.0},
         {"r_measured": 0.25, "N_komsu": 20.0}]
    assert judge(s)["karar"] == "belirsiz"


def test_yargi_kapsamayan_aralikta_BELIRSIZ() -> None:
    """Çalışma noktasını içermeyen tarama **yargı kuramaz** (KAYIT-029/033)."""
    s = [{"r_measured": 0.25, "N_komsu": 10.0 * k} for k in (1, 2, 4)]
    y = judge(s, swing={"N_komsu_p01": 5.0, "N_komsu_p99": 100.0})
    assert y["karar"] == "belirsiz"
    assert y["aralik_kapsiyor"] is False


def test_yargi_kapsayan_aralikta_KARAR_VERIR() -> None:
    """Tarama salınımı kapsıyorsa ve yayılım küçükse: sabit `h` yeterli."""
    s = [{"r_measured": 0.25, "N_komsu": nk} for nk in (10.0, 15.0, 25.0, 40.0)]
    y = judge(s, swing={"N_komsu_p01": 12.0, "N_komsu_p99": 30.0})
    assert y["aralik_kapsiyor"] is True
    assert y["calisma_nokta_sayisi"] == 2
    assert y["karar"] == "sabit_h_yeterli"


def test_yargi_buyuk_yayilimda_UYARLAMALI_ISTER() -> None:
    """Plato kayıyorsa karar tersine döner — ölçüt gerçekten iki yönlü."""
    s = [{"r_measured": r, "N_komsu": nk}
         for r, nk in ((0.24, 10.0), (0.26, 15.0), (0.30, 25.0), (0.31, 40.0))]
    y = judge(s, swing={"N_komsu_p01": 12.0, "N_komsu_p99": 30.0})
    assert y["karar"] == "uyarlamali_h_gerekli"
    assert y["r_yayilim"] > 0.02


def test_yargi_ARALIK_DISI_noktalar_yargiya_GIRMEZ() -> None:
    """Çalışma aralığı dışındaki `dx` yakınsama hatası yargıyı **kirletmemeli**.

    Gerçek ölçümde `n = 40` noktası `%16,17` hata veriyor ama `N_komşu = 65`
    çalışma noktasının **çok altında**; oradaki hata `dx` yakınsamasıdır,
    komşu sayısı duyarlılığı değil. Bu test onu kanıtlıyor: aralık dışı
    nokta ne kadar sapkın olursa olsun karar değişmiyor.
    """
    ic_noktalar = [(0.250, 15.0), (0.251, 25.0)]
    y_temiz = judge([{"r_measured": r, "N_komsu": nk} for r, nk in
                     [(0.250, 10.0)] + ic_noktalar + [(0.251, 40.0)]],
                    swing={"N_komsu_p01": 12.0, "N_komsu_p99": 30.0})
    y_sapkin = judge([{"r_measured": r, "N_komsu": nk} for r, nk in
                      [(0.100, 10.0)] + ic_noktalar + [(0.400, 40.0)]],
                     swing={"N_komsu_p01": 12.0, "N_komsu_p99": 30.0})
    assert y_temiz["karar"] == y_sapkin["karar"] == "sabit_h_yeterli"
    assert y_temiz["r_yayilim"] == pytest.approx(y_sapkin["r_yayilim"])
    # Ama TUM yayilim ikisinde FARKLI -- yani veri gercekten degisti.
    assert y_sapkin["tum_yayilim"] > 10.0 * y_temiz["tum_yayilim"]


def test_n_listesi_KAPSIYOR_ve_IC_NOKTA_veriyor() -> None:
    """Elle aritmetikle iki kez yanıldım; şart artık kodda ve sınanıyor.

    İki şart **aynı anda** sağlanmalı ve birbiriyle çakışıyor: uç noktalar
    aralığın **dışında** olmalı (kapsama), iç noktalar **içinde** olmalı
    (yargı). İlk denememde üst uç `524 < 551` kaldı; ikincisinde kapsadı
    ama çalışma aralığında tek nokta kaldı.
    """
    from dartrift.validation.h_policy import n_sides_for_swing

    sw = {"N_komsu_p01": 268.2296476037067, "N_komsu_p99": 551.5188858997691}
    h = 0.03125
    ns = n_sides_for_swing(sw, h)
    nk = np.array([neighbour_count(1.0, h, 1.0 / n ** 3) for n in ns])
    assert nk.min() <= sw["N_komsu_p01"], f"kapsamiyor (alt): {nk.min()}"
    assert nk.max() >= sw["N_komsu_p99"], f"kapsamiyor (ust): {nk.max()}"
    ic = int(np.sum((nk >= sw["N_komsu_p01"]) & (nk <= sw["N_komsu_p99"])))
    assert ic >= 2, f"calisma araliginda {ic} nokta var, en az 2 gerekir"


def test_n_listesi_uretilen_liste_JUDGE_ile_UYUMLU() -> None:
    """Uçtan uca: türetilen liste `judge`'ı **belirsiz** bırakmamalı."""
    from dartrift.validation.h_policy import n_sides_for_swing

    sw = {"N_komsu_p01": 268.2296476037067, "N_komsu_p99": 551.5188858997691}
    h = 0.03125
    satirlar = [{"r_measured": 0.24, "N_komsu": neighbour_count(1.0, h, 1.0 / n ** 3)}
                for n in n_sides_for_swing(sw, h)]
    y = judge(satirlar, swing=sw)
    assert y["karar"] != "belirsiz", y


def test_n_listesi_gecersiz_salinimda_PATLIYOR() -> None:
    from dartrift.validation.h_policy import n_sides_for_swing

    with pytest.raises(ValueError):
        n_sides_for_swing({"N_komsu_p01": 500.0, "N_komsu_p99": 100.0}, 0.03125)


def test_ADR_0042_var_ve_ADR_0041_madde2_ISARETLENDI() -> None:
    """Kilitli bir karar değiştiyse iz **belgede** olmalı, yalnızca kodda değil.

    RULES.txt: kilitli karara sessiz değişiklik yok. Bu test o izin
    silinmemesini garanti ediyor — ADR-0041 §5b madde 2 hem üstü çizili
    kalmalı hem ADR-0042'ye işaret etmeli.
    """
    from pathlib import Path

    kok = Path(__file__).resolve().parents[1] / "docs" / "adr"
    yeni = kok / "ADR-0042-h-sabittir-omega-birimdir.md"
    assert yeni.is_file(), "ADR-0042 bulunamadı"
    m2 = yeni.read_text(encoding="utf-8")
    assert "KABUL EDİLDİ" in m2 and "ADR-0041" in m2

    eski = (kok / "ADR-0041-yerel-incelme-yaklasimi.md").read_text(encoding="utf-8")
    assert "ADR-0042" in eski, "ADR-0041 halefine işaret etmiyor"
    assert "~~`Ω` (grad-h) düzeltmesi **uygulanır**" in eski, \
        "madde 2 üstü çizili değil — sessiz değişiklik"
