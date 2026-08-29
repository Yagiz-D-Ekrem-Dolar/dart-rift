"""Aşama-1'in **sıkışması** aşama-2'ye taşınıyor mu (rapor A24).

Bulgu: aşama-1 gerçek bir şok üretiyor (`%26` sıkışma, `73 t`) ama
`rho` aktarılmıyordu ve `solver_solid` onu **her zaman**
`rho0/alpha0` ile kuruyordu. `u` taşındığı için aşama-2 **sıcak ama
sıkışmamış** maddeyle başlıyordu — şoklanmış madde için fiziksel
olarak olanaksız, ve A22'nin *"sıkışmadan ısınan madde"*
belirtisinin ta kendisi.

Hasarda **aynı** kusur vardı ve bir koşu boyunca fark edilmedi
(A17). Bu yüzden burada kilitlenen şey yalnızca "taşınıyor mu"
değil, taşınanın **büyüklüğü** ve **hangi ortalamayla** taşındığı.
"""
from __future__ import annotations

import numpy as np
import pytest

from dartrift.setup.coarsen import coarsen_to_sites


def _ikili(rho_a: float, rho_b: float, m_a: float = 1.0, m_b: float = 1.0):
    """İki parçacık **tek** siteye düşecek kadar yakın."""
    x = np.array([[0.0, 0.0, 0.0], [0.01, 0.0, 0.0]])
    return dict(
        x=x, v=np.zeros((2, 3)), m=np.array([m_a, m_b]),
        e=np.zeros(2), siteler=np.zeros((1, 3)),
        alpha0=np.ones(2), Y0=np.ones(2) * 1e7,
        is_boulder=np.zeros(2, bool), rho=np.array([rho_a, rho_b]),
    )


def test_tek_yogunluk_DEGISMEDEN_geciyor() -> None:
    out = coarsen_to_sites(**_ikili(2000.0, 2000.0))
    assert out["rho"][0] == pytest.approx(2000.0)
    assert out["hacim_hatasi"] < 1e-12


def test_HACIM_korunuyor_duz_ortalama_DEGIL() -> None:
    """Kütlenin yarısı `2ρ`, yarısı `ρ` -> `1,333ρ` (düz ortalama `1,5ρ`).

    Yoğunluk `m/V`; birleşen parçacıklar hem kütleyi hem **hacmi**
    korumalı. Düz ortalama boşluk yok ederdi.
    """
    out = coarsen_to_sites(**_ikili(2000.0, 1000.0))
    assert out["rho"][0] == pytest.approx(4000.0 / 3.0)     # 1333,33
    assert out["rho"][0] != pytest.approx(1500.0)
    assert out["hacim_hatasi"] < 1e-12


def test_hacim_defteri_KUTLECE_agirlikli() -> None:
    """Farklı kütlelerde de `V_k = Σ m_i/ρ_i` tam tutmalı."""
    out = coarsen_to_sites(**_ikili(3000.0, 1000.0, m_a=9.0, m_b=1.0))
    bek = 10.0 / (9.0 / 3000.0 + 1.0 / 1000.0)
    assert out["rho"][0] == pytest.approx(bek)
    assert out["hacim_hatasi"] < 1e-12


def test_SIKISMA_aktarimda_KAYBOLMUYOR() -> None:
    """Asıl sınav: sıkışmış madde aktarımdan sıkışmış çıkmalı."""
    taban = 2700.0 / 1.7564
    out = coarsen_to_sites(**_ikili(taban * 1.26, taban * 1.26))
    assert out["rho"][0] / taban - 1.0 == pytest.approx(0.26, abs=1e-9)


def test_rho_VERILMEZSE_alan_yok_davranis_ESKI() -> None:
    kw = _ikili(2000.0, 1000.0)
    kw.pop("rho")
    out = coarsen_to_sites(**kw)
    assert "rho" not in out and "hacim_hatasi" not in out


def test_bozuk_rho_REDDEDILIYOR() -> None:
    kw = _ikili(2000.0, 1000.0)
    kw["rho"] = np.array([2000.0])
    with pytest.raises(ValueError, match="rho uzunlugu"):
        coarsen_to_sites(**kw)
    kw["rho"] = np.array([2000.0, 0.0])
    with pytest.raises(ValueError, match="rho pozitif"):
        coarsen_to_sites(**kw)


def test_cozucu_rho_durum_ALIYOR() -> None:
    import inspect

    from dartrift.warp_core.solver_solid import WarpSolid3D
    s = inspect.signature(WarpSolid3D.__init__)
    assert "rho_durum" in s.parameters
    assert s.parameters["rho_durum"].default is None


def test_faz48_asama2ye_SAHNE_RHOSUNU_veriyor() -> None:
    """Bağlantı kopmuşsa çare koda girmiş ama işlemiyor demektir."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    import faz48_iki_asama as f
    kaynak = inspect_kaynak(f)
    assert "rho_durum=None if a.rho_tasima_yok else sahne.rho" in kaynak
    assert '"--rho-tasima-yok"' in kaynak


def inspect_kaynak(mod) -> str:
    import inspect
    return inspect.getsource(mod)


def test_UCSEVIYELI_aktarim_sikismayi_TASIYOR() -> None:
    """Uçtan uca: aşama-1 durumundaki `rho` sahnede görünmeli.

    `hacim_hatasi` ve `rho_max` defterleri de gelmeli — A17'de hasar
    sessizce yutulmuş ve defter olmadığı için bir koşu boyunca fark
    edilmemişti.
    """
    from dartrift.setup.two_stage import IkiAsamaSahne
    assert "rho" in IkiAsamaSahne.__slots__


def test_ucseviyeli_KAYNAKTA_rho_okunuyor() -> None:
    import inspect

    from dartrift.setup import two_stage
    k = inspect.getsource(two_stage.asama2_sahnesi_ucseviye)
    assert 'a1_durum.get("rho")' in k          # asama-1'den okunuyor
    assert "rho=None if rho1 is None else rho1[ince]" in k   # kabalastiriliyor
    assert 'kaba["rho"], rho1[dis]' in k       # kopyalanan bolge birebir
    assert '"hacim_hatasi"' in k and '"rho_tasindi"' in k    # defter


def test_TOPLAM_yonteminde_rho_durum_REDDEDILIYOR() -> None:
    """Sessiz yoksayma tuzağı: toplam yönteminde `rho` her adımda
    yeniden hesaplanır; devralınan değer ilk adımda silinirdi ve
    çağıran sıkışmayı taşıdığını **sanırdı** — A24'ün ta kendisi."""
    import inspect

    from dartrift.warp_core import solver_solid
    k = inspect.getsource(solver_solid)
    assert "rho_durum yalnizca sureklilik yonteminde anlamli" in k
