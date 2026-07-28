"""Kapi metrik JSON'u: NumPy skalerleri yazilabilir, bilinmeyen tip SESSIZ GECMEZ.

G2 kapisi TRUBA'da (kosu 1426162) fizigi 41 dakika dogru kostuktan sonra
`TypeError: Object of type bool_ is not JSON serializable` ile coktu. Bu
testler o yolu sabitler.
"""

import json

import numpy as np
import pytest

from dartrift.reporting import json_default, write_metrics


class TestJsonDefault:
    def test_numpy_bool_becomes_python_bool(self):
        # np.bool_ tam da G2'yi dusuren tipti: karsilastirmalar bunu uretir.
        val = np.array([2.0]) > np.array([1.0])
        assert isinstance(val[0], np.bool_)
        assert json_default(val[0]) is True

    def test_numpy_integer_and_floating(self):
        assert json_default(np.int64(7)) == 7
        assert isinstance(json_default(np.int64(7)), int)
        assert json_default(np.float64(1.5)) == 1.5
        assert isinstance(json_default(np.float64(1.5)), float)

    def test_numpy_array_becomes_list(self):
        assert json_default(np.array([[1.0, 2.0], [3.0, 4.0]])) == [[1.0, 2.0], [3.0, 4.0]]

    def test_unknown_type_raises(self):
        """Genis bir yakalayici gercek bir tip hatasini rapora gomerdi."""
        with pytest.raises(TypeError, match="yazilamayan tip"):
            json_default(object())


class TestWriteMetrics:
    def test_numpy_laden_metrics_roundtrip(self, tmp_path):
        wave = np.array([600.0, 400.0, 300.0])
        metrics = {
            "converges": wave[0] > wave[1],          # np.bool_
            "n_steps": np.int64(1386),               # np.integer
            "energy_rel_err": np.float64(0.00096),   # np.floating
            "profile": np.array([1.0, 2.0]),         # ndarray
            "device": "cuda:0",                      # duz Python
            "nested": {"ok": wave[1] > wave[2]},     # ic ice np.bool_
        }
        p = tmp_path / "m.json"
        write_metrics(p, metrics)
        got = json.loads(p.read_text(encoding="utf-8"))
        assert got["converges"] is True
        assert got["n_steps"] == 1386
        assert got["energy_rel_err"] == pytest.approx(0.00096)
        assert got["profile"] == [1.0, 2.0]
        assert got["device"] == "cuda:0"
        assert got["nested"]["ok"] is True

    def test_plain_json_dumps_would_have_failed(self):
        """Kontrol: sorun gercekten vardi; test bos degil."""
        with pytest.raises(TypeError, match="not JSON serializable"):
            json.dumps({"converges": np.array([2.0]) > np.array([1.0])[0]})
