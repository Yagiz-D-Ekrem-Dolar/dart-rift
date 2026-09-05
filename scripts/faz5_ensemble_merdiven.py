"""FAZ 5 — **merdivenli** ensemble sürücüsü.

## Neden yeni bir sürücü

Önceki ensemble (`faz46_g4c_hazir_ensemble.py`) şokun hiç oluşmadığı
bir rejimde koştu. Ölçüldü (rapor A19): `G4-C`'nin `q2 = 0,907`'lik
korelasyonu **taban artığından** geliyordu; gerçek sinyalin `q2`'si
**`-0,33`**. Yani vekil eğitildi ama anlamsız bir gözlenebilir
üzerine.

Bu sürücü üç şeyi düzeltiyor:

| | eski | **yeni** |
|---|---|---|
| çözünürlük | tek basamak, şok yok | **merdiven** (`%45,18` sıkışma) |
| şok denetimi | yok | **ADR-0049 kapısı** — geçmeyen nokta `nan` |
| krater ölçüsü | mutlak yarıçap (taban artıklı) | Lagrange'cı yer değiştirme |

## Kaldığı yerden devam

`ensemble_kos` JSONL'i satır satır yazıyor ve tamamlanmış noktaları
atlıyor. Bir SLURM işi kesilse bile ilerleme **kaybolmaz**; iş
yeniden gönderilir ve kaldığı yerden sürer.

## Maliyet

Ölçüldü (`2026-08-31`): merdiven `N ≈ 76 700`, `t_end = 0,2 s` için
`27 429` adım -> H100'de **`~4,3 saat/nokta`**. `40` nokta seri
`~7 gün`, `20` GPU paralel **`~9 saat`**.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from faz48_iki_asama import SAHNE, _mat  # noqa: E402

from dartrift.inference.design import (  # noqa: E402
    DART_UZAYI,
    DART_UZAYI_S3,
    factorial_design,
    lhs_design,
)
from dartrift.inference.ensemble import ensemble_kos  # noqa: E402
from dartrift.inference.forward import (  # noqa: E402
    GOZLENEBILIRLER,
    ileri_kosu_merdiven,
)

#: A25/A26 ile dogrulanmis merdiven -- METRE cinsinden, DISTAN ICE.
MERDIVEN = ("48:2.8", "24:1.4", "12:0.7", "6:0.35", "3:0.175")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-lhs", type=int, default=32,
                    help="Latin hiperkup nokta sayisi (kenarlar ayrica)")
    ap.add_argument("--kenarlar", action="store_true",
                    help="tam carpanli kenar noktalarini da ekle")
    ap.add_argument("--t-end", type=float, default=0.2)
    ap.add_argument("--spacing", type=float, default=7.0)
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--root-seed", type=int, default=None)
    ap.add_argument("--sok-kapisi-kapali", action="store_true",
                    help="TANI AMACLI: ADR-0049 kapisini kapat")
    ap.add_argument("--eski-uzay", action="store_true",
                    help="ADR-0044 ONCESI DART_UZAYI kullan "
                         "(yalnizca gerileme/karsilastirma; sonuc S3 "
                         "onseli sayilmaz)")
    # DILIM (rapor A31): alti gorev ayni anda baslayip BOS dosya
    # gordu ve hepsi i = 0'dan basladi -- 108 GPU-saat harcanip 18
    # saatlik is elde edildi (%83 israf). `ensemble_kos`'un kaldigi
    # yerden devami SIRALI kesinti icin dogru, ESZAMANLI gorevler icin
    # degil. Care: paylasim yerine BOLUSUM.
    ap.add_argument("--dilim", default=None,
                    help="'i/n' -- bu gorev tasarimin i. dilimini kossun "
                         "(A31; eszamanli gorevlerde ZORUNLU)")
    ap.add_argument("--out", required=True, help="JSONL yolu")
    a = ap.parse_args()

    kok = int(SAHNE["root_seed"]) if a.root_seed is None else a.root_seed
    # UZAY SECIMI -- ADR-0044 (KABUL EDILDI) varsayilani S3'tur.
    # Onceki surumde burada kosulsuz `DART_UZAYI` yaziliydi ve is 1539871
    # (K5 pilot) onunla kostu: 19/24 nokta S3'un gerekceli `1,30` sinirinin
    # DISINDA kaldi. Noktalar fiziken kurulabilir cikti (24/24, matris
    # gozenekligi %17,6-52,7, hicbiri %67 esigini asmiyor) -- yani sonuc
    # cop degil, ama kullanilan ONSEL kabul edilmis onsel DEGIL.
    UZAY = DART_UZAYI if a.eski_uzay else DART_UZAYI_S3
    if a.eski_uzay:
        print("  ! TERK EDILMIS UZAY (ADR-0044): sonuc S3 onseli SAYILMAZ",
              flush=True)
    tasarim = lhs_design(UZAY, a.n_lhs, root_seed=kok)
    if a.kenarlar:
        tasarim = np.vstack([factorial_design(UZAY, levels=2), tasarim])

    tam_n = len(tasarim)
    dilim_bilgi = "yok (TEK gorev)"
    if a.dilim:
        i_s, n_s = (int(v) for v in a.dilim.split("/"))
        if not (0 <= i_s < n_s):
            raise SystemExit(f"--dilim 'i/n' ve 0 <= i < n olmali, "
                             f"{a.dilim!r} geldi")
        secim = np.arange(tam_n) % n_s == i_s
        tasarim = tasarim[secim]
        dilim_bilgi = f"{i_s}/{n_s}  ({len(tasarim)}/{tam_n} nokta)"
        if len(tasarim) == 0:
            raise SystemExit(f"dilim {a.dilim} bos -- n cok buyuk")

    print("=" * 78, flush=True)
    print("FAZ 5 — MERDIVENLI ENSEMBLE", flush=True)
    print("=" * 78, flush=True)
    print(f"  uzay        : {UZAY.names}"
          f"{'  [TERK EDILMIS]' if a.eski_uzay else ''}", flush=True)
    print(f"  nokta       : {len(tasarim)}  (lhs {a.n_lhs}"
          f"{' + kenarlar' if a.kenarlar else ''})", flush=True)
    print(f"  dilim       : {dilim_bilgi}", flush=True)
    print(f"  merdiven    : {' '.join(MERDIVEN)}  (metre)", flush=True)
    print(f"  t_end       : {a.t_end} s", flush=True)
    print(f"  sok kapisi  : {'KAPALI (TANI)' if a.sok_kapisi_kapali else 'ACIK'}",
          flush=True)
    print(f"  gozlenebilir: {GOZLENEBILIRLER}", flush=True)
    print(f"  root_seed   : {kok}", flush=True)

    t0 = time.perf_counter()

    def _ilerleme(i, n, mesaj):
        print(f"    [{i + 1:>3}/{n}] {mesaj}  "
              f"({time.perf_counter() - t0:.0f} s)", flush=True)

    yol = Path(a.out)
    if a.dilim:
        yol = yol.with_suffix(f".dilim{a.dilim.replace('/', '_')}.jsonl")

    def _ileri(theta):
        y = ileri_kosu_merdiven(
            np.atleast_2d(theta), material=_mat(), device=a.device,
            t_end=a.t_end, kademeler=MERDIVEN, spacing=a.spacing,
            sahne_taban=None, sok_yargisi=not a.sok_kapisi_kapali,
            durum_dizini=yol.with_suffix(".durumlar"))[0]
        if not np.all(np.isfinite(y)):
            raise RuntimeError(f"nokta okunamadi: {y}")
        return y

    # AYRI DOSYA (A31'in ikinci yuzu): ayni dosyaya eszamanli EKLEME
    # satir bozabilir. Dilimler sonradan birlestirilir. `yol` yukarida
    # tanimli cunku `_ileri` durum dizinini ondan tureti yor.
    # KOD SURUMU (rapor A40). 'Dosya var' ile 'gecerli bilimsel veri
    # var' ayni sey degil: L1 bir kez 47 saniyede COMPLETED donup
    # HICBIR SEY kosmadi cunku devam mantigi iki gun eski kodla ve
    # provenance kaydi olmadan uretilmis satirlari 'tamam' saydi.
    # Artik surumu uysmayan satir GECERSIZ ve o nokta yeniden kosulur.
    surum = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True,
        text=True, check=False).stdout.strip() or None
    print(f"  kod surumu  : {surum or 'BILINMIYOR'}", flush=True)
    durum = ensemble_kos(tasarim, _ileri, yol, root_seed=kok,
                         ilerleme=_ilerleme, surum=surum)
    print(chr(10) + f"  tamamlanan : {durum.tamamlanan}/{durum.toplam}", flush=True)
    print(f"  dusen      : {durum.dusen}   atlanan: {durum.atlanan}", flush=True)
    if durum.bozuk_satir:
        print(f"  BOZUK SATIR: {durum.bozuk_satir} -- kesinti aninda "
              f"yarim yazilmis; o noktalar yeniden kosuldu", flush=True)
    print(f"  duvar      : {time.perf_counter() - t0:.0f} s", flush=True)
    ozet = yol.with_suffix(".ozet.json")
    ozet.write_text(json.dumps({
        "n_nokta": int(durum.toplam), "n_tamam": int(durum.tamamlanan),
        "n_dusen": int(durum.dusen), "n_atlanan": int(durum.atlanan),
        "n_bozuk_satir": int(durum.bozuk_satir),
        "merdiven": list(MERDIVEN),
        "t_end": a.t_end, "spacing": a.spacing, "root_seed": kok,
        "sok_kapisi": not a.sok_kapisi_kapali, "dilim": a.dilim,
        "surum": surum,
        "n_tasarim_tam": int(tam_n),
        "gozlenebilirler": list(GOZLENEBILIRLER),
        "duvar_s": time.perf_counter() - t0,
    }, indent=2))
    print(f"\nyazildi: {a.out}  ve  {ozet}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
