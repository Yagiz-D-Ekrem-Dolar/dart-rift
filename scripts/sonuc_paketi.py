"""Sonuç paketi — kampanya sonuçlarını tek JSON'da, kaynaklarıyla topla.

TRUBA'daki `kampanya/S_*.json`, `ONKAYIT_*.json` ve `BITIS3-TASLAK.md`
dosyaları tek tek okunmak yerine tek pakete girer. Her dosya için boyut,
değişiklik zamanı (UTC) ve SHA-256 yazılır; paket yerelde açılınca
`docs/olcumler/<paket_adi>/` altına **aynı adlarla** çıkarılır ve özetler
doğrulanır. Büyük dosyalar (`> AZAMI_BAYT`) içerik olmadan, yalnız özetle girer.

Kullanim (TRUBA):
    python scripts/sonuc_paketi.py topla --kok kampanya --cikti kampanya/PAKET_20260915.json
Kullanim (yerel):
    python scripts/sonuc_paketi.py ac --paket PAKET_20260915.json \
        --hedef docs/olcumler/PAKET_20260915
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
from pathlib import Path

DESENLER = ("S_*.json", "ONKAYIT_*.json", "BITIS3-TASLAK.md")
AZAMI_BAYT = 2_000_000


def _ozet(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def topla(kok: Path, desenler=DESENLER, azami: int = AZAMI_BAYT) -> dict:
    kok = Path(kok)
    dosyalar = {}
    for d in desenler:
        for p in sorted(kok.glob(d)):
            b = p.read_bytes()
            st = p.stat()
            kayit = {"boyut": len(b), "sha256": _ozet(b),
                     "mtime_utc": _dt.datetime.fromtimestamp(
                         st.st_mtime, _dt.timezone.utc).isoformat(timespec="seconds")}
            if len(b) <= azami:
                kayit["icerik"] = b.decode("utf-8")
            else:
                kayit["icerik"] = None
                kayit["not"] = f"{len(b)} bayt > {azami}: icerik pakete alinmadi"
            dosyalar[p.name] = kayit
    return {"olusturma_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
            "kok": str(kok), "n_dosya": len(dosyalar), "dosyalar": dosyalar}


def ac(paket: dict, hedef: Path) -> dict:
    """Paketi çıkar; her dosyanın özetini doğrula. Bozuk içerik yazılmaz."""
    hedef = Path(hedef)
    hedef.mkdir(parents=True, exist_ok=True)
    yazilan, atlanan, bozuk = [], [], []
    for ad, k in paket["dosyalar"].items():
        if "/" in ad or "\\" in ad or ad.startswith("."):
            bozuk.append(ad)
            continue
        if k.get("icerik") is None:
            atlanan.append(ad)
            continue
        b = k["icerik"].encode("utf-8")
        if _ozet(b) != k["sha256"]:
            bozuk.append(ad)
            continue
        (hedef / ad).write_bytes(b)
        yazilan.append(ad)
    (hedef / "PAKET_KAYNAK.json").write_text(json.dumps(
        {"olusturma_utc": paket.get("olusturma_utc"), "kok": paket.get("kok"),
         "dosyalar": {a: {x: v for x, v in k.items() if x != "icerik"}
                      for a, k in paket["dosyalar"].items()}}, indent=1), encoding="utf-8")
    return {"yazilan": yazilan, "atlanan": atlanan, "bozuk": bozuk}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    alt = ap.add_subparsers(dest="komut", required=True)
    t = alt.add_parser("topla")
    t.add_argument("--kok", type=Path, required=True)
    t.add_argument("--cikti", type=Path, required=True)
    o = alt.add_parser("ac")
    o.add_argument("--paket", type=Path, required=True)
    o.add_argument("--hedef", type=Path, required=True)
    a = ap.parse_args(argv)
    if a.komut == "topla":
        p = topla(a.kok)
        a.cikti.write_text(json.dumps(p, ensure_ascii=False), encoding="utf-8")
        print(f"paket: {p['n_dosya']} dosya -> {a.cikti}")
        return 0
    r = ac(json.loads(a.paket.read_text(encoding="utf-8")), a.hedef)
    print(f"yazilan {len(r['yazilan'])}, atlanan {len(r['atlanan'])}, bozuk {len(r['bozuk'])}")
    for b in r["bozuk"]:
        print("  BOZUK:", b)
    return 0 if not r["bozuk"] else 8


if __name__ == "__main__":
    raise SystemExit(main())
