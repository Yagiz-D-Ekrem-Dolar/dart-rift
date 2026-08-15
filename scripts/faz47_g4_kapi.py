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

from dartrift.validation.g4_ozet import (  # noqa: E402
    faz44_ozet, faz45_ozet)
from dartrift.validation.g4_gate import degerlendir  # noqa: E402


def _oku(p: str | None, ozetle=None) -> dict | None:
    """JSON oku; HAM koşu çıktısıysa kapı anahtarlarına **özetle**.

    ## Düzeltilen kusur

    Bu fonksiyon eskiden ham dosyayı **olduğu gibi** döndürüyordu ve
    `faz44_ozet`/`faz45_ozet` hiç çağrılmıyordu. Kapı ise üst düzeyde
    `A1_mermi_parcacik_cap` gibi anahtarlar arıyor; ham çıktıda o
    değerler `sonuclar` altında iç içe.

    Sonuç: `A1`–`B4`'ün **yedisi birden** *"KOSULMADI"* çıkıyordu ve
    bu, ölçüm yapılmamış gibi görünüyordu — oysa ölçümler vardı,
    yalnızca dönüştürülmüyorlardı.

    > Sessiz bir *"koşulmadı"*, yanlış bir sayıdan daha az zararlı ama
    > yine de yanlış: kapı raporu ölçülmüş bir şeyi ölçülmemiş gösteriyordu.

    Ham biçim `sonuclar` anahtarıyla tanınıyor. Zaten özetlenmiş bir
    dosya verilirse **dokunulmuyor** (aksi hâlde özet, özetin üstüne
    uygulanıp boş dönerdi).
    """
    if not p:
        return None
    f = Path(p)
    if not f.is_file():
        print(f"    yok: {p}  -> ilgili olcutler KOSULMADI", flush=True)
        return None
    ham = json.loads(f.read_text(encoding="utf-8"))
    if ozetle is not None and isinstance(ham, dict) and "sonuclar" in ham:
        ozet = ozetle(ham)
        print(f"    okundu + OZETLENDI: {p}  "
              f"({len(ozet)} kapi anahtari)", flush=True)
        return ozet
    print(f"    okundu: {p}", flush=True)
    return ham


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--faz44", default=None)
    ap.add_argument("--faz45", default=None)
    ap.add_argument("--faz46", default=None)
    # A1 KAYNAGI: `faz44` yakinsama kollarini olcuyor, oysa `A1`
    # cikarimin kullandigi SAHNEYI sormali. Ensemble iki asamali
    # modelle kosuldugu icin `A1` oradan gelmeli.
    ap.add_argument("--faz48", default=None,
                    help="iki asamali kosu ciktisi; A1 BURADAN okunur")
    ap.add_argument("--out", default=str(REPO / "docs" / "G4-KAPI-RAPORU.md"))
    a = ap.parse_args()

    print("=" * 78, flush=True)
    print("FAZ 4.7 — G4 KAPI RAPORU", flush=True)
    print("=" * 78, flush=True)
    print("\n[1] olcum ciktilari", flush=True)
    o44 = _oku(a.faz44, faz44_ozet)
    o48 = _oku(a.faz48)
    if o48 is not None and "A1" in o48:
        eski = (o44 or {}).get("A1_mermi_parcacik_cap")
        o44 = dict(o44 or {})
        o44["A1_mermi_parcacik_cap"] = float(o48["A1"])
        print(f"    A1 KAYNAGI = faz48 (iki asamali uretim modeli): "
              f"{o48['A1']:.4f}"
              + (f"   [faz44'un kendi degeri {eski:.4f} KULLANILMADI]"
                 if eski is not None else "   [faz44'te A1 yoktu]"),
              flush=True)
    r = degerlendir(o44, _oku(a.faz45, faz45_ozet), _oku(a.faz46))

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
