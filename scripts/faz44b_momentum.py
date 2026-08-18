"""FAZ 4.4b — boşluk 3'ün kalanı: **iletilen momentum** gözlenebiliriyle

KAYIT-036 §3 gözenekli kolun ölçülemediğini yazdı: cephe yarıçapı
doygunlaşıyor ve kutu "arayüzü geç" ile "kenara varma" şartlarını aynı
anda sağlayamıyor.

Çözüm kutuyu büyütmek **değil** (pahalı ve gereksiz), gözlenebiliri
değiştirmek: `r > 0,30`'dan geçen toplam **dışarı doğru radyal momentum**.
Bu bir eşik değil bir integraldir; doygunlaşacak tavanı yoktur.

İlk denemem arayüzü küçültmekti (`r_iç: 0,15 → 0,06`) ve **yanlıştı**:
enjeksiyon yarıçapı `0,094`, yani arayüzden büyük olurdu — enerji ince
bölgenin dışına konurdu. Kaba kafesin kaynağı çözmesi `h_inj ≳ 3·dx`
gerektiriyor, o da `r_iç ≥ 0,15` demek. Kısıt gerçek, kaçamak yok.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path  # noqa: E402

# Depo koku __file__'DAN turetiliyor, sabit yazilmiyor: depo
# tasindiginda ya da baska bir kullaniciyla kosuldugunda sabit
# yol SESSIZCE yanlis src'yi bulur (ya da hic bulmaz).
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

# Cikti UTF-8'e sabitleniyor: baslıklarda `—` ve `A′` geciyor ve bir
# raporlama betiginin UnicodeEncodeError ile dusmesi raporu yok eder.
# SLURM isi PYTHONIOENCODING=utf-8 veriyor ama betik ELLE de kosulabilir.
for _akis in (sys.stdout, sys.stderr):
    try:
        _akis.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


from dartrift.validation.solid_interface import (  # noqa: E402
    BASALT_SOLID,
    R_SONDA,
    _malzeme,
    run_solid_interface_momentum,
)

DEV = "cuda:0"
N_KABA = 32
R_IC = 0.15
T_END = 3.0e-5


def _yaz(y: dict) -> None:
    print(f"     yargi    = {y['yargi']}", flush=True)
    print(f"     parantez = [{y['parantez'][0]:.6e}, {y['parantez'][1]:.6e}]"
          f"  (genislik {y['parantez_genisligi_rel']:.3%})", flush=True)
    print(f"     iki bol. = {y['iki_bolgeli_p']:.6e}", flush=True)
    print(f"     TASMA    = {y['tasma_rel']:.4%}", flush=True)
    print(f"     on kosul : ayirt={y['kollar_ayirt_edilebilir']} "
          f"enerji={y['enerji_esit']} bolge={y['enjeksiyon_bolgesi_ayni']} "
          f"kutle={y['kutle_ihmal_edilebilir']}", flush=True)
    for ad in ("tekduze_kaba", "iki_bolgeli", "tekduze_ince"):
        k = y[ad]
        r = k.get("r_measured")
        print(f"       {ad:14s} N={k['N']:7d}  p={k['p_iletilen']:.6e}  "
              f"cephe={'DOYGUN' if r is None else format(r, '.5f')}  "
              f"adim={k['n_steps']}", flush=True)


def main() -> int:
    print("=" * 78, flush=True)
    print("FAZ 4.4b — BOSLUK 3'UN KALANI (iletilen momentum)", flush=True)
    print("=" * 78, flush=True)
    print(f"r_sonda = {R_SONDA}, r_ic = {R_IC}, t_end = {T_END:.3e}\n",
          flush=True)

    sonuclar = {}
    for ad, mat, pph in (
            ("yalniz-EOS", _malzeme(False, False, False), True),
            ("mukavemet", _malzeme(True, False, False), True),
            ("muk+gozenek", _malzeme(True, True, False), True),
            ("TAM-Aprime", BASALT_SOLID, True),
            ("TAM-tek-h", BASALT_SOLID, False)):
        print(f"  -- {ad}", flush=True)
        try:
            y = run_solid_interface_momentum(N_KABA, 2, R_IC, DEV, T_END, mat,
                                             per_particle_h=pph, etiket=ad)
            _yaz(y)
            sonuclar[ad] = y
        except RuntimeError as e:
            print(f"     OLCULEMEDI: {e}", flush=True)
            sonuclar[ad] = {"yargi": "olculemedi", "neden": str(e),
                            "tasma_rel": float("nan")}

    with open(REPO.parent / "faz44b_sonuc.json", "w") as f:
        json.dump({"t_end": T_END, "r_ic": R_IC, "r_sonda": R_SONDA,
                   "sonuclar": sonuclar}, f, indent=2)
    print("\nyazildi: faz44b_sonuc.json", flush=True)

    print("\nOZET", flush=True)
    for ad, y in sonuclar.items():
        print(f"    {ad:14s} yargi={y['yargi']:18s} "
              f"tasma={y['tasma_rel']:.4%}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
