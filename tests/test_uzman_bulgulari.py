"""Uzman incelemesinde bulunan bes kusur — her biri icin bir sinav.

NEDEN VAR. Bes kusurun besi de **cikis kodu 0** veriyordu ve mevcut
takim hicbirini gormuyordu. Deponun tekrar eden sinifi budur: sayi
uretilir, sayi yanlistir. Bu dosya o besini kilitler.

Kaynak: `docs/FAZ4-SIKINTI-RAPORU.md` A46-A50.
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[1]


# --- A46: ensemble sahnesi M0'a dusuyordu ------------------------------

def test_surucu_sahne_tabani_gonderiyor():
    """`sahne_taban=None` YASAK — `build_scene` varsayilani `M0`.

    `M0` dalinda `boulders = None`; `f_boulder` ve `boulder_alpha0`
    SESSIZCE yoksayilir. Uc cikarim ekseninden ikisi sahneye ulasmaz.
    """
    m = (REPO / "scripts" / "faz5_ensemble_merdiven.py").read_text(
        encoding="utf-8")
    assert not re.search(r"sahne_taban\s*=\s*None", m), (
        "surucu sahne_taban=None gonderiyor -> sahne M0 olur, bloklar "
        "kurulmaz, cikarimin iki ekseni olur"
    )
    assert re.search(r"sahne_taban\s*=\s*\{\*\*SAHNE", m), (
        "surucu SAHNE'yi taban olarak gondermeli"
    )


def test_farkli_theta_farkli_sahne_uretir():
    """Iki blok parametresi degisince sahne DEGISMELI.

    Olculen kusur: `(1,05; 0,10)` ve `(1,30; 0,40)` noktalari
    **birebir ayni** `x, v, m, alpha0, Y0` dizilerini uretiyordu.
    """
    import sys

    sys.path.insert(0, str(REPO / "scripts"))
    from dartrift.inference.forward import sahne_parametreleri
    from dartrift.setup.scene import build_scene
    from faz44_dart_yakinsama import SAHNE

    assert SAHNE.get("model_class") == "M1", "SAHNE M1 olmali"

    ort = dict(radius=20.0, spacing=4.0, subdiv=2, root_seed=7)

    def kur(th):
        kw = sahne_parametreleri(th, {k: v for k, v in SAHNE.items()
                                      if k not in ort and k != "n_impactor"})
        return build_scene(**{**ort, **{k: v for k, v in kw.items()
                                        if k not in ort}})

    A = kur([1.05, 1.0e4, 0.10])
    B = kur([1.30, 1.0e4, 0.40])
    assert not np.array_equal(A.alpha0, B.alpha0), (
        "blok alpha0 ve blok kesri degisti ama sahne AYNI kaldi"
    )
    # blok malzemesi gercekten var mi
    assert np.isclose(np.asarray(A.alpha0), 1.05).any(), "blok yerlesmemis"
    assert np.isclose(np.asarray(B.alpha0), 1.30).any(), "blok yerlesmemis"


# --- A47: iki beta defteri ayni sey degil -------------------------------

def test_iki_defter_ayrisiyor_ve_cikarima_dogru_olan_gidiyor():
    """Momentum korunumu kacis TANIMINI dogrulamaz.

    Ayni sentetik durumda `R` defteri ve `2R` hesabi FARKLI beta
    veriyor, ve **ikisi de sifir artikla kapaniyor**.
    """
    from dartrift.observables.momentum_defteri import momentum_defteri
    from dartrift.observables.momentum_transfer import (
        escape_speed,
        momentum_transfer,
    )

    R, rho = 82.0, 1800.0
    M = 4.0 / 3.0 * np.pi * R**3 * rho
    m_imp, v_imp = 579.4, 6144.9
    p_imp = m_imp * v_imp
    ehat = np.array([0.0, 0.0, -1.0])

    x = np.array([[0.0, 0.0, R * 1.05], [0.0, 0.0, R * 1.02], [0.0, 0.0, 0.0]])
    m = np.array([m_imp, 500.0, M - 500.0])
    vz = np.array([800.0, 2000.0, 0.0])
    vz[2] = (m_imp * -v_imp - m[0] * vz[0] - m[1] * vz[1]) / m[2]
    v = np.zeros((3, 3))
    v[:, 2] = vz
    f = np.array([1.0, 0.0, 0.0])

    v_esc = escape_speed(M, R)
    d = momentum_defteri(x, v, m, mermi_kesri=f, R=R, v_esc=v_esc,
                         ehat=ehat, p_imp=p_imp)
    mt = momentum_transfer(x, v, m, impactor_momentum=p_imp * ehat,
                           center=np.zeros(3), target_mass=M,
                           target_radius=R, control_radius=2.0 * R,
                           speed_threshold=v_esc)

    assert abs(d["artik"]) < 1e-6, "defter kapanmali"
    assert abs(float(mt.momentum_closure)) < 1e-6, "ileri yol da kapanmali"
    # ISTE ASIL NOKTA: ikisi de kapali, yine de AYRISIYORLAR
    assert abs(d["beta_hedef"] - float(mt.beta)) > 0.1, (
        "iki defter ayrismali; ayrismiyorsa bu sinav anlamsiz"
    )
    # 2R yuzeyi ejektayi HIC gormuyor
    assert int(mt.n_ejekta if hasattr(mt, "n_ejekta") else mt.n_ejecta) == 0


def test_cikarim_gozlenebiliri_defterden_geliyor():
    m = (REPO / "src" / "dartrift" / "inference" / "forward.py").read_text(
        encoding="utf-8")
    assert 'float(_def["beta_hedef"])' in m, (
        "y[0] defterin beta_hedef'i olmali; `mt.beta` (2R yuzeyi) "
        "410 m/s'den yavas hicbir ejektayi goremiyor"
    )


# --- A48: sok kapisi mermiyi maskelemiyordu -----------------------------

def test_sok_kapisi_mermiyi_maskeliyor():
    m = (REPO / "src" / "dartrift" / "inference" / "forward.py").read_text(
        encoding="utf-8")
    blok = m[m.index("if sok_yargisi:"):][:700]
    assert "is_impactor" in blok, (
        "sok kapisi mermiyi maskelemiyor: aliminyum mermi (alpha0=1) "
        "carpmada cok sikisir ve kapiyi TEK BASINA gecirebilir"
    )


def test_yalniz_mermi_sikisirsa_kapi_gecmemeli():
    """Hedef gevsek, mermi cok sikismis -> kapi GECMEMELI."""
    from dartrift.observables.sok import sok_gecti

    # hedef: hic sikismamis (rho = rho0/alpha0)
    rho_h = np.full(100, 2700.0 / 1.7564)
    a0_h = np.full(100, 1.7564)
    # mermi: cok sikismis
    rho_m = np.full(5, 5000.0)
    a0_m = np.ones(5)

    assert not sok_gecti(rho_h, a0_h), "hedef tek basina gecmemeli"
    # maskesiz cagri (ESKI davranis) gecerdi:
    assert sok_gecti(np.concatenate([rho_h, rho_m]),
                     np.concatenate([a0_h, a0_m])), (
        "bu sinavin anlamli olmasi icin maskesiz cagrinin GECMESI gerek"
    )


# --- A49: durum dosyalari birbirinin uzerine yaziyordu ------------------

def test_durum_adi_theta_ile_degisiyor():
    from dartrift.inference.forward import _durum_adi

    a = _durum_adi(0, [1.05, 1.0e4, 0.10])
    b = _durum_adi(0, [1.30, 1.0e4, 0.40])
    assert a != b, (
        "ayni yigin indeksiyle iki farkli theta AYNI dosyaya yaziyor; "
        "surucu her noktayi ayri cagriyla kosturdugu icin i HEP 0"
    )
    assert _durum_adi(0, [1.05, 1.0e4, 0.10]) == a, "ad kararli olmali"


def test_durum_adi_kaynakta_kullaniliyor():
    m = (REPO / "src" / "dartrift" / "inference" / "forward.py").read_text(
        encoding="utf-8")
    assert not re.search(r'f"nokta_\{i:04d\}\.npz"', m), (
        "eski cakisan ad hala kullaniliyor"
    )


# --- A50: kaydedilen durum tani icin eksikti ----------------------------

@pytest.mark.parametrize("alan", ["alpha", "P", "S", "D", "h"])
def test_durum_kaydi_tani_alanlarini_tasiyor(alan):
    m = (REPO / "src" / "dartrift" / "inference" / "forward.py").read_text(
        encoding="utf-8")
    blok = m[m.index("np.savez_compressed("):][:900]
    assert f'"{alan}"' in blok, (
        f"`{alan}` kaydedilmiyor: bosalma/cekme/hasar sonradan "
        f"incelenemez"
    )


def test_cozucu_h_diziyi_disari_veriyor():
    """`h` PARCACIK BASINA verilmeli; `self.h` skaler ozet."""
    m = (REPO / "src" / "dartrift" / "warp_core" / "solver_solid.py").read_text(
        encoding="utf-8")
    blok = m[m.index("def state_numpy"):][:1400]
    assert '"h": self.h_arr.numpy()' in blok, (
        "state_numpy `h_arr` (dizi) vermeli, `self.h` (skaler) degil"
    )


# --- kimlik: theta + commit + fizik ozeti -------------------------------

def test_fizik_ozeti_yapilandirmayi_ayirt_ediyor():
    """Aynı `θ`, farklı fizik → farklı özet.

    `surum` (commit) bunu yakalamaz: aynı commit'te farklı
    bayraklarla koşulabilir.
    """
    from dartrift.inference.forward import _fizik_ozeti

    taban = {"radius": 82.0}
    a = _fizik_ozeti(taban, "mat", ("48:2.8",), 7.0, 0.2)
    assert a == _fizik_ozeti(taban, "mat", ("48:2.8",), 7.0, 0.2), "kararsiz"
    assert a != _fizik_ozeti(taban, "mat", ("48:1.4",), 7.0, 0.2), "merdiven"
    assert a != _fizik_ozeti(taban, "mat", ("48:2.8",), 7.0, 0.1), "t_end"
    assert a != _fizik_ozeti(taban, "mat2", ("48:2.8",), 7.0, 0.2), "malzeme"
    assert a != _fizik_ozeti({"radius": 80.0}, "mat", ("48:2.8",), 7.0, 0.2), \
        "sahne"


def test_durum_kaydi_kimlik_alanlarini_tasiyor():
    m = (REPO / "src" / "dartrift" / "inference" / "forward.py").read_text(
        encoding="utf-8")
    blok = m[m.index("np.savez_compressed("):][:2200]
    for alan in ("theta", "surum", "fizik_ozeti"):
        assert f"{alan}=" in blok, f"`{alan}` kaydedilmiyor"


def test_surucu_surumu_ileri_modele_gonderiyor():
    m = (REPO / "scripts" / "faz5_ensemble_merdiven.py").read_text(
        encoding="utf-8")
    # Bicime bagli olmayan sinav: `_ileri` govdesinde `surum=surum`
    # gecmeli. Once "surum=surum)[0]" araniyordu ve AV bayragi
    # eklenince kirildi -- test kusuru, kod kusuru degildi.
    govde = m[m.index("def _ileri("):]
    govde = govde[:govde.index("return y")]
    assert "surum=surum" in govde, (
        "surucu commit'i ileri modele gecirmiyor; npz provenance bos kalir"
    )


# --- A56: yapay viskozite ensemble'a gecmiyordu ------------------------

def test_ensemble_yapay_viskoziteyi_gecirebiliyor():
    """`alpha_av` `RefParams` içinde sabit `1,0` kalıyordu.

    A53 ölçtü: `alpha_av` kaçan kütleyi `132` kat, kütle ağırlıklı
    hızı `3 188` kat değiştiriyor. Yani ensemble, mekanizmanın en
    güçlü kontrol parametresini SABIT tutuyordu.
    """
    import inspect

    from dartrift.inference.forward import ileri_kosu_merdiven

    imza = inspect.signature(ileri_kosu_merdiven).parameters
    assert "alpha_av" in imza and "beta_av" in imza
    assert imza["alpha_av"].default == 1.0, "uretim varsayilani degismemeli"

    m = (REPO / "src" / "dartrift" / "inference" / "forward.py").read_text(
        encoding="utf-8")
    blok = m[m.index("def ileri_kosu_merdiven"):]
    assert "RefParams(cfl=0.25, alpha_av=alpha_av, beta_av=beta_av)" in blok, (
        "merdiven yolu AV'yi cozucuye gecirmiyor"
    )


def test_surucu_AV_bayragini_tasiyor():
    m = (REPO / "scripts" / "faz5_ensemble_merdiven.py").read_text(
        encoding="utf-8")
    assert '"--alpha-av"' in m and '"--beta-av"' in m
    assert "alpha_av=a.alpha_av" in m, "bayrak ileri modele gecmiyor"


def test_fizik_ozeti_AV_ile_degisiyor():
    """Aynı `θ`, farklı AV → farklı özet. Yoksa iki koşu karışır."""
    from dartrift.inference.forward import _fizik_ozeti

    taban = {"radius": 82.0}
    a = _fizik_ozeti(taban, "mat", ("48:2.8",), 7.0, 0.024, 1.0, 2.0)
    b = _fizik_ozeti(taban, "mat", ("48:2.8",), 7.0, 0.024, 0.1, 0.2)
    assert a != b, "AV fizik ozetine girmiyor"


def test_surucu_kaba_merdiveni_kurabiliyor():
    """`--kademeler kaba` kısayolu — G kampanyası buna bağlı.

    Sürücünün merdiveni SABİTTİ; `48` koşuluk ayırt edilebilirlik
    taraması orta ölçekte `58` saat, kaba ölçekte `4` saat sürer.
    """
    m = (REPO / "scripts" / "faz5_ensemble_merdiven.py").read_text(
        encoding="utf-8")
    assert "MERDIVEN_KABA" in m
    assert '"--kademeler"' in m
    assert 'list(a.kademeler) == ["kaba"]' in m, "kisayol yok"
    assert "kademeler=merdiven" in m, "secilen merdiven ileri modele gecmiyor"
    # kaba merdiven R1 ile AYNI olmali (Rb_R1: 48:5.6 ... 3:0.35)
    assert '("48:5.6", "24:2.8", "12:1.4", "6:0.7", "3:0.35")' in m


def test_tasarim_tohumu_ile_sahne_tohumu_AYRI():
    """A57: tek tohum ikisini birden sürerse Protokol G çöker.

    G aynı `24` noktayı iki gerçeklemeyle koşuyor; tek tohumla
    ikinci kol FARKLI `θ`'lar örneklerdi ve eşleştirme sıfır çıkardı.
    """
    m = (REPO / "scripts" / "faz5_ensemble_merdiven.py").read_text(
        encoding="utf-8")
    assert '"--sahne-tohum"' in m
    assert "sahne_kok = kok if a.sahne_tohum is None else" in m, (
        "varsayilan degismemeli: verilmezse sahne tohumu = tasarim tohumu"
    )
    assert 'lhs_design(UZAY, a.n_lhs, root_seed=kok)' in m, (
        "tasarim TASARIM tohumunu kullanmali"
    )
    assert '"root_seed": sahne_kok' in m, (
        "sahne SAHNE tohumunu kullanmali"
    )


def test_merdiven_ilk_kullanimdan_ONCE_tanimli():
    """`merdiven` `print`'ten sonra tanımlanırsa her koşu `NameError`."""
    m = (REPO / "scripts" / "faz5_ensemble_merdiven.py").read_text(
        encoding="utf-8")
    tanim = m.index("merdiven = MERDIVEN")
    kullanim = m.index("' '.join(merdiven)")
    assert tanim < kullanim, (
        "merdiven ilk kullanimdan SONRA tanimlaniyor -> NameError"
    )


