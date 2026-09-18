"""PROTOKOL-W2 §3 — duman koşusu kabulü (KİLİTLİ; β YAZDIRILMAZ).

Kabul: donmuş parçacık sayısı `>= 1` **ve** `momentum_artik_bagil <= 1e-4`.
Tutmazsa W2 gönderilmez. Betik bilerek `β` okumaz/yazmaz: tekrar kararı
sonuca değil geçerliliğe bakmalı (KAYIT-066 §4).

Kullanim:
    python scripts/w2_duman_kontrol.py --npz ".../W2D_duman.durumlar/*.npz"
"""
from __future__ import annotations

import argparse
import glob
import json

import numpy as np

ARTIK_ESIGI_DUMAN = 1.0e-4
DONMUS_EN_AZ = 1


def karar(*, donmus: int, artik: float) -> dict:
    """W2 §3 kuralı."""
    tamam = (int(donmus) >= DONMUS_EN_AZ
             and np.isfinite(artik) and float(artik) <= ARTIK_ESIGI_DUMAN)
    return {"kabul": bool(tamam), "donmus": int(donmus), "artik": float(artik),
            "esik_artik": ARTIK_ESIGI_DUMAN, "esik_donmus": DONMUS_EN_AZ,
            "sonuc": "W2 GONDERILEBILIR" if tamam else "W2 GONDERILMEZ"}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--npz", required=True)
    a = ap.parse_args(argv)
    dosyalar = sorted(glob.glob(a.npz))
    if not dosyalar:
        raise SystemExit(f"npz bulunamadi: {a.npz}")
    z = np.load(dosyalar[-1])
    ft = json.loads(str(z["fizik_tani"]))
    gc = json.loads(str(z["gecerlilik"]))
    k = karar(donmus=int(ft.get("dondurulmus", 0)),
              artik=float(gc["degerler"]["momentum_artik_bagil"]))
    print("PROTOKOL W2 S3 -- duman kabulu (beta YAZDIRILMAZ)")
    print(f"  t = {float(z['t']):.3f} s   gecerli = {gc['gecerli']}   "
          f"kontroller = {gc['kontroller']}")
    print(f"  donmus = {k['donmus']} (>= {k['esik_donmus']})   "
          f"artik = {k['artik']:.3e} (<= {k['esik_artik']:.0e})")
    print(f"  SONUC: {k['sonuc']}")
    return 0 if k["kabul"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
