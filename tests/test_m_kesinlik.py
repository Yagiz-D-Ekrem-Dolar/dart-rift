"""Mt/M2t yargıları — OKUNMAZ θ kilitli kararı sessizce kaydırmıyor (2026-09-15, A88).

Kilitli Mt kuralı OKUNMAZ θ'yı YAKINSAMIS saymaz: eksik kampanyada karar
"YAKINSAMIYOR"a kayar ve Bitiş 3 esas-sonuç kuralı (Q §4) ince-72'yi seçerdi.
Karar değişmedi; `kesin` yazılıyor ve belirsizse esas havuz seçilmiyor.
"""
from __future__ import annotations

import importlib.util
import itertools
import json
import sys
from pathlib import Path

import pytest

_KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_KOK / "scripts"))


def _yukle(ad):
    spec = importlib.util.spec_from_file_location(ad, _KOK / "scripts" / f"{ad}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


my = _yukle("m_yakinsama_raporu")
m2 = _yukle("m2_kontrast_raporu")
b3 = _yukle("bitis3_raporu")


def _s(kararlar):
    return [{"karar": k} for k in kararlar]


@pytest.mark.parametrize("kararlar,karar,kesin", [
    (["YAKINSAMIS"] * 4 + ["OKUNMAZ"] * 2, "YAKINSIYOR", True),        # zaten >= 4
    (["YAKINSAMADI"] * 5 + ["OKUNMAZ"], "YAKINSAMIYOR", True),          # 0 + 1 <= 1
    (["YAKINSAMIS"] * 2 + ["OKUNMAZ"] * 4, "KISMI", False),             # 2..6
    (["YAKINSAMIS"] + ["OKUNMAZ"] * 5, "YAKINSAMIYOR", False),          # Mt iptali: 1..6
    (["YAKINSAMIS"] * 3 + ["YAKINSAMADI"] * 3, "KISMI", True),
])
def test_Mt_gozlem_yargisi_karar_AYNI_kesinlik_YANINDA(kararlar, karar, kesin):
    y = my.gozlem_yargisi(_s(kararlar))
    assert y["karar"] == karar and y["kesin"] is kesin
    assert y["n_okunmaz"] == kararlar.count("OKUNMAZ")


def test_bitis3_esikleri_Mt_raporuyla_AYNI():
    for k in range(7):
        assert b3._m_karari(k) == my._m_karari(k)


def test_M2_hipotez_kesinligi():
    def y(kararlar):
        return {("Y", g): {"karar": k} for g, k in zip(m2.HIPOTEZ_KUMESI, kararlar, strict=True)}

    assert m2.hipotez_kesinligi(y(["KARARLI", "KARARLI", "OKUNMAZ"]))["kesin"] is True
    k = m2.hipotez_kesinligi(y(["KARARLI", "OKUNMAZ", "KARARSIZ"]))
    assert k == {"n_kararli": 1, "n_okunmaz": 1, "kesin": False}      # KISMI..DAYANIKLI
    assert m2.hipotez_kesinligi(y(["KARARSIZ", "SINYAL YOK", "KARARSIZ"]))["kesin"] is True
    # Bagimsiz kahin: her OKUNMAZ'i KARARLI/KARARSIZ ile doldur, kilitli hipotez()'i
    # cagir; hepsi ayniysa kesin. (Ilk surum yalniz "etiket gecerli mi" diye bakiyordu --
    # hicbir seyi sinamayan bos iddia; oz denetimde degistirildi.)
    for kar in itertools.product(["KARARLI", "KARARSIZ", "OKUNMAZ"], repeat=3):
        doldur = [["KARARLI", "KARARSIZ"] if k == "OKUNMAZ" else [k] for k in kar]
        sonuc = {m2.hipotez(y(list(d))) for d in itertools.product(*doldur)}
        assert m2.hipotez_kesinligi(y(list(kar)))["kesin"] is (len(sonuc) == 1), kar


def _s_mt(yargilar):
    return {g: {"yargi": y} for g, y in zip(b3.YAKINSAMA_GOZLEMLERI, yargilar, strict=True)}


def test_bitis3_Q1_kesin_degilse_EKSIK_ve_esas_havuz_SECILMEZ(tmp_path):
    kes = {"karar": "YAKINSAMIYOR", "n_yakinsamis": 0, "n_okunmaz": 0, "kesin": True}
    bel = {"karar": "YAKINSAMIYOR", "n_yakinsamis": 1, "n_okunmaz": 5, "kesin": False}
    # Mt iptali: bes gozlenebilirin hepsi belirsiz -> Q1 her sey olabilir
    s = _s_mt([bel] * 5)
    assert b3.yakinsama_yargisi(s).startswith("EKSIK (kesin olmayan: d_merkez")
    (tmp_path / "S_Mt.json").write_text(json.dumps(s), encoding="utf-8")
    e = b3.esas_sonuc(tmp_path)
    assert e["esas"]["havuz"] == "BEKLENIYOR" and e["Q1"].startswith("EKSIK")
    # dort kesin YAKINSAMIYOR + bir belirsiz: Q1 yine YAKINSAMIYOR (belirsizlik sonucu degistirmez)
    assert b3.yakinsama_yargisi(_s_mt([kes] * 4 + [bel])) == "YAKINSAMIYOR"
    # kesin alani olmayan eski JSON: eski davranis
    eski = {g: {"yargi": {"karar": "YAKINSIYOR"}} for g in b3.YAKINSAMA_GOZLEMLERI[:4]}
    assert b3.yakinsama_yargisi(eski) == "YAKINSIYOR"
