"""Gözlenebilir önbelleği — aynı npz'nin krater operatörünü her raporda yeniden koşmamak.

## Neden

N, P-v4 (×2), P-v4b (×2), şekil verisi (×2), D, HT ve tanı raporlarının
hepsi `gozlem_vektoru(np.load(f))` çağırıyor. İnce merdivende (`487 358`
parçacık) krater yüzey operatörü npz başına dakikalar sürüyor; 96–144 npz'lik
havuzda aynı hesap ~10 kez tekrarlanıyor ve raporlar saatler sürüyor.

## Doğruluk sözleşmesi

- Önbellek, npz'nin yanında `nokta_XXXX.gozlem.json` (havuz globları
  `nokta_*.npz` olduğu için karışmaz).
- Anahtar: npz boyutu + `mtime_ns` + **kod özeti** (gözlenebilirleri
  üreten kaynak dosyaların SHA-256'sı). Kod değişirse önbellek geçersiz.
- JSON float gidiş-dönüşü tam (`repr`), `NaN` korunur → değerler bit-aynı
  (sınanıyor).
- Yazma geçici dosya + `os.replace` (eşzamanlı TRUBA işlerinde atomik).
- `DARTRIFT_GOZLEM_ONBELLEK=0` → önbellek hiç kullanılmaz.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import numpy as np

_KOK = Path(__file__).resolve().parents[1]
KAYNAKLAR = (
    _KOK / "scripts" / "gozlem_vektoru.py",
    _KOK / "src" / "dartrift" / "observables" / "crater_shape.py",
    _KOK / "src" / "dartrift" / "observables" / "momentum_defteri.py",
    _KOK / "src" / "dartrift" / "observables" / "momentum_transfer.py",
)
SURUM = 1
_KOD_OZETI: str | None = None


def kod_ozeti(kaynaklar=KAYNAKLAR) -> str:
    h = hashlib.sha256(f"surum={SURUM}".encode())
    for p in kaynaklar:
        h.update(Path(p).name.encode())
        h.update(Path(p).read_bytes())
    return h.hexdigest()[:16]


def _ozet() -> str:
    global _KOD_OZETI
    if _KOD_OZETI is None:
        _KOD_OZETI = kod_ozeti()
    return _KOD_OZETI


def etkin() -> bool:
    return os.environ.get("DARTRIFT_GOZLEM_ONBELLEK", "1") != "0"


def _anahtar(f: Path, kod: str) -> dict:
    st = f.stat()
    return {"boyut": int(st.st_size), "mtime_ns": int(st.st_mtime_ns), "kod": kod}


def gozlem(f, hesap=None, *, kod: str | None = None) -> dict:
    """`gozlem_vektoru(np.load(f))` — önbellekten ya da hesaplayıp önbelleğe yazarak."""
    f = Path(f)
    if hesap is None:
        from gozlem_vektoru import gozlem_vektoru as hesap
    if not etkin():
        return hesap(np.load(f))
    kod = kod or _ozet()
    yan = f.with_name(f.stem + ".gozlem.json")
    anah = _anahtar(f, kod)
    if yan.exists():
        try:
            d = json.loads(yan.read_text(encoding="utf-8"))
            if d.get("anahtar") == anah:
                return {k: float(v) for k, v in d["gozlem"].items()}
        except (ValueError, KeyError, TypeError, OSError):
            pass
    gv = hesap(np.load(f))
    gecici = yan.with_name(f"{yan.name}.{os.getpid()}.tmp")
    try:
        gecici.write_text(json.dumps({"anahtar": anah, "gozlem": gv}), encoding="utf-8")
        os.replace(gecici, yan)
    except OSError:
        if gecici.exists():
            gecici.unlink(missing_ok=True)
    return dict(gv)
