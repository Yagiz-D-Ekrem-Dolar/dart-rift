"""FAZ 4.9 — `N_komşu` salınımı **DART geometrisinde** (ADR-0042 yükümlülüğü).

ADR-0042 `Ω ≡ 1` kararını *sabit `h` yeterli* ölçümüne dayandırdı ve o
ölçüm **küp** (Sedov) kurulumunda yapıldı: `N_komşu` `268,2 → 551,5`
(`2,06×`), çalışma aralığındaki yayılım `%0,607`, tolerans `%2`.

Aynı ADR kendi içine bir yükümlülük yazdı:

> *"DART kurulumunda ölçülen `N_komşu` salınımı `2,06×`'ı belirgin
> biçimde aşarsa … bu ADR yeniden açılır. Ölçüm FAZ 4.4'te DART
> geometrisinde **tekrarlanacaktır**."*

O tekrar yapılmadı; rapordaki A3'ün açık yarısı budur. Bu betik onu
kapatıyor.

## Neden küp ölçümü DART için yeterli değil

Üç fark var ve üçü de `N_komşu`'yu etkiliyor:

1. **Serbest yüzey.** Küp periyodik/geniş; DART bir küre. Yüzeydeki
   eksik komşuluk yapay bir düşük yoğunluk üretir, o yüzden bir iç
   bölge maskesi zorunlu — ama maskenin **nereye** konduğu kritik ve
   ilk sürümde yanlış kondu; bkz. [`_ic_maske`][].
2. **Parçacık başına `h`** (A′, ADR-0041). Küpte `h` tek bir skalerdi.
   `h ∝ s` ve `m ∝ s³ρ` olduğu için `N_komşu` **tasarımca** ince ve
   kaba bölgede aynı kalmalı — ama bu bir *tasarım niyeti*, ölçüm
   değil. Betik ince/kaba ayrı raporluyor.
3. **Gözeneklilik.** P-α'da SPH `rho` alanı **yığın** yoğunluğudur
   (`solver_solid.py:133`, `rho0/alpha0`), dolayısıyla `neighbour_count`
   doğrudan geometrik sayıyı verir. Ezilme (`α → 1`) yığın yoğunluğunu
   büyütür ve salınımı küpte olmayan bir yönden besler.

## Ölçüt önden yazıldı

Karar [`judge_dart_salinimi`][dartrift.validation.h_policy] içinde ve
ADR'nin **kendi kapsama mantığını** kullanıyor: kanıt, taramanın fiilen
kapsadığı `N_komşu` aralığında (`56,1 → 650,5`) geçerlidir. DART
salınımı o aralığın içindeyse kanıt çalışma noktasını kapsıyor,
dışındaysa ADR yeniden açılmalı.

> ADR *"belirgin biçimde"* eşiğini tanımsız bıraktı. Keyfî bir çarpan
> uydurmak yerine ADR'nin başka yerde kullandığı ölçüt alındı; bunun
> bir **yorum** olduğu çıktının `yorum` alanında taşınıyor.

## Örnekleme neden iki aşamada da yapılıyor

En büyük sıkışma çarpma anında, yani **aşama 1**'de (`λ = 19`). Aşama 2
uzun kuyruğu görüyor. Yalnızca birine bakmak salınımın yarısını
kaçırırdı.
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
sys.path.insert(0, str(REPO / "scripts"))
for _akis in (sys.stdout, sys.stderr):
    try:
        _akis.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

from faz44_dart_yakinsama import SAHNE  # noqa: E402
from faz48_iki_asama import T1_OLCULEN, _cozucu, _kos, _mat  # noqa: E402

from dartrift.setup.coarsen import komsu_sagligi  # noqa: E402
from dartrift.setup.refine import refine_scene_ucseviye  # noqa: E402
from dartrift.setup.scene import _build_mesh, build_scene  # noqa: E402
from dartrift.setup.two_stage import asama2_sahnesi_ucseviye  # noqa: E402
from dartrift.validation.h_policy import (  # noqa: E402
    KUP_SALINIMI,
    KUP_TARAMA_KAPSAMI,
    SUPPORT_OVER_H,
    dart_salinim_ozeti,
    judge_dart_salinimi,
    neighbour_count,
)


def _ic_maske(x, h, R: float, ic_frac: float) -> np.ndarray:
    """İç bölge: **çekirdek desteği cisme sığan** parçacıklar.

    ## Neden `r ≤ ic_frac·R` değil

    İlk sürümde küpün tarifi (`ic_frac = 0,6`) aynen kullanıldı ve
    salınım `1,000×` ölçüldü — `101` örnek, `207 252` değer, hepsi
    `379,1`. Bu bir sonuç değil **maske hatasıydı**:

    | | küp (Sedov) | DART |
    |---|---|---|
    | enerji nerede | **merkez** | **yüzey** |
    | `r ≤ 0,6R` neyi kapsar | şok bölgesini | **hiç şok görmeyen çekirdeği** |

    Krater `~10–15 m` derinlikte, cisim `R = 82 m`; `0,6R = 49 m`'nin
    içinde `∇·v ≈ 0` olduğu için `ρ` başlangıç değerinde kalıyor ve
    her matris parçacığının `ρ`'su **aynı** (`ρ₀/α₀`). Dolayısıyla
    `N_komşu` da aynı. Ölçüm çalışma noktasını kaçırmıştı.

    ## Kullanılan ölçüt

    `r_i + destek·h_i ≤ R` — yani parçacığın çekirdek desteği serbest
    yüzeyi kesmiyorsa iç sayılır. Bu **parçacık başına uyarlanır**:
    ince bölgede `h` küçük olduğu için krater çevresi **dahil** olur,
    kaba bölgede `h = 14 m` olduğu için yüzeyden uzak durulur.

    Amaç yüzeydeki eksik komşuluğun yapay düşük yoğunluğunu dışlamak;
    amaç şok görmüş bölgeyi dışlamak **değil**.

    `ic_frac` geriye dönük uyumluluk için tutuluyor: `< 1` verilirse
    eski davranış (küresel kesme) uygulanır ve çıktı bunu **söyler**.
    """
    r = np.linalg.norm(x, axis=1)
    if ic_frac < 1.0:
        return r <= ic_frac * R
    return (r + SUPPORT_OVER_H * np.asarray(h, dtype=np.float64)) <= R


def _sayilan(st, h, R, ic_frac: float, mermi: np.ndarray | None) -> dict:
    """`2h` yarıçapı içindeki komşuları **fiilen sayar** (çapraz kontrol).

    Analitik `neighbour_count` sayıyı `ρ/m` sayı yoğunluğundan türetiyor.
    O tahmin tekdüze paketleme varsayar; moloz yığınında ve genleşmiş
    bölgede tutmayabilir. Üretim aktarım tanısı `komşu medyan = 74,5`
    verirken nominal kafes `(4/3)π(2h/s)³ ≈ 268` verir — `3,6` kat fark.

    > İki sayı **çelişmiyor**: analitik formül ölçülen `ρ` ile
    > beslendiğinde fiilî paketlemeyi zaten içerir. Ama farkın büyüklüğü
    > kaydedilmeli, çünkü küp kanıtı da aynı formülle kuruldu ve
    > karşılaştırmanın **eşdeğer** olduğunu göstermek gerekiyor.

    Pahalı (ağaç kurar); yalnızca birkaç anda çağrılır.
    """
    maske = _ic_maske(st["x"], h, R, ic_frac)
    if mermi is not None:
        maske &= ~mermi
    if int(maske.sum()) < 32:
        return {}
    h_med = float(np.median(h[maske]))
    s = komsu_sagligi(st["x"][maske], h=h_med)
    return {"sayilan_medyan": float(s.get("komsu_medyan", float("nan"))),
            "sayilan_h": h_med, "sayilan_n": int(maske.sum())}


def _ornek(st, h, R, ic_frac: float, ince: np.ndarray | None,
           mermi: np.ndarray | None) -> dict:
    """Bir zaman örneği: iç bölgedeki `N_komşu` değerleri.

    Mermi **dışlanır**: kütlesi ve `h`'si hedeften mertebelerce farklı,
    ve `β` tartışmasında görüldüğü gibi kendi başına bir topluluk. Onu
    içeri katmak salınımı hedefin değil merminin salınımı yapardı.
    """
    maske = _ic_maske(st["x"], h, R, ic_frac)
    if mermi is not None:
        maske &= ~mermi
    if int(maske.sum()) < 32:
        return {"n_komsu": np.array([]), "n_ic": int(maske.sum())}
    nk = neighbour_count(st["rho"][maske], h[maske], st["m"][maske])
    out = {"n_komsu": nk, "n_ic": int(maske.sum()),
           "rho_ortanca": float(np.median(st["rho"][maske])),
           "alpha_ortanca": float(np.median(st["alpha"][maske]))}
    if ince is not None:
        for ad, sec in (("ince", ince[maske]), ("kaba", ~ince[maske])):
            if int(sec.sum()) >= 8:
                out[f"nk_{ad}_ortanca"] = float(np.median(nk[sec]))
                out[f"nk_{ad}_n"] = int(sec.sum())
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--lam1", type=float, default=19.0)
    ap.add_argument("--r-ince1", type=float, default=3.0)
    ap.add_argument("--lam2", type=float, default=2.0)
    ap.add_argument("--r-ince2", type=float, default=25.0)
    ap.add_argument("--t1", type=float, default=T1_OLCULEN)
    ap.add_argument("--t-end", type=float, default=0.20)
    ap.add_argument("--azami-adim", type=int, default=200000)
    ap.add_argument("--her", type=int, default=25,
                    help="kac adimda bir ornekle")
    ap.add_argument("--ic-frac", type=float, default=1.0,
                    help="1.0 -> destek olcutu (r + 2h <= R, ONERILEN); "
                         "<1 -> eski kuresel kesme r <= ic_frac*R")
    ap.add_argument("--out", default=str(REPO.parent / "faz49_komsu.json"))
    a = ap.parse_args()

    print("=" * 78, flush=True)
    print("FAZ 4.9 — N_komsu SALINIMI, DART GEOMETRISI (ADR-0042)", flush=True)
    print("=" * 78, flush=True)
    print(f"\nKUP kaniti (KAYIT-035): N_komsu {KUP_SALINIMI[0]:.1f} -> "
          f"{KUP_SALINIMI[1]:.1f}  ({KUP_SALINIMI[1]/KUP_SALINIMI[0]:.3f}x)",
          flush=True)
    print(f"Taramanin KAPSADIGI aralik: {KUP_TARAMA_KAPSAMI[0]:.1f} -> "
          f"{KUP_TARAMA_KAPSAMI[1]:.1f}", flush=True)
    print("\nOLCUT (veriye bakilmadan): DART araligi kapsamanin ICINDE "
          "kalirsa kanit gecerli;\n         DISINA cikarsa ADR-0042 "
          "yeniden acilir.", flush=True)

    t0 = time.perf_counter()
    kaba = build_scene(spacing=7.0, device="cpu", **SAHNE)
    mesh = _build_mesh("icosphere", radius=SAHNE["radius"], subdiv=4)
    R = float(kaba.target_radius)

    a1 = refine_scene_ucseviye(kaba, mesh, r1=a.r_ince1, lam1=a.lam1,
                               r2=a.r_ince2, lam2=a.lam2)
    ince1 = np.asarray(a1.is_fine, dtype=bool)
    mermi1 = np.asarray(a1.is_impactor, dtype=bool)
    h1 = np.asarray(a1.h, dtype=np.float64)
    print(f"\nASAMA-1: lam={a.lam1}, N={a1.n} (ince {int(ince1.sum())}), "
          f"R={R:.2f} m", flush=True)

    ornek1: list[dict] = []
    sol1 = _cozucu(a1.x, a1.v, a1.m, np.zeros(a1.n), a1.h,
                   a1.alpha0, a1.Y0, a.device, mat=_mat(False, False))
    # t=0 REFERANSI: rho bir degerlendirme yapilmadan hesaplanmaz
    # (KAYIT-035'te bu atlanip sifir raporlanmisti).
    sol1._eval()
    st0 = sol1.state_numpy()
    o0 = _ornek(st0, h1, R, a.ic_frac, ince1, mermi1)
    if o0["n_komsu"].size:
        print(f"  t=0 REFERANS: N_komsu ortanca = "
              f"{np.median(o0['n_komsu']):.1f}  (ic {o0['n_ic']} parcacik)",
              flush=True)
        print(f"    ince ortanca = {o0.get('nk_ince_ortanca', float('nan')):.1f}"
              f"   kaba ortanca = {o0.get('nk_kaba_ortanca', float('nan')):.1f}",
              flush=True)
        ornek1.append({**o0, "t": 0.0, "asama": 1})
    # CAPRAZ KONTROL: analitik formulun tekduze-paketleme varsayimi
    # DART sahnesinde tutuyor mu? Uretim tanisi 74,5 verirken nominal
    # kafes ~268 veriyor; fark kaydedilmeli.
    sayim0 = _sayilan(st0, h1, R, a.ic_frac, mermi1)
    if sayim0:
        print(f"    CAPRAZ: fiilen sayilan komsu medyani = "
              f"{sayim0['sayilan_medyan']:.1f}  "
              f"(analitik {np.median(o0['n_komsu']):.1f}, "
              f"oran {np.median(o0['n_komsu'])/max(sayim0['sayilan_medyan'],1e-9):.2f}x)",
              flush=True)

    def _al1(adim, tt, st):
        o = _ornek(st, h1, R, a.ic_frac, ince1, mermi1)
        if o["n_komsu"].size:
            ornek1.append({**o, "t": float(tt), "asama": 1})
        if adim % (a.her * 20) == 0:
            print(f"    a1 adim {adim:6d} t={tt:.4e}  "
                  f"N_komsu ort={np.median(o['n_komsu']):.1f}", flush=True)

    t = _kos(sol1, 0.0, a.t1, a.azami_adim, "a1", ornekle=_al1, her=a.her)
    print(f"  asama-1 bitti: t={t:.5e}, {len(ornek1)} ornek "
          f"({time.perf_counter() - t0:.1f} s)", flush=True)

    sahne = asama2_sahnesi_ucseviye(a1, sol1.state_numpy())
    h2 = np.asarray(sahne.h, dtype=np.float64)
    ince2 = (np.asarray(sahne.is_fine, dtype=bool)
             if hasattr(sahne, "is_fine") else None)
    mermi2 = (np.asarray(sahne.is_impactor, dtype=bool)
              if hasattr(sahne, "is_impactor") else None)
    print(f"\nASAMA-2: lam={a.lam2}, N={sahne.n}, t {t:.4e} -> {a.t_end}",
          flush=True)

    ornek2: list[dict] = []
    sol2 = _cozucu(sahne.x, sahne.v, sahne.m, sahne.e, sahne.h,
                   sahne.alpha0, sahne.Y0, a.device, mat=_mat(False, False))

    def _al2(adim, tt, st):
        o = _ornek(st, h2, R, a.ic_frac, ince2, mermi2)
        if o["n_komsu"].size:
            ornek2.append({**o, "t": float(tt), "asama": 2})
        if adim % (a.her * 20) == 0:
            print(f"    a2 adim {adim:6d} t={tt:.4e}  "
                  f"N_komsu ort={np.median(o['n_komsu']):.1f}", flush=True)

    t = _kos(sol2, t, a.t_end, a.azami_adim, "a2", ornekle=_al2, her=a.her)
    print(f"  asama-2 bitti: t={t:.5e}, {len(ornek2)} ornek "
          f"({time.perf_counter() - t0:.1f} s)", flush=True)
    sayim_son = _sayilan(sol2.state_numpy(), h2, R, a.ic_frac, mermi2)
    if sayim_son and ornek2:
        an = float(np.median(ornek2[-1]["n_komsu"]))
        print(f"    CAPRAZ (son): fiilen sayilan = "
              f"{sayim_son['sayilan_medyan']:.1f}   analitik = {an:.1f}   "
              f"oran = {an/max(sayim_son['sayilan_medyan'],1e-9):.2f}x",
              flush=True)

    # ------------------------------------------------------------ YARGI
    def _ozetle(ad, orn):
        if not orn:
            print(f"\n  {ad}: ornek YOK", flush=True)
            return None
        oz = dart_salinim_ozeti(orn)
        print(f"\n  {ad}: {oz['n_ornek']} ornek, {oz['n_deger']} deger",
              flush=True)
        print(f"    N_komsu p01..p99 = {oz['N_komsu_p01']:.1f} .. "
              f"{oz['N_komsu_p99']:.1f}   salinim = "
              f"{oz['salinim_p99_p01']:.3f}x", flush=True)
        print(f"    zamanda ortanca  = {oz['ortanca_zaman_min']:.1f} .. "
              f"{oz['ortanca_zaman_max']:.1f}   salinim = "
              f"{oz['salinim_zamanda']:.3f}x", flush=True)
        return oz

    print(f"\n{'=' * 78}\nOZET", flush=True)
    oz1 = _ozetle("asama-1", ornek1)
    oz2 = _ozetle("asama-2", ornek2)
    oz = _ozetle("TUMU", ornek1 + ornek2)

    y = judge_dart_salinimi(oz)
    print(f"\n{'=' * 78}\nYARGI", flush=True)
    print(f"  tarama kapsami   = {y['tarama_kapsami'][0]:.1f} .. "
          f"{y['tarama_kapsami'][1]:.1f}", flush=True)
    print(f"  DART araligi     = {y['dart_araligi'][0]:.1f} .. "
          f"{y['dart_araligi'][1]:.1f}", flush=True)
    print(f"  kup salinimi     = {y['kup_salinim_orani']:.3f}x", flush=True)
    print(f"  DART salinimi    = {y['dart_salinim_orani']:.3f}x", flush=True)
    print(f"\n  KARAR: {y['karar']}", flush=True)
    print(f"  {y['neden']}", flush=True)
    print(f"\n  NOT: {y['yorum']}", flush=True)

    def _kirp(orn):
        return [{k: v for k, v in o.items() if k != "n_komsu"} for o in orn]

    Path(a.out).write_text(json.dumps({
        "kip": "dart_komsu_salinimi", "adr": "ADR-0042",
        "yukumluluk": "ADR-0042 §4: olcum DART geometrisinde tekrarlanacak",
        "sahne": {k: (v if not isinstance(v, np.ndarray) else v.tolist())
                  for k, v in SAHNE.items()},
        "lam1": a.lam1, "lam2": a.lam2, "t1": a.t1, "t_end": a.t_end,
        "ic_frac": a.ic_frac, "her": a.her, "R": R,
        "N_asama1": int(a1.n), "N_asama2": int(sahne.n),
        "kup_salinimi": list(KUP_SALINIMI),
        "kup_tarama_kapsami": list(KUP_TARAMA_KAPSAMI),
        "ozet_asama1": oz1, "ozet_asama2": oz2, "ozet_tumu": oz,
        "yargi": y,
        "capraz_sayim_t0": sayim0, "capraz_sayim_son": sayim_son,
        "ornekler_asama1": _kirp(ornek1), "ornekler_asama2": _kirp(ornek2),
        "duvar_s": time.perf_counter() - t0,
    }, indent=2, default=float), encoding="utf-8")
    print(f"\nyazildi: {a.out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
