"""Protokol Z — bölge yarıçapı yargısı."""
from __future__ import annotations

import importlib.util
import re
from pathlib import Path

_KOK = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("zr", _KOK / "scripts" / "z_bolge_raporu.py")
zr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(zr)


def _f(beta, V):
    return {(g, m, t): (beta if g == "beta_eksi_1" else V)
            for g in zr.YARGI_GOZLEMLERI for m in zr.GENIS for t in zr.TETALAR}


def test_kucuk_farklar_ETKISIZ_buyukler_ETKILI():
    assert zr.yargi(_f(0.05, 0.05))["karar"] == "BOLGE ETKISIZ"
    assert zr.yargi(_f(0.40, 0.35))["karar"] == "BOLGE ETKILI"
    assert zr.yargi(_f(0.20, 0.05))["karar"] == "KISMI"


def test_eksik_OKUNMAZ():
    f = _f(0.05, 0.05)
    f.pop(("V_krater", "orta", 2))
    assert zr.yargi(f)["karar"] == "OKUNMAZ"


def _merdiven(metin, ad):
    m = re.search(ad + r' = \(([^)]*)\)', metin)
    return tuple(re.findall(r'"([\d.]+:[\d.]+)"', m.group(1)))


def test_genis_merdiven_ayni_araliklar_iki_kat_yaricap():
    """Geniş merdiven: EN İNCE İKİ aralığın bölge yarıçapı iki katı; en ince
    aralık aynı; dış bölgeler (`48`, `24` m) aynı.

    (İlk yazımda "her bölge iki katı" diye sınadım ve düştü: tasarım
    öyle değil, belge metni de öyle yazıyordu — ikisi düzeltildi.)"""
    metin = (_KOK / "scripts" / "faz5_ensemble_merdiven.py").read_text(encoding="utf-8")
    standart = {"kaba": _merdiven(metin, "MERDIVEN_KABA"), "orta": _merdiven(metin, "MERDIVEN")}
    for lad, gen in zr.GENIS.items():
        st = {float(s): float(r) for r, s in (c.split(":") for c in standart[lad])}
        gn = {float(s): float(r) for r, s in (c.split(":") for c in gen)}
        iki_ince = sorted(st)[:2]
        for s in iki_ince:
            assert gn[s] == 2 * st[s], (lad, s)
        for s in sorted(st)[-2:]:
            assert gn[s] == st[s], (lad, s)
