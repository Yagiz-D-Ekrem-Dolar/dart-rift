"""FAZ 4.6 — sentetik kurtarma (G4-C)

Üç aşama:

1. **Tasarım** — `factorial_design` (kenarlar) + `lhs_design` (iç kapsama).
   Determinist (ADR-0004, `inference_design` akışı).
2. **İleri koşular** — her tasarım noktası için DART sahnesi kurulup
   çalıştırılır, gözlenebilirler çıkarılır. **GPU gerekir.**
3. **Kurtarma** — vekil kurulur, posterior hesaplanır, G4-C üç sınavı
   uygulanır.

## Neden `--kuru` kipi var

Çıkarım katmanı ileri modelden **bağımsızdır** ve pahalı koşular
harcanmadan **önce** sınanmalıdır. `--kuru` bilinen analitik bir
haritayla tüm hattı uçtan uca koşturur: makine bozuksa burada belli
olur.

> `--kuru` sonucu bir **bilimsel iddia değildir**; hattın çalıştığının
> kanıtıdır. Çıktıya `kuru: true` yazılır ve rapor bunu **ayrı**
> işaretler.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

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


from dartrift.inference.design import (DART_UZAYI, factorial_design,  # noqa: E402
                                       lhs_design)
from dartrift.inference.forward import GOZLENEBILIRLER  # noqa: E402
from dartrift.inference.forward import ileri_kosu as _gercek_ileri  # noqa: E402
from dartrift.inference.posterior import grid_posterior  # noqa: E402
from dartrift.inference.recovery import recovery_verdict  # noqa: E402
from dartrift.inference.surrogate import fit_surrogate  # noqa: E402
from dartrift.validation.kosu_suresi import sure_denetimi  # noqa: E402

#: Nominal gözlem gürültüsü. **Uydurulmadı**: `beta` için ADR-0026'nın
#: hedeflediği `±0,1`; diğer ikisi FAZ 3'ün çıkarıcı duyarlılık
#: taramasından (P3-VR-03) alınacak — o ölçüm gelene kadar `beta`'nın
#: göreli gürültüsü kullanılıyor ve bu **açıkça** işaretli.
SIGMA_NOMINAL = (0.10, 0.10, 0.05)


def _analitik_harita(x: np.ndarray) -> np.ndarray:
    """`--kuru` kipinin ileri modeli — **bilinen** ve ucuz.

    Gerçek fizikle ilgisi yoktur; yalnızca çıkarım hattının uçtan uca
    çalıştığını göstermek için. Üç gözlenebilir, üç parametreye farklı
    biçimlerde bağlı olmalı — aksi halde çözüm dejenere olur ve C2
    yapay biçimde düşer.
    """
    u = DART_UZAYI.to_unit(x)
    a, y, f = u[:, 0], u[:, 1], u[:, 2]
    return np.column_stack([
        3.0 + 1.5 * a - 0.8 * y + 2.0 * f - 0.6 * a * f,
        90.0 + 40.0 * a - 25.0 * y + 10.0 * f,
        0.02 + 0.05 * f + 0.01 * a * y,
    ])


def ileri_kosu(x: np.ndarray, device: str, steps: int,
               r_ince: float, spacing: float, lam: int) -> np.ndarray:
    """Gerçek ileri model — `inference.forward.ileri_kosu`'ya bağlanır.

    .. warning::
       GPU kısmı **koşulmadı** (TRUBA kotası dolu). Ayrıntısı
       `inference/forward.py`'nin başlığında. Düşen noktalar `nan` kalır
       ve çağıran tarafta **sayılır** — sessizce atılmaz.
    """
    sys.path.insert(0, str(REPO / "scripts"))
    from faz44_dart_yakinsama import SAHNE, _malzeme

    def _ilerleme(i, n, mesaj):
        print(f"    [{i + 1}/{n}] {mesaj}", flush=True)

    return _gercek_ileri(x, material=_malzeme(), device=device, steps=steps,
                         r_ince=r_ince, spacing=spacing, lam=lam,
                         sahne_taban=SAHNE, ilerleme=_ilerleme)


def _sure_denetimi(a) -> dict:
    """`--steps` FAZ 4.5'in ölçtüğü durulma zamanına **yetiyor mu**?

    ## Neden gerekli

    `--steps 3000`, `dt ≈ 2,6e-5` ile `t ≈ 0,078 s` demek. FAZ 4.4 aynı
    sahnede `0,2 s`'ye `8000` adımda gitti.

    Erken kesilmiş bir koşu `β`'yı **sistematik olarak** küçük verir ve
    bütün tasarım noktalarını **aynı yönde** kaydırır. Vekil bunu bir
    kusur olarak göremez (`q2` yüksek kalır, yüzey düzgündür); posterior
    dar **ama yanlış** çıkar. Tam olarak ADR-0011 §3'ün dersi.

    > Kontrol **koşudan önce** yapılıyor: `~3` saatlik GPU'yu harcayıp
    > sonucun geçersiz olduğunu görmek pahalı.

    Dosya verilmezse denetim **yapılamaz** ve bu **yazılır** — sessizce
    geçilmez.
    """
    if a.kuru:
        return {"durum": "denetlenemedi", "kisa_kosu": None,
                "neden": "kuru kip — süre denetimi anlamsız"}

    # KARAR MANTIGI BURADA DEGIL: `validation/kosu_suresi.py`de ve 17
    # testle sinaniyor. Burada yalnizca dosya okuma ve raporlama var.
    # Ilk surumde mantik bu betigin icindeydi; raporun iki kez kaydettigi
    # "ayni buyuklugu iki yerde tanimlamak" kalibina girmemek icin disari
    # alindi.
    veri = (json.loads(Path(a.faz45).read_text(encoding="utf-8"))
            if a.faz45 else None)
    out = sure_denetimi(veri, a.steps)
    out["faz45_yolu"] = a.faz45

    if not a.faz45:
        print("\n[0] SURE DENETIMI YAPILMADI: `--faz45` verilmedi — koşu "
              "süresinin yeterliliği DENETLENMEDI", flush=True)
        return out

    print("\n[0] SURE DENETIMI (FAZ 4.5: " + str(a.faz45) + ")", flush=True)
    if out["durum"] == "denetlenemedi":
        print("    DENETLENEMEDI: " + out["neden"], flush=True)
        return out

    print(f"    durulma (FAZ 4.5)  = {out['t_durulma_s']:.4e} s", flush=True)
    print(f"    bu kosu (kestirim) = {out['t_kestirim_s']:.4e} s "
          f"({a.steps} adim x {out['dt_ort_s']:.3e} s)", flush=True)
    if out["durum"] == "kisa":
        print("    KISA KOSU: " + out["neden"], flush=True)
        if not a.kisa_kosuya_izin:
            raise SystemExit(
                "\nFAZ 4.6 DURDURULDU: " + out["neden"] + ".\n"
                "  Erken kesilen kosu beta'yi SISTEMATIK olarak kucuk verir\n"
                "  ve posterior dar AMA YANLIS cikar (ADR-0011 §3).\n"
                "  Bilerek kisa kosmak icin: --kisa-kosuya-izin")
    else:
        print("    YETERLI", flush=True)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kuru", action="store_true",
                    help="analitik haritayla hattı sına (GPU gerekmez)")
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--steps", type=int, default=3000)
    ap.add_argument("--n-lhs", type=int, default=40)
    ap.add_argument("--root-seed", type=int, default=20260808)
    ap.add_argument("--n-grid", type=int, default=48)
    ap.add_argument("--r-ince", type=float, default=25.0)
    ap.add_argument("--spacing", type=float, default=7.0)
    ap.add_argument("--lam", type=int, default=2)
    ap.add_argument("--out", default=str(REPO.parent / "faz46_sonuc.json"))
    # FAZ 4.5'in cikti dosyasi. Verilirse `--steps`in YETERLI olup
    # olmadigi ONCEDEN denetlenir; bkz. `_sure_denetimi`.
    ap.add_argument("--faz45", default=None,
                    help="FAZ 4.5 sonuc JSON'u — kosu suresini dogrular")
    ap.add_argument("--kisa-kosuya-izin", action="store_true",
                    help="FAZ 4.5 durulma zamanina ULASILMASA da kos")
    a = ap.parse_args()

    print("=" * 78, flush=True)
    print(f"FAZ 4.6 — SENTETIK KURTARMA (G4-C){'  [KURU KIP]' if a.kuru else ''}",
          flush=True)
    print("=" * 78, flush=True)

    kisa = _sure_denetimi(a)

    # --- 1) tasarim
    x_kenar = factorial_design(DART_UZAYI, 3)
    x_ic = lhs_design(DART_UZAYI, a.n_lhs, root_seed=a.root_seed)
    x = np.vstack([x_kenar, x_ic])
    print(f"\n[1] tasarim: {len(x_kenar)} kenar + {len(x_ic)} LHS = {len(x)} nokta",
          flush=True)
    for j, ad in enumerate(DART_UZAYI.names):
        print(f"    {ad:12s} [{x[:, j].min():.4g}, {x[:, j].max():.4g}]",
              flush=True)

    # --- 2) ileri kosular
    t0 = time.perf_counter()
    if a.kuru:
        Y = _analitik_harita(x)
        print(f"\n[2] ileri model: ANALITIK (kuru kip) — {len(x)} nokta",
              flush=True)
    else:
        print(f"\n[2] ileri model: GERCEK — {len(x)} GPU kosusu", flush=True)
        # KALDIGI YERDEN DEVAM: her nokta hemen JSONL'e yaziliyor. Bir SLURM
        # isi 12 saatte kesiliyor ve 300 kosuluk ensemble ~10 GPU-gunu
        # (KAYIT-040) -- yani kesinti KACINILMAZ, olasi degil.
        from dartrift.inference.ensemble import (ensemble_kos,
                                                oku_tamamlananlar)
        from dartrift.inference.forward import ileri_kosu as _tek_nokta

        sys.path.insert(0, str(REPO / "scripts"))
        from faz44_dart_yakinsama import SAHNE, _malzeme

        jsonl = Path(a.out).with_suffix(".jsonl")
        _mat = _malzeme()

        def _bir(th):
            # GEREKCEYI YUTMA. `ileri_kosu` dusen noktayi `nan` birakip
            # sebebi yalnizca kendi `ilerleme`sine yaziyor. Burada o geri
            # cagri VERILMEDIGI icin disariya sadece "sonlu olmayan cikti:
            # [nan nan nan]" ciiyordu ve kok neden GORUNMUYORDU.
            #
            # Duman testinde tam bu oldu: 29/29 nokta dustu ve gercek
            # sebep ("matrix_alpha0 ile rho_yigin tutarsiz", ADR-0044)
            # ancak nokta ELLE kosulunca goruldu.
            gerekce: list = []
            y = _tek_nokta(th[None, :], material=_mat, device=a.device,
                           steps=a.steps, r_ince=a.r_ince,
                           spacing=a.spacing, lam=a.lam,
                           sahne_taban=SAHNE,
                           ilerleme=lambda i, n, m: gerekce.append(m))[0]
            if not np.all(np.isfinite(y)) and gerekce:
                # `ileri_kosu` mesaji zaten "DUSTU: " ile basliyor ve
                # `ensemble_kos` bir tane daha ekliyor -> "DUSTU: DUSTU:".
                raise RuntimeError(gerekce[-1].removeprefix("DUSTU: "))
            return y

        def _ilerleme(i, n, mesaj):
            print(f"    [{i + 1}/{n}] {mesaj}", flush=True)

        durum = ensemble_kos(x, _bir, jsonl, root_seed=a.root_seed,
                             ilerleme=_ilerleme)
        print(f"    ensemble: tamamlanan={durum.tamamlanan} "
              f"dusen={durum.dusen} atlanan={durum.atlanan} "
              f"bozuk_satir={durum.bozuk_satir}", flush=True)
        print(f"    devam dosyasi: {jsonl}", flush=True)
        tamam, _ = oku_tamamlananlar(jsonl, root_seed=a.root_seed)
        Y = np.full((len(x), len(GOZLENEBILIRLER)), np.nan)
        for _i, _v in tamam.items():
            if _v is not None and _i < len(Y):
                Y[_i] = _v
        dusen = int(np.count_nonzero(~np.all(np.isfinite(Y), axis=1)))
        if dusen:
            # SEYRELME GIZLENMEZ: dusen nokta tasarimin kapsamasini bozar
            # ve vekilin q2'si sessizce kotulesir.
            print(f"    DUSEN NOKTA: {dusen}/{len(x)} -- tasarim seyreldi",
                  flush=True)
            tut = np.all(np.isfinite(Y), axis=1)
            x, Y = x[tut], Y[tut]
            # HEPSI dustuyse `fit_surrogate` kafa karistirici bir hata
            # verirdi ("n <= p"). Kok neden burada soyleniyor.
            if len(x) == 0:
                raise SystemExit(
                    "DURDURULDU: TASARIMIN TAMAMI dustu. Ileri model hic "
                    "gecerli sonuc uretmedi -- sahne kurulumu ya da malzeme "
                    "parametreleri gozden gecirilmeli. (forward.py'nin "
                    "ilerleme satirlari her noktanin nedenini yazdi.)")
            if len(x) < 12:
                raise SystemExit(
                    f"DURDURULDU: yalnizca {len(x)} nokta ayakta kaldi; "
                    f"ikinci derece vekil 10 katsayi ister ve LOO icin "
                    f"n > p gerekir. Tasarim COK seyreldi.")
    print(f"    {time.perf_counter() - t0:.1f} s", flush=True)

    # --- 3) vekiller
    print("\n[3] vekiller", flush=True)
    vekiller = []
    for k, ad in enumerate(GOZLENEBILIRLER):
        s = fit_surrogate(DART_UZAYI, x, Y[:, k])
        vekiller.append(s)
        tani = ("SABIT -- ILERI MODEL BOZUK OLABILIR" if s.sabit
                else "GUVENILIR" if s.guvenilir else "YETERSIZ")
        print(f"    {ad:20s} q2={s.q2:8.5f}  rmse_loo={s.rmse_loo:.4e}  "
              f"sigma={s.sigma:.4e}  {tani}", flush=True)
    yetersiz = [ad for ad, s in zip(GOZLENEBILIRLER, vekiller)
                if not s.guvenilir]
    sabitler = [ad for ad, s in zip(GOZLENEBILIRLER, vekiller) if s.sabit]
    if sabitler:
        # SABIT bir gozlenebilir "yetersiz vekil" degil, BOZUK ILERI MODEL
        # isaretidir. Devam etmek butun kosuyu bosa harcar.
        raise SystemExit(
            f"DURDURULDU: {sabitler} gozlenebilirleri HIC DEGISMIYOR. "
            f"Muhtemel neden: theta sahneye ulasmiyor (forward.py basligi). "
            f"Cikarim kosturmak bosuna olurdu.")
    if yetersiz:
        print(f"    UYARI: {yetersiz} vekilleri YETERSIZ (q2 <= 0.5). "
              f"Posterior yine hesaplanacak ama yargi guvenilmez.", flush=True)

    # --- 4) gercek deger ve sentetik veri
    gercek = np.array([1.55, 3.0e5, 0.30])
    veri = np.array([float(s.predict(gercek[None, :])[0]) for s in vekiller])
    print(f"\n[4] gercek parametre: "
          + ", ".join(f"{ad}={v:.4g}" for ad, v in zip(DART_UZAYI.names, gercek)),
          flush=True)
    print("    sentetik veri: "
          + ", ".join(f"{ad}={v:.5g}" for ad, v in zip(GOZLENEBILIRLER, veri)),
          flush=True)

    # --- 5) posterior + gurultu taramasi (C3)
    print("\n[5] posterior", flush=True)
    post = grid_posterior(DART_UZAYI, vekiller, veri, SIGMA_NOMINAL,
                          n_grid=a.n_grid)
    tarama = [(c, grid_posterior(DART_UZAYI, vekiller, veri,
                                 tuple(c * s for s in SIGMA_NOMINAL),
                                 n_grid=a.n_grid))
              for c in (1.0, 4.0, 16.0)]
    for j, ad in enumerate(DART_UZAYI.names):
        lo, hi = post.hdi(j)
        print(f"    {ad:12s} gercek={gercek[j]:10.4g}  "
              f"%68=[{lo:.4g}, {hi:.4g}]  "
              f"bant/onsel={post.width_u[j]:.3f}", flush=True)

    # --- 6) G4-C
    print("\n[6] G4-C", flush=True)
    v = recovery_verdict(post, gercek, tarama)
    print(f"    {v.ozet}", flush=True)
    for d in v.c1_ayrinti:
        print(f"      C1 {d['ad']:12s} {'ICERIYOR' if d['iceriyor'] else 'DISARIDA'}"
              f"  gercek={d['gercek']:.4g}  bant={d['bant'][0]:.4g}..{d['bant'][1]:.4g}",
              flush=True)
    if v.c3_kosuldu:
        c = v.c3_ayrinti
        print(f"      C3 eksen={c['eksen']}  genislikler="
              f"{[round(g, 4) for g in c['genislikler']]}  "
              f"buyume={c['buyume_orani']:.2f}x", flush=True)
    print(f"\n    G4-C {'GECTI' if v.gecti else 'GECMEDI'}"
          f"{'  (KURU KIP -- bilimsel iddia DEGIL)' if a.kuru else ''}",
          flush=True)

    Path(a.out).write_text(json.dumps({
        "kuru": bool(a.kuru), "root_seed": a.root_seed,
        "n_tasarim": int(len(x)), "gercek": gercek.tolist(),
        "sigma_nominal": list(SIGMA_NOMINAL),
        "vekil_q2": {ad: float(s.q2) for ad, s in zip(GOZLENEBILIRLER, vekiller)},
        "vekil_guvenilir": {ad: bool(s.guvenilir)
                            for ad, s in zip(GOZLENEBILIRLER, vekiller)},
        "c1_gecti": v.c1_gecti, "c1_kapsama": v.c1_kapsama,
        "c1_ayrinti": v.c1_ayrinti,
        "c2_gecti": v.c2_gecti, "c2_en_dar": v.c2_en_dar,
        "c2_genislikler": v.c2_genislikler,
        "c3_kosuldu": v.c3_kosuldu, "c3_gecti": v.c3_gecti,
        "c3_ayrinti": v.c3_ayrinti,
        "G4C_gecti": v.gecti,
        # SURE DENETIMI ciktiya YAZILIR. Denetlenmeden kosulmus bir
        # ensemble ile durulmaya kadar kosulmus olan ayni sayilmamali;
        # `kuru: true`nun yaptigi ayrimin aynisi.
        "sure_denetimi": kisa,
    }, indent=2))
    print(f"\nyazildi: {a.out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
