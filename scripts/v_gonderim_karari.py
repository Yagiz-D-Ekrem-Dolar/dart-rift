"""Protokol V gönderim kararı — U sonucundan kilitli kuralla (PROTOKOL-V-MODEL2 §0, §2).

U genel yargısı **HİÇBİR VARYANT ULAŞMIYOR** ise V gönderilir; V4'ün ek
bayrakları U'daki en küçük `|z|`'li varyantın bayraklarıdır (U iş betiğindeki
`EK` dizisiyle **aynı** tablo — sınav tutarlılığı denetler). Aksi halde V
gönderilmez. Betik kararı ve (gerekiyorsa) tam `sbatch` komutunu yazar;
**kendisi göndermez**.

A84: `--export` değerlerinde virgül yok; bayraklar boşlukla.

Kullanim:
    python scripts/v_gonderim_karari.py --s-u kampanya/S_U.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

#: truba/is_U_model.slurm `EK` dizisiyle aynı (test_v_gonderim_karari sınar).
U_BAYRAKLARI = {
    "U0": "",
    "U1": "--onsel-disi-izin",
    "U2": "--onsel-disi-izin",
    "U3": "--mu-f 0.2",
    "U4": "--mu-f 0.05",
    "U5": "--porozite-pe 1e5 --porozite-ps 1e7",
    "U6": "--yigin-yogunlugu 1500",
    "U8": "--onsel-disi-izin --mu-f 0.2 --porozite-pe 1e5 --porozite-ps 1e7 --yigin-yogunlugu 1500",
}


def karar(s_u: dict) -> dict:
    genel = s_u.get("genel", "")
    if genel.startswith("MODEL GOZLEME ULASABILIYOR"):
        return {"gonder": False, "sebep": f"U: {genel}", "komut": None}
    if not genel.startswith("HICBIR VARYANT ULASMIYOR"):
        return {"gonder": False, "sebep": f"U okunamadi: {genel or 'genel yok'}", "komut": None}
    okunur = {k: r for k, r in (s_u.get("satirlar") or {}).items()
              if r.get("karar") not in (None, "OKUNMAZ") and "z" in r}
    if not okunur:
        return {"gonder": False, "sebep": "U satirlari okunamadi", "komut": None}
    en = min(okunur, key=lambda k: abs(okunur[k]["z"]))
    varyant = okunur[en]["varyant"] if "varyant" in okunur[en] else en.split(":")[0]
    ek = U_BAYRAKLARI[varyant]
    if "," in ek:
        raise ValueError("A84: V4_EK icinde virgul olamaz")
    komut = (f'sbatch --export=ALL,V4_EK="{ek}",V4_U={varyant} is/is_V_model.slurm')
    return {"gonder": True, "sebep": f"U: {genel}", "en_yakin": en, "V4_U": varyant,
            "V4_EK": ek, "komut": komut}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--s-u", type=Path, required=True)
    a = ap.parse_args(argv)
    k = karar(json.loads(a.s_u.read_text(encoding="utf-8")))
    print(json.dumps(k, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
