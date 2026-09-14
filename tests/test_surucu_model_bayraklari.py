"""Sürücü model bayrakları (U/V) — varsayılan bit-aynı, açıkken malzemeye ulaşıyor."""
from __future__ import annotations

import dataclasses
import sys
from pathlib import Path

_KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_KOK / "scripts"))
sys.path.insert(0, str(_KOK / "src"))


def _surucu() -> str:
    return (_KOK / "scripts" / "faz5_ensemble_merdiven.py").read_text(encoding="utf-8")


def test_bayraklar_tanimli_ve_ozete_giriyor():
    s = _surucu()
    for b in ("--yercekimi", "--hasar", "--mu-f", "--porozite-pe", "--porozite-ps",
              "--yigin-yogunlugu", "--onsel-disi-izin"):
        assert f'"{b}"' in s, b
    assert 'malzeme_ek["yercekimi"] = True' in s and 'malzeme_ek["hasar"] = True' in s
    assert '"malzeme_ek": malzeme_ek' in s
    assert "material=MALZEME" in s


def test_uretim_malzemesinde_yercekimi_ve_hasar_KAPALI_degistirme_yolu_calisiyor():
    from faz48_iki_asama import _mat

    m = _mat()
    assert m.gravity.enabled is False and m.damage.enabled is False
    g = dataclasses.replace(m, gravity=dataclasses.replace(m.gravity, enabled=True))
    h = dataclasses.replace(m, damage=dataclasses.replace(m.damage, enabled=True))
    assert g.gravity.enabled and not g.damage.enabled
    assert h.damage.enabled and not h.gravity.enabled
    assert repr(g) != repr(m) and repr(h) != repr(m)       # fizik_ozeti ayrisir
