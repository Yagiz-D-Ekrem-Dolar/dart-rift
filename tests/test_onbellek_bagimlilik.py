"""Gözlem önbelleğinin kod özeti gözlenebilirleri etkileyen BÜTÜN iç modülleri kapsıyor mu.

2026-09-15 öz denetim: `crater_shape` → `cpu_reference.sph_ref` →
`cpu_reference.adaptive_h` zinciri anahtarda yoktu; SPH çekirdeği değişse
krater gözlemleri önbellekten sessizce eski okunurdu. Bu sınav import
kapanışını AST ile çıkarır (fonksiyon içi tembel importlar dahil) ve
`KAYNAKLAR`'ın onu kapsadığını denetler — yeni bir bağımlılık eklenince düşer.
"""
from __future__ import annotations

import ast
import importlib.util
from pathlib import Path

_KOK = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("gob", _KOK / "scripts" / "gozlem_onbellek.py")
gob = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gob)

GIRIS = ("dartrift.observables.crater_shape", "dartrift.observables.momentum_defteri",
         "dartrift.observables.momentum_transfer")


def _dosya(mod: str) -> Path | None:
    p = _KOK.joinpath("src", *mod.split("."))
    if p.with_suffix(".py").is_file():
        return p.with_suffix(".py")
    if (p / "__init__.py").is_file():
        return p / "__init__.py"
    return None


def _importlar(dosya: Path, mod: str) -> set[str]:
    paket = mod if dosya.name == "__init__.py" else mod.rsplit(".", 1)[0]
    out = set()
    for d in ast.walk(ast.parse(dosya.read_text(encoding="utf-8"))):
        if isinstance(d, ast.ImportFrom):
            if d.level:
                taban = paket.split(".")
                taban = taban[: len(taban) - (d.level - 1)]
                ad = ".".join(taban + ([d.module] if d.module else []))
            else:
                ad = d.module or ""
            if ad.startswith("dartrift"):
                out.add(ad)
                out.update(f"{ad}.{a.name}" for a in d.names)
        elif isinstance(d, ast.Import):
            out.update(a.name for a in d.names if a.name.startswith("dartrift"))
    return out


def kapanis(giris=GIRIS) -> set[Path]:
    gorulen, yigin = set(), list(giris)
    while yigin:
        m = yigin.pop()
        y = _dosya(m)
        if y is None or y in gorulen:
            continue
        gorulen.add(y)
        yigin.extend(_importlar(y, m))
    return gorulen


def test_kapanis_bilinen_zinciri_buluyor():
    adlar = {p.name for p in kapanis()}
    assert {"crater_shape.py", "sph_ref.py", "adaptive_h.py"} <= adlar


def test_KAYNAKLAR_ic_import_kapanisini_KAPSIYOR():
    kaynak = {Path(p).resolve() for p in gob.KAYNAKLAR}
    # paket __init__ dosyalari yalniz yeniden disa aktarir; deger uretmez
    eksik = sorted(str(p.relative_to(_KOK)) for p in kapanis()
                   if p.name != "__init__.py" and p.resolve() not in kaynak)
    assert not eksik, f"onbellek anahtarinda eksik bagimlilik: {eksik}"
    assert (_KOK / "scripts" / "gozlem_vektoru.py").resolve() in kaynak


def test_gozlem_vektoru_yalniz_bu_uc_giris_modulunu_kullaniyor():
    m = (_KOK / "scripts" / "gozlem_vektoru.py").read_text(encoding="utf-8")
    kullanilan = {ad for ad in _importlar(_KOK / "scripts" / "gozlem_vektoru.py", "scripts.x")
                  if ad.count(".") == 2}
    assert kullanilan == set(GIRIS), kullanilan
    assert "import" in m
