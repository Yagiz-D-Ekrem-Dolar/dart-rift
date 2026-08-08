"""FAZ 4.7 — G4 kapı raporunu **üret** (elle yazma).

Ölçüm çıktılarını (`faz44_*.json`, `faz45_*.json`, `faz46_sonuc.json`)
okur, `validation.g4_gate` ile yargılar ve `docs/G4-KAPI-RAPORU.md`
üretir.

Eksik dosya **hata değildir**: ilgili ölçütler `koşulmadı` sayılır ve
kapı geçemez. Bu kasıtlı — bugün kapı geçilemez ve rapor bunu açıkça
söylemelidir.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

# Olcut adlarinda `β` geciyor ve Windows konsolu (cp1254) onu basamiyor.
# Bir raporlama betiginin UnicodeEncodeError ile dusmesi, raporun kendisini
# yok eder; cikti UTF-8'e sabitleniyor.
for _akis in (sys.stdout, sys.stderr):
    try:
        _akis.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):        # yeniden yonlendirilmis olabilir
        pass

from dartrift.validation.g4_gate import degerlendir  # noqa: E402


def _oku(p: str | None) -> dict | None:
    if not p:
        return None
    f = Path(p)
    if not f.is_file():
        print(f"    yok: {p}  -> ilgili olcutler KOSULMADI", flush=True)
        return None
    print(f"    okundu: {p}", flush=True)
    return json.loads(f.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--faz44", default=None)
    ap.add_argument("--faz45", default=None)
    ap.add_argument("--faz46", default=None)
    ap.add_argument("--out", default=str(REPO / "docs" / "G4-KAPI-RAPORU.md"))
    a = ap.parse_args()

    print("=" * 78, flush=True)
    print("FAZ 4.7 — G4 KAPI RAPORU", flush=True)
    print("=" * 78, flush=True)
    print("\n[1] olcum ciktilari", flush=True)
    r = degerlendir(_oku(a.faz44), _oku(a.faz45), _oku(a.faz46))

    print("\n[2] olcutler", flush=True)
    for o in r.tum_olcutler:
        d = "—" if not o.kosuldu else f"{o.deger:.6g}"
        print(f"    {o.kimlik:3s} {o.aciklama[:44]:46s} "
              f"{o.yon} {o.esik:<8g} olculen={d:<12s} {o.durum}", flush=True)

    print(f"\n[3] SONUC: G4 {'GECILDI' if r.gecti else 'GECILEMEDI'}", flush=True)
    if r.kosulmayanlar:
        print(f"    kosulmayan: {', '.join(r.kosulmayanlar)}", flush=True)
    if r.dusenler:
        print(f"    dusen:      {', '.join(r.dusenler)}", flush=True)

    Path(a.out).write_text(r.markdown(), encoding="utf-8")
    print(f"\nyazildi: {a.out}", flush=True)
    # Kapi gecilmediyse cikis kodu 1 -- CI'da sessizce yesil gorunmesin.
    return 0 if r.gecti else 1


if __name__ == "__main__":
    raise SystemExit(main())
