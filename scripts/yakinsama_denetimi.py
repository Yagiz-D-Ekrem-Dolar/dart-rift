"""**Yakınsama denetimi** — motorun ayrıklaştırma düğmelerini *hepsini*
tek tek tarayan bir teknik.

## Neden bu teknik

`G4-B1` *"ardışık iki çözünürlük arası `β` farkı"* diyor ve geçti
(`Δβ = 0,000843`). Ama taranan düğme `λ₂` (hedef ızgarası) oldu.
`β`'yı **üreten** düğme `λ₁` (mermi inceltmesi) hiç taranmamıştı ve
tarandığında `Δβ = 0,226150` (`%16,0`) çıktı — eşiğin üstünde.

> Yakınsama **bir düğmede** ölçülüp *"model yakınsadı"* diye
> okunmuştu. Bu bir kaza değil, **yöntem eksiği**: hangi düğmelerin
> sınandığını hiçbir yer saymıyordu.

Bu betik o eksiği kapatıyor. İşi üç şey:

1. **Sayım.** Motorun bütün ayrıklaştırma düğmelerini bir yerde
   listeler; bir düğmenin taranmamış olması **görünür** olur
   (`denetlenmedi`), sessizce geçmez.
2. **Tarama.** Her düğme için, **yalnızca o düğme** değişen kollar
   üretir (tek değişkenli), koşturur ve gözlenebilirlerdeki farkı
   ölçer.
3. **Mertebe.** Üç noktalı düğmelerde gözlenen yakınsama mertebesini
   `p = log(|Δ₁| / |Δ₂|) / log(oran)` ile verir. Mertebe, farkın
   büyüklüğünden **daha bilgilendiricidir**: küçülüyor mu, ne hızla?

## Ne yapmaz

Bu betik **sorunu çözmez**, bulur ve nicelendirir. Düğmenin
yakınsamadığı ölçülünce ne yapılacağı (inceltmek mi, model-formu
değiştirmek mi, ölçütü düşürmek mi) bir **ADR** kararıdır.

Ayrıca bir düğmenin *"geçti"* çıkması modelin **doğru** olduğunu
göstermez; yalnızca o eksende çözünürlüğe **duyarsız** olduğunu
gösterir. Doğruluk ayrı bir sorudur (analitik çözüm, dış veri).

## Maliyet ekseni — "daha çok örnek" buradan çıkar

Her kol duvar süresini ve parçacık sayısını kaydeder. Bir düğme
zaten yakınsamışsa, **daha kaba** ayarı da aynı sonucu verir; o zaman
ensemble bütçesi aynı kalırken **nokta sayısı** artar. `yeterli_ayar`
tam bunu hesaplar: her eksende toleransı sağlayan **en ucuz** ayar.
"""
from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass, field
from pathlib import Path

#: `G4-OLCUTLERI.md` B1: ardışık çözünürlükte `β` farkı `%10` bağıl.
#: Diğer gözlenebilirler için kapıda eşik **yok**; aynı değer bir
#: **öneri** olarak kullanılıyor ve çıktıda öyle işaretleniyor.
ESIK_BAGIL = {"beta": 0.10, "krater_derinlik": 0.10, "krater_cap": 0.10}
ESIK_KAPIDA_TANIMLI = {"beta"}


@dataclass(frozen=True)
class Dugme:
    """Bir ayrıklaştırma ekseni ve taranacak değerleri."""

    ad: str
    bayrak: str                    # faz48_iki_asama.py CLI bayragi
    taban: float
    basamaklar: tuple[float, ...]  # tabandan sonraki INCELTMELER
    aciklama: str
    #: `deger_orani(kaba, ince)` -> inceltme orani (mertebe hesabi icin).
    #: Cogu dugmede `ince / kaba`, ama `cfl` ve `spacing`de TERS.
    ters: bool = False

    def oran(self, kaba: float, ince: float) -> float:
        return kaba / ince if self.ters else ince / kaba


#: Motorun ayrıklaştırma düğmeleri. **Bu liste denetimin kapsamıdır**:
#: burada olmayan bir düğme denetlenmemiş demektir ve öyle raporlanır.
DUGMELER: tuple[Dugme, ...] = (
    Dugme("lam1", "--lam1", 19.0, (38.0, 55.0),
          "mermi inceltmesi -- beta'yi URETEN eksen"),
    Dugme("lam2", "--lam2", 2.0, (4.0,),
          "hedef izgarasi / krater bolgesi"),
    Dugme("spacing", "--spacing", 7.0, (5.0,),
          "kaba izgara araligi", ters=True),
    Dugme("r_ince1", "--r-ince1", 3.0, (6.0,),
          "asama-1 ince bolge yaricapi"),
    Dugme("r_ince2", "--r-ince2", 25.0, (40.0,),
          "asama-2 ince bolge yaricapi"),
    Dugme("cfl", "--cfl", 0.25, (0.125,),
          "zaman adimi olcegi", ters=True),
    Dugme("n_mermi", "--n-mermi", 800.0, (1600.0,),
          "mermi parcacik sayisi"),
    Dugme("t1", "--t1", 4.767148659522709e-3, (9.534297319045418e-3,),
          "asama-1'in bittigi an (aktarim noktasi)"),
)