def test_ensemble_cekme_kirpma_kolunu_kurabiliyor():
    """Protokol G'nin ikinci kolu buna bağlı (E2 sonucu).

    E2 ölçtü: çekme kırpılınca kaçan parçacık `45 → 3 318`,
    `Δβ` `0,0352 → 0,2715`. G, gözlenebilirin `θ` bilgisini
    akışın VAR OLDUĞU ayarda da sınıyor.
    """
    import inspect

    from dartrift.inference.forward import ileri_kosu_merdiven

    imza = inspect.signature(ileri_kosu_merdiven).parameters
    assert "matris_cekme_yok" in imza
    assert imza["matris_cekme_yok"].default is False, (
        "TANI kolu varsayilan OLMAMALI -- uretim modeli degil"
    )
    m = (REPO / "src" / "dartrift" / "inference" / "forward.py").read_text(
        encoding="utf-8")
    blok = m[m.index("def ileri_kosu_merdiven"):]
    assert "cekme_kirp_maske=(" in blok
    # bloklar ve mermi KIRPILMAMALI -- onlarda cekme dali fiziksel
    assert "~np.asarray(rs.is_impactor, dtype=bool)" in blok
    assert "& ~np.asarray(rs.is_boulder, dtype=bool)" in blok

    s = (REPO / "scripts" / "faz5_ensemble_merdiven.py").read_text(
        encoding="utf-8")
    assert '"--matris-cekme-yok"' in s
    assert "matris_cekme_yok=a.matris_cekme_yok" in s


def test_fizik_ozeti_cekme_kirpmayi_ayirt_ediyor():
    """İki G kolu aynı `θ`'yı koşuyor; özet onları AYIRMALI."""
    from dartrift.inference.forward import _fizik_ozeti

    taban = {"radius": 82.0}
    a = _fizik_ozeti(taban, "mat", ("48:5.6",), 7.0, 0.024, 1.0, 2.0, False)
    b = _fizik_ozeti(taban, "mat", ("48:5.6",), 7.0, 0.024, 1.0, 2.0, True)
    assert a != b, "cekme kirpma fizik ozetine girmiyor -> iki kol karisir"
