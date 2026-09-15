"""GPU-saat sayımı — süre biçimleri, türlü/türsüz GPU iki kat sayılmaz, adımlar atlanır."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_KOK = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("gs", _KOK / "scripts" / "gpu_saat.py")
gs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gs)


@pytest.mark.parametrize("e,saat", [("10:00:00", 10.0), ("1-02:30:00", 26.5),
                                    ("45:00", 0.75), ("00:00:00", 0.0)])
def test_sure_bicimleri(e, saat):
    assert gs.sure_saat(e) == pytest.approx(saat)


def test_turlu_ve_tursuz_GPU_IKI_KAT_sayilmaz():
    assert gs.gpu_sayisi("billing=16,cpu=16,gres/gpu:h100=1,gres/gpu=1,mem=64G,node=1") == 1
    assert gs.gpu_sayisi("cpu=16,gres/gpu:h100=2,node=1") == 2
    assert gs.gpu_sayisi("cpu=4,mem=16G,node=1") == 0
    assert gs.gpu_sayisi("") == 0


def test_topla_adim_atlar_ad_basina_toplar_iptali_sayar():
    satirlar = [
        "1561193_0|Mt_plato|10:00:00|cpu=16,gres/gpu:h100=1,gres/gpu=1|COMPLETED",
        "1561193_0.batch|batch|10:00:00|cpu=16,gres/gpu=1|COMPLETED",   # adim: atlanir
        "1561193_8|Mt_plato|02:00:00|cpu=16,gres/gpu=1|CANCELLED by 123",  # kosmus iptal
        "1561438_[0-19]|U_model|00:00:00|cpu=16,gres/gpu=1|CANCELLED by 123",  # hic kosmadi
        "1561231|Pgen_rap|00:33:42|cpu=16,gres/gpu=1|COMPLETED",
        "",
        "bozuk satir",
    ]
    r = gs.topla(satirlar)
    assert r["n_is"] == 4
    assert r["ad_basina"]["Mt_plato"] == pytest.approx(12.0)
    assert r["ad_basina"]["U_model"] == 0.0
    assert r["toplam"] == pytest.approx(12.0 + 33 / 60 + 42 / 3600)
    assert list(r["ad_basina"])[0] == "Mt_plato"


def test_CLI(tmp_path, capsys):
    p = tmp_path / "s.txt"
    p.write_text("1|a|01:00:00|gres/gpu=2|COMPLETED\n", encoding="utf-8")
    assert gs.main([str(p)]) == 0
    assert "TOPLAM: 2.0 GPU-saat (1 is)" in capsys.readouterr().out
