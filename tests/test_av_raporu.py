"""AV × çözünürlük raporu — **sonuçlardan önce** sınanır.

Eşikler (`MONOTON_ESIGI`) koşudan önce kilitlendi. Sınavlar betiğin
bilinen girdilerde doğru yargıyı verdiğini gösteriyor; sonuç geldiğinde
eşiği ayarlamaya yer kalmıyor.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

_yol = Path(__file__).resolve().parents[1] / "scripts" / "av_raporu.py"
_spec = importlib.util.spec_from_file_location("av_raporu", _yol)
av = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(av)


def _kol(tmp, ad, *, M, P, av_deg, n=16, sev=2, artik=1e-14, sok="KISMI"):
    d = {
        "N": 17201,
        "alpha_av": av_deg,
        "sok": {"yargi": sok},
        "momentum_defteri": {
            "kutle_kacan_hedef": M,
            "P_kacan_hedef": P,
            "n_kacan_hedef": n,
            "beta_hedef": 1.0 - P / 3.56e6,
            "artik_bagil": artik,
            "ejekta_seviyeleri": [{"parcacik_kg": 5.8, "n": n}] * sev,
        },
    }
    y = tmp / f"{ad}.json"
    y.write_text(json.dumps(d), encoding="utf-8")
    return y


# --- monotonluk ---------------------------------------------------------

def test_monoton_azalan_esikle_calisiyor():
    # alpha_av 1,0 -> 0,4 -> 0,1 sirasinda |<v>| dusuyor
    assert av.monoton_azalan([-1264.0, -100.0, -0.4])["monoton"] is True


def test_duz_dizi_monoton_SAYILMAZ():
    m = av.monoton_azalan([-100.0, -99.0, -98.0])   # %1'lik adimlar
    assert m["monoton"] is False
    assert "duz" in m["sebep"] or "tutarsiz" in m["sebep"]


def test_ters_yon_yakalanIYOR():
    m = av.monoton_azalan([-0.4, -100.0, -1264.0])
    assert m["monoton"] is False
    assert m["sebep"] == "ters yonde monoton"


def test_esik_tam_sinirda():
    """`MONOTON_ESIGI = 0,10` — `%9` düşüş monoton SAYILMAZ."""
    assert av.MONOTON_ESIGI == 0.10
    assert av.monoton_azalan([100.0, 91.0])["monoton"] is False
    assert av.monoton_azalan([100.0, 85.0])["monoton"] is True


def test_nan_varsa_monoton_degil():
    assert av.monoton_azalan([-1264.0, float("nan")])["monoton"] is False


# --- tek seviye reddi (A36) ---------------------------------------------

def test_tek_seviyeden_kacan_isaretleniyor():
    assert av.tek_seviye_mi({"seviyeler": [{"n": 33}]}) is True
    assert av.tek_seviye_mi({"seviyeler": [{"n": 3}, {"n": 30}]}) is False
    assert av.tek_seviye_mi({"seviyeler": []}) is False


# --- uctan uca yargi ----------------------------------------------------

def _kos(tmp, kollar):
    yollar = [_kol(tmp, ad, **kw) for ad, kw in kollar]
    return yollar


def test_iki_olcekte_de_monotonsa_AV_KONTROL_PARAMETRESI(tmp_path, capsys):
    kollar = []
    for olcek, taban in (("kaba", 1.0), ("orta", 1.0)):
        for et, a_av, v in (("av10", 1.0, -1264.0), ("av04", 0.4, -100.0),
                            ("av01", 0.1, -0.4)):
            M = 93.0 * taban
            kollar.append((f"F_{olcek}_{et}",
                           dict(M=M, P=v * M, av_deg=a_av)))
    yollar = _kos(tmp_path, kollar)
    av.main(["--kollar", *[str(y) for y in yollar]])
    c = capsys.readouterr().out
    assert "AV GERCEK BIR KONTROL PARAMETRESI" in c


def test_tek_olcekte_gorunurse_ARTEFAKT_SUPHESI(tmp_path, capsys):
    kollar = []
    for et, a_av, v_kaba, v_orta in (("av10", 1.0, -1264.0, -1264.0),
                                     ("av04", 0.4, -100.0, -1260.0),
                                     ("av01", 0.1, -0.4, -1258.0)):
        kollar.append((f"F_kaba_{et}", dict(M=93.0, P=v_kaba * 93.0,
                                            av_deg=a_av)))
        kollar.append((f"F_orta_{et}", dict(M=93.0, P=v_orta * 93.0,
                                            av_deg=a_av)))
    yollar = _kos(tmp_path, kollar)
    av.main(["--kollar", *[str(y) for y in yollar]])
    c = capsys.readouterr().out
    assert "COZUNURLUK ARTEFAKTI SUPHESI" in c


def test_sok_yoksa_OKUNMAZ(tmp_path, capsys):
    yollar = _kos(tmp_path, [
        ("F_kaba_av10", dict(M=93.0, P=-1e5, av_deg=1.0, sok="SOK_YOK")),
        ("F_kaba_av01", dict(M=93.0, P=-1e2, av_deg=0.1)),
    ])
    av.main(["--kollar", *[str(y) for y in yollar]])
    c = capsys.readouterr().out
    assert "OKUNMAZ" in c and "SOK_YOK" in c


def test_defter_acikken_OKUNMAZ(tmp_path, capsys):
    yollar = _kos(tmp_path, [
        ("F_kaba_av10", dict(M=93.0, P=-1e5, av_deg=1.0, artik=1e-5)),
        ("F_kaba_av01", dict(M=93.0, P=-1e2, av_deg=0.1)),
    ])
    av.main(["--kollar", *[str(y) for y in yollar]])
    c = capsys.readouterr().out
    assert "OKUNMAZ" in c and "KAPALI DEGIL" in c


def test_esikler_protokolle_ayni():
    m = (Path(__file__).resolve().parents[1] / "docs" / "truba"
         / "PROTOKOL-F-AV.md").read_text(encoding="utf-8")
    assert "MONOTON" in m.upper()
    assert av.OLCEKLER == ("kaba", "orta")
    assert "kaba" in m and "orta" in m


def test_av_etiketi_cozuluyor():
    assert av._av_degeri("av10") == pytest.approx(1.0)
    assert av._av_degeri("av04") == pytest.approx(0.4)
    assert av._av_degeri("av01") == pytest.approx(0.1)
