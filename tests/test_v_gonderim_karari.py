"""Protokol V gönderim kararı — kilitli kural ve U iş betiğiyle tutarlılık."""
from __future__ import annotations

import importlib.util
import re
from pathlib import Path

_KOK = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("vgk", _KOK / "scripts" / "v_gonderim_karari.py")
vgk = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vgk)


def _u(genel, satirlar):
    return {"genel": genel, "satirlar": satirlar}


def test_ulasan_varsa_V_GONDERILMEZ():
    k = vgk.karar(_u("MODEL GOZLEME ULASABILIYOR: U2:kaba", {}))
    assert k["gonder"] is False and k["komut"] is None


def test_hicbiri_ulasmiyorsa_en_yakin_varyantla_komut():
    s = {"U0:kaba": {"varyant": "U0", "z": 3.4, "karar": "ALTINDA"},
         "U8:kaba": {"varyant": "U8", "z": 2.3, "karar": "ALTINDA"},
         "U8:orta": {"varyant": "U8", "z": 2.9, "karar": "ALTINDA"},
         "U3:kaba": {"karar": "OKUNMAZ"}}
    k = vgk.karar(_u("HICBIR VARYANT ULASMIYOR (en yakin U8:kaba, z = +2.3)", s))
    assert k["gonder"] and k["V4_U"] == "U8" and k["en_yakin"] == "U8:kaba"
    assert "--yigin-yogunlugu 1500" in k["V4_EK"] and "," not in k["V4_EK"]
    assert k["komut"].startswith('sbatch --export=ALL,V4_EK="--onsel-disi-izin --mu-f 0.2')
    assert k["komut"].endswith("V4_U=U8 is/is_V_model.slurm")


def test_okunamayan_U_GONDERILMEZ():
    assert vgk.karar({})["gonder"] is False
    assert vgk.karar(_u("HICBIR VARYANT ULASMIYOR (x)", {"U0:kaba": {"karar": "OKUNMAZ"}}))[
        "gonder"] is False


def test_bayrak_tablosu_U_is_betigiyle_AYNI():
    m = (_KOK / "truba" / "is_U_model.slurm").read_text(encoding="utf-8")
    ad = re.search(r"^AD=\(([^)]*)\)", m, flags=re.M).group(1).split()
    ek_blok = re.search(r"^EK=\((.*?)\)\n", m, flags=re.M | re.S).group(1)
    ek = re.findall(r'"([^"]*)"', ek_blok)
    assert len(ad) == len(ek) == len(vgk.U_BAYRAKLARI)
    for a, e in zip(ad, ek, strict=True):
        assert vgk.U_BAYRAKLARI[a] == e, (a, e)
