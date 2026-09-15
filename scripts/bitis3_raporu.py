"""Bitiş 3 taslak raporu — kilitli karar kurallarını S_*.json çıktılarına uygular.

Yeni yargı ÜRETMEZ; PROTOKOL-Q §4 (esas sonuç seçimi), PROTOKOL-P §4c/§4e
(yol ve P-v4b kuralı) ve PROTOKOL-D'yi (gerçek gözlem) mevcut JSON'lara
uygulayıp tek bir Markdown taslağı yazar. Eksik JSON → "BEKLENİYOR".

Kullanim:
    python scripts/bitis3_raporu.py --kok kampanya --cikti docs/BITIS3-TASLAK.md
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

YAKINSAMA_GOZLEMLERI = ("d_merkez", "R_krater", "V_krater", "beta_eksi_1", "M_ejekta")


def _oku(kok: Path, ad: str):
    p = kok / ad
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _m_karari(n_yak: int) -> str:
    """`m_yakinsama_raporu._m_karari` ile AYNI eşikler (sınanıyor)."""
    return "YAKINSIYOR" if n_yak >= 4 else ("YAKINSAMIYOR" if n_yak <= 1 else "KISMI")


def _q1_birlestir(kararlar) -> str:
    n = sum(1 for k in kararlar if k == "YAKINSIYOR")
    if n >= 4:
        return "YAKINSIYOR"
    n_kismi = sum(1 for k in kararlar if k == "KISMI")
    return "KISMI" if (n + n_kismi) >= 2 else "YAKINSAMIYOR"


def yakinsama_yargisi(s_m: dict | None) -> str:
    """PROTOKOL-Q §4: gözlenebilir yargılarından genel yakınsama sınıfı.

    2026-09-15 öz denetim (A88): gözlenebilir yargısı `kesin: False` ise
    (OKUNMAZ θ'lar) o gözlenebilirin alabileceği bütün kararlar denenir; Q1
    hepsinde aynı değilse "EKSIK" döner ve esas havuz SEÇİLMEZ — eksik Mt
    sessizce ince-72'yi seçtirmesin. `kesin` alanı yoksa eski davranış.
    """
    from itertools import product

    if not s_m:
        return "BEKLENIYOR"
    secenek, belirsiz = [], []
    for g in YAKINSAMA_GOZLEMLERI:
        y = (s_m.get(g) or {}).get("yargi", {})
        if y.get("kesin") is False:
            n0, n_ok = int(y.get("n_yakinsamis", 0)), int(y.get("n_okunmaz", 0))
            secenek.append(sorted({_m_karari(k) for k in range(n0, n0 + n_ok + 1)}))
            belirsiz.append(g)
        else:
            secenek.append([y.get("karar")])
    sonuc = {_q1_birlestir(c) for c in product(*secenek)}
    if len(sonuc) == 1:
        return sonuc.pop()
    return f"EKSIK (kesin olmayan: {', '.join(belirsiz)})"


def _elendi(yol: dict | None) -> bool:
    if not yol or yol.get("hata"):
        return True
    g = yol.get("genel", "")
    return g.startswith("KALIBRASYON") or "GECERSIZ" in g


def _cozulen(yol: dict | None) -> int:
    if not yol or _elendi(yol):
        return -1
    return max((yol.get("cozulen") or {}).values(), default=0)


def p_esas(yol_v4: dict | None, yol_v4b: dict | None) -> dict:
    """PROTOKOL-P §4e: P-v4b yalnız elenmemiş ve daha çok ekseni çözüyorsa girer."""
    if yol_v4 is None and yol_v4b is None:
        return {"kaynak": None, "genel": "BEKLENIYOR"}
    if not _elendi(yol_v4b) and _cozulen(yol_v4b) > _cozulen(yol_v4):
        return {"kaynak": "P-v4b", "genel": yol_v4b["genel"], "esas_vekil": yol_v4b.get("esas")}
    if yol_v4 is not None and not _elendi(yol_v4):
        return {"kaynak": "P-v4", "genel": yol_v4["genel"], "esas_vekil": yol_v4.get("esas")}
    return {"kaynak": "P-v4", "genel": "KALIBRASYON DUSTU"}


def esas_sonuc(kok: Path) -> dict:
    """PROTOKOL-Q §4."""
    q1 = yakinsama_yargisi(_oku(kok, "S_Mt.json"))
    plato = p_esas(_oku(kok, "S_PQo_yol.json"), _oku(kok, "S_PQob_yol.json"))
    ince = p_esas(_oku(kok, "S_Pv4i72_yol.json"), _oku(kok, "S_Pv4i72b_yol.json"))
    if q1 == "YAKINSIYOR":
        esas = {"havuz": "Q3 orta 0,1 s", **plato}
    elif q1 == "YAKINSAMIYOR":
        esas = {"havuz": "ince-72, 24 ms", **ince}
    elif q1 == "KISMI":
        esas = {"havuz": "Q3 orta 0,1 s + ince-72 24 ms (birlikte)", "genel":
                f"plato: {plato['genel']} / ince: {ince['genel']}", "kaynak": "ikisi"}
    else:
        esas = {"havuz": "BEKLENIYOR", "genel": "BEKLENIYOR", "kaynak": None}
    return {"Q1": q1, "esas": esas, "plato": plato, "ince72": ince}


def taslak(kok: Path) -> str:
    e = esas_sonuc(kok)
    satir = ["# Bitiş 3 — taslak (otomatik, kilitli kurallar)", "",
             "Bu belge `scripts/bitis3_raporu.py` ile üretildi; yargılar PROTOKOL-Q §4, "
             "PROTOKOL-P §4c/§4e ve PROTOKOL-D'den. Elle düzenlemeden önce kaynak "
             "JSON'lara bakın.", "",
             "## 1. Esas sonuç seçimi (Q §4)", "",
             f"- Q1 plato anında yakınsama: **{e['Q1']}**",
             f"- Esas havuz: **{e['esas']['havuz']}**",
             f"- Esas posterior yargısı: **{e['esas']['genel']}** "
             f"(kaynak {e['esas'].get('kaynak')})", "",
             "## 2. Havuz başına kilitli yol seçimleri", "",
             "| havuz | P-v4 | P-v4b |", "|---|---|---|"]
    for ad, o in (("kaba-48 (24 ms)", "Pv4k"), ("orta-48 (24 ms)", "Pv4o"),
                  ("ince-48 (24 ms)", "Pv4i"), ("kaba-72", "Pv4k72"), ("orta-72", "Pv4o72"),
                  ("ince-72", "Pv4i72"), ("Q2 kaba 0,1 s", "PQk"), ("Q3 orta 0,1 s", "PQo"),
                  ("Q5 blok kaba 0,1 s", "PQbk")):
        a, b = _oku(kok, f"S_{o}_yol.json"), _oku(kok, f"S_{o}b_yol.json")
        satir.append(f"| {ad} | {(a or {}).get('genel', 'BEKLENIYOR')} | "
                     f"{(b or {}).get('genel', 'BEKLENIYOR')} |")
    m2t = _oku(kok, "S_M2t.json")
    satir += ["", "## 3. Kontrast dayanıklılığı", "",
              f"- M2 (24 ms): H_Y **{(_oku(kok, 'S_M2.json') or {}).get('H_Y', 'BEKLENIYOR')}**",
              f"- M2t (0,1 s): H_Y **{(m2t or {}).get('H_Y', 'BEKLENIYOR')}**, "
              f"H_a {(m2t or {}).get('H_a', '-')}, H_f {(m2t or {}).get('H_f', '-')}"
              + "".join(f" — **H_{e} KESİN DEĞİL** ({k.get('n_okunmaz')} OKUNMAZ)"
                        for e, k in ((m2t or {}).get("kesinlik") or {}).items()
                        if k.get("kesin") is False), "",
              "## 4. Gerçek DART gözlemi (Protokol D)", ""]
    for ad, o in (("orta 0,1 s", "S_DART_Qo.json"), ("kaba 0,1 s", "S_DART_Qk.json"),
                  ("ince 24 ms (betimleyici)", "S_DART_i72.json")):
        d = _oku(kok, o)
        if not d:
            satir.append(f"- {ad}: BEKLENIYOR")
            continue
        k = d["kapsama"]
        g = d["gozlem"]
        sat = (f"- {ad}: gözlenen β = {g['beta']:.2f} ± {g['sigma_beta']:.2f}; model β aralığı "
               f"{1 + 10 ** k['tahmin_min']:.2f}–{k['beta_max_model']:.2f}; **{k['karar']}** "
               f"(üst fark {k['fark_ust_sigma']:+.1f}σ)")
        if "posterior" in d:
            p = d["posterior"]
            sat += " — " + ", ".join(f"{ax}: {p[ax]['karar']}" for ax in
                                     ("blok_alpha0", "log10_Y0", "blok_kesri"))
        if d.get("cozunurluk_notu"):
            sat += f" _(σ_çöz: {d['cozunurluk_notu']})_"
        satir.append(sat)
    u = _oku(kok, "S_U.json")
    satir += ["", "## 5. Model yeterliliği (Protokol U)", "",
              f"- Genel: **{(u or {}).get('genel', 'BEKLENIYOR')}**"]
    if (u or {}).get("tam") is True:
        satir.append("- Kapsam: TAM (beklenen bütün varyant × merdiven × tohum)")
    elif (u or {}).get("tam") is False:
        satir.append(f"- Kapsam: **EKSİK** ({', '.join(u.get('eksik', []))}) — "
                     "genel yargı eksik tasarımla verildi")
    for anah, r in sorted(((u or {}).get("satirlar") or {}).items()):
        if r.get("karar") == "OKUNMAZ":
            satir.append(f"  - {anah}: OKUNMAZ")
            continue
        satir.append(f"  - {anah}: β−1 sim {r['beta_eksi_1_sim']:.3f} / gözlem "
                     f"{r['beta_eksi_1_gozlem']:.3f} (z {r['z']:+.1f}) → {r['karar']}")
    v = _oku(kok, "S_V.json")
    u_genel = (u or {}).get("genel", "")
    if v:
        v_durum = f"koşuldu — **{v.get('genel', 'OKUNMAZ')}**"
    elif u_genel.startswith("HICBIR VARYANT ULASMIYOR") and (u or {}).get("tam") is False:
        v_durum = "BEKLENIYOR — U **EKSİK**; eksik görevler tamamlanmadan V kararı verilmez"
    elif u_genel.startswith("HICBIR VARYANT ULASMIYOR"):
        v_durum = "**GÖNDERİLMELİ** (U hiçbir varyantla ulaşmadı; `scripts/v_gonderim_karari.py`)"
    elif u_genel.startswith("MODEL GOZLEME ULASABILIYOR"):
        v_durum = "gönderilmez (U'da ulaşan varyant var)"
    else:
        v_durum = "BEKLENIYOR (U sonucu yok)"
    satir += ["", "## 5b. Protokol V (koşullu: yerçekimi / hasar / 0,2 s)", "",
              f"- Durum: {v_durum}"]
    satir += ["", "## 6. Hera ön kayıtları (Protokol HT)", ""]
    for etiket in ("Qo", "i72"):
        k = _oku(kok, f"ONKAYIT_HERA_{etiket}.json")
        if not k:
            satir.append(f"- {etiket}: BEKLENIYOR")
            continue
        r = (k.get("tahmin") or {}).get("R_krater", {}).get("kantiller", {})
        satir.append(f"- {etiket}: {k['meta'].get('kosul')}; R_krater q16/q50/q84 = "
                     f"{r.get('q16', float('nan')):.2f} / {r.get('q50', float('nan')):.2f} / "
                     f"{r.get('q84', float('nan')):.2f} m; sha256 {k.get('sha256', '')[:12]}…; "
                     f"t_end {k['meta'].get('t_end_s')} s")
    return "\n".join(satir) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kok", type=Path, required=True)
    ap.add_argument("--cikti", type=Path, required=True)
    a = ap.parse_args(argv)
    metin = taslak(a.kok)
    a.cikti.write_text(metin, encoding="utf-8")
    print(metin)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
