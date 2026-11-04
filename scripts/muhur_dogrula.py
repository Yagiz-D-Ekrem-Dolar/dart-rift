"""MÜHÜR DOĞRULAMA — `docs/onkayit/` altındaki kayıtlar sağlam mı?

## Niçin var

Projenin en güçlü iddiası iki **mühürlü** Hera ön kaydıdır: Hera varmadan
önce yazılmış, SHA-256 ile çivilenmiş öngörüler. O iddianın değeri,
**başkasının doğrulayabilmesine** bağlıdır. 2026-11-04'te ölçüldü:
`tests/test_hera_tahmin.py` yalnız kendi ürettiği **geçici** bir kaydın
özetini sınıyordu; **depoda duran iki gerçek mührü hiçbir şey
doğrulamıyordu**.

Bu betik o boşluğu kapatır ve tek komutla koşar:

    python scripts/muhur_dogrula.py

Çıkış kodu `0` ise bütün mühürler sağlam, `1` ise değil. Jüri de,
gelecekteki bir okur da bunu koşabilir.

## Özetin tarifi — iki üretici betikten BIREBIR alındı

`hera_krater_onkayit.py:288` ve `hera_spin_onkayit.py:224` aynı tarifi
kullanıyor:

    govde = json.dumps(kayit, ensure_ascii=False, indent=1, sort_keys=True)
    sha256 = hashlib.sha256(govde.encode("utf-8")).hexdigest()

burada `kayit` **`sha256` alanı eklenmeden önceki** sözlüktür. Bu betik
tarifi yeniden yazmaz, aynısını uygular — ikinci bir tanım uydurmak
yanlış negatif üretirdi.

## Ne denetlenir

1. **SHA-256** yeniden hesaplanır ve kayıttakiyle karşılaştırılır.
2. **`git_commit`** kayıtta varsa, o commit depoda **gerçekten var mı**.
3. **Gönderme yapılan veri dosyaları** (`havuz`, `krater_olcumu`) hâlâ
   yerinde mi.
4. **Kural 8 sayımı:** `beklenen == kullanilan + dislanan`.

Bir mührün *içeriğinin doğru olduğu* denetlenmez — bu mümkün değildir ve
mühürün amacı da o değildir. Denetlenen şey **değiştirilmediği**dir.

## İki ayrı ağırlık — karıştırılmaz

- **MÜHÜR BOZUK** (ölümcül, çıkış `1`): özet tutmuyor ya da `sha256`
  alanı yok. Kayıt değiştirilmiş demektir.
- **İZ EKSİK** (kusur, ölümcül **değil**): özet sağlam ama gönderme
  yapılan dosya ya da commit depodan bulunamıyor. Mühür geçerlidir,
  **izlenebilirliği** eksiktir. `--kati` ile bu da ölümcül yapılır.

Bu ayrım önemli: ilk koşuşta (2026-11-04) spin kaydının özeti
**sağlam** çıktı ama `havuz` alanı `analiz/havuz_posterior_girdi.csv`
diyordu — TRUBA çalışma alanının yolu, deponun değil. Mühür bozuk
değildi; işaretçisi bayattı. İkisini aynı kefeye koymak abartma olurdu.

## Bilinen sınır — girdi dosyalarının özeti YOK

Mevcut iki kayıt girdi dosyalarının **içerik özetini taşımıyor**, yalnız
yolunu. Dolayısıyla "mühür değişmemiş" doğrulanabilir, ama "mühür
*şu* veriyle üretilmiş" doğrulanamaz. Bu betik o boşluğu **kapatamaz**
(geçmişe dönük hesaplamak, mührü üretenin gördüğü dosyayı gördüğümüzü
varsaymak olurdu). Bundan sonraki kayıtlar her girdi dosyasının
`sha256`'sını de taşımalı; bu bir **öneri**, geçmişe uygulanmaz.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ONKAYIT = REPO / "docs" / "onkayit"
#: Uretici betiklerden BIREBIR: json.dumps(..., indent=1, sort_keys=True)
GOVDE_AYARI = {"ensure_ascii": False, "indent": 1, "sort_keys": True}


def govde_ozeti(kayit: dict) -> str:
    """`sha256` alanı **çıkarılmış** kaydın kanonik özeti."""
    govde_sozluk = {k: v for k, v in kayit.items() if k != "sha256"}
    govde = json.dumps(govde_sozluk, **GOVDE_AYARI)
    return hashlib.sha256(govde.encode("utf-8")).hexdigest()


def _commit_var_mi(sha: str) -> bool | None:
    """Commit depoda var mı? Git yoksa `None` (denetlenemedi)."""
    try:
        s = subprocess.run(["git", "-C", str(REPO), "cat-file", "-e",
                            f"{sha}^{{commit}}"],
                           capture_output=True, timeout=30, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return s.returncode == 0


#: `analiz/` onekli yollar TRUBA calisma alanindan gelir; deponun
#: karsiligi burada. Yol SESSIZCE duzeltilmez -- bulunan karsilik
#: IZ bulgusu olarak YAZILIR.
DEPO_KARSILIGI = {"analiz": Path("docs") / "sonuclar"}


def kaydi_denetle(yol: Path) -> tuple[list[str], list[str]]:
    """`(muhur_ihlalleri, iz_bulgulari)` -- ikisi AYRI agirlikta."""
    ihlal: list[str] = []
    iz: list[str] = []
    try:
        kayit = json.loads(yol.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        return [f"okunamadi/bozuk JSON: {e}"], []

    # --- 1. SHA-256 ----------------------------------------------------
    yazili = kayit.get("sha256")
    if not isinstance(yazili, str) or not yazili:
        ihlal.append("`sha256` alani YOK -- bu bir muhur degil")
    else:
        hesap = govde_ozeti(kayit)
        if hesap != yazili:
            ihlal.append(f"SHA-256 TUTMUYOR\n      kayitta: {yazili}"
                         f"\n      hesap  : {hesap}")

    # --- 2. git_commit depoda var mi -----------------------------------
    gc = kayit.get("git_commit")
    if isinstance(gc, str) and gc:
        var = _commit_var_mi(gc)
        if var is False:
            iz.append(f"git_commit depoda YOK: {gc}")

    # --- 3. gonderme yapilan veri dosyalari ----------------------------
    for alan in ("havuz", "krater_olcumu"):
        d = kayit.get(alan)
        if not isinstance(d, str) or not d:
            continue
        bagil = Path(d.replace("\\", "/"))
        if (REPO / bagil).exists():
            continue
        # Depo karsiligi var mi? Varsa IZ bulgusu olarak yazilir.
        kars = DEPO_KARSILIGI.get(bagil.parts[0] if bagil.parts else "")
        bulundu = (REPO / kars / bagil.name) if kars else None
        if bulundu is not None and bulundu.exists():
            iz.append(f"`{alan}` yolu kayitta `{d}` (TRUBA alani); "
                      f"deponun karsiligi `{bulundu.relative_to(REPO)}` "
                      f"-- SESSIZCE duzeltilmedi")
        else:
            iz.append(f"`{alan}` dosyasi depoda BULUNAMADI: {d}")

    # --- 3b. girdi dosyalarinin ICERIK ozeti --------------------------
    # Varsa DOGRULANIR, yoksa IZ bulgusu olarak yazilir. Gecmise donuk
    # hesaplanmaz: muhrun uretildigi anda gorulen dosyayi gordugumuzu
    # varsaymak olurdu. Uretici betikler artik bu alani yaziyor.
    go = kayit.get("girdi_ozetleri")
    if not isinstance(go, dict) or not go:
        iz.append("`girdi_ozetleri` YOK -- 'muhur degismemis' "
                  "dogrulanabilir, 'muhur SU veriyle uretilmis' "
                  "dogrulanamaz (gecmise donuk eklenmez)")
    else:
        for d, beklenen in sorted(go.items()):
            if not isinstance(beklenen, str) or beklenen.startswith(
                    "OKUNAMADI"):
                iz.append(f"girdi ozeti kayitta bozuk: {d} -> {beklenen}")
                continue
            bagil = Path(d.replace("\\", "/"))
            aday = REPO / bagil
            if not aday.exists():
                kars = DEPO_KARSILIGI.get(
                    bagil.parts[0] if bagil.parts else "")
                aday = (REPO / kars / bagil.name) if kars else aday
            if not aday.exists():
                iz.append(f"girdi dosyasi bulunamadi, ozet denetlenemedi: "
                          f"{d}")
                continue
            try:
                simdi = hashlib.sha256(aday.read_bytes()).hexdigest()
            except OSError as e:
                iz.append(f"girdi okunamadi: {d} ({e})")
                continue
            if simdi != beklenen:
                ihlal.append(
                    f"GIRDI DEGISMIS: {d}\n      kayitta: {beklenen}"
                    f"\n      simdi  : {simdi}")

    # --- 4. kural 8: beklenen == kullanilan + dislanan -----------------
    nk = kayit.get("nokta_kumesi")
    if isinstance(nk, dict):
        b, k, d = nk.get("beklenen"), nk.get("kullanilan"), nk.get("dislanan")
        if all(isinstance(q, int) for q in (b, k, d)) and k + d != b:
            ihlal.append(f"KURAL 8: beklenen {b} != kullanilan {k} + "
                         f"dislanan {d} = {k + d}")
    return ihlal, iz


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dizin", type=Path, default=ONKAYIT)
    p.add_argument("--en-az", type=int, default=2,
                   help="BOSLUK KONTROLU: en az bu kadar kayit bulunmali")
    p.add_argument("--kati", action="store_true",
                   help="IZ bulgularini da olumcul say")
    a = p.parse_args()

    kayitlar = sorted(a.dizin.glob("*.json"))
    print("=" * 68)
    print("MUHUR DOGRULAMA")
    print("=" * 68)
    print(f"dizin : {a.dizin}")
    print(f"kayit : {len(kayitlar)}  (en az {a.en_az} bekleniyor)")
    print()

    # BOSLUK KONTROLU (ADR-0040): dosya yoksa bu betik "hepsi saglam"
    # diye YESIL donerdi. Sayim once denetlenir.
    if len(kayitlar) < a.en_az:
        print(f"BOSLUK: {len(kayitlar)} kayit bulundu, en az {a.en_az} "
              f"bekleniyordu -- dogrulama YAPILMADI sayilir")
        return 1

    bozuk = izli = 0
    for yol in kayitlar:
        ihlal, iz = kaydi_denetle(yol)
        if ihlal:
            etiket, bozuk = "MUHUR BOZUK", bozuk + 1
        elif iz:
            etiket, izli = "IZ EKSIK", izli + 1
        else:
            etiket = "SAGLAM"
        print(f"  [{etiket:>11}] {yol.name}")
        if not ihlal:
            k = json.loads(yol.read_text(encoding="utf-8"))
            print(f"                sha256 {k['sha256'][:16]}...  "
                  f"commit {str(k.get('git_commit', '-'))[:12]}")
        for m in ihlal:
            print(f"                MUHUR -> {m}")
        for m in iz:
            print(f"                IZ    -> {m}")

    print()
    print(f"ozet  : muhur bozuk {bozuk}, iz eksik {izli}, "
          f"saglam {len(kayitlar) - bozuk - izli} / {len(kayitlar)}")
    if bozuk:
        print(f"YARGI: {bozuk} kayitta MUHUR BOZUK -- kayit degistirilmis")
        return 1
    if izli and a.kati:
        print(f"YARGI: muhurler saglam ama {izli} kayitta IZ EKSIK "
              f"(--kati verildi, olumcul sayildi)")
        return 1
    if izli:
        print(f"YARGI: butun muhurler SAGLAM. {izli} kayitta IZ EKSIK -- "
              f"muhur GECERLI, izlenebilirligi eksik (ayrinti yukarida)")
        return 0
    print(f"YARGI: {len(kayitlar)}/{len(kayitlar)} kayit SAGLAM -- "
          f"muhurler degistirilmemis, izleri tam")
    return 0


if __name__ == "__main__":
    sys.exit(main())
