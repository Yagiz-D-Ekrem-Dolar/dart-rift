"""A′'nın DART sahnesine bağlanması — `refine_scene` (GPU gerekmez)."""
from __future__ import annotations

import numpy as np
import pytest

from dartrift.setup.refine import refine_scene
from dartrift.setup.scene import build_scene

KW = dict(radius=82.0, bulk_density=1800.0, root_seed=20260801,
          model_class="M1", f_boulder=0.25, q=3.0, n_impactor=800,
          r_min=14.0, r_max=42.0, device="cpu")


@pytest.fixture(scope="module")
def sahneler():
    return build_scene(spacing=7.0, **KW), build_scene(spacing=3.5, **KW)


def test_incelme_TASARRUF_sagliyor(sahneler) -> None:
    """A′'nın varlık nedeni: her yeri inceltmekten **ucuz** olmalı."""
    kaba, ince = sahneler
    rs = refine_scene(kaba, ince, r_ince=25.0)
    d = rs.diagnostics
    assert d["tasarruf"] > 3.0, d
    assert d["n_toplam"] < d["n_tumu_ince"]


def test_h_PARCACIK_BASINA_ve_iki_degerli(sahneler) -> None:
    kaba, ince = sahneler
    rs = refine_scene(kaba, ince, r_ince=25.0)
    assert rs.h.shape == (rs.n,)
    assert set(np.unique(rs.h)) == {14.0, 7.0}
    # Ince bolge ve mermi KUCUK h; kaba bolge BUYUK h.
    assert np.all(rs.h[rs.is_fine] == 7.0)
    assert np.all(rs.h[~rs.is_fine] == 14.0)


def test_MERMI_her_zaman_ince_sahneden(sahneler) -> None:
    """A′'nın amacı mermiyi çözmek — kaba mermi kullanılmaz."""
    kaba, ince = sahneler
    rs = refine_scene(kaba, ince, r_ince=25.0)
    assert int(rs.is_impactor.sum()) == int(ince.is_impactor.sum())
    assert np.all(rs.h[rs.is_impactor] == 2.0 * ince.spacing)
    # Ve mermi momentumu ince sahneninkiyle AYNI.
    assert np.allclose(rs.impactor_momentum, ince.impactor_momentum)


def test_kutle_sapmasi_KUCUK_ve_RAPORLANIYOR(sahneler) -> None:
    """İki kafes aynı küreyi farklı döşer — gizlenmez, ölçülür."""
    kaba, ince = sahneler
    rs = refine_scene(kaba, ince, r_ince=25.0)
    assert rs.diagnostics["hedef_kutle_sapmasi"] < 5.0e-3


def test_ince_bolge_CARPMA_NOKTASI_cevresinde(sahneler) -> None:
    """İnce parçacıklar gerçekten çarpma noktasının yakınında mı?"""
    kaba, ince = sahneler
    r_ince = 25.0
    rs = refine_scene(kaba, ince, r_ince=r_ince)
    hedef_ince = rs.is_fine & ~rs.is_impactor
    d = np.linalg.norm(rs.x[hedef_ince] - rs.impact_point[None, :], axis=1)
    assert float(d.max()) < r_ince
    hedef_kaba = ~rs.is_fine
    d2 = np.linalg.norm(rs.x[hedef_kaba] - rs.impact_point[None, :], axis=1)
    assert float(d2.min()) >= r_ince


def test_r_ince_BUYUDUKCE_tasarruf_azaliyor(sahneler) -> None:
    """KAYIT-033'ün formülü: kazanç ince kesirle **ağırlıklı**.

    Bu bir pozitif kontroldür: ölçüt gerçekten geometriye tepki veriyor mu?
    """
    kaba, ince = sahneler
    t = [refine_scene(kaba, ince, r_ince=r).diagnostics["tasarruf"]
         for r in (20.0, 40.0, 60.0)]
    assert t[0] > t[1] > t[2], t


def test_gecersiz_girdiler_REDDEDILIYOR(sahneler) -> None:
    kaba, ince = sahneler
    with pytest.raises(ValueError):
        refine_scene(kaba, ince, r_ince=0.0)
    with pytest.raises(ValueError):
        refine_scene(ince, kaba, r_ince=25.0)      # ters sira
    with pytest.raises(ValueError):
        refine_scene(kaba, ince, r_ince=1.0e-3)    # ince bolge bos
    with pytest.raises(ValueError):
        refine_scene(kaba, ince, r_ince=1.0e4)     # kaba bolge bos


def test_FARKLI_TOHUM_reddediliyor() -> None:
    """İki sahne aynı çarpma noktasını görmüyorsa birleştirme anlamsız."""
    kaba = build_scene(spacing=7.0, **KW)
    kw2 = dict(KW); kw2["aim"] = (1.0, 0.0, 0.0)
    ince = build_scene(spacing=3.5, **kw2)
    with pytest.raises(ValueError, match="çarpma noktası"):
        refine_scene(kaba, ince, r_ince=25.0)
