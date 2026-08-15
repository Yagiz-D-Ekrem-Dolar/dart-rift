"""Ensemble sürücüsü — **kesinti** ve devam (FAZ 5 ön koşulu).

Kesinti bir olasılık değil, **yaşanmış**: iş 1460700 zaman aşımından
kesildi. Bu testler sürücünün o durumda ne yaptığını sınıyor.
"""
from __future__ import annotations

import json

import numpy as np
import pytest

from dartrift.inference.ensemble import ensemble_kos, oku_tamamlananlar

TASARIM = np.array([[1.0, 10.0], [2.0, 20.0], [3.0, 30.0],
                    [4.0, 40.0], [5.0, 50.0]])


def _ileri(th):
    return np.array([th[0] * 2.0, th[1] + 1.0])


def test_bos_dosyadan_HEPSI_kosuluyor(tmp_path) -> None:
    y = tmp_path / "e.jsonl"
    d = ensemble_kos(TASARIM, _ileri, y, root_seed=7)
    assert d.toplam == 5 and d.tamamlanan == 5
    assert d.atlanan == 0 and d.dusen == 0
    assert len(y.read_text(encoding="utf-8").strip().splitlines()) == 5


def test_KESINTI_sonrasi_kaldigi_yerden(tmp_path) -> None:
    """Yarıda kesilen ensemble, tamamlananları **yeniden koşmamalı**."""
    y = tmp_path / "e.jsonl"
    cagrilan = []

    def _sayan(th):
        cagrilan.append(float(th[0]))
        if len(cagrilan) > 2:
            raise KeyboardInterrupt("SLURM zaman asimi taklidi")
        return _ileri(th)

    with pytest.raises(KeyboardInterrupt):
        ensemble_kos(TASARIM, _sayan, y, root_seed=7)
    assert len(y.read_text(encoding="utf-8").strip().splitlines()) == 2

    # Yeniden baslat: ilk IKI nokta ATLANMALI.
    # (Kesmeyen bir sayac veriliyor -- ilk surumde `_ileri` verip
    #  `cagrilan`'a bakiyordum, o yuzden liste bos kaliyordu.)
    cagrilan.clear()

    def _sayan2(th):
        cagrilan.append(float(th[0]))
        return _ileri(th)

    d = ensemble_kos(TASARIM, _sayan2, y, root_seed=7)
    assert d.atlanan == 2, d
    assert d.tamamlanan == 5
    assert cagrilan == [3.0, 4.0, 5.0], cagrilan


def test_BOZUK_son_satir_atlaniyor_ve_nokta_YENIDEN_kosuluyor(tmp_path) -> None:
    """Tam yazma anında kesinti → yarım satır. Sessizce kullanılmamalı."""
    y = tmp_path / "e.jsonl"
    ensemble_kos(TASARIM[:2], _ileri, y, root_seed=7)
    with y.open("a", encoding="utf-8") as f:
        f.write('{"i": 2, "y": [6.0, 3')          # YARIM
    tamam, bozuk = oku_tamamlananlar(y, root_seed=7)
    assert bozuk == 1 and set(tamam) == {0, 1}

    d = ensemble_kos(TASARIM, _ileri, y, root_seed=7)
    assert d.bozuk_satir == 1
    assert d.atlanan == 2
    assert d.tamamlanan == 5


def test_TOHUM_degisirse_eski_satirlar_GECERSIZ(tmp_path) -> None:
    """Tasarım değiştiyse eski sonuçlar başka noktalara ait — atılmalı."""
    y = tmp_path / "e.jsonl"
    ensemble_kos(TASARIM, _ileri, y, root_seed=7)
    tamam, bozuk = oku_tamamlananlar(y, root_seed=99)
    assert tamam == {} and bozuk == 5


