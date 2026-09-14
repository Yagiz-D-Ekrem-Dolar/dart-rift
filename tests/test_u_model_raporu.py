"""Protokol U — model yeterliliği yargısı ve sürücü bayrakları."""
from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import pytest

_KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_KOK / "scripts"))
_spec = importlib.util.spec_from_file_location("ur", _KOK / "scripts" / "u_model_raporu.py")
ur = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ur)

M_SAHNE = 4.157e9
P_IMP = 579.4 * 6144.9


def _k(bm1s, M=M_SAHNE):
    return [{"bm1": b, "M": M, "p_imp": P_IMP, "tohum": str(i)} for i, b in enumerate(bm1s)]


def test_ALTINDA_BANDA_ve_genel():
    v = {("U0", "kaba"): _k([0.92, 0.95]), ("U2", "kaba"): _k([1.95, 2.05]),
         ("U8", "kaba"): _k([3.2, 3.3])}
    out = ur.yargi(v)
    s = out["satirlar"]
    assert s["U0:kaba"]["karar"] == "ALTINDA" and s["U0:kaba"]["z"] > 2
    assert s["U2:kaba"]["karar"] == "BANDA ULASIYOR"
    assert s["U8:kaba"]["karar"] == "USTUNDE"
    assert out["genel"] == "MODEL GOZLEME ULASABILIYOR: U2:kaba"
    assert s["U2:kaba"]["fark_tabandan"] == pytest.approx(1.065)


def test_hicbiri_ulasmiyorsa_en_yakin_yaziliyor():
    out = ur.yargi({("U0", "kaba"): _k([0.9, 0.9]), ("U3", "kaba"): _k([1.1, 1.1])})
    assert out["genel"].startswith("HICBIR VARYANT ULASMIYOR (en yakin U3:kaba")


def test_gozlenen_beta_varyantin_KENDI_kutlesiyle():
    """U6 (yığın 1500): hedef kütlesi küçülür → gözlenen β de küçülür."""
    a = ur.yargi({("U6", "kaba"): _k([1.0, 1.0], M=M_SAHNE * 1500 / 1800)})
    b = ur.yargi({("U6", "kaba"): _k([1.0, 1.0])})
    ga = a["satirlar"]["U6:kaba"]["beta_eksi_1_gozlem"]
    gb = b["satirlar"]["U6:kaba"]["beta_eksi_1_gozlem"]
    assert ga < gb


def test_surucu_U_bayraklari_ve_onsel_disi_denetimi():
    s = (_KOK / "scripts" / "faz5_ensemble_merdiven.py").read_text(encoding="utf-8")
    for bayrak in ("--mu-f", "--porozite-pe", "--porozite-ps", "--yigin-yogunlugu",
                   "--onsel-disi-izin"):
        assert f'"{bayrak}"' in s, bayrak
    assert "material=MALZEME" in s and "material=_mat()" not in s
    assert 'if onsel_disi and not a.onsel_disi_izin:' in s
    assert '"onsel_disi": bool(' in s and '"malzeme_ek": malzeme_ek' in s


def test_is_betigi_varyant_eslemesi_belgeyle_ayni():
    m = (_KOK / "truba" / "is_U_model.slurm").read_text(encoding="utf-8")
    ad = re.search(r"^AD=\(([^)]*)\)", m, flags=re.M).group(1).split()
    assert ad == list(ur.VARYANTLAR)
    doc = (_KOK / "docs" / "truba" / "PROTOKOL-U-MODEL.md").read_text(encoding="utf-8")
    for v in ad:
        assert f"| {v} |" in doc, v
    assert ur.Z_ESIGI == 2.0 and "`|z| ≤ 2`" in doc
