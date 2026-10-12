"""Vekil ön çalışması — havuz DOLMADAN, kısmi veriyle.

## Bu bir YARGI DEĞİL

Havuz 96 noktanın hepsini üretmeden hiçbir kilitli eşik uygulanmaz.
Burada yapılan şey **keşif**: vekilin ne öğrenebildiğini erkenden görmek,
havuz dolduğunda sürprizle karşılaşmamak. Protokol P'nin yol seçimi
(kuadratik mi GP mi) dış örneklemde yapılır ve bu betik onu yapmaz.

Buna rağmen prosedür gerçeğin aynısı tutuldu:

* `θ`-gruplu **4 kat** çapraz doğrulama (`p_kalibrasyon_raporu.kat_ata`
  ile aynı kural: kat = grup kimliği % 4). Gerekçe A82: bırak-bir-θ dış
  örneklem hatasını ~1,4 kat KÜÇÜK gösteriyor, çünkü tek nokta çıkınca
  komşuları vekili aynı yere çekiyor. Gerçek Dimorphos'un `θ`'sı
  eğitimde hiç yok.
* Bachoc (2013) varyans kalibrasyonu, `gp_varyans_kalibre` ile.

## Kullanım

    python scripts/vekil_on_calisma.py <havuz.csv>

CSV sütunları: `idx,beta,krater,ejf` — `idx` KÜRESEL tasarım indisi
(0..95). Dikkat: havuz jsonl'lerindeki `i` alanı DİLİM İÇİ indistir
(0..3); küresel indis `dilim + 24*i` ile kurulur.
"""

from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

import numpy as np

from dartrift.inference.design import DART_UZAYI_S4, lhs_design
from dartrift.inference.gp_vekil import (
    gp_grup_loo,
    gp_uydur,
    gp_varyans_kalibre,
)
from dartrift.inference.surrogate import fit_surrogate, loo_artiklari

#: PROTOKOL-HAVUZ §3 kilitli tasarımı.
N_HAVUZ, TOHUM = 96, 20260906
#: p_kalibrasyon_raporu.KAT_SAYISI ile aynı.
KAT_SAYISI = 4

#: ADR-0054: kütleye göre düzeltilmiş gözlem hedefi ve asimetrik aralık.
BETA_GOZ = 3.5418
BETA_GOZ_UST, BETA_GOZ_ALT = 0.188, 0.247
#: PROTOKOL-HAVUZ: ilan edilen bağıl fark terimleri, `b = beta - 1` üzerinde.
SIGMA_MODEL_B = 0.0650


def oku(yol: Path):
    idx, beta, ejf = [], [], []
    with open(yol, newline="", encoding="utf-8") as f:
        for s in csv.DictReader(f):
            idx.append(int(s["idx"]))
            beta.append(float(s["beta"]))
            ejf.append(float(s["ejf"]))
    return np.array(idx), np.array(beta), np.array(ejf)


def kapsama_raporu(U: np.ndarray, adlar) -> None:
    """Birim küpte her eksenin doluluğu: en büyük boşluk önemli.

    Bir eksende büyük bir boşluk varsa vekil orayı DIŞDEĞERLEME ile
    doldurur ve çapraz doğrulama bunu göremez.
    """
    print("\n--- theta kapsamasi (birim kupte) ---")
    for j, ad in enumerate(adlar):
        u = np.sort(U[:, j])
        # uçlar dahil en büyük boşluk
        kenarli = np.concatenate([[0.0], u, [1.0]])
        bosluk = np.diff(kenarli)
        print(f"  {ad:12s} min={u[0]:.3f} max={u[-1]:.3f} "
              f"en_buyuk_bosluk={bosluk.max():.3f} "
              f"(konum {kenarli[bosluk.argmax()]:.2f})")


def kat_ozeti(katlar: np.ndarray) -> None:
    print("\n--- 4 kat dagilimi (kat = kuresel indis % 4) ---")
    for k in range(KAT_SAYISI):
        n = int((katlar == k).sum())
        print(f"  kat {k}: {n:3d} nokta")


