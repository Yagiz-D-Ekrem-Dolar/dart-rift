"""TANI — `f` sahneye NEREYE giriyor: kazı bölgesine mi, çekirdeğe mi?

## Niçin

`LITERATUR-DART-SIMULASYONLARI.md` §11.5 ve KAYIT-097 şunu yazıyor: blok
hacim kesri `f`, öğrenilen yöndeki payını `q90`'da bile `0,045` alıyor —
yani `β` `f`'i **görmüyor**. Aynı belge çözümü *"yerleşim gürültüsü"*
olarak yazdı ve şu cümleyi kullandı: *"sahnede yalnız ~7 blok var ve her
`θ` noktasında tek sahne tohumu var."*

**Ama bu ölçülmedi.** Bir hipotezdi ve raporun en zayıf iddiası oldu.
Üstelik iki **birbirini dışlayan** açıklama var ve ikisi çok farklı
sonuçlar doğuruyor:

- **H1 (gürültü):** `f` kazı bölgesine ulaşıyor, ama tek tohumla etkisi
  yerleşim saçılmasından ayrılamıyor. Çare: `θ` başına çok tohum.
  Bu, §11.5'in yazdığı şey — doğruysa iddiamız ayakta kalır.
- **H2 (yapılandırma):** `f` kazı bölgesine **hiç** ulaşmıyor; eklenen
  blok hacmi cismin çekirdeğine gidiyor. O zaman `β`'nın `f`'i görmemesi
  fizik değil, **bizim sahne kurulumumuzun kusuru**dur ve `f` ekseni
  hakkında söylediğimiz her şey geçersizdir.

H2 boş bir kuşku değil. Üretim `blok_uretici="v1"` kullanıyor ve v1'in
kabul şartı şudur (`rubble_generator.place_boulders` belgesi):

    "Blok TAMAMEN mesh icinde olmali."

Üretim cismi `88,5 x 87,0 x 58,0 m` yarı eksenli elipsoit ve blok yarıçapı
`--blok-rmax 56.0`. En kısa yarı eksen `58 m`, en büyük blok yarıçapı
`56 m`: böyle bir blok ancak merkezin `~2 m` yakınında durabilir. Yani
**büyük bloklar yapı gereği çekirdeğe sürülüyor** ve çarpma noktasının
altına asla gelemiyor. Çarpma noktası ise sabittir (`aim = (0,0,1)`,
`--carpma-acisi 17.0`): üretimin 96 noktasının hepsinde aynı yerdedir.

Protokol L (2026-09-13, `scene.py`'nin kendi yorumunda kayıtlı) şunu
ölçtü: *"bloga carpma beta-1 ~ 0,03, matrise ~ 0,5; kusursuz ayrim."*
Yani `β` için belirleyici olan **çarpma noktasının altındaki malzeme**.
Eğer `f` oraya ulaşmıyorsa `β`'nın `f`'e duyarsızlığı kaçınılmazdır.

## Ne ölçülür — SIFIR GPU

Üretimin sahne yapılandırması birebir kurulur (aşağıdaki sabitler
`truba/is_HAVUZ.slurm` ve `faz44_dart_yakinsama.SAHNE`'den alınmıştır) ve
YALNIZ blok alanı üretilir; çözücü koşmaz, parçacık doldurulmaz.

`K` adet `f` değeri x `M` adet sahne tohumu için, kapalı formla (Monte
Carlo gürültüsü YOK) şunlar hesaplanır:

1. `f_gerceklesen` — yerleşen blok hacmi / cisim hacmi. (`f` isteniyor,
   v1 doyabilir; doyuyorsa bunu görmek gerekir.)
2. `n_blok`, `yaricap_maks` — kaç blok, en büyüğü ne.
3. `carpmada_blok` — çarpma noktası bir bloğun İÇİNDE mi? (ikili olay;
   Protokol L'nin iki dalını seçen şey tam budur.)
4. `bolge_payi(R)` — çarpma noktası merkezli `R` yarıçaplı kazı
   bölgesindeki blok hacmi / o bölgenin cisim içinde kalan hacmi.
   `R` kilitli yapılandırma sayılarına bağlanmıştır: `14 m` (= `r_min`),
   `28 m` (= `2 r_min`), `56 m` (= `r_max`). Küre-küre kesişim hacmi
   KAPALI FORMDUR; pay tam hesaplanır.
5. `kabuk_payi` — normalleştirilmiş yarıçap `s = sqrt((x/a)^2 + (y/b)^2 +
   (z/c)^2)` için `s >= S_KABUK` kabuğunda kalan blok hacminin payı.
   Kabuğun kendi hacim payı `1 - S_KABUK^3`'tür; ikisinin oranı
   `kabuk_zenginlesmesi` olarak raporlanır (1,0 = yansız dağılım).
6. `s_ortalama` — blok hacmiyle ağırlıklı ortalama `s`. Çekirdeğe sürülme
   doğrudan burada görünür (yansız dağılımda `s_ortalama ~ 0,75`).

Sonra her büyüklük için **tek tohumluk ayırt oranı**:

    sinyal = | ortalama(f = F_MAKS) - ortalama(f = F_MIN) |
    gurultu = f'ler uzerinde tohumlar arasi standart sapmanin ORTANCASI
    D = sinyal / gurultu

`D` tam olarak üretimin durumudur: her `θ` noktasında tek tohum var.
`M` tohumla ortalama alınsa gürültü `sqrt(M)` kat düşeceği için gereken
tohum sayısı `M* = ceil((D_HEDEF / D)^2)` olarak raporlanır.

## KAPILAR — koşudan ÖNCE kilitli

- **G1 (akıl sağlığı).** `f` ile `f_gerceklesen` arasında Spearman
  `rho >= 0,90` olmalı. Olmazsa v1 doyuyor demektir; o başka bir
  kusurdur ve G2/G3 yorumlanmaz.
- **G2 (`f` kazı bölgesine ULAŞIYOR mu).** `bolge_payi(28 m)` için
  Spearman `rho >= 0,70`:
  * `rho >= 0,70` **ve** `D >= 1,0` -> `f` kazı bölgesine ulaşıyor ve
    tek tohumda ayırt edilebilir. O zaman körlüğün sebebi sahne DEĞİL;
    kusur çözücüde ya da gözlenebilirde aranmalıdır.
  * `rho >= 0,70` **ve** `D < 1,0` -> **H1 DOĞRULANDI**: ulaşıyor ama
    tek tohumda yerleşim gürültüsünün altında. §11.5 ayakta kalır ve
    artık bir sayısı olur.
  * `rho < 0,70` -> **H2 DOĞRULANDI**: `f` kazı bölgesine ulaşmıyor.
    Bu bir YAPILANDIRMA kusurudur; `f` ekseni için söylediğimiz
    *"ölçülemiyor"* ifadesi doğru kalır ama SEBEBİ değişir ve yeni bir
    kusur kaydı açılır.
- **G3 (çekirdeğe sürülme).** `kabuk_zenginlesmesi` ortancası `< 0,50`
  ise *"bloklar kabukta beklenenin yarısından az; yapı gereği çekirdeğe
  sürülmüşler"* yazılır.
- **G4 (çare).** `bolge_payi(28 m)` için `D_HEDEF = 3,0`'a ulaşmak için
  gereken tohum sayısı `M*` raporlanır. Bu, §8'in *"tohum sayısı
  artırılmalı"* maddesinin sayısal karşılığıdır.

## NOT 1 — duman sınavından sonra EKLENEN yan yana alan

Kapılar yukarıda koşudan önce kilitlendi. `K = 3, M = 3`'lük duman
sınavı, kapılarla ilgisi olmayan ama kaydedilmesi gereken bir şey
gösterdi: **istenen `f` ile gerçekleşen kesir aynı değil.**

    f = 0,05 istendi -> 0,1119 gerçekleşti  (2,2 kat AŞIM)
    f = 0,50 istendi -> 0,3740 gerçekleşti  (DOYMA)

Sebebi v1'in döngü şartıdır (`while v_acc < v_target`): hedef aşılana
kadar blok eklenir, ve `r in [14, 56] m` aralığında **tek bir blok**
cismin hacminin `%0,6` ile `%39`'u arasında yer kaplar. Yani istenen
kesir, blok tanesinin kendi büyüklüğünden küçük olduğunda temsil
edilemez.

Bu yüzden `f_bagil_sapma = (f_gerceklesen - f_istenen) / f_istenen`
büyüklüğü **yan yana alan** olarak eklendi (kural 6). HİÇBİR kapı,
eşik ya da yargı kuralı değiştirilmedi; `G1` hâlâ Spearman `rho`'ya
bakar ve kalibrasyona bakmaz — çünkü o eşik sonucu görmeden yazıldı.
Kalibrasyon sapması raporlanır, kapı olarak kullanılmaz.

## NOT 2 — bu ölçüm A74'ün YERİNE geçmez, onu ÜRETİME taşır

Yazıldıktan sonra fark edildi ve kaynak dürüstlüğü için yazılmalı:
`FAZ4-SIKINTI-RAPORU.md` A74 (2026-09-11, **uzman bulgusu, açık**) bu
ailenin iki parçasını zaten ölçmüştü:

- **(a)** v1 doyuyor: aynı tohumla `f = 0,4304` ve `0,55` **aynı**
  geometriyi veriyor (SHA-256 eşit). G1/G2'nin 48 noktasında nominal
  `0,051 – 0,484` aralığı sahnede **`0,102 – 0,371`**'e sıkışmış;
  `11/48` nokta doymuş.
- **(b)** v1 yüzeyde blok bırakmıyor (14 yönlü "tamamen içinde"
  sınaması; 200 000 yüzey yönünde blok payı `%0,5`).

Ve A74'ün kendi son satırı: *"Varsayılanlar (`v1`, `kaba`) bit-aynı;
kampanyalarda henüz kullanılmadı."* Düzeltme (`place_boulders_v2`)
yazıldı ama **hiçbir kampanyada açılmadı**; üretim havuzu
(`truba/is_HAVUZ.slurm`) `--blok-uretici` vermiyor, yani **v1**.

Bu betiğin eklediği üç şey:

1. A74 `r in [14, 42]`'yi ve **48 noktalı** G1/G2 tasarımını ölçtü.
   Üretim havuzu `r in [14, 56]` ve `88,5 x 87,0 x 58,0 m` elipsoitle
   **96 nokta** koştu; o yapılandırma bu açıdan **hiç ölçülmedi**.
2. A74 yüzey blok payını **küresel** olarak ölçtü (200 000 yüzey
   yönü). Burada ölçülen, `β`'yı belirleyen yer: **sabit çarpma
   noktasının kazı bölgesi** (`R = 14 / 28 / 56 m`).
3. A74 bir **sahne** kusuru olarak kaydedildi; `f` körlüğünün
   **çıkarım** sonucuna (KAYIT-097, §11.5) bağlanmadı. §11.5 sebebi
   *"yerleşim gürültüsü + tek tohum"* diye yazdı. A74 doğruysa sebep
   bundan **daha ağırdır**: düğmenin üst kısmı ölü ve bloklar yüzeyden
   dışlanmış. Bu betiğin yargısı hangisinin geçerli olduğunu söyler.

Yani: A74 açık kusur olarak **yerinde durur**, hiçbir satırı
değiştirilmez; bu ölçüm onun üretim havuzundaki sonucudur.

## Bu bir KEŞİFTİR

Hiçbir kilitli sonuca, mühüre ya da protokole dokunulmaz. `β`
hesaplanmaz; Protokol L'nin iki dal değeri YALNIZ yorumda anılır,
aritmetiğe GİRMEZ. Çıktı `json`'dur; kayıt ayrıca yazılır.

Kullanım (sıfır GPU, tek çekirdek):

    python scripts/tani_f_sahne_tohum.py --cikti f_sahne.json
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from dartrift.setup.impactor import impact_geometry  # noqa: E402
from dartrift.setup.rubble_generator import place_boulders  # noqa: E402
from dartrift.setup.scene import _build_mesh  # noqa: E402
from dartrift.setup.shape_mesh import inside_points  # noqa: E402

# ---------------------------------------------------------------------------
# URETIM YAPILANDIRMASI -- truba/is_HAVUZ.slurm ve SAHNE'den BIREBIR.
# Bu sabitler degistirilmez; degisirse olculen sey uretim DEGILDIR.
# ---------------------------------------------------------------------------
YARI_EKSENLER = (88.5, 87.0, 58.0)   # --hedef-yari-eksenler
SUBDIV = 4                            # build_scene varsayilani
R_MIN, R_MAX = 14.0, 56.0             # --blok-rmin / --blok-rmax
Q_USTEL = 3.0                         # SAHNE["q"]
CARPMA_ACISI = 17.0                   # --carpma-acisi
NISAN = (0.0, 0.0, 1.0)               # build_scene varsayilani `aim`
URETIM_TOHUMU = 20260906              # --sahne-tohum (96 noktanin HEPSI)

# Tasarim uzayi DART_UZAYI_S4'un `f_boulder` sinirlari.
F_MIN, F_MAKS = 0.05, 0.50

# Kazi bolgesi yaricaplari -- kilitli yapilandirma sayilarina bagli.
BOLGE_R = (14.0, 28.0, 56.0)
#: G2 bu yaricapta karar verir.
G2_R = 28.0

# Kabuk siniri: s >= S_KABUK. Kalinligi en kisa eksende ~14,5 m (~r_min).
S_KABUK = 0.75

# ---------------------------------------------------------------------------
# KILITLI KAPI ESIKLERI
# ---------------------------------------------------------------------------
G1_RHO = 0.90
G2_RHO = 0.70
G2_D = 1.0
G3_ZENGINLESME = 0.50
D_HEDEF = 3.0


def kure_kesisim_hacmi(r1: float, r2: float, d: float) -> float:
    """Iki kurenin kesisim hacmi -- KAPALI FORM (Monte Carlo yok)."""
    if d >= r1 + r2:
        return 0.0
    if d <= abs(r1 - r2):
        return 4.0 / 3.0 * math.pi * min(r1, r2) ** 3
    pay = (r1 + r2 - d) ** 2 * (
        d * d + 2.0 * d * (r1 + r2) - 3.0 * (r1 - r2) ** 2)
    return math.pi * pay / (12.0 * d)


def bolge_hacmi_cisimde(mesh, nokta, r, tohum=12345, n=400_000) -> float:
    """`nokta` merkezli `r` yarıçaplı kürenin CİSİM İÇİNDE kalan hacmi.

    `f` ve tohumdan BAGIMSIZ: bir kez hesaplanir, boleni sabitler. Monte
    Carlo yalniz BURADA kullanilir; pay kapali formdur.
    """
    rng = np.random.default_rng(tohum)
    u = rng.normal(size=(n, 3))
    u /= np.linalg.norm(u, axis=1)[:, None]
    rad = r * rng.random(n) ** (1.0 / 3.0)
    pts = np.asarray(nokta)[None, :] + u * rad[:, None]
    ic = inside_points(mesh, pts)
    kure = 4.0 / 3.0 * math.pi * r ** 3
    return float(kure * ic.mean())


def _s_norm(c: np.ndarray) -> np.ndarray:
    a, b, cc = YARI_EKSENLER
    c = np.atleast_2d(c)
    return np.sqrt((c[:, 0] / a) ** 2 + (c[:, 1] / b) ** 2 + (c[:, 2] / cc) ** 2)


def olc(mesh, geom, f: float, tohum: int, v_cisim: float,
        bolge_boleni: dict) -> dict:
    """Tek `(f, tohum)` sahnesinin blok alanini olc."""
    bf = place_boulders(mesh, float(f), Q_USTEL, R_MIN, R_MAX, int(tohum))
    c, r = np.atleast_2d(bf.centers), np.atleast_1d(bf.radii)
    n_blok = int(len(r))
    if n_blok == 0:
        satir = {"f_istenen": float(f), "tohum": int(tohum), "n_blok": 0,
                 "f_gerceklesen": 0.0, "f_bagil_sapma": -1.0,
                 "yaricap_maks": 0.0, "en_yakin_blok_uzakligi_m": float("nan"),
                 "carpmada_blok": 0, "kabuk_zenginlesmesi": float("nan"),
                 "s_ortalama": float("nan")}
        for rr in BOLGE_R:
            satir[f"bolge_payi_{rr:g}"] = 0.0
        return satir

    hac = 4.0 / 3.0 * math.pi * r ** 3
    p = np.asarray(geom.point, dtype=np.float64)
    d_carpma = np.linalg.norm(c - p[None, :], axis=1)

    satir = {
        "f_istenen": float(f),
        "tohum": int(tohum),
        "n_blok": n_blok,
        "f_gerceklesen": float(hac.sum() / v_cisim),
        # YAN YANA ALAN (asagidaki NOT 1): istenen kesre gore bagil sapma.
        "f_bagil_sapma": float((hac.sum() / v_cisim - f) / f),
        "yaricap_maks": float(r.max()),
        # Protokol L'nin iki dalini SECEN ikili olay.
        "carpmada_blok": int(bool(np.any(d_carpma <= r))),
        "en_yakin_blok_uzakligi_m": float(np.min(d_carpma - r)),
    }

    for rr in BOLGE_R:
        kes = sum(kure_kesisim_hacmi(float(ri), float(rr), float(di))
                  for ri, di in zip(r, d_carpma, strict=True))
        satir[f"bolge_payi_{rr:g}"] = float(kes / bolge_boleni[rr])

    s = _s_norm(c)
    kabukta = s >= S_KABUK
    kabuk_hacim_payi = 1.0 - S_KABUK ** 3
    blok_kabuk_payi = float(hac[kabukta].sum() / hac.sum())
    satir["kabuk_zenginlesmesi"] = blok_kabuk_payi / kabuk_hacim_payi
    satir["s_ortalama"] = float((hac * s).sum() / hac.sum())
    return satir


def _spearman(x, y) -> float:
    x, y = np.asarray(x, dtype=np.float64), np.asarray(y, dtype=np.float64)
    if x.size < 3:
        return float("nan")
    rx = np.argsort(np.argsort(x)).astype(np.float64)
    ry = np.argsort(np.argsort(y)).astype(np.float64)
    rx -= rx.mean()
    ry -= ry.mean()
    den = math.sqrt(float((rx ** 2).sum() * (ry ** 2).sum()))
    return float((rx * ry).sum() / den) if den > 0.0 else float("nan")


def _ayirt(f_degerleri, ortalamalar, sapmalar) -> dict:
    """Tek tohumluk ayirt orani `D` ve gereken tohum sayisi `M*`."""
    sinyal = abs(float(ortalamalar[-1]) - float(ortalamalar[0]))
    sap = np.asarray(sapmalar, dtype=np.float64)
    gurultu = float(np.median(sap[np.isfinite(sap)])) if sap.size else float("nan")
    if not np.isfinite(gurultu) or gurultu <= 0.0:
        return {"sinyal": sinyal, "gurultu": gurultu, "D": float("inf"),
                "M_yildiz": 1}
    d = sinyal / gurultu
    if d <= 0.0:
        # Sinyal TAM SIFIR: hicbir tohum sayisi ayirt etmez.
        return {"sinyal": sinyal, "gurultu": gurultu, "D": 0.0,
                "M_yildiz": None}
    m = 1 if d >= D_HEDEF else int(math.ceil((D_HEDEF / d) ** 2))
    return {"sinyal": sinyal, "gurultu": gurultu, "D": d, "M_yildiz": m}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--cikti", required=True)
    p.add_argument("--n-f", type=int, default=8, help="K: kac `f` degeri")
    p.add_argument("--n-tohum", type=int, default=16, help="M: kac tohum")
    a = p.parse_args()
    if a.n_f < 3 or a.n_tohum < 3:
        raise SystemExit("K >= 3 ve M >= 3 olmali (Spearman ve sapma icin)")

    mesh = _build_mesh("ellipsoid", radius=None,
                       semi_axes=list(YARI_EKSENLER), subdiv=SUBDIV)
    v_cisim = float(mesh.volume)
    geom = impact_geometry(mesh, np.asarray(NISAN, dtype=np.float64),
                           angle_deg=CARPMA_ACISI, azimuth_deg=0.0)

    print("=" * 72)
    print("TANI -- `f` sahneye NEREYE giriyor?   (KESIF, sifir GPU)")
    print("=" * 72)
    print(f"cisim      : elipsoit {YARI_EKSENLER} m,  V = {v_cisim:.4e} m3")
    print(f"carpma nok.: {np.round(geom.point, 3).tolist()}  (SABIT, 96 noktada ayni)")
    print(f"blok       : r in [{R_MIN}, {R_MAX}] m, q = {Q_USTEL}, uretici v1")
    print("             v1 sarti: blok TAMAMEN mesh icinde")
    print(f"kapilar    : G1 rho>={G1_RHO}  G2 rho>={G2_RHO} & D>={G2_D}  "
          f"G3 zeng.<{G3_ZENGINLESME}")
    print(flush=True)

    # Boleni bir kez hesapla -- `f` ve tohumdan bagimsiz.
    bolge_boleni = {}
    for rr in BOLGE_R:
        bolge_boleni[rr] = bolge_hacmi_cisimde(mesh, geom.point, rr)
        kure = 4.0 / 3.0 * math.pi * rr ** 3
        print(f"  bolge R = {rr:4.0f} m : cisim icinde kalan hacim "
              f"{bolge_boleni[rr]:.4e} m3  (kurenin %{100*bolge_boleni[rr]/kure:.1f})",
              flush=True)
    print(flush=True)

    f_degerleri = np.linspace(F_MIN, F_MAKS, int(a.n_f))
    tohumlar = [URETIM_TOHUMU + i for i in range(int(a.n_tohum))]

    satirlar = []
    for f in f_degerleri:
        for t in tohumlar:
            satirlar.append(olc(mesh, geom, float(f), int(t), v_cisim,
                                bolge_boleni))
        son = satirlar[-len(tohumlar):]
        print(f"  f = {f:.4f} : n_blok ortanca "
              f"{np.median([s['n_blok'] for s in son]):5.1f}   "
              f"f_gerc ortalama {np.mean([s['f_gerceklesen'] for s in son]):.4f}   "
              f"carpmada blok {sum(s['carpmada_blok'] for s in son)}/{len(son)}",
              flush=True)

    # ------------------------------------------------------------------
    # TOPLAMA
    # ------------------------------------------------------------------
    buyuklukler = (["f_gerceklesen", "f_bagil_sapma", "n_blok",
                    "yaricap_maks", "carpmada_blok",
                    "kabuk_zenginlesmesi", "s_ortalama"]
                   + [f"bolge_payi_{rr:g}" for rr in BOLGE_R])
    ozet = {}
    for ad in buyuklukler:
        ort, sap = [], []
        for f in f_degerleri:
            v = np.array([s[ad] for s in satirlar
                          if abs(s["f_istenen"] - f) < 1e-12], dtype=np.float64)
            v = v[np.isfinite(v)]
            ort.append(float(v.mean()) if v.size else float("nan"))
            sap.append(float(v.std(ddof=1)) if v.size > 1 else float("nan"))
        ozet[ad] = {
            "f": [float(x) for x in f_degerleri],
            "ortalama": ort, "tohum_sapmasi": sap,
            "spearman_rho": _spearman(f_degerleri, ort),
            **_ayirt(f_degerleri, ort, sap),
        }

    g2 = ozet[f"bolge_payi_{G2_R:g}"]
    g1_gecti = bool(np.isfinite(ozet["f_gerceklesen"]["spearman_rho"])
                    and ozet["f_gerceklesen"]["spearman_rho"] >= G1_RHO)
    zeng = np.array([s["kabuk_zenginlesmesi"] for s in satirlar],
                    dtype=np.float64)
    zeng_ortanca = float(np.median(zeng[np.isfinite(zeng)]))

    if not g1_gecti:
        yargi = ("G1 DUSTU: `f` ile gerceklesen kesir izlesmiyor -- v1 "
                 "DOYUYOR. G2/G3 yorumlanmaz; bu BASKA bir kusurdur.")
        hipotez = "BELIRSIZ"
    elif g2["spearman_rho"] < G2_RHO:
        yargi = ("H2 DOGRULANDI: `f` KAZI BOLGESINE ULASMIYOR. Blok hacmi "
                 "cismin cekirdegine gidiyor; carpma noktasinin altindaki "
                 "malzeme `f` ile degismiyor. `beta`nin `f`'i gormemesi "
                 "FIZIK DEGIL, SAHNE YAPILANDIRMASIDIR.")
        hipotez = "H2"
    elif g2["D"] < G2_D:
        yargi = ("H1 DOGRULANDI: `f` kazi bolgesine ULASIYOR ama tek "
                 "tohumda yerlesim gurultusunun ALTINDA. §11.5'in "
                 "aciklamasi ayakta; artik bir sayisi var.")
        hipotez = "H1"
    else:
        yargi = ("IKISI DE DEGIL: `f` kazi bolgesine ulasiyor VE tek "
                 "tohumda ayirt edilebilir. O zaman korlugun sebebi sahne "
                 "DEGIL -- cozucude ya da gozlenebilirde aranmali.")
        hipotez = "NE_H1_NE_H2"

    kayit = {
        "yapilandirma": {
            "yari_eksenler_m": list(YARI_EKSENLER), "subdiv": SUBDIV,
            "r_min_m": R_MIN, "r_max_m": R_MAX, "q": Q_USTEL,
            "carpma_acisi_deg": CARPMA_ACISI, "nisan": list(NISAN),
            "uretim_tohumu": URETIM_TOHUMU, "blok_uretici": "v1",
            "cisim_hacmi_m3": v_cisim,
            "carpma_noktasi_m": [float(x) for x in geom.point],
            "kaynak": "truba/is_HAVUZ.slurm + faz44_dart_yakinsama.SAHNE",
        },
        "kapilar": {
            "G1_rho": G1_RHO, "G2_rho": G2_RHO, "G2_D": G2_D,
            "G2_R_m": G2_R, "G3_zenginlesme": G3_ZENGINLESME,
            "D_hedef": D_HEDEF, "S_kabuk": S_KABUK,
            "NOT": "Kapilar kosudan ONCE bu dosyanin belgesinde kilitlendi.",
        },
        "tasarim": {"K": int(a.n_f), "M": int(a.n_tohum),
                    "f": [float(x) for x in f_degerleri],
                    "tohumlar": tohumlar},
        "bolge_boleni_m3": {f"{k:g}": v for k, v in bolge_boleni.items()},
        "ozet": ozet,
        "kabuk_zenginlesmesi_ortanca": zeng_ortanca,
        "kabuk_hacim_payi": 1.0 - S_KABUK ** 3,
        "G1_gecti": g1_gecti,
        "HIPOTEZ": hipotez,
        "YARGI": yargi,
        "NOT": ("KESIF. Hicbir kilitli sonuca/muhure dokunulmadi. `beta` "
                "HESAPLANMADI; Protokol L'nin iki dal degeri yalniz yorumda "
                "anildi, aritmetige GIRMEDI."),
        "satirlar": satirlar,
    }
    with open(a.cikti, "w", encoding="utf-8") as fh:
        json.dump(kayit, fh, indent=2, ensure_ascii=False)

    # ------------------------------------------------------------------
    print()
    print("=" * 72)
    print("SONUC")
    print("=" * 72)
    basliklar = ("buyukluk", "rho", "sinyal", "tohum gur.", "D", "M*")
    print(f"{basliklar[0]:<22}{basliklar[1]:>7}{basliklar[2]:>12}"
          f"{basliklar[3]:>12}{basliklar[4]:>8}{basliklar[5]:>8}")
    print("-" * 72)
    for ad in buyuklukler:
        o = ozet[ad]
        mm = "inf" if o["M_yildiz"] is None else str(o["M_yildiz"])
        print(f"{ad:<22}{o['spearman_rho']:>7.3f}{o['sinyal']:>12.4g}"
              f"{o['gurultu']:>12.4g}{o['D']:>8.3f}{mm:>8}")
    print("-" * 72)
    print(f"kabuk (s >= {S_KABUK}) hacim payi      : "
          f"{1.0 - S_KABUK**3:.3f}")
    print(f"blok kabuk zenginlesmesi ortanca  : {zeng_ortanca:.3f}"
          f"   (1,0 = yansiz;  kapi G3 < {G3_ZENGINLESME})")
    _g3 = ("DUSTU -- bloklar CEKIRDEGE surulmus"
           if zeng_ortanca < G3_ZENGINLESME else "gecti")
    print(f"G3: {_g3}")
    print()
    _m = ("HICBIRI (sinyal tam sifir)" if g2["M_yildiz"] is None
          else f"{g2['M_yildiz']} tohum")
    print(f"G4: `bolge_payi_{G2_R:g}` icin D_hedef = {D_HEDEF} istiyorsa "
          f"`theta` basina M* = {_m} gerekir.")
    print()
    print(f"HIPOTEZ: {hipotez}")
    print(f"YARGI  : {yargi}")
    print(f"NOT    : {kayit['NOT']}")
    print(f"\nyazildi: {a.cikti}")


if __name__ == "__main__":
    main()
