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


def test_dikis_kalitesi_OLCULUYOR(sahneler) -> None:
    """Dikişte parçacıklar ince aralıktan **daha yakın** olabilir.

    Ölçüldü: `2,2824 m`, yani ince aralığın (`3,5`) `%65`'i. Bu bir
    kurgu değil — iki farklı aralıklı kafes küresel bir sınırda
    buluşunca kaçınılmaz. Gizlenmiyor, raporlanıyor.
    """
    kaba, ince = sahneler
    d = refine_scene(kaba, ince, r_ince=25.0).diagnostics["dikis"]
    assert d["n_kusak"] > 100
    assert 0.5 < d["en_yakin_oran"] < 1.0, d
    # Ince bolgenin KENDI icinde boyle bir yakinlasma YOK -- dikise ozgu.
    assert d["en_yakin"] < ince.spacing


def test_dikis_orani_YARICAPTAN_bagimsiz(sahneler) -> None:
    """Aynı oran her `r_ince`'de çıkıyorsa bu **sistematik** bir özellik.

    Rastgele bir sınır artefaktı olsaydı yarıçapla oynardı. Üç yarıçapta
    da `2,2824` çıkması, iki FCC kafesinin iç içe geçme biçiminden
    geldiğini gösteriyor.
    """
    kaba, ince = sahneler
    o = [refine_scene(kaba, ince, r_ince=r).diagnostics["dikis_en_yakin_oran"]
         for r in (15.0, 25.0, 40.0)]
    assert max(o) - min(o) < 1e-9, o


def test_dikis_TEHLIKELI_durumu_yakalar() -> None:
    """Pozitif kontrol: ölçüt gerçekten küçük bir oran raporlayabiliyor mu?

    Bir ölçütün *"iyi"* dediği her yerde iyi olması, ölçütün **boş**
    olduğu anlamına da gelebilir. Elle çakışan bir çift konuyor.
    """
    from dartrift.setup.refine import _dikis_kalitesi

    x = np.array([[25.0, 0.0, 0.0], [25.02, 0.0, 0.0],
                  [22.0, 0.0, 0.0], [28.0, 0.0, 0.0]])
    d = _dikis_kalitesi(x, np.zeros(3), 25.0, s_kaba=7.0, s_ince=3.5)
    assert d["en_yakin"] == pytest.approx(0.02, abs=1e-9)
    assert d["en_yakin_oran"] < 0.5, "tehlike esigi altinda raporlanmali"


def test_dikis_BOS_kusakta_olculemedi_diyor(sahneler) -> None:
    """Sayı uydurmaktansa "ölçülemedi" demek doğrudur."""
    from dartrift.setup.refine import _dikis_kalitesi

    d = _dikis_kalitesi(np.zeros((0, 3)), np.zeros(3), 25.0, 7.0, 3.5)
    assert d["n_kusak"] == 0
    assert np.isnan(d["en_yakin_oran"])
    assert "ölçülemedi" in d["not"]


def test_refine_diagnostics_JSON_serilestirilebilir(sahneler) -> None:
    """Tanı sözlüğü koşu çıktısına yazılıyor — numpy tipi sızmamalı."""
    import json

    kaba, ince = sahneler
    d = refine_scene(kaba, ince, r_ince=25.0).diagnostics
    json.dumps(d)
    assert d["dikis"]["n_kusak"] > 0


# --------------------------------------------- YEREL kurulum (ADR-0043)

def _mesh():
    from dartrift.setup.scene import _build_mesh

    return _build_mesh("icosphere", radius=82.0, subdiv=4)


def test_YEREL_kurulum_YUKSEK_lam_da_calisiyor(sahneler) -> None:
    """`refine_scene` `λ=19`'da **kurulamıyordu**; yerel kurulum kuruyor.

    Ölçüldü (`R = 82 m`, FCC): tam ince sahne `λ=19`'da **65 314 837**
    parçacık ve **19,6 GB**. Oysa gereken `r_iç = 3 m` içinde `~1500`.
    Yani `%99,998`'i kurulup atılıyordu.

    Yerel kurulum ölçüldü: `N = 11 871`, **0,5 s**.
    """
    from dartrift.setup.refine import refine_scene_local

    kaba, _ = sahneler
    rs = refine_scene_local(kaba, _mesh(), r_ince=3.0, lam=19.0)
    assert rs.spacing_fine == pytest.approx(7.0 / 19.0)
    # A1 = mermi capi / s_ince -- ESIGI GECIYOR
    assert 0.751 / rs.spacing_fine > 2.0
    assert 500 < rs.diagnostics["n_ince"] < 5000, rs.diagnostics["n_ince"]
    assert rs.n < 20000, rs.n
    assert rs.diagnostics["yerel_kurulum"] is True


