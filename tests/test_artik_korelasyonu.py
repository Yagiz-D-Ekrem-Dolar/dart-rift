"""Artık korelasyonu `R` sınavları — havuz OKUNMADAN yazıldı (2026-10-14).

ADR-0058 §4.3 `R`'nin ölçülmesini şart koşuyor; bu sınavlar ölçümün
**doğru şeyi** ölçtüğünü sabitler. Havuz dolmadan yazıldı ki eşik ya da
biçim sonuca göre ayarlanamasın.
"""

from __future__ import annotations

import numpy as np
import pytest

from dartrift.inference.artik_korelasyonu import (
    ASGARI_ORNEK,
    KUCULTME,
    artik_korelasyonu,
    korelasyon_ikilisi,
)


def _artik(n=200, rho=0.8, tohum=7):
    """Bilinen `rho` ile iki gözlemli artık üret."""
    rng = np.random.default_rng(tohum)
    z = rng.standard_normal((n, 2))
    a = z[:, 0]
    b = rho * z[:, 0] + np.sqrt(1 - rho ** 2) * z[:, 1]
    return np.column_stack([a, 2.5 * b])     # farkli olcek: korelasyon ayni


def test_R_KORELASYONDUR_kovaryans_degil():
    """Köşegen tam 1 olmalı: varyans `D(θ)`'dan gelir, `R`'den değil.

    Buraya kovaryans dönerse `grid_posterior_hetero` varyansı İKİ KEZ
    sayar ve posterior yapay olarak genişler.
    """
    R, _ = artik_korelasyonu(_artik())
    assert np.allclose(np.diag(R), 1.0)


def test_kucultme_kosegen_disini_TAM_1_eksi_lam_ile_olcekler():
    """Modül başlığındaki türetme: `R_ij = (1-λ) r_ij`, `R_ii = 1`."""
    E = _artik(rho=0.8)
    R, tani = artik_korelasyonu(E)
    ham = np.asarray(tani["ham_korelasyon"])
    assert tani["rho_kuculmus"] == pytest.approx(
        (1 - KUCULTME) * tani["rho_ham"], rel=1e-12)
    assert R[0, 1] == pytest.approx((1 - KUCULTME) * ham[0, 1], rel=1e-12)


def test_bilinen_rho_geri_okunuyor():
    """Ham korelasyon, üretilen `rho`'yu örneklem hatası içinde vermeli."""
    _, tani = artik_korelasyonu(_artik(n=4000, rho=0.8))
    assert tani["rho_ham"] == pytest.approx(0.8, abs=0.03)


def test_olcek_degisimi_korelasyonu_DEGISTIRMEZ():
    """`M_ejekta` kg, `β` boyutsuz: `R` birime duyarlı olmamalı."""
    E = _artik()
    _, t1 = artik_korelasyonu(E)
    _, t2 = artik_korelasyonu(E * np.array([1.0, 1e7]))
    assert t1["rho_ham"] == pytest.approx(t2["rho_ham"], rel=1e-10)


def test_isaret_korunur():
    """Küçültme korelasyonu geri çeker, İŞARETİNİ çevirmez."""
    for rho in (-0.9, -0.3, 0.3, 0.9):
        _, tani = artik_korelasyonu(_artik(n=3000, rho=rho))
        assert np.sign(tani["rho_kuculmus"]) == np.sign(tani["rho_ham"])
        assert abs(tani["rho_kuculmus"]) < abs(tani["rho_ham"])


def test_R_pozitif_tanimli_TAM_korelasyonda_bile():
    """`rho = 1` örnek korelasyonu tekil yapar; küçültme kurtarmalı.

    `λ = 0` olsaydı `R` tekil olur ve `log det R` ıraksardı.
    """
    n = 60
    a = np.linspace(-1, 1, n)
    E = np.column_stack([a, 3.0 * a])        # tam dogrusal bagimli
    R, tani = artik_korelasyonu(E)
    assert tani["en_kucuk_ozdeger"] > 0.0
    assert np.linalg.det(R) > 0.0


def test_AZ_ORNEKTE_hata():
    """Az örnekle korelasyon okumak gürültüden sayı okumaktır."""
    with pytest.raises(ValueError, match="okunmaz"):
        artik_korelasyonu(_artik(n=ASGARI_ORNEK - 1))


def test_sonsuz_ve_tek_gozlemli_hata():
    E = _artik()
    bozuk = E.copy()
    bozuk[3, 1] = np.nan
    with pytest.raises(ValueError, match="sonlu"):
        artik_korelasyonu(bozuk)
    with pytest.raises(ValueError, match="2 gozlemli"):
        artik_korelasyonu(E[:, :1])


def test_sifir_sacilmada_hata():
    """Bir gözlemlinin artığı sabitse korelasyon tanımsızdır."""
    E = _artik()
    E[:, 1] = 5.0
    with pytest.raises(ValueError, match="sacilmasi sifir"):
        artik_korelasyonu(E)


def test_ikili_kol_ADR0058_43():
    """Yan yana kol: biri birim matris, diğeri ölçülen."""
    R0, Rm = korelasyon_ikilisi(_artik(rho=0.8))
    assert np.allclose(R0, np.eye(2))
    assert Rm[0, 1] != 0.0
    assert np.allclose(np.diag(Rm), 1.0)


def test_KUCULTME_betikle_ayni():
    """Modül ile `p_kalibrasyon_raporu` aynı küçültmeyi kullanmalı.

    İkisi ayrışırsa posterior ile kalibrasyon raporu farklı `R` kullanır
    ve fark kimsenin gözüne çarpmaz.
    """
    import re
    from pathlib import Path
    betik = (Path(__file__).resolve().parents[1]
             / "scripts" / "p_kalibrasyon_raporu.py").read_text(encoding="utf-8")
    m = re.search(r"^KUCULTME\s*=\s*([0-9.]+)", betik, re.M)
    assert m, "betikte KUCULTME bulunamadi"
    assert float(m.group(1)) == pytest.approx(KUCULTME)