def test_DUSEN_nokta_TEKRAR_DENENMIYOR(tmp_path) -> None:
    """Aynı parametre aynı şekilde düşer; tekrar denemek GPU'yu yakar."""
    y = tmp_path / "e.jsonl"

    def _bazilari_duser(th):
        if th[0] == 3.0:
            raise RuntimeError("bu nokta patliyor")
        return _ileri(th)

    d1 = ensemble_kos(TASARIM, _bazilari_duser, y, root_seed=7)
    assert d1.dusen == 1 and d1.tamamlanan == 4

    cagrilan = []

    def _sayan(th):
        cagrilan.append(float(th[0]))
        return _ileri(th)

    d2 = ensemble_kos(TASARIM, _sayan, y, root_seed=7)
    assert cagrilan == [], "dusen nokta YENIDEN denendi"
    assert d2.atlanan == 5


def test_DUSEN_nokta_ISTENIRSE_yeniden_deneniyor(tmp_path) -> None:
    """Düşme nedeni düzeltildiyse yeniden denemek **meşru**."""
    y = tmp_path / "e.jsonl"

    def _duser(th):
        if th[0] == 3.0:
            raise RuntimeError("patliyor")
        return _ileri(th)

    ensemble_kos(TASARIM, _duser, y, root_seed=7)
    d = ensemble_kos(TASARIM, _ileri, y, root_seed=7,
                     yeniden_dene_dusenleri=True)
    assert d.tamamlanan == 5
    tamam, _ = oku_tamamlananlar(y, root_seed=7)
    assert tamam[2] is not None


def test_SONLU_OLMAYAN_cikti_DUSME_sayiliyor(tmp_path) -> None:
    """`nan` döndüren bir ileri model "başarılı" sayılmamalı."""
    y = tmp_path / "e.jsonl"
    d = ensemble_kos(TASARIM[:1], lambda th: np.array([np.nan, 1.0]), y,
                     root_seed=7)
    assert d.dusen == 1 and d.tamamlanan == 0
    kayit = json.loads(y.read_text(encoding="utf-8").strip())
    assert kayit["y"] is None
    assert "sonlu olmayan" in kayit["hata"]


def test_bitti_bayragi(tmp_path) -> None:
    y = tmp_path / "e.jsonl"
    assert ensemble_kos(TASARIM, _ileri, y, root_seed=7).bitti is True


def test_HER_NOKTA_HEMEN_yaziliyor(tmp_path) -> None:
    """Kesinti en fazla **son** noktayı kaybetmeli — arabelleğe alınmamalı."""
    y = tmp_path / "e.jsonl"
    goruldu = []

    def _gozetleyen(th):
        # Bu cagri sirasinda dosyada KAC satir var?
        n = (len(y.read_text(encoding="utf-8").strip().splitlines())
             if y.is_file() and y.read_text(encoding="utf-8").strip() else 0)
        goruldu.append(n)
        return _ileri(th)

    ensemble_kos(TASARIM, _gozetleyen, y, root_seed=7)
    # i. cagri sirasinda tam i satir yazilmis olmali.
    assert goruldu == [0, 1, 2, 3, 4], goruldu


def test_faz46_ENSEMBLE_SURUCUSUNU_kullaniyor() -> None:
    """Kesinti kaçınılmaz; koşucu devam edebilen sürücüyü kullanmalı.

    `~300` koşu `~10` GPU-günü (KAYIT-040) ve bir SLURM işi `12` saat.
    Yani ensemble birden çok işe yayılmak **zorunda**.
    """
    from pathlib import Path

    kaynak = (Path(__file__).resolve().parents[1] / "scripts" /
              "faz46_sentetik_kurtarma.py").read_text(encoding="utf-8")
    assert "from dartrift.inference.ensemble import" in kaynak
    assert "ensemble_kos(" in kaynak
    assert "devam dosyasi" in kaynak
    # Eski TEK SEFERLIK cagri geri GELMEMELI.
    assert "Y = ileri_kosu(x, a.device" not in kaynak, \
        "tek seferlik cagri geri gelmis -- kesintide her sey kaybolur"
