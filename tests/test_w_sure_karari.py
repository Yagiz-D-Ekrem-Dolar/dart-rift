"""PROTOKOL-W §3.2 — `t_end` kuralı koda gömülü; sınavları."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import w_sure_karari as S  # noqa: E402


def _kw(duvar, n_adim=100_000, n_gecis=80_000, t_gecis=0.2, t_end0=2.0):
    return dict(duvar_saniye=duvar, n_adim=n_adim, n_gecis=n_gecis,
                t_gecis=t_gecis, t_end0=t_end0)


def test_KURAL_sabitleri_kilitli():
    assert S.BUTCE_GPU_SAAT == 8.0
    assert S.ADAYLAR == (600.0, 60.0)
    assert S.TABAN_T_END == 10.0


def test_UCUZ_kosuda_600_saniye_seciliyor():
    # 100k adim 600 s duvar -> 0,006 s/adim; gecis sonrasi dt = 1,8/20k = 9e-5 s
    # 600 s icin n ~ 80k + 6,7e6 -> cok pahali; hizli bir ornek kuralim:
    k = S.karar(**_kw(60.0, n_adim=100_000, n_gecis=80_000, t_gecis=0.2,
                      t_end0=2.0))
    # dt_gec = 1,8/20000 = 9e-5 s; 600 s -> 6,67e6 adim x 6e-4 s = 4000 s = 1,1 sa
    assert k["t_end"] == 600.0 and k["damga"] == "TAMAM"
    assert k["maliyet_tahmini_gpu_saat"]["600"] < 8.0


def test_ORTA_hizda_60_saniyeye_dusuyor():
    k = S.karar(**_kw(3600.0, n_adim=100_000, n_gecis=80_000))
    assert k["maliyet_tahmini_gpu_saat"]["600"] > 8.0
    assert k["maliyet_tahmini_gpu_saat"]["60"] <= 8.0
    assert k["t_end"] == 60.0 and k["damga"] == "TAMAM"


def test_COK_YAVASSA_taban_ve_DAMGA():
    k = S.karar(**_kw(36000.0, n_adim=100_000, n_gecis=99_000))
    assert k["t_end"] == S.TABAN_T_END
    assert k["damga"] == "SURE YETERSIZ"


def test_dt_BUYUME_orani_raporlaniyor():
    k = S.karar(**_kw(600.0, n_adim=100_000, n_gecis=80_000))
    # gecis oncesi dt = 0,2/80000 = 2,5e-6; sonrasi 1,8/20000 = 9e-5 -> 36x
    assert k["dt_gecis_oncesi_s"] == pytest.approx(2.5e-6, rel=1e-9)
    assert k["dt_gecis_sonrasi_s"] == pytest.approx(9.0e-5, rel=1e-9)
    assert k["dt_buyume_orani"] == pytest.approx(36.0, rel=1e-9)


def test_ALTI_kosunun_toplami_hesaplaniyor():
    k = S.karar(**_kw(60.0))
    assert k["toplam_6_kosu_gpu_saat"] == pytest.approx(
        6.0 * k["maliyet_tahmini_gpu_saat"][f"{k['t_end']:g}"], rel=1e-12)


@pytest.mark.parametrize("kw", [
    {"duvar_saniye": 0.0}, {"n_adim": 0}, {"n_gecis": 0},
    {"n_gecis": 200_000}, {"t_gecis": 0.0}, {"t_gecis": 5.0},
])
def test_GECERSIZ_girdi_REDDEDILIYOR(kw):
    taban = _kw(600.0)
    taban.update(kw)
    with pytest.raises(ValueError):
        S.karar(**taban)


def test_maliyet_T_ile_ARTIYOR():
    ortak = dict(c_adim=0.01, n_gecis=1000, t_gecis=0.2, dt_gec=1e-3)
    a = S.maliyet_saat(10.0, **ortak)
    b = S.maliyet_saat(100.0, **ortak)
    assert 0.0 < a < b


def test_npz_okuma_ve_CLI(tmp_path, capsys):
    d = tmp_path / "W0.durumlar"
    d.mkdir()
    ft = {"beta_hedef": 2.3, "gec_evre": {"adim_gecis": 80_000, "t_gecis": 0.2}}
    np.savez(d / "nokta_0000_a.npz", n_adim=100_000, t=2.0,
             fizik_tani=json.dumps(ft))
    yol = tmp_path / "S_W0.json"
    assert S.main(["--npz", str(d / "*.npz"), "--duvar-saniye", "60",
                   "--json", str(yol)]) == 0
    veri = json.loads(yol.read_text(encoding="utf-8"))
    assert veri["t_end"] == 600.0
    assert veri["beta_hedef"] == pytest.approx(2.3)
    assert "BILIMSEL SONUC DEGIL" in capsys.readouterr().out


def test_gec_evre_YOKSA_reddediliyor(tmp_path):
    d = tmp_path / "X.durumlar"
    d.mkdir()
    np.savez(d / "nokta_0000_a.npz", n_adim=10, t=1.0,
             fizik_tani=json.dumps({"beta_hedef": 1.0}))
    with pytest.raises(SystemExit, match="gec evre"):
        S.npz_oku(str(d / "*.npz"))
