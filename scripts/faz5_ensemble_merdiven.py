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

#: Kaba merdiven -- `Rb_R1` olcegi. Olculen: `N = 17 201`,
#: `00:05:06`/kosu. `MERDIVEN` (orta) `N = 69 886` ve `~1,2 sa`.
#: 48 kosuluk bir ayirt edilebilirlik taramasi orta olcekte
#: `58` saat, kaba olcekte `4` saat surer.
MERDIVEN_KABA = ("48:5.6", "24:2.8", "12:1.4", "6:0.7", "3:0.35")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-lhs", type=int, default=32,
                    help="Latin hiperkup nokta sayisi (kenarlar ayrica)")
    ap.add_argument("--kenarlar", action="store_true",
                    help="tam carpanli kenar noktalarini da ekle")
    ap.add_argument("--tasarim-dosyasi", type=Path, default=None,
                    help="JSON {'theta': [[a_b, Y0, f], ...]} -- LHS YERINE "
                         "acik nokta listesi (Protokol L duyarlilik pilotu)")
    ap.add_argument("--t-end", type=float, default=0.2)
    ap.add_argument("--spacing", type=float, default=7.0)
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--root-seed", type=int, default=None)
    ap.add_argument("--matris-cekme-yok", action="store_true",
                    help="TANI KOLU (E2 sonucu): matris hedef "
                         "parcaciklarinda negatif basinci sifira kirp. "
                         "Uretim modeli DEGIL.")
    ap.add_argument("--sahne-tohum", type=int, default=None,
                    help="SAHNE gerceklemesi (blok yerlesimi, hasar) "
                         "icin ayri tohum. Verilmezse tasarim tohumu. "
                         "Protokol G gurultu tabani bunu kullanir.")
    ap.add_argument("--kademeler", nargs="+", default=None,
                    help="r:s ciftleri, ikisi de METRE. Verilmezse "
                         "uretim merdiveni. `kaba` kisayolu R1 "
                         "olcegini kurar (N = 17 201, 5 dk/nokta).")
    ap.add_argument("--alpha-av", type=float, default=1.0,
                    help="yapay viskozite dogrusal terim (uretim 1,0). "
                         "A56: bu ensemble'a hic gecmiyordu.")
    ap.add_argument("--beta-av", type=float, default=2.0,
                    help="yapay viskozite karesel terim (uretim 2,0)")
    ap.add_argument("--cfl", type=float, default=0.25,
                    help="zaman adimi carpani (uretim 0,25). Protokol J: "
                         "SABIT h'de Delta t yarilama deneyi (A72).")
    ap.add_argument("--akma-kipi", choices=("son", "ara"), default="son",
                    help="'son' eski davranis (kuvvet GERI DONDURULMEMIS "
                         "gerilmeyi gorur); 'ara' her kuvvet cagrisindan "
                         "once akma yuzeyine donus (A72)")
    ap.add_argument("--blok-uretici", choices=("v1", "v2"), default="v1",
                    help="'v1' eski (doyar, sessiz); 'v2' GERCEK hacim "
                         "kesrine ulasir ya da hata verir (A74)")
    ap.add_argument("--malzeme-kaynagi", choices=("kaba", "geometri"),
                    default="kaba",
                    help="ince parcacik malzemesi: 'kaba' ebeveynden kopya "
                         "(eski) ya da 'geometri' surekli blok alanindan (A74)")
    ap.add_argument("--komsu-arama", choices=("hash", "bvh"), default="hash",
                    help="'hash' tek kuresel yaricap (eski); 'bvh' destek "
                         "kutulu BVH + sirali CSR (A52)")
    ap.add_argument("--blok-rmin", type=float, default=None,
                    help="blok yaricapi alt siniri [m] (SAHNE: 14)")
    ap.add_argument("--blok-rmax", type=float, default=None,
                    help="blok yaricapi ust siniri [m] (SAHNE: 42)")
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
    # A57: TASARIM tohumu ile SAHNE tohumu AYRI olmali.
    #
    # Tek tohum ikisini birden suruyordu: `lhs_design(..., root_seed=kok)`
    # VE `sahne_taban={**SAHNE, "root_seed": kok}`. Protokol G ayni 24
    # noktayi IKI gerceklemeyle kosup gurultu tabanini olcuyor; tek
    # tohumla ikinci kol FARKLI theta'lar orneklerdi ve `ayirt_raporu`
    # hicbir eslesme bulamazdi (F = nan). Kampanya cope giderdi.
    #
    # Varsayilan DEGISMIYOR: verilmezse sahne tohumu tasarim tohumudur.
    sahne_kok = kok if a.sahne_tohum is None else int(a.sahne_tohum)
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
    if a.tasarim_dosyasi is not None:
        # ACIK TASARIM (Protokol L): noktalar dosyadan, LHS kullanilmaz.
        # Uzay sinirlari yine denetlenir -- onsel disi nokta sessizce
        # kosulmasin.
        tasarim = np.atleast_2d(np.asarray(
            json.loads(a.tasarim_dosyasi.read_text(encoding="utf-8"))["theta"],
            dtype=np.float64))
        lo, hi = np.asarray(UZAY.lo, float), np.asarray(UZAY.hi, float)
        if tasarim.shape[1] != 3 or np.any(tasarim < lo) or np.any(tasarim > hi):
            raise SystemExit(f"tasarim dosyasi onsel sinirlarinin disinda: "
                             f"{tasarim.tolist()} (lo={lo}, hi={hi})")
    else:
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

    # `kaba` kisayolu -- yazim hatasi riskini kaldirir.
    if a.kademeler is None:
        merdiven = MERDIVEN
    elif list(a.kademeler) == ["kaba"]:
        merdiven = MERDIVEN_KABA
    else:
        merdiven = tuple(a.kademeler)

    print("=" * 78, flush=True)
    print("FAZ 5 — MERDIVENLI ENSEMBLE", flush=True)
    print("=" * 78, flush=True)
    print(f"  uzay        : {UZAY.names}"
          f"{'  [TERK EDILMIS]' if a.eski_uzay else ''}", flush=True)
    print(f"  nokta       : {len(tasarim)}  (lhs {a.n_lhs}"
          f"{' + kenarlar' if a.kenarlar else ''})", flush=True)
    print(f"  dilim       : {dilim_bilgi}", flush=True)
    print(f"  merdiven    : {' '.join(merdiven)}  (metre)", flush=True)
    print(f"  t_end       : {a.t_end} s", flush=True)
    print(f"  cfl         : {a.cfl}  (uretim 0,25)", flush=True)
    print(f"  akma kipi   : {a.akma_kipi}", flush=True)
    # A74: sahne tabani -- varsayilanlar verilmezse SAHNE AYNEN kalir
    # (bit-ayni); verilen her alan `_fizik_ozeti`ne sahne_taban
    # uzerinden girer.
    sahne_ek = {}
    if a.blok_uretici != "v1":
        sahne_ek["blok_uretici"] = a.blok_uretici
    if a.blok_rmin is not None:
        sahne_ek["r_min"] = float(a.blok_rmin)
    if a.blok_rmax is not None:
        sahne_ek["r_max"] = float(a.blok_rmax)
    print(f"  blok alani  : uretici={a.blok_uretici}  malzeme={a.malzeme_kaynagi}"
          f"  {sahne_ek or '(SAHNE varsayilani)'}", flush=True)
    print(f"  sok kapisi  : {'KAPALI (TANI)' if a.sok_kapisi_kapali else 'ACIK'}",
          flush=True)
    print(f"  gozlenebilir: {GOZLENEBILIRLER}", flush=True)
    print(f"  root_seed   : {kok}  (tasarim)", flush=True)
    print(f"  sahne_tohum : {sahne_kok}  (gerceklem)", flush=True)

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
            t_end=a.t_end, kademeler=merdiven, spacing=a.spacing,
            # A46: `None` gecince `build_scene` VARSAYILANI `M0` oluyor ve
            # `M0` dalinda `boulders = None` -- yani `f_boulder` ve
            # `boulder_alpha0` SESSIZCE yoksayiliyordu. Uc cikarim
            # ekseninden IKISI sahneye hic ulasmiyordu. `SAHNE`'nin
            # kendisi `model_class = 'M1'` tasiyor; gonderilmiyordu.
            sahne_taban={**SAHNE, "root_seed": sahne_kok, **sahne_ek},
            sok_yargisi=not a.sok_kapisi_kapali,
            durum_dizini=yol.with_suffix(".durumlar"),
            surum=surum, alpha_av=a.alpha_av, beta_av=a.beta_av,
            matris_cekme_yok=a.matris_cekme_yok,
            cfl=a.cfl, akma_kipi=a.akma_kipi,
            malzeme_kaynagi=a.malzeme_kaynagi,
            komsu_arama=a.komsu_arama)[0]
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
        "merdiven": list(merdiven),
        "t_end": a.t_end, "spacing": a.spacing, "root_seed": kok,
        "sahne_tohum": sahne_kok,
        "sok_kapisi": not a.sok_kapisi_kapali, "dilim": a.dilim,
        "cfl": a.cfl, "akma_kipi": a.akma_kipi,
        "blok_uretici": a.blok_uretici, "malzeme_kaynagi": a.malzeme_kaynagi,
        "komsu_arama": a.komsu_arama,
        "sahne_ek": sahne_ek,
        "surum": surum,
        "n_tasarim_tam": int(tam_n),
        "gozlenebilirler": list(GOZLENEBILIRLER),
        "duvar_s": time.perf_counter() - t0,
    }, indent=2))
    print(f"\nyazildi: {a.out}  ve  {ozet}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
