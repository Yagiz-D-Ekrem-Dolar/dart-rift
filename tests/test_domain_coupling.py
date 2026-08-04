"""C-1 ara değerleyicisinin kendi denetimi (küçük kafeslerde, hızlı).

Ölçümün kendisi büyük kafes ister; burada sınanan şey **aracın doğruluğu**:
bozuk bir ara değerleyici, C ile A′ arasındaki kıyası sessizce çürütürdü.
"""
from __future__ import annotations

import numpy as np
import pytest

from dartrift.validation.domain_coupling import (RHO0, measure_coupling_error,
                                                 sph_interpolate)

HALF, S, HOS = 4.0, 1.0, 1.3


def _kafes(spacing: float, half: float) -> np.ndarray:
    n = int(np.floor(half / spacing))
    e = np.arange(-n, n + 1) * spacing
    xx, yy, zz = np.meshgrid(e, e, e, indexing="ij")
    return np.column_stack([xx.ravel(), yy.ravel(), zz.ravel()])


def test_sabit_alan_shepard_ile_TAM() -> None:
    """Shepard normalizasyonu sıfırıncı mertebeyi **tanım gereği** düzeltir.

    Bu bir başarı değil, bir **kalibrasyon**: aracın Shepard kolunun doğru
    kurulduğunu gösterir. Düzeltmiyorsa uygulama hatalıdır.
    """
    x = _kafes(S, HALF)
    h = HOS * S
    m = np.full(len(x), RHO0 * S ** 3)
    rho = np.full(len(x), RHO0)
    ic = np.all(np.abs(x) < HALF - 2.0 * h, axis=1)
    d = sph_interpolate(x[ic], x, m, rho, np.ones(len(x)), h)
    f_sh = d["f"] / d["partition_of_unity"]
    assert np.allclose(f_sh, 1.0, atol=1e-12), np.max(np.abs(f_sh - 1.0))


def test_ham_toplam_birim_bolunmesi_acigini_gosteriyor() -> None:
    """BOŞLUK KONTROLÜ: ham toplam **tam 1 olmamalı**.

    Tam 1 çıkarsa Shepard kolu bir şey düzeltmiyor demektir ve yukarıdaki
    test boş bir doğrudur. Ölçülen (h/dx = 1,3): açık ~%0,95.
    """
    x = _kafes(S, HALF)
    h = HOS * S
    m = np.full(len(x), RHO0 * S ** 3)
    rho = np.full(len(x), RHO0)
    ic = np.all(np.abs(x) < HALF - 2.0 * h, axis=1)
    pu = sph_interpolate(x[ic], x, m, rho, np.ones(len(x)), h)["partition_of_unity"]
    sapma = float(np.max(np.abs(pu - 1.0)))
    assert sapma > 1.0e-4, sapma
    assert sapma < 5.0e-2, sapma


def test_dogrusal_alan_shepard_ile_makine_hassasiyetinde() -> None:
    """Shepard + **simetrik** komşuluk ⇒ birinci mertebe de tam olmalı.

    Simetrik bir kafeste `Σ w·(x_j − x_i) = 0` olduğu için doğrusal alan
    Shepard'dan sonra hatasız gelir. Gelmiyorsa çekirdek ya da toplam bozuktur.
    """
    x = _kafes(S, HALF)
    h = HOS * S
    m = np.full(len(x), RHO0 * S ** 3)
    rho = np.full(len(x), RHO0)
    ic = np.all(np.abs(x) < HALF - 2.0 * h, axis=1)
    d = sph_interpolate(x[ic], x, m, rho, x[:, 0].copy(), h)
    f_sh = d["f"] / d["partition_of_unity"]
    assert np.allclose(f_sh, x[ic, 0], atol=1e-10), np.max(
        np.abs(f_sh - x[ic, 0]))


def test_kaynak_boyu_uyusmazligi_reddediliyor() -> None:
    x = _kafes(S, HALF)
    with pytest.raises(ValueError, match="kaynak dizilerinin boyu"):
        sph_interpolate(x, x, np.ones(len(x)), np.ones(len(x)),
                        np.ones(len(x) - 1), 1.0)


def test_lam_bir_altinda_reddediliyor() -> None:
    with pytest.raises(ValueError, match="lam >= 1"):
        measure_coupling_error(lam=0.5, half=HALF)


def test_hedef_bolgesi_bos_kalirsa_hata() -> None:
    """Pay tüm kafesi yerse SESSİZCE ölçme, HATA ver."""
    with pytest.raises(ValueError, match="iç bölge çok küçük"):
        measure_coupling_error(lam=2.0, spacing_coarse=1.0,
                               h_over_spacing=1.3, half=2.0)


def test_iki_yon_de_raporlaniyor() -> None:
    r = measure_coupling_error(lam=2.0, half=HALF)
    for yon in ("fine_to_coarse", "coarse_to_fine"):
        b = r[yon]
        assert b["n_targets"] > 20, (yon, b)
        assert b["shepard_dropped"] == 0, (yon, b)
        for alan in ("constant", "linear", "quadratic"):
            assert f"{alan}_max_err" in b
            assert f"{alan}_max_err_shepard" in b


def test_h_kaynagin_cozunurlugunden_geliyor() -> None:
    """Hayaleti üreten alan **kendi** çekirdeğiyle ara değerler."""
    r = measure_coupling_error(lam=2.0, spacing_coarse=1.0,
                               h_over_spacing=HOS, half=HALF)
    assert r["fine_to_coarse"]["h"] == pytest.approx(HOS * 0.5)
    assert r["coarse_to_fine"]["h"] == pytest.approx(HOS * 1.0)