#: Denetlenmesi gereken ama **bayrağı olmayan** düğmeler. Boş bırakmak
#: yerine yazılıyor: kapsamın nerede bittiği görünsün.
BAYRAKSIZ = {
    "subdiv": "ikosfer bolunme derinligi (build_scene subdiv=4)",
    "kernel": "cekirdek secimi (wendland_c2) -- ayriklastirma degil ama"
              " yakinsama mertebesini belirler",
}


@dataclass
class Kol:
    """Tek bir koşu: hangi düğme, hangi değer, hangi argümanlar."""

    dugme: str
    deger: float
    taban_mi: bool
    argumanlar: list[str] = field(default_factory=list)

    @property
    def ad(self) -> str:
        return f"{self.dugme}_{self.deger:g}".replace(".", "p")


def plan_uret(dugmeler=DUGMELER, *, t_end: float = 0.2) -> list[Kol]:
    """Kolları üret: **bir taban** + her düğme için inceltmeler.

    Taban **tek kez** koşulur ve bütün düğmeler onunla karşılaştırılır;
    aksi halde `n` düğme için `n` özdeş taban koşusu yapılırdı.
    """
    ortak = ["--t-end", f"{t_end:g}"]
    kollar = [Kol("taban", 0.0, True, list(ortak))]
    for d in dugmeler:
        for v in d.basamaklar:
            arg = f"{int(v)}" if float(v).is_integer() else f"{v:.10g}"
            kollar.append(Kol(d.ad, v, False, [*ortak, d.bayrak, arg]))
    return kollar


def mertebe(d1: float, d2: float, oran: float) -> float:
    """Gözlenen yakınsama mertebesi `p = log(|Δ₁|/|Δ₂|) / log(oran)`.

    `Δ₁` kaba çiftin, `Δ₂` ince çiftin farkı. `Δ₂ = 0` ise fark
    makine sıfırına inmiş demektir; `inf` döner ve öyle raporlanır.
    """
    a1, a2 = abs(float(d1)), abs(float(d2))
    if oran <= 1.0:
        raise ValueError(f"oran > 1 olmali, {oran} geldi")
    if a2 == 0.0:
        return math.inf if a1 > 0.0 else float("nan")
    if a1 == 0.0:
        return 0.0
    return math.log(a1 / a2) / math.log(oran)


def bagil_fark(taban: float, ince: float) -> float:
    """`|ince - taban| / |taban|`; taban sıfırsa mutlak fark."""
    t = abs(float(taban))
    d = abs(float(ince) - float(taban))
    return d / t if t > 0.0 else d


def yargi(bagil: float, esik: float) -> str:
    if bagil != bagil:                      # nan
        return "olculemedi"
    return "gecti" if bagil < esik else "DUSTU"


def yeterli_ayar(olcumler: dict[str, float], dugme: Dugme,
                 tol: float) -> float:
    """Toleransı sağlayan **en kaba** (en ucuz) ayar.

    `olcumler`: `{deger: bagil_fark_tabandan}`. Taban her zaman `0`
    farkla dahildir. En kaba ayar, kendisinden **sonraki** inceltmenin
    getirdiği fark `tol`un altındaysa yeterlidir.

    Yakınsamamış bir eksende (**bütün** farklar `tol` üstünde) `nan`
    döner: orada "ucuz ayar" diye bir şey yoktur, ölçüm eksiktir.
    """
    sirali = [dugme.taban, *dugme.basamaklar]
    for kaba, ince in zip(sirali, sirali[1:], strict=False):
        f = olcumler.get(ince)
        if f is None:
            continue
        if f < tol:
            return kaba
    return float("nan")


def _oku(yol: Path) -> dict:
    d = json.loads(yol.read_text(encoding="utf-8"))
    return {
        "beta": d.get("beta"),
        "n_ejekta": d.get("n_ejekta"),
        "A1": d.get("A1"),
        "N": d.get("N_asama2") or d.get("N"),
        "duvar_s": d.get("duvar_s"),
        "t_sim": d.get("t_sim"),
    }