def test_YEREL_kurulum_kutle_sapmasi_KUCUK(sahneler) -> None:
    """İnce bölge kaba bölgeyi değiştiriyor; toplam kütle korunmalı."""
    from dartrift.setup.refine import refine_scene_local

    kaba, _ = sahneler
    for lam, r in ((2.0, 25.0), (6.0, 6.0), (19.0, 3.0)):
        d = refine_scene_local(kaba, _mesh(), r_ince=r,
                               lam=lam).diagnostics
        assert d["hedef_kutle_sapmasi"] < 1.0e-3, (lam, r,
                                                   d["hedef_kutle_sapmasi"])


def test_YEREL_ve_TAM_kurulum_AYNI_mertebede(sahneler) -> None:
    """Boşluk kontrolü: `λ=2`'de iki yol benzer sonuç vermeli.

    Birebir aynı olmaz — kafes başlangıcı farklı — ama `%10` içinde
    olmalı. Olmazsa yerel kurulumun geometrisi bozuk demektir.
    """
    from dartrift.setup.refine import refine_scene_local

    kaba, ince = sahneler
    tam = refine_scene(kaba, ince, r_ince=25.0).diagnostics["n_ince"]
    yerel = refine_scene_local(kaba, _mesh(), r_ince=25.0,
                               lam=2.0).diagnostics["n_ince"]
    assert abs(yerel - tam) / tam < 0.10, (tam, yerel)


def test_YEREL_kurulum_KAYA_BLOKLARINI_koruyor(sahneler) -> None:
    """`α₀`/`Y₀` en yakın kaba parçacıktan alınıyor — blok yapısı silinmiyor.

    Tekdüze matris değeri vermek `f_boulder`'ı yok ederdi ve o, çıkarımın
    üç parametresinden biri.
    """
    from dartrift.setup.refine import refine_scene_local

    kaba, _ = sahneler
    rs = refine_scene_local(kaba, _mesh(), r_ince=25.0, lam=2.0)
    ince_hedef = rs.is_fine & ~rs.is_impactor
    # Ince bolgede EN AZ IKI farkli Y0 olmali (matris + blok).
    assert len(np.unique(rs.Y0[ince_hedef])) >= 2, "blok yapisi silinmis"
    # Ve degerler kaba sahnede GERCEKTEN var olanlardan olmali.
    assert set(np.unique(rs.Y0[ince_hedef])) <= set(np.unique(kaba.Y0))


def test_YEREL_kurulum_gecersiz_girdiler(sahneler) -> None:
    from dartrift.setup.refine import refine_scene_local

    kaba, _ = sahneler
    m = _mesh()
    with pytest.raises(ValueError):
        refine_scene_local(kaba, m, r_ince=3.0, lam=1.0)      # lam <= 1
    with pytest.raises(ValueError):
        refine_scene_local(kaba, m, r_ince=0.0, lam=19.0)     # r_ince <= 0
    # BUYUK r_ince: koruma KAFESTEN ONCE gelmeli.
    #
    # Ilk surumde dogrulama kafes kurulduktan SONRAydi ve numpy
    # "412 TiB ayrilamiyor" diyordu -- anlasilmaz ve gec. Bu test onu
    # yakaladi; simdi anlasilir bir ValueError geliyor.
    with pytest.raises(ValueError, match="hedef çapından"):
        refine_scene_local(kaba, m, r_ince=1.0e4, lam=19.0)
    # Cap icinde ama kafes yine de cok buyuk olacaksa da erken uyari.
    with pytest.raises(ValueError, match="çok büyük"):
        refine_scene_local(kaba, m, r_ince=160.0, lam=200.0)


def test_dikis_kalitesi_parcali_tek_blokla_AYNI():
    """Bellek koruması sonucu **değiştirmemeli**.

    `_dikis_kalitesi` `n×n×3` diziyi tek seferde kuruyordu ve yorumu
    *"kuşak küçük (yüzlerce)"* diyordu. `λ=19, r_ince=9 m`'de kuşakta
    `40 597` parçacık var → `36,8 GiB` → patladı. Parçalı sürüm aynı
    sayıyı vermeli, yoksa düzeltme sessizce ölçümü değiştirir.
    """
    import numpy as np

    from dartrift.setup.refine import _dikis_kalitesi
    rng = np.random.default_rng(4343)
    x = rng.uniform(-30.0, 30.0, size=(900, 3))
    a = _dikis_kalitesi(x, np.zeros(3), 20.0, 7.0, 3.5)
    # Tek blok zorlanan referans: dogrudan tam matris (900 kucuk, guvenli).
    kus = np.abs(np.linalg.norm(x, axis=1) - 20.0) < 7.0
    xk = x[kus]
    D = np.linalg.norm(xk[:, None, :] - xk[None, :, :], axis=2)
    np.fill_diagonal(D, np.inf)
    assert a["en_yakin"] == float(D.min())
    assert a["n_kusak"] == int(kus.sum())


