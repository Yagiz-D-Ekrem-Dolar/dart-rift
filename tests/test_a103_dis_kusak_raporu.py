"""PROTOKOL-A103 raporu — sentetik durumlarla yargı dalları ve kuşak momentumu."""
from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np
import pytest

_SC = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(_SC))
_spec = importlib.util.spec_from_file_location("a103_dis_kusak_raporu",
                                               _SC / "a103_dis_kusak_raporu.py")
RAP = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(RAP)


def _durum(p_ic: float, p_dis: float):
    """Merkezde küçük hedef, mermi -x'ten; iki kaçan parçacık (iç/dış kuşak)."""
    # hedef govdesi (kacmiyor)
    xg = np.array([[0.0, 0.0, 0.0], [10.0, 0.0, 0.0]])
    # kacanlar: r > 75, -x yonunde (v_r > 0), momentumlari p_ic, p_dis
    xk = np.array([[-80.0, 0.0, 0.0], [-80.0, 1.0, 0.0]])
    vk = np.array([[-1.0, 0.0, 0.0], [-1.0, 0.0, 0.0]])
    mk = np.array([p_ic, p_dis])
    x0k = np.array([[-74.0, 5.0, 0.0],      # rho0 ~ 5,1 m  -> ic
                    [-70.0, 20.0, 0.0]])    # rho0 ~ 20,6 m -> dis
    # mermi: baslangicta -x tarafinda
    xm = np.array([[-76.0, 0.0, 0.0]])
    x = np.vstack([xg, xk, xm])
    v = np.vstack([np.zeros((2, 3)), vk, np.zeros((1, 3))])
    m = np.concatenate([[1.0, 1.0], mk, [1.0]])
    x0 = np.vstack([xg, x0k, xm])
    f = np.array([0.0, 0.0, 0.0, 0.0, 1.0])
    return x, v, m, x0, f


def _yaz(kok: Path, ad: str, beta: float, p_ic=1.0, p_dis=1.0, gecerli=True,
         t_son=300.0):
    d = kok / f"{ad}.durumlar"
    d.mkdir(parents=True, exist_ok=True)
    x, v, m, x0, f = _durum(p_ic, p_dis)
    ft = {"impuls_egrisi": [[0.1, 0.0, 1.5, 0.0], [t_son, 0.0, beta, 0.0]]}
    np.savez(d / "nokta_0000_x.npz", x=x, v=v, m=m, x_referans=x0,
             mermi_kesri=f, fizik_tani=json.dumps(ft),
             gecerlilik=json.dumps({"gecerli": gecerli}))


def _hepsi(kok: Path, bk=3.6864, bi=3.8229, bo=3.9784, bd=3.84,
           pd=(1.0, 1.0, 2.0, 1.95)):
    for ad, b, p in zip(RAP.KOLLAR.values(), (bk, bi, bo, bd), pd,
                        strict=True):
        _yaz(kok, ad, b, p_dis=p)


def test_KUSAK_MOMENTUMU_ic_ve_dis_ayriliyor():
    x, v, m, x0, f = _durum(3.0, 5.0)
    k = RAP.kusak_momentumu(x, v, m, x0, f)
    assert k["P_ic"] == pytest.approx(3.0)
    assert k["P_dis"] == pytest.approx(5.0)
    assert k["P_kac"] == pytest.approx(8.0)


def test_ANA_SENARYO_toplamsal_ve_dis_baskin(tmp_path):
    _hepsi(tmp_path)
    y = RAP.yargila(RAP.oku(tmp_path))
    assert y["bulunan"] == 4
    assert y["Delta_tumleyen"] == pytest.approx(3.9784 - 3.8229)
    assert y["Y1"] == "KUSAK KATKILARI YEREL VE TOPLAMSAL"
    assert y["Y2"].startswith("DIS KUSAK (12-48 m) FARKIN COGUNU")
    assert y["Y3"] == "DIS KUSAK EJEKTASI ORTA ILE AYNI"
    assert y["genel"] == y["Y2"]


def test_TOPLAMSAL_DEGIL_ve_AZINI_tasiyor(tmp_path):
    _hepsi(tmp_path, bd=3.70, pd=(1.0, 1.0, 2.0, 1.0))
    y = RAP.yargila(RAP.oku(tmp_path))
    assert y["Y1"] == "TOPLAMSAL DEGIL"
    assert y["Y2"] == "DIS KUSAK FARKIN AZINI TASIYOR"
    assert y["Y3"] == "DIS KUSAK EJEKTASI ORTADAN FARKLI"


def test_EKSIK_ya_da_KISA_kol_OKUNMAZ(tmp_path):
    _hepsi(tmp_path)
    for p in (tmp_path / "A103_dis2.durumlar").iterdir():
        p.unlink()
    y = RAP.yargila(RAP.oku(tmp_path))
    assert y["bulunan"] == 3 and y["eksik"] == {"dis2": "durum yok"}
    assert y["genel"] == "OKUNMAZ"
    _yaz(tmp_path, "A103_dis2", 3.8, t_son=200.0)
    y = RAP.yargila(RAP.oku(tmp_path))
    assert y["eksik"] == {"dis2": "300 s'ye ulasmamis"}
    assert math.isnan(y["beta"]["dis2"])


def test_GECERSIZ_kol_eksik(tmp_path):
    _hepsi(tmp_path)
    _yaz(tmp_path, "UY_ic", 3.8229, gecerli=False)
    y = RAP.yargila(RAP.oku(tmp_path))
    assert y["eksik"] == {"ic": "gecersiz"} and y["Y1"] == "OKUNMAZ"


def test_CLI_json_uzerine_yazmaz(tmp_path):
    _hepsi(tmp_path / "k")
    out = tmp_path / "S.json"
    assert RAP.main(["--kok", str(tmp_path / "k"), "--json", str(out)]) == 0
    assert json.loads(out.read_text(encoding="utf-8"))["bulunan"] == 4
    with pytest.raises(SystemExit):
        RAP.main(["--kok", str(tmp_path / "k"), "--json", str(out)])
