"""**Değiştirilemez anlık görüntü** — "o gün tam olarak ne biliyorduk?"

## Neden gerekli

Artifact aynı URL'de güncelleniyor ve depo sürekli değişiyor. İkisi de
*"bugün ne biliyoruz"* sorusunu yanıtlıyor ama **hiçbiri**
*"`A30` ortaya çıktığında ne biliyorduk"* sorusunu yanıtlamıyor.

Bir dış geri bildirim bunu istedi: her önemli sürüm için depoda
**değişmez** bir kayıt — tarih, commit SHA, koşu kimlikleri, anahtar
sayılar ve **hangi önceki yorumun geçersiz kılındığı**.

## Değişmezlik nasıl **zorlanıyor**

`docs/anlik/MANIFEST.sha256` her anlık görüntünün özetini tutuyor ve
`tests/test_anlik_degismez.py` her koşuda doğruluyor. Eski bir
görüntüyü **düzenlemek testi düşürür**; yenisini eklemek yalnızca
manifeste satır ekler.

> Bu, depo kuralının (*"hiçbir satır silinmez"*) makine tarafından
> uygulanan hâli. Niyet yetmiyor; hata geçmişi ancak
> **değiştirilemezse** korunur.
"""
from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ANLIK = REPO / "docs" / "anlik"
MANIFEST = ANLIK / "MANIFEST.sha256"


def _kabuk(*args: str) -> str:
    return subprocess.run(args, cwd=REPO, capture_output=True,
                          text=True, check=False).stdout.strip()


def depo_durumu() -> dict:
    """Anlık görüntüye girecek **doğrulanabilir** depo bilgisi."""
    kirli = _kabuk("git", "status", "--porcelain")
    return {
        "commit": _kabuk("git", "rev-parse", "HEAD"),
        "kisa": _kabuk("git", "rev-parse", "--short", "HEAD"),
        "dal": _kabuk("git", "rev-parse", "--abbrev-ref", "HEAD"),
        "tarih": _kabuk("git", "log", "-1", "--format=%cI"),
        "temiz": kirli == "",
        "kirli_dosya": len([s for s in kirli.split("\n") if s.strip()]),
    }


def ozet(yol: Path) -> str:
    return hashlib.sha256(yol.read_bytes()).hexdigest()


def manifest_oku() -> dict:
    if not MANIFEST.exists():
        return {}
    out = {}
    for satir in MANIFEST.read_text(encoding="utf-8").splitlines():
        satir = satir.strip()
        if not satir or satir.startswith("#"):
            continue
        h, ad = satir.split(None, 1)
        out[ad] = h
    return out


def manifest_yaz(kayit: dict) -> None:
    bas = ("# DEGISTIRILEMEZ ANLIK GORUNTULER\n"
           "# Bu dosya `tests/test_anlik_degismez.py` tarafindan\n"
           "# dogrulaniyor. Eski bir goruntuyu duzenlemek testi DUSURUR.\n")
    govde = "".join(f"{h}  {ad}\n" for ad, h in sorted(kayit.items()))
    MANIFEST.write_text(bas + govde, encoding="utf-8")


def dogrula() -> list:
    """Manifestteki her görüntü hâlâ aynı mı — bozulanların listesi."""
    bozuk = []
    for ad, h in manifest_oku().items():
        yol = ANLIK / ad
        if not yol.exists():
            bozuk.append((ad, "SILINMIS"))
        elif ozet(yol) != h:
            bozuk.append((ad, "DEGISTIRILMIS"))
    return bozuk


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", help="dosya adi eki, orn. 'momentum-defteri'")
    ap.add_argument("--govde", help="anlik goruntu govdesi (dosya yolu)")
    ap.add_argument("--dogrula", action="store_true",
                    help="yalnizca manifesti dogrula, yeni goruntu alma")
    a = ap.parse_args()

    if a.dogrula:
        bozuk = dogrula()
        for ad, ne in bozuk:
            print(f"  BOZUK: {ad} -- {ne}", flush=True)
        print(f"{len(manifest_oku())} goruntu, {len(bozuk)} bozuk", flush=True)
        return 1 if bozuk else 0

    if not (a.slug and a.govde):
        raise SystemExit("--slug ve --govde gerekli (ya da --dogrula)")

    d = depo_durumu()
    if not d["temiz"]:
        # KIRLI AGACTAN GORUNTU ALINMAZ: commit SHA o an diskteki kodu
        # göstermez ve goruntunun tek isi DOGRULANABILIR olmak.
        raise SystemExit(
            f"calisma agaci KIRLI ({d['kirli_dosya']} dosya) -- anlik "
            f"goruntu yalnizca temiz agactan alinir; SHA yoksa goruntu "
            f"dogrulanamaz")

    ad = f"ANLIK-{date.today().isoformat()}_{a.slug}.md"
    yol = ANLIK / ad
    if yol.exists():
        raise SystemExit(f"{ad} ZATEN VAR -- anlik goruntuler "
                         f"degistirilemez; yeni bir slug secin")

    bas = (f"# ANLIK {date.today().isoformat()} — {a.slug}\n\n"
           f"> **Değiştirilemez kayıt.** Bu dosya `MANIFEST.sha256` ile\n"
           f"> kilitli; düzenlemek testi düşürür. Sonradan öğrenilen\n"
           f"> her şey **yeni** bir anlık görüntüye yazılır.\n\n"
           f"| | |\n|---|---|\n"
           f"| commit | `{d['commit']}` |\n"
           f"| kısa | `{d['kisa']}` · dal `{d['dal']}` |\n"
           f"| commit tarihi | `{d['tarih']}` |\n"
           f"| çalışma ağacı | **temiz** |\n\n---\n\n")
    yol.write_text(bas + Path(a.govde).read_text(encoding="utf-8"),
                   encoding="utf-8")

    kayit = manifest_oku()
    kayit[ad] = ozet(yol)
    manifest_yaz(kayit)
    print(f"yazildi: docs/anlik/{ad}", flush=True)
    print(f"  ozet: {kayit[ad][:16]}...", flush=True)
    print(f"  manifest: {len(kayit)} goruntu", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