def artik_ozeti(ad: str, e: np.ndarray, y: np.ndarray) -> dict:
    rmse = float(np.sqrt(np.mean(e**2)))
    mae = float(np.mean(np.abs(e)))
    enb = float(np.max(np.abs(e)))
    # q2: 1 - SS_cv / SS_toplam. Negatifse vekil ortalamadan kotu.
    q2 = 1.0 - float(np.sum(e**2)) / float(np.sum((y - y.mean()) ** 2))
    print(f"  {ad:22s} rmse={rmse:.4f}  mae={mae:.4f}  "
          f"en_buyuk={enb:.4f}  q2={q2:+.4f}")
    return {"rmse": rmse, "mae": mae, "enb": enb, "q2": q2}


def kapsama68(e: np.ndarray, var: np.ndarray) -> float:
    """Standartlaştırılmış artıkların |z| <= 1 oranı. Hedef ~0,68."""
    z = e / np.sqrt(var)
    return float(np.mean(np.abs(z) <= 1.0))


def ogrenme_egrisi(X, y, idx, rmse_tam, sigma_goz, sigma_model) -> None:
    """CD hatasi nokta sayisiyla nasil duzeliyor; 96'da nerede olur?

    Alt kumeler `maximin_alt_kume` ile secilir -- rastgele degil, uzayi
    EN IYI dolduran alt kume. Rastgele alt kume kapsamayi bozar ve egriyi
    oldugundan kotu gosterir.

    Guc yasasi `rmse = C n^(-p)` log-log'da dogrudur; 96'ya DISDEGERLEME
    yapilir. Disdegerleme bir tahmindir, olcum degil.
    """
    from dartrift.inference.ic_ice_tasarim import maximin_alt_kume

    print("\n--- 5) ogrenme egrisi: CD hatasi nokta sayisiyla ---")
    U = DART_UZAYI_S4.to_unit(X)
    n_hepsi = len(X)
    # Kuadratik 10 katsayi ister; 4 kat CD'de egitim 3/4 n olur -> n > 14.
    boyutlar = [n for n in (20, 28, 36, 44, 50, n_hepsi) if n <= n_hepsi]
    noktalar = []
    print(f"  {'n':>4s}  {'GP rmse':>9s}  {'kuadratik':>9s}")
    for n in boyutlar:
        alt = maximin_alt_kume(U, n)
        Xa, ya, ia = X[alt], y[alt], idx[alt]
        ka = ia % KAT_SAYISI
        if len(np.unique(ka)) < 2:
            continue
        gpa = gp_uydur(DART_UZAYI_S4, Xa, ya)
        ea, _ = gp_grup_loo(gpa, ya, ka)
        r_gp = float(np.sqrt(np.mean(ea**2)))
        try:
            eq = loo_artiklari(DART_UZAYI_S4, Xa, ya, gruplar=ka)
            r_kd = f"{float(np.sqrt(np.mean(eq**2))):9.4f}"
        except ValueError:
            r_kd = "        -"
        noktalar.append((n, r_gp))
        print(f"  {n:4d}  {r_gp:9.4f}  {r_kd}")

    if len(noktalar) >= 3:
        ns = np.array([p[0] for p in noktalar], float)
        rs = np.array([p[1] for p in noktalar], float)
        # log rmse = log C - p log n
        egim, kesme = np.polyfit(np.log(ns), np.log(rs), 1)
        tahmin96 = float(np.exp(kesme + egim * math.log(96)))
        print(f"\n  guc yasasi: rmse ~ n^({egim:+.3f})")
        print(f"  96 noktada TAHMIN: rmse = {tahmin96:.4f}  "
              f"(suan {rmse_tam:.4f})")
        toplam = math.sqrt(sigma_goz**2 + sigma_model**2 + tahmin96**2)
        pay = tahmin96**2 / toplam**2
        print(f"  96'da vekilin varyans payi: %{100 * pay:.1f}")
        if pay > 0.25:
            print("  >> 96 nokta TEK BASINA yetmeyebilir; cok doguruluklu")
            print("     duzeltme ve/veya ek nokta gerekebilir.")
        else:
            print("  >> 96 noktada vekil baskin terim olmaktan cikar.")
        print("  (Disdegerleme TAHMINDIR; 96 nokta gelince olculecek.)")


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    idx, beta, ejf = oku(Path(sys.argv[1]))

    tasarim = lhs_design(DART_UZAYI_S4, N_HAVUZ, root_seed=TOHUM)
    X = tasarim[idx]
    U = DART_UZAYI_S4.to_unit(X)
    adlar = list(DART_UZAYI_S4.names)

    print("=" * 68)
    print("VEKIL ON CALISMASI  --  KESIF, YARGI DEGIL")
    print("=" * 68)
    print(f"nokta           : {len(idx)} / {N_HAVUZ}  "
          f"(%{100 * len(idx) / N_HAVUZ:.1f})")
    print(f"eksenler        : {', '.join(adlar)}")
    print(f"beta araligi    : {beta.min():.4f} .. {beta.max():.4f}  "
          f"(ortalama {beta.mean():.4f}, std {beta.std(ddof=1):.4f})")
    print(f"ejekta kesri    : {ejf.min():.3e} .. {ejf.max():.3e}")

    kapsama_raporu(U, adlar)

    katlar = idx % KAT_SAYISI
    kat_ozeti(katlar)

    # ---------------------------------------------------------------
    # 1) Kuadratik vekil (Protokol P'de BIRINCIL yol)
    # ---------------------------------------------------------------
    print("\n--- 1) kuadratik vekil, theta-gruplu 4 kat CD ---")
    e_kuad = loo_artiklari(DART_UZAYI_S4, X, beta, gruplar=katlar)
    o_kuad = artik_ozeti("kuadratik (beta)", e_kuad, beta)
    uyum_kuad = fit_surrogate(DART_UZAYI_S4, X, beta)
    print(f"  {'tam veri uyumu':22s} q2={uyum_kuad.q2:+.4f}  "
          f"rmse_loo={uyum_kuad.rmse_loo:.4f}")

    # ---------------------------------------------------------------
    # 2) GP vekili (Protokol P §4c ikinci yol)
    # ---------------------------------------------------------------
    print("\n--- 2) GP vekili, theta-gruplu 4 kat CD ---")
    gp = gp_uydur(DART_UZAYI_S4, X, beta)
    e_gp, var_gp = gp_grup_loo(gp, beta, katlar)
    o_gp = artik_ozeti("GP (beta)", e_gp, beta)
    print(f"  kalibrasyon oncesi kapsama68 = {kapsama68(e_gp, var_gp):.3f} "
          f"(hedef ~0,68)")

    gp_k, bilgi = gp_varyans_kalibre(gp, beta, katlar)
    print(f"  Bachoc varyans carpani       = {gp_k.varyans_carpani:.4f}")
    # DIKKAT: `gp_grup_loo` carpani BILEREK uygulamaz -- carpan zaten o
    # artiklardan hesaplaniyor, uygulasa dongusel olurdu. Kalibre edilmis
    # kapsamayi gormek icin varyans elle carpilir (`predict_u` uretimde
    # bunu kendisi yapiyor).
    kapsama_k = kapsama68(e_gp, var_gp * gp_k.varyans_carpani)
    print(f"  kalibrasyon SONRASI kapsama68 = {kapsama_k:.3f}")
    for anah, deg in sorted(bilgi.items()):
        print(f"    {anah:24s} {deg}")

    # ---------------------------------------------------------------
    # 3) ARD uzunluk olcekleri -- hangi eksen beta'yi tasiyor
    # ---------------------------------------------------------------
    print("\n--- 3) ARD uzunluk olcekleri (birim kupte) ---")
    print("  Kisa olcek = beta o eksende HIZLI degisiyor (bilgi tasiyor).")
    print("  Uzun olcek = beta o eksene duyarsiz (ogrenilecek sey yok).")
    ell = gp.ell
    ciftler = sorted(zip(adlar, ell, strict=True), key=lambda t: t[1])
    for ad, olcek in ciftler:
        etiket = ("TASIYOR" if olcek < 1.0
                  else ("zayif" if olcek < 3.0 else "DUYARSIZ"))
        print(f"  {ad:14s} ell={olcek:8.3f}   {etiket}")
    print(f"  sinyal s2={gp.s2:.4f}  gurultu n2={gp.n2:.6f}  "
          f"snr={math.sqrt(gp.s2 / max(gp.n2, 1e-12)):.1f}")

    # ---------------------------------------------------------------
    # 4) Vekil hatasi bütçenin neresinde
    # ---------------------------------------------------------------
    print("\n--- 4) vekil hatasi, hata butcesine karsi ---")
    sigma_goz = 0.5 * (BETA_GOZ_UST + BETA_GOZ_ALT)
    b_goz = BETA_GOZ - 1.0
    sigma_model = SIGMA_MODEL_B * b_goz
    en_iyi = min(o_kuad["rmse"], o_gp["rmse"])
    print(f"  gozlem      sigma_goz   = {sigma_goz:.4f}  (beta biriminde)")
    print(f"  model farki sigma_model = {sigma_model:.4f}  "
          f"({SIGMA_MODEL_B} x b_goz={b_goz:.4f})")
    print(f"  VEKIL       rmse_cd     = {en_iyi:.4f}")
    toplam = math.sqrt(sigma_goz**2 + sigma_model**2 + en_iyi**2)
    pay = en_iyi**2 / toplam**2
    print(f"  toplam                  = {toplam:.4f}")
    print(f"  vekilin varyans payi    = %{100 * pay:.1f}")
    if pay > 0.25:
        print("  >> UYARI: vekil baskin terim. Daha cok nokta ya da daha iyi")
        print("     cekirdek gerekir; posterior vekil hatasiyla genisler.")
    else:
        print("  >> vekil baskin DEGIL: darbogaz gozlem ve model farki.")

    # ---------------------------------------------------------------
    # 5) Ogrenme egrisi -- 96 nokta yetecek mi?
    # ---------------------------------------------------------------
    ogrenme_egrisi(X, beta, idx, en_iyi, sigma_goz, sigma_model)

    # ---------------------------------------------------------------
    # 6) Yanit donusumu -- KESIF, benimsemek AYRI bir karardir
    # ---------------------------------------------------------------
    print("\n--- 6) yanit donusumu: beta mi log(beta-1) mi ---")
    print("  Fiziksel gerekce (sayi gerekcesi DEGIL): b = beta - 1 pozitif,")
    print("  7,5 kat araliga yayiliyor ve PROTOKOL-DO olcumu b = C Y0^p")
    print("  biciminde CARPIMSAL bir yasa buldu. log b o yasayi dogrusal")
    print("  yapar; GP'nin durag anlik varsayimina daha uygundur.")
    b = beta - 1.0
    gp_log = gp_uydur(DART_UZAYI_S4, X, np.log(b))
    e_log, _ = gp_grup_loo(gp_log, np.log(b), katlar)
    # log uzayindaki artigi beta birimine geri tasi: d(beta) = b * d(log b)
    rmse_log_beta = float(np.sqrt(np.mean((b * e_log) ** 2)))
    print(f"  dogrudan beta        rmse={o_gp['rmse']:.4f}")
    print(f"  log(beta-1) -> beta  rmse={rmse_log_beta:.4f}")
    if rmse_log_beta < o_gp["rmse"]:
        kazanc = 100 * (1 - rmse_log_beta / o_gp["rmse"])
        print(f"  log uzayi %{kazanc:.0f} daha iyi.")
    else:
        print("  dogrudan beta daha iyi ya da esit.")
    print("  >> DIKKAT: bu sonucu gorup donusumu secmek, esigi sonuca gore")
    print("     ayarlamakla ayni kusurdur. Donusum benimsenecekse gerekce")
    print("     FIZIKSEL olmali ve havuz okunmadan ONCE yazilmalidir.")
    print("     Burada yalniz olculdu; hicbir sey benimsenmedi.")

    print("\n" + "=" * 68)
    print("Havuz dolmadan hicbir kilitli esik uygulanmadi. Yol secimi")
    print("(kuadratik mi GP mi) Protokol P 4c'ye gore DIS ORNEKLEMDE")
    print("yapilir; bu betik onu YAPMAZ.")
    print("=" * 68)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
