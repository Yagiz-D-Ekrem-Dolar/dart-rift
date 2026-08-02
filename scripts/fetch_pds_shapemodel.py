"""PDS DART sekil modeli paketini indir ve manifesti INDIRMEYLE AYNI ANDA yaz.

G3 kriter C7'yi kapatmak icin. `data_manifest/README.md`deki kural:

  > Manifest INDIRMEYLE AYNI ANDA yazilir, sonradan degil. Sonradan hesaplanan
  > saglama toplami, dosyanin indirildigi andaki halini degil o an diskte ne
  > varsa onu kaydeder — ki yakalamaya calistigi hata tam olarak budur.

Bu betik o kurali uygular: her dosya icin SHA-256 AKIS HALINDE, baytlar diske
yazilirken hesaplanir.

KULLANIM (ag erisimi olan bir makinede; TRUBA login dugumunde calisir):

    python scripts/fetch_pds_shapemodel.py --out data/pds --manifest data_manifest

VARSAYILAN OLARAK HICBIR SEY INDIRMEZ: `--yes` verilmeden yalnizca ne
indirilecegini listeler ve boyutlari raporlar (`--dry-run` davranisi).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BUNDLE_LID = "urn:nasa:pds:dart_shapemodel::1.0"
LANDING = ("https://pds-smallbodies.astro.umd.edu/holdings/"
           "pds4-dart_shapemodel-v1.0/SUPPORT/dataset.shtml")
CITATION = (
    "Daly, T., Barnouin, O., Ernst, C., Nair, H., Espiritu, R., Waller, D., "
    "DART Shapemodel Archive Bundle, urn:nasa:pds:dart_shapemodel::1.0, "
    "NASA Planetary Data System, 2023."
)
UA = "dart-rift/1.0 (akademik kullanim; PDS acik veri)"


def _head(url: str, timeout: float = 30.0) -> tuple[int, str]:
    """(boyut_bayt, icerik_turu); bilinmiyorsa (-1, "")."""
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            n = r.headers.get("Content-Length")
            return (int(n) if n else -1, r.headers.get("Content-Type", ""))
    except (urllib.error.URLError, OSError, ValueError) as exc:
        print(f"  HEAD basarisiz: {exc}", file=sys.stderr)
        return (-1, "")


def _download(url: str, dest: Path, chunk: int = 1 << 20) -> tuple[str, str, int]:
    """Indir; SHA-256 VE MD5'i AKIS HALINDE hesapla -> (sha256, md5, bayt).

    Karmalar, baytlar diske yazilirken ayni tampondan hesaplanir; dosya
    sonradan tekrar okunmaz. Boylece manifest, gercekten indirilen baytlarin
    karmasini tasir.

    MD5 neden de hesaplaniyor: PDS arsivi her koleksiyon icin resmi bir
    `SUPPORT/CHECKSUM/current.md5` yayimliyor. Kendi hesapladigimiz karma
    yalnizca "diskte ne var" der; ARSIVIN karmasiyla karsilastirmak
    "dogru dosyayi, bozulmadan aldik mi" sorusunu yanitlar. Ikisi ayri
    sorulardir ve ikisi de gerekir.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    h = hashlib.sha256()
    m = hashlib.md5()
    n = 0
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    tmp = dest.with_suffix(dest.suffix + ".part")
    with urllib.request.urlopen(req, timeout=600) as r, open(tmp, "wb") as f:
        while True:
            b = r.read(chunk)
            if not b:
                break
            h.update(b)
            m.update(b)
            f.write(b)
            n += len(b)
    tmp.replace(dest)
    return h.hexdigest(), m.hexdigest(), n


