"""PROTOKOL-DO kilitli kuralları — **koşulardan önce** sınandı."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import do_onsel_raporu as DO  # noqa: E402


def _egri(beta, t_son, n=40):
    t = np.geomspace(1e-3, t_son, n)
    b = 1.0 + (beta - 1.0) * t / (t + 0.8)
    b[-1] = beta
    return [[float(ti), 1.0, float(bi), 1e6] for ti, bi in zip(t, b, strict=True)]


def _npz(kok: Path, ad: str, beta, M_ej, t_son=600.0, *, gecerli=True, n=100):
    d = kok / f"{ad}.durumlar"
    d.mkdir(parents=True, exist_ok=True)
    ft = {"beta_hedef": beta, "M_ejekta": M_ej, "impuls_egrisi": _egri(beta, t_son),
          "beta_iki_yontem": {"beta_km": beta + 0.02}}
    np.savez(d / "nokta_0000_a.npz", fizik_tani=json.dumps(ft),
             gecerlilik=json.dumps({"gecerli": gecerli}), m=np.ones(n))


#: Kiyas sahnesinin olculen ussuyle (`p = -0,076`) tutarli, uydurmasi IYI bir
#: uc nokta: gozlem (3,12) `500` ile `5000 Pa` arasina dusuyor.
def _iyi(kok: Path, C=3.60, p=-0.076):
    for ad, y0 in DO.KOLLAR.items():
        _npz(kok, ad, 1.0 + C * y0 ** p, 4.0e7 * y0 ** -0.32)
    return DO.yargi(DO.topla(kok))


def test_sabitler_kilitli():
    assert DO.KOLLAR == {"DY2_dart_g1p0": 10.0, "DO1_Y500_g1p0": 500.0,
                         "DO2_Y5000_g1p0": 5000.0}
    assert DO.BETA_GOZLEM == 3.12 and DO.SIGMA_GOZLEM == 0.34
    assert (DO.ONSEL_LO, DO.ONSEL_HI) == (1.0e3, 1.0e7)
    assert DO.ESIK_ARTIK == 0.15
    assert DO.SIGMA_M_BAGIL == pytest.approx(np.hypot(0.3 / 1.6, 0.15))


def test_tek_kol_eksikse_ya_da_gecersizse_OKUNMAZ_hicbir_sayi_YAZILMAZ(tmp_path):
    assert DO.yargi(DO.topla(tmp_path))["genel"].startswith("OKUNMAZ")
    for bozuk, kw in (("DO1_Y500_g1p0", {"gecerli": False}),
                      ("DO2_Y5000_g1p0", {"t_son": 300.0})):
        kok = tmp_path / f"{bozuk}_{'-'.join(kw)}"
        for ad, y0 in DO.KOLLAR.items():
            ek = kw if ad == bozuk else {}
            _npz(kok, ad, 1.0 + 3.6 * y0 ** -0.076, 4.0e7 * y0 ** -0.32, **ek)
        out = DO.yargi(DO.topla(kok))
        assert out["genel"].startswith("OKUNMAZ"), bozuk
        for alan in ("p", "noktalar", "onsel_denetimi", "M_ejekta_kazanci"):
            assert alan not in out, (bozuk, alan)


def test_IYI_uydurmada_guc_yasasi_kullaniliyor_ve_yargi_veriliyor(tmp_path):
    out = _iyi(tmp_path / "iyi")
    assert out["uydurma"] == "GUC YASASI"
    assert out["artik_uc_nokta"] < DO.ESIK_ARTIK
    assert out["p"] == pytest.approx(-0.076, abs=1e-6)
    assert out["genel"] in ("ONSEL GOZLEMI ICERMIYOR", "GOZLEM ONSEL KENARINDA",
                            "ONSEL GOZLEMI ICERIYOR")
    # uc nokta kayitta ve Y0'ya gore sirali
    assert [n["Y0"] for n in out["noktalar"]] == [10.0, 500.0, 5000.0]


def test_uydurma_KOTUyse_yerel_egime_duser(tmp_path):
    """Artık `> 0,15` ise güç yasası reddedilir (§5.1), kuşatan çift kullanılır."""
    kok = tmp_path / "kotu"
    # orta noktayi bilerek egriden cok uzaga koy -> artik buyur
    _npz(kok, "DY2_dart_g1p0", 3.90, 3.0e7)
    _npz(kok, "DO1_Y500_g1p0", 3.60, 1.0e7)     # cok yuksek: egri bozulur
    _npz(kok, "DO2_Y5000_g1p0", 2.00, 5.0e6)
    out = DO.yargi(DO.topla(kok))
    assert out["artik_uc_nokta"] > DO.ESIK_ARTIK
    assert out["uydurma"] == "UYGUN DEGIL, YEREL EGIM"
    # gozlem 3,12 -> 500 (3,60) ile 5000 (2,00) arasinda; yerel egim o ciftten
    # b = beta - 1: 500 Pa -> 2,60 ; 5000 Pa -> 1,00
    bekle_p = np.log(1.00 / 2.60) / np.log(5000.0 / 500.0)
    assert out["p"] == pytest.approx(-abs(bekle_p), rel=1e-9)
    assert 500.0 < out["onsel_denetimi"]["Y0_gozlem"] < 5000.0   # INTERPOLASYON


@pytest.mark.parametrize("C,genel", [
    (3.00, "ONSEL GOZLEMI ICERMIYOR"),    # dik dusus -> gozlem cok dusuk Y0'da
    (4.20, "ONSEL GOZLEMI ICERIYOR")])    # yuksek beta -> gozlem onselin icinde
def test_onsel_yargisi_uc_dala_ayriliyor(tmp_path, C, genel):
    out = _iyi(tmp_path / f"c{C}", C=C)
    assert out["genel"] == genel


def test_M_ejekta_kazanci_olculuyor_ve_yargilaniyor(tmp_path):
    out = _iyi(tmp_path / "kazanc")
    m = out["M_ejekta_kazanci"]
    assert m["p_M"] == pytest.approx(-0.32, abs=1e-6)
    assert m["carpan_M"] < m["carpan_beta"]        # M_ejekta daha siki
    assert m["kazanc"] > 4.0
    assert m["genel"] == "M_EJEKTA TANIMLAYICI"


def test_M_ejekta_duyarsizsa_KAZANC_YOK(tmp_path):
    kok = tmp_path / "kazancyok"
    for ad, y0 in DO.KOLLAR.items():
        # M_ejekta neredeyse sabit -> Y0'yu sikistirmaz
        _npz(kok, ad, 1.0 + 3.60 * y0 ** -0.076, 2.0e7 * y0 ** -0.002)
    m = DO.yargi(DO.topla(kok))["M_ejekta_kazanci"]
    assert m["genel"] == "KAZANC YOK"


def test_payda_DY2_ile_AYNI_terimlerden(tmp_path):
    out = _iyi(tmp_path / "payda")
    rel = DO._sigma_model_bagil()
    assert out["payda"] == pytest.approx(
        float(np.hypot(DO.SIGMA_GOZLEM, (DO.BETA_GOZLEM - 1.0) * rel)), rel=1e-12)
    # DY2'nin terim listesiyle ayni dort terim
    import dy_dart_raporu as DY
    assert DY.TERIMLER == ("gerceklem_beta", "cozunurluk_uzak", "plato",
                           "carpma_yeri")


def test_CLI_json_yaziyor(tmp_path, capsys):
    kok = tmp_path / "cli"
    _iyi(kok)
    yol = tmp_path / "S_DO.json"
    assert DO.main(["--kok", str(kok), "--json", str(yol)]) == 0
    d = json.loads(yol.read_text(encoding="utf-8"))
    assert d["genel"] == d["onsel_denetimi"]["genel"]
    cikti = capsys.readouterr().out
    assert "PROTOKOL DO" in cikti and "M_ejekta" in cikti and "GENEL:" in cikti


def test_kusatan_cift_uclarda_da_komsu_cift_veriyor():
    nk = [(10.0, 3.90, 3e7), (500.0, 3.60, 1e7), (5000.0, 3.40, 5e6)]
    # hedef hepsinin ALTINDA -> en yakin uc (5000) ve komsusu
    (y1, _), (y2, _) = DO._kusatan_cift(nk, 2.0)
    assert (y1, y2) == (500.0, 5000.0)
    # hedef hepsinin USTUNDE -> ilk iki nokta
    (y1, _), (y2, _) = DO._kusatan_cift(nk, 9.0)
    assert (y1, y2) == (10.0, 500.0)
