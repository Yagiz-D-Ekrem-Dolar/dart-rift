"""Sonuç paketi — topla/aç gidiş-dönüşü, özet doğrulama, güvenli adlar."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

_KOK = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("sp", _KOK / "scripts" / "sonuc_paketi.py")
sp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sp)


def _kampanya(k: Path):
    k.mkdir()
    (k / "S_DART_Qo.json").write_text(json.dumps({"kapsama": {"karar": "ONSEL DISI"}}), "utf-8")
    (k / "ONKAYIT_HERA_Qo.json").write_text('{"sha256": "ab"}', "utf-8")
    (k / "BITIS3-TASLAK.md").write_text("# taslak\nçözülüyor\n", "utf-8")
    (k / "baska.txt").write_text("alinmaz", "utf-8")
    (k / "S_buyuk.json").write_text("x" * 50, "utf-8")


def test_topla_ac_gidis_donus_bit_ayni(tmp_path):
    _kampanya(tmp_path / "kampanya")
    p = sp.topla(tmp_path / "kampanya", azami=40)
    assert p["n_dosya"] == 4 and "baska.txt" not in p["dosyalar"]
    assert p["dosyalar"]["S_buyuk.json"]["icerik"] is None
    p = json.loads(json.dumps(p))                      # diske yazilip okunmus gibi
    r = sp.ac(p, tmp_path / "hedef")
    assert sorted(r["yazilan"]) == ["BITIS3-TASLAK.md", "ONKAYIT_HERA_Qo.json", "S_DART_Qo.json"]
    assert r["atlanan"] == ["S_buyuk.json"] and r["bozuk"] == []
    for ad in r["yazilan"]:
        assert (tmp_path / "hedef" / ad).read_bytes() == (tmp_path / "kampanya" / ad).read_bytes()
    kaynak = json.loads((tmp_path / "hedef" / "PAKET_KAYNAK.json").read_text("utf-8"))
    assert "icerik" not in kaynak["dosyalar"]["S_DART_Qo.json"]


def test_bozulmus_icerik_YAZILMAZ(tmp_path):
    _kampanya(tmp_path / "kampanya")
    p = sp.topla(tmp_path / "kampanya")
    p["dosyalar"]["S_DART_Qo.json"]["icerik"] = '{"kapsama": {"karar": "ONSEL ICINDE"}}'
    r = sp.ac(p, tmp_path / "hedef")
    assert r["bozuk"] == ["S_DART_Qo.json"]
    assert not (tmp_path / "hedef" / "S_DART_Qo.json").exists()


def test_yol_iceren_ad_REDDEDILIR(tmp_path):
    p = {"dosyalar": {"../kacis.json": {"icerik": "{}", "sha256": sp._ozet(b"{}")}}}
    r = sp.ac(p, tmp_path / "hedef")
    assert r["bozuk"] == ["../kacis.json"] and not (tmp_path / "kacis.json").exists()