def _official_md5(collection_url: str) -> dict[str, str]:
    """Koleksiyonun resmi `SUPPORT/CHECKSUM/current.md5` dosyasini oku."""
    url = collection_url.rstrip("/") + "/SUPPORT/CHECKSUM/current.md5"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    out: dict[str, str] = {}
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            for line in r.read().decode("utf-8", "replace").splitlines():
                p = line.split(None, 1)
                if len(p) == 2:
                    out[p[1].strip()] = p[0].strip().lower()
    except (urllib.error.URLError, OSError) as exc:
        print(f"  UYARI: resmi MD5 alinamadi ({exc}) — dogrulama YAPILAMAZ",
              file=sys.stderr)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--urls", nargs="*", default=[],
                    help="indirilecek dogrudan URL'ler")
    ap.add_argument("--url-file", default=None,
                    help="her satirda bir URL bulunan dosya")
    ap.add_argument("--out", default="data/pds")
    ap.add_argument("--manifest", default="data_manifest")
    ap.add_argument("--yes", action="store_true",
                    help="GERCEKTEN indir. Verilmezse yalnizca listeler.")
    args = ap.parse_args()

    urls = list(args.urls)
    if args.url_file:
        urls += [ln.strip() for ln in Path(args.url_file).read_text(
            encoding="utf-8").splitlines() if ln.strip() and not ln.startswith("#")]
    if not urls:
        print("URL verilmedi. Paket kimligi:", BUNDLE_LID)
        print("Inis sayfasi:", LANDING)
        print("\n--urls ya da --url-file ile dogrudan urun adresleri verin.")
        return 2

    print(f"paket : {BUNDLE_LID}")
    print(f"kaynak: {LANDING}")
    print(f"urun  : {len(urls)}")
    print()

    toplam = 0
    for u in urls:
        n, ct = _head(u)
        toplam += max(n, 0)
        print(f"  {u}\n    boyut={n if n >= 0 else 'bilinmiyor'} bayt  tur={ct}")
    print(f"\ntoplam (bilinen): {toplam} bayt = {toplam / 1e6:.1f} MB")

    if not args.yes:
        print("\nHICBIR SEY INDIRILMEDI. Gercekten indirmek icin --yes ekleyin.")
        return 0

    out = Path(args.out)
    urunler = []
    md5_cache: dict[str, dict[str, str]] = {}
    dogrulanan, uyusmayan, dogrulanamayan = 0, [], 0
    for u in urls:
        ad = u.rstrip("/").split("/")[-1]
        koleksiyon = u.rsplit("/", 1)[0]
        hedef = out / ad
        print(f"indiriliyor: {ad} ...", flush=True)
        sha, md5, n = _download(u, hedef)

        if koleksiyon not in md5_cache:
            md5_cache[koleksiyon] = _official_md5(koleksiyon)
        resmi = md5_cache[koleksiyon].get(ad)
        if resmi is None:
            durum = "resmi MD5 yok"
            dogrulanamayan += 1
        elif resmi == md5:
            durum = "MD5 DOGRULANDI"
            dogrulanan += 1
        else:
            durum = f"MD5 UYUSMADI (resmi {resmi})"
            uyusmayan.append(ad)
        print(f"  {n} bayt  sha256={sha[:16]}...  {durum}", flush=True)

        urunler.append({
            "product_id": f"{BUNDLE_LID}#{ad}",
            "filename": str(hedef),
            "source_url": u,
            "sha256": sha,
            "md5": md5,
            "md5_official": resmi,
            "md5_verified": bool(resmi is not None and resmi == md5),
            "bytes": n,
            "used_by": "setup/shape_mesh.load_obj",
        })

    print(f"\nMD5: {dogrulanan} dogrulandi, {len(uyusmayan)} uyusmadi, "
          f"{dogrulanamayan} dogrulanamadi", flush=True)
    if uyusmayan:
        print(f"HATA: bozuk indirme: {uyusmayan}", file=sys.stderr)
        return 1

    man = {
        "bundle": BUNDLE_LID,
        "retrieved_utc": datetime.now(timezone.utc).isoformat(),
        "retrieved_by": "scripts/fetch_pds_shapemodel.py",
        "source_url": LANDING,
        "license": "NASA PDS acik veri; atif zorunlu",
        "citation": CITATION,
        "md5_verified_count": dogrulanan,
        "md5_unverifiable_count": dogrulanamayan,
        "products": urunler,
    }
    mp = Path(args.manifest) / "dart_shapemodel.json"
    mp.parent.mkdir(parents=True, exist_ok=True)
    mp.write_text(json.dumps(man, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nmanifest yazildi: {mp}  ({len(urunler)} urun)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