# ------------------------- UC SEVIYELI sahne (ADR-0043 §4f)

def _uc_sahne(r1=6.0, lam1=6.0, r2=25.0, lam2=2.0):
    import numpy as np

    from dartrift.setup.refine import refine_scene_ucseviye
    from dartrift.setup.scene import _build_mesh, build_scene
    kaba = build_scene(spacing=14.0, device="cpu", radius=82.0,
                       bulk_density=1800.0, root_seed=20260801,
                       model_class="M1", f_boulder=0.25, q=3.0,
                       n_impactor=200, r_min=14.0, r_max=42.0)
    mesh = _build_mesh("icosphere", radius=82.0, subdiv=3)
    return kaba, refine_scene_ucseviye(kaba, mesh, r1=r1, lam1=lam1,
                                       r2=r2, lam2=lam2)


def test_ucseviye_UC_AYRI_h_seviyesi_var():
    """Şemanın tanımı: üç çözünürlük. İkiye düşerse `%69` kaybı geri gelir."""
    import numpy as np
    _, rs = _uc_sahne()
    h = np.unique(np.round(np.asarray(rs.h), 9))
    assert len(h) == 3, f"3 seviye bekleniyordu, {len(h)} var: {h}"
    d = rs.diagnostics
    assert h.min() == pytest.approx(2.0 * d["s1"])
    assert d["s1"] < d["s2"] < rs.spacing_coarse


def test_ucseviye_ORTA_seviye_asama2_ile_AYNI_aralik():
    """Aktarımın birebir kopyalanabilmesi **buna** bağlı."""
    import numpy as np

    from dartrift.setup.refine import refine_scene_local
    from dartrift.setup.scene import _build_mesh, build_scene
    kaba, rs = _uc_sahne()
    mesh = _build_mesh("icosphere", radius=82.0, subdiv=3)
    a2 = refine_scene_local(kaba, mesh, r_ince=25.0, lam=2.0)
    assert rs.diagnostics["s2"] == pytest.approx(a2.spacing_fine)


def test_ucseviye_KUTLE_kaba_sahneyle_tutuyor():
    import numpy as np
    kaba, rs = _uc_sahne()
    assert rs.diagnostics["hedef_kutle_sapmasi"] < 5.0e-3
    imp = np.asarray(rs.is_impactor, bool)
    assert float(rs.m[imp].sum()) == pytest.approx(
        float(np.asarray(kaba.m)[np.asarray(kaba.is_impactor, bool)].sum()),
        rel=1e-12)


def test_ucseviye_MERMI_en_ince_h_aliyor():
    """`A1` mermiye bağlı; mermi orta seviyede kalırsa çözülmez."""
    import numpy as np
    _, rs = _uc_sahne()
    imp = np.asarray(rs.is_impactor, bool)
    assert np.all(rs.h[imp] == pytest.approx(2.0 * rs.diagnostics["s1"]))


def test_ucseviye_is_fine_CEKIRDEK_ve_MERMI():
    """Aktarılacak küme tam olarak bu; yanlışsa momentum yine kaybolur."""
    import numpy as np
    _, rs = _uc_sahne()
    ince = np.asarray(rs.is_fine, bool)
    imp = np.asarray(rs.is_impactor, bool)
    assert np.all(ince[imp]), "mermi ince kumede olmali"
    # Ince olan HER parcacik en ince `h`ye sahip olmali.
    assert np.all(rs.h[ince] == pytest.approx(2.0 * rs.diagnostics["s1"]))
    # Ince OLMAYAN hicbiri en ince `h`ye sahip OLMAMALI.
    assert not np.any(rs.h[~ince] == pytest.approx(2.0 * rs.diagnostics["s1"]))


@pytest.mark.parametrize("kw,mesaj", [
    (dict(r1=30.0, r2=25.0), "0 < r1 < r2"),
    (dict(r1=0.0), "0 < r1 < r2"),
    (dict(lam1=2.0, lam2=2.0), "lam1 > lam2"),
    (dict(lam1=1.5, lam2=2.0), "lam1 > lam2"),
])
def test_ucseviye_gecersiz_girdiler(kw, mesaj):
    with pytest.raises(ValueError, match=mesaj):
        _uc_sahne(**kw)