def topla(dizin: Path, dugmeler=DUGMELER) -> dict:
    """Kolların JSON'larını oku, matrisi ve yargıları üret."""
    kollar = plan_uret(dugmeler)
    veri: dict[str, dict] = {}
    eksik: list[str] = []
    for k in kollar:
        y = dizin / f"{k.ad}.json"
        if y.is_file():
            veri[k.ad] = _oku(y)
        else:
            eksik.append(k.ad)
    if "taban_0" not in veri:
        raise SystemExit("taban kolu yok -- karsilastirma yapilamaz")
    taban = veri["taban_0"]

    satirlar = []
    for d in dugmeler:
        olcumler: dict[float, float] = {}
        farklar: list[float] = []
        for v in d.basamaklar:
            ad = Kol(d.ad, v, False).ad
            if ad not in veri:
                continue
            b = bagil_fark(taban["beta"], veri[ad]["beta"])
            olcumler[v] = b
            farklar.append(float(veri[ad]["beta"]) - float(taban["beta"]))
        if not olcumler:
            satirlar.append({"dugme": d.ad, "durum": "denetlenmedi",
                             "aciklama": d.aciklama})
            continue
        en_ince = max(olcumler)
        p = float("nan")
        if len(farklar) >= 2:
            oran = d.oran(d.basamaklar[0], d.basamaklar[1])
            p = mertebe(farklar[0], farklar[1] - farklar[0], oran)
        satirlar.append({
            "dugme": d.ad, "durum": "denetlendi", "aciklama": d.aciklama,
            "bagil_fark": olcumler[en_ince],
            "yargi": yargi(olcumler[en_ince], ESIK_BAGIL["beta"]),
            "mertebe": p,
            "yeterli_ayar": yeterli_ayar(olcumler, d, ESIK_BAGIL["beta"]),
            "olcumler": {str(k): v for k, v in olcumler.items()},
        })
    return {"taban": taban, "satirlar": satirlar, "eksik_kollar": eksik,
            "bayraksiz_dugmeler": BAYRAKSIZ,
            "esik_bagil": ESIK_BAGIL["beta"],
            "esik_kapida_tanimli": sorted(ESIK_KAPIDA_TANIMLI)}


def bas(r: dict) -> None:
    t = r["taban"]
    print("=" * 74, flush=True)
    print("YAKINSAMA DENETIMI -- her ayriklastirma dugmesi TEK TEK",
          flush=True)
    print("=" * 74, flush=True)
    print(f"  taban: beta = {t['beta']!r}  N = {t['N']}  "
          f"duvar = {t['duvar_s']:.0f} s", flush=True)
    print(f"  esik: bagil {100 * r['esik_bagil']:.0f}%  "
          f"(kapida tanimli olan: {', '.join(r['esik_kapida_tanimli'])}; "
          f"digerleri ONERI)", flush=True)
    print(f"\n  {'dugme':<10} {'bagil fark':>11} {'yargi':>9} "
          f"{'mertebe':>9} {'yeterli':>9}", flush=True)
    print("  " + "-" * 52, flush=True)
    for s in r["satirlar"]:
        if s["durum"] == "denetlenmedi":
            print(f"  {s['dugme']:<10} {'--':>11} {'DENETLENMEDI':>9}",
                  flush=True)
            continue
        p = s["mertebe"]
        ps = "--" if p != p else ("inf" if p == math.inf else f"{p:.2f}")
        ya = s["yeterli_ayar"]
        yas = "--" if ya != ya else f"{ya:g}"
        print(f"  {s['dugme']:<10} {s['bagil_fark']:>11.3e} "
              f"{s['yargi']:>9} {ps:>9} {yas:>9}", flush=True)
    if r["eksik_kollar"]:
        print(f"\n  KOSULMAYAN kol: {len(r['eksik_kollar'])} "
              f"({', '.join(r['eksik_kollar'][:6])}"
              f"{' ...' if len(r['eksik_kollar']) > 6 else ''})", flush=True)
    print("\n  BAYRAGI OLMAYAN dugmeler (denetim kapsaminin disi):",
          flush=True)
    for ad, ac in r["bayraksiz_dugmeler"].items():
        print(f"    {ad:<10} {ac}", flush=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    alt = ap.add_subparsers(dest="kip", required=True)
    p1 = alt.add_parser("plan", help="kollari ve CLI argumanlarini yaz")
    p1.add_argument("--t-end", type=float, default=0.2)
    p1.add_argument("--cikti", type=Path, default=None)
    p2 = alt.add_parser("topla", help="kosmus kollari oku ve yargila")
    p2.add_argument("--dizin", type=Path, required=True)
    p2.add_argument("--cikti", type=Path, default=None)
    a = ap.parse_args()

    if a.kip == "plan":
        kollar = plan_uret(t_end=a.t_end)
        for k in kollar:
            print(f"{k.ad}\t{' '.join(k.argumanlar)}", flush=True)
        print(f"\n{len(kollar)} kol ({len(DUGMELER)} dugme + 1 taban)",
              flush=True)
        if a.cikti:
            a.cikti.write_text(json.dumps(
                [{"ad": k.ad, "dugme": k.dugme, "deger": k.deger,
                  "argumanlar": k.argumanlar} for k in kollar],
                ensure_ascii=False, indent=2), encoding="utf-8")
        return 0

    r = topla(a.dizin)
    bas(r)
    if a.cikti:
        a.cikti.write_text(json.dumps(r, ensure_ascii=False, indent=2,
                                      default=float), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
